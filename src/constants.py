"""应用程序常量配置"""
import os

APP_NAME = "USB 设备管理器"
APP_VERSION = "1.5.0"
APP_AUTHOR = "USB Manager"

AUTO_REFRESH_INTERVAL_MS = 500
DEFAULT_WINDOW_WIDTH = 1280
DEFAULT_WINDOW_HEIGHT = 720
MIN_WINDOW_WIDTH = 960
MIN_WINDOW_HEIGHT = 600

STATUS_CONNECTED = "Connected"
STATUS_ERROR = "Error"
STATUS_UNKNOWN = "Unknown"

REGISTRY_USB_BASE_PATH = r"SYSTEM\CurrentControlSet\Enum\USB"

VID_PATTERN = r'VID_([0-9A-Fa-f]{4})'
PID_PATTERN = r'PID_([0-9A-Fa-f]{4})'


def load_qss():
    """加载 QSS 样式表

    Returns:
        str: QSS 样式表内容
    """
    qss_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles.qss")
    try:
        with open(qss_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""
