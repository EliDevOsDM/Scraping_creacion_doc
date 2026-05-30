# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — modo onedir (exe + _internal), como el original

import sys
from pathlib import Path

block_cipher = None
root = Path(SPECPATH)

a = Analysis(
    [str(root / 'main.py')],
    pathex=[str(root)],
    binaries=[],
    datas=[],
    hiddenimports=[
        'app',
        'app.config',
        'app.automation_service',
        'app.playwright_facade',
        'pandas',
        'openpyxl',
        'openpyxl.utils.dataframe',
        'docx',
        'docx.oxml',
        'docx.oxml.ns',
        'docx.shared',
        'playwright',
        'playwright.async_api',
        'playwright._impl',
        'numpy',
        'asyncio',
        'shutil',
        'win32com',
        'win32com.client',
        'pywintypes',
        'flet',
        'flet.core',
        'flet.utils',
    ],
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
    [],
    exclude_binaries=True,
    name='sgdeaco-decreto',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='sgdeaco-decreto',
)
