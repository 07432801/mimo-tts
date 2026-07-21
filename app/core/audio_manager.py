"""音频管理模块 - 解码、播放、保存"""

import base64
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QUrl, QByteArray, QBuffer, QIODevice
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

logger = logging.getLogger(__name__)

# 格式名 → MIME type 映射
FORMAT_MIME = {
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
}

# 格式名 → 文件扩展名
FORMAT_EXT = {
    "wav": ".wav",
    "mp3": ".mp3",
}


class AudioManager:
    """管理音频数据的解码、播放和保存"""

    def __init__(self):
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)
        self._player.mediaStatusChanged.connect(self._on_status_changed)
        self._player.errorOccurred.connect(self._on_error)
        self._current_data: Optional[bytes] = None
        self._current_format: str = "wav"
        self._temp_file: Optional[str] = None
        self._volume: float = 1.0

        # 信号代理
        self._callbacks = {
            "finished": [],
            "error": [],
            "position_changed": [],
        }

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = max(0.0, min(1.0, value))
        self._audio_output.setVolume(self._volume)

    def on(self, event: str, callback):
        """注册事件回调"""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _on_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            for cb in self._callbacks["finished"]:
                cb()

    def _on_error(self, error, error_string):
        logger.error(f"播放错误: {error_string}")
        for cb in self._callbacks["error"]:
            cb(error_string)

    def decode_base64(self, b64_str: str) -> bytes:
        """解码 Base64 音频数据"""
        return base64.b64decode(b64_str)

    def load_data(self, audio_data: bytes, fmt: str = "wav"):
        """加载音频数据到播放器"""
        self._current_data = audio_data
        self._current_format = fmt
        self._cleanup_temp()

        # 将 bytes 写入临时文件，QMediaPlayer 需要文件路径或 URL
        ext = FORMAT_EXT.get(fmt, ".wav")
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        tmp.write(audio_data)
        tmp.flush()
        tmp.close()
        self._temp_file = tmp.name

        self._player.setSource(QUrl.fromLocalFile(self._temp_file))

    def play(self):
        """开始播放"""
        if self._player.source().isEmpty():
            return
        self._player.play()

    def stop(self):
        """停止播放"""
        self._player.stop()

    def pause(self):
        """暂停播放"""
        self._player.pause()

    @property
    def is_playing(self) -> bool:
        return self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    @property
    def duration(self) -> int:
        return self._player.duration()

    @property
    def position(self) -> int:
        return self._player.position()

    def seek(self, position_ms: int):
        self._player.setPosition(position_ms)

    def save(self, filepath: str) -> bool:
        """保存当前音频数据到文件"""
        if self._current_data is None:
            return False
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "wb") as f:
                f.write(self._current_data)
            logger.info(f"音频已保存: {filepath}")
            return True
        except IOError as e:
            logger.error(f"保存失败: {e}")
            return False

    def save_bytes(self, audio_data: bytes, filepath: str) -> bool:
        """保存任意音频字节到文件"""
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "wb") as f:
                f.write(audio_data)
            logger.info(f"音频已保存: {filepath}")
            return True
        except IOError as e:
            logger.error(f"保存失败: {e}")
            return False

    def _cleanup_temp(self):
        """清理临时文件"""
        if self._temp_file and os.path.exists(self._temp_file):
            try:
                os.unlink(self._temp_file)
            except OSError:
                pass
        self._temp_file = None

    def get_format_info(self, fmt: str) -> str:
        """获取格式对应的 MIME 类型"""
        return FORMAT_MIME.get(fmt, "audio/wav")

    def cleanup(self):
        """释放资源"""
        self.stop()
        self._cleanup_temp()
