"""Phase 4G: offline drift detection across TWO independent read-only rounds.

Input: untrusted PRIVATE legacy release tuples + owner YouTube inventory
report, repeated twice in the same private memory-only process. The existing
pure release reconciler validates each round. Comparing two round trips may
spot an update that occurred while pages/providers were being read, but
matching samples DO NOT prove linearizable reads, source authentication,
atomic cross-provider snapshots, backup success or publication permission.

No source identifiers, media SHA, review timestamps or opaque fingerprints
are exposed in the output. No network, imports of private collector modules,
filesystem writes, database mutations, upload retries or scheduling.
"""
from __future__ import annotations

from .agent_org import WorkflowError
from .cloud_release_snapshot_reconcile import reconcile_existing_private_shapes

BLOCKERS_ALWAYS=(
    "D1_YOUTUBE_CROSS_PROVIDER_ATOMICITY_UNPROVEN",
    "D1_RELEASE_SOURCE_PROVENANCE_UNVERIFIED",
    "YOUTUBE_OWNER_SOURCE_PROVENANCE_UNVERIFIED",
    "D1_BACKUP_AND_RESTORE_UNVERIFIED",
    "SINGLE_DURABLE_RELEASE_WRITER_UNVERIFIED",
)
_ALLOWED_KEY_COLUMNS=6


def _release_map(rows:tuple[tuple,...])->dict:
    out={}
    for item in rows:
        # reconcile_existing_private_shapes already performs strict typed
        # validation before this is called. Keep this check local as defense
        # against a future change that might bypass that validation.
        if type(item) is not tuple or len(item)!=_ALLOWED_KEY_COLUMNS:
            raise WorkflowError("Release double-read sample shape invalid")
        key=item[0:2]
        if key in out:
            raise WorkflowError("Duplicate release row in double read")
        out[key]=item
    return out


def _video_map(report:dict)->dict:
    result={}
    for row in report["videos"]:
        key=row["youtube_id"]
        if key in result:
            raise WorkflowError("Duplicate owner video in double read")
        result[key]=(
            row["privacy"],row["processing"],row["publish_at_utc"],
            row["uncertain_metadata"],
        )
    return result


def compare_private_release_read_rounds(
    *,initial_release_rows:tuple[tuple,...],initial_youtube_inventory:dict,
    repeat_release_rows:tuple[tuple,...],repeat_youtube_inventory:dict,
    expected_channel_id:str,
)->dict:
    """Do NOT mark safe to upload even when two synthetic samples match."""
    reports=[]
    for releases,youtube in (
        (initial_release_rows,initial_youtube_inventory),
        (repeat_release_rows,repeat_youtube_inventory),
    ):
        reports.append(reconcile_existing_private_shapes(
            existing_ledger_rows=releases,
            private_youtube_inventory=youtube,
            expected_channel_id=expected_channel_id,
            # Neither a paginated D1 SELECT nor a YouTube readback proves
            # a DB transactionally consistent snapshot or historical scope.
            local_ledger_snapshot_complete=False,
        ))
    first,second=reports
    earlier=_release_map(initial_release_rows)
    later=_release_map(repeat_release_rows)
    owner_earlier=_video_map(initial_youtube_inventory)
    owner_later=_video_map(repeat_youtube_inventory)
    old_keys=set(earlier)
    new_keys=set(later)
    old_owner=set(owner_earlier)
    new_owner=set(owner_later)
    removed_release=len(old_keys-new_keys)
    added_release=len(new_keys-old_keys)
    edited_release=sum(
        earlier[k]!=later[k] for k in old_keys&new_keys
    )
    removed_owner=len(old_owner-new_owner)
    added_owner=len(new_owner-old_owner)
    edited_owner=sum(
        owner_earlier[k]!=owner_later[k] for k in old_owner&new_owner
    )
    release_drift=bool(removed_release+added_release+edited_release)
    owner_drift=bool(removed_owner+added_owner+edited_owner)
    blockers=set(BLOCKERS_ALWAYS)
    if release_drift:
        blockers.add("D1_RELEASE_ROWS_CHANGED_BETWEEN_READ_ROUNDS")
    if owner_drift:
        blockers.add("YOUTUBE_OWNER_INVENTORY_CHANGED_BETWEEN_READ_ROUNDS")
    if (
        "UPLOAD_STARTED_AMBIGUOUS_NEEDS_MANUAL_RECOVERY"
        in set(first["blocking_reasons"])|set(second["blocking_reasons"])
    ):
        blockers.add("AMBIGUOUS_UPLOAD_PRESENT_NO_AUTO_RETRY")
    if first["quarantined_local_release_count"] or second["quarantined_local_release_count"]:
        blockers.add("AT_LEAST_ONE_RELEASE_QUARANTINED_IN_READ_ROUNDS")
    if first["unmatched_owner_video_count"] or second["unmatched_owner_video_count"]:
        blockers.add("UNMATCHED_HISTORICAL_OWNER_UPLOAD_PRESENT")
    if (initial_release_rows==() or repeat_release_rows==()
            or not initial_youtube_inventory["videos"]
            or not repeat_youtube_inventory["videos"]):
        blockers.add("EMPTY_READ_ROUND_REQUIRES_HISTORY_REVIEW")
    return {
        "status":"DOUBLE_READ_DRIFT_SCREEN_ONLY_NOT_RELEASE_AUTHORITY",
        "double_read_sample_count":2,
        "d1_release_row_added_count":added_release,
        "d1_release_row_removed_count":removed_release,
        "d1_release_row_changed_count":edited_release,
        "youtube_video_added_count":added_owner,
        "youtube_video_removed_count":removed_owner,
        "youtube_video_changed_count":edited_owner,
        "any_snapshot_drift_detected":release_drift or owner_drift,
        "release_reconciliation_quarantine_seen":(
            bool(first["quarantined_local_release_count"]) or
            bool(second["quarantined_local_release_count"])
        ),
        "unmatched_owner_upload_seen":(
            bool(first["unmatched_owner_video_count"]) or
            bool(second["unmatched_owner_video_count"])
        ),
        "blocking_reason_codes":tuple(sorted(blockers)),
        "observed_source_is_cryptographically_authenticated":False,
        "two_rounds_prove_consistent_database_snapshot":False,
        "two_rounds_prove_atomic_cross_provider_snapshot":False,
        "durable_cloud_lease_and_writer_verified":False,
        "backup_restore_verified":False,
        "any_ambiguous_upload_safe_to_retry":False,
        "migration_authorized":False,
        "youtube_upload_authorized":False,
        "scheduling_or_publishing_authorized":False,
        "network_calls":0,
        "database_writes":0,
        "monthly_recurring_infrastructure_inr":0,
    }
