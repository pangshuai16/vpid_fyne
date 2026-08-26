# 跨平台兼容性方案与 CI/CD 部署指南

## 1. 概述

本项目（USB 设备管理器）是一个跨平台 USB 设备查看工具，基于 C++ 原生实现：
- **Windows**: XP 及以上所有版本（32 位 x86 全静态链接）
- **Linux**: glibc 2.28 及以上

### UI 框架选型

| 对比项 | 原生 Win32 (Windows) | GTK3 (Linux) |
|--------|---------------------|--------------|
| 第三方依赖 | ❌ 仅系统库 | ✅ gtk3 + libusb |
| XP 兼容 | ✅ NT 5.1 API 集 | - |
| 产物形态 | 单文件 exe，零 DLL | ELF 动态链接 glibc |
| 打包体积 | ~百 KB 级 | 依赖系统 GTK/libusb |

选择原生方案而非脚本/PyQt：无需运行时（Python/Qt 运行时体积大、XP 兼容差），兼容性最好、体积最小。

---

## 2. 平台兼容性方案

### 2.1 Windows 平台

#### Windows XP 支持

- 工具链：MSYS2 MINGW32（mingw-w64-i686），产出 32 位 x86 可执行文件
- 全静态链接：`-static -static-libgcc -static-libstdc++` + `-municode`（入口 `wWinMain`）
- 仅链接系统库：`setupapi`（设备枚举）、`advapi32`（注册表兜底）、`comctl32`（ListView）、`user32`、`gdi32`
- 锁定 API 集：
  ```cmake
  target_compile_definitions(... _WIN32_WINNT=0x0501 WINVER=0x0501 _WIN32_IE=0x0501)
  ```
- 图标资源 `app.ico` 含 16/24/32/48/64 多尺寸，兼容 XP

#### USB 扫描方案 (Windows)

SetupAPI 设备枚举 + 注册表兜底扫描：
- SetupAPI: `SetupDiGetClassDevs` / `SetupDiEnumDeviceInfo` / `SetupDiGetDeviceRegistryProperty`
- 注册表: `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Enum\USB`

### 2.2 Linux 平台

#### glibc 兼容性

- 使用 Rocky Linux 8 容器构建（glibc 2.28），兼容 CentOS 8、Ubuntu 20.04、Debian 11 及以上
- 可通过 `objdump -T` 验证所需的 GLIBC 版本

#### 构建依赖

```bash
dnf install -y gcc-c++ make cmake libusb1-devel gtk3-devel pkgconfig
```

#### USB 扫描方案 (Linux)

- libusb-1.0（`libusb_get_device_list` 等），系统安装 libusb 即可
- UI 使用原生 GTK3

---

## 3. 项目依赖

| 组件 | 说明 |
|------|------|
| C++17 | 语言标准 |
| CMake ≥ 3.16 | 构建系统 |
| MinGW-w64 i686 | Windows 交叉/原生工具链（MSYS2 MINGW32） |
| gtk3-devel | Linux UI（GTK3） |
| libusb1-devel | Linux USB 枚举 |

无 Python、无 PyInstaller、无第三方运行时。

---

## 4. 构建配置

### 4.1 CMake 关键配置

```cmake
if(WIN32)
  enable_language(RC)                       # Windows 图标资源
  add_executable(vpid_viewer WIN32 platform/win32/main.cpp platform/resources/app.rc ...)
  target_link_options(... -municode -static -static-libgcc -static-libstdc++)
  target_compile_definitions(... _WIN32_WINNT=0x0501 WINVER=0x0501 _WIN32_IE=0x0501)
else()
  find_package(PkgConfig REQUIRED)
  pkg_check_modules(GTK3 REQUIRED gtk+-3.0)
  pkg_check_modules(LIBUSB REQUIRED libusb-1.0)
  # GTK3 + libusb 链接
endif()
```

### 4.2 平台特定构建要点

**Windows XP**:
- MINGW32 (i686) 工具链 + 全静态链接
- NT 5.1 API 集锁定
- 产物零 DLL 依赖，可用于裸机 XP

**Linux**:
- Rocky Linux 8 容器中构建（glibc 2.28）
- 动态链接系统 GTK3 / libusb

---

## 5. GitHub Actions CI/CD 流程

### 5.1 工作流架构

```
build.yml (非 main 分支推送触发)
├── 构建 Windows x86 (MSYS2 MINGW32)
├── 构建 Linux amd64 (Rocky Linux 8)
├── 构建 Linux arm64 (Rocky Linux 8 + QEMU)
└── Upload Artifact (7天)

release.yml (main 分支推送触发)
├── build-windows-x86
├── build-linux-amd64 (Rocky Linux 8)
├── build-linux-arm64 (Rocky Linux 8 + QEMU)
├── 下载所有 artifacts (pattern: release-*, merge-multiple: true)
└── 创建 GitHub Release
```

### 5.2 release.yml 关键配置

#### 权限配置

```yaml
release:
  needs: [...]
  runs-on: ubuntu-latest
  permissions:
    contents: write  # 允许创建 Release
```

#### Artifact 下载

```yaml
- uses: actions/download-artifact@v4
  with:
    path: artifacts
    pattern: release-*
    merge-multiple: true  # 关键：合并多个 artifact
```

### 5.3 Linux 容器构建配置

```yaml
- name: Build in Rocky Linux 8 container (glibc 2.28)
  uses: addnab/docker-run-action@v3
  with:
    image: quay.io/rockylinux/rockylinux:8
    options: --platform ${{ matrix.platform }} -v ${{ github.workspace }}:/workspace -w /workspace
    run: |
      dnf install -y epel-release
      dnf install -y gcc-c++ make cmake libusb1-devel gtk3-devel pkgconfig
      rm -rf build && mkdir -p build
      cmake -B build -S . -DCMAKE_BUILD_TYPE=Release
      cmake --build build -j"$(nproc)"
      objdump -T build/vpid_viewer | grep -m1 GLIBC || true
      cp build/vpid_viewer build/vpid_viewer_linux_amd64
```

---

## 6. 本地开发环境搭建

### 6.1 Windows 开发

需要 MSYS2（MINGW32）环境：

```bash
pacman -S mingw-w64-i686-gcc mingw-w64-i686-cmake mingw-w64-i686-make
cmake -S . -B build -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release
cmake --build build -j$(nproc)
```

### 6.2 Linux 开发

```bash
sudo dnf install -y gcc-c++ make cmake libusb1-devel gtk3-devel pkgconfig
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j$(nproc)
```

注意需要 USB 访问权限，参考 README.md。

---

## 7. 兼容性检查清单

### Windows XP

- [x] MINGW32 (i686) 32 位工具链
- [x] 全静态链接（零 DLL 依赖）
- [x] `_WIN32_WINNT=0x0501` / `WINVER=0x0501` / `_WIN32_IE=0x0501`
- [x] 仅系统库（setupapi / advapi32 / comctl32 / user32 / gdi32）
- [x] 多尺寸图标（16-64px）兼容 XP

### Linux

- [x] glibc 2.28（Rocky Linux 8 构建）
- [x] libusb-1.0 扫描
- [x] amd64 和 arm64 支持

---

## 8. 常见问题

### Q: 为什么 Windows 构建是 32 位的？
A: XP 仅有 32 位系统，i686 产物同时兼容 32/64 位 Windows，且全静态链接可在 XP 裸机运行。

### Q: Linux 上提示没有权限访问 USB？
A: 参考 README.md 的「Linux 权限注意事项」章节。

### Q: 打包后的 exe 在 XP 上闪退？
A: 检查链接标志是否包含 `-static -static-libgcc -static-libstdc++` 且 API 集已锁定 0x0501；避免调用 Vista+ API。

### Q: 如何验证 glibc 兼容性？
A: 使用 `objdump -T vpid_viewer_linux_amd64 | grep GLIBC_` 查看所需的 glibc 版本，最高版本应 ≤ 2.28。