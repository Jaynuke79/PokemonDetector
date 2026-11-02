"""
Fail if the bundle needs a Visual C++ runtime DLL it does not contain.

Build machines have these DLLs in System32, so running the build there cannot
reveal one missing from the bundle; a PC without the redistributable would fail
to load torch. Run with the Windows build dependencies, which include pefile.

Usage: python check_bundled_runtime.py dist/PokemonDetector
"""

import re
import sys
from pathlib import Path

import pefile

VC_RUNTIME_DLL = re.compile(r"^(vcruntime|msvcp|vcomp|concrt|libomp)", re.IGNORECASE)
IMPORT_DIRECTORIES = [
    pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"],
    pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT"],
]


def imported_dlls(path):
    pe = pefile.PE(str(path), fast_load=True)
    try:
        pe.parse_data_directories(directories=IMPORT_DIRECTORIES)
        entries = [
            *getattr(pe, "DIRECTORY_ENTRY_IMPORT", []),
            *getattr(pe, "DIRECTORY_ENTRY_DELAY_IMPORT", []),
        ]
        return {entry.dll.decode("ascii", "replace").lower() for entry in entries}
    finally:
        pe.close()


def main(bundle):
    modules = [
        path
        for path in Path(bundle).rglob("*")
        if path.suffix.lower() in {".exe", ".dll", ".pyd"}
    ]
    bundled = {path.name.lower() for path in modules}
    missing = {}
    for module in modules:
        for dll in imported_dlls(module):
            if VC_RUNTIME_DLL.match(dll) and dll not in bundled:
                missing.setdefault(dll, []).append(module.name)

    print(f"Checked {len(modules)} modules")
    print("Bundled VC runtime DLLs:", sorted(filter(VC_RUNTIME_DLL.match, bundled)))
    for dll, importers in sorted(missing.items()):
        print(f"MISSING {dll}, needed by {', '.join(sorted(importers))}")
    return 1 if missing or not modules else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
