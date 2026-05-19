"""Linux/macOS USB 设备扫描器（基于 libusb/pyusb）

使用 libusb 1.0 通过 pyusb 绑定扫描当前连接的 USB 设备。
libusb 直接访问 USB 总线，只返回当前物理连接的设备。
"""
import logging
from typing import List

from ..device_info import USBDevice
from ..constants import STATUS_CONNECTED
from .base import BaseScanner

logger = logging.getLogger(__name__)


class LibUSBScanner(BaseScanner):
    """基于 libusb/pyusb 的跨平台 USB 设备扫描器

    支持 Linux 和 macOS，直接访问 USB 总线获取设备信息。
    """

    def scan(self):
        """扫描当前连接的 USB 设备

        Returns:
            List[USBDevice]: 当前连接的设备列表
        """
        try:
            import usb.core
            import usb.util
        except ImportError:
            logger.error("pyusb 模块未安装，无法扫描 USB 设备")
            return []

        devices = []
        seen_keys = set()

        try:
            bus_devices = usb.core.find(find_all=True)
        except Exception as e:
            logger.error("libusb 扫描失败: %s", e)
            return []

        for dev in bus_devices:
            try:
                vid = dev.idVendor
                pid = dev.idProduct

                if vid is None or pid is None:
                    continue

                vid_str = "0x{0:04X}".format(vid)
                pid_str = "0x{0:04X}".format(pid)

                serial = self._get_string(dev, dev.iSerialNumber)
                name = self._get_string(dev, dev.iProduct) or "USB Device"
                manufacturer = self._get_string(dev, dev.iManufacturer) or ""

                key = (vid_str, pid_str, serial)
                if key in seen_keys:
                    continue
                seen_keys.add(key)

                device_id = "USB\\VID_{0:04X}&PID_{1:04X}\\{2}".format(
                    vid, pid, serial or ""
                )

                devices.append(USBDevice(
                    vid=vid_str,
                    pid=pid_str,
                    serial=serial or "",
                    name=name,
                    manufacturer=manufacturer,
                    location="bus {0} device {1}".format(dev.bus, dev.address),
                    driver="",
                    device_id=device_id,
                    pnp_device_id=device_id,
                    status=STATUS_CONNECTED,
                    path=device_id,
                ))
            except Exception as e:
                logger.debug("解析 USB 设备失败: %s", e)
                continue

        logger.debug("libusb 扫描完成，找到 %d 个已连接设备", len(devices))
        return devices

    @staticmethod
    def _get_string(dev, index):
        """安全获取 USB 设备字符串描述符

        Args:
            dev: usb.core.Device 对象
            index: 字符串描述符索引

        Returns:
            str: 字符串内容，失败返回空字符串
        """
        if index == 0:
            return ""
        try:
            import usb.util
            return usb.util.get_string(dev, index) or ""
        except Exception:
            return ""
