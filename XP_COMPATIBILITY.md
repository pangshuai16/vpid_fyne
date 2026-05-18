# Windows XP 兼容性方案与 CI/CD 部署指南

## 1. 概述

本项目（USB 设备管理器）使用 Python 3.8 + tkinter/ttk 构建，目标是兼容 Windows XP 及以上所有 Windows 版本。

### 为什么选择 tkinter 而非 PyQt5

| 对比项 | tkinter | PyQt5 |
|--------|---------|-------|
| Python 内置 | ✅ 是 | ❌ 需额外安装 |
| XP 兼容 | ✅ Python 3.8 自带 Tk 8.6 原生支持 | ❌ 需要社区 Qt 5.15.17 覆盖 |
| 打包体积 | ~5-8 MB | ~30-50 MB |
| 依赖数量 | 0 | PyQt5 + Qt5 运行时 |
| 部署复杂度 | 低 | 高（需替换 DLL） |

---

## 2. Python 3.8 XP 兼容方案

### 2.1 为什么是 Python 3.8

- Python 3.8 是最后一个官方支持 Windows XP 的 Python 3.x 分支
- Python 3.9+ 已移除 XP 支持（使用 VISTA API）
- 社区维护的 Python 3.8.20 补丁版本确保持续兼容

### 2.2 安装 Python 3.8.20 (XP 兼容版)

**来源**: [adang1345/PythonVista](https://github.com/adang1345/PythonVista)

此项目提供了针对 Windows XP 兼容性补丁的 Python 3.8.20 安装包。

```powershell
# 下载安装包
$url = "https://raw.githubusercontent.com/adang1345/PythonVista/master/3.8.20/python-3.8.20-full.exe"
Invoke-WebRequest -Uri $url -OutFile python-3.8.20-full.exe

# 静默安装
Start-Process -FilePath python-3.8.20-full.exe -ArgumentList '/quiet InstallAllUsers=0 TargetDir=C:\Python38 Include_pip=1 Include_launcher=0' -Wait
```

### 2.3 tkinter XP 兼容性

Python 3.8.20 自带 Tk 8.6，在 Windows XP 上原生运行，无需额外配置。关键点：

- Tk 8.6 的 `tkinter.ttk` 主题引擎在 XP 上使用 "clam" 主题（"vista" 主题不可用）
- 代码中已做主题降级处理：优先 "vista" → 回退 "clam"
- 所有 Treeview、Button、Frame 等 ttk 组件在 XP 上正常工作

---

## 3. 项目依赖

```
# requirements.txt
wmi==1.5.1                        # Windows WMI 接口
pywin32==228; sys_platform == 'win32'  # Windows API
```

**注意**: tkinter 是 Python 标准库，无需在 requirements.txt 中声明。

### 3.1 依赖版本说明

| 包 | 版本 | 说明 |
|---|------|------|
| wmi | 1.5.1 | 最后支持 Python 3.8 的稳定版 |
| pywin32 | 228 | 兼容 Python 3.8 + XP 的最后版本 |
| tkinter | 内置 | Python 3.8 自带 Tk 8.6 |
| PyInstaller | 4.10 | 兼容 Python 3.8 + XP 的稳定版 |

---

## 4. PyInstaller 打包配置

### 4.1 spec 文件关键配置

```python
# vpid_viewer.spec
hiddenimports = [
    'wmi', 'winreg',
    'win32com', 'win32com.client', 'win32com.client.gencache',
    'pythoncom', 'pywintypes',
    'win32timezone', 'win32api', 'win32con', 'win32process',
    'tkinter', 'tkinter.ttk', 'tkinter.messagebox',
]

excludes = ['PyQt5', 'PyQt6', 'PySide2', 'PySide6']  # 排除不需要的 Qt 库

datas = [('assets', 'assets')]  # 包含图标等资源文件
```

### 4.2 打包命令

```bash
pyinstaller vpid_viewer.spec --clean --noconfirm
```

### 4.3 XP 兼容打包要点

1. **使用 PyInstaller 4.10** — 较新版本可能不兼容 Python 3.8
2. **排除 Qt 库** — 减小体积，避免 XP 兼容问题
3. **包含 tkinter** — 确保打包时包含 Tk 运行时
4. **单文件模式** — 使用 `EXE` 的 onefile 模式，方便分发

---

## 5. GitHub Actions CI/CD 流程

### 5.1 工作流架构

```
build.yml (所有分支推送触发)
├── 安装 Python 3.8.20 (XP 兼容版)
├── 安装依赖
├── 验证 tkinter 可用
├── 语法检查 + 导入验证
├── PyInstaller 打包
├── 非 main 分支 → Upload Artifact (7天)
└── main 分支 → Create GitHub Release

ci.yml (main 分支 PR 触发)
├── 同上步骤
└── Upload Artifact (7天)
```

### 5.2 关键步骤详解

#### 步骤1: 安装 Python 3.8.20

```yaml
- name: Install Python 3.8.20 (XP compatible, community patch)
  shell: powershell
  run: |
    $url = "https://raw.githubusercontent.com/adang1345/PythonVista/master/3.8.20/python-3.8.20-full.exe"
    $installer = "$env:TEMP\python-3.8.20-full.exe"
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $url -OutFile $installer -UseBasicParsing
    Start-Process -FilePath $installer -ArgumentList '/quiet InstallAllUsers=0 TargetDir=C:\Python38 Include_pip=1 Include_launcher=0' -Wait
```

**注意**: 不使用 `actions/setup-python`，因为它不支持 XP 兼容的社区补丁版本。

#### 步骤2: 验证 tkinter

```yaml
- name: Verify tkinter availability
  run: python -c "import tkinter; print('tkinter OK, Tk version:', tkinter.TkVersion)"
```

#### 步骤3: 语法和导入检查

```yaml
- name: Check Python syntax
  run: |
    python -m py_compile main.py
    python -m py_compile src/constants.py
    python -m py_compile src/device_info.py
    python -m py_compile src/usb_scanner.py
    python -m py_compile src/gui/main_window.py
    python -m py_compile src/gui/device_list.py
    python -m py_compile src/gui/device_detail.py

- name: Verify imports
  run: |
    python -c "from src.device_info import USBDevice; print('device_info OK')"
    python -c "from src.usb_scanner import scan_usb_devices, compare_devices; print('usb_scanner OK')"
    python -c "from src.gui.main_window import MainWindow; print('main_window OK')"
```

#### 步骤4: 发布策略

- **所有分支推送**: 编译并上传 Artifact（保留7天）
- **仅 main 分支**: 创建 GitHub Release 并附带可执行文件

---

## 6. 本地开发环境搭建

### 6.1 Windows 开发环境

```bash
# 1. 安装 Python 3.8.x (官方或社区版均可)
# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行应用
python main.py

# 4. 打包测试
pip install pyinstaller==4.10
pyinstaller vpid_viewer.spec --clean --noconfirm
```

### 6.2 非 Windows 环境开发

tkinter 和 usb_scanner 在非 Windows 环境下可正常导入但功能受限：
- tkinter 可正常使用（UI 预览）
- WMI/注册表扫描不可用（返回空列表）
- 建议在 Windows 环境进行完整测试

---

## 7. XP 兼容性检查清单

- [x] Python 3.8.x (最后一个支持 XP 的版本)
- [x] tkinter/ttk (Python 内置，无需额外 Qt 库)
- [x] wmi 1.5.1 (兼容 Python 3.8)
- [x] pywin32 228 (兼容 XP)
- [x] PyInstaller 4.10 (兼容 Python 3.8)
- [x] 不使用任何 Vista+ API (如 TaskDialog, Aero 等)
- [x] ttk 主题降级 (vista → clam)
- [x] 不使用 Unicode 路径 API (使用 ANSI 兼容接口)

---

## 8. 常见问题

### Q: 打包后的 exe 在 XP 上闪退？
A: 检查 PyInstaller 版本是否为 4.10，较新版本可能不兼容。

### Q: tkinter 在 XP 上样式异常？
A: XP 不支持 "vista" 主题，代码已自动降级为 "clam"。

### Q: WMI 扫描在 XP 上不工作？
A: 确保 WMI 服务已启动（`services.msc` → Windows Management Instrumentation）。

### Q: 如何验证 XP 兼容性？
A: 使用 Windows XP SP3 虚拟机测试，或使用 GitHub Actions 的构建产物。
