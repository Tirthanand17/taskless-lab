"""Offline-only editorial slate generator; never uploads or spends money.

Usage:
 python -m autopilot.director --day 2026-10-17 --input candidate.json --output plan.json
This is a validated prototype, not a live research/scheduling integration.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
from autopilot.core import GateError, Topic, SLOTS, CHANNEL_ID, require_future, slot_utc

def draft(day: str, payload: dict, now: datetime | None = None) -> dict:
    entries = payload.get("episodes")
    if not isinstance(entries, dict) or set(entries) != set(SLOTS):
        raise GateError("Exactly short_am, long and short_pm are required")
    recent = tuple(payload.get("recent_titles", ()))
    decisions = []
    previous_example = set()
    for kind in ("short_am", "long", "short_pm"):
        data = entries[kind]
        topic = Topic(
            title=data["title"],
            viewer_benefit=data["viewer_benefit"],
            original_example=data["original_example"],
            source_urls=tuple(data["source_urls"]),
            editorial_score=float(data["editorial_score"]),
        )
        topic.validate(recent)
        example = topic.original_example.strip().lower()
        if example in previous_example:
            raise GateError("Shorts and long should not recycle an identical demonstration")
        previous_example.add(example)
        utc = slot_utc(day, kind)
        require_future(utc, now=now)
        decisions.append({
            "slot":kind,"planned_at_utc":utc,"title":topic.title,
            "source_urls":list(topic.source_urls),
            "editorial_score":topic.editorial_score,
            "status":"research_draft_only",
            "publish_allowed":False,
        })
    return {
        "schema":"flowminute.autopilot.draft.v1",
        "channel_id":CHANNEL_ID,
        "day_ist":day,
        "state":"NO_RENDER_NO_UPLOAD_NO_SCHEDULE",
        "episodes":decisions,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--day",required=True)
    p.add_argument("--input",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    plan=draft(args.day,json.loads(args.input.read_text(encoding="utf8")))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(plan,indent=2)+"\n",encoding="utf8")
    print("DRAFT_ONLY_VALIDATED",args.output)

if __name__ == "__main__":
    main()
