# 跨平台兼容性方案与 CI/CD 部署指南

## 1. 概述

本项目（USB 设备管理器）是一个跨平台 USB 设备查看工具，支持：
- **Windows**: XP 及以上所有版本
- **Linux**: glibc 2.28 及以上
- **macOS**: 10.15 及以上

### UI 框架选型

| 对比项 | tkinter | PyQt5 |
|--------|---------|-------|
| Python 内置 | ✅ 是 | ❌ 需额外安装 |
| XP 兼容 | ✅ Python 3.8 自带 Tk 8.6 | ❌ 需要社区 Qt 5.15.17 覆盖 |
| 跨平台 | ✅ Windows/Linux/macOS | ✅ |
| 打包体积 | ~5-8 MB | ~30-50 MB |
| 依赖数量 | 0 | PyQt5 + Qt5 运行时 |

选择 tkinter 作为 UI 框架，因为它是 Python 标准库，无需额外依赖，完美支持所有目标平台。

---

## 2. 平台兼容性方案

### 2.1 Windows 平台

#### Windows XP 支持

- 使用 Python 3.8.x（最后一个官方支持 XP 的 Python 版本）
- 使用社区补丁版 Python 3.8.20: [R-YaTian/CPython3.8.20WinXP](https://github.com/R-YaTian/CPython3.8.20WinXP)
- PyInstaller 4.10 打包

#### Windows 现代版本 (10+)

- Python 3.11
- PyInstaller 6.11.0 打包
- 支持 x64 和 arm64

#### USB 扫描方案 (Windows)

WMI + 注册表双通道扫描：
- WMI: `Win32_USBHub` / `Win32_USBDevice`
- 注册表: `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Enum\USB`

### 2.2 Linux 平台

#### glibc 兼容性

- 使用 Rocky Linux 8 容器构建
- glibc 2.28，兼容 CentOS 8、Ubuntu 20.04、Debian 11 及以上
- 系统 Python 3.9

#### USB 扫描方案 (Linux)

- pyusb + libusb
- libusb-package 提供静态链接 libusb，用户无需安装系统 libusb

### 2.3 macOS 平台

- Python 3.11
- PyInstaller 6.11.0 打包
- 支持 x64 (Intel) 和 arm64 (Apple Silicon)

#### USB 扫描方案 (macOS)

- pyusb + libusb (与 Linux 相同)
- 使用 IOKit 后端

---

## 3. 项目依赖

```
# requirements.txt
wmi==1.5.1; sys_platform == 'win32'
pywin32==228; sys_platform == 'win32'
pyusb==1.2.1
libusb-package==1.0.26.2; sys_platform != 'win32'
```

### 依赖版本说明

| 包 | 版本 | 平台 | 说明 |
|---|------|------|------|
| wmi | 1.5.1 | Windows | 最后支持 Python 3.8 的稳定版 |
| pywin32 | 228 | Windows | 兼容 Python 3.8 + XP 的最后版本 |
| pyusb | 1.2.1 | 全部 | 跨平台 USB 库 |
| libusb-package | 1.0.26.2 | Linux/macOS | 静态链接 libusb |
| PyInstaller | 4.10 | Windows XP | 兼容 Python 3.8 |
| PyInstaller | 6.11.0 | 其他平台 | 最新稳定版 |

---

## 4. PyInstaller 打包配置

### 4.1 spec 文件关键配置

```python
# vpid_viewer.spec
hiddenimports = [
    # Windows
    'wmi', 'winreg',
    'win32com', 'win32com.client', 'win32com.client.gencache',
    'pythoncom', 'pywintypes',
    'win32timezone', 'win32api', 'win32con', 'win32process',
    # tkinter
    'tkinter', 'tkinter.ttk', 'tkinter.messagebox',
    # Linux/macOS
    'usb', 'usb.backend', 'usb.backend.libusb1', 'usb.backend.libusb0', 'usb.backend.openusb',
]

excludes = ['PyQt5', 'PyQt6', 'PySide2', 'PySide6']

datas = [('assets', 'assets')]
```

### 4.2 runtime_hook.py

用于设置 libusb 路径，确保打包后 libusb-package 能正确工作。

### 4.3 平台特定打包要点

**Windows XP**:
- 使用 PyInstaller 4.10
- Python 3.8.20 (R-YaTian 社区补丁版)
- 排除 Qt 库

**Linux**:
- 在 Rocky Linux 8 容器中构建
- 包含 libusb-package 的静态库
- 无特殊系统依赖

**macOS**:
- 标准 PyInstaller 打包
- .app bundle 格式

---

## 5. GitHub Actions CI/CD 流程

### 5.1 工作流架构

```
build.yml (非 main 分支推送触发)
├── 构建 Windows x86
├── 构建 Linux x64
└── Upload Artifact (7天)

release.yml (main 分支推送触发)
├── build-windows-x86
├── build-windows-arm64
├── build-linux-amd64 (Rocky Linux 8)
├── build-linux-arm64 (Rocky Linux 8 + QEMU)
├── build-macos-amd64
├── build-macos-arm64
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
    options: -v ${{ github.workspace }}:/workspace -w /workspace
    run: |
      dnf install -y python39 python39-pip python39-devel gcc git
      python3.9 -m pip install --upgrade pip setuptools wheel
      python3.9 -m pip install -r requirements.txt
      python3.9 -m pip install pyinstaller==6.11.0
      python3.9 -m PyInstaller vpid_viewer.spec --clean --noconfirm
      mv dist/vpid_viewer dist/vpid_viewer_linux_amd64
```

---

## 6. 本地开发环境搭建

### 6.1 全平台开发

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
python main.py

# 打包测试 (非 Windows XP)
pip install pyinstaller==6.11.0
pyinstaller vpid_viewer.spec --clean --noconfirm
```

### 6.2 Windows XP 开发测试

需在 Windows 10 或更早版本（或虚拟机）上进行：
1. 安装 R-YaTian/CPython3.8.20WinXP
2. 安装依赖: `pip install -r requirements.txt`
3. 安装 PyInstaller 4.10: `pip install pyinstaller==4.10`
4. 打包: `pyinstaller vpid_viewer.spec --clean --noconfirm`

### 6.3 Linux 开发

注意需要 USB 访问权限，参考 README.md。

---

## 7. 兼容性检查清单

### Windows XP

- [x] Python 3.8.x (R-YaTian 社区补丁版)
- [x] tkinter/ttk (Python 内置)
- [x] wmi 1.5.1
- [x] pywin32 228
- [x] PyInstaller 4.10
- [x] ttk 主题降级 (vista → clam)
- [x] 不使用 Vista+ API

### Linux

- [x] glibc 2.28 (Rocky Linux 8 构建)
- [x] pyusb + libusb (静态链接)
- [x] x64 和 arm64 支持

### macOS

- [x] Python 3.11
- [x] pyusb + libusb
- [x] x64 (Intel) 和 arm64 (Apple Silicon) 支持

---

## 8. 常见问题

### Q: 为什么 macOS artifacts 在 Release 中看不到？
A: 确保在 release.yml 的 download-artifact 步骤中设置了 `merge-multiple: true`。

### Q: Linux 上提示没有权限访问 USB？
A: 参考 README.md 的「Linux 权限注意事项」章节。

### Q: 打包后的 exe 在 XP 上闪退？
A: 检查 PyInstaller 版本是否为 4.10，较新版本可能不兼容。

### Q: 如何验证 glibc 兼容性？
A: 使用 `objdump -p vpid_viewer_linux_amd64 | grep GLIBC_` 查看所需的 glibc 版本。
