"""设备列表面板组件 - 显示全部 USB 设备"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal
from typing import Optional, List
from ..device_info import USBDevice


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
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 标题栏（更紧凑）
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        title_label = QLabel("全部 USB 设备")
        title_label.setProperty("class", "header")
        header_layout.addWidget(title_label)

        self.count_label = QLabel("0")
        self.count_label.setProperty("class", "count")
        header_layout.addWidget(self.count_label)
        header_layout.addStretch()

        layout.addWidget(header)

        # 树控件
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["VID", "PID", "设备名称", "路径"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.tree.setRootIsDecorated(False)
        self.tree.itemSelectionChanged.connect(self._on_select)

        # 设置列宽策略
        header_view = self.tree.header()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(2, QHeaderView.Stretch)
        header_view.setSectionResizeMode(3, QHeaderView.Stretch)

        layout.addWidget(self.tree, 1)

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
        self.count_label.setText(str(len(devices)))

    def _update_tree(self, device_list):
        """更新 TreeView 内容"""
        self.tree.clear()
        for device in device_list:
            item = QTreeWidgetItem([
                device.get_formatted_vid(),
                device.get_formatted_pid(),
                device.get_display_name(),
                device.path or "-"
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
        self.count_label.setText("0")
