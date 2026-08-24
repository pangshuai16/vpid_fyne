#pragma once
#include <memory>
#include <string>
#include <vector>
#include "core/device_info.h"

namespace vpid {

// USB 扫描器抽象基类，对应 Python 版 BaseScanner
class Scanner {
public:
    virtual ~Scanner() = default;
    virtual std::vector<USBDevice> scan() = 0;

    // 从设备 ID 提取 VID/PID："USB\VID_8087&PID_0024\.." -> vid="0x8087", pid="0x0024"
    static void extractVidPid(const std::string& device_id, std::string& vid, std::string& pid);

    // 提取反斜杠分隔的第三段作为序列号
    static std::string extractSerialFromDeviceId(const std::string& device_id);
};

// 跨平台工厂（在 windows_scanner.cpp / linux_scanner.cpp 中按平台实现）
std::unique_ptr<Scanner> createScanner();

// 统一入口
std::vector<USBDevice> scanUsbDevices();

} // namespace vpid