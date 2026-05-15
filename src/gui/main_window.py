"""主窗口模块"""
import os
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QCheckBox, QSplitter, QStatusBar,
    QMenuBar, QAction, QMessageBox, QApplication, QStyle
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QKeySequence, QIcon
from datetime import datetime
from typing import Optional, List
from ..device_info import USBDevice
from ..usb_scanner import scan_usb_devices, compare_devices
from .device_list import DeviceListPanel
from .device_detail import DeviceChangePanel
from ..constants import (
    QSS_STYLE,
    AUTO_REFRESH_INTERVAL,
    APP_NAME,
    APP_VERSION
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
        self.resize(1280, 720)
        self.setMinimumSize(960, 600)

        self.devices = []
        self.baseline_devices = []
        self.auto_refresh = False
        self._scanning = False  # 防止并发扫描

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._on_refresh)

        self._apply_style()
        self._set_app_icon()

        self._setup_ui()
        self._setup_menu()
        self._setup_status_bar()
        self._initial_scan()

    def _apply_style(self):
        """应用 QSS 样式表"""
        self.setStyleSheet(QSS_STYLE)

    def _setup_ui(self):
        """初始化 UI 组件"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = QWidget()
        toolbar.setObjectName("toolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 6, 12, 6)
        toolbar_layout.setSpacing(10)

        self.device_count_label = QLabel("0 个设备已连接")
        self.device_count_label.setStyleSheet("font-weight: 600; font-size: 13px; color: #303133;")
        toolbar_layout.addWidget(self.device_count_label)
        toolbar_layout.addSpacing(6)

        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self._on_refresh)
        toolbar_layout.addWidget(self.refresh_btn)

        self.baseline_btn = QPushButton("设为基准")
        self.baseline_btn.setProperty("class", "success")
        self.baseline_btn.clicked.connect(self._on_set_baseline)
        toolbar_layout.addWidget(self.baseline_btn)

        self.copy_btn = QPushButton("复制")
        self.copy_btn.setProperty("class", "secondary")
        self.copy_btn.clicked.connect(self._on_copy)
        toolbar_layout.addWidget(self.copy_btn)

        toolbar_layout.addStretch()

        self.auto_refresh_check = QCheckBox("自动刷新 (0.5s)")
        self.auto_refresh_check.stateChanged.connect(self._toggle_auto_refresh)
        toolbar_layout.addWidget(self.auto_refresh_check)

        layout.addWidget(toolbar)

        splitter = QSplitter(Qt.Horizontal)
        self.device_list = DeviceListPanel()
        self.device_change = DeviceChangePanel()

        splitter.addWidget(self.device_list)
        splitter.addWidget(self.device_change)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setHandleWidth(4)

        layout.addWidget(splitter, 1)

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
        self.status_bar.setSizeGripEnabled(True)
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label, 1)
        self.baseline_status_label = QLabel("")
        self.status_bar.addPermanentWidget(self.baseline_status_label)

    def _set_app_icon(self):
        """设置应用程序图标"""
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            icon_path = os.path.join(base_dir, "assets", "usb-icon.png")

            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                self.setWindowIcon(icon)
                app = QApplication.instance()
                if app:
                    app.setWindowIcon(icon)
            else:
                style = self.style()
                icon = style.standardIcon(QStyle.SP_DriveUSBIcon)
                self.setWindowIcon(icon)
                app = QApplication.instance()
                if app:
                    app.setWindowIcon(icon)
        except Exception:
            pass

    def _start_scan(self):
        """启动一次扫描（安全方式：防止并发、防止信号累积）"""
        if self._scanning:
            return
        self._scanning = True
        self.refresh_btn.setEnabled(False)
        self._update_status("正在扫描 USB 设备...")

        self.scan_thread = ScanThread()
        # 只连接一次，扫描完成后自动断开
        self.scan_thread.scan_finished.connect(self._on_scan_finished)
        self.scan_thread.finished.connect(self._on_scan_thread_finished)
        self.scan_thread.start()

    def _on_scan_finished(self, devices):
        """扫描完成回调（只处理数据，不管理线程状态）"""
        self._update_device_list(devices)

    def _on_scan_thread_finished(self):
        """线程结束回调（管理线程状态）"""
        self._scanning = False
        self.refresh_btn.setEnabled(True)

    def _initial_scan(self):
        """初始设备扫描"""
        self._start_scan()

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
            change_info += " (+{})".format(len(added))
        if removed:
            change_info += " (-{})".format(len(removed))

        self.device_count_label.setText("{} 个设备已连接{}".format(count, change_info))
        self._update_status("最后刷新: {} | 设备数: {} → {}".format(timestamp, prev_count, count))

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
        self.device_count_label.setText("{} 个设备已连接".format(len(self.devices)))

    def _update_baseline_status(self):
        """更新基准状态显示"""
        if self.baseline_devices:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.baseline_status_label.setText(
                "基准: {} 个设备 ({})".format(len(self.baseline_devices), timestamp)
            )

    def _show_change_notification(self, added, removed):
        """显示设备变化通知"""
        messages = []
        if added:
            messages.append("新增 {} 个设备".format(len(added)))
        if removed:
            messages.append("移除 {} 个设备".format(len(removed)))
        if messages:
            self._update_status(" | ".join(messages))

    def _update_status(self, message):
        """更新状态栏文本"""
        self.status_label.setText(message)

    def _on_device_select(self, device):
        """左侧全部设备列表选择回调"""
        if device:
            self.device_change.clear_selection()
            info = "{} | VID: {} | PID: {} | 序列号: {}".format(
                device.get_display_name(),
                device.get_formatted_vid() or "N/A",
                device.get_formatted_pid() or "N/A",
                device.serial or "N/A"
            )
            self._update_status(info)

    def _on_change_select(self, device):
        """右侧变化设备列表选择回调"""
        if device:
            self.device_list.clear_selection()
            added_keys = {d.get_unique_key() for d in self.device_change.added_devices}
            change_type = "新增" if device.get_unique_key() in added_keys else "移除"
            info = "[{}] {} | VID: {} | PID: {} | 序列号: {}".format(
                change_type,
                device.get_display_name(),
                device.get_formatted_vid() or "N/A",
                device.get_formatted_pid() or "N/A",
                device.serial or "N/A"
            )
            self._update_status(info)

    def _get_selected_device(self):
        """获取当前选中的设备（从任意列表）"""
        device = self.device_list.get_selected_device()
        if device:
            return device
        return self.device_change.get_selected_device()

    def _on_refresh(self):
        """刷新按钮点击处理"""
        self._start_scan()

    def _on_copy(self):
        """复制按钮点击处理"""
        device = self._get_selected_device()
        if device:
            clipboard = QApplication.clipboard()
            clipboard.setText(device.to_clipboard_text())
            self._update_status("已复制到剪贴板: {}".format(device.get_display_name()))
        else:
            QMessageBox.information(self, "提示", "请先选择一个设备")

    def _copy_field(self, field):
        """复制特定字段"""
        device = self._get_selected_device()
        if device:
            clipboard = QApplication.clipboard()
            if field == "vid":
                value = device.get_formatted_vid() or "N/A"
            elif field == "pid":
                value = device.get_formatted_pid() or "N/A"
            else:
                value = getattr(device, field, "") or "N/A"
            clipboard.setText(value)
            self._update_status("已复制 {}: {}".format(field.upper(), value))

    def _toggle_auto_refresh(self):
        """切换自动刷新"""
        self.auto_refresh = self.auto_refresh_check.isChecked()
        if self.auto_refresh:
            self.refresh_timer.start(AUTO_REFRESH_INTERVAL)
        else:
            self.refresh_timer.stop()

    def _show_about(self):
        """显示关于对话框"""
        about_text = "{} v{}\n\n用于查看和管理系统中 USB 设备的详细信息\n\n功能特点:\n- 实时扫描 USB 设备\n- 显示 VID/PID 信息\n- 设备序列号追踪\n- 制造商信息查看\n- 自动刷新支持 (0.5s)\n- 现代化 UI 设计\n- 新增/移除设备独立显示\n- 基准比对功能\n\n(C) 2025 {}".format(APP_NAME, APP_VERSION, APP_NAME)
        QMessageBox.about(self, "关于", about_text)

    def _show_help(self):
        """显示帮助对话框"""
        help_text = "使用帮助\n\n【刷新设备】\n点击刷新按钮或按 Ctrl+R 重新扫描 USB 设备\n\n【设为基准】\n将当前设备列表设为基准，后续刷新将与基准比对\n\n【复制信息】\n选择设备后点击复制按钮，或使用快捷键 Ctrl+C\n\n【自动刷新】\n勾选\"自动刷新\"选项，每0.5秒自动更新设备列表\n\n【设备变化】\n左侧显示全部设备列表\n右侧上方显示相对基准新增的设备（绿色）\n右侧下方显示相对基准移除的设备（红色）\n\n【基准比对】\n比对基于基准列表，点击\"设为基准\"可重置基准\n首次启动自动设置基准"
        QMessageBox.information(self, "使用帮助", help_text)
