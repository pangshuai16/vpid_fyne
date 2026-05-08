__version__ = "1.0.0"
__author__ = "vpid_py"

from .device_info import USBDevice
from .usb_scanner import scan_usb_devices

__all__ = ['USBDevice', 'scan_usb_devices']
