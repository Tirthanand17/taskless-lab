"""Compose a real-media FlowMinute DRAFT, never upload or publish.

Example:
python scripts/compose_flow_episode.py --manifest /authorized/episode.json --output /authorized/draft.mp4
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from autopilot.flow_episode_compositor import assemble


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--test-only",action="store_true",
                    help="Permits incomplete synthetic/test previews only; cannot publish")
    args=ap.parse_args()
    if not args.manifest.is_file() or args.manifest.is_symlink():
        ap.error("An existing real manifest JSON is required")
    plan=json.loads(args.manifest.read_text(encoding="utf-8"))
    report=assemble(plan,args.output,test_mode=args.test_only)
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
