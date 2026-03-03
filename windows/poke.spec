# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Pokemon Detector CLI
This creates a single-file Windows executable

IMPORTANT: Before building, download the model file:
https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing
Save as: models/best_model_fold1.pth
"""

import os
from pathlib import Path

block_cipher = None

# Check if model file exists before building
model_path = Path('../models/best_model_fold1.pth')
if not model_path.exists():
    print("\n" + "="*70)
    print("ERROR: Model file not found!")
    print(f"Expected location: {model_path.absolute()}")
    print("\nPlease download from:")
    print("https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing")
    print("="*70 + "\n")
    raise FileNotFoundError(f"Model file not found: {model_path}")

# Build data files list
datas = [
    ('../models/class_names.json', 'models'),
    ('../gengar.png', '.'),
    ('../models/best_model_fold1.pth', 'models'),
]

a = Analysis(
    ['../cli/main.py'],
    pathex=['..'],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'click',
        'torch',
        'torchvision',
        'timm',
        'numpy',
        'PIL',
        'PIL.Image',
        'PIL._imaging',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'IPython',
        'notebook',
        'jupyterlab',
    ],
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
    name='poke',
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
    icon=None,  # Add icon='icon.ico' if you have an icon file
)
