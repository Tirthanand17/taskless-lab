"""Scan only explicitly mapped Google Flow Takeout MP4s; optionally import for QA.

Usage:
python scripts/flow_takeout_import.py --archive flow.zip --mapping clip_mapping.json
python scripts/flow_takeout_import.py --archive flow.zip --mapping clip_mapping.json --import-to /existing/media
"""
from pathlib import Path
import argparse
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from autopilot.flow_takeout_bridge import (
    scan_flow_takeout, import_review_candidates, redacted_report)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--archive",type=Path,required=True)
    parser.add_argument("--mapping",type=Path,required=True)
    parser.add_argument("--import-to",type=Path)
    parser.add_argument("--mode",choices=("pilot","lean_day","full_keyshots","daily_50_credit"),default="pilot")
    args=parser.parse_args()
    if not args.mapping.is_file() or args.mapping.is_symlink():
        parser.error("A real explicit JSON mapping file is required")
    mapping=json.loads(args.mapping.read_text(encoding="utf-8"))
    if args.import_to is None:
        report=redacted_report(scan_flow_takeout(args.archive,mapping))
    else:
        source=json.loads((ROOT/"content"/"flow"/"oct24_cinematic_flow_scene_package.json")
                          .read_text(encoding="utf-8"))
        report=import_review_candidates(args.archive,mapping,args.import_to,
                                        source,mode=args.mode)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    has_issue=isinstance(report,list) and any(x["issues"] for x in report)
    return 1 if has_issue else 0


if __name__=="__main__":
    sys.exit(main())
