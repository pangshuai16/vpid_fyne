"""设备详情面板组件"""
import tkinter as tk
from tkinter import ttk
from typing import Optional
from ..device_info import USBDevice
from ..constants import (
    APPLE_WHITE,
    APPLE_LIGHT_GRAY,
    APPLE_BLUE,
    APPLE_TEXT,
    APPLE_SECONDARY_TEXT,
    APPLE_BORDER,
    APPLE_GREEN,
    APPLE_RED
)


class DeviceDetailPanel(ttk.Frame):
    """显示 USB 设备详细信息的面板"""

    def __init__(self, parent):
        super(DeviceDetailPanel, self).__init__(parent)
        self.current_device: Optional[USBDevice] = None
        self._setup_ui()

    def _setup_ui(self):
        """初始化 UI 组件"""
        container = tk.Frame(self, bg=APPLE_WHITE)
        container.pack(fill="both", expand=True)

        header_frame = tk.Frame(container, bg=APPLE_LIGHT_GRAY, padx=16, pady=12)
        header_frame.pack(fill="x")

        title_label = tk.Label(
            header_frame,
            text="设备详情",
            font=("-apple-system", "SF Pro Display", 13, "bold"),
            bg=APPLE_LIGHT_GRAY,
            fg=APPLE_TEXT
        )
        title_label.pack(side="left")

        self.icon_label = tk.Label(
            header_frame,
            text="⌥",
            font=("-apple-system", "SF Pro Display", 22),
            bg=APPLE_LIGHT_GRAY,
            fg=APPLE_SECONDARY_TEXT
        )
        self.icon_label.pack(side="right")

        info_container = tk.Frame(container, bg=APPLE_WHITE, padx=16, pady=12)
        info_container.pack(fill="both", expand=True)

        # 字段定义 (标签, 属性名)
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
            row = tk.Frame(info_container, bg=APPLE_WHITE)
            row.pack(fill="x", pady=8)

            label = tk.Label(
                row,
                text=label_text,
                font=("-apple-system", "SF Pro Text", 12),
                bg=APPLE_WHITE,
                fg=APPLE_SECONDARY_TEXT,
                width=13,
                anchor="w"
            )
            label.pack(side="left")

            value_label = tk.Label(
                row,
                text="—",
                font=("-apple-system", "SF Pro Text", 12),
                bg=APPLE_WHITE,
                fg=APPLE_TEXT,
                anchor="w",
                wraplength=240
            )
            value_label.pack(side="left", fill="x", expand=True, padx=(12, 0))
            self.labels[field] = value_label

            if i < len(fields) - 1:
                separator = tk.Frame(info_container, bg=APPLE_BORDER, height=1)
                separator.pack(fill="x", pady=(0, 8))

        button_frame = tk.Frame(container, bg=APPLE_WHITE, padx=16, pady=12)
        button_frame.pack(fill="x", side="bottom")

        copy_frame = tk.Frame(button_frame, bg=APPLE_LIGHT_GRAY, padx=14, pady=9)
        copy_frame.pack(side="left", padx=(0, 12))

        self.copy_btn = tk.Label(
            copy_frame,
            text="⧉ 复制全部信息",
            font=("-apple-system", "SF Pro Text", 11, "semibold"),
            bg=APPLE_LIGHT_GRAY,
            fg=APPLE_BLUE,
            cursor="hand2"
        )
        self.copy_btn.pack()
        self.copy_btn.bind("<Button-1>", self._on_copy_click)

    def _on_copy_click(self, event):
        """复制按钮点击处理"""
        self._copy_current_device_info()

    def set_device(self, device: Optional[USBDevice]):
        """设置要显示的设备"""
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

            # 设置状态颜色
            status_text = device.status or ""
            if status_text == "Connected":
                self.labels["status"].config(fg=APPLE_GREEN)
            elif "Error" in status_text:
                self.labels["status"].config(fg=APPLE_RED)
            else:
                self.labels["status"].config(fg=APPLE_TEXT)
        else:
            for label in self.labels.values():
                label.config(text="—", fg=APPLE_TEXT)

    def get_current_device(self) -> Optional[USBDevice]:
        """获取当前选中的设备"""
        return self.current_device

    def _copy_current_device_info(self):
        """复制当前设备信息到剪贴板"""
        if self.current_device:
            text = self.current_device.to_clipboard_text()
            try:
                self.master.clipboard_clear()
                self.master.clipboard_append(text)
            except:
                pass
