import re
import winreg
from .device_info import USBDevice


def extract_vid_pid(device_id):
    vid_match = re.search(r'VID_([0-9A-Fa-f]{4})', device_id)
    pid_match = re.search(r'PID_([0-9A-Fa-f]{4})', device_id)
    vid = "0x{0}".format(vid_match.group(1)) if vid_match else ""
    pid = "0x{0}".format(pid_match.group(1)) if pid_match else ""
    return vid, pid


def extract_serial_from_device_id(device_id):
    """从设备ID中提取序列号"""
    # 设备ID格式通常为: USB\VID_xxxx&PID_xxxx\SerialNumber
    parts = str(device_id).split('\\')
    if len(parts) >= 3:
        return parts[2]
    return ""


def scan_usb_devices():
    devices = []
    # 优先使用 WMI 扫描（更准确的实时状态）
    devices_wmi = _scan_via_wmi()
    if devices_wmi:
        devices.extend(devices_wmi)
    # 只在 WMI 扫描失败时才使用注册表扫描
    if not devices:
        devices_reg = _scan_via_registry()
        if devices_reg:
            devices.extend(devices_reg)
    return _deduplicate_devices(devices)


def _scan_via_wmi():
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
                status="Connected" if getattr(usb, 'ConfigManagerErrorCode', 0) == 0 else "Error",
            )
            devices.append(device)
        return devices
    except Exception as e:
        return []


def _scan_via_registry():
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
                                if device and device.status == "Connected":  # 只添加已连接的设备
                                    devices.append(device)
                                j += 1
                            except OSError:
                                break
                    i += 1
                except OSError:
                    break
    except Exception:
        pass
    return devices


def _parse_registry_device(path, vid, pid):
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
            device_id = "USB\\VID_{0}&PID_{1}".format(vid, pid)
            name = _get_registry_value(key, "FriendlyName") or _get_registry_value(key, "DeviceDesc") or "USB Device"
            manufacturer = _get_registry_value(key, "Mfg") or ""
            serial = ""  # 注册表键名本身就是序列号
            # 获取序列号（路径的最后部分）
            path_parts = path.split('\\')
            if len(path_parts) >= 4:
                serial = path_parts[3]
            driver = _get_registry_value(key, "Driver") or ""
            location = _get_registry_value(key, "LocationInformation") or ""
            status = "Unknown"
            try:
                error_code = int(_get_registry_value(key, "ConfigManagerErrorCode") or "0")
                status = "Connected" if error_code == 0 else "Error ({0})".format(error_code)
            except:
                pass
            return USBDevice(
                vid="0x{0}".format(vid),
                pid="0x{0}".format(pid),
                serial=serial,
                name=name,
                manufacturer=manufacturer,
                location=location,
                driver=driver,
                device_id=device_id,
                pnp_device_id=device_id,
                status=status,
            )
    except Exception:
        return None


def _get_registry_value(key, value_name):
    try:
        value, _ = winreg.QueryValueEx(key, value_name)
        if isinstance(value, (list, tuple)):
            return str(value[0]) if value else ""
        return str(value) if value else ""
    except Exception:
        return None


def _deduplicate_devices(devices):
    seen = set()
    unique = []
    for device in devices:
        key = (device.vid, device.pid, device.serial)
        if key not in seen and device.vid and device.pid:
            seen.add(key)
            unique.append(device)
    return unique


def compare_devices(old_devices, new_devices):
    old_keys = {(d.vid, d.pid, d.serial) for d in old_devices}
    new_keys = {(d.vid, d.pid, d.serial) for d in new_devices}

    added_keys = new_keys - old_keys
    removed_keys = old_keys - new_keys

    added_devices = [d for d in new_devices if (d.vid, d.pid, d.serial) in added_keys]
    removed_devices = [d for d in old_devices if (d.vid, d.pid, d.serial) in removed_keys]

    return added_devices, removed_devices


def get_device_key(device):
    return "{0}:{1}:{2}".format(device.vid, device.pid, device.serial)
