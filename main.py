import sys
import traceback
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow

# 全局异常钩子：捕获所有未处理的异常并弹窗显示，防止闪退
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
        print("".join(traceback.format_exception(exctype, value, tb)))

# 注册钩子
sys.excepthook = global_exception_hook

def main():
    # 启用高 DPI 支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        QApplication.styleHints().colorScheme()
    )
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("HR 数据处理工具集")
    
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
