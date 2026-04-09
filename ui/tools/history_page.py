from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QFileDialog, QMessageBox, QTableWidgetItem
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from qfluentwidgets import (
    PushButton, TableWidget, InfoBar, InfoBarPosition,
    FluentIcon, StrongBodyLabel, CaptionLabel
)
from pathlib import Path
from db.database import Database
import subprocess


class HistoryPage(QWidget):
    """历史记录页面"""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.setObjectName("historyPage")
        self.db = db
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(24)
        layout.setContentsMargins(24, 24, 24, 24)

        # 标题栏
        header = QHBoxLayout()

        title = StrongBodyLabel("生成历史记录")
        header.addWidget(title)

        header.addStretch()

        # 刷新按钮
        refresh_btn = PushButton("刷新", self, FluentIcon.SYNC)
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        # 表格
        self.table = TableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "所属期", "数据条数", "生成时间", "源文件", "输出文件", "操作"
        ])
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(8)
        layout.addWidget(self.table)

        self._load_data()

    def _load_data(self):
        records = self.db.get_records()
        self.table.setRowCount(len(records))

        for i, r in enumerate(records):
            self.table.setItem(i, 0, QTableWidgetItem(r["period"]))

            item = QTableWidgetItem(str(r["total_records"]))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 1, item)

            created = r["created_at"]
            if created:
                created = created.split(".")[0]
            self.table.setItem(i, 2, QTableWidgetItem(created or ""))

            source = r["source_file"] or ""
            self.table.setItem(i, 3, QTableWidgetItem(source))

            output = r["output_file"] or ""
            self.table.setItem(i, 4, QTableWidgetItem(Path(output).name if output else ""))

            # 操作列
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(6)

            btn_view = PushButton("查看", self, FluentIcon.VIEW)
            btn_view.setFixedHeight(28)
            if output:
                btn_view.clicked.connect(lambda checked, p=output: self._open_file(p))
            else:
                btn_view.setEnabled(False)
            btn_layout.addWidget(btn_view)

            btn_folder = PushButton("所在文件夹", self, FluentIcon.FOLDER)
            btn_folder.setFixedHeight(28)
            if output:
                btn_folder.clicked.connect(lambda checked, p=output: self._open_folder(p))
            else:
                btn_folder.setEnabled(False)
            btn_layout.addWidget(btn_folder)

            btn_delete = PushButton("删除", self, FluentIcon.DELETE)
            btn_delete.setFixedHeight(28)
            btn_delete.clicked.connect(lambda checked, rid=r["id"]: self._delete_record(rid))
            btn_layout.addWidget(btn_delete)

            btn_layout.addStretch()

            self.table.setCellWidget(i, 5, btn_widget)

    @staticmethod
    def _open_file(file_path):
        """使用系统默认软件打开文件"""
        QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    @staticmethod
    def _open_folder(file_path):
        """打开文件所在文件夹"""
        folder = str(Path(file_path).parent)
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def _delete_record(self, record_id):
        reply = QMessageBox.question(
            self, "确认", "确定删除这条记录？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_record(record_id)
            self._load_data()
            InfoBar.success(
                title="成功",
                content="记录已删除",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
