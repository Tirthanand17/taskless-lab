"""Phase 5H: simulate safe D1 ledger recovery in ISOLATED SQLite, never production.

This code is not a D1 connector, migration runner, backfill worker, OAuth
client, media uploader, or scheduling tool. Its input is untrusted caller
metadata even if the fields say "owner verified". Its only SQL connection
is a new in-memory SQLite database with a simulation-only schema.

Purpose: detect conflict/rollback behavior for the existing releases,
release_events, UNIQUE youtube_id, and missing UNIQUE (release_date,slot_ist).
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
import re
import sqlite3
from typing import Any

CHANNEL = "UCCcL9Q_jqVq6LJmnYUSAFZA"
SLOTS = {"short_morning": (11, 0), "long": (16, 0), "short_evening": (20, 30)}
COLUMNS = frozenset(("release_date","episode_id","channel_id","slot_ist",
                     "publish_at_utc","state","media_sha256","youtube_id","updated_at_utc"))
INDEXES = frozenset(("idx_release_state","idx_release_date_slot",
                     "sqlite_autoindex_releases_1","sqlite_autoindex_releases_2"))
VIDEO = re.compile(r"[a-zA-Z0-9_-]{11}\Z")
EPISODE = re.compile(r"fm_\d{8}_(?:short|long)_(?:en|hi)\Z")
HASH = re.compile(r"[a-f0-9]{64}\Z")
DAY = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
UTC = timezone.utc


class MigrationHold(ValueError):
    """Safe static message; never add private record values."""


def _record(value: Any, expected: set[str]) -> dict:
    if not isinstance(value, dict) or set(value) != expected:
        raise MigrationHold("INVALID_RECORD_FIELDS")
    return value


def _int(value: Any) -> int:
    if type(value) is not int or value < 0 or value > 1000000:
        raise MigrationHold("INVALID_AGGREGATE")
    return value


def _date(value: Any) -> date:
    if not isinstance(value, str) or not DAY.fullmatch(value):
        raise MigrationHold("INVALID_DATE")
    try:
        out = date.fromisoformat(value)
        if out.isoformat() != value:
            raise ValueError
        return out
    except ValueError:
        raise MigrationHold("INVALID_DATE") from None


def _iso(value: Any) -> datetime:
    if not isinstance(value, str) or len(value)>40 or not value.endswith("Z"):
        raise MigrationHold("INVALID_UTC")
    try:
        d = datetime.fromisoformat(value.replace("Z","+00:00"))
        if d.utcoffset()!=timedelta(0):
            raise ValueError
        return d
    except (ValueError, OverflowError):
        raise MigrationHold("INVALID_UTC") from None


def _slot_target(day: date, slot: str) -> datetime:
    h, m = SLOTS[slot]
    local = datetime.combine(day, time(h,m),
                             tzinfo=timezone(timedelta(hours=5,minutes=30)))
    return local.astimezone(UTC)


def _preflight(packet: Any, now: datetime) -> tuple[list[dict], str]:
    _record(packet, {"release_date","channel_id","canonical_d1_metadata",
                     "owner_receipts","source_verified_by_this_module"})
    if packet["channel_id"] != CHANNEL:
        raise MigrationHold("WRONG_CHANNEL")
    if type(packet["source_verified_by_this_module"]) is not bool or \
       packet["source_verified_by_this_module"]:
        raise MigrationHold("SOURCE_PROVENANCE_MUST_REMAIN_UNATTESTED")
    day = _date(packet["release_date"])
    info = _record(packet["canonical_d1_metadata"],
                   {"release_rows","event_rows","column_names",
                    "release_indexes","date_slot_unique_index_exists",
                    "snapshot_timestamp_utc"})
    if _int(info["release_rows"]) != 0 or _int(info["event_rows"]) != 0:
        raise MigrationHold("NONEMPTY_D1_REQUIRES_INDEPENDENT_RECONCILIATION")
    if not isinstance(info["column_names"], list) or any(not isinstance(c,str) for c in info["column_names"]) or set(info["column_names"])!=COLUMNS or \
        len(info["column_names"])!=len(COLUMNS):
        raise MigrationHold("PRODUCTION_SCHEMA_NOT_CONFIRMED")
    if not isinstance(info["release_indexes"],list) or any(not isinstance(i,str) for i in info["release_indexes"]) or set(info["release_indexes"])!=INDEXES or \
        len(info["release_indexes"])!=len(INDEXES):
        raise MigrationHold("INDEX_EVIDENCE_DIFFERENT")
    if info["date_slot_unique_index_exists"] is not False:
        raise MigrationHold("DATE_SLOT_CONSTRAINT_ALREADY_CHANGED")
    _iso(info["snapshot_timestamp_utc"])
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise MigrationHold("AWARE_NOW_REQUIRED")
    now = now.astimezone(UTC)
    snapshot_age=now-_iso(info["snapshot_timestamp_utc"])
    if snapshot_age<timedelta(0) or snapshot_age>timedelta(hours=12):
        raise MigrationHold("D1_SNAPSHOT_STALE_OR_FUTURE")
    entries=packet["owner_receipts"]
    if not isinstance(entries,list) or len(entries)!=3:
        raise MigrationHold("THREE_OWNER_RECEIPTS_REQUIRED")
    seen_slots,seen_video_ids,seen_episodes=set(),set(),set()
    for e in entries:
        _record(e, {"slot","episode_id","youtube_video_id","media_sha256",
                    "channel_id","publish_at_utc","owner_observed_at_utc",
                    "privacy_status","upload_status","processing_status"})
        s=e["slot"]
        if not isinstance(s,str) or s not in SLOTS or s in seen_slots:
            raise MigrationHold("INVALID_OR_DUPLICATE_SLOT")
        ep=e["episode_id"]
        if not isinstance(ep,str) or not EPISODE.fullmatch(ep) or ep in seen_episodes or \
           not ep.startswith("fm_"+day.strftime("%Y%m%d")+"_"):
            raise MigrationHold("INVALID_OR_DUPLICATE_EPISODE")
        yid=e["youtube_video_id"]
        if not isinstance(yid,str) or not VIDEO.fullmatch(yid) or yid in seen_video_ids:
            raise MigrationHold("INVALID_OR_DUPLICATE_REMOTE_ID")
        digest=e["media_sha256"]
        if not isinstance(digest,str) or not HASH.fullmatch(digest):
            raise MigrationHold("INVALID_MEDIA_DIGEST")
        if e["channel_id"]!=CHANNEL:
            raise MigrationHold("WRONG_RECEIPT_CHANNEL")
        if _iso(e["publish_at_utc"])!=_slot_target(day,s):
            raise MigrationHold("WRONG_SLOT_PUBLISH_TIME")
        observed=_iso(e["owner_observed_at_utc"])
        if observed>now or now-observed>timedelta(hours=24):
            raise MigrationHold("STALE_OR_FUTURE_OWNER_OBSERVATION")
        if (e["privacy_status"],e["upload_status"],e["processing_status"]) != \
           ("private","processed","succeeded"):
            raise MigrationHold("UNVERIFIED_PRIVATE_PROCESSED_RELEASE")
        if s=="long" and "_long_" not in ep or \
           s!="long" and "_short_" not in ep:
            raise MigrationHold("EPISODE_TYPE_SLOT_MISMATCH")
        seen_slots.add(s);seen_video_ids.add(yid);seen_episodes.add(ep)
    if seen_slots!=set(SLOTS):
        raise MigrationHold("NOT_EXACT_THREE_SLOTS")
    return [next(x for x in entries if x["slot"]==slot) for slot in SLOTS], day.isoformat()


def _connection() -> sqlite3.Connection:
    db=sqlite3.connect(":memory:", isolation_level=None, timeout=0.2)
    db.execute("PRAGMA foreign_keys=ON")
    # The important constraints mirror live observed D1. No real D1 URI.
    db.execute("""CREATE TABLE releases (
      release_date TEXT NOT NULL, episode_id TEXT NOT NULL,
      channel_id TEXT NOT NULL, slot_ist TEXT NOT NULL,
      publish_at_utc TEXT, state TEXT NOT NULL, media_sha256 TEXT,
      youtube_id TEXT UNIQUE, updated_at_utc TEXT,
      PRIMARY KEY (release_date, episode_id))""")
    db.execute("CREATE INDEX idx_release_state ON releases(state)")
    db.execute("CREATE INDEX idx_release_date_slot ON releases(release_date,slot_ist)")
    db.execute("""CREATE TABLE release_events (
      id INTEGER PRIMARY KEY AUTOINCREMENT, release_date TEXT NOT NULL,
      episode_id TEXT NOT NULL, event_kind TEXT NOT NULL,
      detail_json TEXT, at_utc TEXT NOT NULL)""")
    return db


def _simulate(packet: dict, now: datetime, *, fault_at: str | None) -> dict:
    # Caller-supplied evidence is not authentication. No real credentials used.
    receipts, day = _preflight(packet,now)
    db=_connection()
    failure_reason=None
    rolled_back=False
    try:
        db.execute("BEGIN IMMEDIATE")
        if fault_at=="before_index":
            raise RuntimeError("SIMULATED_FAULT")
        # Requires independent safety review: production D1 must NOT receive this
        # SQL or be assumed to have a global lock after a dry run succeeds.
        db.execute("CREATE UNIQUE INDEX proposed_ux_release_date_slot ON releases(release_date,slot_ist)")
        for position,e in enumerate(receipts):
            db.execute("""INSERT INTO releases
              (release_date,episode_id,channel_id,slot_ist,publish_at_utc,state,
               media_sha256,youtube_id,updated_at_utc)
              VALUES (?,?,?,?,?,?,?,?,?)""",
              (day,e["episode_id"],CHANNEL,e["slot"],e["publish_at_utc"],
               "SCHEDULED_VERIFIED",e["media_sha256"],e["youtube_video_id"],
               now.isoformat().replace("+00:00","Z")))
            # Do not include YouTube ID/hash/private title in event payload.
            db.execute("""INSERT INTO release_events
              (release_date,episode_id,event_kind,detail_json,at_utc)
              VALUES (?,?,?,?,?)""",
              (day,e["episode_id"],"SIMULATED_RECONCILIATION","{}",
               now.isoformat().replace("+00:00","Z")))
            if fault_at=="after_first_record" and position==0:
                raise RuntimeError("SIMULATED_FAULT")
        if fault_at=="before_commit":
            raise RuntimeError("SIMULATED_FAULT")
        db.execute("COMMIT")
    except Exception:
        db.execute("ROLLBACK")
        rolled_back=True
        failure_reason="SIMULATED_TRANSACTION_ROLLED_BACK"
    rows=db.execute("SELECT COUNT(*) FROM releases").fetchone()[0]
    events=db.execute("SELECT COUNT(*) FROM release_events").fetchone()[0]
    index_exists=bool(db.execute("SELECT 1 FROM sqlite_master WHERE name='proposed_ux_release_date_slot'").fetchone())
    uniqueness_enforced=False
    if not rolled_back:
        try:
            db.execute("SAVEPOINT no_duplicate")
            db.execute("""INSERT INTO releases
              (release_date,episode_id,channel_id,slot_ist,publish_at_utc,state,
               media_sha256,youtube_id,updated_at_utc)
              VALUES (?,?,?,?,?,?,?,?,?)""",
              (day,"fm_"+day.replace("-","")+"_short_zz",CHANNEL,
               "short_morning",receipts[0]["publish_at_utc"],"PLANNED",
               "0"*64,"0123456789A","2026-10-19T00:00:00Z"))
        except sqlite3.IntegrityError:
            uniqueness_enforced=True
        finally:
            db.execute("ROLLBACK TO no_duplicate")
            db.execute("RELEASE no_duplicate")
    final_rows=db.execute("SELECT COUNT(*) FROM releases").fetchone()[0]
    db.close()
    ok=not rolled_back and rows==3 and events==3 and final_rows==3 and index_exists and uniqueness_enforced
    return {
        "status":"ISOLATED_SQLITE_REHEARSAL_PASSED" if ok else
                 "SIMULATED_FAULT_ROLLED_BACK" if rolled_back else "HOLD_REHEARSAL_FAILED",
        "source_trust":"UNATTESTED_SANITIZED_CALLER_INPUT",
        "canonical_d1_rows_in_last_observed_metadata":packet["canonical_d1_metadata"]["release_rows"],
        "sqlite_rows_after_simulation":final_rows,
        "sqlite_event_rows_after_simulation":events,
        "unique_date_slot_index_enforced_in_sqlite":uniqueness_enforced,
        "transaction_rollback_observed":rolled_back,
        "simulated_index_present":index_exists,
        "simulation_fault":failure_reason,
        "planned_slot_labels":list(SLOTS),
        "real_cloudflare_queries":0,
        "production_d1_rows_written":0,
        "real_d1_index_created":False,
        "owner_api_authenticated_in_this_module":False,
        "independent_backup_verified":False,
        "global_zero_overage_verified":False,
        "production_lease_fencing_verified":False,
        "production_migration_authorized":False,
        "production_backfill_authorized":False,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "requires_separate_owner_write_approval":True,
        "cloud_autopilot_ready":False,
    }


def rehearse(packet: dict, *, now: datetime, fault_at: str | None = None) -> dict:
    if fault_at not in (None,"before_index","after_first_record","before_commit"):
        raise MigrationHold("INVALID_FAULT_INJECTION")
    return _simulate(packet,now,fault_at=fault_at)
