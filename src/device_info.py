"""USB 设备信息数据模型"""
from typing import Dict, Optional


class USBDevice(object):
    """USB 设备信息类"""

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
        path=""  # 新增路径字段
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

    def get_display_name(self):
        """获取设备显示名称"""
        if self.name:
            return self.name
        if self.manufacturer:
            return "{0} Device".format(self.manufacturer)
        return "Unknown USB Device"

    def get_formatted_vid(self):
        """获取格式化后的 VID（例如：8087）"""
        # 移除 0x 前缀并转为大写
        if self.vid.startswith("0x"):
            return self.vid[2:].upper()
        return self.vid.upper()

    def get_formatted_pid(self):
        """获取格式化后的 PID（例如：0024）"""
        # 移除 0x 前缀并转为大写
        if self.pid.startswith("0x"):
            return self.pid[2:].upper()
        return self.pid.upper()

    def get_vid_pid_string(self):
        """获取 VID/PID 格式化字符串"""
        return "{0}:{1}".format(self.get_formatted_vid(), self.get_formatted_pid())

    def to_dict(self):
        """转换为字典格式"""
        return {
            "名称": self.name or "未知设备",
            "VID": self.get_formatted_vid() or "N/A",
            "PID": self.get_formatted_pid() or "N/A",
            "序列号": self.serial or "N/A",
            "制造商": self.manufacturer or "N/A",
            "位置": self.location or "N/A",
            "路径": self.path or "N/A",
            "驱动": self.driver or "N/A",
            "状态": self.status or "N/A",
        }

    def to_clipboard_text(self):
        """转换为剪贴板文本格式"""
        data = self.to_dict()
        lines = ["{0}: {1}".format(key, value) for key, value in data.items()]
        return "\n".join(lines)

    def get_unique_key(self):
        """获取设备唯一标识 key"""
        return (self.vid, self.pid, self.serial)

    def __eq__(self, other):
        """两个设备基于唯一 key 比较是否相等"""
        if not isinstance(other, USBDevice):
            return False
        return self.get_unique_key() == other.get_unique_key()

    def __hash__(self):
        """哈希基于唯一 key"""
        return hash(self.get_unique_key())
