"""ONE-TRANSACTION OFFLINE staging master and task coordinator.

All nine episode slots and all eighteen task states per episode are in ONE
SQLite database. BEGIN IMMEDIATE serializes admissions, claims, handoffs,
timeouts and quarantine, unlike the older split-file rehearsal.

This is not a deployment, authenticated service, production release ledger,
source of true time, or approval to upload. Only existing no-side-effect
FlowMinute draft agent contracts may be used.
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

from .agent_org import CHANNEL_ID, MAX_FANOUT, Handoff, WorkflowError, episode_workflow
from .agent_staging_claims import (
    MAX_HANDOFF_EVIDENCE_REFS, MAX_HANDOFF_JSON_BYTES, _lease, _utc_seconds,
)
from .agent_staging_master_queue import (
    MAX_ACTIVE_EPISODES, _validated_manifest,
)

TASK_STATES=frozenset(("blocked","ready","running","complete","quarantined","cancelled"))
EPISODE_STATES=frozenset(("queued","active","complete","quarantined"))


class UnifiedStagingCoordinator:
    """One local SQLite file for atomic admission and draft agent execution."""

    def __init__(self,path:Path,*,episodes:tuple,create:bool=False):
        self.path=Path(path)
        self.manifest,self.fingerprint,self.episodes=_validated_manifest(episodes)
        self.contracts={
            ep.episode_id:episode_workflow(
                ep.episode_id,kind=ep.kind,language=ep.language
            ).contracts for ep in self.episodes
        }
        self.order={
            ep.episode_id:episode_workflow(
                ep.episode_id,kind=ep.kind,language=ep.language
            ).order for ep in self.episodes
        }
        if (self.path.suffix!=".sqlite3" or self.path.is_symlink()
                or not self.path.parent.is_dir() or self.path.parent.is_symlink()
                or (create and self.path.exists())
                or (not create and not self.path.is_file())):
            raise WorkflowError("Unified coordinator needs one safe fresh/existing database")
        if create:
            try:
                self._create()
            except Exception:
                self.path.unlink(missing_ok=True)
                raise
        else:
            with self._tx() as db:
                self._check(db)

    @contextmanager
    def _tx(self)->Iterator[sqlite3.Connection]:
        with closing(sqlite3.connect(
                self.path,timeout=8,isolation_level=None,
        )) as db:
            db.execute("PRAGMA busy_timeout=8000")
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise

    def _create(self)->None:
        with self._tx() as db:
            db.execute(
                "CREATE TABLE queue_policy (id INTEGER PRIMARY KEY CHECK(id=1), "
                "channel TEXT NOT NULL, manifest TEXT NOT NULL, "
                "manifest_sha TEXT NOT NULL, budget_inr INTEGER NOT NULL "
                "CHECK(budget_inr=0), publishing INTEGER NOT NULL "
                "CHECK(publishing=0), last_now INTEGER NOT NULL DEFAULT 0)"
            )
            db.execute(
                "CREATE TABLE video_slots (episode TEXT PRIMARY KEY, "
                "status TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE stage_tasks (episode TEXT NOT NULL, "
                "task_id TEXT NOT NULL, owner TEXT NOT NULL, "
                "status TEXT NOT NULL, failures INTEGER NOT NULL DEFAULT 0, "
                "generation INTEGER NOT NULL DEFAULT 0, "
                "expires INTEGER NOT NULL DEFAULT 0, "
                "artifact TEXT NOT NULL DEFAULT '', "
                "handoff TEXT NOT NULL DEFAULT '', "
                "handoff_sha TEXT NOT NULL DEFAULT '', "
                "PRIMARY KEY(episode,task_id))"
            )
            db.execute(
                "INSERT INTO queue_policy VALUES(1,?,?,?,0,0,0)",
                (CHANNEL_ID,self.manifest,self.fingerprint)
            )
            for ep in self.episodes:
                eid=ep.episode_id
                db.execute("INSERT INTO video_slots VALUES(?,?)",(eid,"queued"))
                for tid in self.order[eid]:
                    contract=self.contracts[eid][tid]
                    status="ready" if not contract.requires else "blocked"
                    db.execute(
                        "INSERT INTO stage_tasks(episode,task_id,owner,status)"
                        " VALUES(?,?,?,?)",
                        (eid,tid,contract.owner,status),
                    )
            self._check(db)

    def _check(self,db:sqlite3.Connection)->tuple[dict,dict]:
        policy=db.execute(
            "SELECT channel,manifest,manifest_sha,budget_inr,publishing,last_now "
            "FROM queue_policy WHERE id=1"
        ).fetchone()
        if (policy is None or policy[:5]!=
                (CHANNEL_ID,self.manifest,self.fingerprint,0,0)
                or type(policy[5]) is not int or policy[5]<0):
            raise WorkflowError("Unified staging manifest/policy changed")
        episodes=dict(db.execute("SELECT episode,status FROM video_slots").fetchall())
        if (len(episodes)!=len(self.episodes)
                or set(episodes)!={x.episode_id for x in self.episodes}
                or any(st not in EPISODE_STATES for st in episodes.values())
                or sum(st=="active" for st in episodes.values())>MAX_ACTIVE_EPISODES):
            raise WorkflowError("Unified episode admission inventory inconsistent")
        values=db.execute(
            "SELECT episode,task_id,owner,status,failures,generation,expires,"
            "artifact,handoff,handoff_sha FROM stage_tasks"
        ).fetchall()
        expected=sum(len(x) for x in self.order.values())
        if len(values)!=expected:
            raise WorkflowError("Unified staging task inventory incomplete")
        states={}
        handoffs={}
        for eid,tid,actor,st,failures,generation,expiry,artifact,payload,digest in values:
            contract=self.contracts.get(eid,{}).get(tid)
            if (contract is None or actor!=contract.owner
                    or st not in TASK_STATES
                    or type(failures) is not int or not 0<=failures<=3
                    or type(generation) is not int or generation<0
                    or type(expiry) is not int or expiry<0
                    or (st=="running")!=(expiry>0)
                    or (st=="quarantined")!=(failures==3)
                    or (st!="quarantined" and failures>2)
                    or (st=="complete") != bool(re.fullmatch(r"[0-9a-f]{64}",artifact))
                    or (st!="complete" and (payload!="" or digest!=""))
                    or (st=="complete" and (
                        not isinstance(payload,str)
                        or len(payload.encode("utf-8"))>MAX_HANDOFF_JSON_BYTES
                        or not isinstance(digest,str)
                        or sha256(payload.encode("utf-8")).hexdigest()!=digest))
                    ):
                raise WorkflowError("Unified task state or evidence invalid")
            if st=="complete":
                try:
                    data=json.loads(payload)
                    if (not isinstance(data,dict)
                            or set(data)!={
                                "task_id","artifact_type","sha256_hex",
                                "evidence_refs","produced_by","recorded_at_utc",
                                "review_state"}
                            or not isinstance(data["evidence_refs"],list)
                            or not 1<=len(data["evidence_refs"])
                            <=MAX_HANDOFF_EVIDENCE_REFS
                            or len(set(data["evidence_refs"]))
                            !=len(data["evidence_refs"])
                            or json.dumps(data,sort_keys=True,
                                          separators=(",",":"))!=payload):
                        raise WorkflowError("Noncanonical unified handoff")
                    h=Handoff(**{**data,
                                 "evidence_refs":tuple(data["evidence_refs"])})
                    h.validate(contract,actor)
                except (TypeError,ValueError,KeyError,UnicodeError) as exc:
                    raise WorkflowError("Staging handoff metadata invalid") from exc
                if h.sha256_hex!=artifact:
                    raise WorkflowError("Staging handoff artifact digest disagrees")
                handoffs[eid,tid]=h
            states[eid,tid]=(st,failures,generation,expiry,artifact)
        if set(states)!={(e,tid) for e,tids in self.order.items()
                         for tid in tids}:
            raise WorkflowError("Unified task IDs duplicate/missing")
        for ep in self.episodes:
            eid=ep.episode_id
            sub=[states[eid,tid][0] for tid in self.order[eid]]
            episode_state=episodes[eid]
            if (episode_state=="queued" and any(
                    st not in ("ready","blocked") for st in sub)
                    or episode_state=="complete" and any(
                        st!="complete" for st in sub)
                    or episode_state=="quarantined" and (
                        not any(st=="quarantined" for st in sub)
                        or any(st in ("ready","running") for st in sub))
                    or episode_state=="active" and (
                        all(st=="complete" for st in sub)
                        or any(st=="quarantined" for st in sub))):
                raise WorkflowError("Unified episode status conflicts with task inventory")
            for tid in self.order[eid]:
                st=states[eid,tid][0]
                reqs=self.contracts[eid][tid].requires
                deps_done=all(states[eid,r][0]=="complete" for r in reqs)
                if ((st=="blocked" and deps_done
                     and episode_state not in ("quarantined",))
                     or (st not in ("blocked","cancelled") and not deps_done)):
                    raise WorkflowError("Unified DAG dependency state invalid")
                if st=="complete" and not all(
                    "sha256:"+states[eid,r][4] in
                    handoffs[eid,tid].evidence_refs for r in reqs
                ):
                    raise WorkflowError("Staging evidence loses direct parent lineage")
        return episodes,states

    def _now(self,db:sqlite3.Connection,now:datetime)->int:
        sec=_utc_seconds(now)
        last=db.execute("SELECT last_now FROM queue_policy WHERE id=1").fetchone()[0]
        if sec<last:
            raise WorkflowError("Unified offline staging clock rolled back")
        db.execute("UPDATE queue_policy SET last_now=? WHERE id=1",(sec,))
        return sec

    def _admit(self,db:sqlite3.Connection,slots:dict)->None:
        free=MAX_ACTIVE_EPISODES-sum(v=="active" for v in slots.values())
        for ep in self.episodes:
            if free==0:
                break
            if slots[ep.episode_id]=="queued":
                db.execute("UPDATE video_slots SET status='active' "
                           "WHERE episode=?",(ep.episode_id,))
                slots[ep.episode_id]="active"
                free-=1

    def _finish_or_abort(self,db:sqlite3.Connection,eid:str,
                         states:dict,slots:dict)->None:
        tasks=[(tid,states[eid,tid][0]) for tid in self.order[eid]]
        if any(st=="quarantined" for _,st in tasks):
            for tid,st in tasks:
                if st in ("ready","running"):
                    db.execute(
                        "UPDATE stage_tasks SET status='cancelled',"
                        "generation=generation+1,expires=0 WHERE episode=? "
                        "AND task_id=?",(eid,tid)
                    )
            db.execute("UPDATE video_slots SET status='quarantined' "
                       "WHERE episode=?",(eid,))
            slots[eid]="quarantined"
            self._admit(db,slots)
        elif all(st=="complete" for _,st in tasks):
            db.execute("UPDATE video_slots SET status='complete' "
                       "WHERE episode=?",(eid,))
            slots[eid]="complete"
            self._admit(db,slots)

    def reconcile(self)->dict:
        with self._tx() as db:
            slots,states=self._check(db)
            self._admit(db,slots)
            self._check(db)
            return self._report(slots,states)

    def _report(self,slots:dict,states:dict)->dict:
        by_status={
            s:[ep.episode_id for ep in self.episodes
               if slots[ep.episode_id]==s]
            for s in ("queued","active","complete","quarantined")
        }
        return {
            **by_status,
            "videos_total":len(self.episodes),
            "task_count":len(states),
            "running_tasks":sum(v[0]=="running" for v in states.values()),
            "completed_tasks":sum(v[0]=="complete" for v in states.values()),
            "active_limit":MAX_ACTIVE_EPISODES,"global_fanout":MAX_FANOUT,
            "single_sqlite_transaction_for_admission_and_tasks":True,
            "authenticated_worker_ids":False,"trusted_remote_clock":False,
            "independent_review_signatures":False,
            "production_cloud_deployed":False,
            "publish_enabled":False,"monthly_inr":0,
        }

    def report(self)->dict:
        with self._tx() as db:
            return self._report(*self._check(db))

    def assignments(self,*,limit:int=MAX_FANOUT)->tuple:
        if type(limit) is not int or not 1<=limit<=MAX_FANOUT:
            raise WorkflowError("Unified staging fanout invalid")
        with self._tx() as db:
            slots,states=self._check(db)
            open_slots=min(limit,MAX_FANOUT-sum(
                info[0]=="running" for info in states.values()
            ))
            lanes=[]
            for ep in self.episodes:
                if slots[ep.episode_id]=="active":
                    lanes.append([
                        (ep.episode_id,tid,self.contracts[ep.episode_id][tid].owner)
                        for tid in sorted(
                            (tid for tid in self.order[ep.episode_id]
                             if states[ep.episode_id,tid][0]=="ready"),
                            key=lambda tid:(-self.contracts[ep.episode_id][tid].priority,tid),
                        )
                    ])
            out=[]
            while len(out)<open_slots and any(lanes):
                for lane in lanes:
                    if lane and len(out)<open_slots:
                        out.append(lane.pop(0))
            return tuple(out)

    def _running(self,slots:dict,states:dict,eid:str,tid:str,
                 actor:str,generation:int,sec:int)->None:
        contract=self.contracts.get(eid,{}).get(tid)
        state=states.get((eid,tid))
        if (slots.get(eid)!="active" or contract is None
                or contract.owner!=actor or state is None
                or type(generation) is not int or state[0]!="running"
                or state[2]!=generation or state[3]<=sec):
            raise WorkflowError("Stale or unauthorized unified staging claim")

    def claim(self,eid:str,tid:str,*,actor:str,now:datetime,
              lease_seconds:int=120)->int:
        seconds=_lease(lease_seconds)
        with self._tx() as db:
            slots,states=self._check(db)
            current=self._now(db,now)
            contract=self.contracts.get(eid,{}).get(tid)
            if (slots.get(eid)!="active" or contract is None
                    or contract.owner!=actor or states[eid,tid][0]!="ready"
                    or sum(x[0]=="running" for x in states.values())>=MAX_FANOUT):
                raise WorkflowError("Unified staging claim denied or capacity full")
            db.execute("UPDATE stage_tasks SET status='running',"
                       "generation=generation+1,expires=? "
                       "WHERE episode=? AND task_id=?",
                       (current+seconds,eid,tid))
            generation=db.execute(
                "SELECT generation FROM stage_tasks WHERE episode=? AND task_id=?",
                (eid,tid),
            ).fetchone()[0]
            self._check(db)
            return generation

    def heartbeat(self,eid:str,tid:str,*,actor:str,generation:int,
                  now:datetime,lease_seconds:int=120)->None:
        seconds=_lease(lease_seconds)
        with self._tx() as db:
            slots,states=self._check(db)
            sec=self._now(db,now)
            self._running(slots,states,eid,tid,actor,generation,sec)
            db.execute("UPDATE stage_tasks SET expires=? WHERE episode=? "
                       "AND task_id=?",(sec+seconds,eid,tid))

    def complete(self,eid:str,handoff:Handoff,*,actor:str,
                 generation:int,now:datetime)->dict:
        if not isinstance(handoff,Handoff):
            raise WorkflowError("Unified staging requires typed handoff")
        tid=handoff.task_id
        contract=self.contracts.get(eid,{}).get(tid)
        if contract is None:
            raise WorkflowError("Cross-episode or unknown handoff")
        handoff.validate(contract,actor)
        if (not 1<=len(handoff.evidence_refs)<=MAX_HANDOFF_EVIDENCE_REFS
                or len(set(handoff.evidence_refs))!=len(handoff.evidence_refs)):
            raise WorkflowError("Unbounded or duplicate handoff evidence")
        payload=json.dumps(asdict(handoff),sort_keys=True,separators=(",",":"))
        if len(payload.encode("utf-8"))>MAX_HANDOFF_JSON_BYTES:
            raise WorkflowError("Staging evidence exceeds safe size bound")
        with self._tx() as db:
            slots,states=self._check(db)
            sec=self._now(db,now)
            self._running(slots,states,eid,tid,actor,generation,sec)
            if not all(
                "sha256:"+states[eid,parent][4] in handoff.evidence_refs
                for parent in contract.requires
            ):
                raise WorkflowError("Unified staging parent artifact missing")
            db.execute(
                "UPDATE stage_tasks SET status='complete',expires=0,"
                "artifact=?,handoff=?,handoff_sha=? WHERE episode=? AND task_id=?",
                (handoff.sha256_hex,payload,sha256(payload.encode()).hexdigest(),
                 eid,tid),
            )
            for next_tid in self.order[eid]:
                next_contract=self.contracts[eid][next_tid]
                if (next_contract.requires
                        and all(
                            db.execute("SELECT status FROM stage_tasks "
                                       "WHERE episode=? AND task_id=?",
                                       (eid,dependency)).fetchone()[0]=="complete"
                            for dependency in next_contract.requires)):
                    db.execute(
                        "UPDATE stage_tasks SET status='ready' WHERE "
                        "episode=? AND task_id=? AND status='blocked'",
                        (eid,next_tid),
                    )
            # One transaction transitions video state AND admits next video.
            after_slots,after_states=self._check(db)
            self._finish_or_abort(db,eid,after_states,after_slots)
            final_slots,final_states=self._check(db)
            return self._report(final_slots,final_states)

    def fail(self,eid:str,tid:str,*,actor:str,generation:int,
             now:datetime,category:str)->dict:
        if not isinstance(category,str) or not re.fullmatch(r"[A-Z_]{3,64}",category):
            raise WorkflowError("Only category-coded staging failure permitted")
        with self._tx() as db:
            slots,states=self._check(db)
            sec=self._now(db,now)
            self._running(slots,states,eid,tid,actor,generation,sec)
            failures=states[eid,tid][1]+1
            outcome="quarantined" if failures>=3 else "ready"
            db.execute(
                "UPDATE stage_tasks SET status=?,failures=?,expires=0,"
                "generation=generation+1 WHERE episode=? AND task_id=?",
                (outcome,failures,eid,tid),
            )
            after_slots,after_states=self._check(db)
            self._finish_or_abort(db,eid,after_states,after_slots)
            final_slots,final_states=self._check(db)
            return self._report(final_slots,final_states)

    def recover_expired(self,*,now:datetime)->tuple[str,...]:
        with self._tx() as db:
            slots,states=self._check(db)
            sec=self._now(db,now)
            changed=[]
            for (eid,tid),(st,failures,_generation,expiry,_artifact) in states.items():
                if slots[eid]=="active" and st=="running" and expiry<=sec:
                    failures+=1
                    outcome="quarantined" if failures>=3 else "ready"
                    db.execute(
                        "UPDATE stage_tasks SET status=?,failures=?,expires=0,"
                        "generation=generation+1 WHERE episode=? AND task_id=?",
                        (outcome,failures,eid,tid),
                    )
                    changed.append(tid)
            # A single expired episode may have other running tasks. Atomically
            # cancel them before releasing its video slot and filling the queue.
            mid_slots,mid_states=self._check(db)
            for ep in self.episodes:
                if mid_slots[ep.episode_id]=="active":
                    self._finish_or_abort(db,ep.episode_id,mid_states,mid_slots)
            self._check(db)
            return tuple(sorted(changed))
