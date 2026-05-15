"""USB 设备管理器 - 应用入口"""
import sys
import os
import logging


def _setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _ensure_path():
    """确保项目根目录在 sys.path 中"""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    if base not in sys.path:
        sys.path.insert(0, base)


def main():
    """应用主入口"""
    _ensure_path()
    _setup_logging()

    try:
        from PyQt5.QtWidgets import QApplication, QMessageBox
        from src.gui.main_window import MainWindow
        from src.constants import APP_NAME

        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        app.setApplicationName(APP_NAME)

        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        import traceback
        try:
            from PyQt5.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Fatal Error")
            msg.setText("应用程序启动失败")
            msg.setDetailedText("{0}\n\n{1}".format(str(e), traceback.format_exc()))
            msg.exec_()
        except Exception:
            sys.stderr.write("Fatal error: {0}\n{1}\n".format(str(e), traceback.format_exc()))
        sys.exit(1)


if __name__ == "__main__":
    main()
