"""主窗口模块"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QCheckBox, QSplitter, QStatusBar,
    QMenuBar, QAction, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QKeySequence
from datetime import datetime
from typing import Optional, List
from ..device_info import USBDevice
from ..usb_scanner import scan_usb_devices, compare_devices
from .device_list import DeviceListPanel
from .device_detail import DeviceChangePanel
from ..constants import (
    BG,
    BG_HEADER,
    PRIMARY,
    PRIMARY_HOVER,
    PRIMARY_PRESSED,
    TEXT,
    TEXT_SECONDARY,
    TEXT_ON_PRIMARY,
    ACCENT_GREEN,
    AUTO_REFRESH_INTERVAL,
    APP_NAME,
    APP_VERSION,
)


class ScanThread(QThread):
    """USB 设备扫描线程"""
    scan_finished = pyqtSignal(list)

    def run(self):
        try:
            devices = scan_usb_devices()
            self.scan_finished.emit(devices)
        except Exception:
            self.scan_finished.emit([])


class MainWindow(QMainWindow):
    """USB 设备管理器主窗口"""

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1180, 800)
        self.setMinimumSize(980, 680)

        self.devices = []
        self.baseline_devices = []
        self.auto_refresh = False
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._on_refresh)

        self._setup_ui()
        self._setup_menu()
        self._setup_status_bar()
        self._initial_scan()

    def _setup_ui(self):
        """初始化 UI 组件"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header_widget = QWidget()
        header_widget.setStyleSheet(f"background-color: {BG_HEADER};")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        title_row = QWidget()
        title_layout = QHBoxLayout(title_row)
        title_layout.setContentsMargins(16, 8, 16, 8)

        title_label = QLabel(APP_NAME)
        title_font = QFont("Segoe UI", 14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {TEXT};")
        title_layout.addWidget(title_label)

        self.device_count_label = QLabel("0 个设备已连接")
        count_font = QFont("Segoe UI", 9)
        self.device_count_label.setFont(count_font)
        self.device_count_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        title_layout.addWidget(self.device_count_label)
        title_layout.addStretch()
        header_layout.addWidget(title_row)

        toolbar_row = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_row)
        toolbar_layout.setContentsMargins(14, 0, 14, 8)

        self.refresh_btn = QPushButton("刷新")
        refresh_font = QFont("Segoe UI", 10)
        refresh_font.setBold(True)
        self.refresh_btn.setFont(refresh_font)
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY};
                color: {TEXT_ON_PRIMARY};
                border: none;
                padding: 6px 16px;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {PRIMARY_PRESSED};
            }}
        """)
        self.refresh_btn.clicked.connect(self._on_refresh)
        toolbar_layout.addWidget(self.refresh_btn)

        self.baseline_btn = QPushButton("设为基准")
        self.baseline_btn.setFont(refresh_font)
        self.baseline_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_GREEN};
                color: {TEXT_ON_PRIMARY};
                border: none;
                padding: 6px 16px;
            }}
        """)
        self.baseline_btn.clicked.connect(self._on_set_baseline)
        toolbar_layout.addWidget(self.baseline_btn)

        self.copy_btn = QPushButton("复制")
        self.copy_btn.setFont(refresh_font)
        self.copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG};
                color: {TEXT};
                border: 1px solid {TEXT_SECONDARY};
                padding: 6px 16px;
            }}
        """)
        self.copy_btn.clicked.connect(self._on_copy)
        toolbar_layout.addWidget(self.copy_btn)

        self.auto_refresh_check = QCheckBox("自动刷新 (3s)")
        self.auto_refresh_check.setFont(QFont("Segoe UI", 10))
        self.auto_refresh_check.setStyleSheet(f"color: {TEXT};")
        self.auto_refresh_check.stateChanged.connect(self._toggle_auto_refresh)
        toolbar_layout.addWidget(self.auto_refresh_check)
        toolbar_layout.addStretch()
        header_layout.addWidget(toolbar_row)

        layout.addWidget(header_widget)

        splitter = QSplitter(Qt.Horizontal)
        self.device_list = DeviceListPanel()
        self.device_change = DeviceChangePanel()

        splitter.addWidget(self.device_list)
        splitter.addWidget(self.device_change)
        splitter.setStretchFactor(0, 6)
        splitter.setStretchFactor(1, 4)

        layout.addWidget(splitter)

        self.device_list.device_selected.connect(self._on_device_select)
        self.device_change.device_selected.connect(self._on_change_select)

    def _setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件")
        refresh_action = QAction("刷新设备列表", self)
        refresh_action.setShortcut(QKeySequence("Ctrl+R"))
        refresh_action.triggered.connect(self._on_refresh)
        file_menu.addAction(refresh_action)

        baseline_action = QAction("设为基准", self)
        baseline_action.triggered.connect(self._on_set_baseline)
        file_menu.addAction(baseline_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        edit_menu = menubar.addMenu("编辑")
        copy_action = QAction("复制设备信息", self)
        copy_action.setShortcut(QKeySequence("Ctrl+C"))
        copy_action.triggered.connect(self._on_copy)
        edit_menu.addAction(copy_action)

        copy_vid_action = QAction("复制 VID", self)
        copy_vid_action.triggered.connect(lambda: self._copy_field("vid"))
        edit_menu.addAction(copy_vid_action)

        copy_pid_action = QAction("复制 PID", self)
        copy_pid_action.triggered.connect(lambda: self._copy_field("pid"))
        edit_menu.addAction(copy_pid_action)

        view_menu = menubar.addMenu("视图")
        auto_refresh_action = QAction("自动刷新", self)
        auto_refresh_action.setCheckable(True)
        auto_refresh_action.triggered.connect(self._toggle_auto_refresh)
        view_menu.addAction(auto_refresh_action)

        window_menu = menubar.addMenu("窗口")
        min_action = QAction("最小化", self)
        min_action.triggered.connect(self.showMinimized)
        window_menu.addAction(min_action)

        help_menu = menubar.addMenu("帮助")
        help_action = QAction("使用帮助", self)
        help_action.triggered.connect(self._show_help)
        help_menu.addAction(help_action)

        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("正在扫描 USB 设备...")
        self.status_bar.addWidget(self.status_label, 1)
        self.baseline_status_label = QLabel("")
        self.status_bar.addPermanentWidget(self.baseline_status_label)

    def _initial_scan(self):
        """初始设备扫描"""
        self._update_status("正在扫描 USB 设备...")
        self.scan_thread = ScanThread()
        self.scan_thread.scan_finished.connect(self._update_device_list)
        self.scan_thread.start()

    def _update_device_list(self, devices):
        """更新设备列表显示"""
        prev_count = len(self.devices)
        self.devices = devices

        if not self.baseline_devices:
            self.baseline_devices = list(devices)
            self._update_baseline_status()

        added, removed = compare_devices(self.baseline_devices, devices)

        self.device_list.update_devices(devices)
        self.device_change.update_changes(added, removed)

        count = len(devices)
        timestamp = datetime.now().strftime("%H:%M:%S")
        change_info = ""
        if added:
            change_info += f" (+{len(added)})"
        if removed:
            change_info += f" (-{len(removed)})"

        self.device_count_label.setText(f"{count} 个设备已连接{change_info}")
        self._update_status(f"最后刷新: {timestamp} | 设备数: {prev_count} -> {count}")

        if added or removed:
            self._show_change_notification(added, removed)

    def _on_set_baseline(self):
        """设置基准设备列表"""
        if not self.devices:
            QMessageBox.information(self, "提示", "当前没有设备列表，请先刷新")
            return
        self.baseline_devices = list(self.devices)
        self._update_baseline_status()
        self.device_list.update_devices(self.devices)
        self.device_change.update_changes([], [])
        self._update_status("已将当前设备列表设为基准")
        self.device_count_label.setText(f"{len(self.devices)} 个设备已连接")

    def _update_baseline_status(self):
        """更新基准状态显示"""
        if self.baseline_devices:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.baseline_status_label.setText(
                f"基准: {len(self.baseline_devices)} 个设备 ({timestamp})"
            )

    def _show_change_notification(self, added, removed):
        """显示设备变化通知"""
        messages = []
        if added:
            messages.append(f"新增 {len(added)} 个设备")
        if removed:
            messages.append(f"移除 {len(removed)} 个设备")

        if messages:
            notification = " | ".join(messages)
            self._update_status(notification)

    def _update_status(self, message):
        """更新状态栏文本"""
        self.status_label.setText(message)

    def _on_device_select(self, device):
        """左侧全部设备列表选择回调"""
        if device:
            self.device_change.clear_selection()
            info = f"{device.get_display_name()} | VID: {device.vid or 'N/A'} | PID: {device.pid or 'N/A'} | 序列号: {device.serial or 'N/A'}"
            self._update_status(info)

    def _on_change_select(self, device):
        """右侧变化设备列表选择回调"""
        if device:
            self.device_list.clear_selection()
            added_keys = {d.get_unique_key() for d in self.device_change.added_devices}
            change_type = "新增" if device.get_unique_key() in added_keys else "移除"
            info = f"[{change_type}] {device.get_display_name()} | VID: {device.vid or 'N/A'} | PID: {device.pid or 'N/A'} | 序列号: {device.serial or 'N/A'}"
            self._update_status(info)

    def _get_selected_device(self):
        """获取当前选中的设备（从任意列表）"""
        device = self.device_list.get_selected_device()
        if device:
            return device
        return self.device_change.get_selected_device()

    def _on_refresh(self):
        """刷新按钮点击处理"""
        self.refresh_btn.setEnabled(False)
        self._update_status("正在扫描 USB 设备...")
        self.scan_thread = ScanThread()
        self.scan_thread.scan_finished.connect(self._update_device_list)
        self.scan_thread.finished.connect(lambda: self.refresh_btn.setEnabled(True))
        self.scan_thread.start()

    def _on_copy(self):
        """复制按钮点击处理"""
        device = self._get_selected_device()
        if device:
            clipboard = QApplication.clipboard()
            clipboard.setText(device.to_clipboard_text())
            self._update_status(f"已复制到剪贴板: {device.get_display_name()}")
        else:
            QMessageBox.information(self, "提示", "请先选择一个设备")

    def _copy_field(self, field):
        """复制特定字段"""
        device = self._get_selected_device()
        if device:
            clipboard = QApplication.clipboard()
            value = getattr(device, field, "") or "N/A"
            clipboard.setText(value)
            self._update_status(f"已复制 {field}: {value}")

    def _toggle_auto_refresh(self):
        """切换自动刷新"""
        self.auto_refresh = self.auto_refresh_check.isChecked()
        if self.auto_refresh:
            self.refresh_timer.start(AUTO_REFRESH_INTERVAL)
        else:
            self.refresh_timer.stop()

    def _show_about(self):
        """显示关于对话框"""
        about_text = f"""{APP_NAME} v{APP_VERSION}

用于查看和管理系统中 USB 设备的详细信息

功能特点:
- 实时扫描 USB 设备
- 显示 VID/PID 信息
- 设备序列号追踪
- 制造商信息查看
- 自动刷新支持
- 扁平风格 UI 设计
- 新增/移除设备独立显示
- 基准比对功能

(C) 2025 {APP_NAME}"""
        QMessageBox.about(self, "关于", about_text)

    def _show_help(self):
        """显示帮助对话框"""
        help_text = """使用帮助

【刷新设备】
点击刷新按钮或按 Ctrl+R 重新扫描 USB 设备

【设为基准】
将当前设备列表设为基准，后续刷新将与基准比对

【复制信息】
选择设备后点击复制按钮，或使用快捷键 Ctrl+C

【自动刷新】
勾选"自动刷新"选项，每3秒自动更新设备列表

【设备变化】
左侧显示全部设备列表
右侧上方显示相对基准新增的设备（绿色）
右侧下方显示相对基准移除的设备（红色）

【基准比对】
比对基于基准列表，点击"设为基准"可重置基准
首次启动自动设置基准
"""
        QMessageBox.information(self, "使用帮助", help_text)
