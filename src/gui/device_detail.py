import tkinter as tk
from tkinter import ttk
from ..device_info import USBDevice


class DeviceDetailPanel(ttk.Frame):
    def __init__(self, parent):
        super(DeviceDetailPanel, self).__init__(parent)
        self.current_device = None
        self._setup_ui()

    def _setup_ui(self):
        bg_color = "#FFFFFF"
        header_bg = "#F5F5F7"
        accent_color = "#007AFF"
        text_color = "#1D1D1F"
        secondary_text = "#86868B"
        border_color = "#E5E5E5"

        container = tk.Frame(self, bg=bg_color)
        container.pack(fill="both", expand=True)

        header_frame = tk.Frame(container, bg=header_bg, padx=15, pady=10)
        header_frame.pack(fill="x")

        title_label = tk.Label(
            header_frame,
            text="设备详情",
            font=("SF Pro Display", 12, "bold"),
            bg=header_bg,
            fg=text_color
        )
        title_label.pack(side="left")

        self.icon_label = tk.Label(
            header_frame,
            text="⌥",
            font=("SF Pro Display", 20),
            bg=header_bg,
            fg=secondary_text
        )
        self.icon_label.pack(side="right")

        info_container = tk.Frame(container, bg=bg_color, padx=15, pady=10)
        info_container.pack(fill="both", expand=True)

        self.labels = {}
        fields = [
            ("名称", "name"),
            ("供应商 ID", "vid"),
            ("产品 ID", "pid"),
            ("序列号", "serial"),
            ("制造商", "manufacturer"),
            ("位置", "location"),
            ("驱动程序", "driver"),
            ("状态", "status"),
        ]

        for i, (label_text, field) in enumerate(fields):
            row = tk.Frame(info_container, bg=bg_color)
            row.pack(fill="x", pady=6)

            label = tk.Label(
                row,
                text=label_text,
                font=("SF Pro Text", 11),
                bg=bg_color,
                fg=secondary_text,
                width=12,
                anchor="w"
            )
            label.pack(side="left")

            value_label = tk.Label(
                row,
                text="—",
                font=("SF Pro Text", 11),
                bg=bg_color,
                fg=text_color,
                anchor="w",
                wraplength=200
            )
            value_label.pack(side="left", fill="x", expand=True, padx=(8, 0))
            self.labels[field] = value_label

            if i < len(fields) - 1:
                separator = tk.Frame(info_container, bg=border_color, height=1)
                separator.pack(fill="x", pady=(0, 6))

        button_frame = tk.Frame(container, bg=bg_color, padx=15, pady=10)
        button_frame.pack(fill="x", side="bottom")

        copy_frame = tk.Frame(button_frame, bg="#F5F5F7", padx=10, pady=6)
        copy_frame.pack(side="left", padx=(0, 8))

        self.copy_btn = tk.Label(
            copy_frame,
            text="⧉ 复制全部信息",
            font=("SF Pro Text", 10),
            bg="#F5F5F7",
            fg=accent_color,
            cursor="hand2"
        )
        self.copy_btn.pack()

    def set_device(self, device):
        self.current_device = device
        if device:
            self.labels["name"].config(text=device.name or "—")
            self.labels["vid"].config(text=device.vid or "—")
            self.labels["pid"].config(text=device.pid or "—")
            self.labels["serial"].config(text=device.serial or "—")
            self.labels["manufacturer"].config(text=device.manufacturer or "—")
            self.labels["location"].config(text=device.location or "—")
            self.labels["driver"].config(text=device.driver or "—")
            self.labels["status"].config(text=device.status or "—")

            if device.status == "Connected":
                self.labels["status"].config(fg="#34C759")
            elif "Error" in str(device.status):
                self.labels["status"].config(fg="#FF3B30")
            else:
                self.labels["status"].config(fg="#1D1D1F")
        else:
            for label in self.labels.values():
                label.config(text="—", fg="#1D1D1F")

    def get_current_device(self):
        return self.current_device
