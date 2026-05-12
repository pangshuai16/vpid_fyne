import tkinter as tk
from tkinter import ttk
from ..device_info import USBDevice


class DeviceListPanel(ttk.Frame):
    def __init__(self, parent, on_select_callback=None):
        super(DeviceListPanel, self).__init__(parent)
        self.on_select_callback = on_select_callback
        self.devices = []
        self._setup_ui()

    def _setup_ui(self):
        bg_color = "#FFFFFF"
        header_bg = "#F5F5F7"

        container = tk.Frame(self, bg=bg_color)
        container.pack(fill="both", expand=True)

        header_frame = tk.Frame(container, bg=header_bg, padx=15, pady=12)
        header_frame.pack(fill="x")

        title_label = tk.Label(
            header_frame,
            text="USB 设备列表",
            font=("SF Pro Display", 13, "bold"),
            bg=header_bg,
            fg="#1D1D1F"
        )
        title_label.pack(side="left")

        self.count_label = tk.Label(
            header_frame,
            text="0",
            font=("SF Pro Display", 11),
            bg=header_bg,
            fg="#86868B"
        )
        self.count_label.pack(side="right")

        list_container = tk.Frame(container, bg=bg_color, padx=15, pady=(0, 15))
        list_container.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("Apple.Treeview",
                       background=bg_color,
                       foreground="#1D1D1F",
                       fieldbackground=bg_color,
                       font=("SF Pro Text", 12),
                       rowheight=40,
                       padding=10,
                       relief="flat",
                       borderwidth=0)

        style.configure("Apple.Treeview.Heading",
                        background=header_bg,
                        foreground="#1D1D1F",
                        font=("SF Pro Text", 11, "bold"),
                        padding=(12, 12),
                        relief="flat",
                        borderwidth=0)

        scrollbar_y = ttk.Scrollbar(list_container, orient="vertical", style="Apple.Vertical.TScrollbar")
        scrollbar_y.pack(side="right", fill="y", padx=(5, 0))

        scrollbar_x = ttk.Scrollbar(list_container, orient="horizontal", style="Apple.Horizontal.TScrollbar")
        scrollbar_x.pack(side="bottom", fill="x", pady=(5, 0))

        style.configure("Apple.Vertical.TScrollbar",
                       background="#E8E8ED",
                       troughcolor=bg_color,
                       borderwidth=0,
                       relief="flat",
                       arrowsize=0)

        style.configure("Apple.Horizontal.TScrollbar",
                       background="#E8E8ED",
                       troughcolor=bg_color,
                       borderwidth=0,
                       relief="flat",
                       arrowsize=0)

        self.tree = ttk.Treeview(
            list_container,
            columns=("vid_pid", "manufacturer"),
            show="tree headings",
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
            selectmode="browse",
            style="Apple.Treeview",
        )
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)

        self.tree.heading("#0", text="设备名称", anchor="w")
        self.tree.heading("vid_pid", text="VID / PID", anchor="w")
        self.tree.heading("manufacturer", text="制造商", anchor="w")

        self.tree.column("#0", width=220, minwidth=150)
        self.tree.column("vid_pid", width=130, minwidth=100)
        self.tree.column("manufacturer", width=150, minwidth=100)

        style.map("Apple.Treeview",
                 background=[("selected", "#007AFF")],
                 foreground=[("selected", "white")])

        self.tree.tag_configure("added",
                              background="#D4EDDA",
                              foreground="#155724",
                              font=("SF Pro Text", 12, "bold"))

        self.tree.tag_configure("removed",
                              background="#F8D7DA",
                              foreground="#721C24",
                              font=("SF Pro Text", 12, "bold"))

        self.tree.tag_configure("normal",
                              background=bg_color,
                              foreground="#1D1D1F",
                              font=("SF Pro Text", 12))

        self.tree.tag_configure("selected",
                              background="#007AFF",
                              foreground="white")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Button-1>", self._on_click)

        selection_placeholder = tk.Frame(list_container, bg=bg_color)
        selection_placeholder.pack(fill="both", expand=True)

        self.empty_label = tk.Label(
            selection_placeholder,
            text="未检测到 USB 设备\n\n点击刷新按钮扫描设备",
            font=("SF Pro Text", 12),
            bg=bg_color,
            fg="#86868B",
            justify="center"
        )
        self.empty_label.pack(expand=True)

    def _on_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "nothing":
            self.tree.selection_remove(self.tree.selection())

    def _on_select(self, event):
        selection = self.tree.selection()
        if selection and self.on_select_callback:
            item_id = selection[0]
            index = self.tree.index(item_id)
            if 0 <= index < len(self.devices):
                self.on_select_callback(self.devices[index])

    def update_devices(self, devices, added_devices=None, removed_devices=None):
        self.devices = devices
        added_keys = set((d.vid, d.pid, d.serial) for d in (added_devices or []))
        removed_keys = set((d.vid, d.pid, d.serial) for d in (removed_devices or []))

        for item in self.tree.get_children():
            self.tree.delete(item)

        self.count_label.config(text="{0} 个设备".format(len(devices)))

        if len(devices) == 0:
            self.empty_label.config(state="normal")
            self.empty_label.lift()
        else:
            self.empty_label.config(state="hidden")

        for device in devices:
            display_name = device.get_display_name()
            vid_pid = device.get_vid_pid_string()
            manufacturer = device.manufacturer or "N/A"
            device_key = (device.vid, device.pid, device.serial)

            tags = ["normal"]
            icon = ""

            if device_key in added_keys:
                tags = ["added"]
                icon = "➕ "
            elif device_key in removed_keys:
                tags = ["removed"]
                icon = "➖ "

            item_id = str(len(self.tree.get_children()))
            self.tree.insert(
                "",
                "end",
                iid=item_id,
                values=(vid_pid, manufacturer),
                text=icon + display_name,
                tags=tags
            )

    def get_selected_device(self):
        selection = self.tree.selection()
        if selection:
            index = self.tree.index(selection[0])
            if 0 <= index < len(self.devices):
                return self.devices[index]
        return None

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.devices = []
        self.count_label.config(text="0 个设备")
