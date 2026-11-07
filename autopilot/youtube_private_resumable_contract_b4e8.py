"""B4e8 OFFLINE YouTube 2026 private-first + resumable protocol rehearsal.

Pure, testable contracts. NO HTTP, OAuth, network import, file writing,
YouTube account state, executable upload or publishing authority.
An actual gateway still needs owner identity, independent factual/rights
approvals, persisted one-attempt fence and authenticated API readback.
"""
from __future__ import annotations

from dataclasses import fields
from datetime import datetime, timedelta
import re
from typing import Sequence
from zoneinfo import ZoneInfo

from autopilot.youtube_private_first_contract import (
    DryRunUploadIntent, ReleaseContractError, prepare_unapproved_intent,
)

IST = ZoneInfo("Asia/Kolkata")
RETRIABLE = {500, 502, 503, 504}
VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}\Z")
RANGE = re.compile(r"bytes=0-([0-9]+)\Z")
MAX_SIMULATED_MEDIA_BYTES = 1_000_000_000
CHUNK_BYTES = 8 * 1024 * 1024
PART_BYTES = 256 * 1024


class OfflineUploadRefused(ValueError):
    """No preflight, malformed progress, or release authority: stop."""


def _require(condition: bool, why: str) -> None:
    if not condition:
        raise OfflineUploadRefused(why)


def _canonical(intent: DryRunUploadIntent, now: datetime) -> None:
    _require(type(intent) is DryRunUploadIntent,
             "Only strict B4a immutable dry-run contract accepted")
    _require(intent.simulation_only is True
             and intent.real_owner_approval is False
             and intent.real_youtube_oauth is False
             and intent.release_authorized is False,
             "Cannot convert an unapproved mock into live publishing")
    try:
        recreated=prepare_unapproved_intent(
            **{key:getattr(intent,key)
               for key in (
                   "episode_id","slot","channel_id","final_mp4_sha256",
                   "captions_srt_sha256","thumbnail_sha256",
                   "source_review_context_sha256","title","description",
                   "language","synthetic_media_disclosure","made_for_kids",
                   "publish_at_utc")},
            now=now,
        )
    except (ReleaseContractError, TypeError, ValueError) as exc:
        raise OfflineUploadRefused("Unapproved intent invalid or too near publishing") from exc
    _require(recreated == intent, "Tampered upload context fingerprint")


def prepare_offline_private_resumable_spec(
    intent: DryRunUploadIntent, media_byte_size: int, *, now: datetime,
) -> dict:
    """Request *specification* only; never calls YouTube or creates a session."""
    _canonical(intent,now)
    _require(type(media_byte_size) is int and
             300_000 <= media_byte_size <= MAX_SIMULATED_MEDIA_BYTES,
             "Invalid proposed full media byte length")
    body={
        "snippet":{
            "title":intent.title,
            "description":intent.description,
            "categoryId":"27",
            "defaultLanguage":intent.language,
        },
        "status":{
            # 2026-11-02 YouTube reversed forced-private unverified project policy;
            # omitted privacyStatus can immediately publish publicly.
            "privacyStatus":"private",
            "publishAt":intent.publish_at_utc,
            "selfDeclaredMadeForKids":intent.made_for_kids,
            "containsSyntheticMedia":intent.synthetic_media_disclosure,
        },
    }
    _require(
        set(body)=={"snippet","status"}
        and body["status"].get("privacyStatus")=="private"
        and body["status"].get("publishAt")==intent.publish_at_utc
        and type(body["status"].get("containsSyntheticMedia")) is bool
        and type(body["status"].get("selfDeclaredMadeForKids")) is bool,
        "Private-first metadata lost mandatory visibility/scheduling flags",
    )
    return {
        "contract":"B4E8_2026_YOUTUBE_PRIVATE_RESUMABLE_MOCK_SPEC_ONLY",
        "operation":"videos.insert",
        "upload_protocol":"resumable",
        "parts":"snippet,status",
        "headers_without_authorization":{
            "Content-Type":"application/json; charset=UTF-8",
            "X-Upload-Content-Type":"video/mp4",
            "X-Upload-Content-Length":str(media_byte_size),
        },
        "metadata":body,
        "context_sha256":intent.context_sha256,
        "media_sha256":intent.final_mp4_sha256,
        "media_bytes":media_byte_size,
        "simulation_only":True,
        "actual_http_requests":0,
        "actual_youtube_uploads":0,
        "owner_authenticated":False,
        "independent_facts_or_rights_reviewed":False,
        "durable_production_attempt_fence_deployed":False,
        "release_authorized":False,
    }


def probe_same_session_headers(total_bytes: int) -> dict:
    """A mock PUT query for an *existing* session; no new videos.insert."""
    _require(type(total_bytes) is int and total_bytes > 0,
             "Invalid video size")
    return {"Content-Length":"0", "Content-Range":f"bytes */{total_bytes}"}


def resume_chunk_spec(total_bytes: int, next_byte: int, *,
                      chunk_bytes: int = CHUNK_BYTES) -> dict:
    """Pure byte-range calculation, never reads local media or sends a PUT."""
    _require(type(total_bytes) is int and 0 < total_bytes <= MAX_SIMULATED_MEDIA_BYTES,
             "Invalid total bytes")
    _require(type(next_byte) is int and 0 <= next_byte < total_bytes,
             "Invalid server-acknowledged resume offset")
    _require(type(chunk_bytes) is int and chunk_bytes >= PART_BYTES
             and chunk_bytes % PART_BYTES == 0,
             "Nonfinal YouTube chunk must be a multiple of 256 KiB")
    last=min(total_bytes,next_byte+chunk_bytes)-1
    return {
        "method":"PUT_ALREADY_RESERVED_SESSION_ONLY",
        "start_byte":next_byte,
        "end_byte":last,
        "chunk_byte_count":last-next_byte+1,
        "headers_without_auth":{
            "Content-Type":"video/mp4",
            "Content-Length":str(last-next_byte+1),
            "Content-Range":f"bytes {next_byte}-{last}/{total_bytes}",
        },
        "actual_http_requests":0,
        "new_insert_allowed":False,
    }


def interpret_injected_session_response(
    http_status: int, headers: dict, total_bytes: int, *, video_id: str | None = None,
) -> dict:
    """Mock interpretation of one response. NO automatic duplicate insertion."""
    _require(type(http_status) is int and 100 <= http_status <= 599,
             "Invalid simulated HTTP status")
    _require(type(headers) is dict and all(type(k) is str and type(v) is str
                                          for k,v in headers.items()),
             "Invalid injected header types")
    _require(type(total_bytes) is int and 0 < total_bytes <= MAX_SIMULATED_MEDIA_BYTES,
             "Invalid media size")
    _require(video_id is None or (
        type(video_id) is str and VIDEO_ID.fullmatch(video_id) is not None),
        "Malformed remote ID evidence")
    if http_status == 308:
        _require(video_id is None,"Incomplete upload cannot return final video ID")
        raw=headers.get("Range")
        if raw is None:
            offset=0
        else:
            match=RANGE.fullmatch(raw)
            _require(match is not None, "Unexpected resume range header")
            offset=int(match[1])+1
            _require(0 < offset < total_bytes,
                     "Server range claims invalid or completed bytes")
        result={"state":"RESUME_EXISTING_SESSION_AT_SERVER_ACKNOWLEDGED_OFFSET",
                "next_byte":offset, "probe_same_session_first":False}
    elif http_status in (200,201):
        _require(video_id is not None, "Ambiguous completed upload: no trusted ID")
        result={"state":"REMOTE_ID_REPORTED_NEEDS_AUTHENTICATED_READBACK",
                "unverified_video_id":video_id}
    elif http_status in RETRIABLE:
        _require(video_id is None, "Transient status cannot claim final video ID")
        result={"state":"QUERY_EXISTING_SESSION_STATUS_BEFORE_RETRY",
                "probe_same_session_first":True}
    else:
        # 4xx, 429, unexpected status or ambiguities: human reconciliation;
        # NEVER start a fresh insert, because the old request may have landed.
        result={"state":"STOP_AMBIGUOUS_OR_PERMANENT_NO_NEW_INSERT",
                "manual_reconciliation_required":True}
    return {
        **result,
        "simulation_only":True,
        "new_insert_allowed":False,
        "actual_http_requests":0,
        "authenticated_remote_upload_proven":False,
        "release_authorized":False,
    }


def simulate_next_seven_days(
    proposed: Sequence[tuple[DryRunUploadIntent,int]], *, now: datetime,
) -> dict:
    """Strict ordered 7x(AM Short, long, PM Short) dry-run, never real scheduling."""
    _require(type(proposed) in (list,tuple) and len(proposed)==21,
             "Seven-day proof needs exactly 21 distinct simulated slots")
    _require(type(now) is datetime and now.tzinfo is not None
             and now.utcoffset() is not None, "Aware clock required")
    starting=now.astimezone(IST).date()+timedelta(days=1)
    expected_slots=("short_am","long","short_pm")
    channel=None
    seen_ids,seen_media,seen_context,seen_schedule=set(),set(),set(),set()
    rows=[]
    for i,(intent,size) in enumerate(proposed):
        _canonical(intent,now)
        today=starting+timedelta(days=i//3)
        _require(intent.slot==expected_slots[i%3],
                 "Wrong AM/long/PM video order")
        # All clock and DST conversions are verified by B4a preparation.
        instant=datetime.fromisoformat(intent.publish_at_utc.replace("Z","+00:00"))
        _require(instant.astimezone(IST).date()==today,
                 "Non-consecutive or wrong-day release simulation")
        if channel is None:
            channel=intent.channel_id
        _require(intent.channel_id==channel, "Mixed/unverified simulated channel")
        for value,seen in ((intent.episode_id,seen_ids),
                           (intent.final_mp4_sha256,seen_media),
                           (intent.context_sha256,seen_context),
                           (intent.publish_at_utc,seen_schedule)):
            _require(value not in seen, "Duplicate media/episode/context or release time")
            seen.add(value)
        spec=prepare_offline_private_resumable_spec(intent,size,now=now)
        _require(spec["metadata"]["status"]["privacyStatus"]=="private",
                 "Accidental public default")
        # Only retain *hashes, counts and timing*; no unapproved title/script.
        rows.append({
            "slot":intent.slot,
            "day_ist":today.isoformat(),
            "publish_at_utc":intent.publish_at_utc,
            "context_sha256":intent.context_sha256,
            "media_sha256":intent.final_mp4_sha256,
            "private_metadata_spec_validated":True,
            "real_video_uploaded":False,
            "real_video_scheduled":False,
        })
    return {
        "status":"B4E8_21_PRIVATE_FIRST_MOCK_REQUESTS_NO_REMOTE_CALLS",
        "simulated_days":7,
        "simulated_slots":len(rows),
        "private_first_specs_created":len(rows),
        "video_upload_quota_consumed":0,
        "real_youtube_uploads":0,
        "real_youtube_scheduled_or_published":0,
        "owner_authenticated":False,
        "rights_and_factual_approvals":0,
        "durable_production_fence_deployed":False,
        "release_authorized":False,
        "slots":rows,
    }
