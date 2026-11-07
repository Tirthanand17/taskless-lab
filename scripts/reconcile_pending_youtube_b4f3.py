"""B4f3: READ-ONLY recovery for a previously sent private YouTube upload.

This module cannot make videos.insert, captions.insert, thumbnails.set,
videos.update, videos.delete or any state-changing YouTube call. It only
checks a pinned pending video/caption ID using owner-authenticated API
readback. A failed/pending readback remains pending: NEVER re-upload.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sys

from scripts.owner_youtube_readback_b4f2 import (
    OwnerYouTubeReadbackRefused, verify_authenticated_owner_channel,
    verify_processed_private_schedule_and_caption,
)

EPISODE_ID=re.compile(r"[A-Za-z0-9_-]{8,100}\Z")
YT_VIDEO=re.compile(r"[A-Za-z0-9_-]{11}\Z")
CAP_ID=re.compile(r"[A-Za-z0-9_.-]{1,128}\Z")
CHANNEL=re.compile(r"UC[A-Za-z0-9_-]{22}\Z")
SHA256=re.compile(r"[0-9a-f]{64}\Z")
UTC_Z=re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\Z")
PENDING_FILE=re.compile(r"state/published/[A-Za-z0-9_-]{1,100}\.json\.pending\.json\Z")
EPISODE_FILE=re.compile(r"content/episodes/[A-Za-z0-9_-]{1,100}\.json\Z")
EXPECTED_WORKFLOW="FlowMinute YouTube Readonly Recovery (NO UPLOAD)"


class ReadonlyRecoveryRefused(ValueError):
    """Never infer completion from missing, forged or ambiguous recovery data."""


def _need(ok: bool, reason: str) -> None:
    if not ok:
        raise ReadonlyRecoveryRefused(reason)


def _read_known_json(root: Path, relative: str, pattern: re.Pattern) -> dict:
    _need(type(relative) is str and pattern.fullmatch(relative) is not None,
          "Unrecognized fixed repository path")
    path=root/relative
    _need(not root.is_symlink() and root.is_dir() and
          path.is_file() and not path.is_symlink() and
          4 <= path.stat().st_size <= 32000,
          "Missing, large or linked recovery file")
    try:
        result=json.loads(path.read_text(encoding="utf8"))
    except (UnicodeError,json.JSONDecodeError):
        raise ReadonlyRecoveryRefused("Invalid repository recovery JSON") from None
    _need(type(result) is dict, "Expected JSON object")
    return result


def validate_recovery_context(
    pending: dict, episode: dict, expected_channel: str,
) -> dict:
    _need(type(pending) is dict and type(episode) is dict,
          "Recovery requires exactly one pending and one episode object")
    _need(type(expected_channel) is str and
          CHANNEL.fullmatch(expected_channel) is not None and
          pending.get("expected_channel_id")==expected_channel,
          "Pending video was not pinned to this authorized channel")
    _need(pending.get("state")=="UPLOAD_EXISTS_SCHEDULE_NOT_YET_VERIFIED" and
          pending.get("youtube_schedule_verified") is False,
          "Not an incomplete previously uploaded video")
    video_id=pending.get("video_id")
    caption_id=pending.get("caption_track_id")
    digest=pending.get("source_mp4_sha256")
    schedule=pending.get("expected_publish_at_utc")
    episode_id=pending.get("episode_id")
    _need(type(video_id) is str and YT_VIDEO.fullmatch(video_id) is not None
          and type(caption_id) is str and CAP_ID.fullmatch(caption_id) is not None
          and type(digest) is str and SHA256.fullmatch(digest) is not None
          and type(schedule) is str and UTC_Z.fullmatch(schedule) is not None
          and type(episode_id) is str and EPISODE_ID.fullmatch(episode_id) is not None
          and episode.get("id")==episode_id,
          "Incomplete or mismatched exact previously uploaded media checkpoint")
    title=episode.get("title")
    description=episode.get("description")
    language=episode.get("language","en")
    _need(type(title) is str and title.strip()==title and len(title)>0 and
          type(description) is str and len(description.strip())>0 and
          language in ("en","hi"),
          "Missing exact previously approved source metadata")
    return {
        "video_id":video_id,
        "caption_id":caption_id,
        "episode_id":episode_id,
        "channel_id":expected_channel,
        "source_mp4_sha256":digest,
        "expected_publish_at_utc":schedule,
        "title":title,
        "description":description,
        "language":language,
    }


def inspect_existing_remote_only(
    youtube: object, pending: dict, episode: dict, expected_channel: str,
) -> dict:
    """Three owner-authenticated read-only calls, never start another insert."""
    context=validate_recovery_context(pending,episode,expected_channel)
    owner=verify_authenticated_owner_channel(youtube,context["channel_id"])
    _need(owner["authenticated_channel_id"]==expected_channel,
          "Wrong owner OAuth channel")
    result=verify_processed_private_schedule_and_caption(
        youtube,
        video_id=context["video_id"],
        expected_channel_id=context["channel_id"],
        expected_publish_at=context["expected_publish_at_utc"],
        expected_title=context["title"],
        expected_description=context["description"],
        expected_language=context["language"],
        expected_caption_id=context["caption_id"],
        expected_synthetic_disclosure=True,
        expected_made_for_kids=False,
    )
    _need(result["authenticated_video_and_caption_api_readback"] is True
          and result["actually_publicly_published"] is False,
          "No authenticated existing-video readback evidence")
    # A sanitized receipt for GitHub Actions artifact. Raw IDs remain only in
    # the protected preexisting pending file and are never printed by this CLI.
    return {
        "status":"B4F3_EXISTING_PRIVATE_VIDEO_PROCESSING_CAPTION_READY_READONLY",
        "episode_id_sha256":sha256(context["episode_id"].encode()).hexdigest(),
        "video_id_sha256":sha256(context["video_id"].encode()).hexdigest(),
        "caption_id_sha256":sha256(context["caption_id"].encode()).hexdigest(),
        "approved_local_mp4_sha256_claim_unindependently_verified":context["source_mp4_sha256"],
        "private_publish_at_utc":context["expected_publish_at_utc"],
        "read_only_youtube_api_calls":3,
        "authenticated_preexisting_private_video_ready":True,
        "new_youtube_uploads_or_updates_or_deletions":0,
        "actual_remote_video_bytes_sha256_verified":False,
        "actual_srt_text_independently_downloaded":False,
        "independent_fact_rights_or_human_watch_review":False,
        "public_release_verified":False,
        "unattended_7_day_21_video_proof_achieved":False,
    }


def require_explicit_manual_readonly_context(environ: dict) -> None:
    _need(environ.get("GITHUB_ACTIONS")=="true"
          and environ.get("GITHUB_REF")=="refs/heads/main"
          and environ.get("GITHUB_REPOSITORY")=="Tirthanand17/taskless-lab"
          and environ.get("GITHUB_EVENT_NAME")=="workflow_dispatch"
          and environ.get("GITHUB_WORKFLOW")==EXPECTED_WORKFLOW
          and environ.get("FLOWMINUTE_READONLY_RECOVERY_ENABLED")=="true",
          "Protected main/manual read-only recovery explicitly required")


def main() -> None:
    # Only explicit environment-protected workflow execution may use OAuth.
    require_explicit_manual_readonly_context(os.environ)
    root=Path.cwd()
    pending=_read_known_json(root,os.environ.get("FM_PENDING_RECEIPT",""),PENDING_FILE)
    episode=_read_known_json(root,os.environ.get("FM_EPISODE",""),EPISODE_FILE)
    expected="UCCcL9Q_jqVq6LJmnYUSAFZA"
    validate_recovery_context(pending,episode,expected)
    from scripts.publish_youtube import load_service
    client=load_service()
    try:
        report=inspect_existing_remote_only(client,pending,episode,expected)
    except (ReadonlyRecoveryRefused,OwnerYouTubeReadbackRefused):
        raise SystemExit(
            "Existing private upload is not fully verified; do NOT re-upload"
        ) from None
    output=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"flowminute-b4f3-readonly-receipt.json"
    output.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("B4F3_READONLY_EXISTING_PRIVATE_VIDEO_READY_NO_UPLOAD")
    print("B4F3_REDACTED_RECEIPT_AT_RUNNER_TEMP")


if __name__=="__main__":
    main()
