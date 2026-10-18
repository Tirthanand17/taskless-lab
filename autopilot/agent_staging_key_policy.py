"""One-DB, zero-secret OFFLINE key enrollment, rotation and revocation.

These admin functions are direct, trusted test-process operations. They are
NOT remotely authenticated administrative endpoints. No shared secrets or
private keys are persisted: only the bounded current opaque key ID, role,
monotonically increasing key generation, active/revoked state, and tombstones.

Signed staging gateway checks require_active() in the SAME SQLite BEGIN
IMMEDIATE transaction as claim/complete, so no already-revoked key can
succeed through that local gateway, including replayed completion receipts.
"""
from __future__ import annotations
from contextlib import closing
from pathlib import Path
import re
import sqlite3

from .agent_org import ROLES, WorkflowError
from .agent_staging_unified import UnifiedStagingCoordinator

WORKER_ID_RE = re.compile(r"[a-z][a-z0-9_]{3,47}")
KEY_ID_RE = re.compile(r"[a-z][a-z0-9_-]{7,63}")
MAX_ENROLLED_WORKERS = 64
MAX_ROTATION_GENERATION = 100


class StagingKeyPolicy:
    """Nonsecret local enrollment state inside the coordinator database."""

    def __init__(self, coordinator: UnifiedStagingCoordinator):
        if not isinstance(coordinator, UnifiedStagingCoordinator):
            raise WorkflowError("Key policy must use a unified staging coordinator")
        self.db_path = Path(coordinator.path)
        with coordinator._tx() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS staging_key_policy ("
                "worker_id TEXT PRIMARY KEY, role TEXT NOT NULL, "
                "key_id TEXT NOT NULL UNIQUE, generation INTEGER NOT NULL,"
                "state TEXT NOT NULL CHECK(state IN ('active','revoked')))"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS staging_retired_keys ("
                "key_id TEXT PRIMARY KEY, worker_id TEXT NOT NULL)"
            )
            self._validate(db)

    def _tx(self):
        # The coordinating SQLite transaction primitive is reused by matching
        # absolute path through a local non-secret connection.
        return _key_transaction(self.db_path)

    def _validate(self, db: sqlite3.Connection) -> None:
        rows=db.execute(
            "SELECT worker_id,role,key_id,generation,state "
            "FROM staging_key_policy"
        ).fetchall()
        if len(rows)>MAX_ENROLLED_WORKERS:
            raise WorkflowError("Staging key inventory exceeded policy")
        for worker,role,key,generation,state in rows:
            if (not isinstance(worker,str)
                    or WORKER_ID_RE.fullmatch(worker) is None
                    or role not in ROLES
                    or not isinstance(key,str)
                    or KEY_ID_RE.fullmatch(key) is None
                    or type(generation) is not int
                    or not 1<=generation<=MAX_ROTATION_GENERATION
                    or state not in ("active","revoked")):
                raise WorkflowError("Stored key policy enrollment invalid")
        old=db.execute(
            "SELECT key_id,worker_id FROM staging_retired_keys"
        ).fetchall()
        for key,worker in old:
            if (not isinstance(key,str) or KEY_ID_RE.fullmatch(key) is None
                    or not isinstance(worker,str)
                    or WORKER_ID_RE.fullmatch(worker) is None):
                raise WorkflowError("Key tombstone inventory corrupted")
        all_keys={entry[2] for entry in rows}
        tombstones={entry[0] for entry in old}
        if (len(tombstones)!=len(old) or all_keys&tombstones):
            raise WorkflowError("Active key overlaps permanently retired key")

    def enroll(self, worker_id: str, role: str, key_id: str) -> None:
        if (not isinstance(worker_id,str)
                or WORKER_ID_RE.fullmatch(worker_id) is None
                or role not in ROLES
                or not isinstance(key_id,str)
                or KEY_ID_RE.fullmatch(key_id) is None):
            raise WorkflowError("Invalid operator-created enrollment")
        with self._tx() as db:
            self._validate(db)
            count=db.execute("SELECT count(*) FROM staging_key_policy").fetchone()[0]
            if count>=MAX_ENROLLED_WORKERS:
                raise WorkflowError("Enrollment cap reached")
            if db.execute(
                "SELECT 1 FROM staging_key_policy WHERE worker_id=?",
                (worker_id,)
            ).fetchone():
                raise WorkflowError("Worker ID already enrolled")
            if db.execute(
                "SELECT 1 FROM staging_key_policy WHERE key_id=?",
                (key_id,)
            ).fetchone() or db.execute(
                "SELECT 1 FROM staging_retired_keys WHERE key_id=?",
                (key_id,)
            ).fetchone():
                raise WorkflowError("Old or reused staging key ID")
            db.execute(
                "INSERT INTO staging_key_policy VALUES(?,?,?,1,'active')",
                (worker_id,role,key_id)
            )

    def rotate(self, worker_id: str, *, old_key_id: str,
               new_key_id: str) -> int:
        if (not isinstance(new_key_id,str)
                or KEY_ID_RE.fullmatch(new_key_id) is None):
            raise WorkflowError("Malformed new key ID")
        with self._tx() as db:
            self._validate(db)
            record=db.execute(
                "SELECT key_id,generation,state FROM staging_key_policy "
                "WHERE worker_id=?",(worker_id,)
            ).fetchone()
            if (record is None or record[0]!=old_key_id
                    or record[2]!="active"
                    or record[1]>=MAX_ROTATION_GENERATION
                    or new_key_id==old_key_id
                    or db.execute(
                        "SELECT 1 FROM staging_key_policy WHERE key_id=?",
                        (new_key_id,)
                    ).fetchone() is not None
                    or db.execute(
                        "SELECT 1 FROM staging_retired_keys WHERE key_id=?",
                        (new_key_id,)
                    ).fetchone() is not None):
                raise WorkflowError("Key rotation does not meet current policy")
            db.execute("INSERT INTO staging_retired_keys VALUES(?,?)",
                       (old_key_id,worker_id))
            db.execute(
                "UPDATE staging_key_policy SET key_id=?,generation=? "
                "WHERE worker_id=?",(new_key_id,record[1]+1,worker_id)
            )
            return record[1]+1

    def revoke(self, worker_id: str, *, expected_key_id: str) -> None:
        with self._tx() as db:
            self._validate(db)
            record=db.execute(
                "SELECT key_id,state FROM staging_key_policy WHERE worker_id=?",
                (worker_id,)
            ).fetchone()
            if (record is None or record!=(expected_key_id,"active")):
                raise WorkflowError("Revocation requires exact live key ID")
            db.execute(
                "UPDATE staging_key_policy SET state='revoked' "
                "WHERE worker_id=?",(worker_id,)
            )
            # A revoked worker ID cannot be enrolled/rotated back to active.
            # New worker identity and explicit operator enrollment are needed.

    def require_active(self, db:sqlite3.Connection,worker_id:str,
                       role:str,key_id:str)->None:
        # Caller already opened BEGIN IMMEDIATE. Check current committed
        # role/key state INSIDE that exact coordinator task transaction.
        row=db.execute(
            "SELECT role,key_id,state FROM staging_key_policy "
            "WHERE worker_id=?",(worker_id,)
        ).fetchone()
        if row!=(role,key_id,"active"):
            raise WorkflowError("Staging credential revoked, rotated or unregistered")

    def status(self)->dict:
        with self._tx() as db:
            self._validate(db)
            rows=db.execute(
                "SELECT worker_id,role,key_id,generation,state "
                "FROM staging_key_policy ORDER BY worker_id"
            ).fetchall()
            return {
                "enrollments":[{
                    "worker_id":x[0],"role":x[1],"key_id":x[2],
                    "generation":x[3],"state":x[4]
                } for x in rows],
                "stores_secrets":False,
                "admin_calls_remotely_authenticated":False,
                "locally_atomic_revocation_checks":True,
                "cloud_deployed":False,
                "youtube_publishing_authorized":False,
                "monthly_recurring_infrastructure_inr":0,
            }


from contextlib import contextmanager


@contextmanager
def _key_transaction(path:Path):
    with closing(sqlite3.connect(path,timeout=8,isolation_level=None)) as db:
        db.execute("PRAGMA busy_timeout=8000")
        db.execute("BEGIN IMMEDIATE")
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
