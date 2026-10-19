"""Fixed, harmless synthetic worker executable for offline CI only.

No filesystem writes, network calls, imports from user projects, media, or
credentials. It emits a bounded piece of synthetic status, not a genuine
production task artifact. Only used by the local subprocess supervisor.
"""
from __future__ import annotations
import hashlib
import json
import sys
import time


def main() -> int:
    if len(sys.argv)!=4:
        return 2
    task, mode, duration=sys.argv[1:]
    if not (3<=len(task)<=100 and all(
            ch.isascii() and (ch.islower() or ch.isdigit()
                              or ch in "_:-") for ch in task)):
        return 2
    if mode not in ("brief","block","error"):
        return 2
    try:
        seconds=float(duration)
    except ValueError:
        return 2
    if not 0<=seconds<=2:
        return 2
    if mode=="block":
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
