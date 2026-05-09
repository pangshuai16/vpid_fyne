class USBDevice(object):
    def __init__(self, vid="", pid="", serial="", name="", 
                 manufacturer="", location="", driver="", 
                 device_id="", pnp_device_id="", status=""):
        self.vid = vid
        self.pid = pid
        self.serial = serial
        self.name = name
        self.manufacturer = manufacturer
        self.location = location
        self.driver = driver
        self.device_id = device_id
        self.pnp_device_id = pnp_device_id
        self.status = status

    def get_display_name(self):
        if self.name:
            return self.name
        if self.manufacturer:
            return "{0} Device".format(self.manufacturer)
        return "Unknown USB Device"

    def get_vid_pid_string(self):
        if self.vid and self.pid:
            return "VID: {0}  PID: {1}".format(self.vid, self.pid)
        return "VID: N/A  PID: N/A"

    def to_dict(self):
        return {
            "名称": self.name or "未知设备",
            "供应商ID (VID)": self.vid or "N/A",
            "产品ID (PID)": self.pid or "N/A",
            "序列号": self.serial or "N/A",
            "制造商": self.manufacturer or "N/A",
            "位置": self.location or "N/A",
            "驱动程序": self.driver or "N/A",
            "设备ID": self.device_id or "N/A",
            "状态": self.status or "N/A",
        }

    def to_clipboard_text(self):
        lines = [
            "名称: {0}".format(self.name or 'N/A'),
            "供应商ID (VID): {0}".format(self.vid or 'N/A'),
            "产品ID (PID): {0}".format(self.pid or 'N/A'),
            "序列号: {0}".format(self.serial or 'N/A'),
            "制造商: {0}".format(self.manufacturer or 'N/A'),
            "位置: {0}".format(self.location or 'N/A'),
            "驱动程序: {0}".format(self.driver or 'N/A'),
            "状态: {0}".format(self.status or 'N/A'),
        ]
        return "\n".join(lines)
