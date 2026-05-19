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

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=['runtime_hook.py'],
    excludes=['PyQt5', 'PyQt6', 'PySide2', 'PySide6'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
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
