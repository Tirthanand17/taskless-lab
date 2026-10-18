"""Offline staging-agent lease prototype: no production release ledger or credentials.

A SQLite BEGIN IMMEDIATE transaction serializes each claim/retry/finish.
Monotonically increasing fencing generations stop late workers from handing
off after an expired lease. This is *not* Cloudflare D1, authenticated worker
identity, a remotely trusted clock, or authorization to render/publish.
Only source-declared 18-stage no-side-effect task contracts can be used.
"""
from __future__ import annotations

from contextlib import closing, contextmanager
from dataclasses import asdict
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3
from typing import Iterator

from .agent_org import (
    CHANNEL_ID, Handoff, State, WorkflowError, episode_workflow,
)

MAX_LEASE_SECONDS = 900
MIN_LEASE_SECONDS = 10
MAX_NOW_EPOCH = 4_102_444_800  # year 2100; offline clock bound only


def _utc_seconds(value: datetime) -> int:
    if (not isinstance(value, datetime) or value.tzinfo is None
            or value.utcoffset() is None):
        raise WorkflowError("Staging clock must be timezone aware")
    timestamp = value.timestamp()
    if timestamp != int(timestamp) or not 1_577_836_800 <= timestamp < MAX_NOW_EPOCH:
        raise WorkflowError("Staging clock out of supported whole-second bounds")
    return int(timestamp)


def _lease(seconds: int) -> int:
    if type(seconds) is not int or not MIN_LEASE_SECONDS <= seconds <= MAX_LEASE_SECONDS:
        raise WorkflowError("Bounded integer lease duration required")
    return seconds


class SQLiteStagingClaims:
    """Single SQLite-file local rehearsal of fenced task claims and recovery.

    Require the *trusted caller* to provide the exact episode/kind/language
    on reopening; the stored SHA-256 merely spots contract identity changes.
    Claim owner strings are labels, NOT authenticated cloud identities.
    """

    def __init__(self, path: Path, *, episode_id: str, kind: str,
                 language: str, create: bool = False):
        self.path = Path(path)
        if (self.path.is_symlink() or not self.path.parent.is_dir()
                or self.path.parent.is_symlink() or
                (create and self.path.exists()) or
                (not create and not self.path.is_file())):
            raise WorkflowError("Existing ordinary staging SQLite path or new fresh file required")
        self.workflow = episode_workflow(episode_id, kind=kind, language=language)
        self.contracts = self.workflow.contracts
        contract_records = [asdict(self.contracts[t]) for t in self.workflow.order]
        canonical = json.dumps(contract_records, sort_keys=True,
                               separators=(",", ":"), ensure_ascii=True)
        self.fingerprint = sha256(canonical.encode("utf-8")).hexdigest()
        if create:
            try:
                self._create()
            except Exception:
                self.path.unlink(missing_ok=True)
                raise
        else:
            with self._tx() as conn:
                self._inspect(conn)

    @contextmanager
    def _tx(self) -> Iterator[sqlite3.Connection]:
        with closing(sqlite3.connect(self.path, timeout=8,
                                     isolation_level=None)) as conn:
            conn.execute("PRAGMA busy_timeout=8000")
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def _create(self) -> None:
        with self._tx() as conn:
            conn.execute(
                "CREATE TABLE stage_policy (id INTEGER PRIMARY KEY CHECK(id=1), "
                "fingerprint TEXT NOT NULL, channel TEXT NOT NULL, "
                "budget_inr INTEGER NOT NULL CHECK(budget_inr=0), "
                "publisher_enabled INTEGER NOT NULL CHECK(publisher_enabled=0), "
                "last_now INTEGER NOT NULL DEFAULT 0)"
            )
            conn.execute(
                "CREATE TABLE stage_tasks ("
                "task_id TEXT PRIMARY KEY, owner TEXT NOT NULL, "
                "status TEXT NOT NULL, failures INTEGER NOT NULL DEFAULT 0, "
                "generation INTEGER NOT NULL DEFAULT 0, "
                "expires INTEGER NOT NULL DEFAULT 0, "
                "artifact_sha TEXT NOT NULL DEFAULT '')"
            )
            conn.execute("INSERT INTO stage_policy(id,fingerprint,channel,budget_inr,"
                         "publisher_enabled,last_now) VALUES(1,?,?,0,0,0)",
                         (self.fingerprint, CHANNEL_ID))
            for tid in self.workflow.order:
                contract = self.contracts[tid]
                conn.execute(
                    "INSERT INTO stage_tasks(task_id,owner,status) VALUES(?,?,?)",
                    (tid, contract.owner, self.workflow.runs[tid].status.value),
                )
            self._inspect(conn)

    def _inspect(self, conn: sqlite3.Connection, *,
                 allow_unblocked_transition: bool = False) -> dict:
        meta = conn.execute("SELECT fingerprint,channel,budget_inr,"
                            "publisher_enabled,last_now FROM stage_policy WHERE id=1"
                           ).fetchone()
        if (meta is None or meta[:4] !=
                (self.fingerprint, CHANNEL_ID, 0, 0)
                or type(meta[4]) is not int or meta[4] < 0):
            raise WorkflowError("Untrusted or changed offline staging policy")
        rows = conn.execute("SELECT task_id,owner,status,failures,generation,"
                            "expires,artifact_sha FROM stage_tasks").fetchall()
        if len(rows)!=len(self.contracts):
            raise WorkflowError("Staging task inventory missing or duplicated")
        found = {}
        for tid, owner, status, failures, generation, expires, artifact in rows:
            contract = self.contracts.get(tid)
            if (contract is None or owner != contract.owner
                    or status not in ("blocked","ready","running","complete","quarantined")
                    or type(failures) is not int or failures < 0
                    or failures > contract.max_retries+1
                    or type(generation) is not int or generation < 0
                    or type(expires) is not int or expires < 0
                    or not isinstance(artifact,str)
                    or (status == "complete") != bool(re.fullmatch(r"[0-9a-f]{64}",artifact))
                    or (status == "running") != (expires > 0)
                    or (status == "quarantined") !=
                       (failures == contract.max_retries+1)
                    or (status != "quarantined" and failures > contract.max_retries)):
                raise WorkflowError("Impossible offline staging task record")
            found[tid] = (status, failures, generation, expires, artifact)
        if set(found)!=set(self.contracts):
            raise WorkflowError("Duplicate or missing staging task IDs")
        for tid, (status, *_rest) in found.items():
            completed = all(found[parent][0]=="complete"
                            for parent in self.contracts[tid].requires)
            # Completion transaction can briefly have a blocked dependent
            # whose last parent has just completed, before READY promotion.
            if (status != "blocked" and not completed) or (
                status == "blocked" and completed
                and not allow_unblocked_transition
            ):
                raise WorkflowError("Staging dependency readiness invariant violated")
        return found

    def _clock(self, conn: sqlite3.Connection, now: datetime) -> int:
        sec = _utc_seconds(now)
        last = conn.execute("SELECT last_now FROM stage_policy WHERE id=1").fetchone()
        if last is None or sec < last[0]:
            raise WorkflowError("Offline staging clock moved backwards")
        conn.execute("UPDATE stage_policy SET last_now=? WHERE id=1",(sec,))
        return sec

    def _ready_after_completion(self, conn: sqlite3.Connection) -> None:
        states=self._inspect(conn, allow_unblocked_transition=True)
        for tid, (status, *_rest) in states.items():
            if status=="blocked" and all(
                states[dep][0]=="complete" for dep in self.contracts[tid].requires
            ):
                conn.execute("UPDATE stage_tasks SET status='ready' WHERE task_id=?",
                             (tid,))
        self._inspect(conn)

    def claim(self, task_id: str, *, actor: str, now: datetime,
              lease_seconds: int = 120) -> int:
        """Acquire atomic local claim; return strictly increasing fencing ID."""
        duration=_lease(lease_seconds)
        if task_id not in self.contracts or actor!=self.contracts[task_id].owner:
            raise WorkflowError("Staging task/owner mismatch")
        with self._tx() as conn:
            states=self._inspect(conn)
            sec=self._clock(conn,now)
            if states[task_id][0]!="ready":
                raise WorkflowError("Staging task not ready for a new worker claim")
            conn.execute("UPDATE stage_tasks SET status='running',"
                         "generation=generation+1,expires=? WHERE task_id=?",
                         (sec+duration,task_id))
            return conn.execute("SELECT generation FROM stage_tasks WHERE task_id=?",
                                (task_id,)).fetchone()[0]

    def heartbeat(self, task_id: str, *, actor: str, generation: int,
                  now: datetime, lease_seconds: int = 120) -> None:
        duration=_lease(lease_seconds)
        with self._tx() as conn:
            state=self._inspect(conn)
            sec=self._clock(conn,now)
            self._fence(task_id,actor,generation,sec,state)
            conn.execute("UPDATE stage_tasks SET expires=? WHERE task_id=?",
                         (sec+duration,task_id))

    def _fence(self, task_id: str, actor: str, generation: int,
               sec: int, states: dict) -> None:
        if (task_id not in self.contracts
                or actor!=self.contracts[task_id].owner
                or type(generation) is not int
                or states[task_id][0]!="running"
                or states[task_id][2]!=generation
                or states[task_id][3]<=sec):
            raise WorkflowError("Missing, expired or stale staging worker fencing token")

    def complete(self, handoff: Handoff, *, actor: str, generation: int,
                 now: datetime) -> None:
        if not isinstance(handoff,Handoff) or handoff.task_id not in self.contracts:
            raise WorkflowError("Staging output must match a known task")
        handoff.validate(self.contracts[handoff.task_id],actor)
        with self._tx() as conn:
            states=self._inspect(conn)
            sec=self._clock(conn,now)
            self._fence(handoff.task_id,actor,generation,sec,states)
            conn.execute("UPDATE stage_tasks SET status='complete',expires=0,"
                         "artifact_sha=? WHERE task_id=?",
                         (handoff.sha256_hex,handoff.task_id))
            self._ready_after_completion(conn)

    def fail(self, task_id: str, *, actor: str, generation: int,
             category: str, now: datetime) -> None:
        if not isinstance(category,str) or not re.fullmatch(r"[A-Z_]{3,64}",category):
            raise WorkflowError("Only bounded staging failure categories permitted")
        with self._tx() as conn:
            states=self._inspect(conn)
            sec=self._clock(conn,now)
            self._fence(task_id,actor,generation,sec,states)
            failures=states[task_id][1]+1
            status=("quarantined" if failures>
                    self.contracts[task_id].max_retries else "ready")
            conn.execute("UPDATE stage_tasks SET status=?,failures=?,"
                         "expires=0,generation=generation+1 WHERE task_id=?",
                         (status,failures,task_id))

    def recover_expired(self, *, now: datetime) -> tuple[str,...]:
        """Atomic expiry recovery, no model/user publishing side effects."""
        with self._tx() as conn:
            states=self._inspect(conn)
            sec=self._clock(conn,now)
            result=[]
            for tid,(status,failures,_generation,expires,_artifact) in states.items():
                if status=="running" and expires<=sec:
                    failures+=1
                    outcome=("quarantined" if failures>
                             self.contracts[tid].max_retries else "ready")
                    conn.execute("UPDATE stage_tasks SET status=?,failures=?,"
                                 "expires=0,generation=generation+1 WHERE task_id=?",
                                 (outcome,failures,tid))
                    result.append(tid)
            self._inspect(conn)
            return tuple(sorted(result))

    def report(self) -> dict:
        with self._tx() as conn:
            states=self._inspect(conn)
            ready=sorted(tid for tid,data in states.items() if data[0]=="ready")
            return {
                "episode_id":next(iter(self.contracts.values())).episode_id,
                "tasks":len(states),"ready_tasks":ready,
                "running_count":sum(x[0]=="running" for x in states.values()),
                "completed_count":sum(x[0]=="complete" for x in states.values()),
                "quarantined_count":sum(x[0]=="quarantined" for x in states.values()),
                "worker_identities_authenticated":False,
                "clock_independently_trusted":False,
                "multi_worker_d1_or_cloud_deployed":False,
                "signed_fact_or_rights_review_authenticated":False,
                "cloud_or_laptop_access":False,
                "youtube_publishing_authorized":False,
                "monthly_infrastructure_inr":0,
            }
