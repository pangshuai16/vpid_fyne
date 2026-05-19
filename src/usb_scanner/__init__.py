"""USB 设备扫描模块

跨平台统一入口，自动根据操作系统选择对应的扫描后端。
"""
import sys
import logging
from typing import List, Tuple

from ..device_info import USBDevice

logger = logging.getLogger(__name__)


def scan_usb_devices():
    """扫描系统中当前真实连接的 USB 设备

    根据操作系统自动选择扫描后端：
    - Windows: 使用 SetupAPI + WMI + 注册表
    - Linux/macOS: 使用 libusb/pyusb

    Returns:
        List[USBDevice]: 当前连接的设备列表
    """
    scanner = _get_scanner()
    return scanner.scan()


def _get_scanner():
    """获取当前平台的扫描器实例"""
    if sys.platform == 'win32':
        from .windows import WindowsScanner
        return WindowsScanner()
    else:
        from .libusb_backend import LibUSBScanner
        return LibUSBScanner()


def compare_devices(old_devices, new_devices):
    """对比两个设备列表，找出新增和移除的设备

    Args:
        old_devices: 基准设备列表
        new_devices: 新设备列表

    Returns:
        Tuple[List[USBDevice], List[USBDevice]]: (新增设备列表, 移除设备列表)
    """
    old_keys = {d.get_unique_key() for d in old_devices}
    new_keys = {d.get_unique_key() for d in new_devices}

    added_keys = new_keys - old_keys
    removed_keys = old_keys - new_keys

    added = [d for d in new_devices if d.get_unique_key() in added_keys]
    removed = [d for d in old_devices if d.get_unique_key() in removed_keys]

    return added, removed
