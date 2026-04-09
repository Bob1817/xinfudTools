#!/bin/bash
echo "================================"
echo "HR 数据处理工具集 - Mac 打包脚本"
echo "================================"
echo ""

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python 3"
    exit 1
fi

echo "[1/4] 创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "    ✓ 虚拟环境创建成功"
else
    echo "    ✓ 虚拟环境已存在"
fi

echo ""
echo "[2/4] 安装依赖包..."
source venv/bin/activate
pip install -r requirements.txt -q
pip install py2app -q
echo "    ✓ 依赖包安装成功"

echo ""
echo "[3/4] 创建打包配置..."

# 创建 setup.py for py2app
cat > setup_mac.py << 'EOF'
from setuptools import setup

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'CFBundleName': 'HR 数据处理工具',
        'CFBundleDisplayName': 'HR 数据处理工具',
        'CFBundleIdentifier': 'com.xinfu.hrtools',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
EOF

echo "    ✓ 打包配置创建成功"

echo ""
echo "[4/4] 开始打包..."
python3 setup_mac.py -A

if [ $? -eq 0 ]; then
    echo "    ✓ 打包成功"
    echo ""
    echo "================================"
    echo "打包完成！"
    echo "================================"
    echo ""
    echo "应用位置：dist/HR 数据处理工具.app"
    echo ""
    echo "使用方法："
    echo "  1. 双击打开 dist/HR 数据处理工具.app"
    echo "  2. 或者运行：open dist/HR 数据处理工具.app"
    echo ""
else
    echo "    ✗ 打包失败"
    exit 1
fi

# 清理
deactivate
