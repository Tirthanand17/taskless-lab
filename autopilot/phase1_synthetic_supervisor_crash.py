"""Fixed Linux-only test: a supervisor parent crashes without cleanup.

No arbitrary command, shell, files or network. Spawn the known synthetic
child, wait until its parent-death guard says READY, then intentionally exit
the parent without waiting or terminating it. Parent-death SIGKILL should
stop the child even when no supervisor polling loop survives.
"""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys

PROBE=Path(__file__).with_name("phase1_synthetic_subprocess.py")

def main()->int:
    if not sys.platform.startswith("linux"):
        return 2
    child=subprocess.Popen(
        [sys.executable,"-I","-B",str(PROBE),
         "synthetic_crash_probe:research","block","0",str(os.getpid())],
        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,text=True,
        env={"PYTHONIOENCODING":"utf-8","PYTHONDONTWRITEBYTECODE":"1"},
        start_new_session=True,
    )
    if child.stdout.readline().strip()!="READY":
        child.kill()
        child.wait()
        return 3
    print(child.pid,flush=True)
    # Abrupt exit intentionally bypasses finally, as in a host crash.
    os._exit(0)

if __name__=="__main__":
    raise SystemExit(main())
