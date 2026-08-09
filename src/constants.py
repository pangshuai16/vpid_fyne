"""应用程序常量配置"""
import os
import sys

APP_NAME = "USB设备ID查看"
APP_VERSION = "2.0.0"
APP_AUTHOR = "USB Manager"

AUTO_REFRESH_INTERVAL_MS = 100
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

COLOR_PRIMARY = "#2775b6"
COLOR_PRIMARY_HOVER = "#3A8FD0"
COLOR_SUCCESS = "#1ba784"
COLOR_SUCCESS_BG = "#E8F8F3"
COLOR_DANGER = "#ed3321"
COLOR_DANGER_BG = "#FEF0F0"
COLOR_TEXT = "#303133"
COLOR_TEXT_SECONDARY = "#909399"
COLOR_BORDER = "#DCDFE6"
COLOR_BG = "#F5F7FA"
COLOR_WHITE = "#FFFFFF"

# 跨平台字体族：等宽字体，用于 VID/PID 等数据展示
# 按优先级列出各平台最佳等宽字体，tkinter 会自动 fallback 到可用字体
if sys.platform == "darwin":
    MONOSPACE_FONT_FAMILY = "Menlo"
elif sys.platform == "win32":
    MONOSPACE_FONT_FAMILY = "Consolas"
else:
    MONOSPACE_FONT_FAMILY = "DejaVu Sans Mono"

# 跨平台 UI 字体族
if sys.platform == "darwin":
    UI_FONT_FAMILY = ".AppleSystemUIFont"
elif sys.platform == "win32":
    UI_FONT_FAMILY = "Segoe UI"
else:
    UI_FONT_FAMILY = "sans-serif"
