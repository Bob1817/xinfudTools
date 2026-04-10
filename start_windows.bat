@echo off
chcp 65001 >nul
title HR 数据处理工具集
echo ==========================================
echo 正在启动 HR 数据处理工具集...
echo ==========================================
echo.

:: 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python 环境。
    echo 请先安装 Python 3.10 或更高版本。
    echo 下载地址：https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: 检查依赖包
echo [1/2] 检查依赖包...
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包 (首次运行可能需要一点时间)...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo [错误] 依赖包安装失败，请检查网络连接。
        pause
        exit /b 1
    )
)
echo     ✓ 依赖检查完成
echo.

:: 启动应用
echo [2/2] 启动应用程序...
echo.
python main.py

if errorlevel 1 (
    echo.
    echo [错误] 程序异常退出。请查看上方日志。
    pause
)
