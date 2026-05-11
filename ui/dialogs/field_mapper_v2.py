"""
字段映射确认弹窗 V2
用于确认社保数据表的字段映射（四个必要字段）
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


class FieldMapperDialogV2(QDialog):
    """字段映射确认弹窗 V2"""
    
    # 四个必要字段
    REQUIRED_FIELDS = {
        '养老': '基本养老保险费',
        '医疗': '基本医疗保险费',
        '失业': '失业保险费',
        '公积金': '住房公积金',
    }
    
    def __init__(self, columns: List[str], suggested_mapping: Dict[str, Optional[str]], 
                 sheet_name: str, parent=None):
        """
        初始化
        
        Args:
            columns: 实际列名列表
            suggested_mapping: 建议的字段映射
            sheet_name: Sheet名称
            parent: 父窗口
        """
        super().__init__(parent)
        self.columns = columns
        self.suggested_mapping = suggested_mapping
        self.sheet_name = sheet_name
        self.current_mapping: Dict[str, str] = {}
        self.combo_boxes: Dict[str, QComboBox] = {}
        
        self._setup_ui()
        self._populate_data()
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle(f"确认字段映射 - {self.sheet_name}")
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
            "检测到社保表的字段名与标准字段不完全匹配，请确认以下四个必要字段的映射：\n"
            "如果映射不正确，请在下拉框中选择正确的列名。"
        )
        desc_label.setStyleSheet("color: #606266;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Sheet信息
        sheet_info = QLabel(f"📄 Sheet: {self.sheet_name}")
        sheet_info.setStyleSheet("color: #606266; font-weight: bold;")
        layout.addWidget(sheet_info)
        
        # 字段映射表格
        table_group = QGroupBox("字段映射（必须四个字段都映射）")
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
            "💡 提示：四个字段（养老、医疗、失业、公积金）都必须选择对应的列，\n"
            "    否则无法生成个税申报表。"
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
        column_options = ["- 请选择 -"] + self.columns
        
        # 设置行数
        self.mapping_table.setRowCount(len(self.REQUIRED_FIELDS))
        
        row = 0
        for target_field, display_name in self.REQUIRED_FIELDS.items():
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
                # 默认选择"- 请选择 -"
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
        
        if selected == "- 请选择 -":
            status_text = "❌ 未选择"
            status_color = "#f56c6c"  # 红色
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
            if selected != "- 请选择 -":
                self.current_mapping[target_field] = selected
            else:
                missing_required.append(self.REQUIRED_FIELDS[target_field])
        
        # 检查必要字段
        if missing_required:
            QMessageBox.warning(
                self, 
                "缺少必要字段",
                f"以下必要字段未选择：\n{', '.join(missing_required)}\n\n"
                f"请为所有字段选择对应的列。"
            )
            return
        
        # 验证是否四个字段都选择了
        if len(self.current_mapping) != 4:
            QMessageBox.warning(
                self,
                "字段不完整",
                f"只选择了 {len(self.current_mapping)}/4 个字段，\n"
                f"请为所有字段选择对应的列。"
            )
            return
        
        self.accept()
    
    def get_mapping(self) -> Dict[str, str]:
        """
        获取字段映射
        
        Returns:
            字段映射字典
        """
        return self.current_mapping.copy()
    
    @staticmethod
    def confirm_mapping(
        columns: List[str], 
        suggested_mapping: Dict[str, Optional[str]],
        sheet_name: str,
        parent=None
    ) -> Optional[Dict[str, str]]:
        """
        静态方法：显示字段映射确认对话框
        
        Args:
            columns: 实际列名列表
            suggested_mapping: 建议的字段映射
            sheet_name: Sheet名称
            parent: 父窗口
            
        Returns:
            确认的字段映射，取消则返回None
        """
        dialog = FieldMapperDialogV2(columns, suggested_mapping, sheet_name, parent)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_mapping()
        
        return None
