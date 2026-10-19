"""Phase 4 OFFLINE release-ledger vs owner-channel readback reconciliation.

This is a private-runtime COMPATIBILITY DESIGN using caller-provided records,
not a provider call, not a trusted remote snapshot or a deployed D1 migration.
Any ambiguous upload_started, wrong video ID, ownership, schedule, privacy,
processing or stage mismatch quarantines the run and NEVER triggers retries.

Reports are AGGREGATE-ONLY: no channel/video IDs, user filenames or titles,
OAuth tokens, raw metadata, URLs, release dates or episode identifiers.
No files, network, cloud writes, upload, scheduling or publishing.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date,datetime,timedelta,timezone
from typing import Sequence
import re

from .agent_org import WorkflowError

VIDEO=re.compile(r"[A-Za-z0-9_-]{11}\Z")
CHANNEL=re.compile(r"UC[A-Za-z0-9_-]{22}\Z")
EPISODE=re.compile(r"[a-z][a-z0-9_]{2,63}\Z")
SHA=re.compile(r"[0-9a-f]{64}\Z")
STAGES=(
    "planned","research_verified","script_verified","media_qa_passed",
    "upload_started","remote_private_verified","scheduled_verified",
    "public_verified",
)
MAX_ROWS=500
REMOTE_PRIVACY=frozenset(("private","public","unlisted"))
REMOTE_PROCESSING=frozenset((
    "succeeded","processing","failed","terminated","unknown",
))


@dataclass(frozen=True)
class ReleaseSnapshot:
    release_date:str
    episode_id:str
    stage:str
    media_sha256:str|None
    youtube_id:str|None
    publish_at_utc:str|None


@dataclass(frozen=True)
class OwnerVideoSnapshot:
    youtube_id:str
    privacy:str
    processing:str
    publish_at_utc:str|None
    uncertain_metadata:bool


def _utc(value:str|None)->datetime|None:
    if value is None:
        return None
    if not isinstance(value,str) or not 1<=len(value)<=64:
        raise WorkflowError("Invalid read-only UTC snapshot timestamp")
    try:
        result=datetime.fromisoformat(value.replace("Z","+00:00"))
    except (ValueError,TypeError,OverflowError) as exc:
        raise WorkflowError("Malformed read-only UTC timestamp") from exc
    if result.tzinfo is None or result.utcoffset()!=timedelta(0):
        raise WorkflowError("Read-only timestamp must be UTC")
    if result.microsecond!=0:
        raise WorkflowError("Read-only reconciliation requires whole UTC seconds")
    return result.astimezone(timezone.utc)


def _validate_release(row:ReleaseSnapshot)->None:
    if (not isinstance(row,ReleaseSnapshot)
            or not isinstance(row.release_date,str)
            or not isinstance(row.episode_id,str)
            or EPISODE.fullmatch(row.episode_id) is None
            or row.stage not in STAGES):
        raise WorkflowError("Malformed release snapshot")
    try:
        parsed=date.fromisoformat(row.release_date)
    except ValueError as exc:
        raise WorkflowError("Malformed release date") from exc
    if parsed.isoformat()!=row.release_date:
        raise WorkflowError("Noncanonical release date")
    if row.media_sha256 is not None and (
            not isinstance(row.media_sha256,str)
            or SHA.fullmatch(row.media_sha256) is None):
        raise WorkflowError("Invalid source media digest")
    if row.youtube_id is not None and (
            not isinstance(row.youtube_id,str)
            or VIDEO.fullmatch(row.youtube_id) is None):
        raise WorkflowError("Invalid private YouTube ID")
    _utc(row.publish_at_utc)
    stage_index=STAGES.index(row.stage)
    if (stage_index<3 and row.media_sha256 is not None
            or stage_index>=3 and row.media_sha256 is None
            or stage_index<5 and row.youtube_id is not None
            or stage_index>=5 and row.youtube_id is None
            or stage_index<6 and row.publish_at_utc is not None
            or stage_index>=6 and row.publish_at_utc is None):
        raise WorkflowError("Internal release stage fields are inconsistent")


def _validate_video(row:OwnerVideoSnapshot)->None:
    if (not isinstance(row,OwnerVideoSnapshot)
            or not isinstance(row.youtube_id,str)
            or VIDEO.fullmatch(row.youtube_id) is None
            or row.privacy not in REMOTE_PRIVACY
            or row.processing not in REMOTE_PROCESSING
            or type(row.uncertain_metadata) is not bool):
        raise WorkflowError("Malformed owner readback video")
    _utc(row.publish_at_utc)
    expected=(row.processing=="unknown"
              or (row.privacy!="private" and row.publish_at_utc is not None))
    if row.uncertain_metadata!=expected:
        raise WorkflowError("Uncertainty cannot be suppressed in owner snapshot")


def reconcile_release_snapshots(
    releases:tuple[ReleaseSnapshot,...],
    owner_videos:tuple[OwnerVideoSnapshot,...],
    *,
    expected_channel_id:str,
    observed_channel_id:str,
    remote_pagination_complete:bool,
    local_ledger_snapshot_complete:bool,
)->dict:
    """Classify contradictions and ambiguous upload attempts, NEVER approve.

    Exact typing, global video uniqueness, date and hash validation are
    prerequisite. Source provenance remains untrusted even when no issue
    is detected. Absence of a video in an incomplete readback is UNKNOWN,
    not permission to re-upload.
    """
    if (type(releases) is not tuple or type(owner_videos) is not tuple
            or len(releases)>MAX_ROWS or len(owner_videos)>MAX_ROWS
            or type(remote_pagination_complete) is not bool
            or type(local_ledger_snapshot_complete) is not bool
            or not isinstance(expected_channel_id,str)
            or CHANNEL.fullmatch(expected_channel_id) is None
            or not isinstance(observed_channel_id,str)
            or CHANNEL.fullmatch(observed_channel_id) is None):
        raise WorkflowError("Reconciliation requires bounded typed snapshots")
    if expected_channel_id!=observed_channel_id:
        raise WorkflowError("Owner channel ID mismatch blocks readback")
    seen_release=set()
    seen_release_videos=set()
    seen_media=set()
    stage_counts={stage:0 for stage in STAGES}
    for row in releases:
        _validate_release(row)
        key=(row.release_date,row.episode_id)
        if key in seen_release:
            raise WorkflowError("Duplicate local release row")
        seen_release.add(key)
        stage_counts[row.stage]+=1
        if row.media_sha256 is not None:
            if row.media_sha256 in seen_media:
                raise WorkflowError("Same original media assigned multiple releases")
            seen_media.add(row.media_sha256)
        if row.youtube_id is not None:
            if row.youtube_id in seen_release_videos:
                raise WorkflowError("Multiple releases claim same YouTube ID")
            seen_release_videos.add(row.youtube_id)
    remote={}
    for row in owner_videos:
        _validate_video(row)
        if row.youtube_id in remote:
            raise WorkflowError("Duplicate owner video ID in remote snapshot")
        remote[row.youtube_id]=row
    blockers=set()
    quarantined=0
    exact_id_matches=0
    unknown_remote=0
    if not local_ledger_snapshot_complete:
        blockers.add("INCOMPLETE_LOCAL_LEDGER_SNAPSHOT")
    if not remote_pagination_complete:
        blockers.add("INCOMPLETE_REMOTE_OWNER_INVENTORY")
    for row in releases:
        issues=set()
        if row.stage=="upload_started":
            # No deterministic identity to reconcile after a lost upload ACK:
            # NEVER blind-retry or assume it failed.
            issues.add("UPLOAD_STARTED_AMBIGUOUS_NEEDS_MANUAL_RECOVERY")
        if row.stage in ("remote_private_verified","scheduled_verified",
                         "public_verified"):
            video=remote.get(row.youtube_id)
            if video is None:
                issues.add("BOUND_REMOTE_ID_NOT_FOUND_RECONCILIATION_REQUIRED")
            else:
                exact_id_matches+=1
                if video.uncertain_metadata:
                    issues.add("UNCERTAIN_REMOTE_VIDEO_METADATA")
                if video.processing!="succeeded":
                    issues.add("REMOTE_PROCESSING_NOT_CONFIRMED_SUCCEEDED")
                if row.stage=="remote_private_verified":
                    if video.privacy!="private":
                        issues.add("REMOTE_PRIVACY_DRIFT")
                    if video.publish_at_utc is not None:
                        issues.add("UNEXPECTED_REMOTE_SCHEDULE")
                elif row.stage=="scheduled_verified":
                    if video.privacy!="private":
                        issues.add("REMOTE_PRIVACY_DRIFT_OR_ALREADY_PUBLIC")
                    if _utc(video.publish_at_utc)!=_utc(row.publish_at_utc):
                        issues.add("REMOTE_SCHEDULE_TIMESTAMP_MISMATCH")
                elif row.stage=="public_verified":
                    if video.privacy!="public":
                        issues.add("REMOTE_PUBLIC_STATE_NOT_CONFIRMED")
        if issues:
            quarantined+=1
            blockers.update(issues)
    unknown_remote=len(set(remote)-seen_release_videos)
    if unknown_remote:
        # These may be legacy channel videos. Do not equate them with this
        # run's uploads and do not discard them as harmless without review.
        blockers.add("UNMATCHED_OWNER_VIDEOS_REQUIRE_LINEAGE_REVIEW")
    if not releases:
        blockers.add("NO_LOCAL_RELEASE_RECORDS_TO_RECONCILE")
    if not owner_videos:
        blockers.add("NO_OWNER_VIDEOS_IN_READBACK")
    if any(x.uncertain_metadata for x in owner_videos):
        blockers.add("OWNER_READBACK_CONTAINS_UNCERTAIN_METADATA")
    blockers.add("PROVIDER_AND_LEDGER_SNAPSHOT_ORIGIN_UNAUTHENTICATED")
    blockers.add("NO_CROSS_PROVIDER_ATOMICITY_OR_SIGNED_SNAPSHOT_PROOF")
    return {
        "status":"DRY_RUN_RELEASE_STATE_RECONCILIATION_NOT_AUTHORITY",
        "local_release_count":len(releases),
        "owner_video_count":len(owner_videos),
        "matched_remote_video_id_count":exact_id_matches,
        "unmatched_owner_video_count":unknown_remote,
        "quarantined_local_release_count":quarantined,
        "stage_counts":stage_counts,
        "blocking_reasons":tuple(sorted(blockers)),
        "dry_run_only":True,
        "owner_snapshot_origin_independently_authenticated":False,
        "d1_release_rows_live_observed":False,
        "remote_identity_readback_authoritative":False,
        "safe_to_retry_any_ambiguous_upload":False,
        "release_ledger_migration_authorized":False,
        "publish_or_upload_authorized":False,
        "cloud_database_writes":0,
        "external_api_requests":0,
        "monthly_recurring_infrastructure_inr":0,
    }
