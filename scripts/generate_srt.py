from __future__ import annotations

import argparse
import json
from pathlib import Path


def ts(seconds: float) -> str:
    ms = round(seconds * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1_000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def build_srt(captions: list[dict]) -> str:
    out = []
    for i, item in enumerate(captions, 1):
        start = float(item["start"])
        end = float(item["end"])
        text = str(item["text"]).strip()
        if end <= start:
            raise ValueError(f"caption {i}: end must be after start")
        if not text:
            raise ValueError(f"caption {i}: empty text")
        out += [str(i), f"{ts(start)} --> {ts(end)}", text, ""]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("episode_json", type=Path)
    ap.add_argument("output_srt", type=Path)
    args = ap.parse_args()

    data = json.loads(args.episode_json.read_text(encoding="utf-8"))
    args.output_srt.write_text(build_srt(data["captions"]), encoding="utf-8")


if __name__ == "__main__":
    main()
