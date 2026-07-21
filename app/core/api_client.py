"""MiMo TTS V2.5 API 客户端封装

使用 OpenAI 兼容的 Chat Completions 接口调用 MiMo TTS。
"""

import base64
import logging
from typing import Optional

from openai import OpenAI, APIError, APITimeoutError, AuthenticationError, RateLimitError

logger = logging.getLogger(__name__)


class MimoAPIError(Exception):
    """MiMo API 调用异常，携带用户友好的中文提示"""

    def __init__(self, message: str, original: Optional[Exception] = None,
                 response_body: str = ""):
        super().__init__(message)
        self.original = original
        self.response_body = response_body


class MimoTTSClient:
    """小米 MiMo TTS V2.5 API 客户端

    兼容 OpenAI Chat Completions 格式，支持三个模型：
    - mimo-v2.5-tts: 预置音色合成
    - mimo-v2.5-tts-voicedesign: 文本音色设计
    - mimo-v2.5-tts-voiceclone: 语音克隆
    """

    MODELS = {
        "mimo-v2.5-tts": "预置音色合成",
        "mimo-v2.5-tts-voicedesign": "音色设计",
        "mimo-v2.5-tts-voiceclone": "语音克隆",
    }

    # MiMo V2.5 官方支持的输出格式
    SUPPORTED_FORMATS = {"wav", "mp3"}

    def __init__(self, api_key: str, base_url: str):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = OpenAI(api_key=api_key, base_url=self._base_url)

    # ── Messages 构建 ──────────────────────────────────

    def _build_messages_for_tts(
        self, text: str, style_text: str = ""
    ) -> list:
        """基础 TTS：user 放风格指令（可选），assistant 放合成文本"""
        messages = []
        if style_text and style_text.strip():
            messages.append({"role": "user", "content": style_text.strip()})
        messages.append({"role": "assistant", "content": text})
        return messages

    def _build_messages_for_voicedesign(
        self, text: str, voice_description: str
    ) -> list:
        """音色设计：user 放音色描述，assistant 放合成文本"""
        return [
            {"role": "user", "content": voice_description},
            {"role": "assistant", "content": text},
        ]

    def _build_messages_for_voiceclone(self, text: str) -> list:
        """语音克隆：仅 assistant message，不传 user（文档建议避免风格指令）"""
        return [
            {"role": "assistant", "content": text},
        ]

    # ── 核心合成 ──────────────────────────────────────

    def synthesize(
        self,
        model: str,
        text: str,
        voice: str = "mimo_default",
        output_format: str = "wav",
        style_text: str = "",
        voice_description: str = "",
        voice_file_path: str = "",
    ) -> bytes:
        """调用 MiMo TTS API 合成语音

        Args:
            model: 模型名称
            text: 要合成的文本
            voice: 音色名称（仅 tts 模型有效）
            output_format: 输出音频格式（wav / mp3）
            style_text: 风格指令文本（仅 tts 模型）
            voice_description: 音色描述（仅 voicedesign 模型）
            voice_file_path: 参考音频路径（仅 voiceclone 模型）

        Returns:
            解码后的音频二进制数据

        Raises:
            MimoAPIError: API 调用失败
        """
        if not text or not text.strip():
            raise MimoAPIError("请输入要合成的文本")

        # ── 校验输出格式 ──
        fmt = output_format.lower()
        if fmt not in self.SUPPORTED_FORMATS:
            raise MimoAPIError(
                f"输出格式 '{output_format}' 可能不被 MiMo V2.5 支持，"
                f"请选择 wav 或 mp3"
            )

        # ── 构造 audio 参数 ──
        audio_params: dict = {"format": fmt}

        # ── 根据模型构造 ──
        if model == "mimo-v2.5-tts":
            audio_params["voice"] = voice
            messages = self._build_messages_for_tts(text, style_text)

        elif model == "mimo-v2.5-tts-voicedesign":
            if not voice_description or not voice_description.strip():
                raise MimoAPIError("音色设计模式需要填写音色描述")
            messages = self._build_messages_for_voicedesign(text, voice_description)

        elif model == "mimo-v2.5-tts-voiceclone":
            # voiceclone：audio.voice 必须是参考音频的 DataURL
            if voice_file_path:
                try:
                    with open(voice_file_path, "rb") as f:
                        audio_data = f.read()
                    ext = voice_file_path.rsplit(".", 1)[-1].lower()
                    mime = "audio/mpeg" if ext == "mp3" else "audio/wav"
                    audio_b64 = base64.b64encode(audio_data).decode("utf-8")
                    audio_params["voice"] = f"data:{mime};base64,{audio_b64}"
                except FileNotFoundError:
                    raise MimoAPIError(f"找不到参考音频文件: {voice_file_path}")
                except Exception as e:
                    raise MimoAPIError(f"读取参考音频文件失败: {e}")
            else:
                raise MimoAPIError("语音克隆模式需要选择参考音频文件")
            messages = self._build_messages_for_voiceclone(text)

        else:
            raise MimoAPIError(f"不支持的模型: {model}")

        # ── 发起请求 ──
        try:
            logger.info(
                "MiMo TTS 请求: model=%s, format=%s, text_len=%d, voice=%s",
                model, fmt, len(text),
                f"data_url({len(audio_params.get('voice',''))} bytes)" if model == "mimo-v2.5-tts-voiceclone" else (voice or "none"),
            )

            resp = self._client.chat.completions.create(
                model=model,
                modalities=["text", "audio"],
                audio=audio_params,
                messages=messages,
            )

        except AuthenticationError as e:
            raise MimoAPIError(
                "API Key 无效或已过期，请在「设置」中检查并更新", original=e
            )
        except RateLimitError as e:
            raise MimoAPIError("请求过于频繁，请稍后重试", original=e)
        except APITimeoutError as e:
            raise MimoAPIError(
                "请求超时，请检查网络连接或 API 地址是否正确", original=e
            )
        except APIError as e:
            status = getattr(e, "status_code", 0)
            body = getattr(e, "body", "") or str(e)

            if status == 400:
                logger.warning("MiMo 400 响应体: %s", body)
                raise MimoAPIError(
                    f"请求参数错误 (400)。请检查：\n"
                    f"  1. 模型名称是否正确\n"
                    f"  2. 输出格式是否支持（推荐 wav/mp3）\n"
                    f"  3. 音色名称是否存在\n"
                    f"  4. 参考音频格式是否正确\n\n"
                    f"服务端返回: {body[:300]}",
                    original=e, response_body=str(body),
                )
            elif status == 401:
                raise MimoAPIError(
                    "API Key 无效或已过期，请在「设置」中检查并更新", original=e
                )
            elif status == 402:
                raise MimoAPIError("账户余额不足，请充值后再试", original=e)
            elif status == 429:
                raise MimoAPIError("请求频率超限，请稍后重试", original=e)
            else:
                raise MimoAPIError(
                    f"API 请求失败 (HTTP {status}): {body[:200]}",
                    original=e, response_body=str(body),
                )
        except Exception as e:
            raise MimoAPIError(
                f"网络请求失败: {e}，请检查网络连接", original=e
            )

        # ── 解析音频数据 ──
        try:
            choice = resp.choices[0]

            # 可能是 reasoning_content 占了全部输出
            if not hasattr(choice.message, "audio") or choice.message.audio is None:
                text_content = getattr(choice.message, "content", None)
                reasoning = getattr(choice.message, "reasoning_content", None)
                detail = ""
                if reasoning:
                    detail = f" (模型返回了思考过程: {reasoning[:200]})"
                raise MimoAPIError(
                    f"响应中没有音频数据{detail}，可能是 max_tokens 太小或模型不支持当前参数",
                )

            audio_data_b64 = choice.message.audio.data
            if not audio_data_b64:
                raise MimoAPIError("响应中音频数据为空")

            audio_bytes = base64.b64decode(audio_data_b64)
            logger.info("MiMo TTS 成功: %d bytes, format=%s", len(audio_bytes), fmt)
            return audio_bytes

        except (AttributeError, KeyError, TypeError, ValueError) as e:
            raise MimoAPIError("音频数据解析失败，请重试", original=e)

    def update_credentials(self, api_key: str, base_url: str):
        """更新认证信息"""
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = OpenAI(api_key=api_key, base_url=self._base_url)
