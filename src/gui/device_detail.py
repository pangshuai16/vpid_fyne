"""设备变化面板组件 - 显示新增和移除的设备"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from typing import Optional, List
from ..device_info import USBDevice
from ..constants import (
    BG,
    BG_HEADER,
    TEXT,
    TEXT_SECONDARY,
    BORDER,
    SUCCESS_BG,
    SUCCESS_TEXT,
    ERROR_BG,
    ERROR_TEXT,
)


class DeviceChangePanel(QWidget):
    """显示新增和移除 USB 设备的面板"""
    device_selected = pyqtSignal(object)

    def __init__(self, parent=None):
        super(DeviceChangePanel, self).__init__(parent)
        self.added_devices = []
        self.removed_devices = []
        self._setup_ui()

    def _setup_ui(self):
        """初始化 UI 组件"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        added_widget = QWidget()
        added_layout = QVBoxLayout(added_widget)
        added_layout.setContentsMargins(0, 0, 0, 4)

        added_header = QWidget()
        added_header.setStyleSheet(f"background-color: {SUCCESS_BG};")
        added_header_layout = QHBoxLayout(added_header)
        added_header_layout.setContentsMargins(16, 10, 16, 10)

        added_title = QLabel("+ 新增设备")
        added_title_font = QFont("Segoe UI", 10)
        added_title_font.setBold(True)
        added_title.setFont(added_title_font)
        added_title.setStyleSheet(f"color: {SUCCESS_TEXT};")
        added_header_layout.addWidget(added_title)

        self.added_count_label = QLabel("0 个")
        count_font = QFont("Segoe UI", 9)
        self.added_count_label.setFont(count_font)
        self.added_count_label.setStyleSheet(f"color: {SUCCESS_TEXT};")
        added_header_layout.addStretch()
        added_header_layout.addWidget(self.added_count_label)
        added_layout.addWidget(added_header)

        self.added_tree = QTreeWidget()
        self.added_tree.setHeaderLabels(["设备名称", "VID", "PID"])
        added_header_view = self.added_tree.header()
        added_header_view.setSectionResizeMode(0, QHeaderView.Stretch)
        added_header_view.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        added_header_view.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.added_tree.setRootIsDecorated(False)
        self.added_tree.setAlternatingRowColors(True)
        self.added_tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.added_tree.itemSelectionChanged.connect(lambda: self._on_select(self.added_tree, self.added_devices))
        added_layout.addWidget(self.added_tree)
        layout.addWidget(added_widget)

        separator = QWidget()
        separator.setStyleSheet(f"background-color: {BORDER}; min-height: 1px; max-height: 1px;")
        layout.addWidget(separator)

        removed_widget = QWidget()
        removed_layout = QVBoxLayout(removed_widget)
        removed_layout.setContentsMargins(0, 4, 0, 0)

        removed_header = QWidget()
        removed_header.setStyleSheet(f"background-color: {ERROR_BG};")
        removed_header_layout = QHBoxLayout(removed_header)
        removed_header_layout.setContentsMargins(16, 10, 16, 10)

        removed_title = QLabel("- 移除设备")
        removed_title_font = QFont("Segoe UI", 10)
        removed_title_font.setBold(True)
        removed_title.setFont(removed_title_font)
        removed_title.setStyleSheet(f"color: {ERROR_TEXT};")
        removed_header_layout.addWidget(removed_title)

        self.removed_count_label = QLabel("0 个")
        self.removed_count_label.setFont(count_font)
        self.removed_count_label.setStyleSheet(f"color: {ERROR_TEXT};")
        removed_header_layout.addStretch()
        removed_header_layout.addWidget(self.removed_count_label)
        removed_layout.addWidget(removed_header)

        self.removed_tree = QTreeWidget()
        self.removed_tree.setHeaderLabels(["设备名称", "VID", "PID"])
        removed_header_view = self.removed_tree.header()
        removed_header_view.setSectionResizeMode(0, QHeaderView.Stretch)
        removed_header_view.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        removed_header_view.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.removed_tree.setRootIsDecorated(False)
        self.removed_tree.setAlternatingRowColors(True)
        self.removed_tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.removed_tree.itemSelectionChanged.connect(lambda: self._on_select(self.removed_tree, self.removed_devices))
        removed_layout.addWidget(self.removed_tree)
        layout.addWidget(removed_widget)

    def _on_select(self, tree, devices):
        """处理设备选择事件"""
        selected_items = tree.selectedItems()
        if selected_items and devices:
            index = tree.indexOfTopLevelItem(selected_items[0])
            if 0 <= index < len(devices):
                self.device_selected.emit(devices[index])

    def update_changes(self, added_devices, removed_devices):
        """更新新增和移除设备列表"""
        self.added_devices = added_devices
        self.removed_devices = removed_devices

        self._update_tree(self.added_tree, self.added_devices)
        self.added_count_label.setText(f"{len(self.added_devices)} 个")

        self._update_tree(self.removed_tree, self.removed_devices)
        self.removed_count_label.setText(f"{len(self.removed_devices)} 个")

    def _update_tree(self, tree, device_list):
        """更新 TreeView 内容"""
        tree.clear()
        for device in device_list:
            item = QTreeWidgetItem([
                device.get_display_name(),
                device.vid or "—",
                device.pid or "—"
            ])
            tree.addTopLevelItem(item)

    def get_selected_device(self):
        """获取当前选中的设备"""
        for tree, devices in [(self.added_tree, self.added_devices),
                              (self.removed_tree, self.removed_devices)]:
            selected_items = tree.selectedItems()
            if selected_items and devices:
                index = tree.indexOfTopLevelItem(selected_items[0])
                if 0 <= index < len(devices):
                    return devices[index]
        return None

    def clear_selection(self):
        """清除所有选择"""
        self.added_tree.clearSelection()
        self.removed_tree.clearSelection()

    def clear(self):
        """清空所有显示"""
        self.added_tree.clear()
        self.removed_tree.clear()
        self.added_devices = []
        self.removed_devices = []
        self.added_count_label.setText("0 个")
        self.removed_count_label.setText("0 个")
