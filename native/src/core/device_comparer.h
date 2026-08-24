#pragma once
#include <vector>
#include "core/device_info.h"

namespace vpid {

// 设备比对工具，对应 Python 版 compare_devices
class DeviceComparer {
public:
    // 输出 (added, removed)
    static void compare(const std::vector<USBDevice>& oldDev, const std::vector<USBDevice>& newDev,
                        std::vector<USBDevice>& added, std::vector<USBDevice>& removed);

    // 唯一键集合是否不一致
    static bool hasChanged(const std::vector<USBDevice>& a, const std::vector<USBDevice>& b);
};

} // namespace vpid