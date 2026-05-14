import sys
import os


def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


sys.path.insert(0, get_base_path())


def main():
    try:
        from src.gui.main_window import MainWindow
        from PyQt5.QtWidgets import QApplication
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        import traceback
        from PyQt5.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Fatal Error")
        msg.setDetailedText("{0}\n\n{1}".format(str(e), traceback.format_exc()))
        msg.setWindowTitle("Fatal Error")
        msg.exec_()


if __name__ == "__main__":
    main()
