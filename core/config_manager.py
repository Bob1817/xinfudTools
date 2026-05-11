"""
配置管理器模块
管理用户设置，包括输出路径等
"""

import json
import os
from pathlib import Path
from typing import Any, Optional, Dict
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class AppConfig:
    """应用配置数据类"""
    output_path: Optional[str] = None
    last_output_path: Optional[str] = None
    auto_open_folder: bool = True
    default_period: Optional[str] = None
    window_width: int = 1200
    window_height: int = 800
    last_payroll_dir: Optional[str] = None
    last_ss_dir: Optional[str] = None
    theme: str = "light"  # light, dark, auto
    language: str = "zh_CN"
    check_update_on_startup: bool = True
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AppConfig':
        """从字典创建"""
        return cls(**data)


class ConfigManager:
    """配置管理器"""
    
    # 默认配置
    DEFAULT_CONFIG = AppConfig()
    
    def __init__(self, config_file: str = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，None则使用默认路径
        """
        if config_file is None:
            # 默认配置文件路径：用户文档目录
            self.config_dir = Path.home() / "Documents" / "HR_Tools_Config"
            self.config_file = self.config_dir / "config.json"
        else:
            self.config_file = Path(config_file)
            self.config_dir = self.config_file.parent
        
        self._config: AppConfig = None
        self._load_config()
    
    def _load_config(self):
        """加载配置"""
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._config = AppConfig.from_dict(data)
            except Exception as e:
                print(f"加载配置文件失败: {e}，使用默认配置")
                self._config = AppConfig()
                self._save_config()
        else:
            # 配置文件不存在，创建默认配置
            self._config = AppConfig()
            self._save_config()
    
    def _save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get_output_path(self) -> str:
        """
        获取输出路径
        
        Returns:
            输出路径（如果不存在则返回默认路径）
        """
        if self._config.output_path and Path(self._config.output_path).exists():
            return self._config.output_path
        
        # 返回默认路径
        default_path = Path.home() / "Documents" / "HR工具输出"
        default_path.mkdir(parents=True, exist_ok=True)
        return str(default_path)
    
    def set_output_path(self, path: str) -> bool:
        """
        设置输出路径
        
        Args:
            path: 新的输出路径
            
        Returns:
            是否设置成功
        """
        try:
            path_obj = Path(path)
            
            # 检查路径是否存在，不存在则创建
            if not path_obj.exists():
                path_obj.mkdir(parents=True, exist_ok=True)
            
            # 检查是否有写入权限
            if not os.access(path_obj, os.W_OK):
                return False
            
            # 保存旧路径
            if self._config.output_path:
                self._config.last_output_path = self._config.output_path
            
            # 设置新路径
            self._config.output_path = str(path_obj)
            self._save_config()
            
            return True
            
        except Exception as e:
            print(f"设置输出路径失败: {e}")
            return False
    
    def reset_output_path(self) -> bool:
        """
        重置输出路径为默认值
        
        Returns:
            是否重置成功
        """
        self._config.output_path = None
        self._save_config()
        return True
    
    def get_last_output_path(self) -> Optional[str]:
        """
        获取上次使用的输出路径
        
        Returns:
            上次使用的输出路径
        """
        return self._config.last_output_path
    
    def update_last_output_path(self, path: str):
        """
        更新上次使用的输出路径
        
        Args:
            path: 路径
        """
        self._config.last_output_path = path
        self._save_config()
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置项名称
            default: 默认值
            
        Returns:
            配置值
        """
        return getattr(self._config, key, default)
    
    def set_config(self, key: str, value: Any) -> bool:
        """
        设置配置项
        
        Args:
            key: 配置项名称
            value: 配置值
            
        Returns:
            是否设置成功
        """
        try:
            setattr(self._config, key, value)
            self._save_config()
            return True
        except Exception as e:
            print(f"设置配置项失败: {e}")
            return False
    
    def get_auto_open_folder(self) -> bool:
        """
        获取是否自动打开文件夹
        
        Returns:
            是否自动打开
        """
        return self._config.auto_open_folder
    
    def set_auto_open_folder(self, auto_open: bool):
        """
        设置是否自动打开文件夹
        
        Args:
            auto_open: 是否自动打开
        """
        self._config.auto_open_folder = auto_open
        self._save_config()
    
    def get_default_period(self) -> Optional[str]:
        """
        获取默认所属期
        
        Returns:
            默认所属期（格式：YYYY-MM）
        """
        return self._config.default_period
    
    def set_default_period(self, period: str):
        """
        设置默认所属期
        
        Args:
            period: 所属期（格式：YYYY-MM）
        """
        self._config.default_period = period
        self._save_config()
    
    def get_last_directory(self, file_type: str) -> Optional[str]:
        """
        获取上次使用的目录
        
        Args:
            file_type: 文件类型（'payroll' 或 'ss'）
            
        Returns:
            目录路径
        """
        if file_type == 'payroll':
            return self._config.last_payroll_dir
        elif file_type == 'ss':
            return self._config.last_ss_dir
        return None
    
    def update_last_directory(self, file_type: str, directory: str):
        """
        更新上次使用的目录
        
        Args:
            file_type: 文件类型（'payroll' 或 'ss'）
            directory: 目录路径
        """
        if file_type == 'payroll':
            self._config.last_payroll_dir = directory
        elif file_type == 'ss':
            self._config.last_ss_dir = directory
        self._save_config()
    
    def get_window_size(self) -> tuple:
        """
        获取窗口大小
        
        Returns:
            (宽度, 高度)
        """
        return (self._config.window_width, self._config.window_height)
    
    def set_window_size(self, width: int, height: int):
        """
        设置窗口大小
        
        Args:
            width: 宽度
            height: 高度
        """
        self._config.window_width = width
        self._config.window_height = height
        self._save_config()
    
    def get_theme(self) -> str:
        """
        获取主题
        
        Returns:
            主题名称
        """
        return self._config.theme
    
    def set_theme(self, theme: str):
        """
        设置主题
        
        Args:
            theme: 主题名称（light, dark, auto）
        """
        if theme in ['light', 'dark', 'auto']:
            self._config.theme = theme
            self._save_config()
    
    def should_check_update_on_startup(self) -> bool:
        """
        获取是否启动时检查更新
        
        Returns:
            是否检查更新
        """
        return self._config.check_update_on_startup
    
    def set_check_update_on_startup(self, check: bool):
        """
        设置是否启动时检查更新
        
        Args:
            check: 是否检查
        """
        self._config.check_update_on_startup = check
        self._save_config()
    
    def get_all_config(self) -> Dict:
        """
        获取所有配置
        
        Returns:
            配置字典
        """
        return self._config.to_dict()
    
    def reset_to_default(self):
        """重置为默认配置"""
        self._config = AppConfig()
        self._save_config()
    
    def export_config(self, file_path: str) -> bool:
        """
        导出配置到文件
        
        Args:
            file_path: 导出文件路径
            
        Returns:
            是否导出成功
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._config.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """
        从文件导入配置
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            是否导入成功
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._config = AppConfig.from_dict(data)
                self._save_config()
            return True
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """
    获取全局配置管理器实例（单例模式）
    
    Returns:
        配置管理器实例
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_output_path() -> str:
    """便捷函数：获取输出路径"""
    return get_config_manager().get_output_path()


def set_output_path(path: str) -> bool:
    """便捷函数：设置输出路径"""
    return get_config_manager().set_output_path(path)


def get_config(key: str, default: Any = None) -> Any:
    """便捷函数：获取配置项"""
    return get_config_manager().get_config(key, default)


def set_config(key: str, value: Any) -> bool:
    """便捷函数：设置配置项"""
    return get_config_manager().set_config(key, value)
