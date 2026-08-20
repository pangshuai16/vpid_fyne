import sys
import os

from PyInstaller.building.splash import Splash

block_cipher = None

datas = [
    ('assets', 'assets'),
]

hiddenimports = [
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
]

if sys.platform == 'win32':
    hiddenimports.extend([
        'wmi',
        'winreg',
        'win32com',
        'win32com.client',
        'win32com.client.gencache',
        'pythoncom',
        'pywintypes',
        'win32timezone',
        'win32api',
        'win32con',
        'win32process',
    ])
else:
    hiddenimports.extend([
        'usb',
        'usb.backend.libusb1',
        'usb.backend.openusb',
        'usb.backend.libusb0',
        'libusb_package',
    ])

binaries = []

# 不排除任何依赖项，确保程序完整性
# 体积压缩通过 UPX 和 strip 实现，不以牺牲功能为代价
excludes = []

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=['runtime_hook.py'],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    # 加快启动：noarchive=False 让 onefile 在解压后保留 PYZ，加快二次冷启动
    noarchive=False,
)

# 启动加载屏：在「双击 exe 的瞬间」由引导程序展示 assets/splash.png，
# 覆盖 PyInstaller 解压与 Python/Tk 初始化这一真正耗时的阶段。
# 主窗口就绪后在 main.py 中通过 pyi_splash.close() 关闭。
def _tkinter_available():
    """Splash 需要 Tcl/Tk；构建环境缺 tkinter 时退化为不启用加载屏，避免整条构建失败"""
    try:
        import tkinter  # noqa: F401
        return True
    except Exception:
        return False


config_splash = Splash(
    'assets/splash.png',
    binaries=a.binaries,
    datas=a.datas,
    always_on_top=True,
) if _tkinter_available() else None

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# EXE 将 Splash 对象作为【位置参数】嵌入 TOC（4.10 走 Target 分支、6.11 走 Splash 分支），
# splash= 关键字参数会被忽略。仅当加载屏可用时才传入，空则完全不带 splash，
# 兼容缺失 tkinter 的构建环境。
_exe_args = [pyz]
if config_splash is not None:
    _exe_args.append(config_splash)
_exe_args += [a.scripts, a.binaries, a.zipfiles, a.datas]

if sys.platform == 'darwin':
    exe = EXE(
        *_exe_args,
        name='vpid_viewer',
        debug=False,
        strip=True,
        upx=True,
        console=False,
        icon='assets/app-icon.icns',
    )
    app = BUNDLE(
        exe,
        name='vpid_viewer.app',
        bundle_identifier='com.usbmanager.vpidviewer',
        icon='assets/app-icon.icns',
    )
elif sys.platform == 'win32':
    exe = EXE(
        *_exe_args,
        name='vpid_viewer',
        debug=False,
        strip=False,
        upx=True,
        console=False,
        icon='assets/app-icon.ico',
    )
else:
    exe = EXE(
        *_exe_args,
        name='vpid_viewer',
        debug=False,
        strip=True,
        upx=True,
        console=False,
        icon='assets/app-icon-linux.png',
    )
