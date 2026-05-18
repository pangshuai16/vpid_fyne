"""USB 设备信息数据模型"""
from typing import Dict, Tuple


class USBDevice(object):
    """USB 设备信息类

    通过 (vid, pid, serial) 三元组唯一标识一个 USB 设备。
    vid/pid 内部存储格式为 "0xXXXX"（带 0x 前缀的大写十六进制）。
    """

    __slots__ = (
        "vid", "pid", "serial", "name", "manufacturer",
        "location", "driver", "device_id", "pnp_device_id",
        "status", "path",
    )

    def __init__(
        self,
        vid="",
        pid="",
        serial="",
        name="",
        manufacturer="",
        location="",
        driver="",
        device_id="",
        pnp_device_id="",
        status="",
        path="",
    ):
        self.vid = vid
        self.pid = pid
        self.serial = serial
        self.name = name
        self.manufacturer = manufacturer
        self.location = location
        self.driver = driver
        self.device_id = device_id
        self.pnp_device_id = pnp_device_id
        self.status = status
        self.path = path

    @staticmethod
    def _strip_0x(hex_str):
        """去除 0x 前缀并转大写

        Args:
            hex_str: 如 "0x8087" 或 "8087"

        Returns:
            str: 如 "8087"
        """
        if hex_str.startswith("0x") or hex_str.startswith("0X"):
            return hex_str[2:].upper()
        return hex_str.upper()

    def get_display_name(self):
        """获取设备显示名称，优先 name → manufacturer → 兜底"""
        if self.name:
            return self.name
        if self.manufacturer:
            return "{0} Device".format(self.manufacturer)
        return "Unknown USB Device"

    def get_formatted_vid(self):
        """格式化 VID，去除 0x 前缀，如 '8087'"""
        return self._strip_0x(self.vid) if self.vid else "N/A"

    def get_formatted_pid(self):
        """格式化 PID，去除 0x 前缀，如 '0024'"""
        return self._strip_0x(self.pid) if self.pid else "N/A"

    def get_vid_pid_string(self):
        """获取 'VID:PID' 格式字符串，如 '8087:0024'"""
        return "{0}:{1}".format(self.get_formatted_vid(), self.get_formatted_pid())

    def get_unique_key(self):
        """获取设备唯一标识 (vid, pid, serial)"""
        return (self.vid, self.pid, self.serial)

    def to_dict(self):
        """转换为有序字典"""
        return {
            "名称": self.name or "未知设备",
            "VID": self.get_formatted_vid(),
            "PID": self.get_formatted_pid(),
            "序列号": self.serial or "N/A",
            "制造商": self.manufacturer or "N/A",
            "位置": self.location or "N/A",
            "路径": self.path or "N/A",
            "驱动": self.driver or "N/A",
            "状态": self.status or "N/A",
        }

    def to_clipboard_text(self):
        """转换为剪贴板文本"""
        return "\n".join(
            "{0}: {1}".format(k, v) for k, v in self.to_dict().items()
        )

    def __eq__(self, other):
        if not isinstance(other, USBDevice):
            return NotImplemented
        return self.get_unique_key() == other.get_unique_key()

    def __hash__(self):
        return hash(self.get_unique_key())

    def __repr__(self):
        return "USBDevice(vid={0!r}, pid={1!r}, serial={2!r}, name={3!r})".format(
            self.vid, self.pid, self.serial, self.name
        )
