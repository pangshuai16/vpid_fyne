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
        self.root.title("USB VID/PID 查看器 v1.0.0")
        self.root.geometry("800x500")
        self.root.minsize(600, 400)

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
            style.theme_use("vista")
        except:
            try:
                style.theme_use("clam")
            except:
                pass

        style.configure("Value.TLabel", foreground="#333333")
        style.configure("Header.TLabel", font=("Microsoft YaHei", 10, "bold"))

    def _setup_ui(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side="top", fill="x", padx=5, pady=5)

        self.refresh_btn = ttk.Button(toolbar, text="🔄 刷新", command=self._on_refresh)
        self.refresh_btn.pack(side="left", padx=2)

        self.copy_btn = ttk.Button(toolbar, text="📋 复制", command=self._on_copy)
        self.copy_btn.pack(side="left", padx=2)

        self.auto_refresh_var = tk.BooleanVar(value=False)
        self.auto_refresh_check = ttk.Checkbutton(
            toolbar,
            text="自动刷新 (3秒)",
            variable=self.auto_refresh_var,
            command=self._toggle_auto_refresh
        )
        self.auto_refresh_check.pack(side="left", padx=10)

        main_frame = ttk.Frame(self.root)
        main_frame.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        paned = ttk.PanedWindow(main_frame, orient="horizontal")
        paned.pack(fill="both", expand=True)

        self.device_list = DeviceListPanel(paned, on_select_callback=self._on_device_select)
        paned.add(self.device_list, weight=2)

        self.device_detail = DeviceDetailPanel(paned)
        paned.add(self.device_detail, weight=1)

        status_frame = ttk.Frame(self.root)
        status_frame.pack(side="bottom", fill="x")

        self.status_label = ttk.Label(status_frame, text="正在扫描...", relief="sunken", anchor="w")
        self.status_label.pack(side="left", fill="x", expand=True, padx=5, pady=2)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="刷新", command=self._on_refresh, accelerator="F5")
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._on_close, accelerator="Alt+F4")

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="复制设备信息", command=self._on_copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="复制 VID", command=lambda: self._copy_field("vid"))
        edit_menu.add_command(label="复制 PID", command=lambda: self._copy_field("pid"))

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self._show_about)

    def _bind_shortcuts(self):
        self.root.bind("<F5>", lambda e: self._on_refresh())
        self.root.bind("<Control-c>", lambda e: self._on_copy())

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
        if not self.is_first_scan and self.old_devices:
            added, removed = compare_devices(self.old_devices, devices)
            self._show_change_notification(added, removed)
        else:
            self.is_first_scan = False

        self.old_devices = self.devices[:]
        self.devices = devices
        self.device_list.update_devices(devices)
        count = len(devices)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._update_status("共 {0} 个 USB 设备 | 最后刷新: {1}".format(count, timestamp))
        self.device_detail.set_device(None)

    def _show_change_notification(self, added, removed):
        messages = []
        if added:
            for device in added:
                messages.append("➕ 新增: {0} ({1})".format(device.get_display_name(), device.get_vid_pid_string()))
        if removed:
            for device in removed:
                messages.append("➖ 移除: {0} ({1})".format(device.get_display_name(), device.get_vid_pid_string()))

        if messages:
            notification = "\n".join(messages)
            self.status_label.config(foreground="blue")
            self._update_status(notification)
            self.root.after(3000, lambda: self.status_label.config(foreground="black"))

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

    def _show_about(self):
        about_text = """USB VID/PID 查看器 v1.0.0

用于查看系统中USB设备的详细信息

支持:
- VID/PID 查看
- 设备序列号
- 制造商信息
- 驱动程序信息

© 2024 vpid_py
"""
        messagebox.showinfo("关于", about_text)

    def _on_close(self):
        self.auto_refresh = False
        self.root.destroy()

    def run(self):
        self.root.mainloop()
