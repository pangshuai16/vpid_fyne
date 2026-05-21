# USB 设备管理器 (vpid_viewer)

跨平台 USB 设备查看和管理工具，支持 Windows (XP 及以上)、Linux 和 macOS。

## 核心逻辑（必须严格遵循）

1. **程序启动**：自动扫描一次 USB 设备，并将扫描结果设为基准列表
2. **每次扫描**：扫描的 USB 设备列表直接显示在"全部USB设备"中，并与基准列表进行比对——新增的 USB 设备显示在"新增设备"，减少的 USB 设备显示在"移除设备"
3. **设为基准**：点击【设为基准】按钮时，将当前"全部USB设备"列表设定为新的基准列表（清空变更记录）

## 功能

- 跨平台 USB 设备扫描（Windows / Linux / macOS）
- 显示 VID / PID / 设备名称 / 路径
- 基准比对：新增设备（绿色）/ 移除设备（红色）
- 自动刷新（0.5 秒间隔）
- 复制设备信息到剪贴板
- Windows XP 兼容
- 多架构支持 (x86 / x64 / arm64)

## 支持平台

| 平台 | 架构 | 支持 | 说明 |
|------|------|------|------|
| **Windows** | x86 (32位) | ✅ | Windows XP 及以上 |
| **Windows** | x64 / arm64 | ✅ | Windows 10 及以上 |
| **Linux** | x64 / arm64 | ✅ | glibc 2.28 及以上 |
| **macOS** | x64 (Intel) / arm64 (Apple Silicon) | ✅ | macOS 10.15 及以上 |

## 技术栈

- **语言**: Python 3.8 (Windows XP) / Python 3.11 (其他平台)
- **UI**: tkinter / ttk（Python 内置）
- **USB 扫描**:
  - Windows: WMI + 注册表 (双通道)
  - Linux/macOS: pyusb + libusb (静态链接)
- **打包**: PyInstaller
- **CI/CD**: GitHub Actions

## 下载与安装

从 [Releases](https://github.com/pangshuai16/vpid_fyne/releases) 页面下载对应平台的可执行文件：

- **Windows**: `vpid_viewer_windows_x86.exe` (XP兼容) 或 `vpid_viewer_windows_arm64.exe`
- **Linux**: `vpid_viewer_linux_amd64` 或 `vpid_viewer_linux_arm64`
- **macOS**: `vpid_viewer_macos_amd64.app` 或 `vpid_viewer_macos_arm64.app`

## 从源码运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

## 打包

```bash
# 安装 PyInstaller
pip install pyinstaller==4.10  # Windows XP
# 或
pip install pyinstaller==6.11.0  # 其他平台

# 打包
pyinstaller vpid_viewer.spec --clean --noconfirm
```

## 项目结构

```
main.py                    # 应用入口
vpid_viewer.spec           # PyInstaller 配置
runtime_hook.py            # 运行时钩子
requirements.txt           # 项目依赖
src/
  __init__.py
  constants.py             # 常量配置
  device_info.py           # USB 设备数据模型
  usb_scanner/
    __init__.py            # 跨平台扫描器入口
    base.py                # 抽象扫描器基类
    windows.py             # Windows 扫描器
    libusb_backend.py      # Linux/macOS 扫描器
  gui/
    __init__.py
    main_window.py         # 主窗口
    device_list.py         # 全部设备列表面板
    device_detail.py       # 新增/移除设备面板
assets/
  app-icon.ico             # Windows 图标
  app-icon.icns            # macOS 图标
  app-icon-linux.png       # Linux 图标
  usb-icon.png             # USB 图标
tests/
  __init__.py
  test_device_info.py
  test_usb_scanner.py
.github/workflows/
  build.yml                # 分支构建
  release.yml              # 发布构建
```

## GitHub Actions 工作流

### build.yml
- 分支推送时触发
- 仅构建 Windows x86 和 Linux x64
- 用于快速验证

### release.yml
- main 分支推送时触发
- 构建全部 6 个平台
- 自动创建 GitHub Release 并上传所有可执行文件

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

## macOS 注意事项

首次打开 macOS 应用时可能需要在「系统设置 - 隐私与安全性」中允许运行。

## 开发指南

### 添加新平台支持

在 `src/usb_scanner/` 中实现新的扫描器类，继承自 `USBDeviceScannerBase`，然后在 `__init__.py` 中注册。

### 贡献

欢迎提交 Issue 和 PR！

## 许可证

本项目使用 MIT 许可证。
