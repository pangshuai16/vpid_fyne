"""设备变化面板组件 - 显示新增和移除的设备"""
import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Callable
from ..device_info import USBDevice
from ..constants import (
    APPLE_WHITE,
    APPLE_LIGHT_GRAY,
    APPLE_BLUE,
    APPLE_TEXT,
    APPLE_SECONDARY_TEXT,
    APPLE_SUCCESS_BG,
    APPLE_SUCCESS_TEXT,
    APPLE_ERROR_BG,
    APPLE_ERROR_TEXT,
    APPLE_VID_COLOR,
    APPLE_PID_COLOR,
    MONO_FONT
)


class DeviceChangePanel(ttk.Frame):
    """显示新增和移除 USB 设备的面板"""

    def __init__(self, parent, on_select_callback: Optional[Callable[[USBDevice], None]] = None):
        super(DeviceChangePanel, self).__init__(parent)
        self.on_select_callback = on_select_callback
        self.added_devices: List[USBDevice] = []
        self.removed_devices: List[USBDevice] = []
        self._setup_ui()

    def _setup_ui(self):
        """初始化 UI 组件"""
        container = tk.Frame(self, bg=APPLE_WHITE)
        container.pack(fill="both", expand=True)

        added_section = tk.Frame(container, bg=APPLE_WHITE)
        added_section.pack(fill="both", expand=True, pady=(0, 4))

        added_header = tk.Frame(added_section, bg=APPLE_SUCCESS_BG, padx=16, pady=10)
        added_header.pack(fill="x")

        tk.Label(
            added_header,
            text="➕ 新增设备",
            font=("-apple-system", "SF Pro Display", 13, "bold"),
            bg=APPLE_SUCCESS_BG,
            fg=APPLE_SUCCESS_TEXT
        ).pack(side="left")

        self.added_count_label = tk.Label(
            added_header,
            text="0 个",
            font=("-apple-system", "SF Pro Text", 12),
            bg=APPLE_SUCCESS_BG,
            fg=APPLE_SUCCESS_TEXT
        )
        self.added_count_label.pack(side="right")

        added_list_frame = tk.Frame(added_section, bg=APPLE_WHITE, padx=12, pady=8)
        added_list_frame.pack(fill="both", expand=True)

        self.added_tree = self._create_treeview(added_list_frame)
        self.added_tree.tag_configure(
            "added",
            background=APPLE_SUCCESS_BG,
            foreground=APPLE_SUCCESS_TEXT,
            font=("-apple-system", "SF Pro Text", 13)
        )

        separator = tk.Frame(container, bg=APPLE_LIGHT_GRAY, height=1)
        separator.pack(fill="x", padx=12, pady=4)

        removed_section = tk.Frame(container, bg=APPLE_WHITE)
        removed_section.pack(fill="both", expand=True, pady=(4, 0))

        removed_header = tk.Frame(removed_section, bg=APPLE_ERROR_BG, padx=16, pady=10)
        removed_header.pack(fill="x")

        tk.Label(
            removed_header,
            text="➖ 移除设备",
            font=("-apple-system", "SF Pro Display", 13, "bold"),
            bg=APPLE_ERROR_BG,
            fg=APPLE_ERROR_TEXT
        ).pack(side="left")

        self.removed_count_label = tk.Label(
            removed_header,
            text="0 个",
            font=("-apple-system", "SF Pro Text", 12),
            bg=APPLE_ERROR_BG,
            fg=APPLE_ERROR_TEXT
        )
        self.removed_count_label.pack(side="right")

        removed_list_frame = tk.Frame(removed_section, bg=APPLE_WHITE, padx=12, pady=8)
        removed_list_frame.pack(fill="both", expand=True)

        self.removed_tree = self._create_treeview(removed_list_frame)
        self.removed_tree.tag_configure(
            "removed",
            background=APPLE_ERROR_BG,
            foreground=APPLE_ERROR_TEXT,
            font=("-apple-system", "SF Pro Text", 13)
        )

    def _create_treeview(self, parent):
        """创建统一风格的 Treeview"""
        scrollbar = ttk.Scrollbar(parent, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        tree = ttk.Treeview(
            parent,
            columns=("name", "vid", "pid"),
            show="headings",
            yscrollcommand=scrollbar.set,
            selectmode="browse",
            height=8
        )
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=tree.yview)

        tree.heading("name", text="设备名称", anchor="w")
        tree.heading("vid", text="VID", anchor="center")
        tree.heading("pid", text="PID", anchor="center")

        tree.column("name", width=180, minwidth=120, anchor="w")
        tree.column("vid", width=80, minwidth=60, anchor="center")
        tree.column("pid", width=80, minwidth=60, anchor="center")

        tree.tag_configure("normal", font=("-apple-system", "SF Pro Text", 13))
        tree.tag_configure("vid_tag", font=(MONO_FONT, 12, "bold"), foreground=APPLE_VID_COLOR)
        tree.tag_configure("pid_tag", font=(MONO_FONT, 12, "bold"), foreground=APPLE_PID_COLOR)
        tree.tag_configure("selected", background=APPLE_BLUE, foreground="white")

        tree.bind("<<TreeviewSelect>>", lambda e, t=tree: self._on_select(e, t))
        tree.bind("<Button-1>", lambda e, t=tree: self._on_click(e, t))

        return tree

    def _on_click(self, event, tree):
        """处理点击空白区域取消选择"""
        region = tree.identify_region(event.x, event.y)
        if region == "nothing":
            tree.selection_remove(tree.selection())

    def _on_select(self, event, tree):
        """处理设备选择事件"""
        selection = tree.selection()
        if selection and self.on_select_callback:
            item_id = selection[0]
            index = tree.index(item_id)
            if tree == self.added_tree and 0 <= index < len(self.added_devices):
                self.on_select_callback(self.added_devices[index])
            elif tree == self.removed_tree and 0 <= index < len(self.removed_devices):
                self.on_select_callback(self.removed_devices[index])

    def update_changes(self, added_devices: List[USBDevice], removed_devices: List[USBDevice]):
        """更新新增和移除设备列表"""
        self.added_devices = added_devices
        self.removed_devices = removed_devices

        self._update_tree(self.added_tree, self.added_devices, "added")
        self.added_count_label.config(text="{0} 个".format(len(self.added_devices)))

        self._update_tree(self.removed_tree, self.removed_devices, "removed")
        self.removed_count_label.config(text="{0} 个".format(len(self.removed_devices)))

    def _update_tree(self, tree, device_list: List[USBDevice], tag: str):
        """更新 Treeview 内容"""
        for item in tree.get_children():
            tree.delete(item)

        for device in device_list:
            name = device.get_display_name()
            vid = device.vid or "—"
            pid = device.pid or "—"

            tree.insert(
                "",
                "end",
                values=(name, vid, pid),
                tags=(tag,)
            )

    def get_selected_device(self) -> Optional[USBDevice]:
        """获取当前选中的设备"""
        for tree, devices in [(self.added_tree, self.added_devices),
                              (self.removed_tree, self.removed_devices)]:
            selection = tree.selection()
            if selection:
                index = tree.index(selection[0])
                if 0 <= index < len(devices):
                    return devices[index]
        return None

    def clear_selection(self):
        """清除所有选择"""
        for tree in [self.added_tree, self.removed_tree]:
            for item in tree.selection():
                tree.selection_remove(item)

    def clear(self):
        """清空所有显示"""
        for tree in [self.added_tree, self.removed_tree]:
            for item in tree.get_children():
                tree.delete(item)
        self.added_devices = []
        self.removed_devices = []
        self.added_count_label.config(text="0 个")
        self.removed_count_label.config(text="0 个")
