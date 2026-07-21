"""配置管理模块 - 持久化 API Key、Base URL 等设置"""

import json
import os
from pathlib import Path


CONFIG_DIR = Path.home() / ".mimo-tts"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "history.json"

DEFAULT_CONFIG = {
    "api_key": "",
    "base_url": "https://api.xiaomimimo.com/v1",
    "last_model": "mimo-v2.5-tts",
    "last_voice": "冰糖",
    "last_format": "wav",
}

PRESET_URLS = {
    "按量付费 (默认)": "https://api.xiaomimimo.com/v1",
    "Token Plan - 中国区": "https://token-plan-cn.xiaomimimo.com/v1",
    "Token Plan - 新加坡": "https://token-plan-sgp.xiaomimimo.com/v1",
    "Token Plan - 阿姆斯特丹": "https://token-plan-ams.xiaomimimo.com/v1",
}

PRESET_VOICES = {
    "mimo-v2.5-tts": [
        ("mimo_default", "默认 (智能选择)"),
        ("冰糖", "冰糖 - 中文女声"),
        ("茉莉", "茉莉 - 中文女声"),
        ("苏打", "苏打 - 中文男声"),
        ("白桦", "白桦 - 中文男声"),
        ("default_zh", "默认中文"),
        ("Mia", "Mia - 英文女声"),
        ("Chloe", "Chloe - 英文女声"),
        ("Milo", "Milo - 英文男声"),
        ("Dean", "Dean - 英文男声"),
        ("default_en", "默认英文"),
    ],
}

OUTPUT_FORMATS = ["wav", "mp3"]

STYLE_TAGS = [
    ("开心", "(开心)"),
    ("悲伤", "(悲伤)"),
    ("生气", "(生气)"),
    ("唱歌", "(唱歌)"),
    ("慵懒", "(慵懒)"),
    ("温柔", "(温柔)"),
    ("严肃", "(严肃)"),
    ("活泼", "(活泼)"),
    ("耳语", "(耳语)"),
    ("东北话", "(东北话)"),
    ("粤语", "(粤语)"),
    ("四川话", "(四川话)"),
    ("语速加快", "(语速加快)"),
    ("语速减慢", "(语速减慢)"),
    ("深呼吸", "[audio:深呼吸]"),
    ("叹气", "[audio:叹气]"),
    ("微笑", "[audio:微笑]"),
    ("大笑", "[audio:大笑]"),
]


class ConfigManager:
    """管理应用配置的读写"""

    def __init__(self):
        self._config = dict(DEFAULT_CONFIG)
        self._ensure_dir()
        self.read()

    def _ensure_dir(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def read(self) -> dict:
        """读取配置文件，缺失字段用默认值填充"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    if k not in loaded:
                        loaded[k] = v
                self._config = loaded
            except (json.JSONDecodeError, IOError):
                self._config = dict(DEFAULT_CONFIG)
        else:
            self._config = dict(DEFAULT_CONFIG)
        return self._config

    def save(self):
        """保存配置到文件"""
        self._ensure_dir()
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default=None):
        return self._config.get(key, default)

    def set(self, key: str, value):
        self._config[key] = value
        self.save()

    @property
    def api_key(self) -> str:
        return self._config.get("api_key", "")

    @api_key.setter
    def api_key(self, value: str):
        self._config["api_key"] = value
        self.save()

    @property
    def base_url(self) -> str:
        return self._config.get("base_url", DEFAULT_CONFIG["base_url"])

    @base_url.setter
    def base_url(self, value: str):
        self._config["base_url"] = value
        self.save()

    @property
    def last_model(self) -> str:
        return self._config.get("last_model", "mimo-v2.5-tts")

    @last_model.setter
    def last_model(self, value: str):
        self._config["last_model"] = value
        self.save()

    @property
    def last_voice(self) -> str:
        return self._config.get("last_voice", "冰糖")

    @last_voice.setter
    def last_voice(self, value: str):
        self._config["last_voice"] = value
        self.save()

    @property
    def last_format(self) -> str:
        return self._config.get("last_format", "wav")

    @last_format.setter
    def last_format(self, value: str):
        self._config["last_format"] = value
        self.save()

    def is_configured(self) -> bool:
        """检查是否已配置 API Key"""
        return bool(self._config.get("api_key", "").strip())
