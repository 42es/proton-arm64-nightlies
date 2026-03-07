#!/usr/bin/env python3
"""
Remove i386 C++ mangled stubs from dlls/wdscore/wdscore.spec.

These stubs (CDynamicArray template methods with @QAE@ i386 calling convention)
cause lld-link to fail with "Invalid ARM64EC function name" when building the
aarch64-windows/wdscore.dll target. They were removed by the GameNative
wdscore patch but filter_patches.py cannot reliably detect whether the patch
has been applied (no unique positive marker exists in the patched version).
"""
import os
import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: fix_wdscore.py <wine-source-dir>")
        return 1

    wine_src = os.path.abspath(sys.argv[1])
    path = os.path.join(wine_src, "dlls", "wdscore", "wdscore.spec")

    if not os.path.exists(path):
        print(f"SKIP: {path} not found")
        return 0

    with open(path, errors="replace") as f:
        lines = f.readlines()

    kept = []
    removed = 0
    for line in lines:
        # i386 mangled names contain @QAE@, @QBE@, @IAE@ etc. (thiscall conventions)
        # These are invalid for ARM64EC and must be removed.
        if "CDynamicArray" in line and ("@QAE@" in line or "@QBE@" in line or
                                         "@IAE@" in line or "@ABV" in line or
                                         "@AAV" in line or "@@QAE" in line or
                                         "@@QBE" in line):
            removed += 1
        else:
            kept.append(line)

    if removed == 0:
        print("OK: no i386 CDynamicArray stubs found in wdscore.spec (already clean)")
        return 0

    with open(path, "w") as f:
        f.writelines(kept)

    print(f"FIXED: removed {removed} i386 CDynamicArray stubs from dlls/wdscore/wdscore.spec")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
