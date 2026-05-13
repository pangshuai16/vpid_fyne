"""主窗口模块"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime
from typing import Optional, List
from ..device_info import USBDevice
from ..usb_scanner import scan_usb_devices, compare_devices
from .device_list import DeviceListPanel
from .device_detail import DeviceChangePanel
from ..constants import (
    BG, BG_HEADER, PRIMARY, TEXT, TEXT_SECONDARY, TEXT_ON_PRIMARY,
    PRIMARY_HOVER, PRIMARY_PRESSED, BORDER, ACCENT_GREEN,
    SELECT_BG, SELECT_FG, MENU_BG,
    FONT_SYSTEM, FONT_SYSTEM_BOLD, FONT_SYSTEM_SMALL,
    FONT_TITLE,
    AUTO_REFRESH_INTERVAL, APP_NAME, APP_VERSION,
)


class MainWindow:
    """USB 设备管理器主窗口"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry("1180x800")
        self.root.minsize(980, 680)

        self.devices: List[USBDevice] = []
        self.baseline_devices: List[USBDevice] = []
        self.auto_refresh = False
        self.refresh_interval = AUTO_REFRESH_INTERVAL

        self._setup_styles()
        self._setup_ui()
        self._setup_menu()
        self._bind_shortcuts()
        self._initial_scan()

    def _setup_styles(self):
        """配置 Tkinter 主题样式"""
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except:
            pass

        style.configure("TFrame", background=BG)
        style.configure("Main.TFrame", background=BG)
        style.configure("Header.TFrame", background=BG_HEADER)

        style.configure("Title.TLabel",
                        background=BG_HEADER,
                        foreground=TEXT,
                        font=FONT_TITLE,
                        padding=(16, 12))

        style.configure("Subtitle.TLabel",
                        background=BG_HEADER,
                        foreground=TEXT_SECONDARY,
                        font=FONT_SUBTITLE,
                        padding=(4, 0))

        style.configure("Primary.TButton",
                        background=PRIMARY,
                        foreground=TEXT_ON_PRIMARY,
                        font=FONT_SYSTEM_BOLD,
                        padding=(16, 6),
                        relief="flat",
                        borderwidth=0)

        style.configure("Secondary.TButton",
                        background=BG,
                        foreground=TEXT,
                        font=FONT_SYSTEM_BOLD,
                        padding=(16, 6),
                        relief="flat",
                        borderwidth=1)

        style.configure("Baseline.TButton",
                        background=ACCENT_GREEN,
                        foreground=TEXT_ON_PRIMARY,
                        font=FONT_SYSTEM_BOLD,
                        padding=(16, 6),
                        relief="flat",
                        borderwidth=0)

        style.configure("Flat.TCheckbutton",
                        background=BG,
                        foreground=TEXT,
                        font=FONT_SYSTEM,
                        padding=(6, 4),
                        relief="flat")

        style.configure("Status.TLabel",
                        background=BG_HEADER,
                        foreground=TEXT_SECONDARY,
                        font=FONT_SYSTEM_SMALL,
                        padding=(14, 8))

        style.configure("Treeview",
                        background="#FFFFFF",
                        foreground=TEXT,
                        fieldbackground="#FFFFFF",
                        font=FONT_SYSTEM,
                        rowheight=26,
                        borderwidth=1)

        style.configure("Treeview.Heading",
                        background=BG_HEADER,
                        foreground=TEXT,
                        font=FONT_SYSTEM_BOLD,
                        padding=(10, 6),
                        borderwidth=0,
                        relief="flat")

        style.map("Primary.TButton",
                  background=[("active", PRIMARY_HOVER), ("pressed", PRIMARY_PRESSED)],
                  foreground=[("active", TEXT_ON_PRIMARY), ("pressed", TEXT_ON_PRIMARY)])

        style.map("Secondary.TButton",
                  background=[("active", ITEM_HOVER_BG), ("pressed", BORDER)])

        style.map("Baseline.TButton",
                  background=[("active", "#0B5E0B"), ("pressed", "#084A08")],
                  foreground=[("active", TEXT_ON_PRIMARY), ("pressed", TEXT_ON_PRIMARY)])

        self.root.configure(bg=BG)

    def _setup_ui(self):
        """初始化 UI 组件"""
        header_frame = ttk.Frame(self.root, style="Header.TFrame")
        header_frame.pack(side="top", fill="x")

        title_container = ttk.Frame(header_frame, style="Header.TFrame")
        title_container.pack(fill="x", pady=(10, 4))

        title_label = ttk.Label(
            title_container,
            text=APP_NAME,
            style="Title.TLabel"
        )
        title_label.pack(side="left", padx=(14, 6))

        self.device_count_label = ttk.Label(
            title_container,
            text="0 个设备已连接",
            style="Subtitle.TLabel"
        )
        self.device_count_label.pack(side="left", pady=(2, 0))

        toolbar = ttk.Frame(header_frame, style="Header.TFrame")
        toolbar.pack(fill="x", padx=14, pady=(0, 10))

        self.refresh_btn = ttk.Button(
            toolbar,
            text="刷新",
            style="Primary.TButton",
            command=self._on_refresh
        )
        self.refresh_btn.pack(side="left", padx=(0, 8))

        self.baseline_btn = ttk.Button(
            toolbar,
            text="设为基准",
            style="Baseline.TButton",
            command=self._on_set_baseline
        )
        self.baseline_btn.pack(side="left", padx=(0, 8))

        self.copy_btn = ttk.Button(
            toolbar,
            text="复制",
            style="Secondary.TButton",
            command=self._on_copy
        )
        self.copy_btn.pack(side="left", padx=(0, 14))

        self.auto_refresh_var = tk.BooleanVar(value=False)
        self.auto_refresh_check = ttk.Checkbutton(
            toolbar,
            text="自动刷新 (3s)",
            style="Flat.TCheckbutton",
            variable=self.auto_refresh_var,
            command=self._toggle_auto_refresh
        )
        self.auto_refresh_check.pack(side="left")

        main_container = ttk.Frame(self.root, style="Main.TFrame")
        main_container.pack(side="top", fill="both", expand=True, padx=14, pady=(0, 14))

        paned = ttk.PanedWindow(main_container, orient="horizontal")
        paned.pack(fill="both", expand=True)

        self.device_list = DeviceListPanel(paned, on_select_callback=self._on_device_select)
        paned.add(self.device_list, weight=6)

        separator = ttk.Separator(paned, orient="vertical")
        paned.add(separator, weight=0)

        self.device_change = DeviceChangePanel(paned, on_select_callback=self._on_change_select)
        paned.add(self.device_change, weight=4)

        status_frame = ttk.Frame(self.root, style="Header.TFrame")
        status_frame.pack(side="bottom", fill="x")

        self.status_label = ttk.Label(
            status_frame,
            text="正在扫描 USB 设备...",
            style="Status.TLabel"
        )
        self.status_label.pack(side="left", padx=14, pady=8)

        self.baseline_status_label = ttk.Label(
            status_frame,
            text="",
            style="Status.TLabel"
        )
        self.baseline_status_label.pack(side="right", padx=14, pady=8)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_menu(self):
        """设置菜单栏"""
        menubar = tk.Menu(self.root, bg=MENU_BG, fg=TEXT, bd=0, relief="flat")
        self.root.config(menu=menubar)

        apple_menu = tk.Menu(menubar, tearoff=0, bg=MENU_BG, fg=TEXT)
        menubar.add_cascade(label="文件", menu=apple_menu)
        apple_menu.add_command(label="刷新设备列表", command=self._on_refresh, accelerator="Ctrl+R")
        apple_menu.add_command(label="设为基准", command=self._on_set_baseline)
        apple_menu.add_separator()
        apple_menu.add_command(label="退出", command=self._on_close)

        edit_menu = tk.Menu(menubar, tearoff=0, bg=MENU_BG, fg=TEXT)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="复制设备信息", command=self._on_copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="复制 VID", command=lambda: self._copy_field("vid"))
        edit_menu.add_command(label="复制 PID", command=lambda: self._copy_field("pid"))

        view_menu = tk.Menu(menubar, tearoff=0, bg=MENU_BG, fg=TEXT)
        menubar.add_cascade(label="视图", menu=view_menu)
        view_menu.add_checkbutton(label="自动刷新", variable=self.auto_refresh_var,
                                  command=self._toggle_auto_refresh)

        window_menu = tk.Menu(menubar, tearoff=0, bg=MENU_BG, fg=TEXT)
        menubar.add_cascade(label="窗口", menu=window_menu)
        window_menu.add_command(label="最小化", command=lambda: self.root.iconify())
        window_menu.add_separator()
        window_menu.add_command(label="缩放", command=self._toggle_fullscreen)

        help_menu = tk.Menu(menubar, tearoff=0, bg=MENU_BG, fg=TEXT)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用帮助", command=self._show_help)

    def _bind_shortcuts(self):
        """绑定快捷键"""
        self.root.bind("<Control-r>", lambda e: self._on_refresh())
        self.root.bind("<Control-R>", lambda e: self._on_refresh())
        self.root.bind("<Control-c>", lambda e: self._on_copy())
        self.root.bind("<Control-C>", lambda e: self._on_copy())

    def _initial_scan(self):
        """初始设备扫描"""
        self._update_status("正在扫描 USB 设备...")
        t = threading.Thread(target=self._scan_devices)
        t.daemon = True
        t.start()

    def _scan_devices(self):
        """执行设备扫描（在后台线程中运行）"""
        try:
            devices = scan_usb_devices()
            self.root.after(0, lambda d=devices: self._update_device_list(d))
        except Exception as e:
            self.root.after(0, lambda: self._update_status("扫描失败: {0}".format(str(e))))

    def _update_device_list(self, devices: List[USBDevice]):
        """更新设备列表显示"""
        prev_count = len(self.devices)
        self.devices = devices

        if not self.baseline_devices:
            self.baseline_devices = list(devices)
            self._update_baseline_status()

        added, removed = compare_devices(self.baseline_devices, devices)

        self.device_list.update_devices(devices)
        self.device_change.update_changes(added, removed)

        count = len(devices)
        timestamp = datetime.now().strftime("%H:%M:%S")
        change_info = ""
        if added:
            change_info += " (+{0})".format(len(added))
        if removed:
            change_info += " (-{0})".format(len(removed))

        self.device_count_label.config(text="{0} 个设备已连接{1}".format(count, change_info))
        self._update_status("最后刷新: {0} | 设备数: {1} → {2}".format(timestamp, prev_count, count))

        if added or removed:
            self._show_change_notification(added, removed)

    def _on_set_baseline(self):
        """设置基准设备列表"""
        if not self.devices:
            messagebox.showinfo("提示", "当前没有设备列表，请先刷新")
            return
        self.baseline_devices = list(self.devices)
        self._update_baseline_status()
        self.device_list.update_devices(self.devices)
        self.device_change.update_changes([], [])
        self._update_status("已将当前设备列表设为基准")
        self.device_count_label.config(text="{0} 个设备已连接".format(len(self.devices)))

    def _update_baseline_status(self):
        """更新基准状态显示"""
        if self.baseline_devices:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.baseline_status_label.config(
                text="基准: {0} 个设备 ({1})".format(len(self.baseline_devices), timestamp)
            )

    def _show_change_notification(self, added: List[USBDevice], removed: List[USBDevice]):
        """显示设备变化通知"""
        messages = []
        if added:
            messages.append("新增 {0} 个设备".format(len(added)))
        if removed:
            messages.append("移除 {0} 个设备".format(len(removed)))

        if messages:
            notification = " | ".join(messages)
            self.status_label.config(foreground=PRIMARY)
            self._update_status(notification)
            self.root.after(3000, lambda: self.status_label.config(foreground=TEXT_SECONDARY))

    def _update_status(self, message: str):
        """更新状态栏文本"""
        self.status_label.config(text=message)

    def _on_device_select(self, device: Optional[USBDevice]):
        """左侧全部设备列表选择回调"""
        if device:
            self.device_change.clear_selection()
            info = "{0} | VID: {1} | PID: {2} | 序列号: {3}".format(
                device.get_display_name(),
                device.vid or "N/A",
                device.pid or "N/A",
                device.serial or "N/A"
            )
            self._update_status(info)

    def _on_change_select(self, device: Optional[USBDevice]):
        """右侧变化设备列表选择回调"""
        if device:
            self.device_list.clear_selection()
            change_type = "新增" if device in self.device_change.added_devices else "移除"
            info = "[{4}] {0} | VID: {1} | PID: {2} | 序列号: {3}".format(
                device.get_display_name(),
                device.vid or "N/A",
                device.pid or "N/A",
                device.serial or "N/A",
                change_type
            )
            self._update_status(info)

    def _get_selected_device(self) -> Optional[USBDevice]:
        """获取当前选中的设备（从任意列表）"""
        device = self.device_list.get_selected_device()
        if device:
            return device
        return self.device_change.get_selected_device()

    def _on_refresh(self):
        """刷新按钮点击处理"""
        self.refresh_btn.config(state="disabled")
        self._update_status("正在扫描 USB 设备...")
        t = threading.Thread(target=self._scan_devices)
        t.daemon = True
        t.start()
        self.root.after(100, lambda: self.refresh_btn.config(state="normal"))

    def _on_copy(self):
        """复制按钮点击处理"""
        device = self._get_selected_device()
        if device:
            self.root.clipboard_clear()
            self.root.clipboard_append(device.to_clipboard_text())
            self._update_status("已复制到剪贴板: {0}".format(device.get_display_name()))
        else:
            messagebox.showinfo("提示", "请先选择一个设备")

    def _copy_field(self, field: str):
        """复制特定字段"""
        device = self._get_selected_device()
        if device:
            value = getattr(device, field, "") or "N/A"
            self.root.clipboard_clear()
            self.root.clipboard_append(value)
            self._update_status("已复制 {0}: {1}".format(field, value))

    def _toggle_auto_refresh(self):
        """切换自动刷新"""
        self.auto_refresh = self.auto_refresh_var.get()
        if self.auto_refresh:
            self._schedule_refresh()

    def _schedule_refresh(self):
        """调度自动刷新"""
        if self.auto_refresh:
            self.root.after(self.refresh_interval, self._on_refresh)
            self.root.after(self.refresh_interval, self._schedule_refresh)

    def _toggle_fullscreen(self):
        """切换全屏"""
        state = self.root.attributes("-fullscreen")
        self.root.attributes("-fullscreen", not state)

    def _show_help(self):
        """显示帮助对话框"""
        help_text = """使用帮助

【刷新设备】
点击刷新按钮或按 Ctrl+R 重新扫描 USB 设备

【设为基准】
将当前设备列表设为基准，后续刷新将与基准比对

【复制信息】
选择设备后点击复制按钮，或使用快捷键 Ctrl+C

【自动刷新】
勾选"自动刷新"选项，每3秒自动更新设备列表

【设备变化】
左侧显示全部设备列表
右侧上方显示相对基准新增的设备（绿色）
右侧下方显示相对基准移除的设备（红色）

【基准比对】
比对基于基准列表，点击"设为基准"可重置基准
首次启动自动设置基准
"""
        messagebox.showinfo("使用帮助", help_text)

    def _on_close(self):
        """窗口关闭处理"""
        self.auto_refresh = False
        self.root.destroy()

    def run(self):
        """运行主窗口"""
        self.root.mainloop()
