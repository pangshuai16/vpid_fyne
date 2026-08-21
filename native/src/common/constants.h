#pragma once
#include <string>
#include <wx/colour.h>

namespace vpid {

// 与 Python 版 src/constants.py 对齐
constexpr const char* kAppName      = "USB设备ID查看";
constexpr const char* kAppVersion   = "2.0.0";
constexpr const char* kAppAuthor    = "USB Manager";

constexpr int kAutoRefreshIntervalMs = 100;
constexpr int kDefaultWindowWidth    = 1280;
constexpr int kDefaultWindowHeight   = 720;
constexpr int kMinWindowWidth        = 960;
constexpr int kMinWindowHeight       = 600;
constexpr int kScanTimeoutMs         = 10000;

constexpr const char* kStatusConnected = "Connected";
constexpr const char* kStatusError     = "Error";
constexpr const char* kStatusUnknown   = "Unknown";

// 注册表 USB 枚举路径（Windows 兜底扫描）
constexpr const char* kRegistryUsbBasePath = R"(SYSTEM\CurrentControlSet\Enum\USB)";

// VID/PID 正则模式
constexpr const char* kVidPattern = R"(VID_([0-9A-Fa-f]{4}))";
constexpr const char* kPidPattern = R"(PID_([0-9A-Fa-f]{4}))";

// 等宽字体（VID/PID 数据展示）
constexpr const char* kMonospaceFontFamily = "Consolas";

// ---------------- 颜色（对应 Python constants.py） ----------------
inline wxColour colPrimary()       { return wxColour(0x27, 0x75, 0xb6); }
inline wxColour colPrimaryHover()  { return wxColour(0x3A, 0x8F, 0xD0); }
inline wxColour colSuccess()       { return wxColour(0x1b, 0xa7, 0x84); }
inline wxColour colSuccessBg()     { return wxColour(0xE8, 0xF8, 0xF3); }
inline wxColour colDanger()        { return wxColour(0xed, 0x33, 0x21); }
inline wxColour colDangerBg()      { return wxColour(0xFE, 0xF0, 0xF0); }
inline wxColour colText()          { return wxColour(0x30, 0x31, 0x33); }
inline wxColour colTextSecondary() { return wxColour(0x90, 0x93, 0x99); }
inline wxColour colBorder()        { return wxColour(0xDC, 0xDF, 0xE6); }
inline wxColour colBg()            { return wxColour(0xF5, 0xF7, 0xFA); }
inline wxColour colWhite()         { return wxColour(0xFF, 0xFF, 0xFF); }

// 将给定颜色变亮（factor 0~1），对应 Python _lighten_color
inline wxColour lighten(const wxColour& c, double factor) {
    return wxColour(
        (unsigned char)(c.Red()   + (255 - c.Red())   * factor),
        (unsigned char)(c.Green() + (255 - c.Green()) * factor),
        (unsigned char)(c.Blue()  + (255 - c.Blue())  * factor));
}

} // namespace vpid