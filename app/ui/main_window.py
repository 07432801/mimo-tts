"""主窗口 - 整合所有 UI 组件"""

import logging
import os
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QPushButton, QLabel, QStackedWidget,
    QSlider, QStatusBar, QMessageBox, QMenuBar,
    QMenu, QFileDialog, QToolBar, QSizePolicy,
    QFrame, QSplitter, QApplication,
)
from PySide6.QtCore import Qt, Signal, Slot, QUrl, QTimer
from PySide6.QtGui import QAction, QIcon, QFont

from ..core.config import ConfigManager, PRESET_VOICES, OUTPUT_FORMATS
from ..core.api_client import MimoTTSClient, MimoAPIError
from ..core.audio_manager import AudioManager

from .tts_panel import TTSPanel
from .design_panel import DesignPanel
from .clone_panel import ClonePanel
from .style_bar import StyleBar
from .history_panel import HistoryPanel, HistoryEntry
from .settings_dialog import SettingsDialog

logger = logging.getLogger(__name__)

MODEL_NAMES = {
    "mimo-v2.5-tts": "预置音色合成",
    "mimo-v2.5-tts-voicedesign": "音色设计",
    "mimo-v2.5-tts-voiceclone": "语音克隆",
}


class MainWindow(QMainWindow):
    """MiMo TTS 语音合成主窗口"""

    def __init__(self):
        super().__init__()
        self._config = ConfigManager()
        self._audio = AudioManager()
        self._api: MimoTTSClient | None = None
        self._last_audio_data: bytes | None = None
        self._last_audio_format: str = "wav"
        self._is_synthesizing = False

        self.setWindowTitle("MiMo TTS 语音合成")
        self.setMinimumSize(900, 700)
        self.resize(1100, 800)

        self._init_audio_callbacks()
        self._setup_ui()
        self._restore_last_state()
        self._init_api_client()

    def _init_audio_callbacks(self):
        self._audio.on("finished", self._on_playback_finished)
        self._audio.on("error", self._on_playback_error)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(8, 4, 8, 4)

        # 菜单栏
        self._setup_menu_bar()

        # 顶部工具栏（模型/音色/格式选择）
        self._setup_toolbar(main_layout)

        # 风格标签栏（仅 tts 模式显示）
        self._style_bar = StyleBar()
        self._style_bar.tagClicked.connect(self._on_style_tag_clicked)
        main_layout.addWidget(self._style_bar)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)

        # 主内容区域：左侧面板 + 右侧历史
        content_splitter = QSplitter(Qt.Orientation.Horizontal)

        # 面板栈
        self._stack = QStackedWidget()
        self._tts_panel = TTSPanel()
        self._design_panel = DesignPanel()
        self._clone_panel = ClonePanel()
        self._stack.addWidget(self._tts_panel)     # index 0
        self._stack.addWidget(self._design_panel)   # index 1
        self._stack.addWidget(self._clone_panel)    # index 2
        content_splitter.addWidget(self._stack)

        # 历史记录面板（右侧）
        self._history_panel = HistoryPanel()
        self._history_panel.playRequested.connect(self._on_history_play)
        self._history_panel.textLoaded.connect(self._on_history_load_text)
        content_splitter.addWidget(self._history_panel)

        # 设置比例 7:3
        content_splitter.setSizes([700, 300])
        content_splitter.setStretchFactor(0, 7)
        content_splitter.setStretchFactor(1, 3)

        main_layout.addWidget(content_splitter, 1)

        # 底部控制栏
        self._setup_controls(main_layout)

        # 状态栏
        self._status_bar = QStatusBar()
        self._status_label = QLabel("就绪")
        self._status_bar.addWidget(self._status_label, 1)
        self.setStatusBar(self._status_bar)

    def _setup_menu_bar(self):
        menu_bar = self.menuBar()

        # 文件菜单
        file_menu = menu_bar.addMenu("文件(&F)")
        save_action = QAction("保存音频(&S)...", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_audio)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction("退出(&Q)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 设置菜单
        settings_menu = menu_bar.addMenu("设置(&S)")
        api_action = QAction("API 配置(&A)...", self)
        api_action.setShortcut("Ctrl+P")
        api_action.triggered.connect(self._open_settings)
        settings_menu.addAction(api_action)

        # 帮助菜单
        help_menu = menu_bar.addMenu("帮助(&H)")
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self, parent_layout):
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 2, 0, 2)
        toolbar_layout.setSpacing(8)

        # 模型选择
        model_label = QLabel("模型:")
        model_label.setStyleSheet("font-weight: bold;")
        toolbar_layout.addWidget(model_label)

        self._model_combo = QComboBox()
        self._model_combo.setMinimumWidth(200)
        for model_id, display_name in MODEL_NAMES.items():
            self._model_combo.addItem(display_name, model_id)
        self._model_combo.currentIndexChanged.connect(self._on_model_changed)
        toolbar_layout.addWidget(self._model_combo)

        # 分隔线
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setFixedWidth(2)
        toolbar_layout.addWidget(sep1)

        # 音色选择
        voice_label = QLabel("音色:")
        voice_label.setStyleSheet("font-weight: bold;")
        toolbar_layout.addWidget(voice_label)

        self._voice_combo = QComboBox()
        self._voice_combo.setMinimumWidth(180)
        self._populate_voices()
        toolbar_layout.addWidget(self._voice_combo)

        # 分隔线
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setFixedWidth(2)
        toolbar_layout.addWidget(sep2)

        # 输出格式
        fmt_label = QLabel("格式:")
        fmt_label.setStyleSheet("font-weight: bold;")
        toolbar_layout.addWidget(fmt_label)

        self._format_combo = QComboBox()
        for fmt in OUTPUT_FORMATS:
            self._format_combo.addItem(fmt.upper(), fmt)
        self._format_combo.setMinimumWidth(80)
        toolbar_layout.addWidget(self._format_combo)

        toolbar_layout.addStretch()

        # 设置按钮
        self._settings_btn = QPushButton("⚙️ 设置")
        self._settings_btn.setFixedWidth(80)
        self._settings_btn.clicked.connect(self._open_settings)
        self._settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        toolbar_layout.addWidget(self._settings_btn)

        parent_layout.addWidget(toolbar)

    def _setup_controls(self, parent_layout):
        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(4, 4, 4, 4)
        controls_layout.setSpacing(8)

        # 合成按钮
        self._synthesize_btn = QPushButton("▶ 合成并播放")
        self._synthesize_btn.setFixedHeight(36)
        self._synthesize_btn.setMinimumWidth(140)
        self._synthesize_btn.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; "
            "border-radius: 6px; font-size: 14px; font-weight: bold; }"
            "QPushButton:hover { background-color: #1976D2; }"
            "QPushButton:disabled { background-color: #90CAF9; }"
        )
        self._synthesize_btn.clicked.connect(self._synthesize)
        self._synthesize_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        controls_layout.addWidget(self._synthesize_btn)

        # 停止按钮
        self._stop_btn = QPushButton("⏹ 停止")
        self._stop_btn.setFixedHeight(36)
        self._stop_btn.setMinimumWidth(80)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop_playback)
        self._stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        controls_layout.addWidget(self._stop_btn)

        # 保存按钮
        self._save_btn = QPushButton("💾 保存")
        self._save_btn.setFixedHeight(36)
        self._save_btn.setMinimumWidth(80)
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self._save_audio)
        self._save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        controls_layout.addWidget(self._save_btn)

        controls_layout.addStretch()

        # 音量
        vol_label = QLabel("🔊")
        controls_layout.addWidget(vol_label)

        self._volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(80)
        self._volume_slider.setFixedWidth(100)
        self._volume_slider.valueChanged.connect(self._on_volume_changed)
        controls_layout.addWidget(self._volume_slider)

        # 进度
        controls_layout.addStretch()
        self._progress_label = QLabel("")
        self._progress_label.setStyleSheet("color: gray;")
        controls_layout.addWidget(self._progress_label)

        parent_layout.addWidget(controls)

    def _populate_voices(self):
        """填充音色列表"""
        self._voice_combo.clear()
        voices = PRESET_VOICES.get("mimo-v2.5-tts", [])
        for voice_id, display in voices:
            self._voice_combo.addItem(display, voice_id)

    def _restore_last_state(self):
        """恢复上次使用的设置"""
        # 恢复模型
        last_model = self._config.last_model
        for i in range(self._model_combo.count()):
            if self._model_combo.itemData(i) == last_model:
                self._model_combo.setCurrentIndex(i)
                break

        # 恢复音色
        last_voice = self._config.last_voice
        for i in range(self._voice_combo.count()):
            if self._voice_combo.itemData(i) == last_voice:
                self._voice_combo.setCurrentIndex(i)
                break

        # 恢复格式
        last_fmt = self._config.last_format
        for i in range(self._format_combo.count()):
            if self._format_combo.itemData(i) == last_fmt:
                self._format_combo.setCurrentIndex(i)
                break

        # 音量
        self._volume_slider.setValue(80)
        self._audio.volume = 0.8

    def _init_api_client(self):
        """初始化 API 客户端"""
        if self._config.is_configured():
            try:
                self._api = MimoTTSClient(
                    self._config.api_key, self._config.base_url
                )
            except Exception as e:
                logger.error(f"初始化 API 客户端失败: {e}")

    def _on_model_changed(self, index):
        """模型切换时更新界面"""
        model_id = self._model_combo.itemData(index)

        # 切换面板
        if model_id == "mimo-v2.5-tts":
            self._stack.setCurrentIndex(0)
            self._voice_combo.setEnabled(True)
            self._style_bar.setVisible(True)
        elif model_id == "mimo-v2.5-tts-voicedesign":
            self._stack.setCurrentIndex(1)
            self._voice_combo.setEnabled(False)
            self._style_bar.setVisible(False)
        elif model_id == "mimo-v2.5-tts-voiceclone":
            self._stack.setCurrentIndex(2)
            self._voice_combo.setEnabled(False)
            self._style_bar.setVisible(False)

        # 保存配置
        self._config.last_model = model_id

    def _on_style_tag_clicked(self, tag: str):
        """风格标签点击，插入到当前活跃的面板"""
        # 只有在 tts 面板时才生效
        if self._stack.currentIndex() == 0:
            self._tts_panel.insert_tag(tag)

    def _on_volume_changed(self, value):
        self._audio.volume = value / 100.0

    @Slot()
    def _synthesize(self):
        """合成语音"""
        if self._is_synthesizing:
            return

        if not self._config.is_configured():
            reply = QMessageBox.question(
                self,
                "API Key 未配置",
                "请先在「设置」中配置 API Key。是否现在配置？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._open_settings()
            return

        # 刷新 API 客户端（确保使用最新配置）
        self._init_api_client()
        if not self._api:
            QMessageBox.warning(self, "错误", "API 客户端初始化失败，请检查配置")
            return

        model_id = self._model_combo.currentData()
        output_format = self._format_combo.currentData()

        # 根据模型获取参数
        if model_id == "mimo-v2.5-tts":
            text = self._tts_panel.get_text()
            style = self._tts_panel.get_style()
            voice = self._voice_combo.currentData()
        elif model_id == "mimo-v2.5-tts-voicedesign":
            text = self._design_panel.get_text()
            desc = self._design_panel.get_description()
            voice = self._voice_combo.currentData()  # API 要求传 voice
            style = ""
        else:  # voiceclone
            text = self._clone_panel.get_text()
            voice_file = self._clone_panel.get_file_path()
            voice = self._voice_combo.currentData()  # API 要求传 voice，不影响音色
            style = ""

        if not text or not text.strip():
            QMessageBox.warning(self, "提示", "请输入要合成的文本")
            return

        # 检查 voicedesign 的 voice_description
        if model_id == "mimo-v2.5-tts-voicedesign":
            if not desc or not desc.strip():
                QMessageBox.warning(self, "提示", "音色设计模式需要填写音色描述")
                return

        # 检查 voiceclone 的文件
        if model_id == "mimo-v2.5-tts-voiceclone":
            if not voice_file:
                QMessageBox.warning(self, "提示", "语音克隆模式需要选择参考音频文件")
                return

        # 开始合成
        self._set_synthesizing(True)
        self._status_label.setText("⏳ 正在合成语音...")

        # 使用 QTimer 让 UI 先刷新再执行网络请求
        QTimer.singleShot(50, lambda: self._do_synthesize(
            model_id, text, voice, output_format,
            style if model_id == "mimo-v2.5-tts" else "",
            desc if model_id == "mimo-v2.5-tts-voicedesign" else "",
            voice_file if model_id == "mimo-v2.5-tts-voiceclone" else "",
        ))

    def _do_synthesize(self, model, text, voice, fmt, style, desc, voice_file):
        """执行合成请求"""
        try:
            audio_bytes = self._api.synthesize(
                model=model,
                text=text,
                voice=voice,
                output_format=fmt,
                style_text=style,
                voice_description=desc,
                voice_file_path=voice_file,
            )

            self._last_audio_data = audio_bytes
            self._last_audio_format = fmt

            # 加载并播放
            self._audio.load_data(audio_bytes, fmt)
            self._audio.play()

            self._status_label.setText(f"✅ 合成完成（{len(audio_bytes)/1024:.0f} KB）")
            self._save_btn.setEnabled(True)
            self._stop_btn.setEnabled(True)

            # 保存历史记录
            voice_display = voice if model == "mimo-v2.5-tts" else ""
            entry = HistoryEntry(
                text=text,
                model=model,
                voice=voice_display,
                fmt=fmt,
            )
            self._history_panel.add_entry(entry)

            # 保存 API Key 和模型/音色/格式
            self._config.last_model = model
            if model == "mimo-v2.5-tts":
                self._config.last_voice = voice
            self._config.last_format = fmt

        except MimoAPIError as e:
            self._status_label.setText("❌ 合成失败")
            QMessageBox.warning(self, "合成失败", str(e))
        except Exception as e:
            self._status_label.setText("❌ 发生未知错误")
            QMessageBox.critical(self, "错误", f"发生未知错误：{e}")
        finally:
            self._set_synthesizing(False)

    def _set_synthesizing(self, is_syncing: bool):
        self._is_synthesizing = is_syncing
        self._synthesize_btn.setEnabled(not is_syncing)
        if is_syncing:
            self._synthesize_btn.setText("⏳ 合成中...")
        else:
            self._synthesize_btn.setText("▶ 合成并播放")

    def _stop_playback(self):
        self._audio.stop()
        self._stop_btn.setEnabled(False)
        self._status_label.setText("⏹ 已停止")
        self._progress_label.setText("")

    def _save_audio(self):
        """保存音频到文件"""
        if self._last_audio_data is None:
            QMessageBox.warning(self, "提示", "没有可保存的音频")
            return

        model_id = self._model_combo.currentData()
        ext_map = {"wav": ".wav", "mp3": ".mp3"}
        ext = ext_map.get(self._last_audio_format, ".wav")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"mimo_tts_{timestamp}{ext}"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存音频",
            default_name,
            f"音频文件 (*{ext});;所有文件 (*)",
        )
        if not file_path:
            return

        success = self._audio.save_bytes(self._last_audio_data, file_path)
        if success:
            self._status_label.setText(f"✅ 已保存: {os.path.basename(file_path)}")
        else:
            QMessageBox.warning(self, "保存失败", "文件保存失败，请检查路径权限")

    def _on_playback_finished(self):
        self._stop_btn.setEnabled(False)
        self._status_label.setText("▶ 播放完成")
        self._progress_label.setText("")

    def _on_playback_error(self, error_string):
        self._stop_btn.setEnabled(False)
        self._status_label.setText(f"❌ 播放错误: {error_string}")

    def _on_history_play(self, entry: HistoryEntry):
        """从历史记录播放（如果对应的音频数据还在缓存中，直接播放；
        否则提示用户重新合成）"""
        # 如果有当前合成的音频，直接播放
        if self._last_audio_data is not None:
            self._audio.play()
            self._stop_btn.setEnabled(True)
            self._status_label.setText("▶ 播放中...")
        else:
            QMessageBox.information(
                self, "提示",
                "当前没有缓存的音频数据，请重新合成。\n"
                "提示：将文本加载到编辑器后点击「合成并播放」。"
            )

    def _on_history_load_text(self, text: str):
        """将历史中的文本加载到当前面板"""
        model_id = self._model_combo.currentData()
        if model_id == "mimo-v2.5-tts":
            self._tts_panel.set_text(text)
            self._stack.setCurrentIndex(0)
        elif model_id == "mimo-v2.5-tts-voicedesign":
            self._design_panel.set_text(text)
            self._stack.setCurrentIndex(1)
        else:
            self._clone_panel.set_text(text)
            self._stack.setCurrentIndex(2)

    def _open_settings(self):
        """打开设置对话框"""
        dialog = SettingsDialog(self._config, self)
        dialog.configSaved.connect(self._on_config_saved)
        dialog.exec()

    def _on_config_saved(self):
        """配置保存后的回调"""
        self._init_api_client()
        self._status_label.setText("✅ 配置已更新")

    def _show_about(self):
        QMessageBox.about(
            self,
            "关于 MiMo TTS 语音合成",
            "<h3>MiMo TTS 语音合成 V1.0</h3>"
            "<p>基于小米 MiMo TTS V2.5 API 的桌面语音合成工具</p>"
            "<p>支持：</p>"
            "<ul>"
            "<li>预置音色合成（多种中英文音色）</li>"
            "<li>文本音色设计（自然语言描述自定义音色）</li>"
            "<li>语音克隆（上传音频样本克隆声音）</li>"
            "<li>风格控制（情感/方言/语速/唱歌等）</li>"
            "</ul>"
            "<p>API 文档：<a href='https://platform.xiaomimimo.com'>platform.xiaomimimo.com</a></p>",
        )

    def closeEvent(self, event):
        """窗口关闭事件"""
        self._audio.cleanup()
        self._clone_panel.cleanup()
        super().closeEvent(event)
