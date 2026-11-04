# Desktop app options

Today the Windows installer ships `poke.exe` (CLI) and `PokemonDetector.exe`,
which serves the Flask page on 127.0.0.1 and opens it in the browser. This page
compares ways to give it a real desktop window, and describes the PySide6
prototype in `desktop/`.

Every option has to bundle torch, torchvision and the 351 MB weights, which
dominate the size: the current installer bundle is 818,372,831 bytes and the
installer 475,514,315 bytes ([run 41520167444](https://github.com/Jaynuke79/PokemonDetector/actions/runs/41520167444)).

Items marked *(unverified)* were not checked in this repo or in CI.

## Comparison

| | PySide6 (Qt Widgets) | tkinter | pywebview around the existing page | Tauri or Electron with a Python sidecar |
| --- | --- | --- | --- | --- |
| UI work | New Python UI. The prototype is about 1,500 lines in `desktop/`, including the scanner styling,, reusing `lib.detector_core` | New Python UI with fewer widgets. Tk has no file drag and drop without `tkinterdnd2`, a binary Tk extension *(unverified on Windows)* | Little: reuse `webapp/templates/index.html` and Flask, or call `lib` through pywebview's JS bridge | Move the page into a JS frontend, and run Python as a separate process the frontend talks to over HTTP or stdio |
| Size added to the bundle | Measured: 41.8 MB (PySide6 and shiboken6 after dropping unused plugins), see [Measured size](#measured-size) | About 10-15 MB of Tcl/Tk *(unverified)* | pythonnet and the WebView2 loader, a few MB; WebView2 itself comes with Windows 10/11 *(unverified)* | Tauri: a small Rust binary using WebView2 *(unverified)*. Electron: a Chromium copy, roughly 150-250 MB unpacked *(unverified)*. Both add a second PyInstaller bundle for the sidecar |
| License against AGPL-3.0 | LGPL-3.0, compatible. See [LGPL obligations](#lgpl-obligations-for-pyside6) | PSF and Tcl/Tk BSD-style licenses, no extra obligations | pywebview 6.2.1 is BSD-3-Clause and pythonnet 3.2.1 is MIT | Tauri is MIT/Apache-2.0 and Electron is MIT; Chromium in Electron carries many third-party notices *(unverified)* |
| Windows packaging with PyInstaller | PyInstaller 6.22.3 has PySide6 hooks and built this onedir bundle in CI. Unused Qt plugins have to be filtered in the spec | Works out of the box | Hooks in pyinstaller-hooks-contrib, but pythonnet and WebView2 DLLs are a common source of runtime failures *(unverified)* | Two toolchains (Rust or Node plus Python) and two build steps; the sidecar is still a PyInstaller build, and its lifetime has to be managed |
| Testable in CI | Yes: Qt's `offscreen` platform runs the real window in pytest on Linux and Windows, and the bundle runs `--self-test` in CI | Needs a display; `tkinter` tests are possible but there is no offscreen backend | The page is already tested through the Flask test client; the window itself needs WebView2 on a desktop session *(unverified on the runner)* | Frontend unit tests plus WebDriver (`tauri-driver`, or Playwright for Electron); the most moving parts *(unverified)* |
| Accessibility | Qt Widgets expose names and roles through UI Automation on Windows, and Qt 6.8+ can announce status changes | Tk exposes almost nothing to screen readers on Windows *(unverified for Tk 9)* | Inherits the web page's accessibility through Edge's UI Automation support | Same as a browser page |

## Recommendation

Use **PySide6** if the goal is a native window. It is the only option where the
whole window, including errors and threading, runs under pytest in CI and the
built bundle is exercised on Windows, it gives native accessibility, and it
keeps one language and one build. The cost is the extra Qt size measured below
and the LGPL notices.

If the goal is only "no browser tab", **pywebview** is the smaller change,
because it reuses the existing page. tkinter is not recommended because of
screen reader support, and Tauri or Electron add a second toolchain without
removing the Python bundle.

## LGPL obligations for PySide6

PySide6 and Qt are LGPL-3.0 (or GPL). LGPL-3.0 code can be combined with an
AGPL-3.0 app. When distributing the bundle:

- Keep Qt as separate shared libraries the user can replace. The onedir build
  does this: `Qt6Core.dll` and the others are separate files under
  `_internal\PySide6`. A PyInstaller onefile build makes replacing them much
  harder, so do not use one.
- Ship the LGPL-3.0 and GPL-3.0 texts and a notice saying Qt and PySide6 are
  used under LGPL. The prototype bundles them from `windows/desktop-licenses/`
  into `_internal\licenses`. The PySide6 wheels contain no license files, so
  they cannot be collected from the package.
- Make the Qt and PySide6 source available. The notice links to the upstream
  source *(unverified whether a link alone meets GPL-3.0 section 6 for a
  binary you distribute; a written offer or hosting the matching source is the
  safe option)*.
- Do not prevent users from running a modified Qt, for example by signature
  checks on the DLLs.

This is a summary, not legal advice.

## The prototype

`desktop/` is a PySide6 window styled as a handheld scanner, with a drop area
(the "screen") and an "Open image…" button (Ctrl+O). It accepts the same
png/jpg/jpeg/gif/bmp files as the web app, and shows a preview, a card with
the top prediction, its confidence and its elemental types, the other top 5
predictions as text with confidence bars, and a status line. A scan line sweeps
the screen while an image is classified; it stays still when Windows
animations are off or `POKE_REDUCED_MOTION=1` is set. Everything is drawn with
Qt stylesheets and QPainter, with no image files. Fonts, sizes and painting
are drawn at 1.5 times their base size, on top of any OS display scaling, or
smaller if the window would not fit the screen (`theme.ui_scale_for()`); the
window opens centred and no larger than the available screen. The types come from
`desktop/elemental_types.json`, which the spec bundles into
`_internal\desktop`. The model loads and images are classified on a worker
thread through `lib.detector_core`; missing model files and unreadable images
show a dialog. The pinned dependency is `pyside6-essentials`, the subset of
PySide6 without the Addons and WebEngine wheels.

It is not in the installer yet.

### Run it locally

```bash
uv sync --extra desktop
uv run --extra desktop poke-gui

# Classify one image through the window and exit 0 on success, 1 on failure
uv run --extra desktop poke-gui --self-test gengar.png

# The same, showing the window and saving a screenshot of it
uv run --extra desktop poke-gui --self-test gengar.png --screenshot window.png
```

It reads the weights from `models/` like the CLI (see `default_models_dir()`).
It ran on WSLg's Wayland display without extra setup. On Linux without a
display, set `QT_QPA_PLATFORM=offscreen`. A small "Starting Pokemon Detector…"
splash shows while torch and timm import, which took about 15 seconds in WSL.

Tests: `uv run --extra test --extra desktop pytest`. Without the `desktop`
extra installed, `tests/test_desktop.py` is reported as skipped.

### Get the Windows build

The [Desktop app prototype workflow](../.github/workflows/desktop-prototype.yml)
runs on pull requests to main that touch the desktop code, and can be run by
hand once it is on main. Each run uploads, for 7 days:

- `PokemonDetectorDesktop-prototype`: the zipped onedir build. Unzip it and run
  `PokemonDetectorDesktop.exe`.

The exe is a windowed app, so a terminal does not wait for it and `--self-test`
prints nothing there unless its output is redirected. In PowerShell:

```powershell
$p = Start-Process .\PokemonDetectorDesktop.exe -ArgumentList '--self-test', 'gengar.png' `
  -Wait -PassThru -NoNewWindow -RedirectStandardOutput out.txt -RedirectStandardError err.txt
$p.ExitCode; Get-Content out.txt, err.txt
```
- `desktop-screenshots`: the window after classifying `gengar.png`, at 100% and
  at 150% scaling, plus the output of each run.

### Measured size

From the onedir build in CI (PyInstaller 6.22.3, PySide6-Essentials 6.12.0,
torch 2.7.1+cpu, Python 3.11). The totals vary by a few hundred bytes between
builds:

| Part | MB | Bytes |
| --- | ---: | ---: |
| Whole bundle | 796.1 | 834,748,811 |
| Qt (PySide6 + shiboken6) | 41.8 | 43,847,576 |
| torch + torchvision | 309.7 | 324,763,891 |
| Model weights | 334.7 | 351,007,742 |

The zipped artifact is 476.1 MB (499,201,866 bytes). Compared with the current
installer bundle (818,372,831 bytes), the desktop bundle drops Flask, Werkzeug
and the CLI and adds Qt.

In CI the window ran on the default `windows` Qt platform, not `offscreen`. The
150% screenshot is 1028x761 pixels: the window shrank to fit the runner's small
screen, and the layout still shows every result without clipping.

The spec keeps only the `qwindows` and `qoffscreen` platform plugins and the
`styles` plugin, and drops Qt's image format, icon engine, TLS and network
plugins, Qt6Svg, Qt6Network, `opengl32sw.dll` and the Qt translations. Pillow
decodes the preview, so Qt needs no image format plugins. Dropping the
translations means Qt's own dialog buttons are always in English.

### Known issue found while building it

Importing torch for the first time on a QThread and then running the model
there corrupted the heap (exit 0xC0000374 on Windows, double frees on Linux).
`desktop/worker.py` imports `lib.detector_core`, and with it torch, at module
level so it happens on the main thread, and `tests/test_desktop.py` checks
that. The root cause inside torch or Qt was not investigated.
