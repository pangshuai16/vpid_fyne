"""设备列表面板 - 显示全部 USB 设备"""
from PyQt5.QtWidgets import QVBoxLayout

from .base_tree import BaseDeviceTree
from ..device_info import USBDevice


class DeviceListPanel(BaseDeviceTree):
    """显示全部 USB 设备列表的面板"""

    def __init__(self, parent=None):
        super(DeviceListPanel, self).__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        header, self._count_label = self._create_header("全部 USB 设备")
        layout.addWidget(header)

        self._tree = self._create_tree(self.COLUMNS_FULL)
        layout.addWidget(self._tree, 1)

    def update_devices(self, devices):
        """更新设备列表显示

        Args:
            devices: 新的设备列表
        """
        self.devices = list(devices)
        self._populate_tree(self._tree, self.devices, self.COLUMNS_FULL)
        self._count_label.setText(str(len(self.devices)))
