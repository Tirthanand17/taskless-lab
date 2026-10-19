"""Phase 5I: production D1 migration ADMISSION SCREEN, NOT a migrator.

Offline review of strictly sanitized, caller-supplied observations only.
Even internally consistent fake evidence never authorizes a production write.
No D1 queries, OAuth, Cloudflare API, checkout, migrations, SQL generation,
YouTube requests, environment-variable lookup, or sensitive record output.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

CHANNEL_ID = "UCCcL9Q_jqVq6LJmnYUSAFZA"
SOURCE_TRUST = "CALLER_ASSERTED_NO_PROVIDER_ATTESTATION"
FIELDS = frozenset(("channel_id","d1","time_travel","writer","youtube","budget","approvals"))
D1_FIELDS = frozenset(("release_rows","event_rows","duplicate_slot_groups",
                       "youtube_id_unique_verified","date_slot_unique_verified",
                       "canonical_schema_verified","snapshot_at_utc"))
TRAVEL_FIELDS = frozenset(("dashboard_time_travel_visible","reported_retention_days",
                          "production_storage_backend_verified","bookmark_recorded_privately",
                          "independent_backup_recovery_proven",
                          "disposable_restore_drill_proven"))
WRITER_FIELDS = frozenset(("all_writers_identified","writers_frozen",
                          "fencing_lease_verified","conflicting_writer_absent"))
YOUTUBE_FIELDS = frozenset(("three_distinct_receipts_confirmed",
                            "channel_title_processing_checked",
                            "private_video_ids_protected",
                            "all_three_media_hashes_verified",
                            "last_owner_readback_utc"))
BUDGET_FIELDS = frozenset(("workers_free_plan_account_verified",
                           "no_paid_upgrade_authorized","no_new_service_connected",
                           "global_zero_spend_control_verified"))
APPROVAL_FIELDS = frozenset(("owner_approved_prod_d1_write",
                             "maintenance_window_approved","migration_diff_approved",
                             "rollback_plan_independently_approved"))
ALL_BOOL = {
    "d1":D1_FIELDS-{"release_rows","event_rows","duplicate_slot_groups","snapshot_at_utc"},
    "time_travel":TRAVEL_FIELDS-{"reported_retention_days"},
    "writer":WRITER_FIELDS,
    "youtube":YOUTUBE_FIELDS-{"last_owner_readback_utc"},
    "budget":BUDGET_FIELDS,
    "approvals":APPROVAL_FIELDS,
}
MAX_FRESHNESS = timedelta(minutes=30)


class ReadinessHold(ValueError):
    """Fixed error code; do not interpolate potentially private input."""


def _exact(value:Any, keys:frozenset[str], code:str)->dict:
    if not isinstance(value,dict) or set(value)!=keys:
        raise ReadinessHold(code)
    return value


def _utc(value:Any)->datetime:
    if (not isinstance(value,str) or len(value)>32 or
        not value.endswith("Z") or "T" not in value):
        raise ReadinessHold("INVALID_UTC_METADATA")
    try:
        result=datetime.fromisoformat(value.replace("Z","+00:00"))
        if result.utcoffset()!=timedelta(0):
            raise ValueError
        return result.astimezone(timezone.utc)
    except (ValueError,OverflowError):
        raise ReadinessHold("INVALID_UTC_METADATA") from None


def _count(value:Any)->int:
    if type(value) is not int or not (0<=value<=10000000):
        raise ReadinessHold("INVALID_AGGREGATE_COUNT")
    return value


def inspect(snapshot:Mapping[str,Any],*,now:datetime)->dict:
    """Evaluate independent approvals still needed before an actual migration.

    The returned review-ready status is about untrusted claims only. It can
    NEVER confer authority to run a D1 mutation, even if every boolean is True.
    """
    _exact(snapshot,FIELDS,"INVALID_TOP_LEVEL")
    if not isinstance(now,datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ReadinessHold("TRUSTED_AWARE_CLOCK_REQUIRED")
    now=now.astimezone(timezone.utc)
    if snapshot["channel_id"]!=CHANNEL_ID:
        raise ReadinessHold("WRONG_OWNER_CHANNEL")
    parts={}
    for name,expected in (
        ("d1",D1_FIELDS),("time_travel",TRAVEL_FIELDS),
        ("writer",WRITER_FIELDS),("youtube",YOUTUBE_FIELDS),
        ("budget",BUDGET_FIELDS),("approvals",APPROVAL_FIELDS)
    ):
        parts[name]=_exact(snapshot[name],expected,"INVALID_"+name.upper()+"_SHAPE")
    for name,keys in ALL_BOOL.items():
        for key in keys:
            if type(parts[name][key]) is not bool:
                raise ReadinessHold("INVALID_BOOLEAN_EVIDENCE")
    d1=parts["d1"]
    d1_counts={k:_count(d1[k]) for k in
               ("release_rows","event_rows","duplicate_slot_groups")}
    retention=parts["time_travel"]["reported_retention_days"]
    if type(retention) is not int or retention<0 or retention>365:
        raise ReadinessHold("INVALID_TIME_TRAVEL_RETENTION")
    schema_at=_utc(d1["snapshot_at_utc"])
    youtube_at=_utc(parts["youtube"]["last_owner_readback_utc"])
    blocks=[]
    if d1_counts["duplicate_slot_groups"]!=0:
        blocks.append("LIVE_DUPLICATE_SLOT_CONFLICT")
    if d1_counts["release_rows"]!=0 or d1_counts["event_rows"]!=0:
        blocks.append("CANONICAL_ROWS_REQUIRE_FRESH_RECONCILIATION")
    if not d1["youtube_id_unique_verified"] or not d1["canonical_schema_verified"]:
        blocks.append("LIVE_CANONICAL_SCHEMA_OR_UNIQUE_VIDEO_INDEX_UNVERIFIED")
    # Already having a unique slot index is schema drift from current plan:
    # the new migration should be reviewed as a different operation.
    if d1["date_slot_unique_verified"]:
        blocks.append("UNEXPECTED_EXISTING_DATE_SLOT_INDEX_RECHECK_PLAN")
    if schema_at>now or now-schema_at>MAX_FRESHNESS:
        blocks.append("LIVE_D1_EVIDENCE_NOT_FRESH")
    travel=parts["time_travel"]
    if not travel["dashboard_time_travel_visible"] or retention!=7:
        blocks.append("EXPECTED_SEVEN_DAY_RECOVERY_WINDOW_UNVERIFIED")
    if not travel["production_storage_backend_verified"]:
        blocks.append("PRODUCTION_BACKEND_VERSION_UNVERIFIED")
    if not travel["bookmark_recorded_privately"]:
        blocks.append("RECOVERY_BOOKMARK_NOT_CUSTODIED")
    if not travel["independent_backup_recovery_proven"]:
        blocks.append("INDEPENDENT_BACKUP_NOT_VERIFIED")
    if not travel["disposable_restore_drill_proven"]:
        blocks.append("DISPOSABLE_RESTORE_DRILL_NOT_PROVEN")
    writer=parts["writer"]
    if not writer["all_writers_identified"] or not writer["writers_frozen"]:
        blocks.append("SINGLE_WRITER_FREEZE_NOT_VERIFIED")
    if not writer["fencing_lease_verified"] or not writer["conflicting_writer_absent"]:
        blocks.append("FENCED_CAS_AND_NO_CONFLICTING_WRITER_NOT_VERIFIED")
    youtube=parts["youtube"]
    if not all(youtube[k] for k in YOUTUBE_FIELDS-{"last_owner_readback_utc"}):
        blocks.append("OWNER_VIDEO_AND_MEDIA_PROVENANCE_INCOMPLETE")
    if youtube_at>now or now-youtube_at>MAX_FRESHNESS:
        blocks.append("OWNER_READBACK_NOT_FRESH")
    budget=parts["budget"]
    if not budget["workers_free_plan_account_verified"] or \
       not budget["no_paid_upgrade_authorized"] or \
       not budget["no_new_service_connected"]:
        blocks.append("FREE_PLAN_OR_CHARGE_PROTECTION_UNVERIFIED")
    if not budget["global_zero_spend_control_verified"]:
        blocks.append("ACCOUNT_WIDE_ZERO_SPEND_CAP_UNPROVEN")
    approvals=parts["approvals"]
    if not approvals["owner_approved_prod_d1_write"]:
        blocks.append("EXPLICIT_PRODUCTION_D1_WRITE_APPROVAL_MISSING")
    if not approvals["maintenance_window_approved"]:
        blocks.append("WRITER_FREEZE_MAINTENANCE_APPROVAL_MISSING")
    if not approvals["migration_diff_approved"] or \
       not approvals["rollback_plan_independently_approved"]:
        blocks.append("SIGNED_MIGRATION_AND_ROLLBACK_REVIEW_INCOMPLETE")
    return {
        "status":"HOLD_PRODUCTION_D1_MIGRATION" if blocks
                 else "CLAIMS_COMPLETE_INDEPENDENT_PROVENANCE_STILL_REQUIRED",
        "source_trust":SOURCE_TRUST,
        "risk_codes":blocks,
        "risk_count":len(blocks),
        "current_canonical_release_count":d1_counts["release_rows"],
        "current_canonical_event_count":d1_counts["event_rows"],
        "duplicate_slot_group_count":d1_counts["duplicate_slot_groups"],
        "restore_window_days_claimed":retention,
        "live_d1_checked_by_module":False,
        "live_google_checked_by_module":False,
        "production_backup_recovered_by_module":False,
        "production_migration_authorized":False,
        "production_d1_writes":0,
        "production_index_created":False,
        "production_backfill_permitted":False,
        "production_rollback_permitted":False,
        "youtube_uploads":0,
        "youtube_schedule_writes":0,
        "sql_statements_generated":[],
        "cloud_autopilot_ready":False,
    }
