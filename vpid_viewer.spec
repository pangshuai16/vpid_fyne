import sys
import os

block_cipher = None

datas = [
    ('assets', 'assets'),
]
hiddenimports = [
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
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=['runtime_hook.py'],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    icon=None,
)
