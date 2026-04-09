"""
自动更新模块
支持从 Gitee 和 GitHub 检查并下载更新
"""

import os
import sys
import json
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from core.version import get_version, compare_versions


class UpdateChecker(QThread):
    """检查更新线程"""
    update_available = pyqtSignal(dict)  # 有新版本
    no_update = pyqtSignal()  # 已是最新版本
    error = pyqtSignal(str)  # 检查失败

    def __init__(self, gitee_url, github_url):
        super().__init__()
        self.gitee_url = gitee_url
        self.github_url = github_url
        self.current_version = get_version()

    def run(self):
        try:
            # 优先尝试从 Gitee 获取
            latest_info = self._check_gitee()
            if not latest_info:
                # Gitee 失败则尝试 GitHub
                latest_info = self._check_github()

            if not latest_info:
                self.error.emit("无法连接到更新服务器，请检查网络连接")
                return

            # 比较版本
            if compare_versions(latest_info["version"], self.current_version) > 0:
                latest_info["current_version"] = self.current_version
                self.update_available.emit(latest_info)
            else:
                self.no_update.emit()

        except Exception as e:
            self.error.emit(f"检查更新失败：{str(e)}")

    def _check_gitee(self):
        """从 Gitee 检查更新"""
        try:
            # Gitee Release API
            api_url = f"{self.gitee_url}/releases/latest"
            req = urllib.request.Request(api_url)
            req.add_header('User-Agent', 'Mozilla/5.0')

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

                return {
                    "version": data.get("tag_name", "").lstrip("v"),
                    "name": data.get("name", ""),
                    "description": data.get("body", ""),
                    "published_at": data.get("published_at", ""),
                    "html_url": data.get("html_url", self.gitee_url),
                    "source": "Gitee"
                }
        except Exception as e:
            print(f"Gitee 检查更新失败：{e}")
            return None

    def _check_github(self):
        """从 GitHub 检查更新"""
        try:
            # GitHub Release API
            api_url = f"{self.github_url}/releases/latest"
            req = urllib.request.Request(api_url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            req.add_header('Accept', 'application/vnd.github.v3+json')

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

                return {
                    "version": data.get("tag_name", "").lstrip("v"),
                    "name": data.get("name", ""),
                    "description": data.get("body", ""),
                    "published_at": data.get("published_at", ""),
                    "html_url": data.get("html_url", self.github_url),
                    "source": "GitHub"
                }
        except Exception as e:
            print(f"GitHub 检查更新失败：{e}")
            return None


class UpdateDownloader(QThread):
    """下载更新包线程"""
    progress = pyqtSignal(int, str)  # 进度百分比，状态信息
    finished = pyqtSignal(str)  # 下载完成，返回文件路径
    error = pyqtSignal(str)  # 下载失败

    def __init__(self, download_url, output_dir):
        super().__init__()
        self.download_url = download_url
        self.output_dir = output_dir

    def run(self):
        try:
            self.progress.emit(0, "正在连接下载服务器...")

            req = urllib.request.Request(self.download_url)
            req.add_header('User-Agent', 'Mozilla/5.0')

            with urllib.request.urlopen(req, timeout=60) as response:
                total_size = response.getheader('Content-Length')
                if total_size:
                    total_size = int(total_size)

                # 确定文件名
                filename = self.download_url.split('/')[-1]
                if not filename.endswith(('.zip', '.exe', '.dmg')):
                    filename = "update.zip"

                output_path = os.path.join(self.output_dir, filename)

                # 下载文件
                downloaded = 0
                chunk_size = 8192

                with open(output_path, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size:
                            percent = int((downloaded / total_size) * 100)
                            self.progress.emit(
                                percent,
                                f"正在下载... {downloaded // 1024}KB / {total_size // 1024}KB"
                            )

                self.progress.emit(100, "下载完成")
                self.finished.emit(output_path)

        except Exception as e:
            self.error.emit(f"下载失败：{str(e)}")


class UpdateManager:
    """更新管理器 - 提供便捷的更新功能"""

    GITEE_REPO = "https://gitee.com/shibo8817/xinfud-tools"
    GITHUB_REPO = "https://github.com/Bob1817/xinfudTools"

    @staticmethod
    def get_update_info_url():
        """获取更新检查 URL"""
        return {
            "gitee": f"{UpdateManager.GITEE_REPO}/api/v5/repos/shibo8817/xinfud-tools/releases/latest",
            "github": f"https://api.github.com/repos/Bob1817/xinfudTools/releases/latest"
        }

    @staticmethod
    def open_download_page():
        """打开下载页面"""
        import webbrowser
        webbrowser.open(UpdateManager.GITEE_REPO)

    @staticmethod
    def get_app_path():
        """获取应用程序路径"""
        if getattr(sys, 'frozen', False):
            # 打包后的应用
            if sys.platform == 'darwin':
                # macOS .app
                return Path(sys.executable).parent.parent.parent
            elif sys.platform == 'win32':
                # Windows .exe
                return Path(sys.executable).parent
        else:
            # 开发环境
            return Path(__file__).parent.parent

    @staticmethod
    def is_frozen():
        """判断是否为打包后的应用"""
        return getattr(sys, 'frozen', False)

    @staticmethod
    def restart_app():
        """重启应用程序"""
        if UpdateManager.is_frozen():
            # 打包后的应用，重启可执行文件
            subprocess.Popen([sys.executable])
        else:
            # 开发环境，重启 Python 脚本
            script_path = Path(__file__).parent.parent / "main.py"
            subprocess.Popen([sys.executable, str(script_path)])

        # 退出当前进程
        os._exit(0)
