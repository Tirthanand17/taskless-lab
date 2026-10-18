"""Phase 4G.1: read-only integrity and crash-recovery audit of the EXISTING
Phase 4A offline SQLite ledger. This is NOT a Cloudflare D1 writer.

Only caller-created OfflineLedger simulation objects are accepted. Rebuild the
allowed stage/event trajectory in one consistent SQLite read transaction.
Count uncertain remote operations, verify row/event, media, lease-fence and
intent consistency. NEVER retry an upload/schedule or certify remote facts.

IMPORTANT: Phase 4A simulator trusts its caller's 'now_utc' and 'authenticated'
booleans. This audit neither fixes that nor connects trusted server clocks or
Google credentials. A future actual D1 writer must enforce those separately.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import timedelta
import json
import sqlite3

from .core import CHANNEL_ID
from .phase4_offline_ledger import (
    OfflineLedger, ProtocolBlocked, LOCAL_NEXT, STAGES,
    HEX64, VIDEO, _instant,
)

MAX_RELEASES=256
MAX_EVENTS=4096
VALID_ACTIONS=frozenset((
    "reserved","lease_claimed","research_verified","script_verified",
    "media_qa_passed","UPLOAD_INTENT_RESERVED_NO_NETWORK",
    "remote_private_verified","SCHEDULE_INTENT_RESERVED_NO_NETWORK",
    "scheduled_verified","public_verified","quarantined",
))
UNCERTAIN=frozenset(("upload_uncertain","schedule_uncertain"))
TERMINAL=frozenset(("public_verified","quarantined"))


def _reject() -> None:
    raise ProtocolBlocked("Offline ledger release/event integrity inconsistent")


def _reconstruct(row:sqlite3.Row, entries:list[sqlite3.Row])->dict:
    if not entries or len(entries)>MAX_EVENTS:
        _reject()
    if (row["channel_id"]!=CHANNEL_ID or row["stage"] not in STAGES
            or not isinstance(row["episode_id"],str)
            or not isinstance(row["planned_utc"],str)
            or not isinstance(row["media_sha256"],str)
            or HEX64.fullmatch(row["media_sha256"]) is None):
        _reject()
    try:
        _instant(row["planned_utc"])
    except ProtocolBlocked:
        _reject()
    stage=None
    fence=0
    uploads=0
    schedules=0
    video=None
    intent=None
    review=None
    lease_owner=None
    lease_until=None
    for expected_version,event in enumerate(entries):
        if (event["channel_id"]!=CHANNEL_ID
                or event["episode_id"]!=row["episode_id"]
                or type(event["version"]) is not int
                or event["version"]!=expected_version
                or event["action"] not in VALID_ACTIONS):
            _reject()
        try:
            _instant(event["at_utc"])
            details=json.loads(event["detail_json"])
        except (TypeError, ValueError, ProtocolBlocked):
            _reject()
        if not isinstance(details,dict) or len(details)>8:
            _reject()
        action=event["action"]
        if expected_version==0:
            if (action!="reserved"
                    or details.get("media_sha256")!=row["media_sha256"]
                    or details.get("slot_utc")!=row["planned_utc"]):
                _reject()
            stage="planned"
            continue
        if stage in TERMINAL:
            _reject()
        if action=="reserved":
            _reject()
        if action=="lease_claimed":
            fence+=1
            if (not isinstance(details.get("worker"),str)
                    or not isinstance(details.get("fence"),int)
                    or details["fence"]!=fence
                    or not isinstance(details.get("expires_utc"),str)):
                _reject()
            lease_owner=details["worker"]
            lease_until=details["expires_utc"]
            try:
                expiration=_instant(lease_until)
                claimed_at=_instant(event["at_utc"])
            except ProtocolBlocked:
                _reject()
            if not timedelta(seconds=1)<=expiration-claimed_at<=timedelta(minutes=5):
                _reject()
        elif action in ("research_verified","script_verified","media_qa_passed"):
            if LOCAL_NEXT.get(stage)!=action or lease_owner is None:
                _reject()
            stage=action
            if action=="media_qa_passed":
                # Actual row digest is not independently signed QA evidence.
                review=row["review_digest"]
                if not isinstance(review,str) or HEX64.fullmatch(review) is None:
                    _reject()
        elif action=="UPLOAD_INTENT_RESERVED_NO_NETWORK":
            if stage!="media_qa_passed" or uploads or lease_owner is None:
                _reject()
            intent=details.get("intent_id")
            if not isinstance(intent,str) or not intent:
                _reject()
            uploads+=1
            stage="upload_uncertain"
        elif action=="remote_private_verified":
            if stage!="upload_uncertain" or uploads!=1 or lease_owner is None:
                _reject()
            video=details.get("youtube_id")
            if not isinstance(video,str) or VIDEO.fullmatch(video) is None:
                _reject()
            stage="remote_private_verified"
        elif action=="SCHEDULE_INTENT_RESERVED_NO_NETWORK":
            if stage!="remote_private_verified" or schedules or lease_owner is None:
                _reject()
            schedules+=1
            stage="schedule_uncertain"
        elif action=="scheduled_verified":
            if (stage!="schedule_uncertain" or schedules!=1
                    or details.get("youtube_id")!=video
                    or details.get("publish_at_utc")!=row["planned_utc"]):
                _reject()
            stage="scheduled_verified"
        elif action=="public_verified":
            if stage!="scheduled_verified" or details.get("youtube_id")!=video:
                _reject()
            stage="public_verified"
        elif action=="quarantined":
            if not isinstance(details.get("reason"),str) or not details["reason"].strip():
                _reject()
            stage="quarantined"
        else:
            _reject()
    if (row["stage"]!=stage or row["version"]!=len(entries)-1
            or row["fence"]!=fence or row["lease_owner"]!=lease_owner
            or row["lease_until"]!=lease_until
            or row["intent_id"]!=intent or row["youtube_id"]!=video
            or (stage not in ("planned","research_verified","script_verified")
                and row["review_digest"]!=review)):
        _reject()
    if stage in ("planned","research_verified","script_verified") and row["review_digest"] is not None:
        _reject()
    return {"stage":stage,"upload_intents":uploads,"schedule_intents":schedules,
            "fences":fence}


def inspect_offline_release_recovery(ledger:OfflineLedger)->dict:
    """Read only; returns aggregated public-safe counts, never media/user IDs.

    No remote retry permission is ever issued, regardless of a clean report.
    All lease clocks in the underlying simulator are caller supplied: a
    successful audit must never be misrepresented as cloud security proof.
    """
    if type(ledger) is not OfflineLedger:
        raise ProtocolBlocked("Only existing Phase 4A offline simulator is supported")
    db=ledger.db
    if db.in_transaction:
        raise ProtocolBlocked("Cannot claim a consistent snapshot inside another transaction")
    try:
        # BEGIN starts a consistent read snapshot, ROLLBACK releases it without
        # changing anything. No other database path or external connection.
        db.execute("BEGIN")
        try:
            releases=db.execute(
                "SELECT * FROM phase4_releases ORDER BY channel_id,episode_id "
                "LIMIT ?", (MAX_RELEASES+1,),
            ).fetchall()
            events=db.execute(
                "SELECT * FROM phase4_events ORDER BY event_id LIMIT ?",
                (MAX_EVENTS+1,),
            ).fetchall()
        finally:
            db.execute("ROLLBACK")
    except sqlite3.Error as exc:
        raise ProtocolBlocked("Unreadable offline simulator tables") from None
    if len(releases)>MAX_RELEASES or len(events)>MAX_EVENTS:
        raise ProtocolBlocked("Offline ledger exceeds bounded audit size")
    event_groups=defaultdict(list)
    for e in events:
        event_groups[(e["channel_id"],e["episode_id"])].append(e)
    counts=Counter()
    versions=Counter()
    intent_total=0
    scheduled_total=0
    total_fences=0
    for row in releases:
        key=(row["channel_id"],row["episode_id"])
        reconstruction=_reconstruct(row,event_groups.pop(key,[]))
        counts[reconstruction["stage"]]+=1
        intent_total+=reconstruction["upload_intents"]
        scheduled_total+=reconstruction["schedule_intents"]
        total_fences+=reconstruction["fences"]
        versions["events"]+=row["version"]+1
    if event_groups or versions["events"]!=len(events):
        _reject()
    return {
        "status":"OFFLINE_LEDGER_EVENT_CHAIN_CONSISTENT_NOT_REMOTE_VERIFIED",
        "release_count":len(releases),
        "event_count":len(events),
        "lease_fences_seen":total_fences,
        "upload_intent_count":intent_total,
        "schedule_intent_count":scheduled_total,
        "upload_uncertain_count":counts["upload_uncertain"],
        "schedule_uncertain_count":counts["schedule_uncertain"],
        "terminal_quarantined_count":counts["quarantined"],
        "terminal_public_claim_count":counts["public_verified"],
        "needs_real_provider_reconciliation_count":
            counts["upload_uncertain"]+counts["schedule_uncertain"],
        "client_clock_trusted_by_simulator":True,
        "real_server_clock_enforced":False,
        "real_authenticated_provider_readback_verified":False,
        "real_independently_verified_media_rights":False,
        "safe_to_blindly_retry_upload":False,
        "safe_to_blindly_retry_schedule":False,
        "youtube_upload_or_scheduling_authorized":False,
        "production_cloud_ledger_writer_deployed":False,
        "public_publishing_authorized":False,
        "database_writes":0,
        "network_calls":0,
        "contains_episode_ids_or_video_ids":False,
    }
