"""Phase 4F.1: reversible *SYNTHETIC-ONLY* legacy-to-canonical ledger rehearsal.

No Cloudflare, YouTube, credentials, provider readback, migration script,
durable files, production D1 writes, or upload/scheduling privileges.
The old private control-plane code has a (release_date, episode_id) key;
the new offline single-writer schema uses (channel_id, episode_id) plus UTC
slot and media-hash uniqueness. Test those conflicting constraints in memory.

Every candidate must explicitly be labeled SYNTHETIC_FIXTURE_ONLY, carry
an exact separately specified UTC slot consistent with the claimed IST day,
and remain in 'planned' state without YouTube ID. Never infer a UTC slot
from a legacy calendar day; remote/ambiguous stages are prohibited.

A clean simulation always ROLLS BACK the staged canonical inserts. Return
only aggregate counts/flags, never original synthetic record values or SQL.
All assertions are local structural observations, NOT migration approval.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from typing import Sequence
import sqlite3

from .core import CHANNEL_ID
from .phase4_offline_ledger import (
    OfflineLedger, ProtocolBlocked, EPISODE, HEX64, _instant,
)
from .phase4c_migration_preview import _slot_day_ist

FIXTURE_MARKER = "SYNTHETIC_FIXTURE_ONLY"
MAX_ROWS = 64


@dataclass(frozen=True)
class SyntheticLegacyRelease:
    fixture_marker: str
    release_date_ist: str
    episode_id: str
    planned_utc: str
    media_sha256: str
    legacy_stage: str = "planned"
    youtube_id: str | None = None


def _validate(item: SyntheticLegacyRelease) -> None:
    if not isinstance(item, SyntheticLegacyRelease) or item.fixture_marker != FIXTURE_MARKER:
        raise ProtocolBlocked("Only explicitly declared synthetic fixture inputs")
    if (not isinstance(item.episode_id, str)
            or EPISODE.fullmatch(item.episode_id) is None
            or not isinstance(item.media_sha256, str)
            or HEX64.fullmatch(item.media_sha256) is None):
        raise ProtocolBlocked("Malformed bounded synthetic episode/media identity")
    if (not isinstance(item.release_date_ist, str)
            or len(item.release_date_ist) != 10):
        raise ProtocolBlocked("Exact original IST calendar day required")
    try:
        parsed = date.fromisoformat(item.release_date_ist)
    except ValueError as exc:
        raise ProtocolBlocked("Invalid legacy calendar day") from exc
    if parsed.isoformat() != item.release_date_ist:
        raise ProtocolBlocked("Noncanonical IST date")
    # Existing canonical-UTC validator refuses local/zoned/non-second instants.
    instant = _instant(item.planned_utc)
    if instant.isoformat(timespec="seconds") != item.planned_utc:
        raise ProtocolBlocked("Exact canonical UTC timestamp required")
    if _slot_day_ist(item.planned_utc) != item.release_date_ist:
        raise ProtocolBlocked("Legacy IST date and supplied UTC slot diverge")
    if item.legacy_stage != "planned" or item.youtube_id is not None:
        raise ProtocolBlocked(
            "Remote/QA/uncertain legacy state requires authenticated reconciliation"
        )


def rehearse_synthetic_migration(
    rows: Sequence[SyntheticLegacyRelease],
    *,
    abort_after_canonical_inserts: int | None = None,
) -> dict:
    """Test the old+new uniqueness shapes with a rollback-only savepoint.

    'abort_after_canonical_inserts' injects a crash in the target simulation;
    it is never a production change. A stale or ambiguous fixture fails closed.
    No claim can override the production false flags returned by this function.
    """
    if (not isinstance(rows, (tuple, list))
            or not 1 <= len(rows) <= MAX_ROWS):
        raise ProtocolBlocked("Require 1..64 synthetic rehearsal releases")
    if (abort_after_canonical_inserts is not None
            and (type(abort_after_canonical_inserts) is not int
                 or not 1 <= abort_after_canonical_inserts <= len(rows))):
        raise ProtocolBlocked("Unsafe fault-injection fixture configuration")
    for item in rows:
        _validate(item)

    # This is a brand new process-local :memory: DB using the existing Phase 4A
    # simulator, not the user's private database or a production D1 adapter.
    ledger = OfflineLedger(":memory:", offline_test_only=True)
    db = ledger.db
    staged_count = 0
    source_count = 0
    reason = "NO_IN_MEMORY_COLLISION_OBSERVED"
    status = "SYNTHETIC_SAVEPOINT_ROLLBACK_REHEARSED"
    try:
        db.execute("""
            CREATE TABLE synthetic_legacy_releases (
                release_date TEXT NOT NULL,
                episode_id TEXT NOT NULL,
                media_sha256 TEXT NOT NULL,
                PRIMARY KEY (release_date,episode_id)
            )
        """)
        # Source load models actual private legacy primary-key behaviour.
        # Deliberately do not use user credential/account/provider rows.
        try:
            for item in rows:
                db.execute(
                    "INSERT INTO synthetic_legacy_releases "
                    "(release_date,episode_id,media_sha256) VALUES (?,?,?)",
                    (item.release_date_ist,item.episode_id,item.media_sha256),
                )
        except sqlite3.IntegrityError:
            status = "SYNTHETIC_SOURCE_IDENTITY_CONFLICT_BLOCKED"
            reason = "LEGACY_DATE_EPISODE_COLLISION"
            return _result(status,reason,0,0,len(rows),False)
        source_count=db.execute(
            "SELECT COUNT(*) FROM synthetic_legacy_releases"
        ).fetchone()[0]
        db.execute("SAVEPOINT phase4f_synthetic_rehearsal")
        try:
            for item in rows:
                # This parameterized target insertion is for the *in-memory*
                # simulator only. No SQL strings are returned for production.
                db.execute(
                    "INSERT INTO phase4_releases "
                    "(channel_id,episode_id,planned_utc,media_sha256,stage) "
                    "VALUES (?,?,?,?,?)",
                    (CHANNEL_ID,item.episode_id,item.planned_utc,
                     item.media_sha256,"planned"),
                )
                staged_count+=1
                if staged_count == abort_after_canonical_inserts:
                    raise RuntimeError("SYNTHETIC_FAULT_INJECTED")
            if db.execute("SELECT COUNT(*) FROM phase4_releases").fetchone()[0] != len(rows):
                raise ProtocolBlocked("Incomplete rehearsal target count")
            if db.execute("SELECT COUNT(*) FROM phase4_events").fetchone()[0] != 0:
                raise ProtocolBlocked("Unexpected release event side effect")
        except sqlite3.IntegrityError:
            status = "SYNTHETIC_TARGET_IDENTITY_CONFLICT_BLOCKED"
            reason = "TARGET_EPISODE_SLOT_OR_MEDIA_COLLISION"
        except RuntimeError as exc:
            if str(exc) != "SYNTHETIC_FAULT_INJECTED":
                raise
            status = "SYNTHETIC_FAILURE_INJECTION_ROLLED_BACK"
            reason = "INJECTED_CRASH_BEFORE_COMMIT"
        finally:
            # Always undo every target insert, even for a clean run.
            db.execute("ROLLBACK TO SAVEPOINT phase4f_synthetic_rehearsal")
            db.execute("RELEASE SAVEPOINT phase4f_synthetic_rehearsal")
        target_after=db.execute(
            "SELECT COUNT(*) FROM phase4_releases"
        ).fetchone()[0]
        source_after=db.execute(
            "SELECT COUNT(*) FROM synthetic_legacy_releases"
        ).fetchone()[0]
        events_after=db.execute(
            "SELECT COUNT(*) FROM phase4_events"
        ).fetchone()[0]
        if (target_after!=0 or source_after!=source_count or
                events_after!=0):
            raise ProtocolBlocked("In-memory rollback or source preservation failed")
        return _result(status,reason,staged_count,source_count,len(rows),True)
    finally:
        ledger.close()


def _result(status:str,reason:str,staged:int,source:int,
            submitted:int,rollback:bool)->dict:
    return {
        "status":status,
        "collision_or_abort_reason":reason,
        "synthetic_input_count":submitted,
        "synthetic_source_rows_intact":source==submitted and rollback,
        "staged_rows_before_rollback":staged,
        "canonical_target_rows_after_rollback":0,
        "rollback_executed_and_verified":rollback,
        "production_source_rows_read":0,
        "real_d1_schema_authenticated":False,
        "legacy_video_ids_reconciled":False,
        "real_utc_slot_mapping_verified":False,
        "media_qa_and_rights_approved":False,
        "real_migration_ready":False,
        "production_migration_authorized":False,
        "single_cloud_writer_deployed":False,
        "private_upload_authorized":False,
        "public_publishing_authorized":False,
        "generated_production_sql":[],
        "provider_connections":0,
        "production_database_writes":0,
        "persistent_files_written":0,
    }
