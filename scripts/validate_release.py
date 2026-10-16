from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE = re.compile(r"(?<!\d)(?:\+?\d[\d .()-]{7,}\d)(?!\d)")
SECRET = re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*[^\s,;]{6,}")


def flatten(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from flatten(v)
    elif isinstance(value, list):
        for v in value:
            yield from flatten(v)
    elif isinstance(value, str):
        yield value


def validate(data: dict, blocked_literals: list[str], *, editorial_only: bool = False) -> list[str]:
    errors = []
    text = "\n".join(flatten(data))

    if EMAIL.search(text):
        errors.append("release contains an email address")
    # URLs and YYYY-MM-DD dates are not personal phone numbers.
    # Keep the full original text for email and secret detection.
    scan = re.sub(r"https?://[^\s]+", " ", text)
    scan = re.sub(r"\b(?:19|20)\d{2}[-/]\d{1,2}[-/]\d{1,2}\b", " ", scan)
    if PHONE.search(scan):
        errors.append("release contains a phone-like number")
    if SECRET.search(text):
        errors.append("release contains a likely secret/credential")

    lower = text.lower()
    for literal in blocked_literals:
        if literal.strip() and literal.lower() in lower:
            errors.append(f"release contains blocked personal identifier: {literal!r}")

    title = str(data.get("title", ""))
    description = str(data.get("description", ""))
    if not 1 <= len(title) <= 100:
        errors.append("YouTube title must be 1-100 characters")
    if len(description) > 5000:
        errors.append("YouTube description exceeds 5000 characters")

    if editorial_only:
        # A script/description is research-stage metadata, not a verified media release.
        # Do not let this path substitute for the strict release-ready gate.
        draft_script = data.get("source_script")
        if data.get("renderer") == "manifest_v2":
            scenes = data.get("scenes", [])
            if not isinstance(scenes, list) or not scenes:
                errors.append("manifest_v2 editorial draft requires scenes")
            else:
                for index, scene in enumerate(scenes, 1):
                    if not isinstance(scene, dict) or not str(scene.get("title", "")).strip() or not str(scene.get("narration", "")).strip():
                        errors.append(f"scene {index} needs a title and narration")
        elif not isinstance(draft_script, str) or not draft_script.strip():
            errors.append("editorial draft requires source_script")
        elif (draft_script.startswith("/") or ".." in draft_script.replace("\\\\", "/").split("/")
              or draft_script.startswith("~") or ":" in draft_script):
            errors.append("unsafe source_script path")
        return errors

    captions = data.get("captions", [])
    if not captions:
        if data.get("renderer") == "manifest_v2":
            scenes = data.get("scenes", [])
            if not scenes:
                errors.append("manifest_v2 episodes require scenes")
            for i, scene in enumerate(scenes, 1):
                if not str(scene.get("title", "")).strip():
                    errors.append(f"scene {i} is missing a title")
                if not str(scene.get("narration", "")).strip():
                    errors.append(f"scene {i} is missing narration")
        else:
            errors.append("captions are required")
    else:
        previous = -1.0
        for i, c in enumerate(captions, 1):
            start = float(c.get("start", -1))
            end = float(c.get("end", -1))
            if start < previous:
                errors.append(f"caption {i} starts before the previous caption")
            if end <= start:
                errors.append(f"caption {i} has invalid timing")
            previous = end

    return errors


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("episode_json", type=Path)
    ap.add_argument("--privacy", type=Path, default=Path("config/privacy.json"))
    ap.add_argument("--editorial-only", action="store_true",
                    help="Validate unpublishable preproduction metadata; never counts as media QA")
    args = ap.parse_args()

    data = json.loads(args.episode_json.read_text(encoding="utf-8"))
    privacy = json.loads(args.privacy.read_text(encoding="utf-8"))
    errors = validate(data, privacy.get("blocked_literals", []), editorial_only=args.editorial_only)
    if errors:
        for err in errors:
            print(f"BLOCK: {err}")
        raise SystemExit(1)
    print("editorial metadata validated; NOT authorized for publication" if args.editorial_only
          else "release-ready validation passed")


if __name__ == "__main__":
    main()
