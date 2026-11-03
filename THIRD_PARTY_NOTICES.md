# Third-Party Notices

Pokemon Detector is licensed under the GNU AGPL v3 (see `LICENSE` and `NOTICE`). The Windows installer also bundles the third-party components below, each under its own license. That license, not the AGPL, governs the component.

## Python packages

These are the packages `windows\build_windows.bat` installs for the bundle: `torch` and `torchvision` from the PyTorch CPU index, and the Windows, Python 3.11 lines of `requirements.txt`. Licenses are taken from each package's own metadata (`License-Expression`, `License`, classifiers and the license files in its `.dist-info`). Where the metadata names only a family such as "BSD", the variant comes from the license file shipped in the package.

| Package | Version | License |
|---------|---------|---------|
| blinker | 1.9.0 | MIT |
| certifi | 2025.4.26 | MPL-2.0 |
| charset-normalizer | 3.4.2 | MIT |
| click | 8.2.1 | BSD-3-Clause |
| colorama | 0.4.6 | BSD-3-Clause |
| filelock | 3.18.0 | Unlicense |
| Flask | 3.1.1 | BSD-3-Clause |
| fsspec | 2025.5.1 | BSD-3-Clause |
| huggingface-hub | 0.33.0 | Apache-2.0 |
| idna | 3.10 | BSD-3-Clause |
| itsdangerous | 2.2.0 | BSD-3-Clause |
| Jinja2 | 3.1.6 | BSD-3-Clause |
| MarkupSafe | 3.0.2 | BSD-3-Clause |
| mpmath | 1.3.0 | BSD-3-Clause |
| networkx | 3.5 | BSD-3-Clause |
| numpy | 2.3.0 | BSD-3-Clause, plus the bundled components listed in its license (see below) |
| packaging | 25.0 | Apache-2.0 OR BSD-2-Clause |
| pillow | 13.0.0 | MIT-CMU |
| PyYAML | 6.0.2 | MIT |
| requests | 2.32.4 | Apache-2.0 |
| safetensors | 0.5.3 | Apache-2.0 (metadata gives only the classifier; the package ships no license file) |
| sympy | 1.14.0 | BSD-3-Clause |
| timm | 1.0.15 | Apache-2.0 |
| torch | 2.7.1+cpu | BSD-3-Clause, plus the bundled components listed in its `NOTICE` (see below) |
| torchvision | 0.22.1+cpu | BSD-3-Clause |
| tqdm | 4.67.1 | MPL-2.0 AND MIT |
| typing_extensions | 4.14.0 | PSF-2.0 |
| urllib3 | 2.4.0 | MIT |
| Werkzeug | 3.1.9 | BSD-3-Clause |

The build environment also installs setuptools 84.2.1 (MIT), a dependency of PyInstaller. Whether PyInstaller collects it into the bundle has not been checked. gunicorn is in `requirements.txt` but the build checks that it is not bundled.

## Native libraries inside those packages

- **torch** ships compiled third-party code, such as libuv (`uv.dll`) and FBGEMM, whose licenses are in the `LICENSE` and `NOTICE` files of the torch wheel. It also ships `asmjit.dll`, `libiomp5md.dll` and `libiompstubs5md.dll`, which those files do not mention, so their licenses were not verified.
- **numpy** ships OpenBLAS (BSD-3-Clause), LAPACK (BSD-3-Clause-Open-MPI) and the GCC runtime library (GPL-3.0-or-later WITH GCC-exception-3.1) in `libscipy_openblas*.dll`, as its license metadata states.
- **pillow** ships libjpeg, libpng, libwebp, zlib and other image libraries. Their licenses are in the `LICENSE` file of the pillow wheel.

## Components not described by package metadata

These are in the bundle but have no Python package metadata to check, so their licenses here were not verified that way:

- **CPython 3.11** (`python311.dll` and the standard library), under the Python Software Foundation License.
- **PyInstaller 6.22.3 bootloader**, the code inside `poke.exe` and `PokemonDetector.exe`. PyInstaller's metadata describes its license as "GPLv2-or-later with a special exception which allows to use PyInstaller to build and distribute non-free programs (including commercial ones)".
- **Microsoft Visual C++ runtime DLLs**, under Microsoft's redistribution terms for the Visual C++ Redistributable.
