"""
输出路径选择弹窗
用于选择报表输出位置
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFileDialog, QCheckBox,
    QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from pathlib import Path
from core.config_manager import get_config_manager


class OutputPathDialog(QDialog):
    """输出路径选择弹窗"""
    
    def __init__(self, default_path: str = None, parent=None):
        """
        初始化
        
        Args:
            default_path: 默认路径
            parent: 父窗口
        """
        super().__init__(parent)
        
        # 获取配置管理器
        self.config = get_config_manager()
        
        # 设置默认路径
        if default_path:
            self.current_path = default_path
        else:
            self.current_path = self.config.get_output_path()
        
        self.remember_path = True
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("选择输出位置")
        self.setMinimumSize(500, 250)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # 标题
        title_label = QLabel("📁 选择报表输出位置")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 说明
        desc_label = QLabel("请选择生成报表的保存位置：")
        desc_label.setStyleSheet("color: #606266;")
        layout.addWidget(desc_label)
        
        # 路径选择
        path_group = QGroupBox("输出路径")
        path_layout = QHBoxLayout(path_group)
        
        self.path_edit = QLineEdit()
        self.path_edit.setText(self.current_path)
        self.path_edit.setReadOnly(True)
        self.path_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                background-color: #f5f7fa;
            }
        """)
        path_layout.addWidget(self.path_edit, stretch=1)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.setFixedWidth(80)
        self.browse_btn.clicked.connect(self._on_browse)
        path_layout.addWidget(self.browse_btn)
        
        layout.addWidget(path_group)
        
        # 选项
        options_group = QGroupBox("选项")
        options_layout = QVBoxLayout(options_group)
        
        self.remember_checkbox = QCheckBox("记住此位置（下次生成时自动使用）")
        self.remember_checkbox.setChecked(self.remember_path)
        self.remember_checkbox.stateChanged.connect(self._on_remember_changed)
        options_layout.addWidget(self.remember_checkbox)
        
        self.open_folder_checkbox = QCheckBox("生成后自动打开文件夹")
        self.open_folder_checkbox.setChecked(self.config.get_auto_open_folder())
        options_layout.addWidget(self.open_folder_checkbox)
        
        layout.addWidget(options_group)
        
        # 提示
        tip_label = QLabel(
            "💡 提示：您也可以在「设置」页面修改默认输出路径"
        )
        tip_label.setStyleSheet("color: #909399; font-size: 12px;")
        layout.addWidget(tip_label)
        
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.ok_btn = QPushButton("✅ 确认")
        self.ok_btn.setDefault(True)
        self.ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d6efd;
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0b5ed7;
            }
        """)
        self.ok_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self.ok_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_browse(self):
        """浏览按钮"""
        path = QFileDialog.getExistingDirectory(
            self,
            "选择输出文件夹",
            self.current_path,
            QFileDialog.Option.ShowDirsOnly
        )
        
        if path:
            self.current_path = path
            self.path_edit.setText(path)
    
    def _on_remember_changed(self, state):
        """记住位置选项改变"""
        self.remember_path = state == Qt.CheckState.Checked.value
    
    def _on_confirm(self):
        """确认"""
        path = self.path_edit.text().strip()
        
        if not path:
            QMessageBox.warning(self, "提示", "请选择输出路径")
            return
        
        # 检查路径是否存在
        path_obj = Path(path)
        if not path_obj.exists():
            try:
                path_obj.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    "错误",
                    f"无法创建目录：{path}\n\n错误：{str(e)}"
                )
                return
        
        # 检查写入权限
        if not path_obj.is_dir():
            QMessageBox.warning(self, "提示", "请选择有效的文件夹")
            return
        
        try:
            # 测试写入权限
            test_file = path_obj / ".write_test"
            test_file.touch()
            test_file.unlink()
        except Exception:
            QMessageBox.critical(
                self,
                "错误",
                f"没有权限写入该目录：{path}\n\n"
                f"请选择其他位置，或以管理员身份运行程序。"
            )
            return
        
        self.current_path = path
        
        # 保存设置
        if self.remember_path:
            self.config.set_output_path(path)
        
        self.config.set_auto_open_folder(self.open_folder_checkbox.isChecked())
        
        self.accept()
    
    def get_output_path(self) -> str:
        """
        获取选中的输出路径
        
        Returns:
            输出路径
        """
        return self.current_path
    
    def should_remember_path(self) -> bool:
        """
        是否记住路径
        
        Returns:
            是否记住
        """
        return self.remember_path
    
    def should_open_folder(self) -> bool:
        """
        是否自动打开文件夹
        
        Returns:
            是否自动打开
        """
        return self.open_folder_checkbox.isChecked()
    
    @staticmethod
    def select_output_path(default_path: str = None, parent=None) -> tuple:
        """
        静态方法：显示输出路径选择对话框
        
        Args:
            default_path: 默认路径
            parent: 父窗口
            
        Returns:
            (路径, 是否记住, 是否自动打开), 取消则返回 (None, False, False)
        """
        dialog = OutputPathDialog(default_path, parent)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return (
                dialog.get_output_path(),
                dialog.should_remember_path(),
                dialog.should_open_folder()
            )
        
        return None, False, False
