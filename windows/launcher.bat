@echo off
chcp 65001 >nul
title MiMo TTS
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "BINARY=%SCRIPT_DIR%MiMo-TTS.exe"
set "FFMPEG_DIR=%SCRIPT_DIR%ffmpeg"
echo [MiMo TTS] 检测环境...
where ffmpeg >nul 2>&1
if not errorlevel 1 goto LAUNCH
if exist "%FFMPEG_DIR%\bin\ffmpeg.exe" (
    set "PATH=%FFMPEG_DIR%\bin;%PATH%"
    goto LAUNCH
)
echo [..] 正在下载 ffmpeg...
set "FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
set "FFMPEG_ZIP=%TEMP%\ffmpeg.zip"
powershell -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%FFMPEG_URL%' -OutFile '%FFMPEG_ZIP%' -UseBasicParsing"
if errorlevel 1 goto LAUNCH
powershell -Command "Add-Type -AssemblyName System.IO.Compression.FileSystem; [IO.Compression.ZipFile]::ExtractToDirectory('%FFMPEG_ZIP%', '%TEMP%\ffmpeg_extract')"
for /d %%d in ("%TEMP%\ffmpeg_extract\*") do (
    if exist "%%d\bin\ffmpeg.exe" (
        mkdir "%FFMPEG_DIR%\bin" 2>nul
        copy "%%d\bin\ffmpeg.exe" "%FFMPEG_DIR%\bin\" >nul
        copy "%%d\bin\ffprobe.exe" "%FFMPEG_DIR%\bin\" >nul
        set "PATH=%FFMPEG_DIR%\bin;%PATH%"
    )
)
del "%FFMPEG_ZIP%" 2>nul
rmdir /s /q "%TEMP%\ffmpeg_extract" 2>nul
:LAUNCH
if exist "%BINARY%" (
    start "" "%BINARY%" %*
) else (
    echo [ERR] 找不到主程序，请重新安装
    pause
)
