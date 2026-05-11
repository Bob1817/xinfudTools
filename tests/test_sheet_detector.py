"""
Sheet识别器单元测试
"""

import unittest
import pandas as pd
import os
from core.sheet_detector import SheetDetector, FieldMapper, detect_social_security_sheets
from core.sheet_detector import SheetMatchResult


class TestSheetDetector(unittest.TestCase):
    """测试Sheet识别器"""

    def setUp(self):
        """测试前准备"""
        self.detector = SheetDetector()
        
        # 创建测试Excel文件
        self.test_file = '/tmp/test_social_security.xlsx'
        self._create_test_file()

    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def _create_test_file(self):
        """创建测试Excel文件"""
        with pd.ExcelWriter(self.test_file, engine='openpyxl') as writer:
            # Sheet 1: 完全匹配的社保数据
            df1 = pd.DataFrame({
                '姓名': ['张三', '李四'],
                '身份证号': ['110101199001011234', '110101199001015678'],
                '个人养老': [200, 250],
                '个人医疗': [100, 120],
                '个人失业': [50, 60],
                '个人公积金': [300, 350]
            })
            df1.to_excel(writer, sheet_name='本月发薪明细', index=False)
            
            # Sheet 2: 部分匹配
            df2 = pd.DataFrame({
                '姓名': ['王五'],
                '身份证号': ['110101199001019012'],
                '养老保险费': [220],
                '医疗保险费': [110],
                '失业保险费': [55]
                # 缺少公积金
            })
            df2.to_excel(writer, sheet_name='社保数据', index=False)
            
            # Sheet 3: 不匹配的数据
            df3 = pd.DataFrame({
                '产品': ['产品A', '产品B'],
                '数量': [100, 200],
                '价格': [50, 80]
            })
            df3.to_excel(writer, sheet_name='产品清单', index=False)

    def test_detect_social_security_sheets(self):
        """测试Sheet检测"""
        results = self.detector.detect_social_security_sheets(self.test_file)
        
        # 应该检测到2个Sheet（本月发薪明细和社保数据）
        self.assertEqual(len(results), 2)
        
        # 第一个应该是完全匹配的
        self.assertTrue(results[0].is_perfect_match)
        self.assertEqual(results[0].sheet_name, '本月发薪明细')
        
        # 第二个应该是部分匹配
        self.assertFalse(results[1].is_perfect_match)
        self.assertEqual(results[1].sheet_name, '社保数据')

    def test_perfect_match_detection(self):
        """测试完全匹配检测"""
        results = self.detector.detect_social_security_sheets(self.test_file)
        
        perfect_matches = [r for r in results if r.is_perfect_match]
        self.assertEqual(len(perfect_matches), 1)
        
        match = perfect_matches[0]
        self.assertEqual(match.match_score, 1.0)
        self.assertEqual(len(match.matched_fields), 4)  # 养老、医疗、失业、公积金
        self.assertEqual(len(match.missing_fields), 0)

    def test_partial_match_detection(self):
        """测试部分匹配检测"""
        results = self.detector.detect_social_security_sheets(self.test_file)
        
        partial_matches = [r for r in results if not r.is_perfect_match]
        self.assertEqual(len(partial_matches), 1)
        
        match = partial_matches[0]
        self.assertTrue(match.match_score < 1.0)
        self.assertEqual(len(match.matched_fields), 3)  # 养老、医疗、失业
        self.assertEqual(len(match.missing_fields), 1)  # 公积金

    def test_get_best_sheet(self):
        """测试获取最佳Sheet"""
        self.detector.detect_social_security_sheets(self.test_file)
        
        best = self.detector.get_best_sheet()
        
        self.assertIsNotNone(best)
        self.assertEqual(best.sheet_name, '本月发薪明细')
        self.assertTrue(best.is_perfect_match)

    def test_has_perfect_match(self):
        """测试检查是否有完全匹配"""
        self.detector.detect_social_security_sheets(self.test_file)
        
        self.assertTrue(self.detector.has_perfect_match())

    def test_get_match_summary(self):
        """测试获取匹配摘要"""
        self.detector.detect_social_security_sheets(self.test_file)
        
        summary = self.detector.get_match_summary()
        
        self.assertIn('社保数据Sheet识别结果', summary)
        self.assertIn('本月发薪明细', summary)
        self.assertIn('社保数据', summary)

    def test_get_sheet_for_user_selection(self):
        """测试获取用户选择列表"""
        self.detector.detect_social_security_sheets(self.test_file)
        
        selection_list = self.detector.get_sheet_for_user_selection()
        
        self.assertEqual(len(selection_list), 2)
        self.assertIn('sheet_name', selection_list[0])
        self.assertIn('match_score', selection_list[0])
        self.assertIn('is_perfect_match', selection_list[0])


class TestFieldMapper(unittest.TestCase):
    """测试字段映射器"""

    def setUp(self):
        """测试前准备"""
        self.mapper = FieldMapper()

    def test_suggest_field_mapping_perfect(self):
        """测试完全匹配的字段建议"""
        columns = ['姓名', '身份证号', '个人养老', '个人医疗', '个人失业', '个人公积金']
        
        suggestions = self.mapper.suggest_field_mapping(columns)
        
        self.assertEqual(suggestions['养老'], '个人养老')
        self.assertEqual(suggestions['医疗'], '个人医疗')
        self.assertEqual(suggestions['失业'], '个人失业')
        self.assertEqual(suggestions['公积金'], '个人公积金')

    def test_suggest_field_mapping_partial(self):
        """测试部分匹配的字段建议"""
        columns = ['姓名', '身份证号', '养老保险费', '医疗保险费', '失业保险费']
        
        suggestions = self.mapper.suggest_field_mapping(columns)
        
        self.assertEqual(suggestions['养老'], '养老保险费')
        self.assertEqual(suggestions['医疗'], '医疗保险费')
        self.assertEqual(suggestions['失业'], '失业保险费')
        self.assertIsNone(suggestions['公积金'])  # 未匹配

    def test_suggest_field_mapping_no_match(self):
        """测试无匹配字段"""
        columns = ['产品', '数量', '价格']
        
        suggestions = self.mapper.suggest_field_mapping(columns)
        
        for key in suggestions:
            self.assertIsNone(suggestions[key])

    def test_validate_mapping_complete(self):
        """测试完整映射验证"""
        mapping = {
            '养老': '个人养老',
            '医疗': '个人医疗',
            '失业': '个人失业',
            '公积金': '个人公积金'
        }
        
        is_valid, missing = self.mapper.validate_mapping(mapping)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(missing), 0)

    def test_validate_mapping_incomplete(self):
        """测试不完整映射验证"""
        mapping = {
            '养老': '个人养老',
            '医疗': '个人医疗'
        }
        
        is_valid, missing = self.mapper.validate_mapping(mapping)
        
        self.assertFalse(is_valid)
        self.assertEqual(len(missing), 2)  # 失业和公积金


class TestConvenienceFunctions(unittest.TestCase):
    """测试便捷函数"""

    def setUp(self):
        """测试前准备"""
        self.test_file = '/tmp/test_social_security.xlsx'
        self._create_test_file()

    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def _create_test_file(self):
        """创建测试Excel文件"""
        with pd.ExcelWriter(self.test_file, engine='openpyxl') as writer:
            df = pd.DataFrame({
                '姓名': ['张三'],
                '身份证号': ['110101199001011234'],
                '个人养老': [200],
                '个人医疗': [100],
                '个人失业': [50],
                '个人公积金': [300]
            })
            df.to_excel(writer, sheet_name='社保数据', index=False)

    def test_detect_social_security_sheets(self):
        """测试detect_social_security_sheets函数"""
        results = detect_social_security_sheets(self.test_file)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].sheet_name, '社保数据')


if __name__ == '__main__':
    unittest.main()
