@echo off
chcp 65001 >nul
title 几何星球AUTO — 安装

echo.
echo   ✦ 几何星球AUTO — 一键安装
echo   ════════════════════════════════════════
echo.

:: ── 检查 Python ──
echo [1/4] 检查 Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [错误] 未检测到 Python，请先安装 Python 3.10+
    echo   下载地址: https://www.python.org/downloads/
    echo   安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)
python --version
echo   OK
echo.

:: ── 安装依赖 ──
echo [2/4] 安装 Python 依赖...
pip install flask playwright openpyxl werkzeug -q
if %errorlevel% neq 0 (
    echo   [错误] pip 安装失败，请检查网络连接
    pause
    exit /b 1
)
echo   OK
echo.

:: ── 安装 Chromium ──
echo [3/4] 安装 Playwright Chromium 浏览器（约 150MB，首次需下载）...
python -m playwright install chromium
if %errorlevel% neq 0 (
    echo   [警告] Chromium 安装失败，抓取功能可能不可用
    echo   手动安装: python -m playwright install chromium
)
echo   OK
echo.

:: ── 初始化 ──
echo [4/5] 初始化数据库 + 创建快捷方式...
python -c "from database import init_db, create_user; from auth import hash_password; init_db(); users=__import__('database').get_all_users(); [create_user('admin',hash_password('admin'),'管理员','admin') for _ in [0] if not any(u['username']=='admin' for u in users)]"
echo   OK
echo.

:: ── 抖音登录 ──
echo [5/5] 抖音首次登录（仅需此一次）
echo   即将打开浏览器，请用抖音 APP 扫码登录
echo   登录完成后关闭浏览器窗口即可
pause
python login_douyin.py
echo.

:: ── 创建桌面快捷方式 ──
set "desktop=%USERPROFILE%\Desktop"
set "shortcut=%desktop%\几何星球AUTO.url"
(
echo [InternetShortcut]
echo URL=file:///%~dp0启动.bat
echo Icon=%~dp0static\favicon.ico
echo IconIndex=0
) > "%shortcut%"
echo   桌面快捷方式已创建
echo.

echo   ════════════════════════════════════════
echo   ✦ 安装完成！
echo.
echo   默认管理员账号: admin / admin
echo   请尽快登录修改密码！
echo.
echo   现在启动系统...
echo   ════════════════════════════════════════
timeout /t 3 >nul
start "" "%~dp0启动.bat"
