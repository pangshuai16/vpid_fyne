"""启动闪屏（Splash）窗口

用途：Python 项目在启动阶段需要加载重型依赖（tkinter / pyusb / wmi
/pywin32 等），进程从运行到主界面显示之间存在等待间隔。此闪屏在主界面构建
前立即显示加载提示与动画进度条，让用户明确知道程序正在启动而不是卡死。

用法：
    splash = SplashScreen()
    splash.set_message("正在加载依赖库...")
    # ... 加载重型依赖 ...
    splash.close()  # 必须在创建主界面前关闭，避免双 Tk root 冲突
"""
import logging
import tkinter as tk
from tkinter import ttk

from ..constants import (
    APP_NAME,
    APP_VERSION,
    COLOR_PRIMARY,
    COLOR_TEXT,
    COLOR_TEXT_SECONDARY,
    COLOR_WHITE,
    UI_FONT_FAMILY,
)

logger = logging.getLogger(__name__)

_WIN_WIDTH = 360
_WIN_HEIGHT = 150


class SplashScreen(tk.Tk):
    """轻量启动闪屏窗口，抢占式立即上屏。"""

    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        # 无系统边框的极简闪屏窗口
        self.overrideredirect(True)
        self.configure(bg=COLOR_WHITE)
        self._center()
        self._build()
        # 立即刷新，确保首帧在当前 import 阻塞前就绘制上屏
        self.update()

    def _center(self):
        """将窗口居中显示"""
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - _WIN_WIDTH) // 2
        y = (sh - _WIN_HEIGHT) // 2
        self.geometry("{0}x{1}+{2}+{3}".format(_WIN_WIDTH, _WIN_HEIGHT, x, y))

    def _build(self):
        container = tk.Frame(self, bg=COLOR_WHITE, padx=24, pady=16)
        container.pack(fill="both", expand=True)

        # 标题使用主色调细条点缀，保持与主界面一致的视觉风格
        tk.Frame(container, bg=COLOR_PRIMARY, height=3).pack(
            fill="x", pady=(0, 12)
        )

        tk.Label(
            container,
            text="{0} v{1}".format(APP_NAME, APP_VERSION),
            font=(UI_FONT_FAMILY, 13, "bold"),
            fg=COLOR_TEXT, bg=COLOR_WHITE, anchor="center",
        ).pack(fill="x")

        self._message_label = tk.Label(
            container,
            text="",
            font=(UI_FONT_FAMILY, 10),
            fg=COLOR_TEXT_SECONDARY, bg=COLOR_WHITE, anchor="center",
        )
        self._message_label.pack(fill="x", pady=(12, 14))

        self._progress = ttk.Progressbar(
            container, mode="indeterminate", length=_WIN_WIDTH - 48
        )
        self._progress.pack(fill="x")
        self._progress.start(12)

        self.set_message("正在启动...")

    def set_message(self, text):
        """更新加载提示文本并立即重绘（在 import 阻塞期间也能刷新）"""
        try:
            self._message_label.config(text=text)
            self.update()
        except Exception:
            logger.debug("更新闪屏提示失败: %s", text)

    def close(self):
        """关闭闪屏。必须在构建主界面前调用，避免双 Tk root 冲突。"""
        try:
            self._progress.stop()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass