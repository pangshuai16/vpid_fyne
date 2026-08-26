# USB 设备管理器 (vpid_viewer)

跨平台 USB 设备查看和管理工具，基于 **C++ 原生实现**（无脚本语言运行时、无第三方 UI 框架），支持 Windows (XP 及以上) 和 Linux。

## 核心逻辑（必须严格遵循）

1. **程序启动**：自动扫描一次 USB 设备，并将扫描结果设为基准列表
2. **每次扫描**：扫描的 USB 设备列表直接显示在"全部USB设备"中，并与基准列表进行比对——新增的 USB 设备显示在"新增设备"，减少的 USB 设备显示在"移除设备"
3. **设为基准**：点击【重置】按钮时，将当前"全部USB设备"列表设定为新的基准列表（清空变更记录）

## 功能

- 原生 USB 设备扫描（Windows SetupAPI + 注册表兜底 / Linux libusb）
- 显示 VID / PID / 设备名称 / 路径
- 基准比对：新增设备（绿色）/ 移除设备（红色）
- 自动刷新（100 ms 间隔）
- 复制设备信息到剪贴板
- Windows XP 兼容（32 位静态链接，零 DLL 依赖）
- Linux 多架构支持（x64 / arm64）

## 支持平台

| 平台 | 架构 | 支持 | 说明 |
|------|------|------|------|
| **Windows** | x86 (32位) | ✅ | Windows XP 及以上，全静态链接 |
| **Linux** | x64 / arm64 | ✅ | glibc 2.28 及以上（Rocky Linux 8 构建） |

## 技术栈

- **语言**: C++17
- **构建**: CMake (≥3.16)
- **Windows UI**: 原生 Win32 API + Common Controls（ListView），MinGW-w64 (i686) 静态链接
- **Linux UI**: 原生 GTK3
- **USB 扫描**:
  - Windows: SetupAPI（设备枚举）+ 注册表兜底
  - Linux: libusb-1.0
- **CI/CD**: GitHub Actions（Windows 2022 + MSYS2 MINGW32 / Rocky Linux 8 容器）

## 下载与安装

从 [Releases](https://github.com/pangshuai16/vpid_fyne/releases) 页面下载对应平台的可执行文件：

- **Windows**: `vpid_viewer_windows_x86.exe`（XP 兼容，单文件免安装）
- **Linux**: `vpid_viewer_linux_amd64` 或 `vpid_viewer_linux_arm64`

## 从源码构建

```bash
# Windows (MinGW-w64 i686 / MSYS2 MINGW32)
cmake -S . -B build -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release
cmake --build build -j$(nproc)

# Linux (需 gcc-c++ cmake gtk3-devel libusb1-devel pkgconfig)
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j$(nproc)
```

产物输出到 `build/vpid_viewer.exe` (Windows) 或 `build/vpid_viewer` (Linux)。

## 项目结构

```
CMakeLists.txt                # 顶层构建（core + 平台 UI 由 CMake 按平台分支选择）
src/
  common/
    constants.h               # 常量配置（含自动刷新间隔）
  core/                       # 跨平台复用的设备模型 / 扫描抽象 / 比对逻辑
    device_info.h/.cpp        # USB 设备数据模型
    device_scanner.h/.cpp     # 扫描器抽象接口
    device_comparer.h/.cpp    # 基准比对（新增/移除）
    linux_scanner.h/.cpp      # Linux 扫描器（libusb）
    windows_scanner.h/.cpp    # Windows 扫描器（SetupAPI + 注册表）
platform/
  win32/main.cpp              # Windows 原生 UI（Win32 + Common Controls）
  gtk/main.cpp                # Linux 原生 UI（GTK3）
  resources/
    app.rc / app.ico          # Windows 图标资源（16-64px，兼容 XP）
    app_icon.h                # Linux 内嵌 128x128 PNG 图标
assets/                       # 仓库文档 / 发布用图标
.github/workflows/
  build.yml                   # 分支构建（Windows x86 + Linux amd64/arm64）
  release.yml                 # main 分支发布构建 + GitHub Release
```

## GitHub Actions 工作流

- **build.yml**：非 main 分支推送时构建验证（Windows x86 + Linux amd64/arm64）
- **release.yml**：main 分支推送时构建全部平台并自动创建 GitHub Release

自动发布的详细操作见 [RELEASE.md](RELEASE.md)，跨平台兼容性方案与 CI/CD 配置见 [XP_COMPATIBILITY.md](XP_COMPATIBILITY.md)。

## Linux 权限注意事项

在 Linux 上运行可能需要 USB 访问权限：

```bash
# 临时方案 (每次重启后需要)
sudo chmod 666 /dev/bus/usb/*/*

# 永久方案 (需要重启)
sudo usermod -aG plugdev $USER
# 或创建 udev 规则
echo 'SUBSYSTEM=="usb", MODE="0666", GROUP="plugdev"' | sudo tee /etc/udev/rules.d/99-usb.rules
sudo udevadm control --reload-rules
```

## 开发指南

### 添加新平台支持

1. 在 `src/core/` 中实现新的扫描器类，继承 `Scanner` 抽象接口
2. 在 `platform/` 下新增对应平台的 UI 入口（参考 `win32/main.cpp` 或 `gtk/main.cpp`）
3. 在 `CMakeLists.txt` 中按平台分支添加目标与链接库

### 贡献

欢迎提交 Issue 和 PR！

## 许可证

本项目使用 MIT 许可证。