from dataclasses import dataclass, field
from typing import Optional


@dataclass
class USBDevice:
    vid: str = ""
    pid: str = ""
    serial: str = ""
    name: str = ""
    manufacturer: str = ""
    location: str = ""
    driver: str = ""
    device_id: str = ""
    pnp_device_id: str = ""
    status: str = ""

    def get_display_name(self) -> str:
        if self.name:
            return self.name
        if self.manufacturer:
            return f"{self.manufacturer} Device"
        return "Unknown USB Device"

    def get_vid_pid_string(self) -> str:
        if self.vid and self.pid:
            return f"VID: {self.vid}  PID: {self.pid}"
        return "VID: N/A  PID: N/A"

    def to_dict(self) -> dict:
        return {
            "名称": self.name or "未知设备",
            "供应商ID (VID)": self.vid or "N/A",
            "产品ID (PID)": self.pid or "N/A",
            "序列号": self.serial or "N/A",
            "制造商": self.manufacturer or "N/A",
            "位置": self.location or "N/A",
            "驱动程序": self.driver or "N/A",
            "设备ID": self.device_id or "N/A",
            "状态": self.status or "N/A",
        }

    def to_clipboard_text(self) -> str:
        lines = [
            f"名称: {self.name or 'N/A'}",
            f"供应商ID (VID): {self.vid or 'N/A'}",
            f"产品ID (PID): {self.pid or 'N/A'}",
            f"序列号: {self.serial or 'N/A'}",
            f"制造商: {self.manufacturer or 'N/A'}",
            f"位置: {self.location or 'N/A'}",
            f"驱动程序: {self.driver or 'N/A'}",
            f"状态: {self.status or 'N/A'}",
        ]
        return "\n".join(lines)
