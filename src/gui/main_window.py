"""主窗口模块"""
import os
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QCheckBox, QSplitter, QStatusBar,
    QMenuBar, QAction, QMessageBox, QApplication, QStyle
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QKeySequence, QIcon
from datetime import datetime

from ..device_info import USBDevice
from ..usb_scanner import scan_usb_devices, compare_devices
from .device_list import DeviceListPanel
from .device_detail import DeviceChangePanel
from ..constants import (
    load_qss,
    AUTO_REFRESH_INTERVAL_MS,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    APP_NAME,
    APP_VERSION,
)

logger = logging.getLogger(__name__)


class ScanThread(QThread):
    """USB 设备扫描线程"""
    scan_finished = pyqtSignal(list)

    def run(self):
        try:
            devices = scan_usb_devices()
            self.scan_finished.emit(devices)
        except Exception as e:
            logger.error("扫描线程异常: %s", e)
            self.scan_finished.emit([])


class MainWindow(QMainWindow):
    """USB 设备管理器主窗口"""

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        self.devices = []
        self.baseline_devices = []
        self._scanning = False
        self._scan_thread = None

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._start_scan)

        self._apply_style()
        self._set_app_icon()
        self._setup_ui()
        self._setup_menu()
        self._setup_status_bar()
        self._start_scan()

    def _apply_style(self):
        """加载并应用 QSS 样式表"""
        qss = load_qss()
        if qss:
            self.setStyleSheet(qss)

    def _setup_ui(self):
        """初始化 UI 组件"""
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_toolbar())
        root.addWidget(self._build_splitter(), 1)

        self.device_list.device_selected.connect(self._on_device_select)
        self.device_change.device_selected.connect(self._on_change_select)

    def _build_toolbar(self):
        """构建顶部工具栏"""
        toolbar = QWidget()
        toolbar.setObjectName("toolbar")
        lay = QHBoxLayout(toolbar)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(10)

        self.device_count_label = QLabel("0 个设备已连接")
        self.device_count_label.setStyleSheet(
            "font-weight: 600; font-size: 13px; color: #303133;"
        )
        lay.addWidget(self.device_count_label)
        lay.addSpacing(6)

        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self._start_scan)
        lay.addWidget(self.refresh_btn)

        self.baseline_btn = QPushButton("设为基准")
        self.baseline_btn.setProperty("class", "success")
        self.baseline_btn.clicked.connect(self._on_set_baseline)
        lay.addWidget(self.baseline_btn)

        self.copy_btn = QPushButton("复制")
        self.copy_btn.setProperty("class", "secondary")
        self.copy_btn.clicked.connect(self._on_copy)
        lay.addWidget(self.copy_btn)

        lay.addStretch()

        self.auto_refresh_check = QCheckBox("自动刷新 (0.5s)")
        self.auto_refresh_check.stateChanged.connect(self._toggle_auto_refresh)
        lay.addWidget(self.auto_refresh_check)

        return toolbar

    def _build_splitter(self):
        """构建主内容分割器"""
        splitter = QSplitter(Qt.Horizontal)
        self.device_list = DeviceListPanel()
        self.device_change = DeviceChangePanel()
        splitter.addWidget(self.device_list)
        splitter.addWidget(self.device_change)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setHandleWidth(4)
        return splitter

    def _setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件")
        self._add_action(file_menu, "刷新设备列表", self._start_scan, "Ctrl+R")
        self._add_action(file_menu, "设为基准", self._on_set_baseline)
        file_menu.addSeparator()
        self._add_action(file_menu, "退出", self.close)

        edit_menu = menubar.addMenu("编辑")
        self._add_action(edit_menu, "复制设备信息", self._on_copy, "Ctrl+C")
        self._add_action(edit_menu, "复制 VID", lambda: self._copy_field("vid"))
        self._add_action(edit_menu, "复制 PID", lambda: self._copy_field("pid"))

        view_menu = menubar.addMenu("视图")
        auto_action = QAction("自动刷新", self)
        auto_action.setCheckable(True)
        auto_action.triggered.connect(self._toggle_auto_refresh)
        view_menu.addAction(auto_action)

        window_menu = menubar.addMenu("窗口")
        self._add_action(window_menu, "最小化", self.showMinimized)

        help_menu = menubar.addMenu("帮助")
        self._add_action(help_menu, "使用帮助", self._show_help)
        self._add_action(help_menu, "关于", self._show_about)

    @staticmethod
    def _add_action(menu, text, slot, shortcut=None):
        """向菜单添加动作的快捷方法"""
        action = QAction(text, menu)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(slot)
        menu.addAction(action)
        return action

    def _setup_status_bar(self):
        """设置状态栏"""
        self.setStatusBar(QStatusBar(self))
        self.status_label = QLabel("就绪")
        self.statusBar().addWidget(self.status_label, 1)
        self.baseline_status_label = QLabel("")
        self.statusBar().addPermanentWidget(self.baseline_status_label)

    def _set_app_icon(self):
        """设置应用程序图标"""
        try:
            base_dir = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            icon_path = os.path.join(base_dir, "assets", "usb-icon.png")
            icon = QIcon(icon_path) if os.path.exists(icon_path) else \
                self.style().standardIcon(QStyle.SP_DriveUSBIcon)
            self.setWindowIcon(icon)
            app = QApplication.instance()
            if app:
                app.setWindowIcon(icon)
        except Exception:
            pass

    # ---- 扫描管理 ----

    def _start_scan(self):
        """启动扫描（防并发）"""
        if self._scanning:
            return
        self._scanning = True
        self.refresh_btn.setEnabled(False)
        self._update_status("正在扫描 USB 设备...")

        self._scan_thread = ScanThread(self)
        self._scan_thread.scan_finished.connect(self._on_scan_data)
        self._scan_thread.finished.connect(self._on_scan_done)
        self._scan_thread.start()

    def _on_scan_data(self, devices):
        """扫描数据回调"""
        self._update_device_list(devices)

    def _on_scan_done(self):
        """扫描完成回调"""
        self._scanning = False
        self.refresh_btn.setEnabled(True)

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
        ts = datetime.now().strftime("%H:%M:%S")
        change = ""
        if added:
            change += " (+{})".format(len(added))
        if removed:
            change += " (-{})".format(len(removed))

        self.device_count_label.setText("{} 个设备已连接{}".format(count, change))
        self._update_status("最后刷新: {} | 设备数: {} → {}".format(ts, prev_count, count))

    # ---- 用户操作 ----

    def _on_set_baseline(self):
        """设置基准"""
        if not self.devices:
            QMessageBox.information(self, "提示", "当前没有设备列表，请先刷新")
            return
        self.baseline_devices = list(self.devices)
        self._update_baseline_status()
        self.device_change.update_changes([], [])
        self._update_status("已将当前设备列表设为基准")
        self.device_count_label.setText("{} 个设备已连接".format(len(self.devices)))

    def _on_copy(self):
        """复制选中设备信息"""
        device = self._get_selected_device()
        if device:
            QApplication.clipboard().setText(device.to_clipboard_text())
            self._update_status("已复制: {}".format(device.get_display_name()))
        else:
            QMessageBox.information(self, "提示", "请先选择一个设备")

    def _copy_field(self, field):
        """复制特定字段"""
        device = self._get_selected_device()
        if not device:
            return
        mapping = {"vid": device.get_formatted_vid, "pid": device.get_formatted_pid}
        value = mapping.get(field, lambda: "N/A")()
        QApplication.clipboard().setText(value)
        self._update_status("已复制 {}: {}".format(field.upper(), value))

    def _toggle_auto_refresh(self):
        """切换自动刷新"""
        if self.auto_refresh_check.isChecked():
            self.refresh_timer.start(AUTO_REFRESH_INTERVAL_MS)
        else:
            self.refresh_timer.stop()

    def _on_device_select(self, device):
        """左侧设备列表选中"""
        if device:
            self.device_change.clear_selection()
            self._update_status(self._device_info_text(device))

    def _on_change_select(self, device):
        """右侧变化列表选中"""
        if device:
            self.device_list.clear_selection()
            added_keys = {d.get_unique_key() for d in self.device_change.added_devices}
            tag = "新增" if device.get_unique_key() in added_keys else "移除"
            self._update_status("[{}] {}".format(tag, self._device_info_text(device)))

    # ---- 辅助方法 ----

    @staticmethod
    def _device_info_text(device):
        """生成设备信息文本"""
        return "{} | VID: {} | PID: {} | 序列号: {}".format(
            device.get_display_name(),
            device.get_formatted_vid(),
            device.get_formatted_pid(),
            device.serial or "N/A",
        )

    def _get_selected_device(self):
        """获取当前选中的设备"""
        return self.device_list.get_selected_device() or \
            self.device_change.get_selected_device()

    def _update_baseline_status(self):
        """更新基准状态"""
        if self.baseline_devices:
            ts = datetime.now().strftime("%H:%M:%S")
            self.baseline_status_label.setText(
                "基准: {} 个设备 ({})".format(len(self.baseline_devices), ts)
            )

    def _update_status(self, message):
        """更新状态栏"""
        self.status_label.setText(message)

    def _show_about(self):
        QMessageBox.about(self, "关于",
            "{0} v{1}\n\n用于查看和管理系统中 USB 设备的详细信息\n\n"
            "功能: 实时扫描 / VID-PID 显示 / 序列号追踪 / 自动刷新 / 基准比对\n\n"
            "(C) 2025 {0}".format(APP_NAME, APP_VERSION))

    def _show_help(self):
        QMessageBox.information(self, "使用帮助",
            "【刷新】Ctrl+R 或点击刷新按钮\n"
            "【设为基准】将当前列表设为基准，后续刷新自动比对\n"
            "【复制】选中设备后 Ctrl+C 复制完整信息\n"
            "【自动刷新】勾选后每 0.5 秒自动更新\n"
            "【设备变化】左侧=全部设备，右侧上方=新增(绿)，右侧下方=移除(红)")
