# USB VID/PID 查看器

基于 Python + Tkinter 构建的 USB 设备信息查看工具，支持 Windows XP 及以上系统。

## 功能特性

- 自动扫描系统中的 USB 设备
- 显示设备 VID/PID/序列号/设备名等信息
- 支持设备拔插实时刷新
- 支持复制设备信息到剪贴板
- 设备变化对比（新增/移除）

## 系统要求

- **运行时**: Windows XP SP3 或更高版本
- **开发时**: Python 3.5 (推荐) 或 XP 兼容的 Python 3.8 补丁版

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行程序

```bash
python main.py
```

## 打包为 exe

### 使用 PyInstaller 打包 (XP 兼容)

要创建真正在 Windows XP 上运行的可执行文件，需要：

1. **使用 Python 3.5** (最后官方支持 XP 的版本)
2. 使用 PyInstaller 3.6 或更低版本
3. 使用 32 位 Python

```bash
pip install pyinstaller==3.6
pyinstaller vpid_viewer.spec
```

### 使用 GitHub Action 自动发布

查看 [RELEASE.md](RELEASE.md) 了解如何使用 GitHub Action 自动编译和发布可执行文件。

项目已配置好 GitHub Action，会自动使用 Python 3.5 构建 XP 兼容的 exe。

## 项目结构

```
vpid_fyne/
├── .github/workflows/
│   └── build-release.yml    # GitHub Action 自动发布配置 (Python 3.5)
├── src/
│   ├── __init__.py
│   ├── usb_scanner.py      # USB 设备扫描核心模块
│   ├── device_info.py      # 设备信息数据模型
│   └── gui/
│       ├── __init__.py
│       ├── main_window.py  # 主窗口
│       ├── device_list.py  # 设备列表组件
│       └── device_detail.py# 设备详情组件
├── requirements.txt        # 依赖包
├── vpid_viewer.spec       # PyInstaller 打包配置
├── RELEASE.md             # 发布指南
├── README.md
└── main.py
```

## XP 兼容性说明

本项目专为 Windows XP 设计，确保：

- 使用 Python 3.5 (最后官方支持 XP 的版本)
- 使用纯 Python 内置模块 (`winreg`, `wmi`)
- 不依赖 Windows Vista+ 新增 API
- 使用 Tkinter 标准 GUI 框架
- 避免使用 Python 3.6+ 新增语法
- 使用旧版字符串格式化而非 f-strings
- 不使用 typing 注解
- GitHub Action 自动使用 Python 3.5 构建

## XP 兼容 Python 版本

推荐 XP 兼容的 Python 版本：

- **Python 3.5** (最后官方支持 XP 的版本，推荐)
- Python 3.8 社区补丁版 (如果必须使用 3.8)
