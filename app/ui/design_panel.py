"""音色设计面板（mimo-v2.5-tts-voicedesign）"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QLabel, QGroupBox, QTextEdit,
)
from PySide6.QtCore import Qt, Signal


class DesignPanel(QWidget):
    """音色设计面板

    通过文本描述自定义音色，无需预设或音频样本。
    """

    textChanged = Signal(str)
    descriptionChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # 音色描述
        desc_group = QGroupBox("🎤 音色描述")
        desc_layout = QVBoxLayout(desc_group)

        desc_help = QLabel(
            "用自然语言描述您想要的音色特征（1-4句话即可）："
        )
        desc_help.setStyleSheet("font-weight: bold;")
        desc_layout.addWidget(desc_help)

        # 填写提示
        tips = QLabel(
            "💡 建议从以下维度描述：\n"
            "  • 性别与年龄：如「25岁左右的年轻女性」「50岁的中年男性」\n"
            "  • 声音质感：如「低沉沙哑」「丝滑醇厚」「清澈明亮」\n"
            "  • 情绪/语气：如「温暖自信」「温柔舒缓」「严肃沉稳」\n"
            "  • 语速/节奏：如「缓慢沉稳」「语速极快」\n"
            "  • 角色定位：如「深夜电台DJ」「纪录片旁白」「故事爷爷」\n\n"
            "⚠️ 避免矛盾描述，避免混响/回声等后期处理术语"
        )
        tips.setStyleSheet("color: #666; font-size: 11px; background: #f5f5f5; "
                          "padding: 8px; border-radius: 4px;")
        tips.setWordWrap(True)
        desc_layout.addWidget(tips)

        self._desc_edit = QPlainTextEdit()
        self._desc_edit.setPlaceholderText(
            "例如：一位慈祥的老年男性，说普通话带北方口音，"
            "语速缓慢而沉稳，声音略带沙哑和沧桑感，"
            "像一位老爷爷在讲故事，充满岁月的智慧。"
        )
        self._desc_edit.setMinimumHeight(120)
        self._desc_edit.textChanged.connect(self._on_desc_changed)
        desc_layout.addWidget(self._desc_edit)

        layout.addWidget(desc_group)

        # 合成文本
        text_group = QGroupBox("📝 合成文本")
        text_layout = QVBoxLayout(text_group)

        text_hint = QLabel(
            "💡 建议：合成文本的风格尽量与音色描述一致\n"
            "（温柔女声搭配晚安独白，而非激情体育解说）"
        )
        text_hint.setStyleSheet("color: #666; font-size: 11px;")
        text_hint.setWordWrap(True)
        text_layout.addWidget(text_hint)

        self._text_edit = QPlainTextEdit()
        self._text_edit.setPlaceholderText("输入要合成语音的文本...")
        self._text_edit.setMinimumHeight(150)
        self._text_edit.textChanged.connect(self._on_text_changed)
        text_layout.addWidget(self._text_edit)

        # 字数统计
        self._char_count = QLabel("字数: 0")
        self._char_count.setStyleSheet("color: gray; font-size: 11px;")
        self._char_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        text_layout.addWidget(self._char_count)

        layout.addWidget(text_group, 1)

    def _on_desc_changed(self):
        self.descriptionChanged.emit(self._desc_edit.toPlainText())

    def _on_text_changed(self):
        text = self._text_edit.toPlainText()
        self._char_count.setText(f"字数: {len(text)}")
        self.textChanged.emit(text)

    def get_description(self) -> str:
        return self._desc_edit.toPlainText()

    def set_description(self, desc: str):
        self._desc_edit.setPlainText(desc)

    def get_text(self) -> str:
        return self._text_edit.toPlainText()

    def set_text(self, text: str):
        self._text_edit.setPlainText(text)

    def clear(self):
        self._desc_edit.clear()
        self._text_edit.clear()
