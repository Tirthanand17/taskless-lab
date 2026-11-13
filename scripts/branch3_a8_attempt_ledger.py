"""CLIVOX A8: transactional SQLite attempt ledger REHEARSAL, never YouTube.

SQLite transactions/UNIQUE constraints provide atomicity among clients using
one local database file, not between ephemeral GitHub Actions runners. The
runner file is destroyed after CI and is NOT a deployed durable ledger.
No media access, Google auth, resumable upload or actual scheduling exists.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
import tempfile

from scripts.branch3_a8_private_first_dryrun import (
    CLIVOX, SHA, ID, DryRunBlocked, require, utc, candidate_attempt_key
)

ROOT = Path(__file__).resolve().parents[1]
STATE_RESERVED = "RESERVED_NO_NETWORK"
STATE_AMBIGUOUS = "UNKNOWN_REMOTE_NO_RETRY"
STATES = (STATE_RESERVED, STATE_AMBIGUOUS)
DB_SCHEMA_VERSION = 1
MAX_FILE_BYTES = 2_000_000
MAX_ATTEMPTS = 1000


class AttemptLedgerDenied(DryRunBlocked):
    """Conflicting, unsafe or ambiguous release attempt: never retry or upload."""


def block(reason: str) -> None:
    raise AttemptLedgerDenied("CLIVOX_A8_LEDGER_DENY_" + reason)


def db_location(path: Path) -> Path:
    require(isinstance(path, Path) and path.is_absolute()
            and path.suffix == ".sqlite3", "DB_LOCATION")
    require(not path.is_symlink() and ROOT not in path.parents,
            "DB_CANNOT_LIVE_IN_PUBLIC_REPO")
    require(path.parent.is_dir() and not path.parent.is_symlink(),
            "DB_PARENT")
    if path.exists():
        require(path.is_file() and path.stat().st_size <= MAX_FILE_BYTES,
                "DB_FILE_SIZE")
    return path


def connect(path: Path) -> sqlite3.Connection:
    db_location(path)
    try:
        db = sqlite3.connect(path, isolation_level=None, timeout=3)
        db.execute("PRAGMA busy_timeout = 3000")
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("PRAGMA synchronous = FULL")
        return db
    except sqlite3.Error:
        block("DATABASE_CONNECT")


def initialize(path: Path) -> None:
    """Set schema with SQLite's single-writer BEGIN IMMEDIATE transaction."""
    db = connect(path)
    try:
        db.execute("BEGIN IMMEDIATE")
        db.execute("""CREATE TABLE IF NOT EXISTS settings (
            name TEXT PRIMARY KEY NOT NULL,
            value TEXT NOT NULL
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS attempts (
            attempt_key TEXT PRIMARY KEY NOT NULL,
            channel_id TEXT NOT NULL,
            release_id TEXT UNIQUE NOT NULL,
            media_sha256 TEXT UNIQUE NOT NULL,
            metadata_sha256 TEXT NOT NULL,
            rights_sha256 TEXT NOT NULL,
            state TEXT NOT NULL CHECK (
                state IN ('RESERVED_NO_NETWORK','UNKNOWN_REMOTE_NO_RETRY')
            ),
            created_utc TEXT NOT NULL,
            updated_utc TEXT NOT NULL,
            CHECK (channel_id='UCfPEvy0SefE_5nNlYlY_CyQ')
        )""")
        db.execute("INSERT OR IGNORE INTO settings(name,value) VALUES ('schema_version','1')")
        db.execute("INSERT OR IGNORE INTO settings(name,value) VALUES ('channel_id',?)", (CLIVOX,))
        rows=dict(db.execute("SELECT name,value FROM settings"))
        if rows != {"schema_version":"1","channel_id":CLIVOX}:
            block("CORRUPT_SETTINGS")
        db.execute("COMMIT")
    except (sqlite3.Error, AttemptLedgerDenied, DryRunBlocked):
        if db.in_transaction:
            db.execute("ROLLBACK")
        block("UNSAFE_SCHEMA")
    finally:
        db.close()


def validate_time(value: str) -> str:
    dt=utc(value)
    require(dt.astimezone(timezone.utc)==dt, "UTC_TIMESTAMP_ONLY")
    require(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value) is not None,
            "EXACT_UTC_TIMESTAMP")
    return value


def reserve_simulated_attempt(
    path: Path, *, channel_id: str, release_id: str,
    media_sha256: str, metadata_sha256: str,
    rights_evidence_sha256: str, at_utc: str
) -> dict:
    """Atomic insert; any duplicate asset/release/key blocks without retry.

    This is not a release approval; positive result is only a row in a
    synthetic, process-shared rehearsal DB. No external I/O is performed.
    """
    require(channel_id==CLIVOX, "WRONG_CHANNEL")
    at=validate_time(at_utc)
    key=candidate_attempt_key(
        channel_id=channel_id, release_id=release_id,
        media_sha256=media_sha256, metadata_sha256=metadata_sha256,
        rights_evidence_sha256=rights_evidence_sha256
    )
    db=connect(path)
    try:
        db.execute("BEGIN IMMEDIATE")
        rows=dict(db.execute("SELECT name,value FROM settings"))
        if rows != {"schema_version":"1","channel_id":CLIVOX}:
            block("NO_VALID_SCHEMA")
        count=db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
        if count>=MAX_ATTEMPTS:
            block("LEDGER_CAPACITY")
        db.execute("""INSERT INTO attempts(
            attempt_key,channel_id,release_id,media_sha256,metadata_sha256,
            rights_sha256,state,created_utc,updated_utc
        ) VALUES (?,?,?,?,?,?,?,?,?)""", (
            key,channel_id,release_id,media_sha256,metadata_sha256,
            rights_evidence_sha256,STATE_RESERVED,at,at
        ))
        db.execute("COMMIT")
    except sqlite3.IntegrityError:
        if db.in_transaction:
            db.execute("ROLLBACK")
        block("DUPLICATE_RELEASE_MEDIA_OR_ATTEMPT")
    except sqlite3.Error:
        if db.in_transaction:
            db.execute("ROLLBACK")
        block("DATABASE_WRITE")
    except AttemptLedgerDenied:
        if db.in_transaction:
            db.execute("ROLLBACK")
        raise
    finally:
        db.close()
    return {
        "stage":"A8_EPHEMERAL_TRANSACTIONAL_RESERVATION_REHEARSAL",
        "local_reservation_inserted":True,
        "single_database_file_atomic_reservation_tested":True,
        "durable_across_github_action_runs":False,
        "owner_signed_real_asset_verified":False,
        "real_creator_rights_verified":False,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
        "actual_google_api_writes":0,
    }


def mark_ambiguous_no_retry(path: Path, *, attempt_key: str, at_utc: str) -> dict:
    """Once simulated network state becomes unknown, it can never be retried.

    This transition is also atomic; a repeated or out-of-order event blocks.
    """
    require(type(attempt_key) is str and SHA.fullmatch(attempt_key) is not None,
            "INVALID_ATTEMPT_KEY")
    at=validate_time(at_utc)
    db=connect(path)
    try:
        db.execute("BEGIN IMMEDIATE")
        row=db.execute(
            "SELECT state,created_utc FROM attempts WHERE attempt_key=?",
            (attempt_key,)
        ).fetchone()
        if row is None or row[0] != STATE_RESERVED:
            block("MISSING_OR_NOT_RESERVED")
        require(utc(at)>=utc(row[1]),"CLOCK_REWIND")
        changed=db.execute(
            "UPDATE attempts SET state=?,updated_utc=? "
            "WHERE attempt_key=? AND state=?",
            (STATE_AMBIGUOUS,at,attempt_key,STATE_RESERVED)
        )
        if changed.rowcount != 1:
            block("CONCURRENT_TRANSITION")
        db.execute("COMMIT")
    except sqlite3.Error:
        if db.in_transaction:
            db.execute("ROLLBACK")
        block("DATABASE_TRANSITION")
    except (DryRunBlocked, AttemptLedgerDenied):
        if db.in_transaction:
            db.execute("ROLLBACK")
        raise
    finally:
        db.close()
    return {
        "state":STATE_AMBIGUOUS,
        "remote_inventory_reconciliation_required":True,
        "automatic_retry_allowed":False,
        "upload_authorized":False,
        "youtube_api_calls":0
    }


def inspect_no_retry(path: Path, *, attempt_key: str) -> dict:
    """No path from either state to a second upload or a cleared release."""
    require(type(attempt_key) is str and SHA.fullmatch(attempt_key) is not None,
            "INVALID_ATTEMPT_KEY")
    db=connect(path)
    try:
        row=db.execute("SELECT state FROM attempts WHERE attempt_key=?",
                       (attempt_key,)).fetchone()
        if row is None or row[0] not in STATES:
            block("UNKNOWN_ATTEMPT_STATE")
        return {
            "state":row[0],
            "decision":"HOLD_REMOTE_RECONCILIATION_AND_OWNER_RELEASE",
            "automatic_retry_allowed":False,
            "youtube_upload_authorized":False,
            "youtube_schedule_authorized":False,
            "youtube_publish_authorized":False
        }
    except sqlite3.Error:
        block("DATABASE_READ")
    finally:
        db.close()


def report_fixture() -> dict:
    """All database writes occur in a throwaway GitHub runner test directory."""
    with tempfile.TemporaryDirectory(prefix="clivox-a8-no-youtube-") as parent:
        db=Path(parent)/"attempts.sqlite3"
        initialize(db)
        at="2026-11-13T04:00:00Z"
        release="clivox_synthetic_rehearsal_00001"
        reserve_simulated_attempt(
            db,channel_id=CLIVOX,release_id=release,
            media_sha256="a"*64,metadata_sha256="b"*64,
            rights_evidence_sha256="c"*64,at_utc=at
        )
        key=candidate_attempt_key(
            channel_id=CLIVOX,release_id=release,
            media_sha256="a"*64,metadata_sha256="b"*64,
            rights_evidence_sha256="c"*64
        )
        mark_ambiguous_no_retry(db,attempt_key=key,at_utc="2026-11-13T04:01:00Z")
        test=inspect_no_retry(db,attempt_key=key)
        assert test["state"]==STATE_AMBIGUOUS
    return {
        "stage":"A8_TRANSACTIONAL_SINGLE_RUNNER_EPHEMERAL_TEST_ONLY",
        "channel_id":CLIVOX,
        "ephemeral_sqlite_atomic_reservation_tested":True,
        "duplicate_release_or_asset_blocked_by_schema":True,
        "ambiguous_attempt_stays_blocked":True,
        "database_retained_after_job":False,
        "cross_runner_durable_ledger_exists":False,
        "real_remote_inventory_reconciled":False,
        "real_creator_licenses":0,
        "production_upload_credentials_configured":False,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
        "actual_youtube_api_calls":0,
    }


def perform_production_upload(*_args,**_kwargs) -> None:
    block("NO_LIVE_UPLOADER_OR_DURABLE_LEDGER")


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("fixture",),default="fixture")
    p.parse_args()
    print(json.dumps(report_fixture(),sort_keys=True))


if __name__=="__main__":
    main()
