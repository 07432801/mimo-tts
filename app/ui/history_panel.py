"""合成历史记录面板"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QPushButton, QLabel, QMenu,
    QMessageBox, QSplitter,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from ..core.config import HISTORY_FILE

logger = logging.getLogger(__name__)

MAX_HISTORY = 200


class HistoryEntry:
    """单条历史记录"""

    def __init__(
        self,
        text: str,
        model: str,
        voice: str,
        fmt: str,
        timestamp: str = "",
        audio_path: str = "",
    ):
        self.text = text
        self.model = model
        self.voice = voice
        self.format = fmt
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.audio_path = audio_path

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "model": self.model,
            "voice": self.voice,
            "format": self.format,
            "timestamp": self.timestamp,
            "audio_path": self.audio_path,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "HistoryEntry":
        return cls(
            text=d.get("text", ""),
            model=d.get("model", ""),
            voice=d.get("voice", ""),
            fmt=d.get("format", ""),
            timestamp=d.get("timestamp", ""),
            audio_path=d.get("audio_path", ""),
        )

    def summary(self) -> str:
        """显示用摘要"""
        text_preview = self.text[:30].replace("\n", " ")
        if len(self.text) > 30:
            text_preview += "..."
        return f"[{self.timestamp}] {text_preview}"


class HistoryPanel(QWidget):
    """历史记录面板"""

    playRequested = Signal(object)  # HistoryEntry
    textLoaded = Signal(str)  # 加载文本到编辑器

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries: list[HistoryEntry] = []
        self.setup_ui()
        self.load_history()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题栏
        header = QHBoxLayout()
        title = QLabel("📋 合成历史")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        header.addWidget(title)
        header.addStretch()

        self._count_label = QLabel("0 条")
        self._count_label.setStyleSheet("color: gray;")
        header.addWidget(self._count_label)

        self._clear_btn = QPushButton("清空")
        self._clear_btn.setFixedWidth(60)
        self._clear_btn.setFixedHeight(24)
        self._clear_btn.clicked.connect(self.clear_history)
        header.addWidget(self._clear_btn)

        layout.addLayout(header)

        # 历史列表
        self._list = QListWidget()
        self._list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._show_context_menu)
        self._list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._list.setAlternatingRowColors(True)
        layout.addWidget(self._list)

    def add_entry(self, entry: HistoryEntry):
        """添加一条历史记录"""
        self._entries.insert(0, entry)
        if len(self._entries) > MAX_HISTORY:
            self._entries = self._entries[:MAX_HISTORY]
        self._refresh_list()
        self.save_history()

    def _refresh_list(self):
        self._list.clear()
        for entry in self._entries:
            item = QListWidgetItem(entry.summary())
            item.setData(Qt.ItemDataRole.UserRole, len(self._entries) - self._entries.index(entry) - 1)
            self._list.addItem(item)
        self._count_label.setText(f"{len(self._entries)} 条")

    def _show_context_menu(self, pos):
        item = self._list.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)
        play_action = menu.addAction("▶ 播放")
        load_text_action = menu.addAction("📝 加载文本到编辑器")
        menu.addSeparator()
        delete_action = menu.addAction("🗑 删除")

        action = menu.exec(self._list.mapToGlobal(pos))
        if action == play_action:
            self._on_play(item)
        elif action == load_text_action:
            self._on_load_text(item)
        elif action == delete_action:
            self._on_delete(item)

    def _on_item_double_clicked(self, item):
        self._on_play(item)

    def _on_play(self, item):
        idx = self._item_index(item)
        if idx is not None and 0 <= idx < len(self._entries):
            self.playRequested.emit(self._entries[idx])

    def _on_load_text(self, item):
        idx = self._item_index(item)
        if idx is not None and 0 <= idx < len(self._entries):
            self.textLoaded.emit(self._entries[idx].text)

    def _on_delete(self, item):
        idx = self._item_index(item)
        if idx is not None and 0 <= idx < len(self._entries):
            del self._entries[idx]
            self._refresh_list()
            self.save_history()

    def _item_index(self, item) -> Optional[int]:
        row = self._list.row(item)
        if 0 <= row < len(self._entries):
            return row
        return None

    def clear_history(self):
        if not self._entries:
            return
        reply = QMessageBox.question(
            self, "确认清空", "确定要清空所有合成历史吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._entries.clear()
            self._refresh_list()
            self.save_history()

    def save_history(self):
        """持久化历史记录到 JSON"""
        try:
            data = [e.to_dict() for e in self._entries]
            HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")

    def load_history(self):
        """从 JSON 加载历史记录"""
        if not HISTORY_FILE.exists():
            return
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._entries = [HistoryEntry.from_dict(d) for d in data]
            self._refresh_list()
        except Exception as e:
            logger.error(f"加载历史记录失败: {e}")
