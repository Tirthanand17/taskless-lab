"""Phase 4H: SQLite IN-MEMORY SHADOW backup/restore rehearsal.

This is NOT a backup of Cloudflare D1, the private mounted ledger, or any
remote source. A typed tuple of untrusted legacy release records is copied
into one disposable SQLite ':memory:' database, backed up with sqlite3.backup
to a SECOND disposable in-memory database and verified after the source is
closed. A shadow rollback / tampered restoration must fail closed.

It cannot prove cloud backup recoverability, event-log integrity, source
authentication, durable writes, lease fencing, Youtube account state, or
permission to upload/schedule/publish. No filesystem/network/cloud access.
"""
from __future__ import annotations

from hashlib import sha256
from sqlite3 import DatabaseError
from datetime import date
import json
import sqlite3

from .agent_org import WorkflowError
from .cloud_release_snapshot_reconcile import (
    ReleaseSnapshot,_validate_release,MAX_ROWS,STAGES,
)

_DDL="""CREATE TABLE shadow_releases (
 release_date TEXT NOT NULL, episode_id TEXT NOT NULL,
 media_sha256 TEXT, stage TEXT NOT NULL,
 youtube_id TEXT, publish_at_utc TEXT,
 PRIMARY KEY (release_date,episode_id),
 UNIQUE(media_sha256), UNIQUE(youtube_id)
) WITHOUT ROWID"""
_INSERT="""INSERT INTO shadow_releases
 (release_date,episode_id,media_sha256,stage,youtube_id,publish_at_utc)
 VALUES (?,?,?,?,?,?)"""
_SELECT="""SELECT release_date,episode_id,media_sha256,stage,youtube_id,publish_at_utc
 FROM shadow_releases ORDER BY release_date,episode_id"""
_HEADERS=("release_date","episode_id","media_sha256","stage","youtube_id",
          "publish_at_utc")


def _validated_rows(rows:tuple[tuple,...])->tuple[tuple,...]:
    if type(rows) is not tuple or len(rows)>MAX_ROWS:
        raise WorkflowError("Bounded private-shape release record tuple required")
    by_key={}
    media=set()
    videos=set()
    for item in rows:
        if type(item) is not tuple or len(item)!=6:
            raise WorkflowError("Private release snapshot tuple shape changed")
        day,episode,digest,stage,video,scheduled=item
        model=ReleaseSnapshot(day,episode,stage,digest,video,scheduled)
        _validate_release(model)
        key=(day,episode)
        if key in by_key:
            raise WorkflowError("Repeated original release identity")
        if digest is not None:
            if digest in media:
                raise WorkflowError("Repeated original release media hash")
            media.add(digest)
        if video is not None:
            if video in videos:
                raise WorkflowError("Repeated release Youtube identity")
            videos.add(video)
        by_key[key]=item
    return tuple(by_key[key] for key in sorted(by_key))


def _sealed_digest(rows:tuple[tuple,...])->str:
    raw=json.dumps(rows,ensure_ascii=False,separators=(",",":"),
                   allow_nan=False).encode("utf-8")
    return sha256(raw).hexdigest()


def check_shadow_restore_integrity(
    original_rows:tuple[tuple,...],
    restored_rows:tuple[tuple,...],
)->dict:
    """Strict FULL row-content equivalence. Never emit row bytes or hashes."""
    first=_validated_rows(original_rows)
    second=_validated_rows(restored_rows)
    if len(first)!=len(second) or _sealed_digest(first)!=_sealed_digest(second):
        raise WorkflowError("Shadow release backup/restore mismatch; quarantine")
    if first!=second:
        # The digest comparison is not a substitute for exact comparison.
        raise WorkflowError("Shadow release backup row content changed")
    pending=sum(row[3]=="upload_started" for row in first)
    stage_counts={stage:0 for stage in STAGES}
    for row in first:
        stage_counts[row[3]]+=1
    blockers={
        "UNTRUSTED_INPUT_ROWS_NOT_LIVE_CLOUDFLARE_SNAPSHOT",
        "REAL_D1_BACKUP_RESTORE_NOT_PERFORMED",
        "RELEASE_EVENT_LOG_NOT_INCLUDED_IN_SNAPSHOT",
        "DURABLE_CLOUD_STORAGE_NOT_VERIFIED",
        "EXCLUSIVE_CLOUD_WRITER_FENCE_NOT_VERIFIED",
        "YOUTUBE_REMOTE_UPLOAD_STATE_NOT_ATTESTED",
    }
    if pending:
        blockers.add("AMBIGUOUS_UPLOAD_STARTED_MUST_NOT_AUTO_RETRY")
    if not first:
        blockers.add("EMPTY_RELEASE_HISTORY_CANNOT_PROVE_RECOVERY")
    return {
        "status":"IN_MEMORY_SHADOW_RESTORE_VERIFIED_NOT_PRODUCTION_BACKUP",
        "shadow_release_row_count":len(first),
        "shadow_restored_row_count":len(second),
        "shadow_stage_counts":stage_counts,
        "ambiguous_upload_started_count":pending,
        "entire_source_record_set_equal_in_shadow":True,
        "shadow_backup_restore_rehearsed":True,
        "production_database_backup_observed":False,
        "production_restore_executed_or_verified":False,
        "cloud_durability_verified":False,
        "event_history_recovery_verified":False,
        "single_writer_fence_verified":False,
        "owner_provenance_verified":False,
        "ambiguous_upload_retry_authorized":False,
        "migration_authorized":False,
        "upload_authorized":False,
        "publishing_authorized":False,
        "blockers":tuple(sorted(blockers)),
        "cloud_database_writes":0,
        "external_api_requests":0,
        "recurring_infrastructure_inr":0,
    }


def rehearse_in_memory_release_restore(
    *, existing_private_ledger_rows:tuple[tuple,...]
)->dict:
    """Run a disposable SQLite online-backup round-trip; NEVER open real D1."""
    original=_validated_rows(existing_private_ledger_rows)
    source=sqlite3.connect(":memory:")
    target=sqlite3.connect(":memory:")
    try:
        source.execute(_DDL)
        source.executemany(_INSERT,original)
        source.commit()
        if source.execute("PRAGMA integrity_check").fetchone()!=("ok",):
            raise WorkflowError("Source shadow SQLite integrity failed")
        source.backup(target,pages=32,sleep=0.01)
        if target.execute("PRAGMA integrity_check").fetchone()!=("ok",):
            raise WorkflowError("Restored shadow SQLite integrity failed")
        # The source is not used for readback: imitate its loss after backup.
        source.close()
        source=None
        restored=tuple(tuple(row) for row in target.execute(_SELECT))
        return check_shadow_restore_integrity(original,restored)
    except (DatabaseError,ValueError,TypeError) as exc:
        raise WorkflowError("Disposable shadow recovery rehearsal denied") from exc
    finally:
        if source is not None:
            source.close()
        target.close()
