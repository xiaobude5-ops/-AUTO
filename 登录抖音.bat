@echo off
chcp 65001 >nul
title 几何星球AUTO — 抖音扫码登录

echo.
echo   ✦ 几何星球AUTO — 抖音扫码登录
echo   ════════════════════════════════════════
echo.

cd /d "%~dp0"
python login_douyin.py

echo.
pause
