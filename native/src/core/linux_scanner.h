#pragma once
#include <cstdint>
#include <string>
#include "core/device_scanner.h"

struct libusb_device; // 前置声明，避免头文件依赖 libusb

namespace vpid {

// Linux/macOS：基于 libusb-1.0，对应 Python 版 LibUSBScanner
class LinuxScanner : public Scanner {
public:
    std::vector<USBDevice> scan() override;

private:
    std::string getString(libusb_device* dev, uint8_t idx);
};

} // namespace vpid