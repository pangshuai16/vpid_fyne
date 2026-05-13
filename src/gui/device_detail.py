import tkinter as tk
from tkinter import ttk
from ..device_info import USBDevice


class DeviceDetailPanel(ttk.Frame):
    def __init__(self, parent):
        super(DeviceDetailPanel, self).__init__(parent)
        self.current_device = None
        self._setup_ui()

    def _setup_ui(self):
        # Apple-inspired color palette
        bg_color = "#FFFFFF"
        header_bg = "#F9FAFB"
        accent_color = "#007AFF"
        text_color = "#1D1D1F"
        secondary_text = "#6E6E73"
        border_color = "#E5E5EA"
        success_color = "#34C759"
        error_color = "#FF3B30"

        container = tk.Frame(self, bg=bg_color)
        container.pack(fill="both", expand=True)

        header_frame = tk.Frame(container, bg=header_bg, padx=16, pady=12)
        header_frame.pack(fill="x")

        title_label = tk.Label(
            header_frame,
            text="设备详情",
            font=("-apple-system", "SF Pro Display", 13, "bold"),
            bg=header_bg,
            fg=text_color
        )
        title_label.pack(side="left")

        self.icon_label = tk.Label(
            header_frame,
            text="⌥",
            font=("-apple-system", "SF Pro Display", 22),
            bg=header_bg,
            fg=secondary_text
        )
        self.icon_label.pack(side="right")

        info_container = tk.Frame(container, bg=bg_color, padx=16, pady=12)
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
            row.pack(fill="x", pady=8)

            label = tk.Label(
                row,
                text=label_text,
                font=("-apple-system", "SF Pro Text", 12),
                bg=bg_color,
                fg=secondary_text,
                width=13,
                anchor="w"
            )
            label.pack(side="left")

            value_label = tk.Label(
                row,
                text="—",
                font=("-apple-system", "SF Pro Text", 12),
                bg=bg_color,
                fg=text_color,
                anchor="w",
                wraplength=240
            )
            value_label.pack(side="left", fill="x", expand=True, padx=(12, 0))
            self.labels[field] = value_label

            if i < len(fields) - 1:
                separator = tk.Frame(info_container, bg=border_color, height=1)
                separator.pack(fill="x", pady=(0, 8))

        button_frame = tk.Frame(container, bg=bg_color, padx=16, pady=12)
        button_frame.pack(fill="x", side="bottom")

        copy_frame = tk.Frame(button_frame, bg=header_bg, padx=14, pady=9)
        copy_frame.pack(side="left", padx=(0, 12))

        self.copy_btn = tk.Label(
            copy_frame,
            text="⧉ 复制全部信息",
            font=("-apple-system", "SF Pro Text", 11, "semibold"),
            bg=header_bg,
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
