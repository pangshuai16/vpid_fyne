"""设备列表面板组件 - 显示全部 USB 设备"""
import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Callable
from ..device_info import USBDevice
from ..constants import (
    APPLE_WHITE,
    APPLE_LIGHT_GRAY,
    APPLE_BLUE,
    APPLE_TEXT,
    APPLE_SECONDARY_TEXT
)


class DeviceListPanel(ttk.Frame):
    """显示全部 USB 设备列表的面板"""

    def __init__(self, parent, on_select_callback: Optional[Callable[[USBDevice], None]] = None):
        super(DeviceListPanel, self).__init__(parent)
        self.on_select_callback = on_select_callback
        self.devices: List[USBDevice] = []
        self._setup_ui()

    def _setup_ui(self):
        """初始化 UI 组件"""
        container = tk.Frame(self, bg=APPLE_WHITE)
        container.pack(fill="both", expand=True)

        all_header = tk.Frame(container, bg=APPLE_LIGHT_GRAY, padx=16, pady=12)
        all_header.pack(fill="x")

        tk.Label(
            all_header,
            text="全部设备",
            font=("-apple-system", "SF Pro Display", 13, "bold"),
            bg=APPLE_LIGHT_GRAY,
            fg=APPLE_TEXT
        ).pack(side="left")

        self.count_label = tk.Label(
            all_header,
            text="0 个",
            font=("-apple-system", "SF Pro Text", 12),
            bg=APPLE_LIGHT_GRAY,
            fg=APPLE_SECONDARY_TEXT
        )
        self.count_label.pack(side="right")

        all_list_frame = tk.Frame(container, bg=APPLE_WHITE, padx=12, pady=8)
        all_list_frame.pack(fill="both", expand=True)

        self.all_tree = self._create_treeview(all_list_frame)

    def _create_treeview(self, parent):
        """创建统一风格的 Treeview"""
        scrollbar = ttk.Scrollbar(parent, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        tree = ttk.Treeview(
            parent,
            columns=("vid_pid", "manufacturer", "serial"),
            show="tree headings",
            yscrollcommand=scrollbar.set,
            selectmode="browse",
            height=20
        )
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=tree.yview)

        tree.heading("#0", text="设备名称", anchor="w")
        tree.heading("vid_pid", text="VID / PID", anchor="w")
        tree.heading("manufacturer", text="制造商", anchor="w")
        tree.heading("serial", text="序列号", anchor="w")

        tree.column("#0", width=200, minwidth=130)
        tree.column("vid_pid", width=140, minwidth=100)
        tree.column("manufacturer", width=140, minwidth=100)
        tree.column("serial", width=120, minwidth=80)

        tree.tag_configure("normal", font=("-apple-system", "SF Pro Text", 13))
        tree.tag_configure("selected", background=APPLE_BLUE, foreground="white")

        tree.bind("<<TreeviewSelect>>", lambda e: self._on_select(e))
        tree.bind("<Button-1>", lambda e: self._on_click(e))

        return tree

    def _on_click(self, event):
        """处理点击空白区域取消选择"""
        region = self.all_tree.identify_region(event.x, event.y)
        if region == "nothing":
            self.all_tree.selection_remove(self.all_tree.selection())

    def _on_select(self, event):
        """处理设备选择事件"""
        selection = self.all_tree.selection()
        if selection and self.on_select_callback:
            item_id = selection[0]
            index = self.all_tree.index(item_id)
            if 0 <= index < len(self.devices):
                self.on_select_callback(self.devices[index])

    def update_devices(self, devices: List[USBDevice]):
        """更新设备列表显示"""
        self.devices = devices
        self._update_tree(self.all_tree, self.devices, "normal")
        self.count_label.config(text="{0} 个".format(len(devices)))

    def _update_tree(self, tree, device_list: List[USBDevice], tag: str):
        """更新 Treeview 内容"""
        for item in tree.get_children():
            tree.delete(item)

        for device in device_list:
            display_name = device.get_display_name()
            vid_pid = device.get_vid_pid_string()
            manufacturer = device.manufacturer or "N/A"
            serial = device.serial or "N/A"

            tree.insert(
                "",
                "end",
                values=(vid_pid, manufacturer, serial),
                text=display_name,
                tags=(tag,)
            )

    def get_selected_device(self) -> Optional[USBDevice]:
        """获取当前选中的设备"""
        selection = self.all_tree.selection()
        if selection:
            index = self.all_tree.index(selection[0])
            if 0 <= index < len(self.devices):
                return self.devices[index]
        return None

    def clear_selection(self):
        """清除选择"""
        for item in self.all_tree.selection():
            self.all_tree.selection_remove(item)

    def clear(self):
        """清空所有显示"""
        for item in self.all_tree.get_children():
            self.all_tree.delete(item)
        self.devices = []
        self.count_label.config(text="0 个")
