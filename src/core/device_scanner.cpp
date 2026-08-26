#include "core/device_scanner.h"
#include "common/constants.h"
#include <algorithm>
#include <cctype>
#include <regex>

namespace vpid {

void Scanner::extractVidPid(const std::string& device_id, std::string& vid, std::string& pid) {
    static const std::regex vidRe(kVidPattern, std::regex::icase);
    static const std::regex pidRe(kPidPattern, std::regex::icase);
    vid.clear();
    pid.clear();
    std::smatch m;
    if (std::regex_search(device_id, m, vidRe) && m[1].matched) {
        std::string hex = m[1].str();
        std::transform(hex.begin(), hex.end(), hex.begin(),
                       [](unsigned char c) { return (char)std::toupper((int)c); });
        vid = "0x" + hex;
    }
    if (std::regex_search(device_id, m, pidRe) && m[1].matched) {
        std::string hex = m[1].str();
        std::transform(hex.begin(), hex.end(), hex.begin(),
                       [](unsigned char c) { return (char)std::toupper((int)c); });
        pid = "0x" + hex;
    }
}

std::string Scanner::extractSerialFromDeviceId(const std::string& device_id) {
    if (device_id.empty()) return std::string();
    auto pos = device_id.find('\\');
    if (pos == std::string::npos) return std::string();
    auto pos2 = device_id.find('\\', pos + 1);
    if (pos2 == std::string::npos) return std::string();
    return device_id.substr(pos2 + 1);
}

std::vector<USBDevice> scanUsbDevices() {
    auto s = createScanner();
    return s->scan();
}

} // namespace vpid