"""Offline October 24 3D story audit. Does not render, upload or approve media."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from autopilot.story3d import validate_3d_lesson, Story3DError
PACK = ROOT / "content" / "storyboards" / "oct24_multicharacter_3d_plans.json"


def main():
    doc = json.loads(PACK.read_text(encoding="utf-8"))
    ids = [episode["episode_id"] for episode in doc["episodes"]]
    if len(ids) != 3 or len(set(ids)) != 3:
        raise Story3DError("Expected three non-duplicate October 24 episodes")
    outcomes = [validate_3d_lesson(item) for item in doc["episodes"]]
    print(json.dumps({
        "pack": doc["package_id"],
        "status": "STORYBOARDS_VALIDATED_NOT_RENDERED",
        "episodes": outcomes,
        "uploads_attempted": 0,
        "youtube_schedule_confirmed": False,
        "monthly_new_cost_inr": 0
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
