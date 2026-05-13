"""测试设备信息类"""
import pytest
from src.device_info import USBDevice


def test_usb_device_init():
    """测试设备初始化"""
    device = USBDevice(
        vid="0x1234",
        pid="0x5678",
        serial="ABC123",
        name="Test Device",
        manufacturer="Test Mfg"
    )
    assert device.vid == "0x1234"
    assert device.pid == "0x5678"
    assert device.serial == "ABC123"
    assert device.name == "Test Device"
    assert device.manufacturer == "Test Mfg"


def test_get_display_name():
    """测试获取显示名称"""
    # 有名称的情况
    device1 = USBDevice(name="My Device")
    assert device1.get_display_name() == "My Device"

    # 只有制造商的情况
    device2 = USBDevice(manufacturer="My Mfg")
    assert device2.get_display_name() == "My Mfg Device"

    # 没有名称和制造商的情况
    device3 = USBDevice()
    assert device3.get_display_name() == "Unknown USB Device"


def test_get_vid_pid_string():
    """测试获取 VID/PID 字符串"""
    device1 = USBDevice(vid="0x1234", pid="0x5678")
    assert "VID: 0x1234" in device1.get_vid_pid_string()
    assert "PID: 0x5678" in device1.get_vid_pid_string()

    device2 = USBDevice()
    assert "N/A" in device2.get_vid_pid_string()


def test_to_dict():
    """测试转换为字典"""
    device = USBDevice(
        vid="0x1234",
        pid="0x5678",
        name="Test",
        serial="123"
    )
    d = device.to_dict()
    assert d["供应商ID (VID)"] == "0x1234"
    assert d["产品ID (PID)"] == "0x5678"
    assert d["名称"] == "Test"
    assert d["序列号"] == "123"


def test_to_clipboard_text():
    """测试剪贴板文本格式"""
    device = USBDevice(name="Test", vid="0x1234")
    text = device.to_clipboard_text()
    assert "Test" in text
    assert "0x1234" in text


def test_get_unique_key():
    """测试获取唯一键"""
    device = USBDevice(vid="0x1", pid="0x2", serial="3")
    key = device.get_unique_key()
    assert key == ("0x1", "0x2", "3")
