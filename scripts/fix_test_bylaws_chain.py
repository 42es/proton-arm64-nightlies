#!/usr/bin/env python3
"""
Apply and verify additional BYLAWS patch chain pieces that commonly drift on
bleeding-edge and can cause runtime hangs if partially missing.

Usage: fix_test_bylaws_chain.py <wine-source-dir>
"""
import os
import subprocess
import sys


PATCHES = [
    "dlls_ntdll_loader_c.patch",
    "dlls_ntdll_ntdll_misc_h.patch",
    "dlls_ntdll_ntdll_spec.patch",
    "dlls_ntdll_signal_arm64_c.patch",
    "dlls_ntdll_signal_arm64ec_c.patch",
    "dlls_ntdll_signal_x86_64_c.patch",
    "dlls_wow64_syscall_c.patch",
    "dlls_wow64_wow64_spec.patch",
    "include_winternl_h.patch",
    "tools_makedep_c.patch",
]

# relative file -> markers that must all be present after patching
REQUIRED_MARKERS = {
    "dlls/ntdll/loader.c": [
        "pWow64SuspendLocalThread",
        "GET_PTR( Wow64SuspendLocalThread )",
    ],
    "dlls/ntdll/ntdll_misc.h": [
        "pWow64SuspendLocalThread",
    ],
    "dlls/ntdll/ntdll.spec": [
        "RtlWow64SuspendThread",
    ],
    "dlls/ntdll/signal_arm64.c": [
        "RtlWow64SuspendThread",
    ],
    "dlls/ntdll/signal_arm64ec.c": [
        "RtlWow64SuspendThread",
    ],
    "dlls/ntdll/signal_x86_64.c": [
        "RtlWow64SuspendThread",
    ],
    "dlls/wow64/syscall.c": [
        "Wow64SuspendLocalThread",
    ],
    "dlls/wow64/wow64.spec": [
        "Wow64SuspendLocalThread",
    ],
    "include/winternl.h": [
        "THREAD_CREATE_FLAGS_BYPASS_PROCESS_FREEZE",
        "RtlWow64SuspendThread",
    ],
    "tools/makedep.c": [
        "arch_install_dirs[arch] = \"$(libdir)/wine/aarch64-windows/\";",
        "output_symlink_rule(",
    ],
}


def run(cmd, cwd):
    p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p.returncode, p.stdout


def try_apply_patch(wine_src, patch_path):
    attempts = [
        ["git", "-C", wine_src, "apply", "--ignore-whitespace", "-C1", patch_path],
        ["git", "-C", wine_src, "apply", "--3way", "--ignore-space-change", patch_path],
        ["patch", "-d", wine_src, "-p1", "--forward", "--batch", "--ignore-whitespace", "-i", patch_path],
    ]

    for cmd in attempts:
        rc, out = run(cmd, cwd=None)
        if rc == 0:
            return True, out

    # already-applied check
    rc, out = run(
        ["git", "-C", wine_src, "apply", "--ignore-whitespace", "-C1", "-R", "--check", patch_path],
        cwd=None,
    )
    if rc == 0:
        return True, "already applied"

    return False, out


def verify(wine_src):
    ok = True
    for rel, markers in REQUIRED_MARKERS.items():
        path = os.path.join(wine_src, rel)
        if not os.path.exists(path):
            print(f"VERIFY FAIL: missing file {rel}")
            ok = False
            continue

        with open(path, errors="replace") as f:
            txt = f.read()

        for m in markers:
            if m not in txt:
                print(f"VERIFY FAIL: marker '{m}' missing in {rel}")
                ok = False

    return ok


def main():
    if len(sys.argv) < 2:
        print("Usage: fix_test_bylaws_chain.py <wine-source-dir>")
        return 1

    wine_src = os.path.abspath(sys.argv[1])
    patch_dir = os.path.join(wine_src, "android", "patches", "test-bylaws")

    if not os.path.isdir(patch_dir):
        print(f"ERROR: patch dir not found: {patch_dir}")
        return 2

    all_ok = True

    for name in PATCHES:
        p = os.path.join(patch_dir, name)
        if not os.path.exists(p):
            print(f"ERROR: missing patch {name}")
            all_ok = False
            continue

        ok, info = try_apply_patch(wine_src, p)
        if ok:
            print(f"BYLAWS OK: {name}")
        else:
            print(f"BYLAWS FAIL: {name}")
            print(info.strip())
            all_ok = False

    verified = verify(wine_src)

    if not all_ok or not verified:
        print("fix_test_bylaws_chain: FAILED")
        return 3

    print("fix_test_bylaws_chain: success")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
