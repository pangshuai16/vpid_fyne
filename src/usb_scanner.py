"""USB 设备扫描模块"""
import re
import logging
from typing import List, Tuple, Set
from .device_info import USBDevice
from .constants import STATUS_CONNECTED, STATUS_ERROR, STATUS_UNKNOWN

try:
    import winreg
except ImportError:
    winreg = None

logger = logging.getLogger(__name__)


def extract_vid_pid(device_id):
    """从设备ID中提取 VID 和 PID

    Args:
        device_id: 设备标识符字符串

    Returns:
        Tuple[str, str]: (vid, pid) 如 ("0x1234", "0x5678")，失败返回空字符串
    """
    vid_match = re.search(r'VID_([0-9A-Fa-f]{4})', device_id, re.IGNORECASE)
    pid_match = re.search(r'PID_([0-9A-Fa-f]{4})', device_id, re.IGNORECASE)
    vid = "0x{0}".format(vid_match.group(1)) if vid_match else ""
    pid = "0x{0}".format(pid_match.group(1)) if pid_match else ""
    return vid, pid


def extract_serial_from_device_id(device_id):
    """从设备ID中提取序列号

    Args:
        device_id: 设备标识符字符串，通常格式为 USB\\VID_xxxx&PID_yyyy\\SERIAL

    Returns:
        str: 序列号字符串
    """
    parts = str(device_id).split('\\')
    if len(parts) >= 3:
        return parts[2]
    return ""


def scan_usb_devices():
    """扫描系统中的 USB 设备

    Returns:
        List[USBDevice]: 设备列表，优先使用 WMI，失败时回退到注册表
    """
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


def _scan_via_wmi():
    """通过 WMI 扫描 USB 设备

    Returns:
        List[USBDevice]: WMI 扫描到的设备列表
    """
    try:
        import wmi
        c = wmi.WMI()
        devices = []
        seen_keys = set()

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
                path=usb.DeviceID or ""
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
                path=pnp.DeviceID or ""
            )
                devices.append(device)

            logger.debug("WMI PnPEntity 补充扫描完成，总计 %d 个设备", len(devices))
        except Exception as e:
            logger.debug("WMI PnPEntity 补充扫描失败（非致命）: %s", e)

        return devices
    except Exception as e:
        logger.error("WMI 扫描失败: %s", e)
        return []


def _scan_via_registry():
    """通过注册表扫描 USB 设备

    Returns:
        List[USBDevice]: 注册表扫描到的设备列表
    """
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
                                # 现在需要遍历设备实例（每个设备都有自己的子键，包含序列号）
                                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, pid_path) as pid_key:
                                    k = 0
                                    while True:
                                        try:
                                            serial_key_name = winreg.EnumKey(pid_key, k)
                                            serial_path = "{0}\\{1}".format(pid_path, serial_key_name)
                                            device = _parse_registry_device(serial_path, vid_key_name, pid_key_name, serial_key_name)
                                            if device:
                                                devices.append(device)
                                            k += 1
                                        except OSError:
                                            break
                                j += 1
                            except OSError:
                                break
                    i += 1
                except OSError:
                    break
    except Exception as e:
        logger.error("注册表扫描失败: %s", e)
    logger.debug("注册表扫描完成，找到 %d 个设备", len(devices))
    return devices


def _parse_registry_device(path, vid_part, pid_part, serial_part):
    """解析注册表中的设备信息

    Args:
        path: 注册表路径
        vid_part: VID 部分（4位十六进制字符串）
        pid_part: PID 部分（4位十六进制字符串）
        serial_part: 序列号/设备实例 ID

    Returns:
        Optional[USBDevice]: 设备对象，解析失败返回 None
    """
    if winreg is None:
        return None
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
            device_id = "USB\\VID_{0}&PID_{1}\\{2}".format(vid_part, pid_part, serial_part)
            name = _get_registry_value(key, "FriendlyName") or _get_registry_value(key, "DeviceDesc") or "USB Device"
            # DeviceDesc 有时候是类似 "USB\\VID_xxxx&PID_xxxx\\Device Description" 格式，需要提取
            if "\\" in name:
                name = name.split("\\")[-1]
            manufacturer = _get_registry_value(key, "Mfg") or ""
            # 同样处理制造商信息
            if "\\" in manufacturer:
                manufacturer = manufacturer.split("\\")[-1]
            serial = serial_part
            driver = _get_registry_value(key, "Driver") or ""
            location = _get_registry_value(key, "LocationInformation") or ""

            # 默认认为设备是已连接的（因为它在 CurrentControlSet 中）
            status = STATUS_CONNECTED
            error_code_str = _get_registry_value(key, "ConfigManagerErrorCode")
            if error_code_str is not None:
                try:
                    error_code = int(error_code_str)
                    if error_code != 0:
                        status = "{0} ({1})".format(STATUS_ERROR, error_code)
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
                path=device_id  # 设置路径为完整设备ID
            )
    except Exception as e:
        logger.debug("解析设备信息失败 %s: %s", path, e)
        return None


def _get_registry_value(key, value_name):
    """获取注册表值

    Args:
        key: 注册表键对象
        value_name: 值名称

    Returns:
        Optional[str]: 值字符串，失败返回 None
    """
    if winreg is None:
        return None
    try:
        value, _ = winreg.QueryValueEx(key, value_name)
        if isinstance(value, (list, tuple)):
            return str(value[0]) if value else ""
        return str(value) if value else ""
    except Exception:
        return None


def _deduplicate_devices(devices):
    """去重设备列表

    Args:
        devices: 设备列表

    Returns:
        List[USBDevice]: 去重后的设备列表
    """
    seen = set()
    unique = []
    for device in devices:
        key = device.get_unique_key()
        if key not in seen:
            seen.add(key)
            unique.append(device)
    return unique


def compare_devices(old_devices, new_devices):
    """对比两个设备列表，找出新增和移除的设备

    Args:
        old_devices: 基准设备列表
        new_devices: 新设备列表

    Returns:
        Tuple[List[USBDevice], List[USBDevice]]: (新增设备列表, 移除设备列表)
    """
    old_keys = {device.get_unique_key() for device in old_devices}
    new_keys = {device.get_unique_key() for device in new_devices}

    added_keys = new_keys - old_keys
    removed_keys = old_keys - new_keys

    added_devices = [device for device in new_devices if device.get_unique_key() in added_keys]
    removed_devices = [device for device in old_devices if device.get_unique_key() in removed_keys]

    return added_devices, removed_devices
