"""Fixed, harmless synthetic worker executable for offline CI only.

No filesystem writes, network calls, imports from user projects, media, or
credentials. It emits a bounded piece of synthetic status, not a genuine
production task artifact. Only used by the local subprocess supervisor.
"""
from __future__ import annotations
import ctypes
import hashlib
import json
import os
import signal
import subprocess
import sys
import time


def _require_live_parent(expected_pid: int) -> bool:
    """Linux parent-death SIGKILL protects against supervisor crash.

    PR_SET_PDEATHSIG is Linux-only and fires when the *immediate* parent
    exits. Check expected parent again after prctl to close setup race.
    """
    if not sys.platform.startswith("linux") or expected_pid <= 1:
        return False
    libc=ctypes.CDLL(None,use_errno=True)
    prctl=libc.prctl
    prctl.argtypes=[ctypes.c_int,ctypes.c_ulong,
                    ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong]
    prctl.restype=ctypes.c_int
    if prctl(1,signal.SIGKILL,0,0,0)!=0:
        return False
    return os.getppid()==expected_pid


def main() -> int:
    if len(sys.argv)!=5:
        return 2
    task, mode, duration, expected_parent=sys.argv[1:]
    try:
        parent_pid=int(expected_parent)
    except ValueError:
        return 2
    if not _require_live_parent(parent_pid):
        return 3
    if not (3<=len(task)<=100 and all(
            ch.isascii() and (ch.islower() or ch.isdigit()
                              or ch in "_:-") for ch in task)):
        return 2
    if mode not in ("brief","block","error","tree"):
        return 2
    try:
        seconds=float(duration)
    except ValueError:
        return 2
    if not 0<=seconds<=2:
        return 2
    if mode=="tree":
        # Fixed stdlib-only grandchild inherits this private process group;
        # both it and its immediate parent configure parent-death SIGKILL.
        desc=subprocess.Popen(
            [sys.executable,"-I","-B",os.path.abspath(__file__),
             task,"block","0",str(os.getpid())],
            stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={"PYTHONIOENCODING":"utf-8","PYTHONDONTWRITEBYTECODE":"1"},
            close_fds=True,
        )
        print("CHILD_PID:"+str(desc.pid),flush=True)
        while True:
            time.sleep(0.1)
    if mode=="block":
        print("READY",flush=True)
        while True:
            time.sleep(0.1)
    time.sleep(seconds)
    if mode=="error":
        return 9
    payload={
        "kind":"SYNTHETIC_STAGING_PROBE",
        "task_id":task,
        "marker_sha256":hashlib.sha256(task.encode("utf-8")).hexdigest(),
        "publishing_authorized":False,
    }
    print(json.dumps(payload,sort_keys=True,separators=(",",":")))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
