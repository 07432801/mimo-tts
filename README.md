# MiMo TTS 语音合成桌面客户端

基于小米 MiMo TTS V2.5 API 的语音合成工具，支持 **桌面版** 和 **Web 版**。

- 🖥️ **桌面版**：PySide6 原生应用，支持 macOS / Windows
- 🌐 **Web 版**：浏览器直接使用，无需安装，托管在 GitHub Pages

## 功能特性

- **三种模型**：预置音色合成 / 音色设计 / 语音克隆
- **多种音色**：11种内置中英文音色（冰糖、茉莉、苏打、白桦、Mia、Chloe 等）
- **风格控制**：情感标签、方言（东北话/粤语/四川话）、唱歌模式、语速控制
- **音色设计**：通过自然语言描述自定义全新音色
- **语音克隆**：上传音频样本，精确克隆任意声音
- **输出格式**：wav / mp3
- **合成历史**：自动保存历史记录，支持回放和重新加载文本
- **配置持久化**：API Key / Base URL 自动保存

## Web 版（浏览器中使用）

无需安装任何软件，在浏览器中直接使用：

👉 **[在线体验](https://07432801.github.io/mimo-tts)**（部署后生效）

### 使用方式

1. 打开上方链接
2. 填入你的 MiMo API Key（在 [platform.xiaomimimo.com](https://platform.xiaomimimo.com) 获取）
3. 选择合成模式（预置音色合成 / 音色设计 / 语音克隆）
4. 输入文本，点击合成即可生成语音并播放/下载

> 🔑 API Key 仅存储在浏览器本地 localStorage，不会上传到任何第三方服务器。

### 功能对比

| 功能 | Web 版 | 桌面版 |
|------|--------|--------|
| 预置音色合成 | ✅ | ✅ |
| 音色设计 | ✅ | ✅ |
| 语音克隆 | ✅ | ✅ |
| 风格标签 | ✅ | ✅ |
| 音频播放与下载 | ✅ | ✅ |
| 离线/无网络使用 | ❌ | ✅ |
| 本地文件处理（ffmpeg 转换） | ❌ | ✅ |

### 部署方式

本项目使用 GitHub Actions 自动将 `web/` 目录部署到 GitHub Pages。
推送 `main` 分支后，此工作流自动执行。

---

## 安装方式（桌面版）

### Windows

> 以下操作需在 **Windows 环境** 执行

**方法一：Inno Setup 安装程序（推荐）**

1. 安装 [Python 3.9+](https://www.python.org/downloads/)（勾选 "Add Python to PATH"）
2. 双击 `windows\build.bat` — 自动构建可执行文件
3. 安装 [Inno Setup](https://jrsoftware.org/isdl.php)
4. 右键 `windows\installer.iss` → "Compile"
5. 在 `dist\` 得到 `MiMo-TTS_Setup_v1.0.0.exe`
6. 双击安装，自动完成

安装程序自动检测：
- ✅ VC++ Redistributable（Qt 必需）
- ✅ ffmpeg（首次启动自动下载）

**方法二：绿色版**

```batch
windows\build.bat
dist\MiMo-TTS\launcher.bat
```

启动器 `launcher.bat` 自动下载 ffmpeg。

### macOS

```bash
pip install PySide6 openai
python main.py
```

### 配置 API Key

启动后，点击菜单栏「设置 → API 配置」（或顶部的 ⚙️ 设置按钮）：
- 填入你的 MiMo API Key（在 https://platform.xiaomimimo.com 获取）
- 选择或输入 API Base URL
- 点击保存

## 使用方法

### 预置音色合成
1. 顶部选择模型「预置音色合成」
2. 选择音色和输出格式
3. 输入合成文本（可插入风格标签）
4. 可选：填写风格指令
5. 点击「合成并播放」

### 音色设计
1. 切换到「音色设计」模型
2. 在「音色描述」中描述想要的音色特征
3. 输入合成文本
4. 点击「合成并播放」

### 语音克隆
1. 切换到「语音克隆」模型
2. 点击「选择音频文件」上传参考音频
   - 原生支持 mp3 / wav 格式，直接使用
   - flac / ogg / m4a / aac / wma 等格式自动调用 **ffmpeg** 转换为 16kHz 单声道 wav
3. 输入合成文本
4. 点击「合成并播放」

> **ffmpeg 自动转换**：如果系统中已安装 ffmpeg，选择非标准格式时会自动转换；如果未安装，会提示选择 mp3/wav 文件。

## 打包为独立应用

### macOS

```bash
# 安装依赖
pip install PySide6 openai

# 运行
python main.py
```

### Windows

在 **Windows 环境** 执行：

```batch
pip install PySide6 openai pyinstaller
python -m PyInstaller --windowed --onedir --name "MiMo-TTS" ^
    --add-data "app/resources;app/resources" ^
    --hidden-import PySide6.QtMultimedia ^
    main.py
```

## API 文档

- 平台入口：https://platform.xiaomimimo.com
- Base URL（按量付费）：https://api.xiaomimimo.com/v1
- Token Plan 中国区：https://token-plan-cn.xiaomimimo.com/v1

## 项目结构

```
mimo-tts-app/
├── main.py                     # 桌面版应用入口
├── requirements.txt            # 桌面版依赖声明
├── README.md                   # 说明文档
├── LICENSE                     # MIT 开源许可证
├── .gitignore                  # Git 忽略规则
├── web/                        # Web 版（GitHub Pages）
│   └── index.html              # 单页 Web 应用
├── .github/workflows/
│   └── deploy-pages.yml        # Pages 自动部署
├── app/
│   ├── core/
│   │   ├── config.py           # 配置管理（API Key、URL 等）
│   │   ├── api_client.py       # MiMo API 封装
│   │   └── audio_manager.py    # 音频解码/播放/保存
│   ├── ui/
│   │   ├── main_window.py      # 主窗口
│   │   ├── tts_panel.py        # 预置音色合成面板
│   │   ├── design_panel.py     # 音色设计面板
│   │   ├── clone_panel.py      # 语音克隆面板
│   │   ├── style_bar.py        # 风格标签工具栏
│   │   ├── history_panel.py    # 合成历史面板
│   │   └── settings_dialog.py  # API 配置对话框
│   └── resources/
│       └── styles.qss          # Qt 样式表
```

## 注意事项

- **API Key**：请妥善保管，不要分享给他人
- **语音克隆**：参考音频建议 10-15 秒清晰人声，格式 mp3/wav，大小不超过 10MB
- **唱歌模式**：仅在「预置音色合成」模型下支持，文本开头加 (唱歌) 标签
- **音频标签**：风格标签可组合使用，如 (开心 语速加快)今天天气真好
