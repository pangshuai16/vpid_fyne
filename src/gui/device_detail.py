"""设备变化面板 - 显示新增和移除的设备"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import pyqtSignal

from .base_tree import BaseDeviceTree
from ..device_info import USBDevice


class _ChangeSection(BaseDeviceTree):
    """单个变化区域（新增或移除），内部使用"""

    def __init__(self, title, header_bg, text_color, parent=None):
        super(_ChangeSection, self).__init__(parent)
        self._title = title
        self._header_bg = header_bg
        self._text_color = text_color
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        header_widget = QWidget()
        header_widget.setStyleSheet(
            "background-color: {0}; border-radius: 4px;".format(self._header_bg)
        )
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(8, 4, 8, 4)

        title_label = QLabel(self._title)
        title_label.setStyleSheet(
            "font-weight: 600; color: {0};".format(self._text_color)
        )
        header_layout.addWidget(title_label)

        self._count_label = QLabel("0")
        self._count_label.setStyleSheet(
            "font-weight: 600; color: {0};".format(self._text_color)
        )
        header_layout.addStretch()
        header_layout.addWidget(self._count_label)
        layout.addWidget(header_widget)

        self._tree = self._create_tree(self.COLUMNS_SHORT, stretch_last_index=[2])
        layout.addWidget(self._tree, 1)

    def update_devices(self, devices):
        self.devices = list(devices)
        self._populate_tree(self._tree, self.devices, self.COLUMNS_SHORT)
        self._count_label.setText(str(len(self.devices)))


class DeviceChangePanel(QWidget):
    """显示新增和移除 USB 设备的面板"""

    device_selected = pyqtSignal(object)

    def __init__(self, parent=None):
        super(DeviceChangePanel, self).__init__(parent)
        self.added_section = None
        self.removed_section = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        self.added_section = _ChangeSection(
            "+ 新增设备", "#F0F9EB", "#67C23A", self
        )
        self.added_section.device_selected.connect(self._forward_selected)
        layout.addWidget(self.added_section, 1)

        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #E4E7ED;")
        layout.addWidget(separator)

        self.removed_section = _ChangeSection(
            "- 移除设备", "#FEF0F0", "#F56C6C", self
        )
        self.removed_section.device_selected.connect(self._forward_selected)
        layout.addWidget(self.removed_section, 1)

    def _forward_selected(self, device):
        """转发子面板的选中信号"""
        self.device_selected.emit(device)

    @property
    def added_devices(self):
        return self.added_section.devices

    @property
    def removed_devices(self):
        return self.removed_section.devices

    def update_changes(self, added_devices, removed_devices):
        """更新新增和移除设备列表"""
        self.added_section.update_devices(added_devices)
        self.removed_section.update_devices(removed_devices)

    def get_selected_device(self):
        """获取当前选中的设备"""
        device = self.added_section.get_selected_device()
        if device:
            return device
        return self.removed_section.get_selected_device()

    def clear_selection(self):
        self.added_section.clear_selection()
        self.removed_section.clear_selection()

    def clear(self):
        self.added_section.clear()
        self.removed_section.clear()
