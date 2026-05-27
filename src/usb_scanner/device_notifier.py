"""跨平台 USB 设备通知模块

Windows: 使用 RegisterDeviceNotification API 监听 WM_DEVICECHANGE 消息。
Linux/macOS: 使用 libusb_hotplug_register_callback 监听设备插拔事件。
"""
import ctypes
import logging
import sys
import threading
import queue

logger = logging.getLogger(__name__)


# ==================== Windows 实现 ====================

if sys.platform == 'win32':
    import atexit

    WM_DEVICECHANGE = 0x0219
    DBT_DEVICEARRIVAL = 0x8000
    DBT_DEVICEREMOVECOMPLETE = 0x8004
    DBT_DEVNODES_CHANGED = 0x0007
    DBT_DEVTYP_DEVICEINTERFACE = 5
    DEVICE_NOTIFY_WINDOW_HANDLE = 0
    GWLP_WNDPROC = -4

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

        在 tkinter 主窗口上注册 RegisterDeviceNotification，
        并通过 SetWindowLongPtrW 子类化窗口过程来拦截 WM_DEVICECHANGE。
        """

        _instances = {}

        def __init__(self, hwnd, on_device_change):
            self._hwnd = hwnd
            self._on_device_change = on_device_change
            self._hdevnotify = None
            self._old_proc = None
            self._new_proc = None
            self._registered = False
            self._user32 = None

            self._register()

        def _register(self):
            try:
                self._user32 = ctypes.windll.user32
            except (OSError, AttributeError):
                logger.error("user32.dll 不可用")
                return

            if not self._hwnd:
                logger.error("窗口句柄为 None，无法注册 USB 设备通知")
                return

            guid = _GUID()
            guid.Data1 = GUID_DEVINTERFACE_USB_DEVICE[0]
            guid.Data2 = GUID_DEVINTERFACE_USB_DEVICE[1]
            guid.Data3 = GUID_DEVINTERFACE_USB_DEVICE[2]
            guid.Data4 = (ctypes.c_ubyte * 8)(*GUID_DEVINTERFACE_USB_DEVICE[3])

            dev_broadcast = _DEV_BROADCAST_DEVICEINTERFACE()
            dev_broadcast.dbcc_size = ctypes.sizeof(_DEV_BROADCAST_DEVICEINTERFACE)
            dev_broadcast.dbcc_devicetype = DBT_DEVTYP_DEVICEINTERFACE
            dev_broadcast.dbcc_classguid = guid

            self._hdevnotify = self._user32.RegisterDeviceNotificationW(
                ctypes.c_void_p(self._hwnd),
                ctypes.byref(dev_broadcast),
                DEVICE_NOTIFY_WINDOW_HANDLE,
            )

            if not self._hdevnotify:
                error = ctypes.GetLastError()
                logger.warning("RegisterDeviceNotification 失败 (error=%d)", error)
                return

            logger.info("RegisterDeviceNotification 成功 (hwnd=%s)", self._hwnd)

            WNDPROC = ctypes.WINFUNCTYPE(
                ctypes.c_long,
                ctypes.c_void_p,
                ctypes.c_uint,
                ctypes.c_void_p,
                ctypes.c_void_p,
            )

            notifier = self
            WindowsDeviceNotifier._instances[self._hwnd] = notifier

            @WNDPROC
            def new_window_proc(hwnd, msg, wparam, lparam):
                if msg == WM_DEVICECHANGE:
                    event_type = wparam
                    if event_type == DBT_DEVICEARRIVAL:
                        try:
                            device_name = WindowsDeviceNotifier._parse_device_info(lparam)
                            logger.debug("USB 设备插入: %s", device_name or "(未知)")
                            notifier._on_device_change('arrival', device_name)
                        except Exception as e:
                            logger.debug("解析设备通知失败: %s", e)
                        return 0
                    elif event_type == DBT_DEVICEREMOVECOMPLETE:
                        try:
                            device_name = WindowsDeviceNotifier._parse_device_info(lparam)
                            logger.debug("USB 设备拔出: %s", device_name or "(未知)")
                            notifier._on_device_change('removal', device_name)
                        except Exception as e:
                            logger.debug("解析设备通知失败: %s", e)
                        return 0
                    elif event_type == DBT_DEVNODES_CHANGED:
                        logger.debug("DBT_DEVNODES_CHANGED 收到")
                        notifier._on_device_change('devnodes_changed', '')
                        return 0

                return notifier._user32.CallWindowProcW(
                    notifier._old_proc,
                    ctypes.c_void_p(hwnd),
                    ctypes.c_uint(msg),
                    ctypes.c_void_p(wparam),
                    ctypes.c_void_p(lparam),
                )

            self._new_proc = new_window_proc

            old_proc = self._user32.SetWindowLongPtrW(
                ctypes.c_void_p(self._hwnd),
                GWLP_WNDPROC,
                ctypes.cast(new_window_proc, ctypes.c_void_p),
            )
            if old_proc == 0:
                error = ctypes.GetLastError()
                logger.warning("SetWindowLongPtrW 失败 (error=%d)", error)
                self._user32.UnregisterDeviceNotification(self._hdevnotify)
                self._hdevnotify = None
                del WindowsDeviceNotifier._instances[self._hwnd]
                return

            self._old_proc = old_proc
            self._registered = True
            logger.info("窗口子类化成功，USB 设备通知已注册")

        @staticmethod
        def _parse_device_info(lparam):
            try:
                hdr = _DEV_BROADCAST_HDR.from_address(lparam)
                if hdr.dbch_devicetype == DBT_DEVTYP_DEVICEINTERFACE:
                    iface = _DEV_BROADCAST_DEVICEINTERFACE.from_address(lparam)
                    return iface.dbcc_name
            except Exception:
                pass
            return ""

        def unregister(self):
            if not self._registered:
                return

            try:
                if self._old_proc and self._user32:
                    self._user32.SetWindowLongPtrW(
                        ctypes.c_void_p(self._hwnd),
                        GWLP_WNDPROC,
                        self._old_proc,
                    )
                if self._hdevnotify and self._user32:
                    self._user32.UnregisterDeviceNotification(self._hdevnotify)
                self._registered = False
                if self._hwnd in WindowsDeviceNotifier._instances:
                    del WindowsDeviceNotifier._instances[self._hwnd]
                logger.info("USB 设备通知已取消注册")
            except Exception as e:
                logger.error("取消注册设备通知失败: %s", e)

        def is_registered(self):
            return self._registered


# ==================== Linux/macOS 实现 ====================

else:
    LIBUSB_HOTPLUG_EVENT_DEVICE_ARRIVED = 0x01
    LIBUSB_HOTPLUG_EVENT_DEVICE_LEFT = 0x02
    LIBUSB_HOTPLUG_MATCH_ANY = -1

    class _LibUSBDeviceNotifier:
        """Linux/macOS USB 设备通知器

        使用 libusb 热插拔回调 API 监听 USB 设备插拔事件。
        后台线程运行 libusb 事件循环，通过队列与 tkinter 主线程通信。
        """

        def __init__(self, hwnd, on_device_change):
            """初始化设备通知器

            Args:
                hwnd: 未使用（保持与 Windows 接口一致）
                on_device_change: 回调函数，签名为 callback(event_type, device_name)
                    event_type: 'arrival' 或 'removal'
                    device_name: 设备名称（可能为空）
            """
            self._on_device_change = on_device_change
            self._registered = False
            self._running = False
            self._ctx = None
            self._hotplug_cb_handle = None
            self._event_thread = None
            self._event_queue = queue.Queue()
            self._lib = None
            self._hotplug_cb_fn = None

            self._register()

        def _find_libusb(self):
            """查找 libusb 库路径"""
            try:
                from libusb_package import find_library
                lib_path = find_library('1.0')
                if lib_path:
                    return lib_path
            except ImportError:
                pass

            import platform
            system = platform.system()
            if system == 'Linux':
                candidates = [
                    'libusb-1.0.so',
                    'libusb-1.0.so.0',
                    '/usr/lib/x86_64-linux-gnu/libusb-1.0.so.0',
                    '/usr/lib/aarch64-linux-gnu/libusb-1.0.so.0',
                    '/lib/x86_64-linux-gnu/libusb-1.0.so.0',
                    '/lib/aarch64-linux-gnu/libusb-1.0.so.0',
                ]
            elif system == 'Darwin':
                candidates = [
                    'libusb-1.0.dylib',
                    '/opt/homebrew/lib/libusb-1.0.dylib',
                    '/usr/local/lib/libusb-1.0.dylib',
                    '/opt/local/lib/libusb-1.0.dylib',
                    '/usr/lib/libusb-1.0.dylib',
                ]
            else:
                candidates = ['libusb-1.0.so']

            for candidate in candidates:
                try:
                    handle = ctypes.CDLL(candidate)
                    if hasattr(handle, 'libusb_hotplug_register_callback'):
                        return candidate
                except OSError:
                    continue

            return None

        def _register(self):
            """注册热插拔通知"""
            lib_path = self._find_libusb()
            if not lib_path:
                logger.warning("未找到 libusb 库，无法注册 USB 设备事件监听")
                return

            try:
                self._lib = ctypes.CDLL(lib_path)
            except OSError as e:
                logger.error("加载 libusb 失败: %s", e)
                return

            if not hasattr(self._lib, 'libusb_hotplug_register_callback'):
                logger.warning("libusb 版本不支持热插拔回调")
                self._lib = None
                return

            ctx = ctypes.c_void_p()
            rc = self._lib.libusb_init(ctypes.byref(ctx))
            if rc != 0:
                logger.error("libusb_init 失败: %d", rc)
                self._lib = None
                return
            self._ctx = ctx

            self._hotplug_cb_fn = ctypes.CFUNCTYPE(
                ctypes.c_int,
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_void_p,
            )(self._hotplug_callback)

            cb_handle = ctypes.c_void_p()
            rc = self._lib.libusb_hotplug_register_callback(
                self._ctx,
                LIBUSB_HOTPLUG_EVENT_DEVICE_ARRIVED | LIBUSB_HOTPLUG_EVENT_DEVICE_LEFT,
                0,
                LIBUSB_HOTPLUG_MATCH_ANY,
                LIBUSB_HOTPLUG_MATCH_ANY,
                LIBUSB_HOTPLUG_MATCH_ANY,
                self._hotplug_cb_fn,
                None,
                ctypes.byref(cb_handle),
            )

            if rc != 0:
                logger.error("libusb_hotplug_register_callback 失败: %d", rc)
                self._lib.libusb_exit(self._ctx)
                self._ctx = None
                self._lib = None
                return

            self._hotplug_cb_handle = cb_handle
            self._running = True
            self._registered = True

            self._event_thread = threading.Thread(
                target=self._event_loop, daemon=True
            )
            self._event_thread.start()

            logger.info("libusb 热插拔事件监听已注册")

        def _hotplug_callback(self, ctx, device, event, user_data):
            """libusb 热插拔回调（在事件线程中执行）"""
            try:
                if event == LIBUSB_HOTPLUG_EVENT_DEVICE_ARRIVED:
                    event_type = 'arrival'
                elif event == LIBUSB_HOTPLUG_EVENT_DEVICE_LEFT:
                    event_type = 'removal'
                else:
                    return 0

                logger.debug("libusb USB 设备%s", event_type)
                self._event_queue.put(event_type)
            except Exception as e:
                logger.debug("处理热插拔回调失败: %s", e)

            return 0

        def _event_loop(self):
            """libusb 事件循环（运行在后台线程中）"""
            timeout = ctypes.c_int(100)

            while self._running:
                completed = ctypes.c_int(0)
                rc = self._lib.libusb_handle_events_timeout_completed(
                    self._ctx,
                    ctypes.byref(timeout),
                    ctypes.byref(completed),
                )
                if rc != 0:
                    logger.debug("libusb_handle_events 返回 %d", rc)

                while True:
                    try:
                        event_type = self._event_queue.get_nowait()
                        self._on_device_change(event_type, '')
                    except queue.Empty:
                        break

        def unregister(self):
            """取消注册"""
            if not self._registered:
                return

            self._running = False

            if self._hotplug_cb_handle and self._lib:
                try:
                    self._lib.libusb_hotplug_deregister_callback(
                        self._ctx,
                        self._hotplug_cb_handle,
                    )
                except Exception as e:
                    logger.error("取消注册热插拔回调失败: %s", e)

            if self._event_thread and self._event_thread.is_alive():
                self._event_thread.join(timeout=1.0)

            if self._lib and self._ctx:
                try:
                    self._lib.libusb_exit(self._ctx)
                except Exception:
                    pass

            self._ctx = None
            self._lib = None
            self._registered = False
            logger.debug("libusb 热插拔事件监听已取消注册")

        def is_registered(self):
            return self._registered

    LibUSBDeviceNotifier = _LibUSBDeviceNotifier
