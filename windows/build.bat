@echo off
chcp 65001 >nul
REM ============================================================
REM  MiMo TTS 语音合成 - Windows 构建脚本
REM  依赖: Python 3.9+, PyInstaller, Inno Setup (可选)
REM ============================================================

setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "DIST_DIR=%PROJECT_DIR%\dist"
set "BUILD_DIR=%PROJECT_DIR%\build"

echo ==========================================
echo   MiMo TTS 语音合成 - Windows 构建
echo ==========================================
echo.

REM ── Step 1: 检测 Python ──────────────────────────
echo [1/4] 检测 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   Python 未安装！正在尝试自动安装...
    REM 尝试使用 winget 安装 Python
    winget install Python.Python.3.12 >nul 2>&1
    if errorlevel 1 (
        echo   ❌ 自动安装失败，请手动安装 Python 3.9+
        echo   下载地址: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    echo   ✅ Python 已安装
) else (
    for /f "tokens=*" %%a in ('python --version') do echo   ✅ %%a
)

REM ── Step 2: 安装依赖 ─────────────────────────────
echo [2/4] 安装 Python 依赖...
pip install -r "%PROJECT_DIR%\requirements.txt" >nul 2>&1
pip install pyinstaller >nul 2>&1
echo   ✅ 依赖安装完成

REM ── Step 3: PyInstaller 构建 ─────────────────────
echo [3/4] PyInstaller 构建中...
cd /d "%PROJECT_DIR%"

REM 清理旧构建
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"

pyinstaller --windowed --onedir --name "MiMo-TTS" ^
    --add-data "app/resources;app/resources" ^
    --hidden-import PySide6.QtMultimedia ^
    --hidden-import openai ^
    --exclude-module PyQt5 ^
    --exclude-module tkinter ^
    --exclude-module matplotlib ^
    --exclude-module numpy ^
    --noconfirm ^
    main.py

if errorlevel 1 (
    echo   ❌ 构建失败
    pause
    exit /b 1
)
echo   ✅ PyInstaller 构建完成

REM ── Step 4: 准备安装包文件 ───────────────────────
echo [4/4] 准备安装包文件...

REM 复制启动器
copy "%SCRIPT_DIR%launcher.bat" "%DIST_DIR%\MiMo-TTS\launcher.bat" >nul

REM 复制环境安装脚本
copy "%SCRIPT_DIR%install_deps.bat" "%DIST_DIR%\install_deps.bat" >nul

echo   ✅ 安装包文件已准备

echo.
echo ==========================================
echo   🎉 构建完成！
echo.
echo   输出目录: %DIST_DIR%\MiMo-TTS\
echo   运行: %DIST_DIR%\MiMo-TTS\launcher.bat
echo.
echo   若要创建安装程序 (.exe):
echo   1. 安装 Inno Setup: https://jrsoftware.org/isdl.php
echo   2. 双击编译 windows/installer.iss
echo ==========================================
pause
