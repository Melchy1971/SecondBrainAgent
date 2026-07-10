# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Jarvis (Windows).

Builds an onedir distribution with two executables that share one analysis:
- Jarvis.exe      : windowed GUI entry (desktop/start-menu shortcut target)
- jarvis-cli.exe  : console entry for CLI commands and the post-install smoke test

The whole ``secondbrain`` package is collected because the launcher imports many
submodules dynamically; runtime resources (web HUD, prompts, dashboard, seed
config) are bundled as data.
"""

import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

ROOT = os.path.abspath(os.path.join(SPECPATH, "..", ".."))

hiddenimports = collect_submodules("secondbrain") + [
    "cryptography",
    "cryptography.hazmat.primitives.ciphers.aead",
    "cryptography.hazmat.primitives.kdf.scrypt",
]

datas = []
for rel in ("web", "prompts", "config", "migrations"):
    src = os.path.join(ROOT, rel)
    if os.path.isdir(src):
        datas.append((src, rel))
for rel in ("dashboard.html", "pyproject.toml", "README.md"):
    src = os.path.join(ROOT, rel)
    if os.path.isfile(src):
        datas.append((src, "."))
datas += collect_data_files("secondbrain", includes=["**/*.json", "**/*.html", "**/*.md", "**/*.css", "**/*.js"])

block_cipher = None

a = Analysis(
    [os.path.join(SPECPATH, "jarvis_bootstrap.py")],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinterdnd2"],  # optional; drag&drop falls back to file dialog
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

_icon = os.path.join(ROOT, "packaging", "windows", "jarvis.ico")
icon = _icon if os.path.isfile(_icon) else None

exe_gui = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name="Jarvis",
    console=False, icon=icon, disable_windowed_traceback=False,
)
exe_cli = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name="jarvis-cli",
    console=True, icon=icon,
)

coll = COLLECT(
    exe_gui, exe_cli, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=False, name="Jarvis",
)
