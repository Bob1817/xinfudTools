"""
Sheet选择弹窗
用于选择社保数据表中的Sheet
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QListWidgetItem, QPushButton,
    QGroupBox, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import List, Dict, Optional
from core.sheet_detector import SheetMatchResult


class SheetSelectorDialog(QDialog):
    """Sheet选择弹窗"""
    
    def __init__(self, match_results: List[SheetMatchResult], parent=None):
        """
        初始化
        
        Args:
            match_results: Sheet匹配结果列表
            parent: 父窗口
        """
        super().__init__(parent)
        self.match_results = match_results
        self.selected_sheet: Optional[str] = None
        self.selected_result: Optional[SheetMatchResult] = None
        
        self._setup_ui()
        self._populate_data()
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("选择社保数据表")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # 标题
        title_label = QLabel("📊 检测到多个社保数据表")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 说明
        desc_label = QLabel("请选择包含正确社保数据的Sheet：")
        desc_label.setStyleSheet("color: #606266;")
        layout.addWidget(desc_label)
        
        # Sheet列表
        list_group = QGroupBox("可用的Sheet")
        list_layout = QVBoxLayout(list_group)
        
        self.sheet_list = QListWidget()
        self.sheet_list.setMinimumHeight(150)
        self.sheet_list.currentRowChanged.connect(self._on_selection_changed)
        self.sheet_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        list_layout.addWidget(self.sheet_list)
        
        layout.addWidget(list_group)
        
        # 详情区域
        detail_group = QGroupBox("选中Sheet详情")
        detail_layout = QVBoxLayout(detail_group)
        
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMaximumHeight(150)
        detail_layout.addWidget(self.detail_text)
        
        layout.addWidget(detail_group)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.clicked.connect(self._on_refresh)
        btn_layout.addWidget(self.refresh_btn)
        
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.ok_btn = QPushButton("✅ 确认选择")
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
        self.ok_btn.setEnabled(False)
        btn_layout.addWidget(self.ok_btn)
        
        layout.addLayout(btn_layout)
    
    def _populate_data(self):
        """填充数据"""
        self.sheet_list.clear()
        
        for result in self.match_results:
            # 创建列表项
            item = QListWidgetItem()
            
            # 状态图标
            if result.is_perfect_match:
                status = "✅"
                tooltip = "完全匹配"
            elif result.match_score >= 0.7:
                status = "⚠️"
                tooltip = "部分匹配"
            else:
                status = "❓"
                tooltip = "匹配度较低"
            
            # 显示文本
            display_text = f"{status} {result.sheet_name}"
            if result.row_count > 0:
                display_text += f" ({result.row_count}行)"
            
            item.setText(display_text)
            item.setToolTip(tooltip)
            item.setData(Qt.ItemDataRole.UserRole, result)
            
            self.sheet_list.addItem(item)
        
        # 默认选中第一个
        if self.sheet_list.count() > 0:
            self.sheet_list.setCurrentRow(0)
    
    def _on_selection_changed(self, row: int):
        """选择改变时"""
        if row < 0 or row >= self.sheet_list.count():
            self.detail_text.clear()
            self.ok_btn.setEnabled(False)
            return
        
        item = self.sheet_list.item(row)
        result: SheetMatchResult = item.data(Qt.ItemDataRole.UserRole)
        
        # 更新详情
        details = self._format_details(result)
        self.detail_text.setText(details)
        
        self.ok_btn.setEnabled(True)
    
    def _format_details(self, result: SheetMatchResult) -> str:
        """格式化详情"""
        lines = [
            f"Sheet名称: {result.sheet_name}",
            f"数据行数: {result.row_count}",
            f"匹配度: {result.match_score:.1%}",
            f"",
            f"字段匹配情况:",
        ]
        
        if result.matched_fields:
            for target, actual in result.matched_fields.items():
                lines.append(f"  ✅ {target}: {actual}")
        
        if result.missing_fields:
            lines.append(f"")
            lines.append(f"缺失字段:")
            for field in result.missing_fields:
                lines.append(f"  ❌ {field}")
        
        if result.is_perfect_match:
            lines.append(f"")
            lines.append(f"✅ 该Sheet完全匹配，推荐使用")
        
        return '\n'.join(lines)
    
    def _on_item_double_clicked(self, item: QListWidgetItem):
        """双击项目"""
        self._on_confirm()
    
    def _on_confirm(self):
        """确认选择"""
        current_row = self.sheet_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择一个Sheet")
            return
        
        item = self.sheet_list.item(current_row)
        result: SheetMatchResult = item.data(Qt.ItemDataRole.UserRole)
        
        self.selected_sheet = result.sheet_name
        self.selected_result = result
        
        self.accept()
    
    def _on_refresh(self):
        """刷新"""
        # 这里可以重新检测Sheet
        QMessageBox.information(self, "提示", "请重新选择文件以刷新")
    
    def get_selected_sheet(self) -> Optional[str]:
        """
        获取选中的Sheet名称
        
        Returns:
            Sheet名称
        """
        return self.selected_sheet
    
    def get_selected_result(self) -> Optional[SheetMatchResult]:
        """
        获取选中的Sheet匹配结果
        
        Returns:
            Sheet匹配结果
        """
        return self.selected_result
    
    @staticmethod
    def select_sheet(match_results: List[SheetMatchResult], parent=None) -> Optional[SheetMatchResult]:
        """
        静态方法：显示选择对话框
        
        Args:
            match_results: Sheet匹配结果列表
            parent: 父窗口
            
        Returns:
            选中的Sheet匹配结果，取消则返回None
        """
        dialog = SheetSelectorDialog(match_results, parent)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_selected_result()
        
        return None
