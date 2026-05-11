"""
设置页面（优化版）
新增输出路径设置功能
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from qfluentwidgets import (
    PushButton, InfoBar, InfoBarPosition,
    FluentIcon, StrongBodyLabel, BodyLabel,
    CardWidget, MessageBox, ToggleButton,
    LineEdit
)
from core.version import get_version
from core.updater import UpdateChecker, UpdateManager
from core.config_manager import get_config_manager
from ui.update_dialog import UpdateDialog, DownloadDialog
import webbrowser
from pathlib import Path


class SettingsPage(QWidget):
    """设置页面（优化版）"""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsPage")
        self.db = db
        self.parent_window = parent
        
        # 获取配置管理器
        self.config = get_config_manager()
        
        self._build_ui()

    def _build_ui(self):
        """构建 UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(24)
        layout.setContentsMargins(24, 24, 24, 24)

        # 标题
        title = StrongBodyLabel("设置")
        layout.addWidget(title)

        # 输出设置卡片
        output_card = self._create_output_settings_card()
        layout.addWidget(output_card)

        # 更新卡片
        update_card = self._create_update_card()
        layout.addWidget(update_card)

        # 关于卡片
        about_card = self._create_about_card()
        layout.addWidget(about_card)

        layout.addStretch()

    def _create_output_settings_card(self):
        """创建输出设置卡片"""
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setSpacing(16)

        title = StrongBodyLabel("📁 输出设置")
        layout.addWidget(title)

        desc = BodyLabel("配置报表文件的默认输出位置")
        desc.setStyleSheet("color: #606266;")
        layout.addWidget(desc)

        # 输出路径设置
        path_layout = QHBoxLayout()
        
        path_label = BodyLabel("默认输出路径：")
        path_layout.addWidget(path_label)
        
        self.path_edit = LineEdit()
        self.path_edit.setText(self.config.get_output_path())
        self.path_edit.setReadOnly(True)
        self.path_edit.setFixedWidth(350)
        path_layout.addWidget(self.path_edit, stretch=1)
        
        browse_btn = PushButton("浏览...", self, FluentIcon.FOLDER)
        browse_btn.setFixedWidth(100)
        browse_btn.clicked.connect(self._on_browse_output_path)
        path_layout.addWidget(browse_btn)
        
        layout.addLayout(path_layout)

        # 选项
        options_layout = QHBoxLayout()
        
        # 自动打开文件夹
        self.auto_open_toggle = ToggleButton("生成后自动打开文件夹")
        self.auto_open_toggle.setChecked(self.config.get_auto_open_folder())
        self.auto_open_toggle.checkedChanged.connect(self._on_auto_open_changed)
        options_layout.addWidget(self.auto_open_toggle)
        
        options_layout.addStretch()
        
        layout.addLayout(options_layout)

        # 重置按钮
        reset_btn = PushButton("恢复默认设置", self, FluentIcon.RETURN)
        reset_btn.setFixedWidth(150)
        reset_btn.clicked.connect(self._on_reset_output_settings)
        layout.addWidget(reset_btn)

        return card

    def _create_update_card(self):
        """创建更新卡片"""
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        title = StrongBodyLabel("🔄 软件更新")
        layout.addWidget(title)

        desc = BodyLabel("检查并下载最新版本的软件更新")
        desc.setStyleSheet("color: #606266;")
        layout.addWidget(desc)

        # 选项
        options_layout = QHBoxLayout()
        
        self.check_update_toggle = ToggleButton("启动时自动检查更新")
        self.check_update_toggle.setChecked(self.config.should_check_update_on_startup())
        self.check_update_toggle.checkedChanged.connect(self._on_check_update_changed)
        options_layout.addWidget(self.check_update_toggle)
        
        options_layout.addStretch()
        
        layout.addLayout(options_layout)

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

    def _create_about_card(self):
        """创建关于卡片"""
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        title = StrongBodyLabel("ℹ️ 关于")
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

    def _on_browse_output_path(self):
        """浏览输出路径"""
        current_path = self.path_edit.text()
        
        path = QFileDialog.getExistingDirectory(
            self,
            "选择默认输出文件夹",
            current_path,
            QFileDialog.Option.ShowDirsOnly
        )
        
        if path:
            # 验证路径
            path_obj = Path(path)
            
            # 检查写入权限
            try:
                test_file = path_obj / ".write_test"
                test_file.touch()
                test_file.unlink()
            except Exception:
                MessageBox.critical(
                    self,
                    "错误",
                    f"无法写入该目录：{path}\n\n"
                    f"请选择其他位置，或以管理员身份运行程序。"
                )
                return
            
            # 更新配置
            if self.config.set_output_path(path):
                self.path_edit.setText(path)
                
                InfoBar.success(
                    title="设置已保存",
                    content=f"默认输出路径已更新",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
            else:
                MessageBox.critical(
                    self,
                    "错误",
                    "保存设置失败，请重试"
                )

    def _on_auto_open_changed(self, checked):
        """自动打开文件夹选项改变"""
        self.config.set_auto_open_folder(checked)

    def _on_check_update_changed(self, checked):
        """检查更新选项改变"""
        self.config.set_check_update_on_startup(checked)

    def _on_reset_output_settings(self):
        """重置输出设置"""
        reply = MessageBox.question(
            self,
            "确认重置",
            "确定要恢复默认输出设置吗？\n\n"
            "这将清除您自定义的输出路径。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 重置配置
            self.config.reset_output_path()
            
            # 更新UI
            self.path_edit.setText(self.config.get_output_path())
            self.auto_open_toggle.setChecked(True)
            
            InfoBar.success(
                title="设置已重置",
                content="输出设置已恢复默认值",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

    def refresh_settings(self):
        """刷新设置显示"""
        self.path_edit.setText(self.config.get_output_path())
        self.auto_open_toggle.setChecked(self.config.get_auto_open_folder())
        self.check_update_toggle.setChecked(self.config.should_check_update_on_startup())

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
        dialog = UpdateDialog(update_info, self.window())
        if dialog.exec():
            # 用户点击了下载
            self._download_update(update_info)

    def _on_no_update(self):
        """已是最新版本"""
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
        print(f"更新检查错误: {error_msg}")
        
        # 创建通用的错误提示对话框
        msg_box = MessageBox(
            "检查更新失败",
            f"无法获取最新版本信息。\n\n"
            f"可能原因：\n"
            "1. 网络连接异常\n"
            "2. API 请求频率受限\n"
            "3. 仓库状态变更\n\n"
            f"您可以点击「前往下载」手动查看最新版本。",
            self.window()
        )
        msg_box.yesButton.setText("前往下载")
        msg_box.cancelButton.setText("关闭")
        if msg_box.exec():
            self._open_download_page()

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
