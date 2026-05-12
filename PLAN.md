# USB VID/PID 查看器 - Python 重构方案

## 一、项目概述

**项目名称**: USB Device Viewer (vpid_fyne → vpid_py)

**目标**: 使用 Python + Tkinter 重构 USB VID/PID 设备查看器，支持 Windows XP 及以上系统

**核心功能**:
1. 自动扫描系统中的 USB 设备
2. 显示设备 VID/PID/序列号/设备名等信息
3. 支持设备拔插实时刷新
4. 支持复制设备信息到剪贴板

---

## 二、技术栈选型

| 组件 | 选型 | 版本要求 | XP 兼容性 |
|-----|------|---------|-----------|
| **语言** | Python | 3.8.20 (社区补丁版) | ✅ XP 兼容 |
| **GUI框架** | Tkinter | Python 标准库 | ✅ 原生支持 |
| **USB读取** | WMI / winreg | 内置模块 | ✅ XP 可用 |
| **打包工具** | PyInstaller | 4.10 | ✅ |

---

## 三、项目结构

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
├── requirements.txt        # 依赖清单
├── build_spec.py           # PyInstaller 配置
└── main.py                 # 程序入口
```

---

## 四、核心模块设计

### 4.1 USB 扫描模块 (usb_scanner.py)

**数据源**:
- **WMI**: Win32_USBHub / Win32_USBDevice
- **注册表**: `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Enum\USB`

**XP 兼容性策略**:
- 优先使用 `winreg` (纯 Python，内置)
- WMI 使用 `wmi` 库 (纯 Python 封装)
- 不依赖任何 C 扩展库

### 4.2 设备信息模型 (device_info.py)

```python
@dataclass
class USBDevice:
    vid: str          # 供应商ID (e.g., "0x1234")
    pid: str          # 产品ID (e.g., "0x5678")
    serial: str       # 序列号
    name: str         # 设备名称
    manufacturer: str # 制造商
    location: str     # 连接端口
    driver: str       # 驱动名称
```

### 4.3 GUI 设计

**主窗口布局**:
```
+--------------------------------------------------+
|  [刷新按钮]  [复制]  [关于]           [_][□][X]   |
+--------------------------------------------------+
|  USB 设备列表                              | 设备详情 |
|  +-------------------------------------+ | VID:    |
|  │ 📱 USB Device 1                     | | PID:    |
|  │ VID: 0x1234 PID: 0x5678            | | Serial: |
|  ├-------------------------------------+ | Name:   |
|  │ 📱 USB Device 2                     | | Mfr:   |
|  │ VID: 0xABCD PID: 0xEF01            | | Driver: |
|  +-------------------------------------+ | Location|
+--------------------------------------------------+
|  状态: 共 5 个 USB 设备 | 最后刷新: 10:30:45     |
+--------------------------------------------------+
```

**设计要点**:
- 使用 Tkinter ttk 主题（更现代的外观）
- Treeview 显示设备列表
- 选中设备显示详细信息
- 实时拔插检测（使用定时轮询）

---

## 五、XP 兼容性保证

### 5.1 Python 运行时
- 使用社区 XP 补丁版 Python 3.8.20 (来自 PythonVista 项目)
- 参考项目: https://github.com/adang1345/PythonVista

### 5.2 第三方库限制
- **禁止使用**: NumPy, Pandas, Requests (HTTP/2+ 不支持 XP)
- **可用**: wmi (纯 Python), pywin32 (提供预编译 wheel)

### 5.3 Windows API 使用
- 避免使用 Windows Vista+ 新增 API
- 使用 WMI 和注册表查询（XP 支持）

### 5.4 打包配置
```python
# build_spec.py
a = Analysis(['main.py'],
    ...
    hiddenimports=['wmi', '_winreg'],  # 显式声明导入
    )
```

---

## 六、实现步骤

### Phase 1: 基础架构 (1-2天)
1. 初始化项目结构
2. 实现 USBDevice 数据模型
3. 实现 USB 扫描核心逻辑
4. 命令行版本测试验证

### Phase 2: GUI 开发 (2-3天)
1. 设计主窗口布局
2. 实现设备列表组件
3. 实现设备详情组件
4. 实现刷新和复制功能

### Phase 3: 高级功能 (1-2天)
1. 添加实时拔插检测
2. 设备图标和分类
3. 搜索过滤功能

### Phase 4: XP 兼容和打包 (1天)
1. 集成 XP 补丁 Python
2. PyInstaller 打包配置
3. 测试 XP 兼容性

---

## 七、关键代码示例

### USB 扫描核心逻辑

```python
import wmi
import winreg

def scan_usb_devices():
    devices = []

    # WMI 方式 (推荐)
    try:
        c = wmi.WMI()
        for usb in c.Win32_USBHub():
            device = parse_wmi_device(usb)
            devices.append(device)
    except:
        pass

    # 备用: 注册表方式
    if not devices:
        devices = scan_usb_registry()

    return devices

def parse_wmi_device(usb):
    # 提取 VID/PID 从 DeviceID
    device_id = usb.DeviceID
    vid = extract_vid_pid(device_id, 'vid')
    pid = extract_vid_pid(device_id, 'pid')
    return USBDevice(
        vid=vid,
        pid=pid,
        name=usb.Name or usb.Caption,
        serial=usb.DeviceID,
        manufacturer=usb.PNPDeviceID.split('\\')[0] if usb.PNPDeviceID else '',
    )
```

---

## 八、风险和注意事项

| 风险 | 缓解措施 |
|-----|---------|
| WMI 性能问题 | 添加缓存，定期刷新 |
| XP 上 wmi 库兼容性 | 测试 XP 环境 |
| PyInstaller 打包大小 | 使用 UPX 压缩 |
| Unicode 设备名称 | 使用 UTF-8 编码处理 |

---

## 九、验收标准

- [ ] 程序能在 Windows XP SP3 上运行
- [ ] 能正确列出所有 USB 设备
- [ ] VID/PID 显示正确
- [ ] 设备拔插后能自动刷新
- [ ] 可打包为单文件 exe
- [ ] 启动时间 < 3 秒
