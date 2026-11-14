"""CLIVOX V2 P10: source-free own-channel analytics provenance & learning gates.

REUSES original A10 synthetic Analytics parser and owner-only read-only
adapter. This module NEVER calls YouTube, loads OAuth credentials, processes
creator footage, or claims real Shorts engagement. It validates hypothetical
owner-only metric schemas, differentiates Studio-only metrics, and prepares
review timing without fake viral scores, causal winners or upload approval.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from scripts.branch3_v2_p5_synthetic_moment_proposals import CHANNEL
from scripts.branch3_v2_p9_private_first_preflight import (
    P9Denied, _closed_live_policies,
)
from scripts.branch3_a10_analytics import (
    AnalyticsDenied, METRICS, FIXTURE, POLICY, CATEGORIES,
    read_json, validate_policy, validate_dataset,
)
from scripts.branch3_a10_owner_readonly import (
    OwnerAnalyticsDenied, MAX_ROWS, fixture_report,
)

STAGE = "CLIVOX_V2_P10_SYNTHETIC_OWNER_METRIC_PROVENANCE_QA_ONLY"
PUBLISH_EXAMPLE = datetime(2027, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
WINDOW_HOURS = (24, 72, 168, 336)
STUDIO_NAMES = (
    "stayed_to_watch_percent",
    "shown_in_feed",
    "shorts_audience_retention_curve",
)
REQUIRED_METRICS = (
    "views", "engagedViews", "averageViewDuration",
    "averageViewPercentage", "shares", "subscribersGained",
)
ALLOWED_COHORTS = frozenset(CATEGORIES)
WINDOW_FIELDS = frozenset({
    "hours_after_hypothetical_publish",
    "hypothetical_checkpoint_utc",
    "real_video_publish_time_verified",
    "real_authenticated_snapshot_received",
    "youtube_data_availability_confirmed",
    "owner_editorial_review_completed",
    "performance_conclusion_allowed",
})
METRIC_FIELDS = frozenset({
    "metric", "source", "fixture_reported_value_count",
    "fixture_missing_value_count", "real_clivox_value",
    "can_infer_short_swipe_behaviour", "safe_for_cross_creator_comparison",
})
COHORT_FIELDS = frozenset({
    "category", "fixture_hook_A_count", "fixture_hook_B_count",
    "minimum_examples_per_arm", "real_video_samples",
    "experiment_randomized", "causal_winner_declared",
    "real_editorial_optimization_authorized",
})
REPORT_FIELDS = frozenset({
    "stage", "channel_id", "source_kind", "synthetic_fixture_only",
    "original_a10_offline_schema_validated",
    "p9_closed_rights_and_upload_gate_verified",
    "a10_owner_only_readonly_adapter_policy_respected",
    "hypothetical_record_count",
    "metric_provenance", "studio_only_metrics", "synthetic_cohort_review",
    "hypothetical_review_checkpoints",
    "public_report_exposes_private_video_ids",
    "real_analytics_oauth_verified", "real_google_requests",
    "real_clivox_metrics_observed", "live_owner_analytics_connected",
    "real_published_videos_observed", "creator_analytics_requested",
    "video_or_creator_ranking_performed", "public_api_derived_viral_score",
    "copyright_or_ypp_status_inferred", "retention_curve_verified",
    "shorts_feed_stayed_to_watch_verified",
    "synthetic_metrics_extrapolated_as_real",
    "cross_owner_metric_aggregation_performed",
    "experiment_causal_winner_declared",
    "auto_optimization_or_publication_authorized",
    "real_analysis_milestone_complete", "youtube_uploads",
    "youtube_publish_authorized", "status",
})


class P10Denied(ValueError):
    """Never promote test numbers, missing Studio metrics or fake consent."""


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise P10Denied("CLIVOX_V2_P10_DENIED_" + reason)


def closed_a10_and_p9() -> None:
    """Existing independent gates: real P9 release off and A10 OAuth absent."""
    _closed_live_policies()
    owner = fixture_report()
    require(type(owner) is dict and owner == {
        "stage": "A10_CLIVOX_OWNER_READONLY_ADAPTER_OFFLINE_NOT_CONNECTED",
        "channel_id": CHANNEL,
        "strict_dual_readonly_scopes_required": True,
        "channel_identity_before_reports_required": True,
        "analytics_report_sample_max_rows": MAX_ROWS,
        "real_owner_google_oauth_consent_completed": False,
        "real_analytics_report_checked": False,
        "actual_google_requests": 0,
        "real_clivox_video_metrics_observed": False,
        "youtube_upload_authorized": False,
        "youtube_schedule_authorized": False,
        "youtube_publish_authorized": False,
    }, "A10_OWNER_READONLY_ACTUAL_OAUTH_NOT_CONNECTED")


def synthetic_metric_availability(rows: list[dict]) -> list[dict]:
    """Inventory fields, not values or derived metrics; no private IDs emitted."""
    require(type(rows) is list and 0 < len(rows) <= 250, "ROW_COUNT")
    results = []
    require(tuple(METRICS) == REQUIRED_METRICS, "METRIC_CATALOG_CHANGED")
    for name in REQUIRED_METRICS:
        require(all(type(x) is dict and name in x
                    for x in rows), "METRIC_FIELD_MISSING")
        known = sum(x[name] is not None for x in rows)
        results.append({
            "metric": name, "source": "SYNTHETIC_A10_API_SHAPE_NOT_REAL",
            "fixture_reported_value_count": known,
            "fixture_missing_value_count": len(rows) - known,
            "real_clivox_value": None,
            "can_infer_short_swipe_behaviour": False,
            "safe_for_cross_creator_comparison": False,
        })
    return results


def synthetic_review_groups(rows: list[dict], *, threshold: int) -> list[dict]:
    """Only sample counts; no score, prediction, confounded winner or label."""
    require(type(threshold) is int and threshold == 10,
            "UNAPPROVED_SAMPLE_THRESHOLD")
    tally = Counter((r["category"], r["hook_variant"]) for r in rows)
    require(all(category in ALLOWED_COHORTS
                and variant in ("A", "B")
                for category, variant in tally), "COHORT_SCOPE")
    return [
        {
            "category": category,
            "fixture_hook_A_count": tally[(category, "A")],
            "fixture_hook_B_count": tally[(category, "B")],
            "minimum_examples_per_arm": threshold,
            "real_video_samples": 0,
            "experiment_randomized": False,
            "causal_winner_declared": False,
            "real_editorial_optimization_authorized": False,
        }
        for category in sorted({r["category"] for r in rows})
    ]


def hypothetical_checkpoints(*, template_publish_at: datetime =
                             PUBLISH_EXAMPLE) -> list[dict]:
    """24h/72h/7d/14d *sample* observation plan; no scheduled API requests."""
    require(type(template_publish_at) is datetime
            and template_publish_at == PUBLISH_EXAMPLE
            and template_publish_at.tzinfo is timezone.utc,
            "SYNTHETIC_DATE_ONLY")
    return [{
        "hours_after_hypothetical_publish": hours,
        "hypothetical_checkpoint_utc": (
            template_publish_at + timedelta(hours=hours)
        ).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "real_video_publish_time_verified": False,
        "real_authenticated_snapshot_received": False,
        "youtube_data_availability_confirmed": False,
        "owner_editorial_review_completed": False,
        "performance_conclusion_allowed": False,
    } for hours in WINDOW_HOURS]


def validate_report(report: object) -> dict:
    """Output cannot become public real-channel Analytics or an uploader."""
    require(type(report) is dict and set(report) == REPORT_FIELDS,
            "EXACT_PUBLIC_REPORT_SCHEMA")
    require(report["stage"] == STAGE and report["channel_id"] == CHANNEL
            and report["source_kind"] ==
            "OFFLINE_A10_SYNTHETIC_METRIC_SHAPE_ONLY"
            and report["status"] ==
            "NO_LIVE_CLIVOX_UPLOAD_OR_OWNER_ANALYTICS_NO_REAL_LEARNING",
            "NO_FAKE_REAL_STATUS")
    for k in (
        "synthetic_fixture_only",
        "original_a10_offline_schema_validated",
        "p9_closed_rights_and_upload_gate_verified",
        "a10_owner_only_readonly_adapter_policy_respected",
    ):
        require(report[k] is True, "MISSING_SYNTHETIC_GATE_" + k.upper())
    for k in (
        "public_report_exposes_private_video_ids",
        "real_analytics_oauth_verified",
        "real_clivox_metrics_observed", "live_owner_analytics_connected",
        "creator_analytics_requested",
        "video_or_creator_ranking_performed",
        "public_api_derived_viral_score",
        "copyright_or_ypp_status_inferred",
        "retention_curve_verified",
        "shorts_feed_stayed_to_watch_verified",
        "synthetic_metrics_extrapolated_as_real",
        "cross_owner_metric_aggregation_performed",
        "experiment_causal_winner_declared",
        "auto_optimization_or_publication_authorized",
        "real_analysis_milestone_complete",
        "youtube_publish_authorized",
    ):
        require(report[k] is False, "UNSAFE_REAL_FLAG_" + k.upper())
    for k in ("real_google_requests", "real_published_videos_observed",
              "youtube_uploads"):
        require(type(report[k]) is int and report[k] == 0,
                "FORGED_REAL_COUNT_" + k.upper())
    require(type(report["hypothetical_record_count"]) is int
            and 0 < report["hypothetical_record_count"] <= 250,
            "TEST_RECORD_COUNT")
    metrics = report["metric_provenance"]
    require(type(metrics) is list and len(metrics) == len(REQUIRED_METRICS)
            and [m.get("metric") for m in metrics] == list(REQUIRED_METRICS),
            "METRIC_PROVENANCE_FIELDS")
    for m in metrics:
        require(type(m) is dict and set(m) == METRIC_FIELDS
                and m["source"] == "SYNTHETIC_A10_API_SHAPE_NOT_REAL"
                and type(m["fixture_reported_value_count"]) is int
                and type(m["fixture_missing_value_count"]) is int
                and 0 <= m["fixture_reported_value_count"]
                and 0 <= m["fixture_missing_value_count"]
                and (m["fixture_reported_value_count"] +
                     m["fixture_missing_value_count"]) ==
                report["hypothetical_record_count"]
                and m["real_clivox_value"] is None
                and m["can_infer_short_swipe_behaviour"] is False
                and m["safe_for_cross_creator_comparison"] is False,
                "METRIC_CANNOT_PROMOTE")
    require(type(report["studio_only_metrics"]) is dict
            and set(report["studio_only_metrics"]) == set(STUDIO_NAMES)
            and all(report["studio_only_metrics"][k] is None
                    for k in STUDIO_NAMES),
            "STUDIO_DATA_NOT_AVAILABLE")
    groups = report["synthetic_cohort_review"]
    require(type(groups) is list and 0 < len(groups) <= len(CATEGORIES)
            and len(set(g.get("category") for g in groups)) == len(groups),
            "SYNTHETIC_COHORT_SCHEMA")
    for group in groups:
        require(type(group) is dict and set(group) == COHORT_FIELDS
                and group["category"] in CATEGORIES
                and type(group["fixture_hook_A_count"]) is int
                and type(group["fixture_hook_B_count"]) is int
                and group["fixture_hook_A_count"] >= 0
                and group["fixture_hook_B_count"] >= 0
                and group["minimum_examples_per_arm"] == 10
                and type(group["real_video_samples"]) is int
                and group["real_video_samples"] == 0
                and group["experiment_randomized"] is False
                and group["causal_winner_declared"] is False
                and group["real_editorial_optimization_authorized"] is False,
                "UNJUSTIFIED_EXPERIMENT_CLAIM")
    require(sum(g["fixture_hook_A_count"] +
                g["fixture_hook_B_count"] for g in groups) ==
            report["hypothetical_record_count"], "COHORTS_COUNT_MATCH")
    checkpoints = report["hypothetical_review_checkpoints"]
    require(type(checkpoints) is list and len(checkpoints) == 4,
            "CHECKPOINTS_COUNT")
    require(checkpoints == hypothetical_checkpoints()
            and all(type(v) is dict and set(v) == WINDOW_FIELDS
                    for v in checkpoints), "HYPOTHETICAL_NOT_LIVE_SCHEDULE")
    # Domain forbids private IDs, raw Analytics numeric values, external video
    # input, real Studio metrics, model-generated viral scores or OAuth tokens.
    raw = json.dumps(report, sort_keys=True, allow_nan=False)
    for forbidden in ("youtube.com/watch?", "access_token", "Bearer ",
                      "CLIVOX_ANALYTICS_REFRESH_TOKEN", "viral_probability",
                      "creator_video_url", "signed_creator_license"):
        require(forbidden not in raw, "FORBIDDEN_ANALYTICS_EXPORT")
    return report


def source_free_p10_report(dataset: dict, policy: dict) -> dict:
    """Connect existing A10 fixtures to P9 closed release and evidence gates."""
    closed_a10_and_p9()
    try:
        validate_policy(policy)
        records = validate_dataset(dataset)
    except (AnalyticsDenied, ValueError, TypeError, KeyError):
        raise P10Denied("CLIVOX_V2_P10_DENIED_A10_SOURCE_FIXTURE") from None
    require(dataset["hypothetical_observation_date"] == "2027-02-01"
            and dataset["window_days"] == 7
            and len(records) == 12, "FIXED_SOURCE_FREE_TEST")
    # No real YouTube Analytics response is supplied, ingested or exported.
    report = {
        "stage": STAGE, "channel_id": CHANNEL,
        "source_kind": "OFFLINE_A10_SYNTHETIC_METRIC_SHAPE_ONLY",
        "synthetic_fixture_only": True,
        "original_a10_offline_schema_validated": True,
        "p9_closed_rights_and_upload_gate_verified": True,
        "a10_owner_only_readonly_adapter_policy_respected": True,
        "hypothetical_record_count": len(records),
        "metric_provenance": synthetic_metric_availability(records),
        "studio_only_metrics": {name: None for name in STUDIO_NAMES},
        "synthetic_cohort_review": synthetic_review_groups(
            records, threshold=policy["minimum_examples_per_arm"]),
        "hypothetical_review_checkpoints": hypothetical_checkpoints(),
        "public_report_exposes_private_video_ids": False,
        "real_analytics_oauth_verified": False, "real_google_requests": 0,
        "real_clivox_metrics_observed": False,
        "live_owner_analytics_connected": False,
        "real_published_videos_observed": 0,
        "creator_analytics_requested": False,
        "video_or_creator_ranking_performed": False,
        "public_api_derived_viral_score": False,
        "copyright_or_ypp_status_inferred": False,
        "retention_curve_verified": False,
        "shorts_feed_stayed_to_watch_verified": False,
        "synthetic_metrics_extrapolated_as_real": False,
        "cross_owner_metric_aggregation_performed": False,
        "experiment_causal_winner_declared": False,
        "auto_optimization_or_publication_authorized": False,
        "real_analysis_milestone_complete": False,
        "youtube_uploads": 0, "youtube_publish_authorized": False,
        "status": "NO_LIVE_CLIVOX_UPLOAD_OR_OWNER_ANALYTICS_NO_REAL_LEARNING",
    }
    closed_a10_and_p9()
    return validate_report(report)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("closed", "synthetic"),
                        default="closed")
    args = parser.parse_args()
    try:
        closed_a10_and_p9()
        if args.mode == "closed":
            report = {
                "stage": "CLIVOX_V2_P10_NO_OWNER_ANALYTICS_NO_UPLOAD",
                "channel_id": CHANNEL,
                "real_analytics_oauth_verified": False,
                "real_google_requests": 0,
                "youtube_uploads": 0,
                "real_analysis_milestone_complete": False,
            }
        else:
            report = source_free_p10_report(
                read_json(FIXTURE), read_json(POLICY))
        print(json.dumps(report, sort_keys=True, allow_nan=False))
    except (P10Denied, P9Denied, AnalyticsDenied, OwnerAnalyticsDenied,
            OSError, ValueError, KeyError, TypeError, UnicodeError):
        raise SystemExit(
            "CLIVOX_V2_P10_BLOCKED_NO_REAL_OWNED_ANALYTICS_AND_NO_UPLOAD"
        ) from None


if __name__ == "__main__":
    main()
