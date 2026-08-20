"""USB 设备管理器 - 应用入口

启动期性能要点（按 Python 社区最佳实践）：
- 仅在主入口按需 import，避免触发 tkinter / pyusb / wmi 等重模块的隐式加载
- 日志级别使用 INFO（DEBUG 会带来大量格式化开销并拖慢启动）
- PyInstaller 打包时调用 multiprocessing.freeze_support() 以避免子进程问题
"""
import sys

# PyInstaller 启动加载屏（bootloader splash）：
# 仅在打包时配置了 splash 的 exe 里才能导入；源码运行会 ImportError。
# logo 图片在「点击 exe 的瞬间」即由引导程序展示，覆盖解压/初始化阶段。
try:
    import pyi_splash
except ImportError:
    pyi_splash = None


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

        app = MainWindow()
        # 主窗口已就绪，关闭 bootloader 加载屏，直接进入主界面
        if pyi_splash is not None:
            pyi_splash.close()
        app.mainloop()
    except Exception as e:
        import traceback
        if pyi_splash is not None:
            try:
                pyi_splash.close()
            except Exception:
                pass
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
