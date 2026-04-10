"""
版本管理模块
"""

__version__ = "1.0.3"
__app_name__ = "HR 数据处理工具集"


def get_version():
    """获取当前版本号"""
    return __version__


def get_version_tuple():
    """获取版本号元组，用于比较"""
    return tuple(map(int, __version__.split(".")))


def compare_versions(v1, v2):
    """
    比较两个版本号
    返回: 
        1 如果 v1 > v2
        -1 如果 v1 < v2
        0 如果 v1 == v2
    """
    v1_tuple = tuple(map(int, v1.split(".")))
    v2_tuple = tuple(map(int, v2.split(".")))
    
    if v1_tuple > v2_tuple:
        return 1
    elif v1_tuple < v2_tuple:
        return -1
    else:
        return 0
