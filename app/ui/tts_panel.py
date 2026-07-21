"""基础 TTS 合成面板（mimo-v2.5-tts）"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QLabel, QLineEdit, QGroupBox,
)
from PySide6.QtCore import Qt, Signal


class TTSPanel(QWidget):
    """预置音色合成面板

    提供文本输入、风格指令输入，配合 StyleBar 实现标签插入。
    """

    textChanged = Signal(str)
    styleChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # 风格指令
        style_group = QGroupBox("🎯 风格指令（可选）")
        style_layout = QVBoxLayout(style_group)

        style_desc = QLabel(
            "用自然语言描述期望的语速、情感、角色等效果，"
            "也可在下方文本中直接插入风格标签"
        )
        style_desc.setStyleSheet("color: #666; font-size: 11px;")
        style_desc.setWordWrap(True)
        style_layout.addWidget(style_desc)

        self._style_input = QLineEdit()
        self._style_input.setPlaceholderText(
            "例如：用欢快的语气，语速稍快 / 严肃的新闻播报 / 慵懒的，刚睡醒的感觉"
        )
        self._style_input.textChanged.connect(self.styleChanged.emit)
        style_layout.addWidget(self._style_input)

        layout.addWidget(style_group)

        # 合成文本
        text_group = QGroupBox("📝 合成文本")
        text_layout = QVBoxLayout(text_group)

        self._text_edit = QPlainTextEdit()
        self._text_edit.setPlaceholderText(
            "在此输入要合成语音的文本内容...\n\n"
            "💡 技巧：可在文本中插入风格标签，例如：\n"
            "  (开心)今天天气真好！\n"
            "  (东北话)哎呀妈呀，今儿太冷了！\n"
            "  (唱歌)歌词内容在这里"
        )
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

    def insert_tag(self, tag: str):
        """在当前光标位置插入标签"""
        cursor = self._text_edit.textCursor()
        cursor.insertText(tag)
        self._text_edit.setTextCursor(cursor)
        self._text_edit.setFocus()

    def get_text(self) -> str:
        return self._text_edit.toPlainText()

    def set_text(self, text: str):
        self._text_edit.setPlainText(text)

    def get_style(self) -> str:
        return self._style_input.text()

    def set_style(self, style: str):
        self._style_input.setText(style)

    def clear(self):
        self._text_edit.clear()
        self._style_input.clear()
