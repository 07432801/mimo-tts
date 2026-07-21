"""语音克隆面板（mimo-v2.5-tts-voiceclone）

支持自动用 ffmpeg 转换非标准格式音频为 wav。
"""

import os
import subprocess
import tempfile
import logging
import shutil
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QLabel, QPushButton, QGroupBox, QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal

logger = logging.getLogger(__name__)


class ClonePanel(QWidget):
    """语音克隆面板

    通过上传音频样本来克隆声音。
    支持 ffmpeg 自动转换非标准格式（flac / ogg / m4a / aac / wma 等）为 wav。
    """

    textChanged = Signal(str)
    fileSelected = Signal(str)

    # 原生支持的格式（API 端可直接接收）
    NATIVE_EXTENSIONS = {".mp3", ".wav"}
    # 所有可接受的输入格式（不在此列表中的也会尝试用 ffmpeg 转换）
    KNOWN_AUDIO_EXTENSIONS = {
        ".mp3", ".wav", ".wave",
        ".flac", ".ogg", ".oga",
        ".m4a", ".aac", ".wma",
        ".opus", ".webm",
        ".aiff", ".aif", ".aifc",
        ".caf", ".amr",
    }
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB（最终用于上传的文件）

    def __init__(self, parent=None):
        super().__init__(parent)
        self._file_path = ""           # 当前有效文件路径（可能是转换后的临时文件）
        self._original_path = ""       # 用户选择的原始文件路径
        self._converted = False        # 是否经过了 ffmpeg 转换
        self._temp_dir = None          # 转换临时目录
        self._ffmpeg_checked = False   # 是否已检测过 ffmpeg
        self._ffmpeg_available = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # 参考音频
        file_group = QGroupBox("🎤 参考音频")
        file_layout = QVBoxLayout(file_group)

        file_hint = QLabel(
            "上传一段清晰人声作为克隆参考（建议 10-15 秒，最终文件 ≤10MB）\n"
            "支持 mp3 / wav / flac / ogg / m4a / aac / wma 等常见格式，非标准格式自动用 ffmpeg 转换"
        )
        file_hint.setStyleSheet("color: #666; font-size: 11px;")
        file_hint.setWordWrap(True)
        file_layout.addWidget(file_hint)

        file_btn_layout = QHBoxLayout()
        self._select_btn = QPushButton("📂 选择音频文件")
        self._select_btn.clicked.connect(self._select_file)
        self._select_btn.setFixedWidth(140)
        file_btn_layout.addWidget(self._select_btn)

        self._file_info = QLabel("未选择文件")
        self._file_info.setStyleSheet("color: gray;")
        file_btn_layout.addWidget(self._file_info, 1)

        file_layout.addLayout(file_btn_layout)

        self._file_status = QLabel("")
        file_layout.addWidget(self._file_status)

        layout.addWidget(file_group)

        # 合成文本
        text_group = QGroupBox("📝 合成文本")
        text_layout = QVBoxLayout(text_group)

        text_hint = QLabel(
            "💡 注意：\n"
            "  • 语音克隆模式下不建议添加风格指令，参考音频本身已包含音色信息\n"
            "  • 风格标签不能放在文本开头或末尾，只能放在中间位置"
        )
        text_hint.setStyleSheet("color: #666; font-size: 11px;")
        text_hint.setWordWrap(True)
        text_layout.addWidget(text_hint)

        self._text_edit = QPlainTextEdit()
        self._text_edit.setPlaceholderText("输入要合成语音的文本...")
        self._text_edit.setMinimumHeight(200)
        self._text_edit.textChanged.connect(self._on_text_changed)
        text_layout.addWidget(self._text_edit)

        # 字数统计
        self._char_count = QLabel("字数: 0")
        self._char_count.setStyleSheet("color: gray; font-size: 11px;")
        self._char_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        text_layout.addWidget(self._char_count)

        layout.addWidget(text_group, 1)

    def _on_text_changed(self):
        text = self._text_edit.toPlainText()
        self._char_count.setText(f"字数: {len(text)}")
        self.textChanged.emit(text)

    # ── ffmpeg 检测 ──────────────────────────────────────

    def _check_ffmpeg(self) -> bool:
        """检测 ffmpeg 是否可用"""
        if self._ffmpeg_checked:
            return self._ffmpeg_available
        self._ffmpeg_checked = True
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True, timeout=5,
            )
            self._ffmpeg_available = True
        except (FileNotFoundError, subprocess.SubprocessError):
            self._ffmpeg_available = False
        return self._ffmpeg_available

    # ── 文件选择 ─────────────────────────────────────────

    def _build_filter(self) -> str:
        """构建文件选择对话框的过滤器"""
        parts = [
            "所有音频文件 (*.mp3 *.wav *.flac *.ogg *.m4a *.aac *.wma *.opus *.aiff)",
            "MP3 (*.mp3)",
            "WAV (*.wav)",
            "FLAC (*.flac)",
            "OGG (*.ogg *.oga)",
            "M4A / AAC (*.m4a *.aac)",
            "WMA (*.wma)",
            "其他音频 (*.opus *.webm *.aiff *.aif *.caf *.amr)",
            "所有文件 (*)",
        ]
        return ";;".join(parts)

    def _select_file(self):
        """打开文件选择对话框，自动转换非标准格式"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择参考音频",
            "",
            self._build_filter(),
        )
        if not file_path:
            return

        self._original_path = file_path
        ext = os.path.splitext(file_path)[1].lower()
        fname = os.path.basename(file_path)

        # ── 大小检查（原始文件） ──
        raw_size = os.path.getsize(file_path)
        if raw_size > self.MAX_FILE_SIZE:
            mb = raw_size / (1024 * 1024)
            QMessageBox.warning(
                self, "文件过大",
                f"文件大小为 {mb:.1f}MB，超过 10MB 限制，请选择更短的音频"
            )
            return

        # ── 原生支持的格式，直接使用 ──
        if ext in self.NATIVE_EXTENSIONS:
            self._converted = False
            self._file_path = file_path
            size_kb = raw_size / 1024
            self._file_info.setText(f"{fname} ({size_kb:.0f} KB)")
            self._file_status.setText("✅ 文件已选择")
            self._file_status.setStyleSheet("color: green;")
            self.fileSelected.emit(file_path)
            return

        # ── 非原生格式：尝试 ffmpeg 转换 ──
        if not self._check_ffmpeg():
            reply = QMessageBox.question(
                self, "需要 ffmpeg",
                f"格式 {ext} 需要 ffmpeg 才能转换为支持的格式。\n\n"
                "是否改用「所有文件 (*)」过滤器选择 mp3/wav 文件？\n"
                "（选择「否」可尝试直接发送原始文件）",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                return  # 让用户重新选择
            # 用户选择直接发送，试试看 API 能不能处理
            self._converted = False
            self._file_path = file_path
            size_kb = raw_size / 1024
            self._file_info.setText(f"{fname} ({size_kb:.0f} KB) ⚠️ 未转换")
            self._file_status.setText(
                "⚠️ 未检测到 ffmpeg，已使用原始文件（API 可能不支持此格式）"
            )
            self._file_status.setStyleSheet("color: orange;")
            self.fileSelected.emit(file_path)
            return

        # ── 执行转换 ──
        self._file_status.setText("⏳ 正在转换音频格式...")
        self._file_status.setStyleSheet("color: #2196F3;")
        # 让 Qt 事件循环先刷新 UI
        from PySide6.QtCore import QCoreApplication
        QCoreApplication.processEvents()

        success, result_path = self._convert_to_wav(file_path)
        if not success:
            self._file_status.setText("")
            QMessageBox.warning(
                self, "转换失败",
                f"ffmpeg 转换失败：{result_path}\n\n"
                "请选择 mp3 或 wav 格式的音频文件。"
            )
            return

        # ── 检查转换后文件大小 ──
        conv_size = os.path.getsize(result_path)
        if conv_size > self.MAX_FILE_SIZE:
            mb = conv_size / (1024 * 1024)
            os.unlink(result_path)
            QMessageBox.warning(
                self, "文件过大",
                f"转换后的音频大小为 {mb:.1f}MB，超过 10MB 限制。\n"
                "请选择更短的音频文件。"
            )
            return

        self._converted = True
        self._file_path = result_path
        conv_size_kb = conv_size / 1024
        display_name = os.path.basename(result_path)
        self._file_info.setText(
            f"{fname} → {display_name} ({conv_size_kb:.0f} KB)"
        )
        self._file_status.setText("✅ 已转换并加载")
        self._file_status.setStyleSheet("color: green;")
        self.fileSelected.emit(result_path)

    # ── ffmpeg 转换 ──────────────────────────────────────

    def _convert_to_wav(self, src_path: str) -> tuple[bool, str]:
        """用 ffmpeg 将任意音频转为 16kHz 单声道 wav（适合语音克隆）"""
        try:
            if self._temp_dir is None:
                self._temp_dir = tempfile.mkdtemp(prefix="mimo_clone_")

            dst_path = os.path.join(
                self._temp_dir,
                "converted_voice.wav",
            )

            # ffmpeg 参数：
            #   -y           覆盖输出文件
            #   -i <src>     输入文件
            #   -ar 16000    采样率 16kHz（语音克隆最佳）
            #   -ac 1        单声道
            #   -sample_fmt s16  16-bit PCM
            #   -vn          丢弃视频流（如果有）
            result = subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", src_path,
                    "-ar", "16000",
                    "-ac", "1",
                    "-sample_fmt", "s16",
                    "-vn",
                    dst_path,
                ],
                capture_output=True,
                timeout=120,
            )

            if result.returncode != 0:
                stderr = result.stderr.decode("utf-8", errors="replace")[:300]
                return False, stderr

            if not os.path.exists(dst_path) or os.path.getsize(dst_path) == 0:
                return False, "输出文件为空"

            return True, dst_path

        except subprocess.TimeoutExpired:
            return False, "转换超时（>120秒）"
        except FileNotFoundError:
            return False, "找不到 ffmpeg 可执行文件"
        except Exception as e:
            return False, str(e)

    # ── 对外接口 ─────────────────────────────────────────

    def get_file_path(self) -> str:
        return self._file_path

    def get_text(self) -> str:
        return self._text_edit.toPlainText()

    def set_text(self, text: str):
        self._text_edit.setPlainText(text)

    def clear(self):
        """清空选择并清理临时文件"""
        self._cleanup_temp()
        self._file_path = ""
        self._original_path = ""
        self._converted = False
        self._file_info.setText("未选择文件")
        self._file_status.setText("")
        self._text_edit.clear()

    def _cleanup_temp(self):
        """清理转换产生的临时目录"""
        if self._temp_dir and os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            except Exception as e:
                logger.warning(f"清理临时目录失败: {e}")
        self._temp_dir = None

    def cleanup(self):
        """释放资源（窗口关闭时调用）"""
        self._cleanup_temp()
