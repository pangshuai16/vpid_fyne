import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime
from ..device_info import USBDevice
from ..usb_scanner import scan_usb_devices, compare_devices
from .device_list import DeviceListPanel
from .device_detail import DeviceDetailPanel


class MainWindow(object):
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("USB 设备管理器")
        self.root.geometry("1100x750")
        self.root.minsize(900, 650)

        self.devices = []
        self.old_devices = []
        self.auto_refresh = False
        self.refresh_interval = 3000
        self.is_first_scan = True

        self._setup_styles()
        self._setup_ui()
        self._setup_menu()
        self._bind_shortcuts()
        self._initial_scan()

    def _setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except:
            pass

        bg_color = "#FFFFFF"
        header_bg = "#F5F5F7"
        accent_color = "#007AFF"
        text_color = "#1D1D1F"
        secondary_text = "#86868B"

        style.configure("TFrame", background=bg_color)
        style.configure("Main.TFrame", background=bg_color)
        style.configure("Header.TFrame", background=header_bg)

        style.configure("Title.TLabel",
                        background=header_bg,
                        foreground=text_color,
                        font=("SF Pro Display", 18, "bold"),
                        padding=20)

        style.configure("Subtitle.TLabel",
                        background=header_bg,
                        foreground=secondary_text,
                        font=("SF Pro Text", 11),
                        padding=10)

        style.configure("Apple.TButton",
                        background=accent_color,
                        foreground="white",
                        font=("SF Pro Text", 11),
                        padding=10,
                        relief="flat")

        style.configure("Secondary.TButton",
                        background="#F5F5F7",
                        foreground=text_color,
                        font=("SF Pro Text", 11),
                        padding=10,
                        relief="flat")

        style.configure("Apple.TCheckbutton",
                        background=bg_color,
                        foreground=text_color,
                        font=("SF Pro Text", 11),
                        padding=5,
                        relief="flat")

        style.configure("Status.TLabel",
                        background=header_bg,
                        foreground=secondary_text,
                        font=("SF Pro Text", 10),
                        padding=10)

        style.configure("Treeview",
                        background=bg_color,
                        foreground=text_color,
                        fieldbackground=bg_color,
                        font=("SF Pro Text", 11),
                        rowheight=32)

        style.configure("Treeview.Heading",
                        background=header_bg,
                        foreground=text_color,
                        font=("SF Pro Text", 10, "bold"))

        style.configure("Treeview", borderwidth=0, relief="flat")
        style.configure("Treeview.Heading", borderwidth=0, relief="flat")

        style.map("Apple.TButton",
                  background=[("active", "#0056CC"), ("pressed", "#004499")],
                  foreground=[("active", "white"), ("pressed", "white")])

        style.map("Secondary.TButton",
                  background=[("active", "#E8E8ED"), ("pressed", "#D1D1D6")])

        self.root.configure(bg=bg_color)

    def _setup_ui(self):
        header_frame = ttk.Frame(self.root, style="Header.TFrame")
        header_frame.pack(side="top", fill="x")

        title_container = ttk.Frame(header_frame, style="Header.TFrame")
        title_container.pack(fill="x", pady=(10, 5))

        title_label = ttk.Label(
            title_container,
            text="USB 设备管理器",
            style="Title.TLabel"
        )
        title_label.pack(side="left", padx=(15, 10))

        self.device_count_label = ttk.Label(
            title_container,
            text="0 个设备已连接",
            style="Subtitle.TLabel"
        )
        self.device_count_label.pack(side="left", pady=(5, 0))

        toolbar = ttk.Frame(header_frame, style="Header.TFrame")
        toolbar.pack(fill="x", padx=15, pady=(0, 10))

        self.refresh_btn = ttk.Button(
            toolbar,
            text="↻ 刷新",
            style="Apple.TButton",
            command=self._on_refresh
        )
        self.refresh_btn.pack(side="left", padx=(0, 8))

        self.copy_btn = ttk.Button(
            toolbar,
            text="⧉ 复制",
            style="Secondary.TButton",
            command=self._on_copy
        )
        self.copy_btn.pack(side="left", padx=(0, 8))

        self.auto_refresh_var = tk.BooleanVar(value=False)
        self.auto_refresh_check = ttk.Checkbutton(
            toolbar,
            text="自动刷新 (3秒)",
            style="Apple.TCheckbutton",
            variable=self.auto_refresh_var,
            command=self._toggle_auto_refresh
        )
        self.auto_refresh_check.pack(side="left", padx=(15, 0))

        main_container = ttk.Frame(self.root, style="Main.TFrame")
        main_container.pack(side="top", fill="both", expand=True, padx=15, pady=(0, 15))

        paned = ttk.PanedWindow(main_container, orient="horizontal")
        paned.pack(fill="both", expand=True)

        self.device_list = DeviceListPanel(paned, on_select_callback=self._on_device_select)
        paned.add(self.device_list, weight=2)

        separator = ttk.Separator(paned, orient="vertical")
        paned.add(separator, weight=0)

        self.device_detail = DeviceDetailPanel(paned)
        paned.add(self.device_detail, weight=1)

        status_frame = ttk.Frame(self.root, style="Header.TFrame")
        status_frame.pack(side="bottom", fill="x")

        self.status_label = ttk.Label(
            status_frame,
            text="正在扫描 USB 设备...",
            style="Status.TLabel"
        )
        self.status_label.pack(side="left", padx=15, pady=5)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_menu(self):
        menubar = tk.Menu(self.root, bg="#FFFFFF", fg="#1D1D1F", bd=0, relief="flat")
        self.root.config(menu=menubar)

        apple_menu = tk.Menu(menubar, tearoff=0, bg="#FFFFFF", fg="#1D1D1F")
        menubar.add_cascade(label="Apple", menu=apple_menu)
        apple_menu.add_command(label="关于此应用", command=self._show_about)
        apple_menu.add_separator()
        apple_menu.add_command(label="退出", command=self._on_close, accelerator="⌘Q")

        file_menu = tk.Menu(menubar, tearoff=0, bg="#FFFFFF", fg="#1D1D1F")
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="刷新设备列表", command=self._on_refresh, accelerator="⌘R")
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._on_close)

        edit_menu = tk.Menu(menubar, tearoff=0, bg="#FFFFFF", fg="#1D1D1F")
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="复制设备信息", command=self._on_copy, accelerator="⌘C")
        edit_menu.add_command(label="复制 VID", command=lambda: self._copy_field("vid"))
        edit_menu.add_command(label="复制 PID", command=lambda: self._copy_field("pid"))

        view_menu = tk.Menu(menubar, tearoff=0, bg="#FFFFFF", fg="#1D1D1F")
        menubar.add_cascade(label="视图", menu=view_menu)
        view_menu.add_checkbutton(label="自动刷新", variable=self.auto_refresh_var, command=self._toggle_auto_refresh)

        window_menu = tk.Menu(menubar, tearoff=0, bg="#FFFFFF", fg="#1D1D1F")
        menubar.add_cascade(label="窗口", menu=window_menu)
        window_menu.add_command(label="最小化", command=lambda: self.root.iconify())
        window_menu.add_separator()
        window_menu.add_command(label="缩放", command=self._toggle_fullscreen)

        help_menu = tk.Menu(menubar, tearoff=0, bg="#FFFFFF", fg="#1D1D1F")
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用帮助", command=self._show_help)

    def _bind_shortcuts(self):
        self.root.bind("<Command-r>", lambda e: self._on_refresh())
        self.root.bind("<Command-R>", lambda e: self._on_refresh())
        self.root.bind("<Command-c>", lambda e: self._on_copy())
        self.root.bind("<Command-C>", lambda e: self._on_copy())

    def _initial_scan(self):
        self._update_status("正在扫描 USB 设备...")
        t = threading.Thread(target=self._scan_devices)
        t.daemon = True
        t.start()

    def _scan_devices(self):
        try:
            devices = scan_usb_devices()
            self.root.after(0, lambda: self._update_device_list(devices))
        except Exception as e:
            self.root.after(0, lambda: self._update_status("扫描失败: {0}".format(str(e))))

    def _update_device_list(self, devices):
        added = []
        removed = []

        if not self.is_first_scan and self.old_devices:
            added, removed = compare_devices(self.old_devices, devices)
            self._show_change_notification(added, removed)
        else:
            self.is_first_scan = False

        self.old_devices = self.devices[:]
        self.devices = devices
        self.device_list.update_devices(devices, added, removed)
        count = len(devices)
        timestamp = datetime.now().strftime("%H:%M:%S")
        change_info = ""
        if added:
            change_info += " (+{0})".format(len(added))
        if removed:
            change_info += " (-{0})".format(len(removed))

        self.device_count_label.config(text="{0} 个设备已连接{1}".format(count, change_info))
        self._update_status("最后刷新: {0}".format(timestamp))
        self.device_detail.set_device(None)

    def _show_change_notification(self, added, removed):
        messages = []
        if added:
            messages.append("新增 {0} 个设备".format(len(added)))
        if removed:
            messages.append("移除 {0} 个设备".format(len(removed)))

        if messages:
            notification = " | ".join(messages)
            self.status_label.config(foreground="#007AFF")
            self._update_status(notification)
            self.root.after(3000, lambda: self.status_label.config(foreground="#86868B"))

    def _update_status(self, message):
        self.status_label.config(text=message)

    def _on_device_select(self, device):
        self.device_detail.set_device(device)

    def _on_refresh(self):
        self.refresh_btn.config(state="disabled")
        self._update_status("正在扫描 USB 设备...")
        t = threading.Thread(target=self._scan_devices)
        t.daemon = True
        t.start()
        self.root.after(100, lambda: self.refresh_btn.config(state="normal"))

    def _on_copy(self):
        device = self.device_detail.get_current_device()
        if device:
            self.root.clipboard_clear()
            self.root.clipboard_write(device.to_clipboard_text())
            self._update_status("已复制到剪贴板")
        else:
            messagebox.showinfo("提示", "请先选择一个设备")

    def _copy_field(self, field):
        device = self.device_detail.get_current_device()
        if device:
            value = getattr(device, field, "") or "N/A"
            self.root.clipboard_clear()
            self.root.clipboard_write(value)
            self._update_status("已复制 {0}: {1}".format(field, value))

    def _toggle_auto_refresh(self):
        self.auto_refresh = self.auto_refresh_var.get()
        if self.auto_refresh:
            self._schedule_refresh()

    def _schedule_refresh(self):
        if self.auto_refresh:
            self.root.after(self.refresh_interval, self._on_refresh)
            self.root.after(self.refresh_interval, self._schedule_refresh)

    def _toggle_fullscreen(self):
        state = self.root.attributes("-fullscreen")
        self.root.attributes("-fullscreen", not state)

    def _show_about(self):
        about_text = """USB 设备管理器 v1.2.0

用于查看和管理系统中 USB 设备的详细信息

功能特点:
• 实时扫描 USB 设备
• 显示 VID/PID 信息
• 设备序列号追踪
• 制造商信息查看
• 自动刷新支持
• Apple 风格 UI 设计
• 新增/移除设备独立显示

© 2024 USB Manager
"""
        messagebox.showinfo("关于", about_text)

    def _show_help(self):
        help_text = """使用帮助

【刷新设备】
点击刷新按钮或按 ⌘R 重新扫描 USB 设备

【复制信息】
选择设备后点击复制按钮，或使用快捷键 ⌘C

【自动刷新】
勾选"自动刷新"选项，每3秒自动更新设备列表

【设备详情】
点击设备列表中的设备，查看详细信息

【新增/移除设备】
新增设备显示在绿色区域，移除设备显示在红色区域
"""
        messagebox.showinfo("使用帮助", help_text)

    def _on_close(self):
        self.auto_refresh = False
        self.root.destroy()

    def run(self):
        self.root.mainloop()
