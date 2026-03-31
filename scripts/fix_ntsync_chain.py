#!/usr/bin/env python3
"""
Apply the drift-prone 0162 ntsync prerequisite edits directly to
dlls/ntdll/unix/sync.c.

This avoids failing the whole build on a single drifting patch hunk while still
producing the source shape that later ntsync patches expect.
"""
from __future__ import annotations

import os
import sys


def apply_once(src: str, desc: str, old: str, new: str) -> tuple[str, int]:
    if new in src:
        print(f"  [{desc}] already applied")
        return src, 0
    if old not in src:
        print(f"  [{desc}] pattern not found")
        return src, -1
    print(f"  [{desc}] applied")
    return src.replace(old, new, 1), 1


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: fix_ntsync_chain.py <wine-source-dir>")
        return 1

    path = os.path.join(sys.argv[1], "dlls", "ntdll", "unix", "sync.c")
    if not os.path.exists(path):
        print(f"ERROR: missing file {path}")
        return 2

    with open(path, encoding="utf-8", errors="replace") as f:
        src = f.read()

    ops = [
        (
            "insert 0162 inproc stubs",
            "static unsigned int validate_open_object_attributes( const OBJECT_ATTRIBUTES *attr )\n"
            "{\n"
            "    if (attr->Length != sizeof(*attr)) return STATUS_INVALID_PARAMETER;\n"
            "    return STATUS_SUCCESS;\n"
            "}\n"
            "\n"
            "\n"
            "/******************************************************************************\n"
            " *              NtCreateSemaphore (NTDLL.@)\n",
            "static unsigned int validate_open_object_attributes( const OBJECT_ATTRIBUTES *attr )\n"
            "{\n"
            "    if (attr->Length != sizeof(*attr)) return STATUS_INVALID_PARAMETER;\n"
            "    return STATUS_SUCCESS;\n"
            "}\n"
            "\n"
            "static NTSTATUS inproc_release_semaphore( HANDLE handle, ULONG count, ULONG *prev_count )\n"
            "{\n"
            "    return STATUS_NOT_IMPLEMENTED;\n"
            "}\n"
            "\n"
            "static NTSTATUS inproc_query_semaphore( HANDLE handle, SEMAPHORE_BASIC_INFORMATION *info )\n"
            "{\n"
            "    return STATUS_NOT_IMPLEMENTED;\n"
            "}\n"
            "\n"
            "static NTSTATUS inproc_set_event( HANDLE handle, LONG *prev_state )\n"
            "{\n"
            "    return STATUS_NOT_IMPLEMENTED;\n"
            "}\n"
            "\n"
            "static NTSTATUS inproc_reset_event( HANDLE handle, LONG *prev_state )\n"
            "{\n"
            "    return STATUS_NOT_IMPLEMENTED;\n"
            "}\n"
            "\n"
            "static NTSTATUS inproc_pulse_event( HANDLE handle, LONG *prev_state )\n"
            "{\n"
            "    return STATUS_NOT_IMPLEMENTED;\n"
            "}\n"
            "\n"
            "static NTSTATUS inproc_query_event( HANDLE handle, EVENT_BASIC_INFORMATION *info )\n"
            "{\n"
            "    return STATUS_NOT_IMPLEMENTED;\n"
            "}\n"
            "\n"
            "static NTSTATUS inproc_release_mutex( HANDLE handle, LONG *prev_count )\n"
            "{\n"
            "    return STATUS_NOT_IMPLEMENTED;\n"
            "}\n"
            "\n"
            "static NTSTATUS inproc_query_mutex( HANDLE handle, MUTANT_BASIC_INFORMATION *info )\n"
            "{\n"
            "    return STATUS_NOT_IMPLEMENTED;\n"
            "}\n"
            "\n"
            "static NTSTATUS inproc_wait( DWORD count, const HANDLE *handles, BOOLEAN wait_any,\n"
            "                             BOOLEAN alertable, const LARGE_INTEGER *timeout )\n"
            "{\n"
            "    return STATUS_NOT_IMPLEMENTED;\n"
            "}\n"
            "\n"
            "static NTSTATUS inproc_signal_and_wait( HANDLE signal, HANDLE wait,\n"
            "                                        BOOLEAN alertable, const LARGE_INTEGER *timeout )\n"
            "{\n"
            "    return STATUS_NOT_IMPLEMENTED;\n"
            "}\n"
            "\n"
            "\n"
            "/******************************************************************************\n"
            " *              NtCreateSemaphore (NTDLL.@)\n",
        ),
        (
            "hook NtQuerySemaphore",
            "    if (len != sizeof(SEMAPHORE_BASIC_INFORMATION)) return STATUS_INFO_LENGTH_MISMATCH;\n"
            "\n"
            "    if (do_fsync())\n",
            "    if (len != sizeof(SEMAPHORE_BASIC_INFORMATION)) return STATUS_INFO_LENGTH_MISMATCH;\n"
            "\n"
            "    if ((ret = inproc_query_semaphore( handle, out )) != STATUS_NOT_IMPLEMENTED)\n"
            "    {\n"
            "        if (!ret && ret_len) *ret_len = sizeof(SEMAPHORE_BASIC_INFORMATION);\n"
            "        return ret;\n"
            "    }\n"
            "\n"
            "    if (do_fsync())\n",
        ),
        (
            "hook NtReleaseSemaphore",
            "    TRACE( \"handle %p, count %u, prev_count %p\\n\", handle, (int)count, previous );\n"
            "\n"
            "    if (do_fsync())\n",
            "    TRACE( \"handle %p, count %u, prev_count %p\\n\", handle, (int)count, previous );\n"
            "\n"
            "    if ((ret = inproc_release_semaphore( handle, count, previous )) != STATUS_NOT_IMPLEMENTED)\n"
            "        return ret;\n"
            "\n"
            "    if (do_fsync())\n",
        ),
        (
            "hook NtSetEvent",
            "    TRACE( \"handle %p, prev_state %p\\n\", handle, prev_state );\n"
            "\n"
            "    if (do_fsync())\n",
            "    TRACE( \"handle %p, prev_state %p\\n\", handle, prev_state );\n"
            "\n"
            "    if ((ret = inproc_set_event( handle, prev_state )) != STATUS_NOT_IMPLEMENTED)\n"
            "        return ret;\n"
            "\n"
            "    if (do_fsync())\n",
        ),
        (
            "hook NtResetEvent",
            "    TRACE( \"handle %p, prev_state %p\\n\", handle, prev_state );\n"
            "\n"
            "    if (do_fsync())\n",
            "    TRACE( \"handle %p, prev_state %p\\n\", handle, prev_state );\n"
            "\n"
            "    if ((ret = inproc_reset_event( handle, prev_state )) != STATUS_NOT_IMPLEMENTED)\n"
            "        return ret;\n"
            "\n"
            "    if (do_fsync())\n",
        ),
        (
            "hook NtPulseEvent",
            "    TRACE( \"handle %p, prev_state %p\\n\", handle, prev_state );\n"
            "\n"
            "    if (do_fsync())\n",
            "    TRACE( \"handle %p, prev_state %p\\n\", handle, prev_state );\n"
            "\n"
            "    if ((ret = inproc_pulse_event( handle, prev_state )) != STATUS_NOT_IMPLEMENTED)\n"
            "        return ret;\n"
            "\n"
            "    if (do_fsync())\n",
        ),
        (
            "hook NtQueryEvent",
            "    if (len != sizeof(EVENT_BASIC_INFORMATION)) return STATUS_INFO_LENGTH_MISMATCH;\n"
            "\n"
            "    if (do_fsync())\n",
            "    if (len != sizeof(EVENT_BASIC_INFORMATION)) return STATUS_INFO_LENGTH_MISMATCH;\n"
            "\n"
            "    if ((ret = inproc_query_event( handle, out )) != STATUS_NOT_IMPLEMENTED)\n"
            "    {\n"
            "        if (!ret && ret_len) *ret_len = sizeof(EVENT_BASIC_INFORMATION);\n"
            "        return ret;\n"
            "    }\n"
            "\n"
            "    if (do_fsync())\n",
        ),
        (
            "hook NtReleaseMutant",
            "    TRACE( \"handle %p, prev_count %p\\n\", handle, prev_count );\n"
            "\n"
            "    if (do_fsync())\n",
            "    TRACE( \"handle %p, prev_count %p\\n\", handle, prev_count );\n"
            "\n"
            "    if ((ret = inproc_release_mutex( handle, prev_count )) != STATUS_NOT_IMPLEMENTED)\n"
            "        return ret;\n"
            "\n"
            "    if (do_fsync())\n",
        ),
        (
            "hook NtQueryMutant",
            "    if (len != sizeof(MUTANT_BASIC_INFORMATION)) return STATUS_INFO_LENGTH_MISMATCH;\n"
            "\n"
            "    if (do_fsync())\n",
            "    if (len != sizeof(MUTANT_BASIC_INFORMATION)) return STATUS_INFO_LENGTH_MISMATCH;\n"
            "\n"
            "    if ((ret = inproc_query_mutex( handle, out )) != STATUS_NOT_IMPLEMENTED)\n"
            "    {\n"
            "        if (!ret && ret_len) *ret_len = sizeof(MUTANT_BASIC_INFORMATION);\n"
            "        return ret;\n"
            "    }\n"
            "\n"
            "    if (do_fsync())\n",
        ),
        (
            "hook NtWaitForMultipleObjects",
            "    if (do_fsync())\n"
            "    {\n",
            "    if ((ret = inproc_wait( count, handles, wait_any, alertable, timeout )) != STATUS_NOT_IMPLEMENTED)\n"
            "    {\n"
            "        TRACE( \"-> %#x\\n\", ret );\n"
            "        return ret;\n"
            "    }\n"
            "\n"
            "    if (do_fsync())\n"
            "    {\n",
        ),
        (
            "hook NtSignalAndWaitForSingleObject",
            "NTSTATUS WINAPI NtSignalAndWaitForSingleObject( HANDLE signal, HANDLE wait,\n"
            "                                                BOOLEAN alertable, const LARGE_INTEGER *timeout )\n"
            "{\n"
            "    union select_op select_op;\n"
            "    UINT flags = SELECT_INTERRUPTIBLE;\n"
            "\n"
            "    TRACE( \"signal %p, wait %p, alertable %u, timeout %s\\n\", signal, wait, alertable, debugstr_timeout(timeout) );\n"
            "\n"
            "    if (do_fsync())\n"
            "        return fsync_signal_and_wait( signal, wait, alertable, timeout );\n"
            "\n"
            "    if (do_esync())\n"
            "        return esync_signal_and_wait( signal, wait, alertable, timeout );\n"
            "\n"
            "    if (!signal) return STATUS_INVALID_HANDLE;\n",
            "NTSTATUS WINAPI NtSignalAndWaitForSingleObject( HANDLE signal, HANDLE wait,\n"
            "                                                BOOLEAN alertable, const LARGE_INTEGER *timeout )\n"
            "{\n"
            "    NTSTATUS ret;\n"
            "    union select_op select_op;\n"
            "    UINT flags = SELECT_INTERRUPTIBLE;\n"
            "\n"
            "    TRACE( \"signal %p, wait %p, alertable %u, timeout %s\\n\", signal, wait, alertable, debugstr_timeout(timeout) );\n"
            "\n"
            "    if (!signal) return STATUS_INVALID_HANDLE;\n"
            "\n"
            "    if ((ret = inproc_signal_and_wait( signal, wait, alertable, timeout )) != STATUS_NOT_IMPLEMENTED)\n"
            "        return ret;\n"
            "\n"
            "    if (do_fsync())\n"
            "        return fsync_signal_and_wait( signal, wait, alertable, timeout );\n"
            "\n"
            "    if (do_esync())\n"
            "        return esync_signal_and_wait( signal, wait, alertable, timeout );\n"
            "\n"
            "    if (!signal) return STATUS_INVALID_HANDLE;\n",
        ),
    ]

    ok = True
    for desc, old, new in ops:
        src, rc = apply_once(src, desc, old, new)
        if rc < 0:
            ok = False

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)

    if not ok:
        print("fix_ntsync_chain: failed to apply full 0162 drift fix")
        return 2

    print("fix_ntsync_chain: 0162 ntsync prerequisite looks complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
