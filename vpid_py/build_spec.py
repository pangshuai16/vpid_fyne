import sys
import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

datas = []
hiddenimports = ['wmi', 'winreg']

if sys.platform == 'win32':
    datas += collect_data_files('wmi')

a = Analysis(
    ['main.py'],
    pathex=[os.path.dirname(os.path.abspath(__file__))],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='vpid_viewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    version=None,
    manifest=None,
    resources=[],
)
