"""设备列表面板 - 显示全部 USB 设备"""
import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Optional

from ..device_info import USBDevice
from ..constants import COLOR_PRIMARY, COLOR_TEXT, COLOR_BG, COLOR_WHITE


class DeviceListPanel(ttk.Frame):
    """显示全部 USB 设备列表的面板"""

    COLUMNS = ("vid", "pid", "name", "path")
    HEADERS = ("VID", "PID", "设备名称", "路径")
    WIDTHS = (70, 70, 200, 300)

    def __init__(self, parent, on_select=None):
        super(DeviceListPanel, self).__init__(parent)
        self.devices = []
        self._on_select_cb = on_select
        self._setup_ui()

    def _setup_ui(self):
        header_frame = tk.Frame(self, bg=COLOR_WHITE)
        header_frame.pack(fill=tk.X, padx=4, pady=(4, 2))

        tk.Label(
            header_frame, text="全部 USB 设备",
            font=("Segoe UI", 10, "bold"), fg=COLOR_TEXT, bg=COLOR_WHITE
        ).pack(side=tk.LEFT)

        self.count_label = tk.Label(
            header_frame, text="0",
            font=("Segoe UI", 10, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE
        )
        self.count_label.pack(side=tk.RIGHT)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        self.tree = ttk.Treeview(
            tree_frame, columns=self.COLUMNS, show="headings",
            selectmode="browse", height=10
        )

        for col, heading, width in zip(self.COLUMNS, self.HEADERS, self.WIDTHS):
            self.tree.heading(col, text=heading)
            stretch = tk.YES if col in ("name", "path") else tk.NO
            self.tree.column(col, width=width, minwidth=50, stretch=stretch)

        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _on_select(self, event=None):
        device = self.get_selected_device()
        if device and self._on_select_cb:
            self._on_select_cb(device)

    def update_devices(self, devices):
        self.devices = list(devices)
        self._populate()
        self.count_label.config(text=str(len(self.devices)))

    def _populate(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for device in self.devices:
            self.tree.insert("", tk.END, values=(
                device.get_formatted_vid(),
                device.get_formatted_pid(),
                device.get_display_name(),
                device.path or "-",
            ))

    def get_selected_device(self):
        sel = self.tree.selection()
        if not sel or not self.devices:
            return None
        idx = self.tree.index(sel[0])
        if 0 <= idx < len(self.devices):
            return self.devices[idx]
        return None

    def clear_selection(self):
        for item in self.tree.selection():
            self.tree.selection_remove(item)

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.devices = []
        self.count_label.config(text="0")
