@echo off
chcp 65001 >nul
echo ==========================================
echo HR 数据处理工具集 - Windows EXE 打包脚本
echo ==========================================
echo.

:: 获取版本号
for /f "delims=" %%i in ('python -c "from core.version import get_version; print(get_version())" 2^>nul') do set VERSION=%%i
if "%VERSION%"=="" set VERSION=1.0.0

set APP_NAME=HR数据处理工具集
set EXE_NAME=%APP_NAME%-v%VERSION%-windows.exe

echo [版本] v%VERSION%
echo.

:: [1/4] 检查 Python 环境
echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python
    pause
    exit /b 1
)
echo     ✓ Python 环境正常
echo.

:: [2/4] 安装依赖
echo [2/4] 安装依赖包...
pip install -r requirements.txt -q
pip install pyinstaller -q
if errorlevel 1 (
    echo [错误] 依赖包安装失败
    pause
    exit /b 1
)
echo     ✓ 依赖包安装成功
echo.

:: [3/4] 打包 EXE
echo [3/4] 开始打包 EXE...
pyinstaller --clean --noconfirm ^
    --name="%APP_NAME%" ^
    --onedir ^
    --windowed ^
    --add-data="core;core" ^
    --add-data="ui;ui" ^
    --add-data="db;db" ^
    --hidden-import="PyQt6" ^
    --hidden-import="PyQt6.QtCore" ^
    --hidden-import="PyQt6.QtGui" ^
    --hidden-import="PyQt6.QtWidgets" ^
    --hidden-import="qfluentwidgets" ^
    --hidden-import="pandas" ^
    --hidden-import="openpyxl" ^
    main.py

if not exist "dist\%APP_NAME%\%APP_NAME%.exe" (
    echo [错误] EXE 打包失败
    pause
    exit /b 1
)
echo     ✓ EXE 打包成功
echo.

:: [4/4] 创建安装程序
echo [4/4] 创建安装程序...

:: 检查是否安装了 Inno Setup
set INNO_SETUP=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set INNO_SETUP="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set INNO_SETUP="C:\Program Files\Inno Setup 6\ISCC.exe"
)

if defined INNO_SETUP (
    echo     使用 Inno Setup 创建安装程序...
    
    :: 创建 Inno Setup 脚本
    (
        echo [Setup]
        echo AppName=%APP_NAME%
        echo AppVersion=%VERSION%
        echo DefaultDirName={autopf}\%APP_NAME%
        echo DefaultGroupName=%APP_NAME%
        echo OutputDir=dist
        echo OutputBaseFilename=%EXE_NAME%
        echo Compression=lzma2/max
        echo SolidCompression=yes
        echo WizardStyle=modern
        echo.
        echo [Files]
        echo Source: "dist\%APP_NAME%\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
        echo.
        echo [Icons]
        echo Name: "{group}\%APP_NAME%"; Filename: "{app}\%APP_NAME%.exe"
        echo Name: "{autodesktop}\%APP_NAME%"; Filename: "{app}\%APP_NAME%.exe"
        echo.
        echo [Run]
        echo Filename: "{app}\%APP_NAME%.exe"; Description: "运行程序"; Flags: nowait postinstall skipifsilent
    ) > setup.iss
    
    %INNO_SETUP% setup.iss
    
    if exist "dist\%EXE_NAME%" (
        echo     ✓ 安装程序创建成功
        echo.
        echo ==========================================
        echo 打包完成！
        echo ==========================================
        echo.
        echo 安装程序位置：dist\%EXE_NAME%
        echo.
        echo 安装方法：
        echo   1. 双击 %EXE_NAME%
        echo   2. 按照安装向导提示完成安装
        echo   3. 安装后可从开始菜单或桌面快捷方式运行
        echo.
        
        del /q setup.iss
    ) else (
        echo [警告] 安装程序创建失败
        pause
        exit /b 1
    )
) else (
    echo [提示] 未检测到 Inno Setup
    echo.
    echo 如需创建安装程序，请安装 Inno Setup 6：
    echo   https://jrsoftware.org/isdl.php
    echo.
    pause
    exit /b 1
)

:: 清理临时文件
rmdir /s /q build 2>nul
del /q setup.iss 2>nul

echo 按任意键退出...
pause >nul
