from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    rendered = 0
    for path in sorted((ROOT / "content" / "episodes").glob("short_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("renderer") != "manifest_v2":
            continue
        subprocess.run(
            ["python", str(ROOT / "scripts" / "render_manifest_short.py"), str(path)],
            check=True,
            cwd=ROOT,
        )
        rendered += 1
    print(f"rendered {rendered} manifest short(s)")

if __name__ == "__main__":
    main()
