"""测试 USB 扫描模块"""
import pytest
import sys

from src.device_info import USBDevice
from src.usb_scanner.base import BaseScanner
from src.usb_scanner import compare_devices


class TestBaseScanner:
    """测试 BaseScanner 基础方法"""

    def test_extract_vid_pid(self):
        """测试提取 VID 和 PID"""
        device_id = "USB\\VID_1234&PID_5678\\Serial"
        vid, pid = BaseScanner.extract_vid_pid(device_id)
        assert vid == "0x1234"
        assert pid == "0x5678"

        # 测试小写（结果转为大写）
        device_id2 = "USB\\vid_abcd&PID_cdef\\test"
        vid2, pid2 = BaseScanner.extract_vid_pid(device_id2)
        assert vid2 == "0xABCD"
        assert pid2 == "0xCDEF"

        # 测试空情况
        vid3, pid3 = BaseScanner.extract_vid_pid("")
        assert vid3 == ""
        assert pid3 == ""

    def test_extract_serial_from_device_id(self):
        """测试提取序列号"""
        device_id = "USB\\VID_1234&PID_5678\\ABC123"
        serial = BaseScanner.extract_serial_from_device_id(device_id)
        assert serial == "ABC123"

        # 测试没有序列号的情况
        device_id2 = "USB\\VID_1234&PID_5678"
        serial2 = BaseScanner.extract_serial_from_device_id(device_id2)
        assert serial2 == ""


class TestCompareDevices:
    """测试设备比对功能"""

    def test_compare_devices(self):
        """测试设备比对"""
        old_device1 = USBDevice(vid="0x1", pid="0x2", serial="3", name="Old1")
        old_device2 = USBDevice(vid="0x4", pid="0x5", serial="6", name="Old2")
        new_device1 = USBDevice(vid="0x1", pid="0x2", serial="3", name="Old1")
        new_device3 = USBDevice(vid="0x7", pid="0x8", serial="9", name="New")

        old_devices = [old_device1, old_device2]
        new_devices = [new_device1, new_device3]

        added, removed = compare_devices(old_devices, new_devices)

        assert len(added) == 1
        assert added[0].name == "New"
        assert len(removed) == 1
        assert removed[0].name == "Old2"

    def test_compare_empty(self):
        """测试空列表比对"""
        added, removed = compare_devices([], [])
        assert len(added) == 0
        assert len(removed) == 0

    def test_compare_all_added(self):
        """测试完全新增"""
        device = USBDevice(vid="0x1", pid="0x2", serial="3", name="Test")
        added, removed = compare_devices([], [device])
        assert len(added) == 1
        assert len(removed) == 0

    def test_compare_all_removed(self):
        """测试完全移除"""
        device = USBDevice(vid="0x1", pid="0x2", serial="3", name="Test")
        added, removed = compare_devices([device], [])
        assert len(added) == 0
        assert len(removed) == 1


class TestPlatformScanner:
    """测试平台扫描器"""

    def test_scanner_import(self):
        """测试扫描器可以正确导入"""
        if sys.platform == 'win32':
            from src.usb_scanner.windows import WindowsScanner
            scanner = WindowsScanner()
            assert scanner is not None
        else:
            from src.usb_scanner.libusb_backend import LibUSBScanner
            scanner = LibUSBScanner()
            assert scanner is not None

    def test_scan_returns_list(self):
        """测试 scan 返回列表"""
        if sys.platform == 'win32':
            from src.usb_scanner.windows import WindowsScanner
            scanner = WindowsScanner()
        else:
            from src.usb_scanner.libusb_backend import LibUSBScanner
            scanner = LibUSBScanner()

        result = scanner.scan()
        assert isinstance(result, list)
