# -*- mode: python ; coding: utf-8 -*-
"""Paji build config.

EXCLUDE_ASSETS: files kept in assets/ (materials) but NOT packed into the exe.
"""

import os

EXCLUDE_ASSETS = {
    'emoji_u1f1f9_1f1fc.png',   # kept as material, excluded from the exe
}

datas = []
for root, dirs, files in os.walk('assets'):
    for f in files:
        if f in EXCLUDE_ASSETS:
            continue
        src = os.path.join(root, f)
        dst = os.path.relpath(root, '.')
        datas.append((src, dst))

a = Analysis(
    ['paji.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Paji v1.8.6-beta',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
