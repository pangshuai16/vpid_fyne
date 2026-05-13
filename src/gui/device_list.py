import tkinter as tk
from tkinter import ttk
from ..device_info import USBDevice


class DeviceListPanel(ttk.Frame):
    def __init__(self, parent, on_select_callback=None):
        super(DeviceListPanel, self).__init__(parent)
        self.on_select_callback = on_select_callback
        self.devices = []
        self.added_devices = []
        self.removed_devices = []
        self._setup_ui()

    def _setup_ui(self):
        bg_color = "#FFFFFF"
        header_bg = "#F5F5F7"
        accent_color = "#007AFF"
        text_color = "#1D1D1F"
        secondary_text = "#86868B"
        green_bg = "#D4EDDA"
        green_text = "#155724"
        red_bg = "#F8D7DA"
        red_text = "#721C24"

        container = tk.Frame(self, bg=bg_color)
        container.pack(fill="both", expand=True)

        # === 全部设备区域 ===
        all_header = tk.Frame(container, bg=header_bg, padx=15, pady=10)
        all_header.pack(fill="x")

        tk.Label(
            all_header,
            text="全部设备",
            font=("SF Pro Display", 12, "bold"),
            bg=header_bg,
            fg=text_color
        ).pack(side="left")

        self.count_label = tk.Label(
            all_header,
            text="0",
            font=("SF Pro Text", 11),
            bg=header_bg,
            fg=secondary_text
        )
        self.count_label.pack(side="right")

        all_list_frame = tk.Frame(container, bg=bg_color, padx=10, pady=5)
        all_list_frame.pack(fill="both", expand=True)

        self.all_tree = self._create_treeview(all_list_frame, "all")

        # === 新增设备区域 ===
        added_header = tk.Frame(container, bg=green_bg, padx=15, pady=8)
        added_header.pack(fill="x", pady=(10, 0))

        tk.Label(
            added_header,
            text="➕ 新增设备",
            font=("SF Pro Display", 11, "bold"),
            bg=green_bg,
            fg=green_text
        ).pack(side="left")

        self.added_count_label = tk.Label(
            added_header,
            text="0",
            font=("SF Pro Text", 10),
            bg=green_bg,
            fg=green_text
        )
        self.added_count_label.pack(side="right")

        added_list_frame = tk.Frame(container, bg=bg_color, padx=10, pady=5)
        added_list_frame.pack(fill="x")

        self.added_tree = self._create_treeview(added_list_frame, "added")
        self.added_tree.tag_configure("item", background=green_bg, foreground=green_text,
                                      font=("SF Pro Text", 11))

        # === 移除设备区域 ===
        removed_header = tk.Frame(container, bg=red_bg, padx=15, pady=8)
        removed_header.pack(fill="x", pady=(10, 0))

        tk.Label(
            removed_header,
            text="➖ 移除设备",
            font=("SF Pro Display", 11, "bold"),
            bg=red_bg,
            fg=red_text
        ).pack(side="left")

        self.removed_count_label = tk.Label(
            removed_header,
            text="0",
            font=("SF Pro Text", 10),
            bg=red_bg,
            fg=red_text
        )
        self.removed_count_label.pack(side="right")

        removed_list_frame = tk.Frame(container, bg=bg_color, padx=10, pady=5)
        removed_list_frame.pack(fill="x")

        self.removed_tree = self._create_treeview(removed_list_frame, "removed")
        self.removed_tree.tag_configure("item", background=red_bg, foreground=red_text,
                                        font=("SF Pro Text", 11))

    def _create_treeview(self, parent, prefix):
        """创建统一风格的 Treeview"""
        scrollbar = ttk.Scrollbar(parent, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        tree = ttk.Treeview(
            parent,
            columns=("vid_pid", "manufacturer"),
            show="tree headings",
            yscrollcommand=scrollbar.set,
            selectmode="browse",
            height=4 if prefix != "all" else 8
        )
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=tree.yview)

        tree.heading("#0", text="设备名称", anchor="w")
        tree.heading("vid_pid", text="VID / PID", anchor="w")
        tree.heading("manufacturer", text="制造商", anchor="w")

        tree.column("#0", width=200, minwidth=120)
        tree.column("vid_pid", width=110, minwidth=80)
        tree.column("manufacturer", width=130, minwidth=80)

        tree.tag_configure("normal", font=("SF Pro Text", 11))
        tree.tag_configure("selected", background="#007AFF", foreground="white")

        tree.bind("<<TreeviewSelect>>", lambda e, t=tree: self._on_select(e, t))
        tree.bind("<Button-1>", lambda e, t=tree: self._on_click(e, t))

        return tree

    def _on_click(self, event, tree):
        region = tree.identify_region(event.x, event.y)
        if region == "nothing":
            tree.selection_remove(tree.selection())

    def _on_select(self, event, tree):
        selection = tree.selection()
        if selection and self.on_select_callback:
            item_id = selection[0]
            index = tree.index(item_id)
            # 根据 tree 确定数据源
            if tree == self.all_tree and 0 <= index < len(self.devices):
                self.on_select_callback(self.devices[index])
            elif tree == self.added_tree and 0 <= index < len(self.added_devices):
                self.on_select_callback(self.added_devices[index])
            elif tree == self.removed_tree and 0 <= index < len(self.removed_devices):
                self.on_select_callback(self.removed_devices[index])

    def update_devices(self, devices, added_devices=None, removed_devices=None):
        self.devices = devices
        self.added_devices = added_devices or []
        self.removed_devices = removed_devices or []

        # 更新全部设备列表
        self._update_tree(self.all_tree, self.devices, "normal")
        self.count_label.config(text="{0} 个".format(len(devices)))

        # 更新新增设备列表
        self._update_tree(self.added_tree, self.added_devices, "item")
        self.added_count_label.config(text="{0} 个".format(len(self.added_devices)))

        # 更新移除设备列表
        self._update_tree(self.removed_tree, self.removed_devices, "item")
        self.removed_count_label.config(text="{0} 个".format(len(self.removed_devices)))

    def _update_tree(self, tree, device_list, tag):
        for item in tree.get_children():
            tree.delete(item)

        for device in device_list:
            display_name = device.get_display_name()
            vid_pid = device.get_vid_pid_string()
            manufacturer = device.manufacturer or "N/A"

            item_id = str(len(tree.get_children()))
            tree.insert(
                "",
                "end",
                iid=item_id,
                values=(vid_pid, manufacturer),
                text=display_name,
                tags=(tag,)
            )

    def get_selected_device(self):
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
        for tree in [self.all_tree, self.added_tree, self.removed_tree]:
            for item in tree.get_children():
                tree.delete(item)
        self.devices = []
        self.added_devices = []
        self.removed_devices = []
        self.count_label.config(text="0")
        self.added_count_label.config(text="0")
        self.removed_count_label.config(text="0")
