#!/bin/bash
echo "================================"
echo "HR 数据处理工具集 - Mac 测试脚本"
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
if [ $? -eq 0 ]; then
    echo "    ✓ 依赖包安装成功"
else
    echo "    ✗ 依赖包安装失败"
    exit 1
fi

echo ""
echo "[3/4] 运行模块导入测试..."
python3 -c "
from core.data_loader import PayrollLoader
from core.social_security_loader import SocialSecurityLoader
from core.two_table_mapper import TwoTableMapper
from core.report_generator import ReportGenerator
from db.database import Database
from ui.main_window import MainWindow
print('✓ 所有模块导入成功')
"
if [ $? -eq 0 ]; then
    echo "    ✓ 模块导入测试通过"
else
    echo "    ✗ 模块导入测试失败"
    exit 1
fi

echo ""
echo "[4/4] 运行完整流程测试..."
python3 -c "
import pandas as pd
from core.social_security_loader import SocialSecurityLoader
from core.two_table_mapper import TwoTableMapper
from core.data_loader import PayrollLoader
from core.report_generator import ReportGenerator
from pathlib import Path

# 测试 1: 读取社保表
print('    测试 1: 读取社保数据表...')
ss_loader = SocialSecurityLoader()
ss_df = ss_loader.load('社保数据表.xlsx')
assert len(ss_df) > 0, '社保表数据为空'
print(f'      ✓ 读取成功：{len(ss_df)} 条数据')

# 测试 2: 读取发薪表
print('    测试 2: 读取发薪数据表...')
payroll_loader = PayrollLoader()
payroll_df = payroll_loader.load('测试发薪表.xlsx')
assert len(payroll_df) > 0, '发薪表数据为空'
print(f'      ✓ 读取成功：{len(payroll_df)} 条数据')

# 测试 3: 合并映射
print('    测试 3: 数据合并映射...')
mapper = TwoTableMapper()
ss_dict = ss_loader.get_social_security_data(ss_df)
tax_df = mapper.merge_and_map(payroll_df, ss_dict, '2025-04')
assert len(tax_df) == len(payroll_df), '合并后数据量不匹配'
assert len(tax_df.columns) == 28, f'申报表列数应为 28，实际{len(tax_df.columns)}'
print(f'      ✓ 合并成功：{len(tax_df)} 条数据，{len(tax_df.columns)} 列')

# 测试 4: 生成 Excel
print('    测试 4: 生成申报表 Excel...')
generator = ReportGenerator()
output_path = generator.generate(tax_df, '2025-04', '/tmp')
assert Path(output_path).exists(), '生成的文件不存在'
print(f'      ✓ 生成成功：{output_path}')

# 测试 5: 验证生成的文件
print('    测试 5: 验证生成的文件...')
import openpyxl
wb = openpyxl.load_workbook(output_path)
assert '扣缴申报表' in wb.sheetnames, '工作表名称不正确'
ws = wb['扣缴申报表']
assert ws.max_row == len(tax_df) + 1, '行数不正确'
print(f'      ✓ 文件验证通过')

print()
print('=' * 40)
print('所有测试通过！✓')
print('=' * 40)
"
if [ $? -eq 0 ]; then
    echo "    ✓ 完整流程测试通过"
else
    echo "    ✗ 完整流程测试失败"
    exit 1
fi

echo ""
echo "================================"
echo "所有测试完成！"
echo "================================"
echo ""
echo "现在可以运行以下命令启动应用："
echo "  ./run_mac.sh"
echo ""

# 清理
deactivate
