"""FlowMinute Phase 4C: deterministic OFFLINE migration review preview.

Consumes caller-provided, NON-AUTHENTICATED metadata claims. No database access,
HTTP, D1, Google credential, LLM, upload, scheduling, or Cloudflare control.
All outputs are planning diagnostics; NONE authorizes any production migration.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from hashlib import sha256
from json import dumps
from typing import Mapping, Sequence
from zoneinfo import ZoneInfo

from .core import CHANNEL_ID
from .phase4b_readonly_audit import (
    AuditBlocked, _normalize_record, reconcile_claimed_releases,
)

IST = ZoneInfo("Asia/Kolkata")
AMBIGUOUS_STAGES = frozenset({
    "upload_started", "upload_uncertain", "schedule_unresolved",
    "schedule_uncertain",
})
REMOTE_STAGES = frozenset({
    "private_uploaded", "processing_succeeded", "remote_private_verified",
    "scheduled_verified", "public_verified",
})
SOURCES = ("private_sqlite_claim", "public_draft_claim", "d1_claim", "youtube_claim")


def _legacy_release_day(raw: Mapping) -> str | None:
    """Read the optional claimed IST day; never synthesize a legacy mapping."""
    value = raw.get("release_date")
    if value is None:
        return None
    if not isinstance(value, str) or len(value) != 10:
        raise AuditBlocked("Legacy release_date must be YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise AuditBlocked("Impossible legacy release_date") from exc
    if parsed.isoformat() != value:
        raise AuditBlocked("Canonical legacy release_date required")
    return value


def _slot_day_ist(utc_iso: str) -> str:
    return datetime.fromisoformat(utc_iso).astimezone(IST).date().isoformat()


def _fingerprint(value: object) -> str:
    return sha256(dumps(value, sort_keys=True, separators=(",", ":"),
                        ensure_ascii=True).encode("utf-8")).hexdigest()


def generate_migration_review_preview(claims: Sequence[Mapping]) -> dict:
    """Generate a no-SQL, no-write preview from UNTRUSTED source claims.

    Never use these results as a verified remote state: youtube_claim labels
    are caller supplied. Every candidate is blocked pending real authenticated
    readbacks, real D1 inventory, separately approved rollback and migrations.
    """
    if not isinstance(claims, (list, tuple)) or len(claims) > 5000:
        raise AuditBlocked("Bounded claim array required")
    base = reconcile_claimed_releases(claims)
    rows = []
    for original in claims:
        normalized = _normalize_record(original)
        normalized["legacy_release_date"] = _legacy_release_day(original)
        rows.append(normalized)

    by_episode: dict[str, list[dict]] = defaultdict(list)
    for item in rows:
        by_episode[item["episode_id"]].append(item)

    global_issues: dict[str, set[str]] = defaultdict(set)
    for issue in base["conflicts"]:
        problem = issue["problem"]
        targets = issue.get("episodes") or [issue["episode_id"]]
        for episode in targets:
            global_issues[episode].add(problem)

    candidates = []
    issue_histogram: dict[str, int] = defaultdict(int)
    for episode, observations in sorted(by_episode.items()):
        issues = set(global_issues[episode])
        source_names = tuple(sorted({x["source"] for x in observations}))
        stages = {x["stage"] for x in observations}
        legacy_days = {x["legacy_release_date"] for x in observations
                       if x["legacy_release_date"] is not None}
        if len(legacy_days) > 1:
            issues.add("CONTRADICTORY_LEGACY_RELEASE_DAY")
        if "d1_claim" not in source_names:
            issues.add("MISSING_LIVE_D1_METADATA_CLAIM")
        if "youtube_claim" not in source_names:
            issues.add("MISSING_YOUTUBE_METADATA_CLAIM")
        if stages & AMBIGUOUS_STAGES:
            issues.add("UNCERTAIN_REMOTE_OPERATION_REQUIRES_RECONCILIATION")
        if len(stages) > 1:
            issues.add("DIVERGENT_STAGE_OBSERVATIONS")
        if (stages & REMOTE_STAGES) and any(
            x["youtube_id"] is None for x in observations if x["stage"] in REMOTE_STAGES
        ):
            issues.add("REMOTE_STAGE_LACKS_EXACT_VIDEO_ID")
        if "public_verified" in stages and "quarantined" in stages:
            issues.add("PUBLIC_VS_QUARANTINE_CONTRADICTION")

        for item in observations:
            legacy_day, slot = item["legacy_release_date"], item["planned_utc"]
            if legacy_day is not None and slot is None:
                issues.add("LEGACY_DATE_WITHOUT_EXACT_RELEASE_SLOT")
            if legacy_day is not None and slot is not None:
                if _slot_day_ist(slot) != legacy_day:
                    issues.add("LEGACY_IST_RELEASE_DAY_MISMATCH")

        def unique(field):
            non_null = {x[field] for x in observations if x[field] is not None}
            return next(iter(non_null)) if len(non_null) == 1 else None

        for issue in issues:
            issue_histogram[issue] += 1
        candidate = {
            "channel_id": CHANNEL_ID,
            "episode_id": episode,
            "claimed_media_sha256": unique("media_sha256"),
            "claimed_youtube_id": unique("youtube_id"),
            "claimed_planned_utc": unique("planned_utc"),
            "claimed_legacy_release_date": next(iter(legacy_days))
                if len(legacy_days) == 1 else None,
            "source_labels_not_proof": list(source_names),
            "claimed_stages": sorted(stages),
            "issues": sorted(issues),
            "resolution": "QUARANTINE_PENDING_RECONCILIATION"
                if issues else "UNVERIFIED_CANDIDATE_REQUIRES_INDEPENDENT_REVIEW",
            "operator_review_required": True,
            "proposed_mutation": None,
        }
        candidates.append(candidate)

    digest = _fingerprint(candidates)
    return {
        "schema_version": 1,
        "phase": "PHASE4C_OFFLINE_PREVIEW_ONLY",
        "channel_id": CHANNEL_ID,
        "claim_count": len(rows),
        "episode_count": len(candidates),
        "candidates": candidates,
        "issue_counts": dict(sorted(issue_histogram.items())),
        "preview_sha256": digest,
        "requires_live_d1_schema": True,
        "requires_authenticated_youtube_readback": True,
        "requires_separate_migration_approval": True,
        "requires_documented_rollback": True,
        "trusted_live_evidence": False,
        "production_migration_ready": False,
        "production_upload_ready": False,
        "production_schedule_ready": False,
        "generated_sql": [],
        "database_mutations": 0,
        "network_calls": 0,
        "blockers": [
            "CLAIM_SOURCE_LABELS_ARE_NOT_PROVIDER_ATTESTATIONS",
            "UNVERIFIED_D1_SCHEMA_AND_HISTORICAL_RELEASE_HISTORY",
            "NO_TRUSTED_REMOTE_VIDEO_OWNERSHIP_OR_PROCESSING_READBACK",
            "NO_APPROVED_D1_MIGRATION_AND_ROLLBACK",
            "PRODUCTION_UPLOADS_AND_SCHEDULING_DISABLED",
        ],
    }
