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
        from src.gui.main_window import MainWindow
        from src.constants import APP_NAME

        app = MainWindow()
        app.mainloop()
    except Exception as e:
        import traceback
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Fatal Error",
                "应用程序启动失败\n\n{0}".format(traceback.format_exc())
            )
            root.destroy()
        except Exception:
            sys.stderr.write("Fatal error: {0}\n{1}\n".format(str(e), traceback.format_exc()))
        sys.exit(1)


if __name__ == "__main__":
    main()
