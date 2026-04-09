"""
设置页面
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from qfluentwidgets import (
    PushButton, InfoBar, InfoBarPosition,
    FluentIcon, StrongBodyLabel, BodyLabel,
    CardWidget, MessageBox
)
from core.version import get_version
from core.updater import UpdateChecker, UpdateManager
from ui.update_dialog import UpdateDialog, DownloadDialog
import webbrowser


class SettingsPage(QWidget):
    """设置页面"""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsPage")
        self.db = db
        self.parent_window = parent
        self._build_ui()

    def _build_ui(self):
        """构建 UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(24)
        layout.setContentsMargins(24, 24, 24, 24)

        # 标题
        title = StrongBodyLabel("设置")
        layout.addWidget(title)

        # 关于卡片
        about_card = self._create_about_card()
        layout.addWidget(about_card)

        # 更新卡片
        update_card = self._create_update_card()
        layout.addWidget(update_card)

        layout.addStretch()

    def _create_about_card(self):
        """创建关于卡片"""
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        title = StrongBodyLabel("关于")
        layout.addWidget(title)

        version = get_version()
        info = BodyLabel(
            f"软件名称：HR 数据处理工具集\n"
            f"当前版本：v{version}\n"
            f"开发团队：HR Tools Team\n\n"
            f"本工具用于处理 HR 日常办公中的表格数据，\n"
            f"支持发薪表、社保表转换为个税申报表。"
        )
        info.setStyleSheet("color: #606266; line-height: 1.6;")
        layout.addWidget(info)

        return card

    def _create_update_card(self):
        """创建更新卡片"""
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        title = StrongBodyLabel("软件更新")
        layout.addWidget(title)

        desc = BodyLabel("检查并下载最新版本的软件更新")
        desc.setStyleSheet("color: #606266;")
        layout.addWidget(desc)

        # 按钮行
        btn_layout = QHBoxLayout()

        check_btn = PushButton("检查更新", self, FluentIcon.SYNC)
        check_btn.setFixedHeight(36)
        check_btn.clicked.connect(self._check_for_updates)
        btn_layout.addWidget(check_btn)

        download_btn = PushButton("前往下载", self, FluentIcon.DOWNLOAD)
        download_btn.setFixedHeight(36)
        download_btn.clicked.connect(self._open_download_page)
        btn_layout.addWidget(download_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return card

    def _check_for_updates(self):
        """检查更新"""
        InfoBar.info(
            title="检查更新",
            content="正在检查更新...",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=-1,  # 不自动关闭
            parent=self
        )

        self.checker = UpdateChecker(
            UpdateManager.GITEE_REPO,
            UpdateManager.GITHUB_REPO
        )
        self.checker.update_available.connect(self._on_update_available)
        self.checker.no_update.connect(self._on_no_update)
        self.checker.error.connect(self._on_check_error)
        self.checker.start()

    def _on_update_available(self, update_info):
        """有可用更新"""
        InfoBar.remove(self)

        dialog = UpdateDialog(update_info, self.window())
        if dialog.exec():
            # 用户点击了下载
            self._download_update(update_info)

    def _on_no_update(self):
        """已是最新版本"""
        InfoBar.remove(self)
        InfoBar.success(
            title="检查更新",
            content="✅ 当前已是最新版本",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

    def _on_check_error(self, error_msg):
        """检查更新失败"""
        InfoBar.remove(self)
        InfoBar.error(
            title="检查更新",
            content=error_msg,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )

    def _download_update(self, update_info):
        """下载更新"""
        # 获取下载链接
        download_url = update_info.get('download_url', '')
        
        if not download_url:
            # 如果没有直接下载链接，打开下载页面
            self._open_download_page()
            return

        dialog = DownloadDialog(download_url, self.window())
        dialog.exec()

    def _open_download_page(self):
        """打开下载页面"""
        webbrowser.open(UpdateManager.GITEE_REPO)
