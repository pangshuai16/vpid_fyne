# USB 设备管理器 (vpid_viewer)

用于查看和管理系统中 USB 设备的详细信息，支持 Windows XP 及以上系统。

## 核心逻辑（必须严格遵循）

1. **程序启动**：自动扫描一次 USB 设备，并将扫描结果设为基准列表
2. **每次扫描**：扫描的 USB 设备列表直接显示在"全部USB设备"中，并与基准列表进行比对——新增的 USB 设备显示在"新增设备"，减少的 USB 设备显示在"移除设备"
3. **设为基准**：点击【设为基准】按钮时，将当前"全部USB设备"列表设定为新的基准列表（清空变更记录）

## 功能

- 实时扫描 USB 设备（WMI + 注册表双通道）
- 显示 VID / PID / 设备名称 / 路径
- 基准比对：新增设备（绿色）/ 移除设备（红色）
- 自动刷新（0.5 秒间隔）
- 复制设备信息到剪贴板
- Windows XP 兼容

## 技术栈

- Python 3.8（XP 兼容）
- tkinter / ttk（Python 内置 UI 库）
- WMI + Windows Registry（设备扫描）
- PyInstaller 4.10（打包）

## 运行

```bash
pip install -r requirements.txt
python main.py
```

## 打包

```bash
pip install pyinstaller==4.10
pyinstaller vpid_viewer.spec --clean --noconfirm
```

## 项目结构

```
main.py                    # 应用入口
src/
  __init__.py              # 包初始化
  constants.py             # 常量配置
  device_info.py           # USB 设备数据模型
  usb_scanner.py           # USB 设备扫描模块
  gui/
    __init__.py
    main_window.py         # 主窗口
    device_list.py         # 全部设备列表面板
    device_detail.py       # 新增/移除设备面板
assets/
  usb-icon.png             # 应用图标
```
