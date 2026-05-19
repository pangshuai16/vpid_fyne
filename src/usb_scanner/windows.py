"""Windows USB 设备扫描器

使用 SetupAPI + WMI + 注册表扫描当前连接的 USB 设备。
与 Windows 设备管理器使用相同的 API，只返回当前真正连接的设备。
"""
import logging
from typing import List, Optional

from ..device_info import USBDevice
from ..constants import (
    STATUS_CONNECTED,
    REGISTRY_USB_BASE_PATH,
)
from .base import BaseScanner

try:
    import winreg
except ImportError:
    winreg = None

logger = logging.getLogger(__name__)


class WindowsScanner(BaseScanner):
    """Windows 平台 USB 设备扫描器"""

    def scan(self):
        """扫描系统中当前真实连接的 USB 设备

        扫描策略：合并 SetupAPI + WMI 结果并去重。
        - SetupAPI（DIGCF_PRESENT）和 WMI（ConfigManagerErrorCode==0）
          都有可靠的连接状态检查，合并后不会引入幽灵设备。
        - 注册表仅在前两者都失败时作为最后手段使用。

        Returns:
            List[USBDevice]: 当前连接的设备列表
        """
        devices = []

        devices_setupapi = self._scan_via_setupapi()
        if devices_setupapi:
            devices.extend(devices_setupapi)
            logger.debug(
                "SetupAPI 扫描找到 %d 个已连接设备", len(devices_setupapi)
            )

        devices_wmi = self._scan_via_wmi()
        if devices_wmi:
            devices.extend(devices_wmi)
            logger.debug("WMI 扫描找到 %d 个已连接设备", len(devices_wmi))

        if devices:
            result = self._deduplicate_devices(devices)
            logger.debug("合并去重后共 %d 个已连接 USB 设备", len(result))
            return result

        devices_reg = self._scan_via_registry()
        if devices_reg:
            logger.debug(
                "注册表扫描找到 %d 个已连接设备", len(devices_reg)
            )
            return devices_reg

        logger.warning("所有扫描方法均未找到设备")
        return []

    @staticmethod
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

    @staticmethod
    def _extract_manufacturer(pnp_id):
        """从 PnP 设备 ID 中提取制造商前缀"""
        if not pnp_id:
            return ""
        parts = pnp_id.split('\\')
        return parts[0] if parts else ""

    @staticmethod
    def _is_device_connected(error_code):
        """判断设备是否真正连接

        ConfigManagerErrorCode 含义：
          0 = 设备正常工作（已连接）
          其他值 = 设备有问题或已断开
        """
        try:
            return int(error_code) == 0
        except (TypeError, ValueError):
            return False

    @classmethod
    def _has_vid_pid(cls, device_id):
        """检查设备 ID 是否包含 VID 和 PID 模式"""
        device_id = str(device_id).upper()
        return bool(cls._VID_RE.search(device_id) and cls._PID_RE.search(device_id))

    @staticmethod
    def _clean_registry_string(value):
        """清理注册表字符串值，提取反斜杠分隔的最后一段"""
        if not value:
            return ""
        if "\\" in value:
            value = value.split("\\")[-1]
        return value

    @staticmethod
    def _get_registry_value(key, value_name):
        """安全获取注册表值"""
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

    @staticmethod
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

    def _scan_via_setupapi(self):
        """通过 SetupAPI 扫描当前真实连接的 USB 设备"""
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
            ctypes.POINTER(GUID), ctypes.c_wchar_p, ctypes.c_void_p, ctypes.c_ulong,
        ]
        setupapi.SetupDiEnumDeviceInfo.restype = ctypes.c_int
        setupapi.SetupDiEnumDeviceInfo.argtypes = [
            ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(SP_DEVINFO_DATA),
        ]
        setupapi.SetupDiGetDeviceInstanceIdW.restype = ctypes.c_int
        setupapi.SetupDiGetDeviceInstanceIdW.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(SP_DEVINFO_DATA),
            ctypes.c_wchar_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong),
        ]
        setupapi.SetupDiDestroyDeviceInfoList.restype = ctypes.c_int
        setupapi.SetupDiDestroyDeviceInfoList.argtypes = [ctypes.c_void_p]

        h_dev_info = setupapi.SetupDiGetClassDevsW(
            None, None, None, DIGCF_PRESENT | DIGCF_ALLCLASSES
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
                    vid, pid = self.extract_vid_pid(instance_id)
                    if vid and pid:
                        serial = self.extract_serial_from_device_id(instance_id)
                        key = (vid, pid, serial)
                        if key not in seen_keys:
                            seen_keys.add(key)

                            name = self._get_setupapi_reg_property(
                                setupapi, h_dev_info, dev_info, SPDRP_FRIENDLYNAME
                            ) or self._get_setupapi_reg_property(
                                setupapi, h_dev_info, dev_info, SPDRP_DEVICEDESC
                            )
                            manufacturer = self._get_setupapi_reg_property(
                                setupapi, h_dev_info, dev_info, SPDRP_MFG
                            )
                            driver = self._get_setupapi_reg_property(
                                setupapi, h_dev_info, dev_info, SPDRP_DRIVER
                            )
                            location = self._get_setupapi_reg_property(
                                setupapi, h_dev_info, dev_info, SPDRP_LOCATION_INFORMATION
                            )

                            devices.append(self._build_device(
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

    def _get_setupapi_reg_property(self, setupapi, h_dev_info, dev_info, prop_id):
        """获取 SetupAPI 设备注册表属性（字符串类型）"""
        import ctypes

        buf_size = 512
        buffer = ctypes.create_unicode_buffer(buf_size)
        required_size = ctypes.c_ulong(0)
        data_type = ctypes.c_ulong(0)

        result = setupapi.SetupDiGetDeviceRegistryPropertyW(
            h_dev_info, ctypes.byref(dev_info), prop_id, ctypes.byref(data_type),
            ctypes.cast(buffer, ctypes.c_void_p), ctypes.sizeof(buffer),
            ctypes.byref(required_size),
        )

        if result:
            return buffer.value

        if ctypes.get_last_error() == 122:
            buf_size = required_size.value + 2
            buffer = ctypes.create_unicode_buffer(buf_size)
            result = setupapi.SetupDiGetDeviceRegistryPropertyW(
                h_dev_info, ctypes.byref(dev_info), prop_id, ctypes.byref(data_type),
                ctypes.cast(buffer, ctypes.c_void_p), ctypes.sizeof(buffer),
                ctypes.byref(required_size),
            )
            if result:
                return buffer.value

        return ""

    # ============================================================
    # 扫描方法 2：WMI（次可靠）
    # ============================================================

    def _scan_via_wmi(self):
        """通过 WMI 扫描当前连接的 USB 设备"""
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
            vid, pid = self.extract_vid_pid(device_id)
            if not vid or not pid:
                return
            error_code = getattr(wmi_obj, 'ConfigManagerErrorCode', None)
            if error_code is None:
                error_code = -1
            if not self._is_device_connected(error_code):
                return
            serial = self.extract_serial_from_device_id(device_id)
            key = (vid, pid, serial)
            if key in seen_keys:
                return
            seen_keys.add(key)
            devices.append(self._build_device(
                vid=vid, pid=pid, serial=serial,
                name=name or caption,
                manufacturer=self._extract_manufacturer(pnp_id),
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
                    usb, usb.DeviceID or "", usb.PNPDeviceID or "",
                    usb.Name, usb.Caption,
                )
            logger.debug("WMI USBHub 扫描完成，找到 %d 个设备", len(devices))
        except Exception as e:
            logger.error("WMI Win32_USBHub 扫描失败: %s", e)

        try:
            for pnp in c.Win32_PnPEntity():
                pnp_id = pnp.PNPDeviceID or ""
                if not self._has_vid_pid(pnp_id):
                    continue
                _add_wmi_device(
                    pnp, pnp.DeviceID or "", pnp_id,
                    pnp.Name, pnp.Caption,
                )
            logger.debug("WMI PnPEntity 补充扫描完成，总计 %d 个设备", len(devices))
        except Exception as e:
            logger.debug("WMI PnPEntity 补充扫描失败（非致命）: %s", e)

        return devices

    # ============================================================
    # 扫描方法 3：注册表（最后手段）
    # ============================================================

    def _scan_via_registry(self):
        """通过注册表扫描当前连接的 USB 设备"""
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
                        vid, pid = self.extract_vid_pid(vid_pid_key_name)
                        if vid and pid:
                            vid_pid_path = "{0}\\{1}".format(
                                REGISTRY_USB_BASE_PATH, vid_pid_key_name
                            )
                            self._enumerate_registry_instances(
                                vid_pid_path, vid, pid, devices
                            )
                        idx += 1
                    except OSError:
                        break
        except Exception as e:
            logger.error("注册表扫描失败: %s", e)

        logger.debug("注册表扫描完成，找到 %d 个已连接设备", len(devices))
        return devices

    def _enumerate_registry_instances(self, vid_pid_path, vid, pid, devices):
        """遍历注册表中某个 VID/PID 下的所有设备实例"""
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
                        device = self._parse_registry_device(
                            instance_path, vid, pid, instance_key_name
                        )
                        if device:
                            devices.append(device)
                        j += 1
                    except OSError:
                        break
        except OSError:
            pass

    def _parse_registry_device(self, path, vid, pid, serial_part):
        """解析注册表中的设备信息"""
        if winreg is None:
            return None

        vid_hex = vid.replace("0x", "")
        pid_hex = pid.replace("0x", "")
        device_id = "USB\\VID_{0}&PID_{1}\\{2}".format(
            vid_hex, pid_hex, serial_part
        )

        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                error_code_str = self._get_registry_value(
                    key, "ConfigManagerErrorCode"
                )
                if not self._is_device_connected(error_code_str):
                    return None

                config_flags_str = self._get_registry_value(key, "ConfigFlags")
                if config_flags_str is not None:
                    try:
                        config_flags = int(config_flags_str)
                        if config_flags & 0x00000004:
                            return None
                    except (TypeError, ValueError):
                        pass

                name = self._clean_registry_string(
                    self._get_registry_value(key, "FriendlyName")
                    or self._get_registry_value(key, "DeviceDesc")
                )
                manufacturer = self._clean_registry_string(
                    self._get_registry_value(key, "Mfg")
                )
                driver = self._get_registry_value(key, "Driver") or ""
                location = self._get_registry_value(
                    key, "LocationInformation"
                ) or ""

                return self._build_device(
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
