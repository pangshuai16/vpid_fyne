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
        # Apple-inspired color palette
        bg_color = "#FFFFFF"
        header_bg = "#F9FAFB"
        text_color = "#1D1D1F"
        secondary_text = "#6E6E73"
        success_bg = "#F2FBF6"
        success_text = "#1F7F3F"
        error_bg = "#FEF5F5"
        error_text = "#C83C3C"

        container = tk.Frame(self, bg=bg_color)
        container.pack(fill="both", expand=True)

        # === All Devices Section ===
        all_header = tk.Frame(container, bg=header_bg, padx=16, pady=12)
        all_header.pack(fill="x")

        tk.Label(
            all_header,
            text="全部设备",
            font=("-apple-system", "SF Pro Display", 13, "bold"),
            bg=header_bg,
            fg=text_color
        ).pack(side="left")

        self.count_label = tk.Label(
            all_header,
            text="0",
            font=("-apple-system", "SF Pro Text", 12),
            bg=header_bg,
            fg=secondary_text
        )
        self.count_label.pack(side="right")

        all_list_frame = tk.Frame(container, bg=bg_color, padx=12, pady=8)
        all_list_frame.pack(fill="both", expand=True)

        self.all_tree = self._create_treeview(all_list_frame, "all")

        # === Added Devices Section ===
        added_header = tk.Frame(container, bg=success_bg, padx=16, pady=10)
        added_header.pack(fill="x", pady=(12, 0))

        tk.Label(
            added_header,
            text="➕ 新增设备",
            font=("-apple-system", "SF Pro Display", 12, "bold"),
            bg=success_bg,
            fg=success_text
        ).pack(side="left")

        self.added_count_label = tk.Label(
            added_header,
            text="0",
            font=("-apple-system", "SF Pro Text", 11),
            bg=success_bg,
            fg=success_text
        )
        self.added_count_label.pack(side="right")

        added_list_frame = tk.Frame(container, bg=bg_color, padx=12, pady=8)
        added_list_frame.pack(fill="x")

        self.added_tree = self._create_treeview(added_list_frame, "added")
        self.added_tree.tag_configure("item", background=success_bg, foreground=success_text,
                                      font=("-apple-system", "SF Pro Text", 13))

        # === Removed Devices Section ===
        removed_header = tk.Frame(container, bg=error_bg, padx=16, pady=10)
        removed_header.pack(fill="x", pady=(12, 0))

        tk.Label(
            removed_header,
            text="➖ 移除设备",
            font=("-apple-system", "SF Pro Display", 12, "bold"),
            bg=error_bg,
            fg=error_text
        ).pack(side="left")

        self.removed_count_label = tk.Label(
            removed_header,
            text="0",
            font=("-apple-system", "SF Pro Text", 11),
            bg=error_bg,
            fg=error_text
        )
        self.removed_count_label.pack(side="right")

        removed_list_frame = tk.Frame(container, bg=bg_color, padx=12, pady=8)
        removed_list_frame.pack(fill="x")

        self.removed_tree = self._create_treeview(removed_list_frame, "removed")
        self.removed_tree.tag_configure("item", background=error_bg, foreground=error_text,
                                        font=("-apple-system", "SF Pro Text", 13))

    def _create_treeview(self, parent, prefix):
        """Create a unified Treeview with Apple style"""
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
            # Determine data source based on tree
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

        # Update all devices list
        self._update_tree(self.all_tree, self.devices, "normal")
        self.count_label.config(text="{0} 个".format(len(devices)))

        # Update added devices list
        self._update_tree(self.added_tree, self.added_devices, "item")
        self.added_count_label.config(text="{0} 个".format(len(self.added_devices)))

        # Update removed devices list
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
