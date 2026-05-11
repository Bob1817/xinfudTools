"""
数据合并器单元测试
"""

import unittest
import pandas as pd
import numpy as np
from core.data_merger import DataMerger, merge_payroll_data


class TestDataMerger(unittest.TestCase):
    """测试数据合并器"""

    def setUp(self):
        """测试前准备"""
        self.merger = DataMerger()

    def test_merge_single_record(self):
        """测试单条数据（无需合并）"""
        data = {
            '身份证号': ['110101199001011234'],
            '姓名': ['张三'],
            '应发金额': [5000],
            '养老': [200],
            '医疗': [100],
            '失业': [50],
            '公积金': [300]
        }
        df = pd.DataFrame(data)
        
        result, warnings = self.merger.merge_by_id_card(df, '身份证号')
        
        self.assertEqual(len(result), 1)
        self.assertEqual(len(warnings), 0)
        self.assertEqual(result.iloc[0]['应发金额'], 5000)
        self.assertEqual(result.iloc[0]['姓名'], '张三')

    def test_merge_multiple_records_same_id(self):
        """测试同一身份证号多条数据合并"""
        data = {
            '身份证号': ['110101199001011234', '110101199001011234'],
            '姓名': ['张三', '张三'],
            '应发金额': [5000, 3000],
            '养老': [200, 150],
            '医疗': [100, 80],
            '失业': [50, 40],
            '公积金': [300, 200]
        }
        df = pd.DataFrame(data)
        
        result, warnings = self.merger.merge_by_id_card(df, '身份证号')
        
        self.assertEqual(len(result), 1)
        self.assertEqual(len(warnings), 0)
        self.assertEqual(result.iloc[0]['应发金额'], 8000)  # 5000 + 3000
        self.assertEqual(result.iloc[0]['养老'], 350)  # 200 + 150
        self.assertEqual(result.iloc[0]['医疗'], 180)  # 100 + 80
        self.assertEqual(result.iloc[0]['失业'], 90)  # 50 + 40
        self.assertEqual(result.iloc[0]['公积金'], 500)  # 300 + 200

    def test_merge_with_different_names(self):
        """测试姓名不一致时的合并"""
        data = {
            '身份证号': ['110101199001011234', '110101199001011234'],
            '姓名': ['张三', '张小三'],
            '应发金额': [5000, 3000],
            '养老': [200, 150],
            '医疗': [100, 80],
            '失业': [50, 40],
            '公积金': [300, 200]
        }
        df = pd.DataFrame(data)
        
        result, warnings = self.merger.merge_by_id_card(df, '身份证号')
        
        self.assertEqual(len(result), 1)
        self.assertEqual(len(warnings), 1)  # 应该有姓名不一致的警告
        self.assertEqual(result.iloc[0]['姓名'], '张三')  # 取第一条
        self.assertEqual(result.iloc[0]['应发金额'], 8000)

    def test_merge_with_empty_values(self):
        """测试包含空值的合并"""
        data = {
            '身份证号': ['110101199001011234', '110101199001011234'],
            '姓名': ['张三', '张三'],
            '应发金额': [5000, np.nan],
            '养老': [200, None],
            '医疗': [100, ''],
            '失业': [50, 40],
            '公积金': [300, 200]
        }
        df = pd.DataFrame(data)
        
        result, warnings = self.merger.merge_by_id_card(df, '身份证号')
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]['应发金额'], 5000)  # 忽略空值
        self.assertEqual(result.iloc[0]['养老'], 200)  # 忽略空值
        self.assertEqual(result.iloc[0]['医疗'], 100)  # 忽略空值
        self.assertEqual(result.iloc[0]['失业'], 90)  # 50 + 40
        self.assertEqual(result.iloc[0]['公积金'], 500)  # 300 + 200

    def test_merge_with_id_card_cleaning(self):
        """测试身份证号清洗"""
        data = {
            '身份证号': ['110101199001011234', '110101199001011234.0', ' 110101199001011234 '],
            '姓名': ['张三', '张三', '张三'],
            '应发金额': [5000, 3000, 2000],
            '养老': [200, 150, 100],
            '医疗': [100, 80, 60],
            '失业': [50, 40, 30],
            '公积金': [300, 200, 100]
        }
        df = pd.DataFrame(data)
        
        result, warnings = self.merger.merge_by_id_card(df, '身份证号')
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]['应发金额'], 10000)  # 5000 + 3000 + 2000

    def test_merge_multiple_different_ids(self):
        """测试多个不同身份证号的合并"""
        data = {
            '身份证号': ['110101199001011234', '110101199001011234', '110101199001015678'],
            '姓名': ['张三', '张三', '李四'],
            '应发金额': [5000, 3000, 6000],
            '养老': [200, 150, 250],
            '医疗': [100, 80, 120],
            '失业': [50, 40, 60],
            '公积金': [300, 200, 350]
        }
        df = pd.DataFrame(data)
        
        result, warnings = self.merger.merge_by_id_card(df, '身份证号')
        
        self.assertEqual(len(result), 2)
        
        # 张三
        zhang_san = result[result['姓名'] == '张三'].iloc[0]
        self.assertEqual(zhang_san['应发金额'], 8000)
        self.assertEqual(zhang_san['养老'], 350)
        
        # 李四
        li_si = result[result['姓名'] == '李四'].iloc[0]
        self.assertEqual(li_si['应发金额'], 6000)
        self.assertEqual(li_si['养老'], 250)

    def test_empty_dataframe(self):
        """测试空DataFrame"""
        df = pd.DataFrame()
        
        result, warnings = self.merger.merge_by_id_card(df, '身份证号')
        
        self.assertEqual(len(result), 0)
        self.assertEqual(len(warnings), 0)

    def test_validate_data_consistency(self):
        """测试数据一致性验证"""
        data = {
            '身份证号': ['110101199001011234', '110101199001011234', '110101199001015678'],
            '姓名': ['张三', '张小三', '李四'],
            '应发金额': [5000, 3000, 6000],
            '养老': [200, 150, 250],
            '医疗': [100, 80, 120],
            '失业': [50, 40, 60],
            '公积金': [300, 200, 350]
        }
        df = pd.DataFrame(data)
        
        stats = self.merger.validate_data_consistency(df, '身份证号')
        
        self.assertEqual(stats['total_rows'], 3)
        self.assertEqual(stats['unique_ids'], 2)
        self.assertEqual(stats['duplicate_ids'], 1)
        self.assertEqual(stats['max_duplicates'], 2)
        self.assertEqual(len(stats['warnings']), 1)  # 姓名不一致警告

    def test_get_merge_preview(self):
        """测试合并预览"""
        data = {
            '身份证号': ['110101199001011234', '110101199001011234', '110101199001015678'],
            '姓名': ['张三', '张小三', '李四'],
            '应发金额': [5000, 3000, 6000],
            '养老': [200, 150, 250],
            '医疗': [100, 80, 120],
            '失业': [50, 40, 60],
            '公积金': [300, 200, 350]
        }
        df = pd.DataFrame(data)
        
        preview = self.merger.get_merge_preview(df, '身份证号')
        
        self.assertIn('数据合并预览', preview)
        self.assertIn('总数据条数: 3', preview)
        self.assertIn('唯一身份证号: 2', preview)
        self.assertIn('重复身份证号: 1', preview)
        self.assertIn('⚠️', preview)  # 应该有警告标记


class TestMergeFunctions(unittest.TestCase):
    """测试便捷函数"""

    def test_merge_payroll_data(self):
        """测试merge_payroll_data函数"""
        data = {
            '身份证号': ['110101199001011234', '110101199001011234'],
            '姓名': ['张三', '张三'],
            '应发金额': [5000, 3000],
            '养老': [200, 150],
            '医疗': [100, 80],
            '失业': [50, 40],
            '公积金': [300, 200]
        }
        df = pd.DataFrame(data)
        
        result, warnings = merge_payroll_data(df)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]['应发金额'], 8000)


if __name__ == '__main__':
    unittest.main()
