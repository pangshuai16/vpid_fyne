"""USB 设备扫描模块"""
import re
import logging
from typing import List, Tuple, Set, Optional
from .device_info import USBDevice
from .constants import STATUS_CONNECTED, STATUS_ERROR, STATUS_UNKNOWN

try:
    import winreg
except ImportError:
    winreg = None

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def extract_vid_pid(device_id: str) -> Tuple[str, str]:
    """从设备ID中提取 VID 和 PID"""
    vid_match = re.search(r'VID_([0-9A-Fa-f]{4})', device_id, re.IGNORECASE)
    pid_match = re.search(r'PID_([0-9A-Fa-f]{4})', device_id, re.IGNORECASE)
    vid = "0x{0}".format(vid_match.group(1)) if vid_match else ""
    pid = "0x{0}".format(pid_match.group(1)) if pid_match else ""
    return vid, pid


def extract_serial_from_device_id(device_id: str) -> str:
    """从设备ID中提取序列号"""
    parts = str(device_id).split('\\')
    if len(parts) >= 3:
        return parts[2]
    return ""


def scan_usb_devices() -> List[USBDevice]:
    """扫描系统中的 USB 设备"""
    devices = []
    devices_wmi = _scan_via_wmi()
    if devices_wmi:
        devices.extend(devices_wmi)
    if not devices:
        logger.debug("WMI 扫描失败，尝试注册表扫描")
        devices_reg = _scan_via_registry()
        if devices_reg:
            devices.extend(devices_reg)
    result = _deduplicate_devices(devices)
    logger.debug("扫描完成，共找到 %d 个 USB 设备", len(result))
    for d in result:
        logger.debug("  设备: %s VID=%s PID=%s Serial=%s Status=%s",
                     d.get_display_name(), d.vid, d.pid, d.serial, d.status)
    return result


def _scan_via_wmi() -> List[USBDevice]:
    """通过 WMI 扫描 USB 设备"""
    try:
        import wmi
        c = wmi.WMI()
        devices = []
        seen_keys: Set[Tuple[str, str, str]] = set()

        for usb in c.Win32_USBHub():
            vid, pid = extract_vid_pid(usb.DeviceID or "")
            if not vid and not pid:
                continue
            serial = extract_serial_from_device_id(usb.DeviceID or "")
            key = (vid, pid, serial)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            manufacturer = ""
            if usb.PNPDeviceID:
                parts = usb.PNPDeviceID.split('\\')
                if parts:
                    manufacturer = parts[0]

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

        logger.debug("WMI USBHub 扫描完成，找到 %d 个设备", len(devices))

        try:
            for pnp in c.Win32_PnPEntity():
                pnp_id = pnp.PNPDeviceID or ""
                if not pnp_id.upper().startswith("USB"):
                    continue
                vid, pid = extract_vid_pid(pnp_id)
                if not vid or not pid:
                    continue
                serial = extract_serial_from_device_id(pnp_id)
                key = (vid, pid, serial)
                if key in seen_keys:
                    continue
                seen_keys.add(key)

                manufacturer = ""
                if pnp_id:
                    parts = pnp_id.split('\\')
                    if len(parts) > 1:
                        manufacturer = parts[0]

                device = USBDevice(
                    vid=vid,
                    pid=pid,
                    serial=serial,
                    name=pnp.Name or pnp.Caption or "USB Device",
                    manufacturer=manufacturer,
                    location=getattr(pnp, 'DeviceLocator', '') or getattr(pnp, 'Location', ''),
                    driver="",
                    device_id=pnp.DeviceID or "",
                    pnp_device_id=pnp_id,
                    status=STATUS_CONNECTED if getattr(pnp, 'ConfigManagerErrorCode', 0) == 0 else STATUS_ERROR,
                )
                devices.append(device)

            logger.debug("WMI PnPEntity 补充扫描完成，总计 %d 个设备", len(devices))
        except Exception as e:
            logger.debug("WMI PnPEntity 补充扫描失败（非致命）: %s", e)

        return devices
    except Exception as e:
        logger.error("WMI 扫描失败: %s", e, exc_info=True)
        return []


def _scan_via_registry() -> List[USBDevice]:
    """通过注册表扫描 USB 设备，只返回已连接的设备"""
    if winreg is None:
        logger.debug("winreg 不可用，跳过注册表扫描")
        return []
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
                                if device and device.status == STATUS_CONNECTED:
                                    devices.append(device)
                                j += 1
                            except OSError:
                                break
                    i += 1
                except OSError:
                    break
    except Exception as e:
        logger.error("注册表扫描失败: %s", e, exc_info=True)
    logger.debug("注册表扫描完成，找到 %d 个已连接设备", len(devices))
    return devices


def _parse_registry_device(path: str, vid_part: str, pid_part: str) -> Optional[USBDevice]:
    """解析注册表中的设备信息"""
    if winreg is None:
        return None
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
            device_id = "USB\\VID_{0}&PID_{1}".format(vid_part, pid_part)
            name = _get_registry_value(key, "FriendlyName") or _get_registry_value(key, "DeviceDesc") or "USB Device"
            manufacturer = _get_registry_value(key, "Mfg") or ""
            serial = ""
            path_parts = path.split('\\')
            if len(path_parts) >= 4:
                serial = path_parts[3]
            driver = _get_registry_value(key, "Driver") or ""
            location = _get_registry_value(key, "LocationInformation") or ""

            status = STATUS_UNKNOWN
            error_code_str = _get_registry_value(key, "ConfigManagerErrorCode")
            if error_code_str is not None:
                try:
                    error_code = int(error_code_str)
                    status = STATUS_CONNECTED if error_code == 0 else "{0} ({1})".format(STATUS_ERROR, error_code)
                except ValueError:
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
    if winreg is None:
        return None
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
