"""B4b2: pure no-network YouTube resumable-session status recovery contract.

Fake sessions and responses only. No YouTube SDK, OAuth, HTTP, real video, or
persistent storage. An actual owner-operated worker must atomically store an
encrypted session URI before sending media bytes. A fake boolean cannot prove
it stored anything. Any uncertain fresh videos.insert state stays fenced.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import re

from autopilot.youtube_private_first_contract import (
    DryRunUploadIntent, prepare_unapproved_intent, ReleaseContractError,
)

HEX64 = re.compile(r"^[0-9a-f]{64}$")
RANGE = re.compile(r"^bytes=0-(0|[1-9][0-9]*)$")
VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
CHANNEL_ID = re.compile(r"^UC[A-Za-z0-9_-]{22}$")
MAX_MEDIA_BYTES = 256_000_000_000
MAX_TRANSIENT = 4
RETRYABLE = {500, 502, 503, 504}


class RecoveryRefused(ValueError):
    """No new upload may be initiated after ambiguous state."""


@dataclass(frozen=True)
class FakeSession:
    context_sha256: str
    media_sha256: str
    owner_channel_id: str
    total_bytes: int
    encrypted_session_reference_sha256: str
    synthetic_checkpoint_saved: bool
    acknowledged_end: int = -1
    transient_responses: int = 0
    state: str = "PROBE_REQUIRED"
    unverified_video_id: str | None = None
    mock_only: bool = True
    real_cloud_storage_verified: bool = False
    owner_oauth_verified: bool = False
    actual_upload_verified: bool = False
    release_authorized: bool = False


@dataclass(frozen=True)
class RecoveryInstruction:
    action: str
    method: str | None = None
    headers: dict[str, str] | None = None
    next_offset: int | None = None
    remaining_bytes: int | None = None
    returned_video_id_unverified: str | None = None
    reason: str | None = None
    min_delay_seconds: int = 0
    same_session_only: bool = True
    actual_http_executed: bool = False
    actual_video_uploaded: bool = False
    actual_video_scheduled: bool = False
    release_authorized: bool = False


def _canonical_intent(intent: DryRunUploadIntent, now: datetime) -> None:
    if (type(intent) is not DryRunUploadIntent or intent.simulation_only is not True
            or intent.real_owner_approval is not False
            or intent.real_youtube_oauth is not False
            or intent.release_authorized is not False):
        raise RecoveryRefused("Only exact unapproved B4a mock intent accepted")
    try:
        rebuilt = prepare_unapproved_intent(
            episode_id=intent.episode_id, slot=intent.slot,
            channel_id=intent.channel_id,
            final_mp4_sha256=intent.final_mp4_sha256,
            captions_srt_sha256=intent.captions_srt_sha256,
            thumbnail_sha256=intent.thumbnail_sha256,
            source_review_context_sha256=intent.source_review_context_sha256,
            title=intent.title, description=intent.description,
            language=intent.language,
            synthetic_media_disclosure=intent.synthetic_media_disclosure,
            made_for_kids=intent.made_for_kids,
            publish_at_utc=intent.publish_at_utc, now=now,
        )
    except ReleaseContractError as exc:
        raise RecoveryRefused("Invalid, modified or expired target slot") from exc
    if rebuilt != intent:
        raise RecoveryRefused("Original media/source metadata digest mismatch")


def fake_persisted_session(
    *, intent: DryRunUploadIntent, total_bytes: int,
    encrypted_session_reference_sha256: str,
    synthetic_checkpoint_saved: bool,
    now: datetime | None = None,
) -> FakeSession:
    """Represent an invented stored session; DOES NOT persist or authenticate."""
    _canonical_intent(intent, now or datetime.now(timezone.utc))
    if type(total_bytes) is not int or not 0 < total_bytes <= MAX_MEDIA_BYTES:
        raise RecoveryRefused("Invalid exact media length")
    if (not isinstance(encrypted_session_reference_sha256, str)
            or not HEX64.fullmatch(encrypted_session_reference_sha256)):
        raise RecoveryRefused("Only a SHA256 of an imaginary encrypted handle")
    if synthetic_checkpoint_saved is not True:
        raise RecoveryRefused("No mock checkpoint claimed before bytes transfer")
    return FakeSession(
        context_sha256=intent.context_sha256,
        media_sha256=intent.final_mp4_sha256,
        owner_channel_id=intent.channel_id,
        total_bytes=total_bytes,
        encrypted_session_reference_sha256=encrypted_session_reference_sha256,
        synthetic_checkpoint_saved=True,
    )


def _require_fake(session: FakeSession) -> None:
    if (type(session) is not FakeSession or session.mock_only is not True
            or session.real_cloud_storage_verified is not False
            or session.owner_oauth_verified is not False
            or session.actual_upload_verified is not False
            or session.release_authorized is not False
            or session.synthetic_checkpoint_saved is not True
            or not isinstance(session.context_sha256, str)
            or not HEX64.fullmatch(session.context_sha256)
            or not isinstance(session.media_sha256, str)
            or not HEX64.fullmatch(session.media_sha256)
            or not isinstance(session.encrypted_session_reference_sha256, str)
            or not HEX64.fullmatch(session.encrypted_session_reference_sha256)
            or not isinstance(session.owner_channel_id, str)
            or not CHANNEL_ID.fullmatch(session.owner_channel_id)
            or type(session.total_bytes) is not int
            or not 0 < session.total_bytes <= MAX_MEDIA_BYTES
            or type(session.acknowledged_end) is not int
            or not -1 <= session.acknowledged_end < session.total_bytes
            or type(session.transient_responses) is not int
            or not 0 <= session.transient_responses <= MAX_TRANSIENT):
        raise RecoveryRefused("Forged, malformed, or live-authority-claiming session")


def make_status_probe(session: FakeSession) -> RecoveryInstruction:
    """Describe the official zero-body PUT; no URI/credentials/bytes are sent."""
    _require_fake(session)
    if session.state != "PROBE_REQUIRED" or session.unverified_video_id is not None:
        raise RecoveryRefused("No repeated probes after terminal/unknown state")
    return RecoveryInstruction(
        action="QUERY_EXISTING_SESSION_ONLY",
        method="PUT",
        headers={
            "Content-Length": "0",
            "Content-Range": "bytes */" + str(session.total_bytes),
        },
        remaining_bytes=0,
    )


def _normalize_headers(raw: dict[str, str] | None) -> dict[str, str]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise RecoveryRefused("Invalid HTTP header map")
    out: dict[str, str] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise RecoveryRefused("Malformed header")
        lower=key.lower()
        if lower in out:
            raise RecoveryRefused("Conflicting case-variant duplicate header")
        out[lower]=value
    return out


def _retry_after_seconds(headers: dict[str, str]) -> int:
    raw=headers.get("retry-after")
    if raw is None:
        return 0
    if not re.fullmatch(r"(0|[1-9][0-9]{0,3})",raw):
        raise RecoveryRefused("Untrusted Retry-After format, manual check")
    delay=int(raw)
    if delay>3600:
        raise RecoveryRefused("Excessive Retry-After, manual reconciliation")
    return delay


def interpret_fake_status_reply(
    session: FakeSession,
    *, status_code: int | None, response_headers: dict[str,str] | None = None,
    response_video: dict | None = None,
) -> tuple[FakeSession, RecoveryInstruction]:
    """Interpret ONLY a fictional response to a SAME-SESSION status probe.

    A production publisher must independently verify actual session identity,
    authenticated original media bytes, external DB checkpoint and owner rights
    before acting on a resulting plan. These outputs NEVER authorize upload.
    """
    _require_fake(session)
    if session.state != "PROBE_REQUIRED" or session.unverified_video_id is not None:
        raise RecoveryRefused("Illegal replay/non-probe state")
    if status_code is not None and type(status_code) is not int:
        raise RecoveryRefused("Invalid HTTP status")
    try:
        headers=_normalize_headers(response_headers)
    except RecoveryRefused as exc:
        return replace(session,state="HALTED_RECONCILIATION"), RecoveryInstruction(
            action="STOP_NO_NEW_INSERT",reason=str(exc))

    if status_code is None or status_code in RETRYABLE:
        n=session.transient_responses+1
        if n >= MAX_TRANSIENT:
            return replace(session,state="HALTED_RECONCILIATION",
                           transient_responses=n), RecoveryInstruction(
                action="STOP_NO_NEW_INSERT",reason="Repeated uncertain responses")
        try:
            delay=_retry_after_seconds(headers)
        except RecoveryRefused as exc:
            return replace(session,state="HALTED_RECONCILIATION",
                           transient_responses=n), RecoveryInstruction(
                action="STOP_NO_NEW_INSERT",reason=str(exc))
        return replace(session,transient_responses=n), RecoveryInstruction(
            action="REQUERY_EXISTING_SESSION_ONLY",
            reason="Backoff at least "+str(delay)+" seconds; never initiate a new upload",
            min_delay_seconds=delay)

    if status_code==308:
        if response_video is not None:
            return replace(session,state="HALTED_RECONCILIATION"), RecoveryInstruction(
                action="STOP_NO_NEW_INSERT",reason="Incomplete response carries video body")
        try:
            delay=_retry_after_seconds(headers)
            field=headers.get("range")
            if field is None:
                last=-1
            else:
                m=RANGE.fullmatch(field)
                if not m:
                    raise RecoveryRefused("Malformed inclusive zero-indexed Range")
                last=int(m.group(1))
            if last<session.acknowledged_end or last >= session.total_bytes-1:
                raise RecoveryRefused("Regression, overflow or terminal 308 Range")
            first=last+1
            remaining=session.total_bytes-first
            if remaining<=0:
                raise RecoveryRefused("No bytes remain for a 308 response")
        except RecoveryRefused as exc:
            return replace(session,state="HALTED_RECONCILIATION"), RecoveryInstruction(
                action="STOP_NO_NEW_INSERT",reason=str(exc))
        return replace(session,acknowledged_end=last,
                       transient_responses=0), RecoveryInstruction(
            action="RESUME_EXISTING_SESSION_BYTES_ONLY",
            method="PUT",
            headers={
                "Content-Type":"video/mp4",
                "Content-Length":str(remaining),
                "Content-Range":f"bytes {first}-{session.total_bytes-1}/{session.total_bytes}",
            },
            next_offset=first,remaining_bytes=remaining,
            min_delay_seconds=delay,
        )

    if status_code in (200,201):
        if not isinstance(response_video,dict):
            return replace(session,state="HALTED_RECONCILIATION"), RecoveryInstruction(
                action="STOP_NO_NEW_INSERT",reason="No original completion video resource")
        video_id=response_video.get("id")
        snippet=response_video.get("snippet")
        status=response_video.get("status")
        if (not isinstance(video_id,str) or not VIDEO_ID.fullmatch(video_id)
                or not isinstance(snippet,dict)
                or snippet.get("channelId")!=session.owner_channel_id
                or not isinstance(status,dict)
                or status.get("privacyStatus")!="private"):
            return replace(session,state="HALTED_RECONCILIATION"), RecoveryInstruction(
                action="STOP_NO_NEW_INSERT",reason="Wrong channel/ID or unsafe public status")
        return replace(session,state="REMOTE_ID_REPORTED_UNVERIFIED",
                       unverified_video_id=video_id), RecoveryInstruction(
            action="REMOTE_ID_REPORTED_UNVERIFIED",
            returned_video_id_unverified=video_id,
            reason="Owner-authenticated independent private/processing/rights readback still missing")

    return replace(session,state="HALTED_RECONCILIATION"), RecoveryInstruction(
        action="STOP_NO_NEW_INSERT",
        reason="Expired, revoked, unknown or unrecoverable session; manual reconcile")
