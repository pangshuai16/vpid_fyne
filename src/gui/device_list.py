"""设备列表面板组件 - 显示全部 USB 设备"""
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
)


class DeviceListPanel(QWidget):
    """显示全部 USB 设备列表的面板"""
    device_selected = pyqtSignal(object)

    def __init__(self, parent=None):
        super(DeviceListPanel, self).__init__(parent)
        self.devices = []
        self._setup_ui()

    def _setup_ui(self):
        """初始化 UI 组件"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header_widget = QWidget()
        header_widget.setStyleSheet(f"background-color: {BG_HEADER};")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(8, 4, 8, 4)  # 减少边距

        title_label = QLabel("全部设备")
        title_font = QFont("Segoe UI", 9)  # 减小字体
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {TEXT};")
        header_layout.addWidget(title_label)

        self.count_label = QLabel("0 个")
        count_font = QFont("Segoe UI", 8)  # 减小字体
        self.count_label.setFont(count_font)
        self.count_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        header_layout.addStretch()
        header_layout.addWidget(self.count_label)

        layout.addWidget(header_widget)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["设备名称", "VID", "PID", "序列号"])
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.tree.itemSelectionChanged.connect(self._on_select)
        layout.addWidget(self.tree)

    def _on_select(self):
        """处理设备选择事件"""
        selected_items = self.tree.selectedItems()
        if selected_items and self.devices:
            index = self.tree.indexOfTopLevelItem(selected_items[0])
            if 0 <= index < len(self.devices):
                self.device_selected.emit(self.devices[index])

    def update_devices(self, devices):
        """更新设备列表显示"""
        self.devices = devices
        self._update_tree(self.devices)
        self.count_label.setText(f"{len(devices)} 个")

    def _update_tree(self, device_list):
        """更新 TreeView 内容"""
        self.tree.clear()
        for device in device_list:
            item = QTreeWidgetItem([
                device.get_display_name(),
                device.vid or "—",
                device.pid or "—",
                device.serial or "—"
            ])
            self.tree.addTopLevelItem(item)

    def get_selected_device(self):
        """获取当前选中的设备"""
        selected_items = self.tree.selectedItems()
        if selected_items and self.devices:
            index = self.tree.indexOfTopLevelItem(selected_items[0])
            if 0 <= index < len(self.devices):
                return self.devices[index]
        return None

    def clear_selection(self):
        """清除选择"""
        self.tree.clearSelection()

    def clear(self):
        """清空所有显示"""
        self.tree.clear()
        self.devices = []
        self.count_label.setText("0 个")
