"""Branch 1 viewer-first recovery: editorial proof gates and privacy-safe cohort analysis.

No YouTube OAuth, uploads, publishing, client records or guarantee of virality.
Only source-free briefs and aggregate, age-matched local Studio metrics.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

SCHEMA = "FLOWMINUTE_B1_RETENTION_FIRST_V1"
ROLES = {"hook", "demonstration", "cause", "fix", "payoff", "takeaway"}
FORMATS = {"short", "long"}
SERIES = {"excel_sheets", "privacy_browser", "python_automation"}
HEX = re.compile(r"^[0-9a-f]{64}$")
EPISODE = re.compile(r"^fm_[a-z0-9_]{8,64}$")
VIDEO = re.compile(r"^[A-Za-z0-9_-]{11}$")
COLUMNS = (
    "video_id", "format", "series", "age_hours", "duration_seconds",
    "views", "engaged_views", "shown_in_feed", "stayed_to_watch_pct",
    "impressions", "impressions_ctr_pct", "average_view_duration_seconds",
    "subscribers_gained", "retention_3s_pct", "retention_30s_pct",
)
OPTIONAL = {"shown_in_feed", "stayed_to_watch_pct", "impressions",
            "impressions_ctr_pct", "retention_3s_pct", "retention_30s_pct"}
BASELINE = {
    "short_stayed_to_watch_pct": 21.2,
    "long_average_view_duration_seconds": 58.0,
}
MIN_VIDEOS = 5
MIN_SHORT_FEED_EXPOSURES = 500
MIN_LONG_IMPRESSIONS = 500
MIN_LONG_VIEWS = 100

class RecoveryRefused(ValueError):
    """Refuse unproved creative work or ambiguous audience data."""

def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RecoveryRefused(reason)

def _number(value, name: str, *, minimum=0, maximum=1_000_000_000):
    require(type(value) in (int, float) and math.isfinite(value)
            and minimum <= value <= maximum, "INVALID_" + name)
    return float(value)

def _plain(value, limit: int, name: str):
    require(type(value) is str and 1 <= len(value.strip()) <= limit
            and value == value.strip() and "\n" not in value
            and "<" not in value and ">" not in value, "INVALID_" + name)
    return value

def validate_creative(brief: dict) -> dict:
    """Enforce an observable proof-first narrative; never manufacture approval."""
    require(type(brief) is dict and set(brief) == {
        "schema", "episode_id", "format", "series", "duration_seconds",
        "title", "viewer_problem", "viewer_promise", "source_url",
        "beats", "demo", "approval",
    }, "CREATIVE_SCHEMA_MISMATCH")
    require(brief["schema"] == SCHEMA
            and type(brief["episode_id"]) is str
            and EPISODE.fullmatch(brief["episode_id"]) is not None
            and brief["format"] in FORMATS and brief["series"] in SERIES,
            "CREATIVE_ID_FORMAT_OR_SERIES")
    duration = _number(brief["duration_seconds"], "DURATION", minimum=10,
                       maximum=90 if brief["format"] == "short" else 1200)
    _plain(brief["title"], 100, "TITLE")
    _plain(brief["viewer_problem"], 250, "PROBLEM")
    _plain(brief["viewer_promise"], 250, "PROMISE")
    require(type(brief["source_url"]) is str
            and brief["source_url"].startswith("https://")
            and not re.search(r"[\s<>]", brief["source_url"]),
            "SOURCE_MUST_BE_HTTPS")
    demo = brief["demo"]
    require(type(demo) is dict
            and set(demo) == {"mode", "application", "fixture_only",
                              "recording_provenance", "local_only"}
            and demo["mode"] == "real_software_capture"
            and demo["application"] in ("Python terminal", "LibreOffice Calc",
                                         "Chromium browser")
            and demo["fixture_only"] is True
            and demo["local_only"] is True
            and demo["recording_provenance"] == "first_party_executed_software",
            "REAL_DEMONSTRATION_REQUIRED")
    require(brief["approval"] == {
        "owner_watched_exact_video": False, "rights_reviewed": False,
        "facts_reviewed": False, "release_signed": False,
        "youtube_scheduled": False,
    }, "CREATIVE_MUST_STAY_UNAPPROVED")
    beats = brief["beats"]
    require(type(beats) is list and 4 <= len(beats) <= 12,
            "MISSING_OR_MASS_PRODUCED_BEATS")
    prev = 0.0
    seen = []
    demo_start = []
    payoffs = []
    for index, beat in enumerate(beats):
        require(type(beat) is dict and set(beat) == {
            "role", "start_seconds", "end_seconds", "visual_evidence",
            "spoken_purpose", "action_or_result",
        }, "BEAT_SCHEMA_MISMATCH")
        role = beat["role"]
        require(role in ROLES, "INVALID_BEAT_ROLE")
        start = _number(beat["start_seconds"], "BEAT_START", maximum=duration)
        end = _number(beat["end_seconds"], "BEAT_END", maximum=duration)
        require(abs(start - prev) <= .05 and end > start + .20,
                "BEAT_GAP_OR_NEGATIVE_LENGTH")
        _plain(beat["spoken_purpose"], 260, "PURPOSE")
        _plain(beat["action_or_result"], 260, "ACTION")
        require(beat["visual_evidence"] == "actual_executed_software_frame",
                "DECORATIVE_OR_FICTITIOUS_EVIDENCE")
        prev = end
        seen.append(role)
        if role == "demonstration":
            demo_start.append(start)
        if role == "payoff":
            payoffs.append(start)
        if index == 0:
            require(role == "hook" and abs(start) <= .05 and end <= 2.0,
                    "OPEN_WITH_PROOF_WITHIN_TWO_SECONDS")
    require(abs(prev - duration) <= .05, "BEATS_MUST_COVER_WHOLE_VIDEO")
    require(demo_start and min(demo_start) <= 3.0,
            "FIRST_REAL_ACTION_TOO_LATE")
    require(payoffs and min(payoffs) >= min(demo_start)
            and min(payoffs) <= .85 * duration,
            "PAYOFF_MUST_BE_VISIBLE_BEFORE_END")
    require("fix" in seen and seen.index("fix") < seen.index("payoff"),
            "FIX_BEFORE_PAYOFF_REQUIRED")
    require("takeaway" in seen and seen[-1] == "takeaway",
            "END_WITH_A_USEFUL_RULE")
    return {
        "status": "CREATIVE_BRIEF_VALIDATED_NOT_RELEASE_APPROVED",
        "episode_id": brief["episode_id"],
        "format": brief["format"],
        "series": brief["series"],
        "duration_seconds": duration,
        "opening_proof_by_seconds": beats[0]["end_seconds"],
        "first_real_action_at_seconds": min(demo_start),
        "visible_payoff_at_seconds": min(payoffs),
        "narrative_beats": len(beats),
        "owner_approval": False, "youtube_uploads": 0,
    }

def verify_capture(brief: dict, capture: Path, receipt: Path, *, windows_evidence: Path | None = None) -> dict:
    """Bound a genuine capture by actual file bytes AND a closed local receipt.

    A hash proves file identity, NOT that a screen recording is pedagogically
    compelling or that a UI truly represents a vendor's production application.
    """
    summary = validate_creative(brief)
    require(capture.is_file() and not capture.is_symlink()
            and 30_000 <= capture.stat().st_size <= 100_000_000
            and receipt.is_file() and not receipt.is_symlink()
            and receipt.stat().st_size < 8192, "MISSING_EXACT_MEDIA_PROOF")
    r = json.loads(receipt.read_text("utf8"))
    if type(r) is dict and r.get("schema") == "FLOWMINUTE_B1_WINDOWS_CONTINUOUS_CAPTURE_V2":
        from autopilot.branch1_windows_capture import verify_windows
        return {**summary, **verify_windows(brief, capture, r, windows_evidence, require)}
    require(windows_evidence is None, "WINDOWS_EVIDENCE_WITH_LEGACY_RECEIPT")
    require(type(r) is dict and set(r) == {
        "schema", "status", "episode_id", "capture_sha256",
        "capture_bytes", "fixture_sha256", "capture_method",
        "private_data", "youtube_uploads", "release_approved",
    }, "CAPTURE_RECEIPT_SCHEMA")
    require(r["schema"] == "FLOWMINUTE_B1_REAL_CAPTURE_V1"
            and r["status"] == "ACTUAL_FIRST_PARTY_TERMINAL_CAPTURE_REVIEW_ONLY"
            and r["episode_id"] == brief["episode_id"]
            and r["capture_method"] == "xvfb_xterm_ffmpeg_live"
            and r["private_data"] is False
            and r["youtube_uploads"] == 0
            and r["release_approved"] is False
            and type(r["capture_bytes"]) is int
            and r["capture_bytes"] == capture.stat().st_size
            and type(r["capture_sha256"]) is str
            and HEX.fullmatch(r["capture_sha256"])
            and type(r["fixture_sha256"]) is str
            and HEX.fullmatch(r["fixture_sha256"])
            and hashlib.sha256(capture.read_bytes()).hexdigest() == r["capture_sha256"],
            "EXACT_CAPTURE_PROVENANCE_FAILED")
    return {**summary, "capture_status": "EXACT_HASH_VERIFIED_REVIEW_ONLY",
            "capture_sha256": r["capture_sha256"], "owner_approval": False}

def _int(s: str, name: str, *, allow_blank=False):
    if s == "" and allow_blank:
        return None
    require(type(s) is str and re.fullmatch(r"\d{1,10}", s) is not None,
            "INVALID_INTEGER_" + name)
    return int(s)

def _float(s: str, name: str, *, allow_blank=False):
    if s == "" and allow_blank:
        return None
    require(type(s) is str and re.fullmatch(r"\d{1,8}(?:\.\d{1,5})?", s) is not None,
            "INVALID_NUMBER_" + name)
    v = float(s)
    require(math.isfinite(v), "INVALID_NUMBER_" + name)
    return v

def parse_metrics_csv(path: Path) -> list[dict]:
    """Import only explicitly curated numeric Studio metrics; no raw export PII."""
    require(path.is_file() and not path.is_symlink()
            and 0 < path.stat().st_size <= 150_000, "METRICS_FILE_UNSAFE")
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == list(COLUMNS), "UNEXPECTED_CSV_HEADER_OR_PRIVATE_DATA")
        rows = []
        seen = set()
        for row in reader:
            require(len(rows) < 500 and None not in row
                    and set(row) == set(COLUMNS), "METRICS_ROW_SCHEMA")
            require(VIDEO.fullmatch(row["video_id"] or "") is not None
                    and row["video_id"] not in seen
                    and row["format"] in FORMATS
                    and row["series"] in SERIES, "VIDEO_ID_OR_SERIES_INVALID")
            seen.add(row["video_id"])
            fmt = row["format"]
            r = {"format": fmt, "series": row["series"]}
            for key in ("views", "engaged_views", "shown_in_feed",
                        "impressions", "subscribers_gained"):
                r[key] = _int(row[key], key, allow_blank=(key in OPTIONAL))
            for key in ("age_hours", "duration_seconds",
                        "stayed_to_watch_pct", "impressions_ctr_pct",
                        "average_view_duration_seconds",
                        "retention_3s_pct", "retention_30s_pct"):
                r[key] = _float(row[key], key, allow_blank=(key in OPTIONAL))
            require(0 <= r["age_hours"] <= 720 and
                    (10 <= r["duration_seconds"] <=
                     (180 if fmt == "short" else 7200)) and
                    r["engaged_views"] <= r["views"] and
                    r["average_view_duration_seconds"] <= 86400,
                    "IMPOSSIBLE_VIEW_DATA")
            for key in ("stayed_to_watch_pct", "impressions_ctr_pct",
                        "retention_3s_pct", "retention_30s_pct"):
                require(r[key] is None or 0 <= r[key] <= 100,
                        "PERCENT_OUT_OF_RANGE")
            if fmt == "short":
                require(r["impressions"] is None
                        and r["impressions_ctr_pct"] is None
                        and (r["stayed_to_watch_pct"] is None
                             or r["shown_in_feed"] is not None
                             and r["shown_in_feed"] > 0), "SHORTS_VIEW_METRIC_MISMATCH")
            else:
                require(r["shown_in_feed"] is None
                        and r["stayed_to_watch_pct"] is None
                        and (r["impressions_ctr_pct"] is None
                             or r["impressions"] is not None
                             and r["impressions"] > 0), "LONG_VIEW_METRIC_MISMATCH")
            rows.append(r)
    require(rows, "EMPTY_METRICS_DATASET")
    return rows

def analyze_72h(rows: list[dict]) -> dict:
    """72h +/-12h descriptive cohort rollups, never cross-format or causal."""
    cohorts = []
    for fmt in ("short", "long"):
        for series in sorted(SERIES):
            subset = [r for r in rows if r["format"] == fmt
                      and r["series"] == series
                      and 60 <= r["age_hours"] <= 84]
            if not subset:
                continue
            v = sum(r["views"] for r in subset)
            engaged = sum(r["engaged_views"] for r in subset)
            subs = sum(r["subscribers_gained"] for r in subset)
            completion = statistics.median(
                r["average_view_duration_seconds"]/r["duration_seconds"]
                for r in subset)
            data = {"format": fmt, "series": series,
                    "age_window_hours": "60-84",
                    "videos": len(subset), "views": v,
                    "engaged_views": engaged, "subscribers_gained": subs,
                    "median_avg_duration_over_length": round(completion, 4),
                    "subscribers_per_1000_engaged":
                        round(1000*subs/engaged, 2) if engaged else None,
                    "status": "INSUFFICIENT_SAMPLE",
                    "suggestion": "Gather more age-matched, source-verified metrics."}
            if fmt == "short":
                valid = [r for r in subset if r["shown_in_feed"] is not None
                         and r["stayed_to_watch_pct"] is not None]
                exposure = sum(r["shown_in_feed"] for r in valid)
                data["shown_in_feed_with_valid_stay_pct"] = exposure
                data["weighted_stayed_to_watch_pct"] = (
                    round(sum(r["shown_in_feed"]*r["stayed_to_watch_pct"]
                              for r in valid)/exposure, 2)
                    if exposure else None)
                eligible = (len(valid) == len(subset)
                            and len(subset) >= MIN_VIDEOS
                            and exposure >= MIN_SHORT_FEED_EXPOSURES
                            and engaged >= 100)
                if eligible:
                    data["status"] = "DESCRIPTIVE_EXPERIMENT_ELIGIBLE"
                    data["suggestion"] = (
                        "Test one alternate opening with actual software proof; "
                        "compare after the same age window, not raw views.")
            else:
                valid = [r for r in subset if r["impressions"] is not None
                         and r["impressions_ctr_pct"] is not None]
                impressions = sum(r["impressions"] for r in valid)
                data["impressions_with_valid_ctr"] = impressions
                data["weighted_impressions_ctr_pct"] = (
                    round(sum(r["impressions"]*r["impressions_ctr_pct"]
                              for r in valid)/impressions, 2)
                    if impressions else None)
                eligible = (len(valid) == len(subset)
                            and len(subset) >= MIN_VIDEOS
                            and impressions >= MIN_LONG_IMPRESSIONS
                            and v >= MIN_LONG_VIEWS)
                if eligible:
                    data["status"] = "DESCRIPTIVE_EXPERIMENT_ELIGIBLE"
                    data["suggestion"] = (
                        "Review first-30-second retention and test a "
                        "proof-first opening; CTR is not a retention metric.")
            cohorts.append(data)
    return {
        "schema": "FLOWMINUTE_B1_AGGREGATE_ANALYTICS_V1",
        "status": "OBSERVATIONAL_NOT_CAUSAL",
        "baseline_previous_studio_observation": BASELINE,
        "cohorts": cohorts,
        "guardrails": [
            "No individual video IDs, URLs, comments, emails or audience PII are exported.",
            "Shorts stayed_to_watch_pct is NEVER engaged_views / views.",
            "No recommendation or winning niche from insufficient 72-hour samples.",
            "Do not upload or schedule video based on an analytics score."
        ],
        "youtube_uploads": 0,
        "youtube_schedules": 0,
    }

def main():
    cli = argparse.ArgumentParser(description="Offline viewer-first QA; no YouTube access")
    cli.add_argument("--creative", type=Path)
    cli.add_argument("--capture", type=Path)
    cli.add_argument("--capture-receipt", type=Path)
    cli.add_argument("--windows-evidence", type=Path)
    cli.add_argument("--studio-csv", type=Path)
    args = cli.parse_args()
    require(not args.windows_evidence or (args.creative and args.capture and args.capture_receipt), "WINDOWS_EVIDENCE_REQUIRES_CAPTURE")
    if args.creative:
        brief = json.loads(args.creative.read_text("utf8"))
        result = (verify_capture(brief, args.capture, args.capture_receipt, windows_evidence=args.windows_evidence)
                  if args.capture and args.capture_receipt else
                  validate_creative(brief))
        require(bool(args.capture) == bool(args.capture_receipt),
                "CAPTURE_AND_RECEIPT_MUST_BE_PAIRED")
    elif args.studio_csv and not args.capture and not args.capture_receipt:
        result = analyze_72h(parse_metrics_csv(args.studio_csv))
    else:
        cli.error("Supply --creative or --studio-csv (not both)")
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
