"""设备列表面板组件"""
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
    APPLE_ERROR_TEXT
)


class DeviceListPanel(ttk.Frame):
    """显示 USB 设备列表的面板"""

    def __init__(self, parent, on_select_callback: Optional[Callable[[USBDevice], None]] = None):
        super(DeviceListPanel, self).__init__(parent)
        self.on_select_callback = on_select_callback
        self.devices: List[USBDevice] = []
        self.added_devices: List[USBDevice] = []
        self.removed_devices: List[USBDevice] = []
        self._setup_ui()

    def _setup_ui(self):
        """初始化 UI 组件"""
        container = tk.Frame(self, bg=APPLE_WHITE)
        container.pack(fill="both", expand=True)

        # 全部设备区域
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
            text="0",
            font=("-apple-system", "SF Pro Text", 12),
            bg=APPLE_LIGHT_GRAY,
            fg=APPLE_SECONDARY_TEXT
        )
        self.count_label.pack(side="right")

        all_list_frame = tk.Frame(container, bg=APPLE_WHITE, padx=12, pady=8)
        all_list_frame.pack(fill="both", expand=True)

        self.all_tree = self._create_treeview(all_list_frame, "all")

        # 新增设备区域
        added_header = tk.Frame(container, bg=APPLE_SUCCESS_BG, padx=16, pady=10)
        added_header.pack(fill="x", pady=(12, 0))

        tk.Label(
            added_header,
            text="➕ 新增设备",
            font=("-apple-system", "SF Pro Display", 12, "bold"),
            bg=APPLE_SUCCESS_BG,
            fg=APPLE_SUCCESS_TEXT
        ).pack(side="left")

        self.added_count_label = tk.Label(
            added_header,
            text="0",
            font=("-apple-system", "SF Pro Text", 11),
            bg=APPLE_SUCCESS_BG,
            fg=APPLE_SUCCESS_TEXT
        )
        self.added_count_label.pack(side="right")

        added_list_frame = tk.Frame(container, bg=APPLE_WHITE, padx=12, pady=8)
        added_list_frame.pack(fill="x")

        self.added_tree = self._create_treeview(added_list_frame, "added")
        self.added_tree.tag_configure("item", background=APPLE_SUCCESS_BG, foreground=APPLE_SUCCESS_TEXT,
                                      font=("-apple-system", "SF Pro Text", 13))

        # 移除设备区域
        removed_header = tk.Frame(container, bg=APPLE_ERROR_BG, padx=16, pady=10)
        removed_header.pack(fill="x", pady=(12, 0))

        tk.Label(
            removed_header,
            text="➖ 移除设备",
            font=("-apple-system", "SF Pro Display", 12, "bold"),
            bg=APPLE_ERROR_BG,
            fg=APPLE_ERROR_TEXT
        ).pack(side="left")

        self.removed_count_label = tk.Label(
            removed_header,
            text="0",
            font=("-apple-system", "SF Pro Text", 11),
            bg=APPLE_ERROR_BG,
            fg=APPLE_ERROR_TEXT
        )
        self.removed_count_label.pack(side="right")

        removed_list_frame = tk.Frame(container, bg=APPLE_WHITE, padx=12, pady=8)
        removed_list_frame.pack(fill="x")

        self.removed_tree = self._create_treeview(removed_list_frame, "removed")
        self.removed_tree.tag_configure("item", background=APPLE_ERROR_BG, foreground=APPLE_ERROR_TEXT,
                                        font=("-apple-system", "SF Pro Text", 13))

    def _create_treeview(self, parent, prefix: str):
        """创建统一风格的 Treeview"""
        scrollbar = ttk.Scrollbar(parent, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        tree = ttk.Treeview(
            parent,
            columns=("vid_pid", "manufacturer"),
            show="tree headings",
            yscrollcommand=scrollbar.set,
            selectmode="browse",
            height=5 if prefix != "all" else 10
        )
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=tree.yview)

        tree.heading("#0", text="设备名称", anchor="w")
        tree.heading("vid_pid", text="VID / PID", anchor="w")
        tree.heading("manufacturer", text="制造商", anchor="w")

        tree.column("#0", width=220, minwidth=140)
        tree.column("vid_pid", width=130, minwidth=100)
        tree.column("manufacturer", width=160, minwidth=100)

        tree.tag_configure("normal", font=("-apple-system", "SF Pro Text", 13))
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
            if tree == self.all_tree and 0 <= index < len(self.devices):
                self.on_select_callback(self.devices[index])
            elif tree == self.added_tree and 0 <= index < len(self.added_devices):
                self.on_select_callback(self.added_devices[index])
            elif tree == self.removed_tree and 0 <= index < len(self.removed_devices):
                self.on_select_callback(self.removed_devices[index])

    def update_devices(self, devices: List[USBDevice], added_devices: Optional[List[USBDevice]] = None,
                       removed_devices: Optional[List[USBDevice]] = None):
        """更新设备列表显示"""
        self.devices = devices
        self.added_devices = added_devices or []
        self.removed_devices = removed_devices or []

        self._update_tree(self.all_tree, self.devices, "normal")
        self.count_label.config(text="{0} 个".format(len(devices)))

        self._update_tree(self.added_tree, self.added_devices, "item")
        self.added_count_label.config(text="{0} 个".format(len(self.added_devices)))

        self._update_tree(self.removed_tree, self.removed_devices, "item")
        self.removed_count_label.config(text="{0} 个".format(len(self.removed_devices)))

    def _update_tree(self, tree, device_list: List[USBDevice], tag: str):
        """更新 Treeview 内容"""
        for item in tree.get_children():
            tree.delete(item)

        for device in device_list:
            display_name = device.get_display_name()
            vid_pid = device.get_vid_pid_string()
            manufacturer = device.manufacturer or "N/A"

            tree.insert(
                "",
                "end",
                values=(vid_pid, manufacturer),
                text=display_name,
                tags=(tag,)
            )

    def get_selected_device(self) -> Optional[USBDevice]:
        """获取当前选中的设备"""
        for tree in [self.all_tree, self.added_tree, self.removed_tree]:
            selection = tree.selection()
            if selection:
                index = tree.index(selection[0])
                if tree == self.all_tree and 0 <= index < len(self.devices):
                    return self.devices[index]
                elif tree == self.added_tree and 0 <= index < len(self.added_devices):
                    return self.added_devices[index]
                elif tree == self.removed_tree and 0 <= index < len(self.removed_devices):
                    return self.removed_devices[index]
        return None

    def clear(self):
        """清空所有显示"""
        for tree in [self.all_tree, self.added_tree, self.removed_tree]:
            for item in tree.get_children():
                tree.delete(item)
        self.devices = []
        self.added_devices = []
        self.removed_devices = []
        self.count_label.config(text="0")
        self.added_count_label.config(text="0")
        self.removed_count_label.config(text="0")
