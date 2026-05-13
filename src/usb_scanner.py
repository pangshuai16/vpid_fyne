"""USB 设备扫描模块"""
import re
import winreg
import logging
from typing import List, Tuple, Set, Optional
from .device_info import USBDevice
from .constants import STATUS_CONNECTED, STATUS_ERROR, STATUS_UNKNOWN

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def extract_vid_pid(device_id: str) -> Tuple[str, str]:
    """从设备ID中提取 VID 和 PID"""
    vid_match = re.search(r'VID_([0-9A-Fa-f]{4})', device_id)
    pid_match = re.search(r'PID_([0-9A-Fa-f]{4})', device_id)
    vid = "0x{0}".format(vid_match.group(1)) if vid_match else ""
    pid = "0x{0}".format(pid_match.group(1)) if pid_match else ""
    return vid, pid


def extract_serial_from_device_id(device_id: str) -> str:
    """从设备ID中提取序列号"""
    # 设备ID格式通常为: USB\VID_xxxx&PID_xxxx\SerialNumber
    parts = str(device_id).split('\\')
    if len(parts) >= 3:
        return parts[2]
    return ""


def scan_usb_devices() -> List[USBDevice]:
    """扫描系统中的 USB 设备"""
    devices = []
    # 优先使用 WMI 扫描（更准确的实时状态）
    devices_wmi = _scan_via_wmi()
    if devices_wmi:
        devices.extend(devices_wmi)
    # 只在 WMI 扫描失败时才使用注册表扫描
    if not devices:
        logger.debug("WMI 扫描失败，尝试注册表扫描")
        devices_reg = _scan_via_registry()
        if devices_reg:
            devices.extend(devices_reg)
    return _deduplicate_devices(devices)


def _scan_via_wmi() -> List[USBDevice]:
    """通过 WMI 扫描 USB 设备"""
    try:
        import wmi
        c = wmi.WMI()
        devices = []
        for usb in c.Win32_USBHub():
            vid, pid = extract_vid_pid(usb.DeviceID or "")
            manufacturer = ""
            if usb.PNPDeviceID:
                parts = usb.PNPDeviceID.split('\\')
                if parts:
                    manufacturer = parts[0]
            serial = extract_serial_from_device_id(usb.DeviceID or "")
            device = USBDevice(
                vid=vid,
                pid=pid,
                serial=serial,
                name=usb.Name or usb.Caption or "USB Device",
                manufacturer=manufacturer,
                location=getattr(usb, 'DeviceLocator', '') or getattr(usb, 'Location', ''),
                driver="",
                device_id=usb.DeviceID or "",
                pnp_device_id=usb.PNPDeviceID or "",
                status=STATUS_CONNECTED if getattr(usb, 'ConfigManagerErrorCode', 0) == 0 else STATUS_ERROR,
            )
            devices.append(device)
        return devices
    except Exception as e:
        logger.error("WMI 扫描失败: %s", e, exc_info=True)
        return []


def _scan_via_registry() -> List[USBDevice]:
    """通过注册表扫描 USB 设备，只返回已连接的设备"""
    devices = []
    try:
        base_path = r"SYSTEM\CurrentControlSet\Enum\USB"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_path) as base_key:
            i = 0
            while True:
                try:
                    vid_key_name = winreg.EnumKey(base_key, i)
                    vid_path = "{0}\\{1}".format(base_path, vid_key_name)
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, vid_path) as vid_key:
                        j = 0
                        while True:
                            try:
                                pid_key_name = winreg.EnumKey(vid_key, j)
                                pid_path = "{0}\\{1}".format(vid_path, pid_key_name)
                                device = _parse_registry_device(pid_path, vid_key_name, pid_key_name)
                                if device and device.status == STATUS_CONNECTED:  # 只添加已连接的设备
                                    devices.append(device)
                                j += 1
                            except OSError:
                                break
                    i += 1
                except OSError:
                    break
    except Exception as e:
        logger.error("注册表扫描失败: %s", e, exc_info=True)
    return devices


def _parse_registry_device(path: str, vid_part: str, pid_part: str) -> Optional[USBDevice]:
    """解析注册表中的设备信息"""
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
            device_id = "USB\\VID_{0}&PID_{1}".format(vid_part, pid_part)
            name = _get_registry_value(key, "FriendlyName") or _get_registry_value(key, "DeviceDesc") or "USB Device"
            manufacturer = _get_registry_value(key, "Mfg") or ""
            serial = ""  # 注册表键名本身就是序列号
            # 获取序列号（路径的最后部分）
            path_parts = path.split('\\')
            if len(path_parts) >= 4:
                serial = path_parts[3]
            driver = _get_registry_value(key, "Driver") or ""
            location = _get_registry_value(key, "LocationInformation") or ""
            status = STATUS_UNKNOWN
            try:
                error_code = int(_get_registry_value(key, "ConfigManagerErrorCode") or "0")
                status = STATUS_CONNECTED if error_code == 0 else "{0} ({1})".format(STATUS_ERROR, error_code)
            except:
                pass
            return USBDevice(
                vid="0x{0}".format(vid_part),
                pid="0x{0}".format(pid_part),
                serial=serial,
                name=name,
                manufacturer=manufacturer,
                location=location,
                driver=driver,
                device_id=device_id,
                pnp_device_id=device_id,
                status=status,
            )
    except Exception as e:
        logger.debug("解析设备信息失败 %s: %s", path, e)
        return None


def _get_registry_value(key, value_name: str) -> Optional[str]:
    """获取注册表值"""
    try:
        value, _ = winreg.QueryValueEx(key, value_name)
        if isinstance(value, (list, tuple)):
            return str(value[0]) if value else ""
        return str(value) if value else ""
    except Exception:
        return None


def _deduplicate_devices(devices: List[USBDevice]) -> List[USBDevice]:
    """去重设备列表"""
    seen: Set[Tuple[str, str, str]] = set()
    unique = []
    for device in devices:
        key = device.get_unique_key()
        if key not in seen and device.vid and device.pid:
            seen.add(key)
            unique.append(device)
    return unique


def compare_devices(old_devices: List[USBDevice], new_devices: List[USBDevice]) -> Tuple[List[USBDevice], List[USBDevice]]:
    """对比两个设备列表，找出新增和移除的设备"""
    old_keys = {device.get_unique_key() for device in old_devices}
    new_keys = {device.get_unique_key() for device in new_devices}

    added_keys = new_keys - old_keys
    removed_keys = old_keys - new_keys

    added_devices = [device for device in new_devices if device.get_unique_key() in added_keys]
    removed_devices = [device for device in old_devices if device.get_unique_key() in removed_keys]

    return added_devices, removed_devices
