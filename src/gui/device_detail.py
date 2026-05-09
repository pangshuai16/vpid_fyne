import tkinter as tk
from tkinter import ttk, messagebox
from ..device_info import USBDevice


class DeviceDetailPanel(ttk.Frame):
    def __init__(self, parent):
        super(DeviceDetailPanel, self).__init__(parent)
        self.current_device = None
        self._setup_ui()

    def _setup_ui(self):
        title_label = ttk.Label(self, text="设备详情", font=("Microsoft YaHei", 11, "bold"))
        title_label.pack(anchor="w", pady=(0, 10))

        self.info_frame = ttk.Frame(self)
        self.info_frame.pack(fill="both", expand=True)

        self.labels = {}
        fields = [
            ("名称", "name"),
            ("供应商ID (VID)", "vid"),
            ("产品ID (PID)", "pid"),
            ("序列号", "serial"),
            ("制造商", "manufacturer"),
            ("位置", "location"),
            ("驱动程序", "driver"),
            ("状态", "status"),
        ]

        for i, (label_text, field) in enumerate(fields):
            row = ttk.Frame(self.info_frame)
            row.pack(fill="x", pady=2)

            label = ttk.Label(row, text="{0}:".format(label_text), width=16, anchor="w")
            label.pack(side="left")

            value_label = ttk.Label(row, text="N/A", anchor="w", style="Value.TLabel")
            value_label.pack(side="left", fill="x", expand=True)
            self.labels[field] = value_label

    def set_device(self, device):
        self.current_device = device
        if device:
            self.labels["name"].config(text=device.name or "N/A")
            self.labels["vid"].config(text=device.vid or "N/A")
            self.labels["pid"].config(text=device.pid or "N/A")
            self.labels["serial"].config(text=device.serial or "N/A")
            self.labels["manufacturer"].config(text=device.manufacturer or "N/A")
            self.labels["location"].config(text=device.location or "N/A")
            self.labels["driver"].config(text=device.driver or "N/A")
            self.labels["status"].config(text=device.status or "N/A")
        else:
            for label in self.labels.values():
                label.config(text="N/A")

    def get_current_device(self):
        return self.current_device
