"""Major Phase 4: simulated canonical D1 single-use upload reservation.

UNDEPLOYABLE by design: only creates new SQLite ':memory:' databases; never
accepts a connection, credential, account binding, URI, or external API client.
A production D1 Worker must independently implement/verify a safe migration,
writer fencing, recoverable backup and Cloudflare-native transaction semantics.

This simulation deliberately does not retry uncertain YouTube acknowledgments.
A successful MEDIA_QA_PASSED -> UPLOAD_STARTED transition is one-way until
separately authenticated manual recovery. No upload is ever performed.
"""
from __future__ import annotations
import re
import sqlite3
from datetime import date, datetime, timedelta, timezone
from typing import Any

CHANNEL = "UCCcL9Q_jqVq6LJmnYUSAFZA"
SLOTS = {"short_morning": (5, 30), "long": (10, 30), "short_evening": (15, 0)}
EPISODE = re.compile(r"fm_\d{8}_(?:short|long)_(?:en|hi)\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
DAY = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
REQUEST_FIELDS = frozenset(("release_date", "slot_ist", "episode_id", "channel_id",
                           "publish_at_utc", "media_sha256"))
STATES = frozenset(("MEDIA_QA_PASSED", "UPLOAD_STARTED", "SCHEDULED_VERIFIED",
                    "SCHEDULING_UNRESOLVED", "PUBLIC_VERIFIED"))
CAS = """UPDATE releases SET state='UPLOAD_STARTED', updated_at_utc=?
         WHERE release_date=? AND episode_id=? AND slot_ist=?
           AND channel_id=? AND publish_at_utc=? AND media_sha256=?
           AND state='MEDIA_QA_PASSED' AND youtube_id IS NULL"""
EVENT = """INSERT INTO release_events
             (release_date,episode_id,event_kind,detail_json,at_utc)
             VALUES (?,?,'SIMULATED_UPLOAD_RESERVATION','{}',?)"""


class UnsafeReservation(ValueError):
    """Static error messages; never interpolate private metadata."""


def _valid(packet: Any) -> dict:
    if type(packet) is not dict or set(packet)!=REQUEST_FIELDS:
        raise UnsafeReservation("INVALID_RESERVATION_PACKET")
    day=packet["release_date"]
    slot=packet["slot_ist"]
    episode=packet["episode_id"]
    digest=packet["media_sha256"]
    if type(day) is not str or not DAY.fullmatch(day):
        raise UnsafeReservation("INVALID_RELEASE_DATE")
    try:
        parsed=date.fromisoformat(day)
        if parsed.isoformat()!=day:
            raise ValueError
    except ValueError:
        raise UnsafeReservation("INVALID_RELEASE_DATE") from None
    if type(slot) is not str or slot not in SLOTS:
        raise UnsafeReservation("INVALID_RELEASE_SLOT")
    h,m=SLOTS[slot]
    expected=f"{day}T{h:02d}:{m:02d}:00Z"
    if packet["publish_at_utc"]!=expected:
        raise UnsafeReservation("INCORRECT_IST_UTC_SLOT")
    if packet["channel_id"]!=CHANNEL:
        raise UnsafeReservation("WRONG_CHANNEL")
    if (type(episode) is not str or not EP.fullmatch(episode) or
        not episode.startswith("fm_"+day.replace("-","")+"_") or
        (slot=="long") != ("_long_" in episode)):
        raise UnsafeReservation("INVALID_EPISODE_ID")
    if type(digest) is not str or not SHA.fullmatch(digest):
        raise UnsafeReservation("INVALID_SHA256")
    return packet


def _database(*, unique_slot:bool) -> sqlite3.Connection:
    # NEVER replace ':memory:' with a caller-provided path.
    db=sqlite3.connect(":memory:",isolation_level=None)
    db.execute("""CREATE TABLE releases (
       release_date TEXT NOT NULL, episode_id TEXT NOT NULL,
       channel_id TEXT NOT NULL, slot_ist TEXT NOT NULL,
       publish_at_utc TEXT, state TEXT NOT NULL, media_sha256 TEXT,
       youtube_id TEXT UNIQUE, updated_at_utc TEXT,
       PRIMARY KEY(release_date,episode_id))""")
    db.execute("CREATE INDEX idx_release_date_slot ON releases(release_date,slot_ist)")
    db.execute("""CREATE TABLE release_events (
       id INTEGER PRIMARY KEY AUTOINCREMENT, release_date TEXT NOT NULL,
       episode_id TEXT NOT NULL, event_kind TEXT NOT NULL,
       detail_json TEXT, at_utc TEXT NOT NULL)""")
    if unique_slot:
        db.execute("CREATE UNIQUE INDEX ux_release_date_slot ON releases(release_date,slot_ist)")
    return db


def _slot_index_verified(db:sqlite3.Connection) -> bool:
    for ix in db.execute("PRAGMA index_list('releases')"):
        # seq, name, unique, origin, partial
        if ix[2] != 1 or ix[4] != 0:
            continue
        columns=[r[2] for r in db.execute("PRAGMA index_info('"+ix[1]+"')")]
        if columns==["release_date","slot_ist"]:
            return True
    return False


def _attempt(db:sqlite3.Connection, packet:dict, *, fault:bool=False) -> str:
    if not _slot_index_verified(db):
        return "HOLD_DATE_SLOT_UNIQUENESS_NOT_PROVEN"
    args=("2026-10-20T00:00:00Z",packet["release_date"],
          packet["episode_id"],packet["slot_ist"],packet["channel_id"],
          packet["publish_at_utc"],packet["media_sha256"])
    try:
        db.execute("BEGIN IMMEDIATE")
        result=db.execute(CAS,args)
        if result.rowcount!=1:
            db.execute("ROLLBACK")
            return "HOLD_ALREADY_RESERVED_OR_IMMUTABLE_CONFLICT"
        db.execute(EVENT,(packet["release_date"],packet["episode_id"],
                          "2026-10-20T00:00:00Z"))
        if fault:
            raise RuntimeError("SYNTHETIC_TRANSACTION_INTERRUPTED")
        db.execute("COMMIT")
        return "SIMULATED_RESERVATION_ONLY_NO_EXTERNAL_UPLOAD"
    except Exception:
        if db.in_transaction:
            db.execute("ROLLBACK")
        return "HOLD_TRANSACTION_FAILURE_ROLLED_BACK"


def rehearse(packet:dict,*,unique_slot:bool=False,
             existing_state:str="MEDIA_QA_PASSED",
             altered_digest:bool=False,
             replay:bool=False,
             simulate_failure:bool=False) -> dict:
    """Run zero-network admission rehearsal and return sanitized aggregates."""
    _valid(packet)
    if any(type(v) is not bool for v in
           (unique_slot,altered_digest,replay,simulate_failure)):
        raise UnsafeReservation("INVALID_REHEARSAL_FLAGS")
    if existing_state not in STATES or type(existing_state) is not str:
        raise UnsafeReservation("INVALID_START_STATE")
    db=_database(unique_slot=unique_slot)
    try:
        digest=("0"*64 if altered_digest else packet["media_sha256"])
        db.execute("""INSERT INTO releases
            (release_date,episode_id,channel_id,slot_ist,publish_at_utc,
             state,media_sha256,youtube_id,updated_at_utc)
             VALUES (?,?,?,?,?,?,?,?,?)""",
             (packet["release_date"],packet["episode_id"],
              packet["channel_id"],packet["slot_ist"],
              packet["publish_at_utc"],existing_state,digest,
              None,"2026-10-19T00:00:00Z"))
        first=_attempt(db,packet,fault=simulate_failure)
        again=_attempt(db,packet) if replay else None
        state=db.execute("SELECT state FROM releases").fetchone()[0]
        events=db.execute("SELECT COUNT(*) FROM release_events").fetchone()[0]
        rows=db.execute("SELECT COUNT(*) FROM releases").fetchone()[0]
        return {
            "decision":first,"replayed_decision":again,
            "simulated_release_state":state,
            "simulated_release_rows":rows,"simulated_event_rows":events,
            "unique_slot_verified_in_synthetic_sqlite":_slot_index_verified(db),
            "source_trust":"SANITIZED_LOCAL_SQLITE_ONLY",
            "live_cloudflare_d1_access":False,
            "cloudflare_d1_schema_changed":False,
            "production_d1_writes":0,"real_youtube_uploads":0,
            "real_youtube_schedule_writes":0,
            "automatic_upload_retry_authorized":False,
            "owner_oauth_authenticated_here":False,
            "production_migration_authorized":False,
            "cloud_autopilot_ready":False
        }
    finally:
        db.close()
