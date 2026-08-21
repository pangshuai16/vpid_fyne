#pragma once
#include <string>

namespace vpid {

// 设备唯一键 (vid, pid, serial)，用于比较/去重/哈希
struct DeviceKey {
    std::string vid;
    std::string pid;
    std::string serial;

    bool operator==(const DeviceKey& o) const {
        return vid == o.vid && pid == o.pid && serial == o.serial;
    }
    bool operator!=(const DeviceKey& o) const { return !(*this == o); }
    // 供 std::set/map 使用
    bool operator<(const DeviceKey& o) const {
        if (vid != o.vid) return vid < o.vid;
        if (pid != o.pid) return pid < o.pid;
        return serial < o.serial;
    }
};

// USB 设备信息，对应 Python 版 USBDevice
class USBDevice {
public:
    std::string vid, pid, serial, name, manufacturer;
    std::string location, driver, device_id, pnp_device_id;
    std::string status, path;

    USBDevice() = default;

    // 显示名称：name -> "manufacturer Device" -> "Unknown USB Device"
    std::string getDisplayName() const;

    // 去前缀大写 hex（如 "0x8087" -> "8087"）
    std::string getFormattedVid() const;
    std::string getFormattedPid() const;

    // "VID:PID"
    std::string getVidPidString() const;

    // 唯一键
    DeviceKey getUniqueKey() const;

    // 剪贴板多行文本
    std::string toClipboardText() const;
};

} // namespace vpid