"""Phase 5F: fail-closed, OFFLINE release-ledger reconciliation dry-run.

Does NOT access Cloudflare, Google, OAuth, GitHub actions, or any database.
Inputs are caller-asserted, sanitized evidence, NOT authenticated observations.
It does not generate SQL, modify records, recover uploads, schedule, or publish.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from collections import Counter
from typing import Any, Mapping
import re

CHANNEL = "UCCcL9Q_jqVq6LJmnYUSAFZA"
SLOTS = {"short_morning":(11,0), "long":(16,0), "short_evening":(20,30)}
ID = re.compile(r"[A-Za-z0-9_-]{11}\Z")
EPISODE = re.compile(r"fm_\d{8}_[a-z]{2,12}_[a-z]{2,12}\Z")
DATE = re.compile(r"\d{4}-\d\d-\d\d\Z")
STATES = frozenset((
    "PLANNED","RESEARCH_VERIFIED","SCRIPT_VERIFIED","MEDIA_QA_PASSED",
    "UPLOAD_STARTED","REMOTE_PRIVATE_VERIFIED","SCHEDULED_VERIFIED",
    "PUBLIC_VERIFIED","RENDERING",
))
EXTERNAL_STATES = frozenset(("SCHEDULED_VERIFIED","PUBLIC_VERIFIED","REMOTE_PRIVATE_VERIFIED","RENDERING","PLANNED","UPLOAD_STARTED"))
OBS_STATES = frozenset(("SCHEDULED_OBSERVED","PUBLIC_OBSERVED","UNKNOWN","PRIVATE_OBSERVED"))
RESULT_SOURCE = "OFFLINE_UNATTESTED_SANITIZED_INPUT"


class ReconciliationBlocked(ValueError):
    """No user-controlled payload is interpolated into diagnostic messages."""


def _shape(value: Any, keys: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ReconciliationBlocked(label)
    return value


def _day(value: Any) -> date:
    if not isinstance(value,str) or not DATE.fullmatch(value):
        raise ReconciliationBlocked("BAD_DAY")
    try:
        d=date.fromisoformat(value)
        if d.isoformat()!=value:
            raise ValueError()
        return d
    except ValueError:
        raise ReconciliationBlocked("BAD_DAY") from None


def _utc(value: Any) -> datetime | None:
    if value is None:return None
    if not isinstance(value,str) or len(value)>40 or not value.endswith("Z"):
        raise ReconciliationBlocked("BAD_UTC")
    try:
        x=datetime.fromisoformat(value.replace("Z","+00:00"))
        if x.utcoffset()!=timedelta(0):
            raise ValueError()
        return x
    except (ValueError,OverflowError):
        raise ReconciliationBlocked("BAD_UTC") from None


def _expect(day:date,slot:str)->datetime:
    if slot not in SLOTS:raise ReconciliationBlocked("BAD_SLOT")
    # IST is currently a fixed +05:30, no DST.
    h,m=SLOTS[slot]
    return datetime.combine(day,time(hour=h,minute=m),
                            tzinfo=timezone(timedelta(hours=5,minutes=30))).astimezone(timezone.utc)


def _video(value:Any)->None:
    if value is not None and (not isinstance(value,str) or not ID.fullmatch(value)):
        raise ReconciliationBlocked("BAD_VIDEO_ID")


def _count(value:Any)->int:
    if type(value) is not int or value<0 or value>1000000:
        raise ReconciliationBlocked("BAD_AGGREGATE_COUNT")
    return value


def reconcile(snapshot:Mapping[str,Any])->dict:
    """Decide only whether more authenticated verification is required.

    Raw episode IDs and YouTube IDs are compared in memory, never output.
    Even no discrepancies NEVER authorizes a write or publish.
    """
    _shape(snapshot,{"release_date","channel_id","d1","external"}, "BAD_SNAPSHOT")
    day=_day(snapshot["release_date"])
    if snapshot["channel_id"]!=CHANNEL:
        raise ReconciliationBlocked("WRONG_CHANNEL")
    d1=_shape(snapshot["d1"],{"row_count","rows","events_count","observations"}, "BAD_D1")
    row_count=_count(d1["row_count"])
    events_count=_count(d1["events_count"])
    rows=d1["rows"]
    obs=d1["observations"]
    ext=snapshot["external"]
    if not isinstance(rows,list) or len(rows)>200 or not isinstance(obs,list) or len(obs)>200:
        raise ReconciliationBlocked("UNBOUNDED_INPUT")
    if not isinstance(ext,list) or len(ext)!=3:
        raise ReconciliationBlocked("REQUIRE_EXACT_THREE_EXTERNAL_SLOTS")
    if len(rows)!=row_count:
        raise ReconciliationBlocked("D1_SNAPSHOT_NOT_COMPLETE")
    known, slots_seen, videos_seen={},set(),set()
    for r in rows:
        _shape(r,{"release_date","episode_id","channel_id","slot_ist","state","youtube_id","publish_at_utc"}, "BAD_D1_ROW")
        _day(r["release_date"])
        if r["release_date"]!=day.isoformat() or r["channel_id"]!=CHANNEL:
            raise ReconciliationBlocked("WRONG_DAY_OR_CHANNEL_ROW")
        ep=r["episode_id"]
        if not isinstance(ep,str) or not EPISODE.fullmatch(ep) or ep in known:
            raise ReconciliationBlocked("INVALID_OR_DUPLICATE_EPISODE")
        slot=r["slot_ist"]
        if not isinstance(slot,str) or slot not in SLOTS or not isinstance(r["state"],str) or r["state"] not in STATES:
            raise ReconciliationBlocked("BAD_D1_STATE_OR_SLOT")
        _video(r["youtube_id"])
        _utc(r["publish_at_utc"])
        known[ep]=r
        slots_seen.add(slot)
        if r["youtube_id"] is not None:
            if r["youtube_id"] in videos_seen:raise ReconciliationBlocked("DUPLICATE_D1_VIDEO_ID")
            videos_seen.add(r["youtube_id"])
    observed=[]
    for r in obs:
        _shape(r,{"release_date","slot_ist","status","api_rechecked","has_schedule"}, "BAD_OBSERVATION")
        _day(r["release_date"])
        if not isinstance(r["slot_ist"],str) or r["slot_ist"] not in SLOTS or \
            not isinstance(r["status"],str) or r["status"] not in OBS_STATES or \
            type(r["api_rechecked"]) is not bool or type(r["has_schedule"]) is not bool:
            raise ReconciliationBlocked("BAD_OBSERVATION_VALUE")
        observed.append(r)
    planned={}
    external_ids=set()
    for r in ext:
        _shape(r,{"slot","episode_id","youtube_id","status","publish_at_utc"}, "BAD_EXTERNAL_LANE")
        slot=r["slot"]
        ep=r["episode_id"]
        if not isinstance(slot,str) or slot not in SLOTS or slot in planned or \
          not isinstance(ep,str) or not EPISODE.fullmatch(ep) or \
          not isinstance(r["status"],str) or r["status"] not in EXTERNAL_STATES:
            raise ReconciliationBlocked("BAD_OR_DUPLICATE_EXTERNAL_LANE")
        _video(r["youtube_id"])
        expected=_expect(day,slot)
        at=_utc(r["publish_at_utc"])
        if at is not None and at!=expected:
            raise ReconciliationBlocked("WRONG_PUBLISH_INSTANT")
        if r["status"] in ("SCHEDULED_VERIFIED","PUBLIC_VERIFIED") and \
           (r["youtube_id"] is None or at is None):
            raise ReconciliationBlocked("ASSERTED_RELEASE_WITHOUT_ID_AND_TIME")
        if r["status"]=="REMOTE_PRIVATE_VERIFIED" and (r["youtube_id"] is None or at is not None):
            raise ReconciliationBlocked("PRIVATE_VIDEO_WITHOUT_SAFE_UNSCHEDULED_RECEIPT")
        if r["youtube_id"] is not None:
            if r["youtube_id"] in external_ids:
                raise ReconciliationBlocked("DUPLICATE_EXTERNAL_VIDEO_ID")
            external_ids.add(r["youtube_id"])
        planned[slot]=r
    if set(planned)!=set(SLOTS):
        raise ReconciliationBlocked("MISSING_RELEASE_SLOT")
    collisions=Counter(r["slot_ist"] for r in rows)
    slot_collisions=sum(n-1 for n in collisions.values() if n>1)
    missing_rows=0
    missing_remote_records=0
    wrong_remote_ids=0
    stuck_uploads=0
    unscheduled_private=0
    disagreements=0
    lanes=[]
    for slot in SLOTS:
        expected=planned[slot]
        remote_label="PRIVATE_LEDGER_HAS_ID_NOT_LIVE_RECHECKED" if expected["youtube_id"] \
            else "NO_EXTERNAL_VIDEO_ID"
        db=known.get(expected["episode_id"])
        reason=[]
        if expected["status"]=="REMOTE_PRIVATE_VERIFIED":
            unscheduled_private+=1
            reason.append("PRIVATE_VIDEO_SCHEDULE_NOT_VERIFIED")
        if db is None:
            missing_rows+=1
            reason.append("MISSING_CANONICAL_D1_ROW")
            if expected["youtube_id"] is not None:missing_remote_records+=1
        else:
            if db["slot_ist"]!=slot:
                reason.append("SLOT_MISMATCH");disagreements+=1
            if expected["youtube_id"]!=db["youtube_id"]:
                reason.append("REMOTE_ID_CONFLICT_OR_MISSING");wrong_remote_ids+=1
            if db["state"]=="UPLOAD_STARTED" and db["youtube_id"] is None:
                reason.append("UNCERTAIN_UPLOAD_REQUIRES_OWNER_RECONCILIATION");stuck_uploads+=1
            if _utc(db["publish_at_utc"]) is not None and \
              _utc(db["publish_at_utc"])!=_expect(day,slot):
                reason.append("D1_TIME_MISMATCH");disagreements+=1
        lanes.append({"slot":slot,"d1_present":db is not None,
                      "external_video_evidence":remote_label,
                      "verification_state":"UNATTESTED_DRY_RUN",
                      "reasons":reason})
    obs_today=sum(x["release_date"]==day.isoformat() for x in observed)
    rechecked_today=sum(x["release_date"]==day.isoformat() and x["api_rechecked"] for x in observed)
    old_observations=sum(x["release_date"]!=day.isoformat() for x in observed)
    risks=[]
    if missing_rows:risks.append("CANONICAL_LEDGER_MISSING_EPISODES")
    if missing_remote_records:risks.append("REMOTE_IDS_OUTSIDE_CANONICAL_LEDGER")
    if slot_collisions:risks.append("DUPLICATE_D1_SLOTS")
    if wrong_remote_ids:risks.append("REMOTE_ID_RECONCILIATION_NEEDED")
    if stuck_uploads:risks.append("UNCERTAIN_UPLOAD_NO_RETRY")
    if unscheduled_private:risks.append("PRIVATE_UPLOAD_SCHEDULE_UNCONFIRMED")
    if disagreements:risks.append("RELEASE_KEY_OR_TIME_CONFLICT")
    if events_count and not row_count:risks.append("EVENTS_WITHOUT_RELEASES_REVIEW")
    if rechecked_today==0:risks.append("NO_SAME_DAY_AUTHENTICATED_RECHECK_TIMESTAMP")
    return {
        "release_date":day.isoformat(),
        "status":"BLOCKED_LEDGER_DIVERGENCE" if risks else "CONSISTENT_UNATTESTED_NO_WRITE",
        "source_trust":RESULT_SOURCE,
        "canonical_d1_release_count":row_count,
        "canonical_d1_event_count":events_count,
        "d1_observations_total":len(observed),
        "prior_day_observations":old_observations,
        "current_day_observations":obs_today,
        "current_day_recheck_timestamps":rechecked_today,
        "missing_d1_episode_count":missing_rows,
        "external_video_ids_without_canonical_row":missing_remote_records,
        "d1_duplicate_slot_surplus":slot_collisions,
        "remote_id_disagreement_count":wrong_remote_ids,
        "uncertain_upload_count":stuck_uploads,
        "private_video_schedule_unconfirmed_count":unscheduled_private,
        "risk_codes":risks,
        "lanes":lanes,
        "real_owner_api_readback_performed":False,
        "real_cloudflare_query_performed_by_this_module":False,
        "automatic_backfill_authorized":False,
        "automatic_upload_retry_authorized":False,
        "automatic_schedule_retry_authorized":False,
        "canonical_ledger_write_authorized":False,
        "migration_sql_generated":[],
        "youtube_uploads_attempted":0,
        "youtube_schedule_updates":0,
        "cloud_autopilot_ready":False,
    }
