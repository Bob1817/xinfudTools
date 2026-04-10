import sys
import traceback
import os
import io
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow

# ==========================================
# 修复 PyInstaller 打包后的 stdout 缺失问题
# ==========================================
# 在 windowed 模式下，sys.stdout 为 None。
# 为了防止代码中的 print() 或 sys.stdout.flush() 导致崩溃，将其重定向到虚拟流。
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

# ==========================================
# 全局异常捕获：防止程序闪退并显示错误原因
# ==========================================
def global_exception_hook(exctype, value, tb):
    # 1. 记录错误日志
    log_path = Path(os.path.expanduser("~")) / "Documents" / "HR_Tools_Crash.log"
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"=== Crash Report ===\n")
            f.write(f"Exception Type: {exctype.__name__}\n")
            f.write(f"Exception Value: {value}\n\n")
            traceback.print_exception(exctype, value, tb, file=f)
    except: 
        pass
    
    # 2. 弹窗提示用户
    app = QApplication.instance()
    if app:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("程序发生严重错误")
        msg.setText("程序运行中遇到了未处理的异常，详细信息已保存。")
        msg.setInformativeText(f"请查看日志文件：\n{log_path}")
        msg.setDetailedText(''.join(traceback.format_exception(exctype, value, tb)))
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
    else:
        # 如果 QApplication 还没启动或已退出，打印到控制台
        # 注意：此时 stdout 已经被重定向，所以是安全的
        print("".join(traceback.format_exception(exctype, value, tb)))

# 注册钩子
sys.excepthook = global_exception_hook

def main():
    # 修复启动崩溃：移除错误的 setHighDpiScaleFactorRoundingPolicy 调用
    # 该调用之前传入了错误的枚举类型 (ColorScheme) 导致立即崩溃。
    # 现在依赖 Qt 默认的 DPI 行为。
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("HR 数据处理工具集")
    app.setApplicationVersion("1.0.11") # 更新版本号

    try:
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        # 捕获启动时的异常
        global_exception_hook(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
        sys.exit(1)

if __name__ == "__main__":
    main()
