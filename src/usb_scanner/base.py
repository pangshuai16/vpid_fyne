"""USB 扫描器抽象基类"""
import re
from abc import ABC, abstractmethod
from typing import List, Tuple

from ..constants import VID_PATTERN, PID_PATTERN


class BaseScanner(ABC):
    """USB 设备扫描器抽象基类"""

    _VID_RE = re.compile(VID_PATTERN, re.IGNORECASE)
    _PID_RE = re.compile(PID_PATTERN, re.IGNORECASE)

    @abstractmethod
    def scan(self):
        """扫描当前连接的 USB 设备

        Returns:
            List[USBDevice]: 当前连接的设备列表
        """
        pass

    @classmethod
    def extract_vid_pid(cls, device_id):
        """从设备 ID 中提取 VID 和 PID

        Args:
            device_id: 如 "USB\\VID_8087&PID_0024\\5&1234"

        Returns:
            Tuple[str, str]: ("0x8087", "0x0024")，匹配失败返回 ("", "")
        """
        device_id = str(device_id)
        vid_match = cls._VID_RE.search(device_id)
        pid_match = cls._PID_RE.search(device_id)
        vid = "0x{0}".format(vid_match.group(1).upper()) if vid_match else ""
        pid = "0x{0}".format(pid_match.group(1).upper()) if pid_match else ""
        return vid, pid

    @classmethod
    def extract_serial_from_device_id(cls, device_id):
        """从设备 ID 中提取序列号（反斜杠分隔的第三段）

        Args:
            device_id: 如 "USB\\VID_8087&PID_0024\\SERIAL"

        Returns:
            str: 序列号，失败返回空字符串
        """
        parts = str(device_id).split('\\')
        return parts[2] if len(parts) >= 3 else ""
