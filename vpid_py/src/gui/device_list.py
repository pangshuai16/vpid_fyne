import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, List
from ..device_info import USBDevice


class DeviceListPanel(ttk.Frame):
    def __init__(self, parent, on_select_callback: Optional[Callable] = None):
        super().__init__(parent)
        self.on_select_callback = on_select_callback
        self.devices: List[USBDevice] = []
        self._setup_ui()

    def _setup_ui(self):
        title_label = ttk.Label(self, text="USB 设备列表", font=("Microsoft YaHei", 11, "bold"))
        title_label.pack(anchor="w", pady=(0, 10))

        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True)

        scrollbar_y = ttk.Scrollbar(list_frame, orient="vertical")
        scrollbar_y.pack(side="right", fill="y")

        scrollbar_x = ttk.Scrollbar(list_frame, orient="horizontal")
        scrollbar_x.pack(side="bottom", fill="x")

        self.tree = ttk.Treeview(
            list_frame,
            columns=("vid_pid", "manufacturer"),
            show="tree headings",
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
            selectmode="browse",
        )
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)

        self.tree.heading("#0", text="设备名称")
        self.tree.heading("vid_pid", text="VID/PID")
        self.tree.heading("manufacturer", text="制造商")

        self.tree.column("#0", width=200)
        self.tree.column("vid_pid", width=140)
        self.tree.column("manufacturer", width=120)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _on_select(self, event):
        selection = self.tree.selection()
        if selection and self.on_select_callback:
            item_id = selection[0]
            index = self.tree.index(item_id)
            if 0 <= index < len(self.devices):
                self.on_select_callback(self.devices[index])

    def update_devices(self, devices: List[USBDevice]):
        self.devices = devices
        for item in self.tree.get_children():
            self.tree.delete(item)
        for device in devices:
            display_name = device.get_display_name()
            vid_pid = device.get_vid_pid_string()
            manufacturer = device.manufacturer or "N/A"
            self.tree.insert("", "end", iid=str(len(self.tree.get_children())), values=(vid_pid, manufacturer), text=display_name)

    def get_selected_device(self) -> Optional[USBDevice]:
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
