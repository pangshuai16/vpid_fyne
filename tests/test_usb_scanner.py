"""测试 USB 扫描模块"""
import pytest
from src.device_info import USBDevice
from src.usb_scanner import (
    extract_vid_pid,
    extract_serial_from_device_id,
    compare_devices,
    _deduplicate_devices
)


def test_extract_vid_pid():
    """测试提取 VID 和 PID"""
    device_id = "USB\\VID_1234&PID_5678\\Serial"
    vid, pid = extract_vid_pid(device_id)
    assert vid == "0x1234"
    assert pid == "0x5678"

    # 测试小写
    device_id2 = "USB\\vid_abcd&PID_cdef\\test"
    vid2, pid2 = extract_vid_pid(device_id2)
    assert vid2 == "0xabcd"
    assert pid2 == "0xcdef"

    # 测试空情况
    vid3, pid3 = extract_vid_pid("")
    assert vid3 == ""
    assert pid3 == ""


def test_extract_serial_from_device_id():
    """测试提取序列号"""
    device_id = "USB\\VID_1234&PID_5678\\ABC123"
    serial = extract_serial_from_device_id(device_id)
    assert serial == "ABC123"

    # 测试没有序列号的情况
    device_id2 = "USB\\VID_1234&PID_5678"
    serial2 = extract_serial_from_device_id(device_id2)
    assert serial2 == ""


def test_compare_devices():
    """测试设备比对"""
    # 创建测试设备
    old_device1 = USBDevice(vid="0x1", pid="0x2", serial="3", name="Old1")
    old_device2 = USBDevice(vid="0x4", pid="0x5", serial="6", name="Old2")
    new_device1 = USBDevice(vid="0x1", pid="0x2", serial="3", name="Old1")
    new_device3 = USBDevice(vid="0x7", pid="0x8", serial="9", name="New")

    old_devices = [old_device1, old_device2]
    new_devices = [new_device1, new_device3]

    added, removed = compare_devices(old_devices, new_devices)

    # 验证结果
    assert len(added) == 1
    assert added[0].name == "New"
    assert len(removed) == 1
    assert removed[0].name == "Old2"

    # 测试空情况
    added2, removed2 = compare_devices([], [])
    assert len(added2) == 0
    assert len(removed2) == 0

    # 测试完全新增
    added3, removed3 = compare_devices([], [new_device1, new_device3])
    assert len(added3) == 2
    assert len(removed3) == 0

    # 测试完全移除
    added4, removed4 = compare_devices([old_device1, old_device2], [])
    assert len(added4) == 0
    assert len(removed4) == 2


def test_deduplicate_devices():
    """测试设备去重"""
    device1 = USBDevice(vid="0x1", pid="0x2", serial="3", name="Device1")
    device2 = USBDevice(vid="0x4", pid="0x5", serial="6", name="Device2")
    device1_dup = USBDevice(vid="0x1", pid="0x2", serial="3", name="Duplicate")

    devices = [device1, device2, device1_dup]
    deduplicated = _deduplicate_devices(devices)

    assert len(deduplicated) == 2
    # 应该保留第一个
    assert deduplicated[0].name == "Device1"
    assert deduplicated[1].name == "Device2"

    # 测试空列表
    assert len(_deduplicate_devices([])) == 0

    # 测试无vid/pid的设备被排除
    device_no_vid = USBDevice(serial="xxx", name="No VID")
    assert len(_deduplicate_devices([device_no_vid])) == 0
