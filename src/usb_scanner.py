"""USB 设备扫描模块

只返回当前真实连接的 USB 设备。已断开的设备不会出现在结果中。
不允许有缓存数据，不允许有模拟数据，不允许有硬编码。

扫描策略（合并去重）：
1. SetupAPI（最可靠）：使用 SetupDiGetClassDevs + DIGCF_PRESENT 标志，
   与 Windows 设备管理器使用相同的 API，只返回当前真正连接的设备。
2. WMI（次可靠）：Win32_USBHub + Win32_PnPEntity，
   通过 ConfigManagerErrorCode == 0 过滤已断开设备。
3. 注册表（最后手段）：CurrentControlSet\\Enum\\USB，
   必须检查 ConfigManagerErrorCode == 0 且 ConfigFlags 不含移除标记。

设备过滤规则：
  不再使用 instance_id.startswith("USB") 过滤，因为很多 USB 设备的实例 ID
  以其他前缀开头（如 HID\\、FTDIBUS\\ 等）。改为检查实例 ID 中是否包含
  VID_ 和 PID_ 模式，这是 USB 设备的专属标识，非 USB 设备不会使用。

注意：注册表 CurrentControlSet\\Enum\\USB 包含历史设备记录，
已断开的设备条目仍然存在，必须严格过滤。
"""
import re
import logging
from typing import List, Tuple, Optional

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
                   或 "HID\\VID_046D&PID_C52B&MI_02\\7&1234"

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
    """构建 USBDevice 实例的统一入口"""
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
    """从 PnP 设备 ID 中提取制造商前缀"""
    if not pnp_id:
        return ""
    parts = pnp_id.split('\\')
    return parts[0] if parts else ""


def _is_device_connected(error_code):
    """判断设备是否真正连接

    ConfigManagerErrorCode 含义：
      0 = 设备正常工作（已连接）
      其他值 = 设备有问题或已断开

    Args:
        error_code: ConfigManagerErrorCode 值

    Returns:
        bool: True 表示设备已连接
    """
    try:
        return int(error_code) == 0
    except (TypeError, ValueError):
        return False


def _has_vid_pid(device_id):
    """检查设备 ID 是否包含 VID 和 PID 模式

    USB 设备的实例 ID 中包含 VID_xxxx&PID_xxxx 模式，
    无论前缀是 USB\\、HID\\、FTDIBUS\\ 还是其他。
    非 USB 设备不会使用此模式。

    Args:
        device_id: 设备实例 ID

    Returns:
        bool: 包含 VID 和 PID 返回 True
    """
    device_id = str(device_id).upper()
    return bool(_VID_RE.search(device_id) and _PID_RE.search(device_id))


def _clean_registry_string(value):
    """清理注册表字符串值，提取反斜杠分隔的最后一段"""
    if not value:
        return ""
    if "\\" in value:
        value = value.split("\\")[-1]
    return value


def _get_registry_value(key, value_name):
    """安全获取注册表值

    注意：必须正确处理值为 0 的情况。
    winreg.QueryValueEx 对于 REG_DWORD 类型返回 int，
    当值为 0 时，int 0 在 Python 中是 falsy 的，
    不能用 `if value` 来判断，否则 0 会被错误地转为空字符串。
    """
    if winreg is None:
        return None
    try:
        value, _ = winreg.QueryValueEx(key, value_name)
        if value is None:
            return None
        if isinstance(value, (list, tuple)):
            return str(value[0]) if value else ""
        return str(value)
    except Exception:
        return None


def _deduplicate_devices(devices):
    """基于 unique key 去重"""
    seen = set()
    unique = []
    for device in devices:
        key = device.get_unique_key()
        if key not in seen:
            seen.add(key)
            unique.append(device)
    return unique


# ============================================================
# 扫描方法 1：SetupAPI（最可靠）
# ============================================================

def _scan_via_setupapi():
    """通过 SetupAPI 扫描当前真实连接的 USB 设备

    使用 SetupDiGetClassDevs + DIGCF_PRESENT 标志，
    只返回当前真正连接的设备。这是最可靠的扫描方法，
    与 Windows 设备管理器使用相同的 API。

    DIGCF_PRESENT 标志确保只枚举当前物理存在的设备，
    已断开的设备不会被返回。

    过滤规则：不再限制 instance_id 必须以 "USB" 开头，
    而是检查是否包含 VID_/PID_ 模式，以涵盖 HID、
    FTDIBUS 等前缀的 USB 设备。

    Returns:
        List[USBDevice]: 当前连接的设备列表
    """
    try:
        import ctypes
    except ImportError:
        logger.debug("ctypes 不可用，跳过 SetupAPI 扫描")
        return []

    DIGCF_PRESENT = 0x00000002
    DIGCF_ALLCLASSES = 0x00000004

    SPDRP_DEVICEDESC = 0x00000000
    SPDRP_FRIENDLYNAME = 0x0000000C
    SPDRP_LOCATION_INFORMATION = 0x0000000D
    SPDRP_MFG = 0x0000000F
    SPDRP_DRIVER = 0x00000009

    class GUID(ctypes.Structure):
        _fields_ = [
            ('Data1', ctypes.c_ulong),
            ('Data2', ctypes.c_ushort),
            ('Data3', ctypes.c_ushort),
            ('Data4', ctypes.c_ubyte * 8),
        ]

    class SP_DEVINFO_DATA(ctypes.Structure):
        _fields_ = [
            ('cbSize', ctypes.c_ulong),
            ('ClassGuid', GUID),
            ('DevInst', ctypes.c_ulong),
            ('Reserved', ctypes.c_void_p),
        ]

    try:
        setupapi = ctypes.windll.setupapi
    except (OSError, AttributeError):
        logger.debug("setupapi.dll 不可用，跳过 SetupAPI 扫描")
        return []

    setupapi.SetupDiGetClassDevsW.restype = ctypes.c_void_p
    setupapi.SetupDiGetClassDevsW.argtypes = [
        ctypes.POINTER(GUID),
        ctypes.c_wchar_p,
        ctypes.c_void_p,
        ctypes.c_ulong,
    ]

    setupapi.SetupDiEnumDeviceInfo.restype = ctypes.c_int
    setupapi.SetupDiEnumDeviceInfo.argtypes = [
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.POINTER(SP_DEVINFO_DATA),
    ]

    setupapi.SetupDiGetDeviceInstanceIdW.restype = ctypes.c_int
    setupapi.SetupDiGetDeviceInstanceIdW.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(SP_DEVINFO_DATA),
        ctypes.c_wchar_p,
        ctypes.c_ulong,
        ctypes.POINTER(ctypes.c_ulong),
    ]

    setupapi.SetupDiDestroyDeviceInfoList.restype = ctypes.c_int
    setupapi.SetupDiDestroyDeviceInfoList.argtypes = [ctypes.c_void_p]

    h_dev_info = setupapi.SetupDiGetClassDevsW(
        None, None, None,
        DIGCF_PRESENT | DIGCF_ALLCLASSES
    )

    if not h_dev_info or h_dev_info == -1:
        logger.error("SetupDiGetClassDevs 失败")
        return []

    devices = []
    seen_keys = set()
    index = 0

    try:
        while True:
            dev_info = SP_DEVINFO_DATA()
            dev_info.cbSize = ctypes.sizeof(SP_DEVINFO_DATA)

            if not setupapi.SetupDiEnumDeviceInfo(
                h_dev_info, index, ctypes.byref(dev_info)
            ):
                break

            instance_id_buf = ctypes.create_unicode_buffer(1024)
            required_size = ctypes.c_ulong(0)

            if setupapi.SetupDiGetDeviceInstanceIdW(
                h_dev_info, ctypes.byref(dev_info),
                instance_id_buf, 1024, ctypes.byref(required_size)
            ):
                instance_id = instance_id_buf.value
                vid, pid = extract_vid_pid(instance_id)
                if vid and pid:
                    serial = extract_serial_from_device_id(instance_id)
                    key = (vid, pid, serial)
                    if key not in seen_keys:
                        seen_keys.add(key)

                        name = _get_setupapi_reg_property(
                            setupapi, h_dev_info, dev_info,
                            SPDRP_FRIENDLYNAME
                        ) or _get_setupapi_reg_property(
                            setupapi, h_dev_info, dev_info,
                            SPDRP_DEVICEDESC
                        )
                        manufacturer = _get_setupapi_reg_property(
                            setupapi, h_dev_info, dev_info,
                            SPDRP_MFG
                        )
                        driver = _get_setupapi_reg_property(
                            setupapi, h_dev_info, dev_info,
                            SPDRP_DRIVER
                        )
                        location = _get_setupapi_reg_property(
                            setupapi, h_dev_info, dev_info,
                            SPDRP_LOCATION_INFORMATION
                        )

                        devices.append(_build_device(
                            vid=vid, pid=pid, serial=serial,
                            name=name, manufacturer=manufacturer,
                            location=location, driver=driver,
                            device_id=instance_id,
                            pnp_device_id=instance_id,
                            status=STATUS_CONNECTED,
                            path=instance_id,
                        ))

            index += 1
    finally:
        setupapi.SetupDiDestroyDeviceInfoList(h_dev_info)

    logger.debug("SetupAPI 扫描完成，找到 %d 个已连接设备", len(devices))
    return devices


def _get_setupapi_reg_property(setupapi, h_dev_info, dev_info, prop_id):
    """获取 SetupAPI 设备注册表属性（字符串类型）

    Args:
        setupapi: setupapi DLL 句柄
        h_dev_info: 设备信息集句柄
        dev_info: SP_DEVINFO_DATA 结构
        prop_id: 属性 ID（如 SPDRP_FRIENDLYNAME）

    Returns:
        str: 属性值，失败返回空字符串
    """
    import ctypes

    buf_size = 512
    buffer = ctypes.create_unicode_buffer(buf_size)
    required_size = ctypes.c_ulong(0)
    data_type = ctypes.c_ulong(0)

    result = setupapi.SetupDiGetDeviceRegistryPropertyW(
        h_dev_info, ctypes.byref(dev_info),
        prop_id, ctypes.byref(data_type),
        ctypes.cast(buffer, ctypes.c_void_p),
        ctypes.sizeof(buffer),
        ctypes.byref(required_size),
    )

    if result:
        return buffer.value

    if ctypes.get_last_error() == 122:
        buf_size = required_size.value + 2
        buffer = ctypes.create_unicode_buffer(buf_size)
        result = setupapi.SetupDiGetDeviceRegistryPropertyW(
            h_dev_info, ctypes.byref(dev_info),
            prop_id, ctypes.byref(data_type),
            ctypes.cast(buffer, ctypes.c_void_p),
            ctypes.sizeof(buffer),
            ctypes.byref(required_size),
        )
        if result:
            return buffer.value

    return ""


# ============================================================
# 扫描方法 2：WMI（次可靠）
# ============================================================

def _scan_via_wmi():
    """通过 WMI 扫描当前连接的 USB 设备

    WMI 的 Win32_USBHub 和 Win32_PnPEntity 查询中，
    通过 ConfigManagerErrorCode == 0 过滤已断开设备。

    过滤规则：不再限制 PNPDeviceID 必须以 "USB" 开头，
    而是检查是否包含 VID_/PID_ 模式，以涵盖 HID、
    FTDIBUS 等前缀的 USB 设备。

    Returns:
        List[USBDevice]: 当前连接的设备列表
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

    def _add_wmi_device(wmi_obj, device_id, pnp_id, name, caption):
        """尝试添加一个 WMI 设备，自动去重，只添加已连接设备"""
        vid, pid = extract_vid_pid(device_id)
        if not vid or not pid:
            return
        error_code = getattr(wmi_obj, 'ConfigManagerErrorCode', None)
        if error_code is None:
            error_code = -1
        if not _is_device_connected(error_code):
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
            location=getattr(wmi_obj, 'DeviceLocator', '') or '',
            driver="",
            device_id=device_id,
            pnp_device_id=pnp_id,
            status=STATUS_CONNECTED,
            path=device_id,
        ))

    try:
        for usb in c.Win32_USBHub():
            _add_wmi_device(
                usb,
                usb.DeviceID or "",
                usb.PNPDeviceID or "",
                usb.Name,
                usb.Caption,
            )
        logger.debug("WMI USBHub 扫描完成，找到 %d 个设备", len(devices))
    except Exception as e:
        logger.error("WMI Win32_USBHub 扫描失败: %s", e)

    try:
        for pnp in c.Win32_PnPEntity():
            pnp_id = pnp.PNPDeviceID or ""
            if not _has_vid_pid(pnp_id):
                continue
            _add_wmi_device(
                pnp,
                pnp.DeviceID or "",
                pnp_id,
                pnp.Name,
                pnp.Caption,
            )
        logger.debug("WMI PnPEntity 补充扫描完成，总计 %d 个设备", len(devices))
    except Exception as e:
        logger.debug("WMI PnPEntity 补充扫描失败（非致命）: %s", e)

    return devices


# ============================================================
# 扫描方法 3：注册表（最后手段）
# ============================================================

def _scan_via_registry():
    """通过注册表扫描当前连接的 USB 设备

    关键：注册表 CurrentControlSet\\Enum\\USB 包含历史设备记录，
    已断开的设备条目仍然存在。必须同时满足以下条件才认为设备已连接：
    1. ConfigManagerErrorCode == 0
    2. ConfigFlags 不包含 CONFIGFLAG_REMOVED (0x00000004) 标记

    注意：注册表 Enum\\USB 路径下只有 USB\\ 前缀的设备，
    HID\\ 等前缀的设备在 Enum\\HID 等其他路径下，
    因此注册表扫描只能发现 USB\\ 前缀的设备。

    Returns:
        List[USBDevice]: 当前连接的设备列表
    """
    if winreg is None:
        logger.debug("winreg 不可用，跳过注册表扫描")
        return []

    devices = []
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, REGISTRY_USB_BASE_PATH
        ) as base_key:
            idx = 0
            while True:
                try:
                    vid_pid_key_name = winreg.EnumKey(base_key, idx)
                    vid, pid = extract_vid_pid(vid_pid_key_name)
                    if vid and pid:
                        vid_pid_path = "{0}\\{1}".format(
                            REGISTRY_USB_BASE_PATH, vid_pid_key_name
                        )
                        _enumerate_registry_instances(
                            vid_pid_path, vid, pid, devices
                        )
                    idx += 1
                except OSError:
                    break
    except Exception as e:
        logger.error("注册表扫描失败: %s", e)

    logger.debug("注册表扫描完成，找到 %d 个已连接设备", len(devices))
    return devices


def _enumerate_registry_instances(vid_pid_path, vid, pid, devices):
    """遍历注册表中某个 VID/PID 下的所有设备实例

    Args:
        vid_pid_path: 注册表路径
        vid: VID 字符串
        pid: PID 字符串
        devices: 输出设备列表（只添加已连接设备）
    """
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, vid_pid_path
        ) as vid_pid_key:
            j = 0
            while True:
                try:
                    instance_key_name = winreg.EnumKey(vid_pid_key, j)
                    instance_path = "{0}\\{1}".format(
                        vid_pid_path, instance_key_name
                    )
                    device = _parse_registry_device(
                        instance_path, vid, pid, instance_key_name
                    )
                    if device:
                        devices.append(device)
                    j += 1
                except OSError:
                    break
    except OSError:
        pass


def _parse_registry_device(path, vid, pid, serial_part):
    """解析注册表中的设备信息

    只返回同时满足以下条件的设备：
    1. ConfigManagerErrorCode == 0（设备正常工作）
    2. ConfigFlags 不包含 CONFIGFLAG_REMOVED 标记

    Args:
        path: 注册表路径
        vid: VID 字符串
        pid: PID 字符串
        serial_part: 设备实例 ID

    Returns:
        Optional[USBDevice]: 已连接的设备对象，未连接或解析失败返回 None
    """
    if winreg is None:
        return None

    vid_hex = vid.replace("0x", "")
    pid_hex = pid.replace("0x", "")
    device_id = "USB\\VID_{0}&PID_{1}\\{2}".format(
        vid_hex, pid_hex, serial_part
    )

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
            error_code_str = _get_registry_value(
                key, "ConfigManagerErrorCode"
            )
            if not _is_device_connected(error_code_str):
                return None

            config_flags_str = _get_registry_value(key, "ConfigFlags")
            if config_flags_str is not None:
                try:
                    config_flags = int(config_flags_str)
                    if config_flags & 0x00000004:
                        return None
                except (TypeError, ValueError):
                    pass

            name = _clean_registry_string(
                _get_registry_value(key, "FriendlyName")
                or _get_registry_value(key, "DeviceDesc")
            )
            manufacturer = _clean_registry_string(
                _get_registry_value(key, "Mfg")
            )
            driver = _get_registry_value(key, "Driver") or ""
            location = _get_registry_value(
                key, "LocationInformation"
            ) or ""

            return _build_device(
                vid=vid, pid=pid, serial=serial_part,
                name=name, manufacturer=manufacturer,
                location=location, driver=driver,
                device_id=device_id, pnp_device_id=device_id,
                status=STATUS_CONNECTED,
                path=device_id,
            )
    except Exception as e:
        logger.debug("解析设备信息失败 %s: %s", path, e)
        return None


# ============================================================
# 主扫描入口
# ============================================================

def scan_usb_devices():
    """扫描系统中当前真实连接的 USB 设备

    只返回当前已连接的设备，已断开的设备不会出现在结果中。
    不允许有缓存数据，不允许有模拟数据，不允许有硬编码。

    扫描策略：合并 SetupAPI + WMI 结果并去重。
    - SetupAPI（DIGCF_PRESENT）和 WMI（ConfigManagerErrorCode==0）
      都有可靠的连接状态检查，合并后不会引入幽灵设备。
    - 注册表仅在前两者都失败时作为最后手段使用。

    设备覆盖范围：
    - USB\\ 前缀：USB 控制器、Hub、复合设备
    - HID\\ 前缀：USB 键盘、鼠标等 HID 设备
    - FTDIBUS\\ 等其他前缀：FTDI 串口等特殊 USB 设备
    只要设备 ID 中包含 VID_/PID_ 模式，就会被识别为 USB 设备。

    Returns:
        List[USBDevice]: 当前连接的设备列表
    """
    devices = []

    devices_setupapi = _scan_via_setupapi()
    if devices_setupapi:
        devices.extend(devices_setupapi)
        logger.debug(
            "SetupAPI 扫描找到 %d 个已连接设备", len(devices_setupapi)
        )

    devices_wmi = _scan_via_wmi()
    if devices_wmi:
        devices.extend(devices_wmi)
        logger.debug("WMI 扫描找到 %d 个已连接设备", len(devices_wmi))

    if devices:
        result = _deduplicate_devices(devices)
        logger.debug("合并去重后共 %d 个已连接 USB 设备", len(result))
        return result

    devices_reg = _scan_via_registry()
    if devices_reg:
        logger.debug(
            "注册表扫描找到 %d 个已连接设备", len(devices_reg)
        )
        return devices_reg

    logger.warning("所有扫描方法均未找到设备")
    return []


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
