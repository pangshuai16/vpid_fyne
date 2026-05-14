"""设备列表面板组件 - 显示全部 USB 设备"""
import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Callable
from ..device_info import USBDevice
from ..constants import (
    BG,
    BG_HEADER,
    PRIMARY,
    TEXT,
    TEXT_SECONDARY,
    SELECT_BG,
    SELECT_FG,
    VID_COLOR,
    PID_COLOR,
    FONT_SYSTEM,
    FONT_SYSTEM_BOLD,
    FONT_MONO,
)


class DeviceListPanel(ttk.Frame):
    """显示全部 USB 设备列表的面板"""

    def __init__(self, parent, on_select_callback: Optional[Callable[[USBDevice], None]] = None):
        super(DeviceListPanel, self).__init__(parent)
        self.on_select_callback = on_select_callback
        self.devices = []
        self._setup_ui()

    def _setup_ui(self):
        """初始化 UI 组件"""
        container = tk.Frame(self, bg=BG)
        container.pack(fill="both", expand=True)

        all_header = tk.Frame(container, bg=BG_HEADER, padx=16, pady=12)
        all_header.pack(fill="x")

        tk.Label(
            all_header,
            text="全部设备",
            font=FONT_SYSTEM_BOLD,
            bg=BG_HEADER,
            fg=TEXT
        ).pack(side="left")

        self.count_label = tk.Label(
            all_header,
            text="0 个",
            font=FONT_SYSTEM,
            bg=BG_HEADER,
            fg=TEXT_SECONDARY
        )
        self.count_label.pack(side="right")

        all_list_frame = tk.Frame(container, bg=BG, padx=12, pady=8)
        all_list_frame.pack(fill="both", expand=True)

        self.all_tree = self._create_treeview(all_list_frame)

    def _create_treeview(self, parent):
        """创建统一风格的 Treeview"""
        scrollbar = ttk.Scrollbar(parent, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        tree = ttk.Treeview(
            parent,
            columns=("vid", "pid", "serial"),
            show="tree headings",
            yscrollcommand=scrollbar.set,
            selectmode="browse",
        )
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=tree.yview)

        tree.heading("#0", text="设备名称", anchor="w")
        tree.heading("vid", text="VID", anchor="w")
        tree.heading("pid", text="PID", anchor="w")
        tree.heading("serial", text="序列号", anchor="w")

        tree.column("#0", width=200, minwidth=130, anchor="w", stretch=True)
        tree.column("vid", width=90, minwidth=70, anchor="w", stretch=True)
        tree.column("pid", width=90, minwidth=70, anchor="w", stretch=True)
        tree.column("serial", width=130, minwidth=80, anchor="w", stretch=True)

        tree.tag_configure("normal", font=FONT_SYSTEM)
        tree.tag_configure("selected", background=SELECT_BG, foreground=SELECT_FG)

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

    def update_devices(self, devices):
        """更新设备列表显示"""
        self.devices = devices
        self._update_tree(self.all_tree, self.devices)
        self.count_label.config(text="{0} 个".format(len(devices)))

    def _update_tree(self, tree, device_list):
        """更新 Treeview 内容"""
        for item in tree.get_children():
            tree.delete(item)

        for device in device_list:
            name = device.get_display_name()
            vid = device.vid or "—"
            pid = device.pid or "—"
            serial = device.serial or "—"

            tree.insert(
                "",
                "end",
                text=name,
                values=(vid, pid, serial),
                tags=("normal",)
            )

    def get_selected_device(self):
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