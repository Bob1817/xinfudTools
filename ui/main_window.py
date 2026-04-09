import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl
from qfluentwidgets import FluentWindow, FluentIcon, NavigationItemPosition, InfoBar, InfoBarPosition
from db.database import Database
from ui.tools.tax_merge_page import TaxMergePage
from ui.tools.history_page import HistoryPage
from ui.settings_page import SettingsPage
from ui.update_dialog import UpdateDialog, DownloadDialog
from core.updater import UpdateChecker, UpdateManager
from core.version import get_version


class MainWindow(FluentWindow):
    """主窗口 - FluentWindow 风格"""

    def __init__(self):
        super().__init__()
        self.version = get_version()
        self.setWindowTitle(f"HR 数据处理工具集 v{self.version}")
        self.resize(1200, 800)

        # 初始化数据库
        self.db = Database()

        # 创建子界面
        self.taxMergePage = TaxMergePage(self.db, self)
        self.historyPage = HistoryPage(self.db, self)
        self.settingsPage = SettingsPage(self.db, self)

        # 添加导航项
        self.addSubInterface(
            self.taxMergePage,
            FluentIcon.DOCUMENT,
            "报税合并",
            NavigationItemPosition.TOP
        )
        self.addSubInterface(
            self.historyPage,
            FluentIcon.HISTORY,
            "历史记录",
            NavigationItemPosition.BOTTOM
        )
        self.addSubInterface(
            self.settingsPage,
            FluentIcon.SETTING,
            "设置",
            NavigationItemPosition.BOTTOM
        )

        # 初始化导航
        self.navigationInterface.setCurrentItem(
            self.taxMergePage.objectName()
        )

        # 启动时自动检查更新（静默）
        self._silent_check_update()

    def closeEvent(self, event):
        """关闭时清理数据库连接"""
        self.db.close()
        event.accept()

    def _silent_check_update(self):
        """静默检查更新"""
        self.checker = UpdateChecker(
            UpdateManager.GITEE_REPO,
            UpdateManager.GITHUB_REPO
        )
        self.checker.update_available.connect(self._on_silent_update)
        self.checker.no_update.connect(lambda: None)
        self.checker.error.connect(lambda: None)
        self.checker.start()

    def _on_silent_update(self, update_info):
        """静默更新提示"""
        InfoBar.info(
            title="发现新版本",
            content=f"发现新版本 {update_info['version']}，前往设置页更新",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=10000,
            parent=self
        )

    def check_for_updates(self):
        """手动检查更新"""
        self.switchTo(self.settingsPage.objectName())
        self.settingsPage._check_for_updates()
