# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Pokemon Detector on Windows.

Builds dist/PokemonDetector/ holding poke.exe (CLI) and PokemonDetector.exe
(web app launcher), which share one _internal/ folder. The installer script
windows/installer.iss packages that folder.

IMPORTANT: Before building, download the model file:
https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing
Save as: models/best_model_fold1.pth
"""

from pathlib import Path

from PyInstaller.utils.hooks import copy_metadata

project_root = Path(SPECPATH).parent

model_path = project_root / 'models' / 'best_model_fold1.pth'
if not model_path.exists():
    print("\n" + "="*70)
    print("ERROR: Model file not found!")
    print(f"Expected location: {model_path}")
    print("\nPlease download from:")
    print("https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing")
    print("="*70 + "\n")
    raise FileNotFoundError(f"Model file not found: {model_path}")

model_datas = [
    (str(project_root / 'models' / 'class_names.json'), 'models'),
    (str(model_path), 'models'),
]

# Werkzeug's server looks up its own version from package metadata at startup.
webapp_datas = [
    (str(project_root / 'webapp' / 'templates'), 'webapp/templates'),
    *copy_metadata('werkzeug'),
]

excludes = [
    'matplotlib',
    'scipy',
    'pandas',
    'IPython',
    'notebook',
    'jupyterlab',
]


def analyze(script, datas):
    return Analysis(
        [str(project_root / script)],
        pathex=[str(project_root)],
        datas=datas,
        excludes=excludes,
    )


def console_exe(analysis, name):
    return EXE(
        PYZ(analysis.pure),
        analysis.scripts,
        [],
        exclude_binaries=True,
        name=name,
        upx=False,
        console=True,
    )


cli = analyze('cli/main.py', model_datas)
web = analyze('webapp/launcher.py', model_datas + webapp_datas)

COLLECT(
    console_exe(cli, 'poke'),
    cli.binaries,
    cli.datas,
    console_exe(web, 'PokemonDetector'),
    web.binaries,
    web.datas,
    upx=False,
    name='PokemonDetector',
)
