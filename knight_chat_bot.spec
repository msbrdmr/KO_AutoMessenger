# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['knight_chat_bot.py'],
    pathex=[],
    binaries=[('C:\\\\Users\\\\musab\\\\Desktop\\\\KO\\\\KO_AutoMessenger\\\\autoit\\\\lib\\\\AutoItX3_x64.dll', 'autoit\\\\lib')],
    datas=[],
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
    name='knight_chat_bot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
