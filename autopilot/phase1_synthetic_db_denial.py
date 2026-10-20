"""Fixed Linux test client: check that a worker cannot read private SQLite.

Exit code 0 ONLY when the supplied one-file SQLite path is inaccessible via
normal OS permissions. This script runs as the disposable worker UID in
no-secrets GitHub CI, not on the user's laptop. No database is modified.
"""
from __future__ import annotations

import os
import sys


def main() -> int:
    if len(sys.argv)!=2 or not sys.platform.startswith("linux"):
        return 2
    try:
        fd=os.open(sys.argv[1],os.O_RDONLY|os.O_CLOEXEC)
    except PermissionError:
        return 0
    except OSError:
        return 3
    else:
        os.close(fd)
        return 4


if __name__=="__main__":
    raise SystemExit(main())
