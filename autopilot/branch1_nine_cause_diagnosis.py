"""Privacy-safe nine-cause growth diagnostic. A media QA pass is not audience recovery.

Inputs are curated, local Studio exports. Source figures must come from Studio,
never guessed from public views or manufactured as a percentage.
No OAuth, YouTube writes, personal audience data, or automatic release.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
from statistics import median

from autopilot.branch1_recovery import (
    BASELINE, RecoveryRefused, analyze_72h, parse_metrics_csv, require,
)

TRAFFIC_COLUMNS = (
    "period", "format", "views", "suggested_views", "search_views",
    "browse_views", "shorts_feed_views", "external_views", "other_views",
)
TRAFFIC_TYPES = ("suggested_views", "search_views", "browse_views",
                 "shorts_feed_views", "external_views", "other_views")
CAUSES = (
    "weak_shorts_hook", "weak_long_retention", "weak_suggested_discovery",
    "low_subscriber_conversion", "scattered_topic_language",
    "repetitive_visuals", "non_demonstrative_look",
    "volume_before_quality", "weak_packaging",
)

def parse_traffic_csv(path: Path) -> dict:
    """Only anonymous, comparable 60-84-hour traffic totals by format/period."""
    require(path.is_file() and not path.is_symlink()
            and 0 < path.stat().st_size <= 12000, "TRAFFIC_FILE_UNSAFE")
    seen = {}
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        require(tuple(reader.fieldnames or ()) == TRAFFIC_COLUMNS,
                "TRAFFIC_HEADER_OR_PRIVATE_COLUMNS")
        for row in reader:
            require(None not in row and set(row) == set(TRAFFIC_COLUMNS),
                    "TRAFFIC_ROW_SCHEMA")
            period, fmt = row["period"], row["format"]
            require(period in ("baseline", "recovery")
                    and fmt in ("short", "long")
                    and (period, fmt) not in seen,
                    "TRAFFIC_PERIOD_OR_FORMAT_INVALID")
            numbers = {}
            for key in ("views",) + TRAFFIC_TYPES:
                value = row[key]
                require(type(value) is str and value.isascii()
                        and value.isdecimal() and len(value) <= 10,
                        "TRAFFIC_COUNT_NOT_STUDIO_INTEGER")
                numbers[key] = int(value)
                require(0 <= numbers[key] <= 1_000_000_000,
                        "TRAFFIC_COUNT_OUT_OF_RANGE")
            require(sum(numbers[k] for k in TRAFFIC_TYPES) == numbers["views"],
                    "TRAFFIC_SOURCES_MUST_SUM_TO_VIEWS")
            seen[period, fmt] = numbers
            require(len(seen) <= 4, "TOO_MANY_TRAFFIC_COHORTS")
    require(bool(seen), "EMPTY_TRAFFIC_CSV")
    return seen

def diagnosis(rows: list[dict], source_totals: dict | None = None) -> dict:
    """Never infer a growth fix from a source-code check or small dataset."""
    require(type(rows) is list and bool(rows), "STUDIO_COHORT_REQUIRED")
    source_totals = source_totals or {}
    require(type(source_totals) is dict, "BAD_TRAFFIC_SOURCE_DATA")
    rollup = analyze_72h(rows)
    cohorts = rollup["cohorts"]
    statuses = {
        key: {"status": "NEEDS_REAL_AUDIENCE_EVIDENCE",
              "evidence": "No age-matched published recovery experiment proves this cause resolved."}
        for key in CAUSES
    }
    short = [c for c in cohorts if c["format"] == "short"
             and c["status"] == "DESCRIPTIVE_EXPERIMENT_ELIGIBLE"]
    long = [c for c in cohorts if c["format"] == "long"
            and c["status"] == "DESCRIPTIVE_EXPERIMENT_ELIGIBLE"]
    if short:
        better = [c for c in short
                  if c.get("weighted_stayed_to_watch_pct") is not None
                  and c["weighted_stayed_to_watch_pct"]
                  > BASELINE["short_stayed_to_watch_pct"]]
        if better:
            statuses["weak_shorts_hook"] = {
                "status": "DESCRIPTIVE_SIGNAL_ONLY",
                "evidence": "Recovery Shorts chose-to-watch exceeded historical 21.2% in eligible cohorts; this is not causal proof."
            }
    if long:
        qualifying = [r for r in rows if r["format"] == "long"
                      and 60 <= r["age_hours"] <= 84
                      and r["average_view_duration_seconds"] >= 0]
        if qualifying and median(r["average_view_duration_seconds"]
                                 for r in qualifying) > BASELINE["long_average_view_duration_seconds"]:
            statuses["weak_long_retention"] = {
                "status": "DESCRIPTIVE_SIGNAL_ONLY",
                "evidence": "Median long watch duration exceeded the historical 58s reference; verify 30s audience retention."
            }
        if any(c.get("weighted_impressions_ctr_pct") is not None
               and c["weighted_impressions_ctr_pct"] > 4.8 for c in long):
            statuses["weak_packaging"] = {
                "status": "DESCRIPTIVE_SIGNAL_ONLY",
                "evidence": "Recovery long-form CTR exceeded historical 4.8%; impressions, traffic mix and watch time still matter."
            }
    for fmt in ("short", "long"):
        base = source_totals.get(("baseline", fmt))
        trial = source_totals.get(("recovery", fmt))
        if (base and trial and base["views"] >= 200 and trial["views"] >= 200
                and trial["suggested_views"] * base["views"]
                > base["suggested_views"] * trial["views"]):
            statuses["weak_suggested_discovery"] = {
                "status": "DESCRIPTIVE_SIGNAL_ONLY",
                "evidence": "Suggested share increased in comparable owner-supplied traffic cohorts; distribution recovery not established."
            }
    matched = [r for r in rows if 60 <= r["age_hours"] <= 84]
    if (len(matched) >= 5 and sum(r["engaged_views"] for r in matched) >= 100
            and sum(r["subscribers_gained"] for r in matched) > 0):
        statuses["low_subscriber_conversion"] = {
            "status": "DESCRIPTIVE_SIGNAL_ONLY",
            "evidence": "Observed some subscriber gains in a matched sample; sustained conversion not established."
        }
    return {
        "schema": "FLOWMINUTE_B1_NINE_CAUSES_EVIDENCE_ONLY_V1",
        "status": "NOT_VALIDATED_AS_GROWTH_RECOVERY",
        "issues": statuses,
        "issues_count": len(statuses),
        "proven_fixed_count": 0,
        "technical_qa_not_audience_retention": True,
        "topic_language_requires_real_cohort_experiment": True,
        "visual_and_originality_require_exact_video_human_review": True,
        "automatic_publishing_approved": False,
        "youtube_uploads": 0,
        "youtube_schedules": 0,
    }

def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only nine-cause growth evidence; NEVER publish")
    parser.add_argument("--studio-csv", type=Path, required=True)
    parser.add_argument("--traffic-csv", type=Path)
    args = parser.parse_args()
    rows = parse_metrics_csv(args.studio_csv)
    traffic = parse_traffic_csv(args.traffic_csv) if args.traffic_csv else {}
    print(json.dumps(diagnosis(rows, traffic), indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
