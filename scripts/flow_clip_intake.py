"""Offline read-only Google Flow MP4 intake; no upload or spending."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from autopilot.flow_clip_intake import inspect_flow_clip, redacted_json


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--file",required=True,type=Path)
    p.add_argument("--episode",required=True)
    p.add_argument("--clip",required=True)
    p.add_argument("--mode",choices=("pilot","lean_day","full_keyshots"),default="pilot")
    p.add_argument("--source",choices=("google_flow_download","user_supplied_file"),
                   default="google_flow_download")
    p.add_argument("--report",type=Path)
    args=p.parse_args()
    data=json.loads((ROOT/"content"/"flow"/"oct24_cinematic_flow_scene_package.json")
                    .read_text(encoding="utf-8"))
    result=inspect_flow_clip(args.file,data,episode_id=args.episode,clip_id=args.clip,
                             mode=args.mode,source=args.source)
    output=json.dumps(redacted_json(result),indent=2,ensure_ascii=False)+"\n"
    if args.report is not None:
        if (not args.report.parent.is_dir() or args.report.parent.is_symlink()
                or args.report.is_symlink()):
            p.error("Report parent must be an existing real directory")
        args.report.write_text(output,encoding="utf-8")
    print(output,end="")
    return 0 if result.technical_candidate else 1


if __name__=="__main__":
    raise SystemExit(main())
