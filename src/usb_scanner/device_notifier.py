"""Windows 设备通知模块

使用 RegisterDeviceNotification API 监听 USB 设备插拔事件。
在 tkinter 窗口上注册，收到 WM_DEVICECHANGE 消息后触发回调。
"""
import ctypes
import logging
import struct
import sys

logger = logging.getLogger(__name__)

# WM_DEVICECHANGE 消息
WM_DEVICECHANGE = 0x0219

# 设备变更事件类型
DBT_DEVICEARRIVAL = 0x8000
DBT_DEVICEREMOVECOMPLETE = 0x8004
DBT_DEVNODES_CHANGED = 0x0007

# 设备类型
DBT_DEVTYP_DEVICEINTERFACE = 5

# 通知标志
DEVICE_NOTIFY_WINDOW_HANDLE = 0

# USB 设备接口 GUID: {A5DCBF10-6530-11D2-901F-00C04FB951ED}
GUID_DEVINTERFACE_USB_DEVICE = (
    0xA5DCBF10, 0x6530, 0x11D2,
    (0x90, 0x1F, 0x00, 0xC0, 0x4F, 0xB9, 0x51, 0xED)
)


class _GUID(ctypes.Structure):
    _fields_ = [
        ('Data1', ctypes.c_ulong),
        ('Data2', ctypes.c_ushort),
        ('Data3', ctypes.c_ushort),
        ('Data4', ctypes.c_ubyte * 8),
    ]


class _DEV_BROADCAST_HDR(ctypes.Structure):
    _fields_ = [
        ('dbch_size', ctypes.c_ulong),
        ('dbch_devicetype', ctypes.c_ulong),
        ('dbch_reserved', ctypes.c_ulong),
    ]


class _DEV_BROADCAST_DEVICEINTERFACE(ctypes.Structure):
    _fields_ = [
        ('dbcc_size', ctypes.c_ulong),
        ('dbcc_devicetype', ctypes.c_ulong),
        ('dbcc_reserved', ctypes.c_ulong),
        ('dbcc_classguid', _GUID),
        ('dbcc_name', ctypes.c_wchar),
    ]


class WindowsDeviceNotifier:
    """Windows USB 设备通知器

    在 tkinter 窗口上注册 RegisterDeviceNotification，
    拦截 WM_DEVICECHANGE 消息并触发回调。
    """

    def __init__(self, hwnd, on_device_change):
        """初始化设备通知器

        Args:
            hwnd: tkinter 窗口的 HWND 句柄
            on_device_change: 回调函数，签名为 callback(event_type, device_name)
                event_type: 'arrival' 或 'removal'
                device_name: 设备名称（可能为空）
        """
        self._hwnd = hwnd
        self._on_device_change = on_device_change
        self._hdevnotify = None
        self._old_proc = None
        self._new_proc = None
        self._registered = False

        self._register()

    def _register(self):
        """注册设备通知"""
        try:
            user32 = ctypes.windll.user32
        except (OSError, AttributeError):
            logger.error("user32.dll 不可用")
            return

        # 构建 DEV_BROADCAST_DEVICEINTERFACE 结构
        guid = _GUID()
        guid.Data1 = GUID_DEVINTERFACE_USB_DEVICE[0]
        guid.Data2 = GUID_DEVINTERFACE_USB_DEVICE[1]
        guid.Data3 = GUID_DEVINTERFACE_USB_DEVICE[2]
        guid.Data4 = (ctypes.c_ubyte * 8)(*GUID_DEVINTERFACE_USB_DEVICE[3])

        dev_broadcast = _DEV_BROADCAST_DEVICEINTERFACE()
        dev_broadcast.dbcc_size = ctypes.sizeof(_DEV_BROADCAST_DEVICEINTERFACE)
        dev_broadcast.dbcc_devicetype = DBT_DEVTYP_DEVICEINTERFACE
        dev_broadcast.dbcc_classguid = guid

        # 注册设备通知
        self._hdevnotify = user32.RegisterDeviceNotificationW(
            ctypes.c_void_p(self._hwnd),
            ctypes.byref(dev_broadcast),
            DEVICE_NOTIFY_WINDOW_HANDLE,
        )

        if not self._hdevnotify:
            error = ctypes.GetLastError()
            logger.warning("RegisterDeviceNotification 失败 (error=%d)", error)
            return

        # 子类化窗口过程
        self._new_proc = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_void_p, ctypes.c_uint,
            ctypes.c_void_p, ctypes.c_void_p
        )(self._window_proc)

        self._old_proc = user32.SetWindowLongPtrW(
            ctypes.c_void_p(self._hwnd),
            -4,  # GWLP_WNDPROC
            self._new_proc,
        )

        self._registered = True
        logger.debug("USB 设备通知已注册")

    def _window_proc(self, hwnd, msg, wparam, lparam):
        """拦截窗口消息"""
        if msg == WM_DEVICECHANGE:
            event_type = wparam
            if event_type in (DBT_DEVICEARRIVAL, DBT_DEVICEREMOVECOMPLETE):
                try:
                    device_name = self._parse_device_info(lparam)
                    event_str = 'arrival' if event_type == DBT_DEVICEARRIVAL else 'removal'
                    logger.debug("USB 设备%s: %s", event_str, device_name or "(未知)")
                    self._on_device_change(event_str, device_name)
                except Exception as e:
                    logger.debug("解析设备通知消息失败: %s", e)
            elif event_type == DBT_DEVNODES_CHANGED:
                logger.debug("DBT_DEVNODES_CHANGED 收到")
                self._on_device_change('devnodes_changed', '')

        # 调用原始窗口过程
        user32 = ctypes.windll.user32
        return user32.CallWindowProcW(
            self._old_proc,
            ctypes.c_void_p(hwnd),
            ctypes.c_uint(msg),
            ctypes.c_void_p(wparam),
            ctypes.c_void_p(lparam),
        )

    @staticmethod
    def _parse_device_info(lparam):
        """从 lParam 解析设备信息"""
        try:
            hdr = _DEV_BROADCAST_HDR.from_address(lparam)
            if hdr.dbch_devicetype == DBT_DEVTYP_DEVICEINTERFACE:
                iface = _DEV_BROADCAST_DEVICEINTERFACE.from_address(lparam)
                return iface.dbcc_name
        except Exception:
            pass
        return ""

    def unregister(self):
        """取消注册"""
        if not self._registered:
            return

        try:
            user32 = ctypes.windll.user32
            if self._old_proc:
                user32.SetWindowLongPtrW(
                    ctypes.c_void_p(self._hwnd),
                    -4,
                    self._old_proc,
                )
            if self._hdevnotify:
                user32.UnregisterDeviceNotification(self._hdevnotify)
            self._registered = False
            logger.debug("USB 设备通知已取消注册")
        except Exception as e:
            logger.error("取消注册设备通知失败: %s", e)

    def is_registered(self):
        return self._registered
