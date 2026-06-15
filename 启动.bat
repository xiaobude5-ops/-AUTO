@echo off
chcp 65001 >nul
title 几何星球AUTO

echo.
echo   ✦ 几何星球AUTO 启动中...
echo   ════════════════════════════════════════
echo.

:: 切换到脚本所在目录
cd /d "%~dp0"

:: 启动 Flask
python app.py

:: 如果异常退出，暂停以便查看错误
if %errorlevel% neq 0 (
    echo.
    echo   [错误] 系统异常退出
    pause
)
