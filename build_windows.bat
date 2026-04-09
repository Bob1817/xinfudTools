@echo off
echo ================================
echo HR 数据处理工具集 - Windows 打包脚本
echo ================================
echo.

REM 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

REM 安装依赖
echo [1/3] 安装依赖包...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [错误] 依赖包安装失败
    pause
    exit /b 1
)
echo     依赖包安装完成
echo.

REM 清理旧的构建文件
echo [2/3] 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec
echo     清理完成
echo.

REM 使用 PyInstaller 打包
echo [3/3] 使用 PyInstaller 打包...
pyinstaller --name="HR 数据处理工具" ^
    --windowed ^
    --onefile ^
    --icon=NONE ^
    --add-data "core;core" ^
    --add-data "ui;ui" ^
    --add-data "db;db" ^
    main.py
if errorlevel 1 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo.
echo ================================
echo 打包完成！
echo 可执行文件位置：dist\HR 数据处理工具.exe
echo ================================
pause
