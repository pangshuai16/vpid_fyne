"""USB 设备管理器 - 应用入口

启动期性能要点（按 Python 社区最佳实践）：
- 仅在主入口按需 import，避免触发 tkinter / pyusb / wmi 等重模块的隐式加载
- 日志级别使用 INFO（DEBUG 会带来大量格式化开销并拖慢启动）
- PyInstaller 打包时调用 multiprocessing.freeze_support() 以避免子进程问题
"""
import sys


def _ensure_path():
    """确保项目根目录在 sys.path 中（仅源码运行场景需要）"""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        import os
        base = os.path.dirname(os.path.abspath(__file__))
    if base not in sys.path:
        sys.path.insert(0, base)


def _setup_logging():
    """配置日志（INFO 级别；DEBUG 仅在显式环境变量开启时使用）"""
    import logging
    import os
    level = logging.DEBUG if os.environ.get("VPID_DEBUG") else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    """应用主入口"""
    # PyInstaller 打包后必须尽早调用，否则 Windows 下多进程会无限重启
    if getattr(sys, 'frozen', False):
        from multiprocessing import freeze_support
        freeze_support()

    _ensure_path()
    _setup_logging()

    try:
        from src.gui.main_window import MainWindow
        from src.constants import APP_NAME  # noqa: F401  保留以便未来引用

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
