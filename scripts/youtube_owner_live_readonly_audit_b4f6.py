"""B4f6 LIVE-capable OWNER-OAUTH read-only channel and Nov 05-11 slot audit.

Unlike prior CI mocks this *may* check real YouTube channel state, but ONLY
on an explicitly manually dispatched main-branch GitHub environment job with
an already-configured token. The code itself never creates, publishes, edits,
deletes, reserves or retries any YouTube video.

The already-existing owner token may be refreshed by Google OAuth middleware.
Only channels.list, playlistItems.list, videos.list are accessible to the
audit code. No OAuth/token/channel ID/video ID/title/description is logged or
placed in the GitHub artifact; errors are strictly redacted.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re

from autopilot.branch1_owner_schedule_readonly_v6 import (
    RELEASE_STATUS as SCHEDULE_STATUS,
    read_owner_nov_schedule,
)
from scripts.owner_youtube_readback_b4f2 import (
    verify_authenticated_owner_channel,
)

EXPECTED_CHANNEL="UCCcL9Q_jqVq6LJmnYUSAFZA"
EXPECTED_REPO="Tirthanand17/taskless-lab"
EXPECTED_WORKFLOW="FlowMinute Owner YouTube Readonly Channel Audit"
STATUS="B4F6_REAL_OWNER_CHANNEL_READONLY_AUDIT_NO_YOUTUBE_MUTATION"
SHA40=re.compile(r"[0-9a-f]{40}\Z")


class OwnerLiveAuditRefused(ValueError):
    """Do not perform privileged readback if the job context is ambiguous."""


def _need(ok: bool, reason: str) -> None:
    if not ok:
        raise OwnerLiveAuditRefused(reason)


def require_manual_owner_context(env: dict[str, str]) -> None:
    """Guarantee explicitly opted-in, default-main GitHub workflow context."""
    _need(type(env) is dict
          and env.get("GITHUB_ACTIONS")=="true"
          and env.get("GITHUB_EVENT_NAME")=="workflow_dispatch"
          and env.get("GITHUB_REPOSITORY")==EXPECTED_REPO
          and env.get("GITHUB_WORKFLOW")==EXPECTED_WORKFLOW
          and env.get("GITHUB_REF")=="refs/heads/main"
          and env.get("FM_EXPLICIT_OWNER_READONLY_AUDIT")=="true"
          and type(env.get("GITHUB_SHA")) is str
          and SHA40.fullmatch(env["GITHUB_SHA"]) is not None,
          "Owner main-only manual read-only audit was not explicitly requested")


class _ListOnlyResource:
    """Only expose .list(..), not insert/update/delete/batch state APIs."""
    __slots__=("_inner",)

    def __init__(self, inner):
        self._inner=inner

    def list(self, **kwargs):
        return self._inner.list(**kwargs)


class ReadOnlyYoutubeClient:
    """Whitelisted API interface. No get-to-write helpers or raw client escape."""
    __slots__=("_inner",)

    def __init__(self, inner):
        self._inner=inner

    def channels(self):
        return _ListOnlyResource(self._inner.channels())

    def playlistItems(self):
        return _ListOnlyResource(self._inner.playlistItems())

    def videos(self):
        return _ListOnlyResource(self._inner.videos())


def audit_live_owner_readonly(youtube: object, *, root: Path,
                              checked_at_utc: datetime) -> dict:
    """Return only sanitized counters; absolutely no video/account details."""
    _need(isinstance(root,Path) and root.is_dir() and
          isinstance(checked_at_utc,datetime)
          and checked_at_utc.tzinfo is not None
          and checked_at_utc.utcoffset() is not None,
          "Trusted repo root and timezone-aware clock required")
    owned=ReadOnlyYoutubeClient(youtube)
    try:
        owner=verify_authenticated_owner_channel(owned,EXPECTED_CHANNEL)
    except Exception:
        raise OwnerLiveAuditRefused("OWNER_OAUTH_CHANNEL_NOT_INDEPENDENTLY_VERIFIED") from None
    _need(owner.get("authenticated_channel_id")==EXPECTED_CHANNEL,
          "Owner identity mismatch, no release permission")
    result={
        "status":STATUS,
        "checked_at_utc":checked_at_utc.astimezone(timezone.utc)
            .isoformat(timespec="seconds").replace("+00:00","Z"),
        "owner_authenticated_youtube_channel_readback_verified":True,
        "independent_owner_signature_or_fact_or_rights_clearance":False,
        "youtube_video_insert_update_delete_requests":0,
        "youtube_video_published_or_scheduled_by_this_audit":False,
        "owner_approved_replacement_of_existing_videos":False,
        "unattended_7_day_21_video_release_proof":False,
        "schedule_scan_complete":False,
        "schedule_scan_outcome":"NO_COMPLETED_SCAN",
    }
    # The historical read-only scanner strictly binds actual upload playlist
    # membership and current private publishAt to Nov05-Nov11 expected slots.
    # A failed scan must NEVER be converted into 'no scheduled videos'.
    try:
        scan=read_owner_nov_schedule(
            owned,root=root,checked_at_utc=checked_at_utc)
        _need(type(scan) is dict
              and scan.get("status")==SCHEDULE_STATUS
              and scan.get("channel_owned_by_authenticated_oauth") is True
              and scan.get("owner_uploads_pagination_exhausted") is True
              and scan.get("only_readonly_channels_playlistitems_videos_list_called") is True
              and scan.get("slots_checked")==21
              and scan.get("video_uploaded_or_edited_or_deleted") is False
              and scan.get("safe_to_change_any_scheduled_video") is False,
              "Incomplete owner-private schedule inventory")
    except Exception:
        result["schedule_scan_outcome"]="INCOMPLETE_STOP_NO_MUTATION"
        return result
    # Strip video IDs, upload playlist IDs, channel identifiers, titles,
    # descriptions, token fields, old receipt pointers and per-video data.
    allowed={
        "original_git_receipts_count":(0,21),
        "slots_checked":(21,21),
        "private_scheduled_slots_found":(0,21),
        "historical_ids_same_private_schedule_count":(0,21),
        "slot_conflicts":(0,21),
        "private_schedule_outside_standard_time_count":(0,10000),
        "current_youtube_uploads_scanned":(0,2000),
    }
    for key,(lo,hi) in allowed.items():
        val=scan.get(key)
        if type(val) is not int or not lo<=val<=hi:
            result["schedule_scan_outcome"]="INCOMPLETE_STOP_NO_MUTATION"
            return result
        result[key]=val
    result["schedule_scan_complete"]=True
    result["schedule_scan_outcome"]="COMPLETE_READONLY_NOV05_NOV11_OWNER_STATUS"
    return result


def main() -> None:
    # No network or secret loading unless explicitly opted-in on GitHub main.
    require_manual_owner_context(dict(os.environ))
    root=Path.cwd()
    output=Path(os.environ.get("RUNNER_TEMP", "/tmp"))/"flowminute-b4f6-readonly-owner-audit.json"
    _need(not output.exists() and not output.is_symlink(),
          "Cannot overwrite existing protected owner audit")
    # Credential value stays in a GitHub environment secret and only enters
    # Google SDK in memory; no commands/paths that write or print OAuth.
    try:
        from scripts.publish_youtube import load_service
        youtube=load_service()
        report=audit_live_owner_readonly(
            youtube,root=root,checked_at_utc=datetime.now(timezone.utc))
    except Exception:
        report={
            "status":STATUS,
            "owner_authenticated_youtube_channel_readback_verified":False,
            "schedule_scan_complete":False,
            "schedule_scan_outcome":"OAUTH_OR_OWNER_CHANNEL_UNVERIFIED_STOP",
            "youtube_video_insert_update_delete_requests":0,
            "youtube_video_published_or_scheduled_by_this_audit":False,
            "independent_owner_signature_or_fact_or_rights_clearance":False,
            "unattended_7_day_21_video_release_proof":False,
        }
    output.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("B4F6_REAL_OWNER_CHANNEL_READBACK_VERIFIED="+
          str(report["owner_authenticated_youtube_channel_readback_verified"]).lower())
    print("B4F6_EXISTING_NOV05_11_SCHEDULE_SCAN="+report["schedule_scan_outcome"])
    if report["schedule_scan_complete"]:
        print("B4F6_PRIVATE_SCHEDULED_SLOTS="+str(report["private_scheduled_slots_found"]))
        print("B4F6_SLOT_CONFLICTS="+str(report["slot_conflicts"]))
    print("B4F6_YOUTUBE_WRITES=0; NO_VIDEO_RELEASE_OR_OWNER_APPROVAL")
    if not report["owner_authenticated_youtube_channel_readback_verified"]:
        raise SystemExit(2)


if __name__=="__main__":
    main()
