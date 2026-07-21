"""风格标签快速插入工具栏"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QScrollArea,
    QSizePolicy, QToolTip, QFrame,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..core.config import STYLE_TAGS


class StyleTagButton(QPushButton):
    """单个风格标签按钮"""

    def __init__(self, label: str, tag: str, parent=None):
        super().__init__(label, parent)
        self._tag = tag
        self.setToolTip(f"插入标签: {tag}")
        self.setFixedHeight(28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        font = self.font()
        font.setPointSize(10)
        self.setFont(font)

    def tag(self) -> str:
        return self._tag


class StyleBar(QWidget):
    """风格标签快捷插入工具栏

    将点击的标签文本通过 signal 发送，由外部插入到文本编辑框。
    """

    tagClicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        # "风格标签:" 标签
        label = QPushButton("🎭 标签")
        label.setFlat(True)
        label.setEnabled(False)
        label.setFixedWidth(60)
        font = label.font()
        font.setPointSize(10)
        label.setFont(font)
        layout.addWidget(label)

        # 可滚动的按钮区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(4)

        for label_text, tag_text in STYLE_TAGS:
            btn = StyleTagButton(label_text, tag_text)
            btn.clicked.connect(self._on_btn_clicked)
            btn_layout.addWidget(btn)

        btn_layout.addStretch()
        scroll.setWidget(btn_container)
        layout.addWidget(scroll, 1)

    def _on_btn_clicked(self):
        btn = self.sender()
        if isinstance(btn, StyleTagButton):
            self.tagClicked.emit(btn.tag())
