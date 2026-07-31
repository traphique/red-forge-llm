# -*- mode: python ; coding: utf-8 -*-
"""Cross-platform PyInstaller build for the RedForge desktop app."""

import sys
from pathlib import Path

project_root = Path(SPECPATH).parent

a = Analysis(
    [str(project_root / "redforge_app" / "__main__.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(project_root / "skills"), "skills"),
        (str(project_root / "MASTER_INDEX.md"), "."),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["numpy", "sklearn", "streamlit"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RedForge",
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
)
collection = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="RedForge",
)

if sys.platform == "darwin":
    app = BUNDLE(
        collection,
        name="RedForge.app",
        icon=None,
        bundle_identifier="io.redforge.desktop",
    )

