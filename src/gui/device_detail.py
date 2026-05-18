"""设备变化面板 - 显示新增和移除的设备"""
import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Optional

from ..device_info import USBDevice
from ..constants import (
    COLOR_SUCCESS, COLOR_SUCCESS_BG, COLOR_DANGER, COLOR_DANGER_BG,
    COLOR_PRIMARY, COLOR_TEXT, COLOR_BORDER, COLOR_WHITE,
)


class _ChangeSection(ttk.Frame):
    """单个变化区域（新增或移除）"""

    COLUMNS = ("vid", "pid", "name")
    HEADERS = ("VID", "PID", "设备名称")
    WIDTHS = (70, 70, 200)

    def __init__(self, parent, title, header_bg, text_color, on_select=None):
        super(_ChangeSection, self).__init__(parent)
        self.devices = []
        self._on_select_cb = on_select
        self._setup_ui(title, header_bg, text_color)

    def _setup_ui(self, title, header_bg, text_color):
        header_frame = tk.Frame(self, bg=header_bg)
        header_frame.pack(fill=tk.X, padx=2, pady=(2, 1))

        tk.Label(
            header_frame, text=title,
            font=("Segoe UI", 9, "bold"), fg=text_color, bg=header_bg
        ).pack(side=tk.LEFT, padx=6, pady=3)

        self.count_label = tk.Label(
            header_frame, text="0",
            font=("Segoe UI", 9, "bold"), fg=text_color, bg=header_bg
        )
        self.count_label.pack(side=tk.RIGHT, padx=6, pady=3)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=(0, 2))

        self.tree = ttk.Treeview(
            tree_frame, columns=self.COLUMNS, show="headings",
            selectmode="browse", height=5
        )

        for col, heading, width in zip(self.COLUMNS, self.HEADERS, self.WIDTHS):
            self.tree.heading(col, text=heading)
            stretch = tk.YES if col == "name" else tk.NO
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


class DeviceChangePanel(ttk.Frame):
    """显示新增和移除 USB 设备的面板"""

    def __init__(self, parent, on_select=None):
        super(DeviceChangePanel, self).__init__(parent)
        self._on_select_cb = on_select
        self._setup_ui()

    def _setup_ui(self):
        self.added_section = _ChangeSection(
            self, "+ 新增设备", COLOR_SUCCESS_BG, COLOR_SUCCESS,
            on_select=self._forward_select
        )
        self.added_section.pack(fill=tk.BOTH, expand=True, padx=4, pady=(4, 2))

        sep = tk.Frame(self, bg=COLOR_BORDER, height=1)
        sep.pack(fill=tk.X, padx=4, pady=2)

        self.removed_section = _ChangeSection(
            self, "- 移除设备", COLOR_DANGER_BG, COLOR_DANGER,
            on_select=self._forward_select
        )
        self.removed_section.pack(fill=tk.BOTH, expand=True, padx=4, pady=(2, 4))

    def _forward_select(self, device):
        if self._on_select_cb:
            self._on_select_cb(device)

    @property
    def added_devices(self):
        return self.added_section.devices

    @property
    def removed_devices(self):
        return self.removed_section.devices

    def update_changes(self, added_devices, removed_devices):
        self.added_section.update_devices(added_devices)
        self.removed_section.update_devices(removed_devices)

    def get_selected_device(self):
        device = self.added_section.get_selected_device()
        if device:
            return device
        return self.removed_section.get_selected_device()

    def clear_selection(self):
        self.added_section.clear_selection()
        self.removed_section.clear_selection()

    def clear(self):
        self.added_section.clear()
        self.removed_section.clear()
