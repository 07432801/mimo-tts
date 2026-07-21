#!/usr/bin/env python3
"""MiMo TTS 语音合成 - 桌面客户端入口"""

import os
import sys
import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


def setup_logging():
    """配置日志输出"""
    log_dir = Path.home() / ".mimo-tts" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def load_styles(app: QApplication) -> str:
    """加载 QSS 样式表"""
    style_path = Path(__file__).parent / "app" / "resources" / "styles.qss"
    if style_path.exists():
        with open(style_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("启动 MiMo TTS 语音合成")

    # 启用高分屏缩放（在创建 QApplication 前设置环境变量）
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"

    app = QApplication(sys.argv)
    app.setApplicationName("MiMo TTS 语音合成")
    app.setOrganizationName("MiMo-TTS")
    app.setApplicationVersion("1.0.0")

    # 加载全局样式
    styles = load_styles(app)
    if styles:
        app.setStyleSheet(styles)

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
