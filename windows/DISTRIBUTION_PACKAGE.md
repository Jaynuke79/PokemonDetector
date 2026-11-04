# Distributing Pokemon Detector on Windows

The distributable is one file, `PokemonDetectorSetup-<version>.exe`. Users do not need Python.

## Where it comes from

The [Windows installer workflow](../.github/workflows/windows-installer.yml) builds, tests and uploads it on a clean Windows runner. It stores the installer and a `.sha256` file as a workflow artifact for 7 days. It does not publish a release.

The workflow builds with `windows\build_windows.bat`, and you can run the same script on your own Windows PC. It needs Python 3.11 and the weights in `models\`, and it compiles the installer if [Inno Setup 6](https://jrsoftware.org/isinfo.php) is installed. CI only runs its success path; its error messages have not been run.

## How it is built

| File | Purpose |
|------|---------|
| `poke.spec` | PyInstaller build of `dist\PokemonDetector\`: `poke.exe`, `PokemonDetector.exe` and a shared `_internal\` holding the weights |
| `installer.iss` | Inno Setup script. Pass the version from `pyproject.toml` with `ISCC /DAppVersion=<version>` |
| `verify_installer.ps1` | Installs, runs, upgrades and uninstalls the installer. It rewrites the user PATH, so use it only on a throwaway machine |
| `check_bundled_runtime.py` | Fails if the bundle needs a Visual C++ runtime DLL it does not contain |

## Before sharing it

- The installer is not code signed, so Windows SmartScreen warns users, who have to choose "More info" and then "Run anyway". Antivirus tools can also flag PyInstaller executables.
- Publish the SHA-256 alongside the installer so users can check their download: `certutil -hashfile PokemonDetectorSetup-<version>.exe SHA256`.
- The installer shows `LICENSE` (GNU AGPL v3) on a page the user must accept, and installs it with `NOTICE` and `THIRD_PARTY_NOTICES.md`. Update `THIRD_PARTY_NOTICES.md` when the bundled dependencies change.
