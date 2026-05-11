"""
字段映射确认弹窗
用于确认社保数据表的字段映射
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QPushButton,
    QGroupBox, QHeaderView, QMessageBox, QComboBox,
    QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import Dict, List, Optional


class FieldMapperDialog(QDialog):
    """字段映射确认弹窗"""
    
    # 目标字段
    TARGET_FIELDS = {
        '养老': '基本养老保险费',
        '医疗': '基本医疗保险费',
        '失业': '失业保险费',
        '公积金': '住房公积金',
        '姓名': '姓名',
        '身份证号': '身份证号'
    }
    
    def __init__(self, columns: List[str], suggested_mapping: Dict[str, Optional[str]], parent=None):
        """
        初始化
        
        Args:
            columns: 实际列名列表
            suggested_mapping: 建议的字段映射
            parent: 父窗口
        """
        super().__init__(parent)
        self.columns = columns
        self.suggested_mapping = suggested_mapping
        self.current_mapping: Dict[str, str] = {}
        self.combo_boxes: Dict[str, QComboBox] = {}
        
        self._setup_ui()
        self._populate_data()
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("确认字段映射")
        self.setMinimumSize(550, 450)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # 标题
        title_label = QLabel("⚠️ 字段匹配确认")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 说明
        desc_label = QLabel(
            "检测到社保表的字段名与标准字段不完全匹配，请确认以下字段映射：\n"
            "如果映射不正确，请在下拉框中选择正确的列名。"
        )
        desc_label.setStyleSheet("color: #606266;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # 字段映射表格
        table_group = QGroupBox("字段映射")
        table_layout = QVBoxLayout(table_group)
        
        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(3)
        self.mapping_table.setHorizontalHeaderLabels([
            "标准字段", "匹配的列", "状态"
        ])
        self.mapping_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.mapping_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.mapping_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.mapping_table.setColumnWidth(2, 80)
        self.mapping_table.setMinimumHeight(200)
        
        table_layout.addWidget(self.mapping_table)
        layout.addWidget(table_group)
        
        # 提示
        tip_label = QLabel(
            "💡 提示：如果某个标准字段没有对应的列，请选择「- 无对应列 -」，"
            "该字段将使用默认值 0.00"
        )
        tip_label.setStyleSheet("color: #909399; font-size: 12px;")
        tip_label.setWordWrap(True)
        layout.addWidget(tip_label)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.ok_btn = QPushButton("✅ 确认映射")
        self.ok_btn.setDefault(True)
        self.ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d6efd;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0b5ed7;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.ok_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self.ok_btn)
        
        layout.addLayout(btn_layout)
    
    def _populate_data(self):
        """填充数据"""
        # 准备列名选项
        column_options = ["- 无对应列 -"] + self.columns
        
        # 设置行数
        self.mapping_table.setRowCount(len(self.TARGET_FIELDS))
        
        row = 0
        for target_field, display_name in self.TARGET_FIELDS.items():
            # 标准字段
            target_item = QTableWidgetItem(display_name)
            target_item.setFlags(target_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.mapping_table.setItem(row, 0, target_item)
            
            # 匹配列（下拉框）
            combo = QComboBox()
            combo.addItems(column_options)
            
            # 设置建议值
            suggested = self.suggested_mapping.get(target_field)
            if suggested and suggested in self.columns:
                index = combo.findText(suggested)
                if index >= 0:
                    combo.setCurrentIndex(index)
            else:
                # 默认选择"无对应列"
                combo.setCurrentIndex(0)
            
            self.combo_boxes[target_field] = combo
            self.mapping_table.setCellWidget(row, 1, combo)
            
            # 状态
            self._update_status(row, target_field)
            
            # 连接信号
            combo.currentIndexChanged.connect(lambda idx, r=row, tf=target_field: self._update_status(r, tf))
            
            row += 1
    
    def _update_status(self, row: int, target_field: str):
        """更新状态"""
        combo = self.combo_boxes[target_field]
        selected = combo.currentText()
        
        if selected == "- 无对应列 -":
            status_text = "⚠️ 默认"
            status_color = "#e6a23c"  # 黄色
        else:
            status_text = "✅ 已映射"
            status_color = "#67c23a"  # 绿色
        
        status_item = QTableWidgetItem(status_text)
        status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        status_item.setForeground(Qt.GlobalColor(status_color))
        self.mapping_table.setItem(row, 2, status_item)
    
    def _on_confirm(self):
        """确认"""
        # 收集映射
        self.current_mapping = {}
        missing_required = []
        
        for target_field, combo in self.combo_boxes.items():
            selected = combo.currentText()
            if selected != "- 无对应列 -":
                self.current_mapping[target_field] = selected
            else:
                # 检查是否是必要字段
                if target_field in ['姓名', '身份证号']:
                    missing_required.append(self.TARGET_FIELDS[target_field])
        
        # 检查必要字段
        if missing_required:
            QMessageBox.warning(
                self, 
                "缺少必要字段",
                f"以下必要字段未映射：\n{', '.join(missing_required)}\n\n"
                f"请为这些字段选择对应的列，或取消操作。"
            )
            return
        
        # 显示确认信息
        mapped_count = len(self.current_mapping)
        total_count = len(self.TARGET_FIELDS)
        unmapped = total_count - mapped_count
        
        if unmapped > 0:
            reply = QMessageBox.question(
                self,
                "确认映射",
                f"已映射 {mapped_count}/{total_count} 个字段，"
                f"{unmapped} 个字段将使用默认值 0.00。\n\n"
                f"是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
        
        self.accept()
    
    def get_mapping(self) -> Dict[str, str]:
        """
        获取字段映射
        
        Returns:
            字段映射字典
        """
        return self.current_mapping.copy()
    
    def get_missing_fields(self) -> List[str]:
        """
        获取未映射的字段
        
        Returns:
            未映射字段列表
        """
        mapped = set(self.current_mapping.keys())
        all_fields = set(self.TARGET_FIELDS.keys())
        missing = all_fields - mapped
        return [self.TARGET_FIELDS[f] for f in missing]
    
    @staticmethod
    def confirm_mapping(
        columns: List[str], 
        suggested_mapping: Dict[str, Optional[str]], 
        parent=None
    ) -> Optional[Dict[str, str]]:
        """
        静态方法：显示字段映射确认对话框
        
        Args:
            columns: 实际列名列表
            suggested_mapping: 建议的字段映射
            parent: 父窗口
            
        Returns:
            确认的字段映射，取消则返回None
        """
        dialog = FieldMapperDialog(columns, suggested_mapping, parent)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_mapping()
        
        return None
