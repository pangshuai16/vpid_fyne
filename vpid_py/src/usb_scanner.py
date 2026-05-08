import re
import winreg
from typing import List, Optional
from .device_info import USBDevice


def extract_vid_pid(device_id: str) -> tuple:
    vid_match = re.search(r'VID_([0-9A-Fa-f]{4})', device_id)
    pid_match = re.search(r'PID_([0-9A-Fa-f]{4})', device_id)
    vid = f"0x{vid_match.group(1)}" if vid_match else ""
    pid = f"0x{pid_match.group(1)}" if pid_match else ""
    return vid, pid


def scan_usb_devices() -> List[USBDevice]:
    devices = []
    devices_wmi = _scan_via_wmi()
    if devices_wmi:
        devices.extend(devices_wmi)
    if not devices:
        devices_reg = _scan_via_registry()
        if devices_reg:
            devices.extend(devices_reg)
    return _deduplicate_devices(devices)


def _scan_via_wmi() -> List[USBDevice]:
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
            device = USBDevice(
                vid=vid,
                pid=pid,
                serial=usb.DeviceID or "",
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


def _scan_via_registry() -> List[USBDevice]:
    devices = []
    try:
        base_path = r"SYSTEM\CurrentControlSet\Enum\USB"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_path) as base_key:
            i = 0
            while True:
                try:
                    vid_key_name = winreg.EnumKey(base_key, i)
                    vid_path = f"{base_path}\\{vid_key_name}"
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, vid_path) as vid_key:
                        j = 0
                        while True:
                            try:
                                pid_key_name = winreg.EnumKey(vid_key, j)
                                pid_path = f"{vid_path}\\{pid_key_name}"
                                device = _parse_registry_device(pid_path, vid_key_name, pid_key_name)
                                if device:
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


def _parse_registry_device(path: str, vid: str, pid: str) -> Optional[USBDevice]:
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
            device_id = f"USB\\VID_{vid}&PID_{pid}"
            name = _get_registry_value(key, "FriendlyName") or _get_registry_value(key, "DeviceDesc") or "USB Device"
            manufacturer = _get_registry_value(key, "Mfg") or ""
            serial = _get_registry_value(key, "SerialNumber") or ""
            driver = _get_registry_value(key, "Driver") or ""
            location = _get_registry_value(key, "LocationInformation") or ""
            status = "Unknown"
            try:
                error_code = int(_get_registry_value(key, "ConfigManagerErrorCode") or "0")
                status = "Connected" if error_code == 0 else f"Error ({error_code})"
            except:
                pass
            return USBDevice(
                vid=f"0x{vid}",
                pid=f"0x{pid}",
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


def _get_registry_value(key, value_name: str) -> Optional[str]:
    try:
        value, _ = winreg.QueryValueEx(key, value_name)
        if isinstance(value, (list, tuple)):
            return str(value[0]) if value else ""
        return str(value) if value else ""
    except Exception:
        return None


def _deduplicate_devices(devices: List[USBDevice]) -> List[USBDevice]:
    seen = set()
    unique = []
    for device in devices:
        key = (device.vid, device.pid, device.serial)
        if key not in seen and device.vid and device.pid:
            seen.add(key)
            unique.append(device)
    return unique
