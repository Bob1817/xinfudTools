#!/bin/bash
echo "================================"
echo "HR 数据处理工具集 - Mac 运行脚本"
echo "================================"
echo ""

# 检查 Python 环境
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "[$PYTHON_VERSION]"
else
    echo "[错误] 未找到 Python 3，请先安装 Python 3.10+"
    exit 1
fi

echo ""
echo "[1/2] 检查/安装依赖包..."

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "    创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip -q

# 安装依赖
echo "    安装依赖包..."
pip install -r requirements.txt -q

if [ $? -eq 0 ]; then
    echo "    依赖包安装完成"
else
    echo "    [错误] 依赖包安装失败"
    exit 1
fi

echo ""
echo "[2/2] 启动应用..."
echo ""
echo "应用已启动！"
echo "请关闭此窗口以保持应用运行"
echo ""

# 启动应用
python3 main.py

# 清理
deactivate
