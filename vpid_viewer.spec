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
splash = Splash(
    'assets/splash.png',
    binaries=a.binaries,
    datas=a.datas,
    always_on_top=True,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if sys.platform == 'darwin':
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
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
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        name='vpid_viewer',
        debug=False,
        strip=False,
        upx=True,
        console=False,
        splash=splash,
        icon='assets/app-icon.ico',
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        name='vpid_viewer',
        debug=False,
        strip=True,
        upx=True,
        console=False,
        splash=splash,
        icon='assets/app-icon-linux.png',
    )
