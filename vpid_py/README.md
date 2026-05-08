# USB VID/PID 查看器

基于 Python + Tkinter 构建的 USB 设备信息查看工具，支持 Windows XP 及以上系统。

## 功能特性

- 自动扫描系统中的 USB 设备
- 显示设备 VID/PID/序列号/设备名等信息
- 支持设备拔插实时刷新
- 支持复制设备信息到剪贴板
- 跨版本兼容设计

## 系统要求

- Windows XP SP3 或更高版本
- Python 3.5+ (建议使用 XP 兼容补丁版)

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行程序

```bash
python main.py
```

## 打包为 exe

```bash
pip install pyinstaller
pyinstaller build_spec.py --onefile
```

## 项目结构

```
vpid_py/
├── src/
│   ├── __init__.py
│   ├── usb_scanner.py      # USB 设备扫描核心模块
│   ├── device_info.py      # 设备信息数据模型
│   └── gui/
│       ├── __init__.py
│       ├── main_window.py  # 主窗口
│       ├── device_list.py  # 设备列表组件
│       └── device_detail.py# 设备详情组件
├── requirements.txt
├── build_spec.py
└── main.py
```

## XP 兼容性说明

本项目专为 Windows XP 设计，确保：

- 使用纯 Python 内置模块 (`winreg`, `wmi`)
- 不依赖 Windows Vista+ 新增 API
- 使用 Tkinter 标准 GUI 框架
- 打包为单文件 exe 便于分发
