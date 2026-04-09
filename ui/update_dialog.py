"""
更新对话框
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from qfluentwidgets import (
    MessageBox, PushButton, ProgressBar,
    InfoBar, InfoBarPosition, FluentIcon
)
from pathlib import Path
from core.updater import UpdateDownloader, UpdateManager
import webbrowser
import subprocess


class UpdateDialog(MessageBox):
    """更新提示对话框"""

    def __init__(self, update_info, parent=None):
        super().__init__(
            "发现新版本",
            f"当前版本：{update_info['current_version']}\n"
            f"最新版本：{update_info['version']}\n\n"
            f"{update_info.get('description', '请前往下载页面获取最新版本')}",
            parent
        )
        self.update_info = update_info
        self._init_custom_ui()

    def _init_custom_ui(self):
        """自定义 UI 初始化"""
        # 添加更多按钮
        self.download_btn = PushButton("前往下载", self, FluentIcon.DOWNLOAD)
        self.download_btn.clicked.connect(self._open_download_page)
        self.buttonLayout.addWidget(self.download_btn)

        # 修改取消按钮文本
        self.cancelButton.setText("稍后更新")

    def _open_download_page(self):
        """打开下载页面"""
        url = self.update_info.get('html_url', UpdateManager.GITEE_REPO)
        webbrowser.open(url)
        self.reject()


class DownloadDialog(QDialog):
    """下载进度对话框"""

    def __init__(self, download_url, parent=None):
        super().__init__(parent)
        self.download_url = download_url
        self.output_dir = str(Path.home() / "Downloads")
        self.downloaded_file = None
        self._build_ui()

    def _build_ui(self):
        """构建 UI"""
        self.setWindowTitle("下载更新")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setFixedHeight(250)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        # 标题
        title = QLabel("正在下载更新...")
        title.setFont(QFont("SF Pro", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(30)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #E0E0E0;
                border-radius: 10px;
                text-align: center;
                background-color: #F5F5F5;
            }
            QProgressBar::chunk {
                background-color: #0078D4;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # 状态标签
        self.status_label = QLabel("正在连接...")
        self.status_label.setStyleSheet("color: #666; font-size: 13px;")
        layout.addWidget(self.status_label)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedHeight(36)
        self.cancel_btn.setFixedWidth(100)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

        # 开始下载
        self._start_download()

    def _start_download(self):
        """开始下载"""
        self.worker = UpdateDownloader(self.download_url, self.output_dir)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_progress(self, percent, status):
        """更新进度"""
        self.progress_bar.setValue(percent)
        self.status_label.setText(status)

    def _on_finished(self, file_path):
        """下载完成"""
        self.downloaded_file = file_path
        self.status_label.setText("下载完成！")

        # 询问是否打开文件位置
        reply = QMessageBox.question(
            self,
            "下载完成",
            f"更新包已下载到：\n{file_path}\n\n是否打开文件位置？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._open_file_location(file_path)

        self.accept()

    def _on_error(self, error_msg):
        """下载失败"""
        QMessageBox.critical(self, "下载失败", error_msg)
        self.reject()

    def _open_file_location(self, file_path):
        """打开文件所在位置"""
        from pathlib import Path
        folder = str(Path(file_path).parent)

        if Path(file_path).root == '/':
            # macOS
            subprocess.run(['open', folder])
        else:
            # Windows
            subprocess.Popen(f'explorer "{folder}"', shell=True)

    def closeEvent(self, event):
        """关闭时取消下载"""
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
        event.accept()


class UpdateResultDialog(QDialog):
    """更新结果提示对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("更新提示")
        self.setModal(True)
        self.setMinimumWidth(450)
        self.setFixedHeight(200)
        self._build_ui()

    def _build_ui(self):
        """构建 UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # 提示信息
        info_label = QLabel(
            "✅ 更新包已下载完成！\n\n"
            "请手动安装更新：\n"
            "1. 关闭本应用程序\n"
            "2. 运行下载的安装包\n"
            "3. 按照提示完成更新"
        )
        info_label.setStyleSheet("font-size: 14px; line-height: 1.6;")
        layout.addWidget(info_label)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        open_folder_btn = QPushButton("打开下载文件夹")
        open_folder_btn.setFixedHeight(36)
        open_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border-radius: 6px;
                padding: 0 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #106EBE; }
        """)
        open_folder_btn.clicked.connect(self._open_download_folder)
        btn_layout.addWidget(open_folder_btn)

        close_btn = QPushButton("关闭")
        close_btn.setFixedHeight(36)
        close_btn.setFixedWidth(80)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _open_download_folder(self):
        """打开下载文件夹"""
        from pathlib import Path
        import subprocess

        folder = str(Path.home() / "Downloads")
        if Path(folder).root == '/':
            subprocess.run(['open', folder])
        else:
            subprocess.Popen(f'explorer "{folder}"', shell=True)
