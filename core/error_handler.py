"""
错误处理器模块
统一处理错误信息，提供友好的错误提示
"""

import traceback
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class ErrorInfo:
    """错误信息"""
    title: str
    message: str
    suggestion: str
    error_type: str
    technical_detail: str
    can_continue: bool  # 是否可以继续操作


class ErrorHandler:
    """错误处理器：统一处理错误信息"""
    
    # 错误类型定义
    ERROR_TYPES = {
        'FILE_NOT_FOUND': {
            'title': '文件未找到',
            'template': '找不到文件：{path}\n\n请检查文件路径是否正确。',
            'suggestion': '请确认文件存在且未被移动或删除。如果文件在网络驱动器上，请检查网络连接。',
            'can_continue': False
        },
        'FILE_ACCESS_DENIED': {
            'title': '文件访问被拒绝',
            'template': '无法访问文件：{path}\n\n您可能没有足够的权限读取此文件。',
            'suggestion': '请检查文件权限，或尝试将文件复制到其他位置后再打开。',
            'can_continue': False
        },
        'FILE_LOCKED': {
            'title': '文件被占用',
            'template': '文件正在被其他程序使用：{path}\n\n请关闭可能正在使用该文件的程序（如Excel）。',
            'suggestion': '请关闭Excel或其他正在使用该文件的程序，然后重试。',
            'can_continue': False
        },
        'INVALID_FILE_FORMAT': {
            'title': '文件格式错误',
            'template': '文件格式不正确：{path}\n\n无法识别为有效的Excel文件。',
            'suggestion': '请确保上传的是有效的Excel文件（.xlsx 或 .xls 格式）。如果文件已损坏，请尝试恢复或重新保存。',
            'can_continue': False
        },
        'FILE_CORRUPTED': {
            'title': '文件损坏',
            'template': '文件可能已损坏：{path}\n\n无法读取文件内容。',
            'suggestion': '请尝试在Excel中打开并重新保存文件，或使用备份文件。',
            'can_continue': False
        },
        'MISSING_REQUIRED_COLUMNS': {
            'title': '缺少必要列',
            'template': '缺少以下必要列：{columns}\n\n请检查文件内容是否符合要求。',
            'suggestion': '请确保文件包含完整的表头信息。参考使用指南了解所需的列名。',
            'can_continue': False
        },
        'INVALID_COLUMN_DATA': {
            'title': '列数据格式错误',
            'template': '列 "{column}" 的数据格式不正确。\n\n期望格式：{expected}\n实际值：{actual}',
            'suggestion': '请检查该列的数据格式，确保所有数据都符合要求。',
            'can_continue': False
        },
        'EMPTY_FILE': {
            'title': '文件为空',
            'template': '文件没有数据：{path}\n\n请检查文件内容。',
            'suggestion': '请确保文件中包含有效的数据行。',
            'can_continue': False
        },
        'NO_VALID_DATA': {
            'title': '无有效数据',
            'template': '未找到有效的数据记录。\n\n可能原因：\n1. 身份证号格式不正确\n2. 所有数据行均为空\n3. 数据被过滤',
            'suggestion': '请检查数据内容，确保包含有效的身份证号和金额数据。',
            'can_continue': False
        },
        'DATA_MERGE_ERROR': {
            'title': '数据合并错误',
            'template': '合并数据时发生错误：{error}\n\n请检查数据格式是否正确。',
            'suggestion': '请检查发薪表和社保表的数据格式，确保身份证号格式一致。',
            'can_continue': False
        },
        'SHEET_NOT_FOUND': {
            'title': '未找到数据表',
            'template': '在社保数据表中未找到有效的数据Sheet。\n\n请确保文件中包含社保数据。',
            'suggestion': '请检查社保数据表是否包含正确的工作表，或尝试手动选择Sheet。',
            'can_continue': False
        },
        'FIELD_MATCH_ERROR': {
            'title': '字段匹配失败',
            'template': '无法匹配社保表中的必要字段。\n\n缺失字段：{fields}',
            'suggestion': '请检查社保表的列名是否正确，或手动指定字段映射。',
            'can_continue': False
        },
        'OUTPUT_ERROR': {
            'title': '输出错误',
            'template': '生成输出文件时发生错误：{error}',
            'suggestion': '请检查输出路径是否有写入权限，或尝试更换输出位置。',
            'can_continue': False
        },
        'PERMISSION_DENIED': {
            'title': '权限不足',
            'template': '没有权限执行此操作：{operation}\n\n请检查用户权限。',
            'suggestion': '请以管理员身份运行程序，或联系系统管理员获取权限。',
            'can_continue': False
        },
        'DISK_FULL': {
            'title': '磁盘空间不足',
            'template': '磁盘空间不足，无法保存文件。\n\n请清理磁盘空间后重试。',
            'suggestion': '请删除不必要的文件，或将输出保存到其他磁盘。',
            'can_continue': False
        },
        'MEMORY_ERROR': {
            'title': '内存不足',
            'template': '系统内存不足，无法处理数据。\n\n数据量：{rows} 行',
            'suggestion': '请关闭其他程序释放内存，或分批处理数据。',
            'can_continue': False
        },
        'NETWORK_ERROR': {
            'title': '网络错误',
            'template': '网络连接异常：{error}\n\n请检查网络连接。',
            'suggestion': '请检查网络连接，或稍后重试。',
            'can_continue': True
        },
        'TIMEOUT_ERROR': {
            'title': '操作超时',
            'template': '操作超时，请稍后重试。\n\n如果问题持续存在，可能是数据量过大。',
            'suggestion': '请尝试减少数据量，或分批处理。',
            'can_continue': True
        },
        'UNKNOWN_ERROR': {
            'title': '未知错误',
            'template': '发生未知错误：{error}\n\n请稍后重试或联系技术支持。',
            'suggestion': '请记录错误信息，并联系技术支持获取帮助。',
            'can_continue': False
        }
    }
    
    # 错误映射（异常类型 -> 错误代码）
    EXCEPTION_MAP = {
        'FileNotFoundError': 'FILE_NOT_FOUND',
        'PermissionError': 'FILE_ACCESS_DENIED',
        'IsADirectoryError': 'FILE_NOT_FOUND',
        'NotADirectoryError': 'FILE_NOT_FOUND',
        'ValueError': 'INVALID_FILE_FORMAT',
        'KeyError': 'MISSING_REQUIRED_COLUMNS',
        'IndexError': 'INVALID_COLUMN_DATA',
        'MemoryError': 'MEMORY_ERROR',
        'TimeoutError': 'TIMEOUT_ERROR',
        'ConnectionError': 'NETWORK_ERROR',
        'OSError': 'PERMISSION_DENIED',
        'IOError': 'FILE_ACCESS_DENIED',
    }
    
    def __init__(self):
        self.error_log = []
    
    def handle_error(self, error: Exception, context: Dict = None) -> ErrorInfo:
        """
        处理错误，返回友好的错误信息
        
        Args:
            error: 异常对象
            context: 上下文信息（如文件路径、列名等）
            
        Returns:
            友好的错误信息
        """
        context = context or {}
        
        # 获取错误类型
        error_type = self._get_error_type(error)
        
        # 获取错误定义
        error_def = self.ERROR_TYPES.get(error_type, self.ERROR_TYPES['UNKNOWN_ERROR'])
        
        # 构建错误信息
        message = self._build_message(error_def['template'], error, context)
        
        # 获取技术详情
        technical_detail = self._get_technical_detail(error)
        
        # 记录错误日志
        self._log_error(error_type, message, technical_detail)
        
        return ErrorInfo(
            title=error_def['title'],
            message=message,
            suggestion=error_def['suggestion'],
            error_type=error_type,
            technical_detail=technical_detail,
            can_continue=error_def['can_continue']
        )
    
    def _get_error_type(self, error: Exception) -> str:
        """
        根据异常类型确定错误代码
        
        Args:
            error: 异常对象
            
        Returns:
            错误代码
        """
        error_class = error.__class__.__name__
        
        # 检查异常类型映射
        if error_class in self.EXCEPTION_MAP:
            return self.EXCEPTION_MAP[error_class]
        
        # 检查错误消息中的关键词
        error_msg = str(error).lower()
        
        if 'no such file' in error_msg or '找不到' in error_msg:
            return 'FILE_NOT_FOUND'
        elif 'permission' in error_msg or '拒绝访问' in error_msg:
            return 'FILE_ACCESS_DENIED'
        elif 'locked' in error_msg or '占用' in error_msg:
            return 'FILE_LOCKED'
        elif 'corrupt' in error_msg or '损坏' in error_msg:
            return 'FILE_CORRUPTED'
        elif 'memory' in error_msg or '内存' in error_msg:
            return 'MEMORY_ERROR'
        elif 'disk full' in error_msg or '空间不足' in error_msg:
            return 'DISK_FULL'
        elif 'network' in error_msg or '网络' in error_msg:
            return 'NETWORK_ERROR'
        elif 'timeout' in error_msg or '超时' in error_msg:
            return 'TIMEOUT_ERROR'
        elif 'column' in error_msg or '列' in error_msg:
            return 'MISSING_REQUIRED_COLUMNS'
        elif 'sheet' in error_msg or '工作表' in error_msg:
            return 'SHEET_NOT_FOUND'
        
        return 'UNKNOWN_ERROR'
    
    def _build_message(self, template: str, error: Exception, context: Dict) -> str:
        """
        构建错误消息
        
        Args:
            template: 消息模板
            error: 异常对象
            context: 上下文信息
            
        Returns:
            构建后的消息
        """
        message = template
        
        # 替换上下文变量
        for key, value in context.items():
            placeholder = f'{{{key}}}'
            if placeholder in message:
                message = message.replace(placeholder, str(value))
        
        # 替换错误信息
        if '{error}' in message:
            message = message.replace('{error}', str(error))
        
        # 替换路径
        if '{path}' in message and 'path' not in context:
            message = message.replace('{path}', '未知路径')
        
        # 替换columns（用于KeyError）
        if '{columns}' in message and 'columns' not in context:
            # 尝试从错误对象获取列名
            error_str = str(error)
            message = message.replace('{columns}', error_str)
        
        return message
    
    def _get_technical_detail(self, error: Exception) -> str:
        """
        获取技术详情（用于调试）
        
        Args:
            error: 异常对象
            
        Returns:
            技术详情字符串
        """
        return f"异常类型: {error.__class__.__name__}\n" \
               f"异常信息: {str(error)}\n\n" \
               f"堆栈跟踪:\n{traceback.format_exc()}"
    
    def _log_error(self, error_type: str, message: str, technical_detail: str):
        """
        记录错误日志
        
        Args:
            error_type: 错误类型
            message: 错误消息
            technical_detail: 技术详情
        """
        from datetime import datetime
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'message': message,
            'technical_detail': technical_detail
        }
        
        self.error_log.append(log_entry)
        
        # 限制日志大小
        if len(self.error_log) > 100:
            self.error_log = self.error_log[-100:]
    
    def get_error_log(self) -> List[Dict]:
        """
        获取错误日志
        
        Returns:
            错误日志列表
        """
        return self.error_log.copy()
    
    def clear_error_log(self):
        """清空错误日志"""
        self.error_log = []
    
    def create_error_dialog_text(self, error_info: ErrorInfo, show_technical: bool = False) -> str:
        """
        创建错误对话框文本
        
        Args:
            error_info: 错误信息
            show_technical: 是否显示技术详情
            
        Returns:
            对话框文本
        """
        lines = [
            f"❌ {error_info.title}",
            f"",
            f"{error_info.message}",
            f"",
            f"💡 建议:",
            f"{error_info.suggestion}",
        ]
        
        if show_technical:
            lines.extend([
                f"",
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                f"技术详情（用于调试）:",
                f"{error_info.technical_detail}",
            ])
        
        return '\n'.join(lines)


# 便捷函数
error_handler = ErrorHandler()


def handle_error(error: Exception, context: Dict = None) -> ErrorInfo:
    """
    便捷函数：处理错误
    
    Args:
        error: 异常对象
        context: 上下文信息
        
    Returns:
        错误信息
    """
    return error_handler.handle_error(error, context)


def get_friendly_error_message(error: Exception, context: Dict = None) -> str:
    """
    获取友好的错误消息
    
    Args:
        error: 异常对象
        context: 上下文信息
        
    Returns:
        友好的错误消息
    """
    error_info = handle_error(error, context)
    return error_handler.create_error_dialog_text(error_info)


# 装饰器：自动处理函数错误
def handle_errors(default_return=None, show_dialog=False):
    """
    错误处理装饰器
    
    Args:
        default_return: 出错时的默认返回值
        show_dialog: 是否显示错误对话框
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_info = handle_error(e)
                
                if show_dialog:
                    # 这里可以调用UI显示错误对话框
                    print(error_handler.create_error_dialog_text(error_info))
                
                return default_return
        return wrapper
    return decorator


# 特定错误处理函数
def handle_file_error(file_path: str, error: Exception) -> ErrorInfo:
    """
    处理文件相关错误
    
    Args:
        file_path: 文件路径
        error: 异常对象
        
    Returns:
        错误信息
    """
    return handle_error(error, {'path': file_path})


def handle_column_error(column_name: str, error: Exception) -> ErrorInfo:
    """
    处理列相关错误
    
    Args:
        column_name: 列名
        error: 异常对象
        
    Returns:
        错误信息
    """
    return handle_error(error, {'column': column_name})


def handle_data_error(rows: int, error: Exception) -> ErrorInfo:
    """
    处理数据相关错误
    
    Args:
        rows: 数据行数
        error: 异常对象
        
    Returns:
        错误信息
    """
    return handle_error(error, {'rows': rows})
