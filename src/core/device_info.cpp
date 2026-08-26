#include "core/device_info.h"
#include <algorithm>
#include <cctype>

namespace vpid {

namespace {
// 去除 0x/0X 前缀并转大写
std::string strip0x(std::string s) {
    if (s.size() >= 2 && s[0] == '0' && (s[1] == 'x' || s[1] == 'X')) {
        s = s.substr(2);
    }
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return (char)std::toupper((int)c); });
    return s;
}
} // namespace

std::string USBDevice::getDisplayName() const {
    if (!name.empty()) return name;
    if (!manufacturer.empty()) return manufacturer + " Device";
    return "Unknown USB Device";
}

std::string USBDevice::getFormattedVid() const {
    return vid.empty() ? std::string("N/A") : strip0x(vid);
}
std::string USBDevice::getFormattedPid() const {
    return pid.empty() ? std::string("N/A") : strip0x(pid);
}
std::string USBDevice::getVidPidString() const {
    return getFormattedVid() + ":" + getFormattedPid();
}
DeviceKey USBDevice::getUniqueKey() const { return {vid, pid, serial}; }

std::string USBDevice::toClipboardText() const {
    auto orN = [](const std::string& v)->std::string{ return v.empty() ? std::string("N/A") : v; };
    std::string n = name.empty() ? std::string("未知设备") : name;
    return "名称: "   + n + "\n"
         + "VID: "    + getFormattedVid() + "\n"
         + "PID: "    + getFormattedPid() + "\n"
         + "序列号: "  + orN(serial) + "\n"
         + "制造商: "  + orN(manufacturer) + "\n"
         + "位置: "    + orN(location) + "\n"
         + "路径: "    + orN(path) + "\n"
         + "驱动: "    + orN(driver) + "\n"
         + "状态: "    + orN(status);
}

} // namespace vpid