"""Branch 2 B4a: pure, MOCK-ONLY YouTube private-first transaction contract.

No YouTube imports, HTTP requests, credentials, disk writes, AWS, or publisher.
This is NOT a durable distributed lock, authenticated readback, or an upload.
The eventual owner-run gateway MUST atomically persist the attempt fence in an
independent protected database BEFORE attempting any remote videos.insert.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import re
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
CHANNEL = re.compile(r"^UC[A-Za-z0-9_-]{22}$")
VIDEO = re.compile(r"^[A-Za-z0-9_-]{11}$")
UTC_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
SLOTS = {"short_am": (11, 0), "long": (16, 0), "short_pm": (20, 30)}


class ReleaseContractError(ValueError):
    """Unverified or uncertain state must block remote writes."""


def _sha(value: str) -> str:
    if not isinstance(value, str) or not HEX64.fullmatch(value):
        raise ReleaseContractError("All source/media hashes must be lowercase SHA256")
    return value


def _instant(value: str) -> datetime:
    if not isinstance(value, str) or not UTC_Z.fullmatch(value):
        raise ReleaseContractError("Only exact whole-second UTC-Z timestamps accepted")
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReleaseContractError("Invalid UTC calendar timestamp") from exc
    if instant.utcoffset() != timedelta(0):
        raise ReleaseContractError("UTC offset must equal zero")
    return instant


@dataclass(frozen=True)
class DryRunUploadIntent:
    episode_id: str
    slot: str
    channel_id: str
    final_mp4_sha256: str
    captions_srt_sha256: str
    thumbnail_sha256: str
    source_review_context_sha256: str
    title: str
    description: str
    language: str
    synthetic_media_disclosure: bool
    made_for_kids: bool
    publish_at_utc: str
    context_sha256: str
    simulation_only: bool = True
    real_owner_approval: bool = False
    real_youtube_oauth: bool = False
    release_authorized: bool = False


def prepare_unapproved_intent(
    *, episode_id: str, slot: str, channel_id: str,
    final_mp4_sha256: str, captions_srt_sha256: str,
    thumbnail_sha256: str, source_review_context_sha256: str,
    title: str, description: str, language: str,
    synthetic_media_disclosure: bool, made_for_kids: bool,
    publish_at_utc: str, now: datetime,
) -> DryRunUploadIntent:
    """Build only an unapproved simulated request, never authorize a release."""
    if not isinstance(episode_id, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{8,100}", episode_id):
        raise ReleaseContractError("Stable episode ID required")
    if slot not in SLOTS:
        raise ReleaseContractError("One of the exact 2 Shorts + 1 Long slots required")
    if not isinstance(channel_id, str) or not CHANNEL.fullmatch(channel_id):
        raise ReleaseContractError("YouTube owner channel ID is malformed")
    if not isinstance(title, str) or not (1 <= len(title) <= 100) or title.strip() != title:
        raise ReleaseContractError("Exact intended title required")
    if not isinstance(description, str) or not description.strip():
        raise ReleaseContractError("Approved description cannot be empty")
    if language not in ("en", "hi"):
        raise ReleaseContractError("Captions language unsupported")
    if type(synthetic_media_disclosure) is not bool or type(made_for_kids) is not bool:
        raise ReleaseContractError("Disclosure and audience choice must be explicit")
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ReleaseContractError("Trusted aware UTC clock must be supplied")
    target = _instant(publish_at_utc)
    if target <= now.astimezone(timezone.utc) + timedelta(minutes=15):
        raise ReleaseContractError("Too close, immediate/past publication forbidden")
    if (target.astimezone(IST).hour, target.astimezone(IST).minute) != SLOTS[slot]:
        raise ReleaseContractError("Slot does not match 11:00/16:00/20:30 IST")
    fields = dict(
        episode_id=episode_id, slot=slot, channel_id=channel_id,
        final_mp4_sha256=_sha(final_mp4_sha256),
        captions_srt_sha256=_sha(captions_srt_sha256),
        thumbnail_sha256=_sha(thumbnail_sha256),
        source_review_context_sha256=_sha(source_review_context_sha256),
        title=title, description=description, language=language,
        synthetic_media_disclosure=synthetic_media_disclosure,
        made_for_kids=made_for_kids, publish_at_utc=publish_at_utc,
    )
    digest = sha256(json.dumps(fields, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return DryRunUploadIntent(**fields, context_sha256=digest)


@dataclass(frozen=True)
class MockAttemptFence:
    """Only a transition shape. A real fence requires atomic external storage."""
    context_sha256: str
    state: str
    remote_video_id: str | None = None
    simulated_only: bool = True
    remote_upload_proven: bool = False
    release_authorized: bool = False


def propose_first_attempt(intent: DryRunUploadIntent, existing: MockAttemptFence | None) -> MockAttemptFence:
    """Treat even a suspected sent request as permanently NO NEW UPLOAD.

    The resulting state must be committed to durable, exclusive-owner storage
    BEFORE actual initiation. This function neither stores nor sends anything.
    """
    if type(intent) is not DryRunUploadIntent or not intent.simulation_only:
        raise ReleaseContractError("Only the unapproved dry-run intent is allowed")
    if existing is not None:
        raise ReleaseContractError("Existing or uncertain attempt: NEVER start new upload")
    return MockAttemptFence(intent.context_sha256, "POSSIBLY_SENT_NO_RETRY")


def note_returned_id(fence: MockAttemptFence, video_id: str) -> MockAttemptFence:
    if fence.state != "POSSIBLY_SENT_NO_RETRY" or fence.remote_video_id is not None:
        raise ReleaseContractError("Illegal duplicate or reversed transition")
    if not isinstance(video_id, str) or not VIDEO.fullmatch(video_id):
        raise ReleaseContractError("No trustworthy remote video identifier")
    return replace(fence, state="REMOTE_ID_REPORTED_UNVERIFIED", remote_video_id=video_id)


def inspect_injected_video_readback(
    intent: DryRunUploadIntent, fence: MockAttemptFence,
    video: dict, captions: dict,
) -> dict:
    """Compare fake/injected records against an exact target, never attest live API.

    Actual authorized production must authenticate the owner and fetch video
    + captions independently, verify uploaded media identity and other assets,
    and re-read the final remote schedule. A fake fixture is not such proof.
    """
    if fence.context_sha256 != intent.context_sha256 or fence.state != "REMOTE_ID_REPORTED_UNVERIFIED":
        raise ReleaseContractError("Mismatched or incomplete attempted upload")
    if not isinstance(video, dict) or not isinstance(captions, dict):
        raise ReleaseContractError("Missing independent owner readback fields")
    snippet = video.get("snippet")
    status = video.get("status")
    processing = video.get("processingDetails")
    detail = video.get("contentDetails")
    caption_items = captions.get("items")
    if not all(isinstance(x, dict) for x in (snippet, status, processing, detail)):
        return _mock_result(False)
    if not isinstance(caption_items, list) or len(caption_items) != 1 or not isinstance(caption_items[0], dict):
        return _mock_result(False)
    caption_info = caption_items[0].get("snippet")
    if not isinstance(caption_info, dict):
        return _mock_result(False)
    try:
        matching_schedule = _instant(status.get("publishAt")) == _instant(intent.publish_at_utc)
    except ReleaseContractError:
        matching_schedule = False
    matched = all((
        video.get("id") == fence.remote_video_id,
        snippet.get("channelId") == intent.channel_id,
        snippet.get("title") == intent.title,
        snippet.get("description") == intent.description,
        status.get("privacyStatus") == "private",
        status.get("uploadStatus") == "processed",
        processing.get("processingStatus") == "succeeded",
        matching_schedule,
        type(status.get("containsSyntheticMedia")) is bool
            and status["containsSyntheticMedia"] == intent.synthetic_media_disclosure,
        type(status.get("selfDeclaredMadeForKids")) is bool
            and status["selfDeclaredMadeForKids"] == intent.made_for_kids,
        detail.get("hasCustomThumbnail") is True,
        caption_info.get("videoId") == fence.remote_video_id,
        caption_info.get("language") == intent.language,
        caption_info.get("status") == "serving",
    ))
    return _mock_result(matched)


def _mock_result(matched: bool) -> dict:
    return {
        "synthetic_api_response_contract_matches": bool(matched),
        "actual_authenticated_youtube_readback": False,
        "actual_uploaded_mp4_sha256_independently_verified": False,
        "actual_srt_text_independently_verified": False,
        "owner_identity_and_rights_independently_verified": False,
        "durable_cross_process_exactly_once_guarantee": False,
        "real_video_scheduled": False,
        "real_video_published": False,
        "release_authorized": False,
    }
