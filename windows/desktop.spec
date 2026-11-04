# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for the Pokemon Detector desktop app prototype.

Builds dist/PokemonDetectorDesktop/ holding PokemonDetectorDesktop.exe. This is
a onedir build, so the LGPL-licensed Qt libraries stay separate, replaceable
DLLs. The installer does not package it yet.

IMPORTANT: Before building, download the model file:
https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing
Save as: models/best_model_fold1.pth
"""

from pathlib import PurePath, Path

project_root = Path(SPECPATH).parent

model_path = project_root / 'models' / 'best_model_fold1.pth'
if not model_path.exists():
    raise FileNotFoundError(f"Model file not found: {model_path}")

datas = [
    (str(project_root / 'models' / 'class_names.json'), 'models'),
    (str(model_path), 'models'),
    (str(project_root / 'windows' / 'desktop-licenses'), 'licenses'),
]

excludes = [
    'flask',
    'werkzeug',
    'jinja2',
    'gunicorn',
    'click',
    'tkinter',
    'matplotlib',
    'scipy',
    'pandas',
    'IPython',
    'notebook',
    'jupyterlab',
]

# The preview is decoded by Pillow, so Qt needs no image format plugins, and
# the window uses no SVG icons, networking or OpenGL.
KEPT_QT_PLUGINS = {
    'platforms/qwindows.dll',
    'platforms/qoffscreen.dll',
}
KEPT_QT_PLUGIN_DIRS = {'styles'}
DROPPED_QT_FILES = {'opengl32sw.dll', 'qt6network.dll', 'qt6svg.dll', 'qt6pdf.dll'}


def keep(entry):
    parts = PurePath(entry[0]).parts
    if not parts or parts[0] != 'PySide6':
        return True
    if parts[-1].lower() in DROPPED_QT_FILES or 'translations' in parts:
        return False
    if 'plugins' not in parts:
        return True
    plugin = parts[parts.index('plugins') + 1:]
    return plugin[0] in KEPT_QT_PLUGIN_DIRS or '/'.join(plugin) in KEPT_QT_PLUGINS


def without_unused_qt_files(toc):
    kept = [entry for entry in toc if keep(entry)]
    for entry in toc:
        if not keep(entry):
            print(f"desktop.spec: dropped {entry[0]}")
    return kept


a = Analysis(
    [str(project_root / 'desktop' / 'main.py')],
    pathex=[str(project_root)],
    datas=datas,
    excludes=excludes,
)
a.binaries = without_unused_qt_files(a.binaries)
a.datas = without_unused_qt_files(a.datas)
for entry in a.binaries + a.datas:
    if PurePath(entry[0]).parts[:2] == ('PySide6', 'plugins'):
        print(f"desktop.spec: kept {entry[0]}")

exe = EXE(
    PYZ(a.pure),
    a.scripts,
    [],
    exclude_binaries=True,
    name='PokemonDetectorDesktop',
    upx=False,
    console=False,
)

COLLECT(
    exe,
    a.binaries,
    a.datas,
    upx=False,
    name='PokemonDetectorDesktop',
)
