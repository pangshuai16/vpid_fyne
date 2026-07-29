import sys
import os

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

# excludes：跳过项目用不到的标准库/三方库，减小打包体积、加快 PyInstaller 分析与启动期 zip 解包
# 风险提示：以下模块确认未被本项目直接 import；如后续引入新依赖请同步维护本列表
excludes = [
    'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
    'fontconfig',
    'numpy', 'scipy', 'pandas',
    'matplotlib', 'PIL', 'cv2',
    'pytest', 'pytest_asyncio',
    'setuptools', 'pip', 'wheel', 'pkg_resources',
    'lib2to3', 'pydoc_data',
    'test', 'tests',
    'email', 'html', 'http', 'xml', 'xmlrpc',
]

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

# Exclude fontconfig-related libraries to use system ones on Linux
if sys.platform.startswith('linux'):
    a.binaries = [x for x in a.binaries if not x[0].startswith('libfontconfig')]
    a.binaries = [x for x in a.binaries if not x[0].startswith('libfreetype')]
    a.binaries = [x for x in a.binaries if not x[0].startswith('libexpat')]

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
        strip=False,
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
        strip=False,
        upx=True,
        console=False,
        icon='assets/app-icon-linux.png',
    )
