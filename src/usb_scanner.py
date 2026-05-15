"""USB 设备扫描模块

同时使用 WMI 和注册表两种方式扫描，合并去重，确保不遗漏设备。
注册表结构:
  HKLM\\SYSTEM\\CurrentControlSet\\Enum\\USB\\
    VID_8087&PID_0024\\          ← 第一层: VID_xxxx&PID_xxxx 合在一起
      5&1234ABCD&0&1\\           ← 第二层: 设备实例ID
"""
import re
import logging
from typing import List, Tuple, Optional, Set

from .device_info import USBDevice
from .constants import (
    STATUS_CONNECTED, STATUS_ERROR,
    REGISTRY_USB_BASE_PATH, VID_PATTERN, PID_PATTERN,
)

try:
    import winreg
except ImportError:
    winreg = None

logger = logging.getLogger(__name__)

_VID_RE = re.compile(VID_PATTERN, re.IGNORECASE)
_PID_RE = re.compile(PID_PATTERN, re.IGNORECASE)


def extract_vid_pid(device_id):
    """从设备 ID 中提取 VID 和 PID

    Args:
        device_id: 如 "USB\\VID_8087&PID_0024\\5&1234"

    Returns:
        Tuple[str, str]: ("0x8087", "0x0024")，匹配失败返回 ("", "")
    """
    device_id = str(device_id)
    vid_match = _VID_RE.search(device_id)
    pid_match = _PID_RE.search(device_id)
    vid = "0x{0}".format(vid_match.group(1).upper()) if vid_match else ""
    pid = "0x{0}".format(pid_match.group(1).upper()) if pid_match else ""
    return vid, pid


def extract_serial_from_device_id(device_id):
    """从设备 ID 中提取序列号（反斜杠分隔的第三段）

    Args:
        device_id: 如 "USB\\VID_8087&PID_0024\\SERIAL"

    Returns:
        str: 序列号，失败返回空字符串
    """
    parts = str(device_id).split('\\')
    return parts[2] if len(parts) >= 3 else ""


def _build_device(vid, pid, serial, name, manufacturer, location,
                  driver, device_id, pnp_device_id, status, path):
    """构建 USBDevice 实例的统一入口

    集中构造逻辑，避免 WMI / 注册表两处重复。
    """
    return USBDevice(
        vid=vid, pid=pid, serial=serial,
        name=name or "USB Device",
        manufacturer=manufacturer,
        location=location,
        driver=driver,
        device_id=device_id,
        pnp_device_id=pnp_device_id,
        status=status,
        path=path,
    )


def _extract_manufacturer(pnp_id):
    """从 PnP 设备 ID 中提取制造商前缀

    Args:
        pnp_id: 如 "USB\\VID_8087&PID_0024\\5&..."

    Returns:
        str: 制造商前缀，如 "USB"
    """
    if not pnp_id:
        return ""
    parts = pnp_id.split('\\')
    return parts[0] if parts else ""


def _wmi_device_status(obj):
    """从 WMI 对象获取设备状态

    Args:
        obj: WMI Win32_USBHub 或 Win32_PnPEntity 对象

    Returns:
        str: STATUS_CONNECTED 或 STATUS_ERROR
    """
    code = getattr(obj, 'ConfigManagerErrorCode', -1)
    return STATUS_CONNECTED if code == 0 else STATUS_ERROR


def _scan_via_wmi():
    """通过 WMI 扫描 USB 设备（Win32_USBHub + Win32_PnPEntity 补充）

    Returns:
        List[USBDevice]: 去重后的设备列表
    """
    try:
        import wmi
    except ImportError:
        logger.debug("wmi 模块不可用，跳过 WMI 扫描")
        return []

    try:
        c = wmi.WMI()
    except Exception as e:
        logger.error("WMI 连接失败: %s", e)
        return []

    devices = []
    seen_keys = set()

    def _add_wmi_device(device_id, pnp_id, name, caption):
        """尝试添加一个 WMI 设备，自动去重"""
        vid, pid = extract_vid_pid(device_id)
        if not vid or not pid:
            return
        serial = extract_serial_from_device_id(device_id)
        key = (vid, pid, serial)
        if key in seen_keys:
            return
        seen_keys.add(key)
        devices.append(_build_device(
            vid=vid, pid=pid, serial=serial,
            name=name or caption,
            manufacturer=_extract_manufacturer(pnp_id),
            location=getattr(c, 'DeviceLocator', '') or '',
            driver="",
            device_id=device_id,
            pnp_device_id=pnp_id,
            status=_wmi_device_status(obj),
            path=device_id,
        ))

    try:
        for usb in c.Win32_USBHub():
            _add_wmi_device(usb.DeviceID or "", usb.PNPDeviceID or "",
                            usb.Name, usb.Caption)
        logger.debug("WMI USBHub 扫描完成，找到 %d 个设备", len(devices))
    except Exception as e:
        logger.error("WMI Win32_USBHub 扫描失败: %s", e)

    try:
        for pnp in c.Win32_PnPEntity():
            pnp_id = pnp.PNPDeviceID or ""
            if not pnp_id.upper().startswith("USB"):
                continue
            _add_wmi_device(pnp.DeviceID or "", pnp_id,
                            pnp.Name, pnp.Caption)
        logger.debug("WMI PnPEntity 补充扫描完成，总计 %d 个设备", len(devices))
    except Exception as e:
        logger.debug("WMI PnPEntity 补充扫描失败（非致命）: %s", e)

    return devices


def _scan_via_registry():
    """通过注册表扫描 USB 设备

    Returns:
        List[USBDevice]: 设备列表
    """
    if winreg is None:
        logger.debug("winreg 不可用，跳过注册表扫描")
        return []

    devices = []
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REGISTRY_USB_BASE_PATH) as base_key:
            idx = 0
            while True:
                try:
                    vid_pid_key_name = winreg.EnumKey(base_key, idx)
                    vid, pid = extract_vid_pid(vid_pid_key_name)
                    if vid and pid:
                        vid_pid_path = "{0}\\{1}".format(REGISTRY_USB_BASE_PATH, vid_pid_key_name)
                        _enumerate_registry_instances(vid_pid_path, vid, pid, devices)
                    idx += 1
                except OSError:
                    break
    except Exception as e:
        logger.error("注册表扫描失败: %s", e)

    logger.debug("注册表扫描完成，找到 %d 个设备", len(devices))
    return devices


def _enumerate_registry_instances(vid_pid_path, vid, pid, devices):
    """遍历注册表中某个 VID/PID 下的所有设备实例

    Args:
        vid_pid_path: 注册表路径
        vid: VID 字符串，如 "0x8087"
        pid: PID 字符串，如 "0x0024"
        devices: 输出设备列表
    """
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, vid_pid_path) as vid_pid_key:
            j = 0
            while True:
                try:
                    instance_key_name = winreg.EnumKey(vid_pid_key, j)
                    instance_path = "{0}\\{1}".format(vid_pid_path, instance_key_name)
                    device = _parse_registry_device(instance_path, vid, pid, instance_key_name)
                    if device:
                        devices.append(device)
                    j += 1
                except OSError:
                    break
    except OSError:
        pass


def _parse_registry_device(path, vid, pid, serial_part):
    """解析注册表中的设备信息

    Args:
        path: 注册表路径
        vid: VID 字符串，如 "0x8087"
        pid: PID 字符串，如 "0x0024"
        serial_part: 设备实例 ID

    Returns:
        Optional[USBDevice]: 设备对象，解析失败返回 None
    """
    if winreg is None:
        return None

    vid_hex = vid.replace("0x", "")
    pid_hex = pid.replace("0x", "")
    device_id = "USB\\VID_{0}&PID_{1}\\{2}".format(vid_hex, pid_hex, serial_part)

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
            name = _clean_registry_string(
                _get_registry_value(key, "FriendlyName")
                or _get_registry_value(key, "DeviceDesc")
            )
            manufacturer = _clean_registry_string(
                _get_registry_value(key, "Mfg")
            )
            driver = _get_registry_value(key, "Driver") or ""
            location = _get_registry_value(key, "LocationInformation") or ""

            status = STATUS_CONNECTED
            error_code_str = _get_registry_value(key, "ConfigManagerErrorCode")
            if error_code_str is not None:
                try:
                    if int(error_code_str) != 0:
                        status = "{0} ({1})".format(STATUS_ERROR, error_code_str)
                except ValueError:
                    pass

            return _build_device(
                vid=vid, pid=pid, serial=serial_part,
                name=name, manufacturer=manufacturer,
                location=location, driver=driver,
                device_id=device_id, pnp_device_id=device_id,
                status=status, path=device_id,
            )
    except Exception as e:
        logger.debug("解析设备信息失败 %s: %s", path, e)
        return None


def _clean_registry_string(value):
    """清理注册表字符串值，提取反斜杠分隔的最后一段

    Args:
        value: 原始注册表字符串，可能含 "USB\\VID_xxxx\\Description" 格式

    Returns:
        str: 清理后的字符串，空值返回空字符串
    """
    if not value:
        return ""
    if "\\" in value:
        value = value.split("\\")[-1]
    return value


def _get_registry_value(key, value_name):
    """安全获取注册表值

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
    """基于 unique key 去重

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


def scan_usb_devices():
    """扫描系统中的 USB 设备

    同时使用 WMI 和注册表扫描，合并结果后去重。

    Returns:
        List[USBDevice]: 设备列表
    """
    devices = []

    devices_wmi = _scan_via_wmi()
    if devices_wmi:
        devices.extend(devices_wmi)
        logger.debug("WMI 扫描找到 %d 个设备", len(devices_wmi))

    devices_reg = _scan_via_registry()
    if devices_reg:
        devices.extend(devices_reg)
        logger.debug("注册表扫描找到 %d 个设备", len(devices_reg))

    result = _deduplicate_devices(devices)
    logger.debug("扫描完成，去重后共 %d 个 USB 设备", len(result))
    return result


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
