"""应用程序常量配置 - 包含现代 QSS 样式系统"""

# ============================================
# 颜色常量
# ============================================
BG = "#F5F7FA"
BG_HEADER = "#E9EDF2"
BG_DARK = "#E3E6EB"

PRIMARY = "#409EFF"
PRIMARY_HOVER = "#66B1FF"
PRIMARY_PRESSED = "#337ECC"
PRIMARY_LIGHT = "#ECF5FF"

ACCENT_GREEN = "#67C23A"
SUCCESS_BG = "#F0F9EB"
SUCCESS_TEXT = "#67C23A"

ACCENT_RED = "#F56C6C"
ERROR_BG = "#FEF0F0"
ERROR_TEXT = "#F56C6C"

TEXT = "#303133"
TEXT_SECONDARY = "#909399"
TEXT_DISABLED = "#C0C4CC"
TEXT_ON_PRIMARY = "#FFFFFF"

BORDER = "#DCDFE6"
BORDER_LIGHT = "#E4E7ED"

# ============================================
# 现代 QSS 样式表
# ============================================
QSS_STYLE = """
/* ============================================
   全局样式
   ============================================ */
QMainWindow {
    background-color: #F5F7FA;
}

QWidget {
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 13px;
    color: #303133;
}

/* ============================================
   按钮样式
   ============================================ */
QPushButton {
    background-color: #409EFF;
    color: #FFFFFF;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: 500;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #66B1FF;
}

QPushButton:pressed {
    background-color: #337ECC;
}

QPushButton:disabled {
    background-color: #C0C4CC;
    color: #909399;
}

QPushButton[class="secondary"] {
    background-color: #FFFFFF;
    color: #606266;
    border: 1px solid #DCDFE6;
}

QPushButton[class="secondary"]:hover {
    background-color: #F5F7FA;
    border-color: #C0C4CC;
    color: #409EFF;
}

QPushButton[class="success"] {
    background-color: #67C23A;
}

QPushButton[class="success"]:hover {
    background-color: #85CE61;
}

QPushButton[class="success"]:pressed {
    background-color: #529B2E;
}

/* ============================================
   复选框样式
   ============================================ */
QCheckBox {
    spacing: 6px;
    color: #606266;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #DCDFE6;
    border-radius: 3px;
    background-color: #FFFFFF;
}

QCheckBox::indicator:checked {
    background-color: #409EFF;
    border-color: #409EFF;
    image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M20 6L9 17l-5-5'/%3E%3C/svg%3E");
}

QCheckBox::indicator:hover {
    border-color: #409EFF;
}

/* ============================================
   树形控件样式
   ============================================ */
QTreeWidget {
    background-color: #FFFFFF;
    border: 1px solid #E4E7ED;
    border-radius: 4px;
    outline: none;
}

QTreeWidget::item {
    padding: 8px 4px;
    border-bottom: 1px solid #F2F6FC;
}

QTreeWidget::item:hover {
    background-color: #F5F7FA;
}

QTreeWidget::item:selected {
    background-color: #ECF5FF;
    color: #409EFF;
}

QTreeWidget::item:selected:!active {
    background-color: #ECF5FF;
    color: #409EFF;
}

QHeaderView::section {
    background-color: #F5F7FA;
    color: #606266;
    padding: 10px 8px;
    border: none;
    border-right: 1px solid #E4E7ED;
    border-bottom: 1px solid #E4E7ED;
    font-weight: 600;
}

QTreeWidget QHeaderView {
    background-color: #F5F7FA;
}

QTreeWidget QHeaderView::section:first {
    border-top-left-radius: 4px;
}

QTreeWidget QHeaderView::section:last {
    border-top-right-radius: 4px;
    border-right: none;
}

/* ============================================
   标签样式
   ============================================ */
QLabel {
    color: #606266;
}

QLabel[class="header"] {
    font-weight: 600;
    color: #303133;
    font-size: 14px;
}

QLabel[class="count"] {
    font-weight: 600;
    color: #409EFF;
}

/* ============================================
   分割器样式
   ============================================ */
QSplitter::handle {
    background-color: #E4E7ED;
    width: 4px;
}

QSplitter::handle:hover {
    background-color: #DCDFE6;
}

/* ============================================
   状态栏样式
   ============================================ */
QStatusBar {
    background-color: #FFFFFF;
    border-top: 1px solid #E4E7ED;
}

QStatusBar::item {
    border: none;
}

/* ============================================
   菜单栏样式
   ============================================ */
QMenuBar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E4E7ED;
}

QMenuBar::item {
    padding: 6px 12px;
}

QMenuBar::item:selected {
    background-color: #ECF5FF;
    color: #409EFF;
}

QMenu {
    background-color: #FFFFFF;
    border: 1px solid #E4E7ED;
    padding: 4px 0;
    border-radius: 4px;
}

QMenu::item {
    padding: 8px 24px;
}

QMenu::item:selected {
    background-color: #ECF5FF;
    color: #409EFF;
}
"""

# ============================================
# 其他常量
# ============================================
AUTO_REFRESH_INTERVAL = 500  # 改为 0.5 秒

APP_NAME = "USB 设备管理器"
APP_VERSION = "1.5.0"
APP_AUTHOR = "USB Manager"

STATUS_CONNECTED = "Connected"
STATUS_ERROR = "Error"
STATUS_UNKNOWN = "Unknown"
