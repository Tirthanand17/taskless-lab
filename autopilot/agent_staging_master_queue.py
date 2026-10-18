"""Bounded, persistent OFFLINE master queue over fenced staging episode stores.

One small local SQLite queue file serializes admission to at most three active
episodes, from at most nine immutable draft specifications. Each admitted episode
reuses the EXISTING SQLiteStagingClaims implementation and its 18-task DAG.
There are no models, network calls, YouTube uploads, Cloudflare deployments,
charged services or production release state here.

Master queue and child SQLite files are distinct: admission isn't cross-file
atomic; a child file created before a master transaction rolls back can be
safely adopted only if its original exact contract matches. The caller must
invoke reconcile() after restart. This is NOT a distributed cloud queue.
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
    CHANNEL_ID, MAX_FANOUT, EpisodeSpec, Handoff, MasterOrchestrator,
    WorkflowError,
)
from .agent_staging_claims import SQLiteStagingClaims

MAX_ACTIVE_EPISODES=3
MAX_QUEUED_EPISODES=9
STATUSES=frozenset({"queued","active","complete","quarantined"})


def _validated_manifest(episodes: tuple[EpisodeSpec,...]) -> tuple[str,str,tuple]:
    if not isinstance(episodes,tuple) or not 1<=len(episodes)<=MAX_QUEUED_EPISODES:
        raise WorkflowError("Master queue requires one to nine fixed episode specs")
    if any(not isinstance(ep,EpisodeSpec)
           or not isinstance(ep.episode_id,str)
           or re.fullmatch(r"[a-z][a-z0-9_]{2,63}",ep.episode_id) is None
           or ep.kind not in ("short","long")
           or ep.language not in ("hi","en","hinglish")
           or type(ep.priority) is not int or not 0<=ep.priority<=100
           for ep in episodes):
        raise WorkflowError("Invalid safe staging episode identity or priority")
    if len({ep.episode_id for ep in episodes})!=len(episodes):
        raise WorkflowError("Master queue has duplicate episode identity")
    # Reuse existing DAG validation instead of authoring a second stage schema.
    MasterOrchestrator(episodes)
    by_priority=tuple(sorted(episodes,key=lambda ep:(-ep.priority,ep.episode_id)))
    manifest=json.dumps([asdict(ep) for ep in by_priority],
                        separators=(",",":"),sort_keys=True)
    return manifest,sha256(manifest.encode("utf-8")).hexdigest(),by_priority


class SQLiteStagingMasterQueue:
    """A crash-reopenable, bounded index, NOT a production publisher.

    Do not put personal information or publishing credentials in episode IDs.
    Per-episode SQLite files are in the exact already-existing parent folder.
    An external runner must not execute task stores for nonactive queue entries.
    """

    def __init__(self, path: Path, *, episodes: tuple[EpisodeSpec,...],
                 create: bool=False):
        self.path=Path(path)
        self.manifest,self.fingerprint,self.episodes=_validated_manifest(episodes)
        if (self.path.suffix!=".sqlite3" or self.path.is_symlink()
                or not self.path.parent.is_dir()
                or self.path.parent.is_symlink()
                or (create and self.path.exists())
                or (not create and not self.path.is_file())):
            raise WorkflowError("Fresh or existing non-symlink SQLite master file required")
        # Derived deterministic paths are never accepted from user/web metadata.
        self.children={
            ep.episode_id:self.path.with_name(
                self.path.stem+"-"+ep.episode_id+".sqlite3"
            ) for ep in self.episodes
        }
        if create:
            if any(path.exists() or path.is_symlink()
                   for path in self.children.values()):
                raise WorkflowError("Refusing to overwrite preexisting task stores")
            try:
                self._create()
            except Exception:
                # Only this new queue index can be removed safely here.
                self.path.unlink(missing_ok=True)
                raise
        else:
            with self._transaction() as conn:
                self._inspect(conn)

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with closing(sqlite3.connect(
            self.path,timeout=8,isolation_level=None,
        )) as conn:
            conn.execute("PRAGMA busy_timeout=8000")
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def _create(self)->None:
        with self._transaction() as conn:
            conn.execute(
                "CREATE TABLE master_policy ("
                "id INTEGER PRIMARY KEY CHECK(id=1),"
                "channel TEXT NOT NULL,"
                "manifest TEXT NOT NULL,manifest_sha TEXT NOT NULL,"
                "budget_inr INTEGER NOT NULL CHECK(budget_inr=0),"
                "upload_enabled INTEGER NOT NULL CHECK(upload_enabled=0),"
                "active_limit INTEGER NOT NULL CHECK(active_limit=3))"
            )
            conn.execute(
                "CREATE TABLE episode_queue ("
                "episode_id TEXT PRIMARY KEY,"
                "status TEXT NOT NULL CHECK(status IN "
                "('queued','active','complete','quarantined')))"
            )
            conn.execute(
                "INSERT INTO master_policy("
                "id,channel,manifest,manifest_sha,budget_inr,"
                "upload_enabled,active_limit) VALUES(1,?,?,?,0,0,3)",
                (CHANNEL_ID,self.manifest,self.fingerprint),
            )
            conn.executemany(
                "INSERT INTO episode_queue(episode_id,status) VALUES(?,?)",
                ((ep.episode_id,"queued") for ep in self.episodes),
            )
            self._inspect(conn)

    def _inspect(self,conn:sqlite3.Connection)->dict[str,str]:
        policy=conn.execute(
            "SELECT channel,manifest,manifest_sha,budget_inr,"
            "upload_enabled,active_limit FROM master_policy WHERE id=1"
        ).fetchone()
        if policy!=(CHANNEL_ID,self.manifest,self.fingerprint,0,0,
                    MAX_ACTIVE_EPISODES):
            raise WorkflowError("Master staging policy/manifest is not trusted")
        rows=conn.execute("SELECT episode_id,status FROM episode_queue").fetchall()
        records=dict(rows)
        if (len(rows)!=len(self.episodes)
                or set(records)!={ep.episode_id for ep in self.episodes}
                or any(value not in STATUSES for value in records.values())
                or sum(v=="active" for v in records.values())>
                   MAX_ACTIVE_EPISODES):
            raise WorkflowError("Invalid or excessive active draft video slots")
        for episode_id,status in records.items():
            child=self.children[episode_id]
            if child.is_symlink() or (
                status in ("active","complete","quarantined")
                and not child.is_file()
            ):
                raise WorkflowError("Active or terminal episode store unavailable")
        return records

    def _child(self,ep:EpisodeSpec,*,create:bool=False)->SQLiteStagingClaims:
        return SQLiteStagingClaims(
            self.children[ep.episode_id],
            episode_id=ep.episode_id,kind=ep.kind,
            language=ep.language,create=create,
        )

    @staticmethod
    def _terminal(report:dict)->str|None:
        if (report["quarantined_count"]>0
                and report["running_count"]==0
                and not report["ready_tasks"]):
            return "quarantined"
        if (report["tasks"]==18 and report["completed_count"]==18
                and report["running_count"]==0
                and report["quarantined_count"]==0
                and not report["ready_tasks"]
                and report["durable_staging_handoffs_verified"]==18):
            return "complete"
        return None

    def reconcile(self)->dict:
        """Check real local child stores, close terminal slots, fill max three.

        Serialized master transactions stop two processes from admitting
        four active episodes. A leftover child store from interrupted
        admission is reopened only after validating its exact safe contract.
        """
        with self._transaction() as conn:
            states=self._inspect(conn)
            for ep in self.episodes:
                if states[ep.episode_id]!="active":
                    continue
                child=self._child(ep)
                # A hard stage quarantine aborts any simultaneously
                # running/ready independent sibling stage before the master
                # releases this episode's active slot.
                child.abort_quarantined_siblings()
                report=child.report()
                terminal=self._terminal(report)
                if terminal:
                    conn.execute(
                        "UPDATE episode_queue SET status=? WHERE episode_id=?",
                        (terminal,ep.episode_id),
                    )
                    states[ep.episode_id]=terminal
            remaining=MAX_ACTIVE_EPISODES-sum(
                status=="active" for status in states.values()
            )
            for ep in self.episodes:
                if remaining==0:
                    break
                if states[ep.episode_id]!="queued":
                    continue
                child_path=self.children[ep.episode_id]
                # Crash between child creation and master COMMIT can leave
                # an orphan; reopen and validate, NEVER truncate.
                self._child(ep,create=not child_path.exists())
                conn.execute(
                    "UPDATE episode_queue SET status='active' WHERE episode_id=?",
                    (ep.episode_id,),
                )
                states[ep.episode_id]="active"
                remaining-=1
            return self._snapshot(states)

    def _snapshot(self,states:dict[str,str])->dict:
        ids_by_status={
            state:[ep.episode_id for ep in self.episodes
                   if states[ep.episode_id]==state]
            for state in ("queued","active","complete","quarantined")
        }
        return {
            "episode_count":len(self.episodes),
            "queued":ids_by_status["queued"],
            "active":ids_by_status["active"],
            "complete":ids_by_status["complete"],
            "quarantined":ids_by_status["quarantined"],
            "active_cap":MAX_ACTIVE_EPISODES,
            "queue_cap":MAX_QUEUED_EPISODES,
            "monthly_budget_inr":0,
            "publication_enabled":False,
            "cloud_deployed":False,
            "worker_identities_authenticated":False,
            "trusted_server_clock":False,
            "separate_child_dbs_atomically_committed":False,
            "staging_only":True,
        }

    def report(self)->dict:
        with self._transaction() as conn:
            return self._snapshot(self._inspect(conn))

    def _active_workload(self, states:dict[str,str]) -> tuple[int,list[list[tuple[str,str,str]]]]:
        """Review all current child states while holding master transaction."""
        running=0
        lanes=[]
        for ep in self.episodes:
            if states[ep.episode_id]!="active":
                continue
            store=self._child(ep)
            report=store.report()
            running+=report["running_count"]
            ready=sorted(
                report["ready_tasks"],
                key=lambda tid:(-store.contracts[tid].priority,tid),
            )
            lanes.append([
                (ep.episode_id,tid,store.contracts[tid].owner)
                for tid in ready
            ])
        return running,lanes

    def ready_assignments(self,*,limit:int=MAX_FANOUT)->tuple[tuple[str,str,str],...]:
        """Advisory draft candidates, fairness and global active worker cap.

        Iterate one task from each active episode before taking a second
        from any episode, rather than filling all four slots with the first
        video's parallel draft tasks. Claims must use claim_active().
        """
        if type(limit) is not int or not 1<=limit<=MAX_FANOUT:
            raise WorkflowError("Master agent fanout exceeds staging policy")
        with self._transaction() as conn:
            states=self._inspect(conn)
            running,lanes=self._active_workload(states)
            available=min(limit,max(0,MAX_FANOUT-running))
            suggestions=[]
            while len(suggestions)<available and any(lanes):
                for lane in lanes:
                    if lane and len(suggestions)<available:
                        suggestions.append(lane.pop(0))
            return tuple(suggestions)

    def _require_active(self,states:dict[str,str],episode_id:str)->EpisodeSpec:
        for ep in self.episodes:
            if ep.episode_id==episode_id and states[episode_id]=="active":
                return ep
        raise WorkflowError("Only a master-admitted active staging video may run")

    def claim_active(self,episode_id:str,task_id:str,*,actor:str,now:datetime,
                     lease_seconds:int=120)->int:
        """Master-serialized active admission plus child-fenced task claim.

        Both SQLite databases are local; this is not a production security
        boundary against someone opening a child file directly.
        """
        with self._transaction() as conn:
            states=self._inspect(conn)
            ep=self._require_active(states,episode_id)
            running,_lanes=self._active_workload(states)
            if running>=MAX_FANOUT:
                raise WorkflowError("Global staging task fanout limit reached")
            return self._child(ep).claim(
                task_id,actor=actor,now=now,lease_seconds=lease_seconds
            )

    def heartbeat_active(self,episode_id:str,task_id:str,*,actor:str,
                         generation:int,now:datetime,lease_seconds:int=120)->None:
        with self._transaction() as conn:
            ep=self._require_active(self._inspect(conn),episode_id)
            self._child(ep).heartbeat(
                task_id,actor=actor,generation=generation,now=now,
                lease_seconds=lease_seconds,
            )

    def complete_active(self,episode_id:str,handoff:Handoff,*,actor:str,
                        generation:int,now:datetime)->None:
        with self._transaction() as conn:
            ep=self._require_active(self._inspect(conn),episode_id)
            if (not isinstance(handoff,Handoff)
                    or handoff.task_id not in self._child(ep).contracts):
                raise WorkflowError("Handoff cannot cross active video boundaries")
            self._child(ep).complete(handoff,actor=actor,
                                     generation=generation,now=now)

    def fail_active(self,episode_id:str,task_id:str,*,actor:str,
                    generation:int,category:str,now:datetime)->None:
        with self._transaction() as conn:
            ep=self._require_active(self._inspect(conn),episode_id)
            self._child(ep).fail(task_id,actor=actor,generation=generation,
                                 category=category,now=now)

    def recover_expired_active(self,episode_id:str,*,now:datetime)->tuple[str,...]:
        """Recover lost task leases for one admitted episode; reconcile separately."""
        with self._transaction() as conn:
            ep=self._require_active(self._inspect(conn),episode_id)
            return self._child(ep).recover_expired(now=now)
