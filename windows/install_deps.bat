@echo off
chcp 65001 >nul
title MiMo TTS - Install Dependencies
echo ==========================================
echo   MiMo TTS - Installing Dependencies
echo ==========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Python not found. Please install Python 3.9+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Install pip deps
echo [1/2] Installing Python packages...
pip install PySide6 openai
echo Done.

REM Check ffmpeg
echo [2/2] Checking ffmpeg...
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo ffmpeg not found. Audio conversion will not be available.
    echo To install: https://ffmpeg.org/download.html
)

echo.
echo ==========================================
echo  Setup complete! Run launcher.bat to start.
echo ==========================================
pause
