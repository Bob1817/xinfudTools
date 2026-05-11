"""
错误处理器单元测试
"""

import unittest
from core.error_handler import ErrorHandler, ErrorInfo, handle_error, get_friendly_error_message


class TestErrorHandler(unittest.TestCase):
    """测试错误处理器"""

    def setUp(self):
        """测试前准备"""
        self.handler = ErrorHandler()

    def test_handle_file_not_found_error(self):
        """测试文件不存在错误"""
        error = FileNotFoundError("No such file or directory: 'test.xlsx'")
        
        error_info = self.handler.handle_error(error, {'path': 'test.xlsx'})
        
        self.assertEqual(error_info.title, "文件未找到")
        self.assertIn("test.xlsx", error_info.message)
        self.assertIn("请检查文件路径是否正确", error_info.message)
        self.assertIn("请确认文件存在且未被移动或删除", error_info.suggestion)
        self.assertEqual(error_info.error_type, "FILE_NOT_FOUND")
        self.assertFalse(error_info.can_continue)

    def test_handle_permission_error(self):
        """测试权限错误"""
        error = PermissionError("Permission denied")
        
        error_info = self.handler.handle_error(error, {'path': 'test.xlsx'})
        
        self.assertEqual(error_info.title, "文件访问被拒绝")
        self.assertEqual(error_info.error_type, "FILE_ACCESS_DENIED")
        self.assertFalse(error_info.can_continue)

    def test_handle_value_error(self):
        """测试值错误"""
        error = ValueError("Invalid file format")
        
        error_info = self.handler.handle_error(error)
        
        self.assertEqual(error_info.title, "文件格式错误")
        self.assertEqual(error_info.error_type, "INVALID_FILE_FORMAT")

    def test_handle_key_error(self):
        """测试键错误（列不存在）"""
        error = KeyError("身份证号")
        
        error_info = self.handler.handle_error(error)
        
        self.assertEqual(error_info.title, "缺少必要列")
        self.assertIn("身份证号", error_info.message)
        self.assertEqual(error_info.error_type, "MISSING_REQUIRED_COLUMNS")

    def test_handle_memory_error(self):
        """测试内存错误"""
        error = MemoryError("Out of memory")
        
        error_info = self.handler.handle_error(error, {'rows': 100000})
        
        self.assertEqual(error_info.title, "内存不足")
        self.assertIn("100000", error_info.message)
        self.assertEqual(error_info.error_type, "MEMORY_ERROR")

    def test_handle_timeout_error(self):
        """测试超时错误"""
        error = TimeoutError("Operation timed out")
        
        error_info = self.handler.handle_error(error)
        
        self.assertEqual(error_info.title, "操作超时")
        self.assertEqual(error_info.error_type, "TIMEOUT_ERROR")
        self.assertTrue(error_info.can_continue)

    def test_handle_network_error(self):
        """测试网络错误"""
        error = ConnectionError("Network error")
        
        error_info = self.handler.handle_error(error)
        
        self.assertEqual(error_info.title, "网络错误")
        self.assertEqual(error_info.error_type, "NETWORK_ERROR")
        self.assertTrue(error_info.can_continue)

    def test_handle_unknown_error(self):
        """测试未知错误"""
        error = Exception("Something unexpected happened")
        
        error_info = self.handler.handle_error(error)
        
        self.assertEqual(error_info.title, "未知错误")
        self.assertEqual(error_info.error_type, "UNKNOWN_ERROR")
        self.assertIn("Something unexpected happened", error_info.message)

    def test_error_message_keywords(self):
        """测试错误消息关键词识别"""
        # 测试中文关键词
        error = Exception("找不到文件")
        error_info = self.handler.handle_error(error)
        self.assertEqual(error_info.error_type, "FILE_NOT_FOUND")
        
        # 测试权限关键词
        error = Exception("拒绝访问")
        error_info = self.handler.handle_error(error)
        self.assertEqual(error_info.error_type, "FILE_ACCESS_DENIED")
        
        # 测试网络关键词
        error = Exception("网络连接失败")
        error_info = self.handler.handle_error(error)
        self.assertEqual(error_info.error_type, "NETWORK_ERROR")

    def test_error_log(self):
        """测试错误日志记录"""
        error = FileNotFoundError("test.xlsx")
        
        self.handler.handle_error(error, {'path': 'test.xlsx'})
        
        logs = self.handler.get_error_log()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['error_type'], 'FILE_NOT_FOUND')
        self.assertIn('test.xlsx', logs[0]['message'])

    def test_clear_error_log(self):
        """测试清空错误日志"""
        error = FileNotFoundError("test.xlsx")
        self.handler.handle_error(error)
        
        self.handler.clear_error_log()
        
        logs = self.handler.get_error_log()
        self.assertEqual(len(logs), 0)

    def test_create_error_dialog_text(self):
        """测试创建错误对话框文本"""
        error = FileNotFoundError("test.xlsx")
        error_info = self.handler.handle_error(error, {'path': 'test.xlsx'})
        
        dialog_text = self.handler.create_error_dialog_text(error_info)
        
        self.assertIn("文件未找到", dialog_text)
        self.assertIn("💡 建议:", dialog_text)
        self.assertNotIn("技术详情", dialog_text)  # 默认不显示技术详情
        
        # 显示技术详情
        dialog_text_with_tech = self.handler.create_error_dialog_text(error_info, show_technical=True)
        self.assertIn("技术详情", dialog_text_with_tech)
        self.assertIn("堆栈跟踪", dialog_text_with_tech)


class TestConvenienceFunctions(unittest.TestCase):
    """测试便捷函数"""

    def test_handle_error(self):
        """测试handle_error函数"""
        error = FileNotFoundError("test.xlsx")
        
        error_info = handle_error(error, {'path': 'test.xlsx'})
        
        self.assertIsInstance(error_info, ErrorInfo)
        self.assertEqual(error_info.title, "文件未找到")

    def test_get_friendly_error_message(self):
        """测试get_friendly_error_message函数"""
        error = ValueError("Invalid format")
        
        message = get_friendly_error_message(error)
        
        self.assertIn("文件格式错误", message)
        self.assertIn("💡 建议:", message)


if __name__ == '__main__':
    unittest.main()
