"""主窗口模块 - tkinter/ttk 实现"""
import os
import logging
import threading
import queue
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

from ..device_info import USBDevice
from ..usb_scanner import scan_usb_devices, compare_devices
from .device_list import DeviceListPanel
from .device_detail import DeviceChangePanel
from ..constants import (
    AUTO_REFRESH_INTERVAL_MS,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    APP_NAME,
    APP_VERSION,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SUCCESS,
    COLOR_TEXT,
    COLOR_TEXT_SECONDARY,
    COLOR_BORDER,
    COLOR_BG,
    COLOR_WHITE,
)

logger = logging.getLogger(__name__)


class MainWindow(tk.Tk):
    """USB 设备管理器主窗口

    核心逻辑（必须严格遵循）：
    1. 程序启动自动扫描一次，并设为基准列表
    2. 每次扫描，扫描结果直接显示在"全部USB设备"，
       并与基准列表比对，新增设备显示在"新增设备"，
       减少设备显示在"移除设备"
    3. 点击【设为基准】按钮时，将当前"全部USB设备"设定为新的基准列表
    """

    def __init__(self):
        super(MainWindow, self).__init__()
        self.title(APP_NAME)
        self.geometry("{0}x{1}".format(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT))
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        self.devices = []
        self.baseline_devices = []
        self._scanning = False
        self._auto_refresh_id = None
        self._result_queue = queue.Queue()

        self._apply_style()
        self._set_icon()
        self._build_toolbar()
        self._build_content()
        self._build_status_bar()
        self._build_menu()

        self._start_scan()
        self._poll_scan_result()

    def _apply_style(self):
        """配置 ttk 主题样式"""
        style = ttk.Style(self)
        available = style.theme_names()
        if "vista" in available:
            style.theme_use("vista")
        elif "clam" in available:
            style.theme_use("clam")

        style.configure("Treeview",
                        background=COLOR_WHITE,
                        foreground=COLOR_TEXT,
                        fieldbackground=COLOR_WHITE,
                        rowheight=26,
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                        background=COLOR_BG,
                        foreground=COLOR_TEXT,
                        font=("Segoe UI", 9, "bold"))
        style.map("Treeview",
                  background=[("selected", "#ECF5FF")],
                  foreground=[("selected", COLOR_PRIMARY)])

    def _set_icon(self):
        """设置窗口图标"""
        try:
            base_dir = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            icon_path = os.path.join(base_dir, "assets", "usb-icon.png")
            if os.path.exists(icon_path):
                icon = tk.PhotoImage(file=icon_path)
                self.iconphoto(False, icon)
                self._icon_ref = icon
        except Exception:
            pass

    def _build_toolbar(self):
        """构建顶部工具栏"""
        toolbar = tk.Frame(self, bg=COLOR_WHITE, pady=6, padx=12)
        toolbar.pack(fill=tk.X)

        self.device_count_label = tk.Label(
            toolbar, text="0 个设备已连接",
            font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, bg=COLOR_WHITE
        )
        self.device_count_label.pack(side=tk.LEFT, padx=(0, 12))

        self.refresh_btn = tk.Button(
            toolbar, text="刷新", font=("Segoe UI", 9, "bold"),
            bg=COLOR_PRIMARY, fg=COLOR_WHITE, activebackground=COLOR_PRIMARY_HOVER,
            activeforeground=COLOR_WHITE, bd=0, padx=14, pady=4,
            cursor="hand2", command=self._start_scan
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.baseline_btn = tk.Button(
            toolbar, text="设为基准", font=("Segoe UI", 9, "bold"),
            bg=COLOR_SUCCESS, fg=COLOR_WHITE, activebackground="#85CE61",
            activeforeground=COLOR_WHITE, bd=0, padx=14, pady=4,
            cursor="hand2", command=self._on_set_baseline
        )
        self.baseline_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.copy_btn = tk.Button(
            toolbar, text="复制", font=("Segoe UI", 9),
            bg=COLOR_WHITE, fg=COLOR_TEXT, activebackground=COLOR_BG,
            activeforeground=COLOR_PRIMARY, bd=1, relief=tk.SOLID,
            highlightbackground=COLOR_BORDER, padx=14, pady=4,
            cursor="hand2", command=self._on_copy
        )
        self.copy_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.auto_refresh_var = tk.BooleanVar(value=False)
        auto_cb = tk.Checkbutton(
            toolbar, text="自动刷新 (0.5s)", variable=self.auto_refresh_var,
            font=("Segoe UI", 9), fg=COLOR_TEXT, bg=COLOR_WHITE,
            activebackground=COLOR_WHITE, activeforeground=COLOR_TEXT,
            selectcolor=COLOR_WHITE, command=self._toggle_auto_refresh
        )
        auto_cb.pack(side=tk.RIGHT)

        sep = tk.Frame(self, bg=COLOR_BORDER, height=1)
        sep.pack(fill=tk.X)

    def _build_content(self):
        """构建主内容区域（左右分割）"""
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.device_list = DeviceListPanel(paned, on_select=self._on_device_select)
        paned.add(self.device_list, weight=3)

        self.device_change = DeviceChangePanel(paned, on_select=self._on_change_select)
        paned.add(self.device_change, weight=2)

    def _build_status_bar(self):
        """构建底部状态栏"""
        status_frame = tk.Frame(self, bg=COLOR_WHITE, pady=2, padx=8)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        sep = tk.Frame(self, bg=COLOR_BORDER, height=1)
        sep.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = tk.Label(
            status_frame, text="就绪",
            font=("Segoe UI", 9), fg=COLOR_TEXT_SECONDARY, bg=COLOR_WHITE,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.baseline_status_label = tk.Label(
            status_frame, text="",
            font=("Segoe UI", 9), fg=COLOR_TEXT_SECONDARY, bg=COLOR_WHITE,
            anchor=tk.E
        )
        self.baseline_status_label.pack(side=tk.RIGHT)

    def _build_menu(self):
        """构建菜单栏"""
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="刷新设备列表", command=self._start_scan, accelerator="Ctrl+R")
        file_menu.add_command(label="设为基准", command=self._on_set_baseline)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.destroy)
        menubar.add_cascade(label="文件", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="复制设备信息", command=self._on_copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="复制 VID", command=lambda: self._copy_field("vid"))
        edit_menu.add_command(label="复制 PID", command=lambda: self._copy_field("pid"))
        menubar.add_cascade(label="编辑", menu=edit_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_checkbutton(label="自动刷新", variable=self.auto_refresh_var,
                                   command=self._toggle_auto_refresh)
        menubar.add_cascade(label="视图", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="使用帮助", command=self._show_help)
        help_menu.add_command(label="关于", command=self._show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)

        self.config(menu=menubar)

        self.bind("<Control-r>", lambda e: self._start_scan())
        self.bind("<Control-R>", lambda e: self._start_scan())
        self.bind("<Control-c>", lambda e: self._on_copy())
        self.bind("<Control-C>", lambda e: self._on_copy())

    # ---- 扫描管理（线程安全） ----

    def _start_scan(self):
        """启动扫描（防并发）"""
        if self._scanning:
            return
        self._scanning = True
        self.refresh_btn.config(state=tk.DISABLED)
        self._update_status("正在扫描 USB 设备...")

        thread = threading.Thread(target=self._scan_worker, daemon=True)
        thread.start()

    def _scan_worker(self):
        """扫描工作线程 - 结果放入队列，不直接操作 UI"""
        try:
            devices = scan_usb_devices()
            self._result_queue.put(("ok", devices))
        except Exception as e:
            logger.error("扫描线程异常: %s", e)
            self._result_queue.put(("error", []))

    def _poll_scan_result(self):
        """主线程轮询扫描结果（线程安全）"""
        try:
            status, devices = self._result_queue.get_nowait()
            if status == "ok":
                self._update_device_list(devices)
            self._scanning = False
            self.refresh_btn.config(state=tk.NORMAL)
        except queue.Empty:
            pass
        self.after(50, self._poll_scan_result)

    def _update_device_list(self, devices):
        """更新设备列表显示

        核心逻辑：
        - 扫描结果直接显示在"全部USB设备"
        - 与基准列表比对，新增显示在"新增设备"，减少显示在"移除设备"
        - 首次扫描自动设为基准
        """
        prev_count = len(self.devices)
        self.devices = devices

        if not self.baseline_devices:
            self.baseline_devices = list(devices)
            self._update_baseline_status()

        added, removed = compare_devices(self.baseline_devices, devices)
        self.device_list.update_devices(devices)
        self.device_change.update_changes(added, removed)

        count = len(devices)
        ts = datetime.now().strftime("%H:%M:%S")
        change = ""
        if added:
            change += " (+{})".format(len(added))
        if removed:
            change += " (-{})".format(len(removed))

        self.device_count_label.config(text="{0} 个设备已连接{1}".format(count, change))
        self._update_status("最后刷新: {0} | 设备数: {1} → {2}".format(ts, prev_count, count))

    # ---- 用户操作 ----

    def _on_set_baseline(self):
        """设为基准：将当前全部USB设备设定为新的基准列表"""
        if not self.devices:
            messagebox.showinfo("提示", "当前没有设备列表，请先刷新", parent=self)
            return
        self.baseline_devices = list(self.devices)
        self._update_baseline_status()
        added, removed = compare_devices(self.baseline_devices, self.devices)
        self.device_change.update_changes(added, removed)
        self._update_status("已将当前设备列表设为基准")
        self.device_count_label.config(text="{0} 个设备已连接".format(len(self.devices)))

    def _on_copy(self):
        """复制选中设备信息到剪贴板"""
        device = self._get_selected_device()
        if device:
            text = device.to_clipboard_text()
            self.clipboard_clear()
            self.clipboard_append(text)
            self._update_status("已复制: {0}".format(device.get_display_name()))
        else:
            messagebox.showinfo("提示", "请先选择一个设备", parent=self)

    def _copy_field(self, field):
        """复制特定字段"""
        device = self._get_selected_device()
        if not device:
            return
        mapping = {"vid": device.get_formatted_vid, "pid": device.get_formatted_pid}
        value = mapping.get(field, lambda: "N/A")()
        self.clipboard_clear()
        self.clipboard_append(value)
        self._update_status("已复制 {0}: {1}".format(field.upper(), value))

    def _toggle_auto_refresh(self):
        """切换自动刷新"""
        if self.auto_refresh_var.get():
            self._schedule_auto_refresh()
        else:
            self._cancel_auto_refresh()

    def _schedule_auto_refresh(self):
        """调度下一次自动刷新"""
        self._cancel_auto_refresh()
        self._auto_refresh_id = self.after(
            AUTO_REFRESH_INTERVAL_MS, self._auto_refresh_tick
        )

    def _auto_refresh_tick(self):
        """自动刷新定时器回调"""
        self._start_scan()
        if self.auto_refresh_var.get():
            self._schedule_auto_refresh()

    def _cancel_auto_refresh(self):
        """取消自动刷新"""
        if self._auto_refresh_id is not None:
            self.after_cancel(self._auto_refresh_id)
            self._auto_refresh_id = None

    def _on_device_select(self, device):
        """左侧设备列表选中"""
        if device:
            self.device_change.clear_selection()
            self._update_status(self._device_info_text(device))

    def _on_change_select(self, device):
        """右侧变化列表选中"""
        if device:
            self.device_list.clear_selection()
            added_keys = {d.get_unique_key() for d in self.device_change.added_devices}
            tag = "新增" if device.get_unique_key() in added_keys else "移除"
            self._update_status("[{0}] {1}".format(tag, self._device_info_text(device)))

    # ---- 辅助方法 ----

    @staticmethod
    def _device_info_text(device):
        """生成设备信息文本"""
        return "{0} | VID: {1} | PID: {2} | 序列号: {3}".format(
            device.get_display_name(),
            device.get_formatted_vid(),
            device.get_formatted_pid(),
            device.serial or "N/A",
        )

    def _get_selected_device(self):
        """获取当前选中的设备"""
        return self.device_list.get_selected_device() or \
            self.device_change.get_selected_device()

    def _update_baseline_status(self):
        """更新基准状态"""
        if self.baseline_devices:
            ts = datetime.now().strftime("%H:%M:%S")
            self.baseline_status_label.config(
                text="基准: {0} 个设备 ({1})".format(len(self.baseline_devices), ts)
            )

    def _update_status(self, message):
        """更新状态栏"""
        self.status_label.config(text=message)

    def _show_about(self):
        messagebox.showinfo("关于",
            "{0} v{1}\n\n用于查看和管理系统中 USB 设备的详细信息\n\n"
            "功能: 实时扫描 / VID-PID 显示 / 序列号追踪 / 自动刷新 / 基准比对\n\n"
            "(C) 2025 {0}".format(APP_NAME, APP_VERSION),
            parent=self)

    def _show_help(self):
        messagebox.showinfo("使用帮助",
            "【刷新】Ctrl+R 或点击刷新按钮\n"
            "【设为基准】将当前列表设为基准，后续刷新自动比对\n"
            "【复制】选中设备后 Ctrl+C 复制完整信息\n"
            "【自动刷新】勾选后每 0.5 秒自动更新\n"
            "【设备变化】左侧=全部设备，右侧上方=新增(绿)，右侧下方=移除(红)",
            parent=self)
