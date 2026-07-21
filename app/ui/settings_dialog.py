"""API 配置对话框"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QPushButton, QLabel,
    QMessageBox, QGroupBox,
)
from PySide6.QtCore import Qt, Signal

from ..core.config import ConfigManager, PRESET_URLS


class SettingsDialog(QDialog):
    """API Key 和 Base URL 配置对话框"""

    configSaved = Signal()

    def __init__(self, config: ConfigManager, parent=None):
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("API 设置")
        self.setMinimumWidth(480)
        self.setModal(True)
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # API 设置组
        api_group = QGroupBox("API 配置")
        api_layout = QFormLayout(api_group)

        # API Key
        key_layout = QHBoxLayout()
        self._api_key_input = QLineEdit()
        self._api_key_input.setPlaceholderText("输入您的 MiMo API Key (sk-... 或 tp-...)")
        self._api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        key_layout.addWidget(self._api_key_input)

        self._toggle_key_btn = QPushButton("👁")
        self._toggle_key_btn.setFixedWidth(32)
        self._toggle_key_btn.setToolTip("显示/隐藏 API Key")
        self._toggle_key_btn.clicked.connect(self._toggle_api_key_visibility)
        key_layout.addWidget(self._toggle_key_btn)

        api_layout.addRow("API Key:", key_layout)

        # API 地址
        url_layout = QHBoxLayout()
        self._url_combo = QComboBox()
        self._url_combo.setEditable(True)
        self._url_combo.setPlaceholderText("选择或输入 API Base URL")
        for name, url in PRESET_URLS.items():
            self._url_combo.addItem(f"{name} — {url}", url)
        url_layout.addWidget(self._url_combo, 1)
        api_layout.addRow("Base URL:", url_layout)

        layout.addWidget(api_group)

        # 状态提示
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: gray;")
        layout.addWidget(self._status_label)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._save_btn = QPushButton("保存")
        self._save_btn.clicked.connect(self._on_save)
        self._save_btn.setFixedWidth(100)
        btn_layout.addWidget(self._save_btn)

        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.clicked.connect(self.reject)
        self._cancel_btn.setFixedWidth(100)
        btn_layout.addWidget(self._cancel_btn)

        layout.addLayout(btn_layout)

    def load_config(self):
        """加载当前配置到界面"""
        self._api_key_input.setText(self._config.api_key)

        current_url = self._config.base_url
        # 尝试匹配预设 URL
        found = False
        for i in range(self._url_combo.count()):
            url_data = self._url_combo.itemData(i)
            if url_data == current_url:
                self._url_combo.setCurrentIndex(i)
                found = True
                break
        if not found:
            self._url_combo.setEditText(current_url)

    def _toggle_api_key_visibility(self):
        """切换 API Key 的显示/隐藏"""
        if self._api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self._api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self._toggle_key_btn.setText("🙈")
        else:
            self._api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self._toggle_key_btn.setText("👁")

    def _on_save(self):
        """保存配置"""
        api_key = self._api_key_input.text().strip()
        # 获取 URL：优先使用 combo 的当前文本（如果是编辑模式）或 data
        url = self._url_combo.currentData() or self._url_combo.currentText().strip()
        # 如果 combo 文本和 data 不一致（用户编辑了），取编辑文本
        if self._url_combo.currentText().strip():
            # 检查是否包含预设名的格式 "xxx — url"
            text = self._url_combo.currentText().strip()
            if "—" in text:
                parts = text.split("—", 1)
                url = parts[-1].strip()
            else:
                url = text

        if not api_key:
            QMessageBox.warning(self, "提示", "请输入 API Key")
            return

        if not url:
            QMessageBox.warning(self, "提示", "请输入或选择 API Base URL")
            return

        self._config.api_key = api_key
        self._config.base_url = url
        self._status_label.setText("✅ 配置已保存")
        self._status_label.setStyleSheet("color: green;")
        self.configSaved.emit()
        self.accept()
