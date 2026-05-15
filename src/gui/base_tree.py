"""设备树形列表公共基类"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, QHeaderView
)
from PyQt5.QtCore import pyqtSignal
from typing import List, Optional

from ..device_info import USBDevice


class BaseDeviceTree(QWidget):
    """设备树形列表的公共基类，封装 QTreeWidget 的通用操作"""

    device_selected = pyqtSignal(object)

    COLUMNS_FULL = ["VID", "PID", "设备名称", "路径"]
    COLUMNS_SHORT = ["VID", "PID", "设备名称"]

    def __init__(self, parent=None):
        super(BaseDeviceTree, self).__init__(parent)
        self.devices = []
        self._tree = None
        self._count_label = None

    def _create_tree(self, columns, stretch_last_index=None):
        """创建并配置 QTreeWidget

        Args:
            columns: 列标题列表
            stretch_last_index: 需要 Stretch 模式的列索引列表，默认最后两列

        Returns:
            QTreeWidget: 配置好的树控件
        """
        tree = QTreeWidget()
        tree.setHeaderLabels(columns)
        tree.setAlternatingRowColors(True)
        tree.setSelectionMode(QTreeWidget.SingleSelection)
        tree.setRootIsDecorated(False)
        tree.itemSelectionChanged.connect(self._on_select)

        header = tree.header()
        if stretch_last_index is None:
            stretch_last_index = list(range(len(columns) - 2, len(columns)))
        for i in range(len(columns)):
            if i in stretch_last_index:
                header.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        return tree

    def _create_header(self, title, count_style=""):
        """创建面板标题行

        Args:
            title: 标题文本
            count_style: 计数标签的额外样式

        Returns:
            Tuple[QWidget, QLabel]: (标题容器, 计数标签)
        """
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setProperty("class", "header")
        layout.addWidget(title_label)

        count_label = QLabel("0")
        count_label.setProperty("class", "count")
        if count_style:
            count_label.setStyleSheet(count_style)
        layout.addStretch()
        layout.addWidget(count_label)

        return header, count_label

    def _on_select(self):
        """选择变更回调，子类可覆盖"""
        device = self._get_selected_from_tree(self._tree, self.devices)
        if device:
            self.device_selected.emit(device)

    @staticmethod
    def _get_selected_from_tree(tree, devices):
        """从 QTreeWidget 获取选中设备

        Args:
            tree: QTreeWidget 实例
            devices: 对应的设备列表

        Returns:
            Optional[USBDevice]: 选中的设备，无选中返回 None
        """
        if not tree or not devices:
            return None
        selected = tree.selectedItems()
        if not selected:
            return None
        index = tree.indexOfTopLevelItem(selected[0])
        if 0 <= index < len(devices):
            return devices[index]
        return None

    def _populate_tree(self, tree, device_list, columns):
        """填充树控件数据

        Args:
            tree: QTreeWidget 实例
            device_list: 设备列表
            columns: 列配置，决定显示哪些字段
        """
        tree.clear()
        for device in device_list:
            values = self._device_to_row(device, columns)
            tree.addTopLevelItem(QTreeWidgetItem(values))

    @staticmethod
    def _device_to_row(device, columns):
        """将设备对象转换为行数据

        Args:
            device: USBDevice 实例
            columns: 列标题列表

        Returns:
            List[str]: 行数据
        """
        row = []
        for col in columns:
            if col == "VID":
                row.append(device.get_formatted_vid())
            elif col == "PID":
                row.append(device.get_formatted_pid())
            elif col == "设备名称":
                row.append(device.get_display_name())
            elif col == "路径":
                row.append(device.path or "-")
        return row

    def get_selected_device(self):
        """获取当前选中的设备"""
        return self._get_selected_from_tree(self._tree, self.devices)

    def clear_selection(self):
        """清除选择"""
        if self._tree:
            self._tree.clearSelection()

    def clear(self):
        """清空所有显示"""
        if self._tree:
            self._tree.clear()
        self.devices = []
        if self._count_label:
            self._count_label.setText("0")
