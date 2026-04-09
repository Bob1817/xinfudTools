@echo off
chcp 65001 >nul
echo ==========================================
echo HR 数据处理工具集 - Windows EXE 打包脚本
echo ==========================================
echo.

:: 颜色设置 (Windows 10+)
:: 绿色 = 成功，黄色 = 警告，红色 = 错误

:: 获取版本号
for /f "delims=" %%i in ('python -c "from core.version import get_version; print(get_version())" 2^>nul') do set VERSION=%%i
if "%VERSION%"=="" set VERSION=1.0.0

set APP_NAME=HR数据处理工具集
set EXE_NAME=%APP_NAME%-v%VERSION%-windows.exe

echo [版本] v%VERSION%
echo.

:: [1/5] 检查 Python 环境
echo [1/5] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python
    pause
    exit /b 1
)
echo     ✓ Python 环境正常
echo.

:: [2/5] 安装依赖
echo [2/5] 安装依赖包...
pip install -r requirements.txt -q
pip install pyinstaller -q
if errorlevel 1 (
    echo [错误] 依赖包安装失败
    pause
    exit /b 1
)
echo     ✓ 依赖包安装成功
echo.

:: [3/5] 创建打包配置
echo [3/5] 创建打包配置...

(
echo # -*- mode: python ; coding: utf-8 -*-
echo.
echo block_cipher = None
echo.
echo a = Analysis^(
echo     ['main.py'],
echo     pathex=[],
echo     binaries=[],
echo     datas=[
echo         ('core', 'core'),
echo         ('ui', 'ui'),
echo         ('db', 'db'),
echo     ],
echo     hiddenimports=[
echo         'PyQt6',
echo         'PyQt6.QtCore',
echo         'PyQt6.QtGui',
echo         'PyQt6.QtWidgets',
echo         'qfluentwidgets',
echo         'pandas',
echo         'openpyxl',
echo     ],
echo     hookspath=[],
echo     hooksconfig={},
echo     runtime_hooks=[],
echo     excludes=[],
echo     win_no_prefer_redirects=False,
echo     win_private_assemblies=False,
echo     cipher=block_cipher,
echo     noarchive=False,
echo ^)
echo.
echo pyz = PYZ^(a.pure, a.zipped_data, cipher=block_cipher^)
echo.
echo exe = EXE^(
echo     pyz,
echo     a.scripts,
echo     a.binaries,
echo     a.zipfiles,
echo     a.datas,
echo     [],
echo     '%APP_NAME%',
echo     False,
echo     False,
echo     None,
echo     False,
echo     False,
echo     False,
echo     '%VERSION%',
echo     None,
echo     None,
echo     False,
echo     False,
echo     None,
echo     0,
echo     0,
echo     0,
echo     True,
echo     False,
echo     0x0409,
echo     'build\\icon.ico',
echo     None,
echo     False,
echo     None,
echo     None,
echo     None,
echo     None,
echo     None,
echo     None,
echo ^)
) > build_windows.spec

echo     ✓ 打包配置创建成功
echo.

:: [4/5] 打包 EXE
echo [4/5] 开始打包 EXE...
pyinstaller --clean --noconfirm build_windows.spec

if not exist "dist\%APP_NAME%.exe" (
    echo [错误] EXE 打包失败
    pause
    exit /b 1
)
echo     ✓ EXE 打包成功
echo.

:: [5/5] 创建安装包（使用 Inno Setup 或自解压）
echo [5/5] 创建安装程序...

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
        echo Compression=lzma
        echo SolidCompression=yes
        echo.
        echo [Files]
        echo Source: "dist\%APP_NAME%.exe"; DestDir: "{app}"; Flags: ignoreversion
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
        echo [警告] 安装程序创建失败，仅打包 EXE
        echo.
        echo ==========================================
        echo 打包完成（仅 EXE）
        echo ==========================================
        echo.
        echo 程序位置：dist\%APP_NAME%.exe
        echo.
        echo 运行方法：
        echo   双击 %APP_NAME%.exe 即可运行
        echo.
    )
) else (
    echo [提示] 未检测到 Inno Setup，仅打包 EXE 文件
    echo.
    echo ==========================================
    echo 打包完成（仅 EXE）
    echo ==========================================
    echo.
    echo 程序位置：dist\%APP_NAME%.exe
    echo.
    echo 运行方法：
    echo   双击 %APP_NAME%.exe 即可运行
    echo.
    echo 如需创建安装程序，请安装 Inno Setup 6：
    echo   https://jrsoftware.org/isdl.php
    echo.
)

:: 清理
rmdir /s /q build 2>nul
del /q build_windows.spec 2>nul
del /q setup.iss 2>nul

pause
