#!/bin/bash
echo "=========================================="
echo "HR 数据处理工具集 - Mac DMG 打包脚本"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[错误] 未找到 Python 3${NC}"
    exit 1
fi

# 获取版本号
VERSION=$(python3 -c "import sys; sys.path.insert(0, '.'); from core.version import get_version; print(get_version())" 2>/dev/null || echo "1.0.0")
APP_NAME="HR数据处理工具集"
DMG_NAME="${APP_NAME}-v${VERSION}-mac.dmg"

echo -e "${YELLOW}[版本] v${VERSION}${NC}"
echo ""

# [1/5] 创建虚拟环境
echo -e "${GREEN}[1/5] 创建虚拟环境...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "    ✓ 虚拟环境创建成功"
else
    echo -e "    ✓ 虚拟环境已存在"
fi

# [2/5] 安装依赖
echo ""
echo -e "${GREEN}[2/5] 安装依赖包...${NC}"
source venv/bin/activate
pip install -r requirements.txt -q
pip install py2app -q
echo -e "    ✓ 依赖包安装成功"

# [3/5] 创建打包配置
echo ""
echo -e "${GREEN}[3/5] 创建打包配置...${NC}"

cat > setup_mac.py << EOF
from setuptools import setup

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'CFBundleName': '${APP_NAME}',
        'CFBundleDisplayName': '${APP_NAME}',
        'CFBundleIdentifier': 'com.xinfu.hrtools',
        'CFBundleVersion': '${VERSION}',
        'CFBundleShortVersionString': '${VERSION}',
        'NSHighResolutionCapable': True,
    },
    'packages': ['core', 'ui', 'db'],
    'iconfile': None,
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
EOF

echo -e "    ✓ 打包配置创建成功"

# [4/5] 打包 .app
echo ""
echo -e "${GREEN}[4/5] 开始打包 .app...${NC}"
python3 setup_mac.py py2app -A

if [ ! -d "dist/${APP_NAME}.app" ]; then
    echo -e "${RED}    ✗ .app 打包失败${NC}"
    exit 1
fi

echo -e "    ✓ .app 打包成功"

# [5/5] 创建 DMG
echo ""
echo -e "${GREEN}[5/5] 创建 DMG 安装包...${NC}"

# 清理旧的 DMG
rm -f "dist/${DMG_NAME}"

# 创建临时目录
TEMP_DIR="dmg_build_tmp"
rm -rf "${TEMP_DIR}"
mkdir -p "${TEMP_DIR}"

# 复制 .app 到临时目录
cp -R "dist/${APP_NAME}.app" "${TEMP_DIR}/"

# 创建 Applications 符号链接
ln -s /Applications "${TEMP_DIR}/Applications"

# 创建背景图片目录（可选）
BACKGROUND_DIR="${TEMP_DIR}/.background"
mkdir -p "${BACKGROUND_DIR}"

# 创建 DMG
hdiutil create -volname "${APP_NAME} v${VERSION}" \
               -srcfolder "${TEMP_DIR}" \
               -ov -format UDZO \
               "dist/${DMG_NAME}"

if [ $? -eq 0 ]; then
    echo -e "    ✓ DMG 创建成功"
    echo ""
    echo -e "${GREEN}=========================================="
    echo "打包完成！"
    echo -e "==========================================${NC}"
    echo ""
    echo -e "DMG 文件位置：${YELLOW}dist/${DMG_NAME}${NC}"
    echo ""
    echo -e "安装方法："
    echo "  1. 双击 ${DMG_NAME}"
    echo "  2. 将应用拖拽到 Applications 文件夹"
    echo "  3. 运行应用程序"
    echo ""
    
    # 清理临时文件
    rm -rf "${TEMP_DIR}"
    rm -f setup_mac.py
else
    echo -e "${RED}    ✗ DMG 创建失败${NC}"
    exit 1
fi

deactivate
