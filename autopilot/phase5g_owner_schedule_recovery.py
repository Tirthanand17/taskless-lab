"""Phase 5G: offline owner-API schedule reconciliation policy, NO mutating tools.

Works only on sanitized in-memory observations supplied by a caller.
It does not connect to YouTube/Cloudflare and therefore cannot attest that
the input came from an owner account. Actual trusted caller must independently
verify the owner channel and cryptographically protected source of evidence.

Never generate upload, schedule, metadata-backfill, or public-release actions.
"""
from __future__ import annotations
from datetime import datetime, date, time, timedelta, timezone
from typing import Any, Mapping
import re

CHANNEL = "UCCcL9Q_jqVq6LJmnYUSAFZA"
SLOTS = {"short_morning":(11,0), "long":(16,0), "short_evening":(20,30)}
VID = re.compile(r"[A-Za-z0-9_-]{11}\Z")
DAY = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
TITLE = re.compile(r".{1,100}\Z",re.DOTALL)
ALLOWED_PRIVACY = frozenset(("private","public","unlisted"))
MAX_AGE = timedelta(minutes=10)


class OwnerReadbackHold(ValueError):
    """Safe static diagnostic, never interpolated private input."""


def _schema(value: Any, keys: set[str]) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise OwnerReadbackHold("INVALID_EVIDENCE_SCHEMA")
    return value


def _instant(value:Any) -> datetime:
    if not isinstance(value,str) or len(value)>40 or not value.endswith("Z"):
        raise OwnerReadbackHold("INVALID_EVIDENCE_TIME")
    try:
        dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    except (ValueError,OverflowError):
        raise OwnerReadbackHold("INVALID_EVIDENCE_TIME") from None
    if dt.utcoffset()!=timedelta(0):
        raise OwnerReadbackHold("INVALID_EVIDENCE_TIME")
    return dt


def _day(value: Any) -> date:
    if not isinstance(value,str) or not DAY.fullmatch(value):
        raise OwnerReadbackHold("INVALID_DATE")
    try:
        result=date.fromisoformat(value)
        if result.isoformat()!=value:
            raise ValueError()
    except ValueError:
        raise OwnerReadbackHold("INVALID_DATE") from None
    return result


def _target(day:date,slot:str) -> datetime:
    hour,minute=SLOTS[slot]
    local=datetime.combine(day,time(hour=hour,minute=minute),
                           tzinfo=timezone(timedelta(hours=5,minutes=30)))
    return local.astimezone(timezone.utc)


def _check_video(value:Any) -> None:
    if not isinstance(value,str) or not VID.fullmatch(value):
        raise OwnerReadbackHold("INVALID_VIDEO_ID")


def verify_scheduled_receipts(payload: Mapping[str,Any], *, now:datetime) -> dict:
    """Evaluate a three-lane receipt snapshot without any external side effects.

    A matching readback is a consistency result about caller-supplied material,
    never cryptographic attestation of real owner identity or permission to act.
    """
    if not isinstance(now,datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise OwnerReadbackHold("AWARE_UTC_CLOCK_REQUIRED")
    now=now.astimezone(timezone.utc)
    _schema(payload,{"date","expected_channel_id","owner_channel_checked",
                     "release_slots","remote_observations"})
    if payload["expected_channel_id"]!=CHANNEL:
        raise OwnerReadbackHold("WRONG_EXPECTED_CHANNEL")
    if type(payload["owner_channel_checked"]) is not bool:
        raise OwnerReadbackHold("INVALID_OWNER_FLAG")
    day=_day(payload["date"])
    manifest=payload["release_slots"]
    observations=payload["remote_observations"]
    if not isinstance(manifest,list) or not isinstance(observations,list) or len(manifest)!=3 or len(observations)!=3:
        raise OwnerReadbackHold("EXACT_THREE_LANES_REQUIRED")
    required_manifest={"slot","video_id","expected_title"}
    required_remote={"slot","video_id","channel_id","title","privacy_status","upload_status",
                     "processing_status","publish_at_utc","observed_at_utc"}
    by_slot,remote_by_slot={},{}
    seen_ids=set()
    for entry in manifest:
        _schema(entry,required_manifest)
        slot=entry["slot"]
        if not isinstance(slot,str) or slot not in SLOTS or slot in by_slot:
            raise OwnerReadbackHold("DUPLICATE_OR_INVALID_RELEASE_SLOT")
        _check_video(entry["video_id"])
        if entry["video_id"] in seen_ids:
            raise OwnerReadbackHold("DUPLICATE_REMOTE_VIDEO_ID")
        seen_ids.add(entry["video_id"])
        if not isinstance(entry["expected_title"],str) or not TITLE.fullmatch(entry["expected_title"]) or entry["expected_title"].strip()!=entry["expected_title"]:
            raise OwnerReadbackHold("INVALID_TITLE")
        by_slot[slot]=entry
    for entry in observations:
        _schema(entry,required_remote)
        slot=entry["slot"]
        if not isinstance(slot,str) or slot not in SLOTS or slot in remote_by_slot:
            raise OwnerReadbackHold("DUPLICATE_OR_INVALID_OBSERVATION_SLOT")
        _check_video(entry["video_id"])
        if not isinstance(entry["channel_id"],str) or len(entry["channel_id"])>64:
            raise OwnerReadbackHold("INVALID_OBSERVED_CHANNEL")
        if not isinstance(entry["title"],str) or len(entry["title"])>100:
            raise OwnerReadbackHold("INVALID_OBSERVED_TITLE")
        if entry["privacy_status"] not in ALLOWED_PRIVACY or not isinstance(entry["privacy_status"],str):
            raise OwnerReadbackHold("INVALID_PRIVACY")
        if not isinstance(entry["upload_status"],str) or entry["upload_status"] not in ("processed","uploaded","rejected","failed","deleted"):
            raise OwnerReadbackHold("INVALID_UPLOAD_STATUS")
        if not isinstance(entry["processing_status"],str) or entry["processing_status"] not in ("succeeded","processing","failed","unknown"):
            raise OwnerReadbackHold("INVALID_PROCESSING_STATUS")
        if entry["publish_at_utc"] is not None:
            _instant(entry["publish_at_utc"])
        _instant(entry["observed_at_utc"])
        remote_by_slot[slot]=entry
    if set(by_slot)!=set(SLOTS) or set(remote_by_slot)!=set(SLOTS):
        raise OwnerReadbackHold("MISSING_LANE")
    out=[]
    for slot in SLOTS:
        planned=by_slot[slot]
        remote=remote_by_slot[slot]
        target=_target(day,slot)
        actual=_instant(remote["publish_at_utc"]) if remote["publish_at_utc"] is not None else None
        seen=_instant(remote["observed_at_utc"])
        reason=[]
        if not payload["owner_channel_checked"]:
            reason.append("OWNER_CHANNEL_NOT_CHECKED")
        if remote["channel_id"]!=CHANNEL or remote["video_id"]!=planned["video_id"] or remote["title"]!=planned["expected_title"]:
            reason.append("VIDEO_IDENTITY_MISMATCH")
        if seen>now or now-seen>MAX_AGE:
            reason.append("OWNER_OBSERVATION_STALE_OR_FUTURE")
        if remote["upload_status"]!="processed" or remote["processing_status"]!="succeeded":
            reason.append("PROCESSING_NOT_VERIFIED")
        if remote["privacy_status"]!="private":
            reason.append("NOT_PRIVATE")
        if actual is None:
            reason.append("PUBLISH_AT_MISSING_DO_NOT_BLIND_RETRY")
        elif actual!=target:
            reason.append("PUBLISH_AT_CONFLICT")
        if not reason:
            state="RECEIPT_MATCHED_UNATTESTED"
        elif "VIDEO_IDENTITY_MISMATCH" in reason or "PUBLISH_AT_CONFLICT" in reason:
            state="HOLD_IDENTITY_OR_SCHEDULE_CONFLICT"
        elif "PUBLISH_AT_MISSING_DO_NOT_BLIND_RETRY" in reason and len(reason)==1:
            state="HOLD_EXISTING_PRIVATE_VIDEO_NEEDS_OWNER_REVIEW"
        else:
            state="HOLD_UNVERIFIED"
        out.append({"slot":slot,"expected_publish_at_utc":target.isoformat().replace("+00:00","Z"),
                    "decision":state,"reason_codes":reason,"video_id_redacted":True})
    matched=sum(x["decision"]=="RECEIPT_MATCHED_UNATTESTED" for x in out)
    return {
        "date":day.isoformat(),
        "state":"ALL_THREE_RECEIPTS_MATCHED_UNATTESTED" if matched==3 else "HOLD_FOR_OWNER_RECONCILIATION",
        "matched_receipts":matched,
        "slots_total":3,
        "lanes":out,
        "input_trust":"CALLER_SUPPLIED_UNATTESTED",
        "actual_google_api_calls":0,
        "remote_credentials_authenticated_here":False,
        "automatic_upload_permitted":False,
        "automatic_schedule_retry_permitted":False,
        "automatic_d1_backfill_permitted":False,
        "youtube_writes":0,
        "d1_writes":0,
        "cloud_autopilot_ready":False,
    }
