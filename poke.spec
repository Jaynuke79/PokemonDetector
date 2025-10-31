# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Pokemon Detector CLI
This creates a single-file Windows executable
"""

block_cipher = None

a = Analysis(
    ['scripts/cli/detector.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('scripts/cli/class_names.json', 'scripts/cli'),
        ('scripts/cli/gengar.png', 'scripts/cli'),
        # Note: Model file (best_model_fold1.pth) should be placed in scripts/cli/
        # Download from: https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing
        ('scripts/cli/best_model_fold1.pth', 'scripts/cli'),
    ],
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
