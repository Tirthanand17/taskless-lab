"""FlowMinute deterministic three-level agent organization; STAGING ONLY.

No network, LLM billing, OAuth, rendering, uploads, scheduling, or laptop access.
A bounded dependency graph coordinates evidence-labelled *draft* handoffs.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from contextlib import closing
from pathlib import Path
import json
import re
import sqlite3

CHANNEL_ID="UCCcL9Q_jqVq6LJmnYUSAFZA"
MAX_TASKS=64
MAX_RETRIES=2
MAX_FANOUT=4

_DEPARTMENTS={
    "research":("Research Manager",{
        "launch_researcher":"gather_evidence",
        "evergreen_researcher":"gather_evidence",
        "audience_researcher":"gather_evidence",
        "topic_scorer":"score_topics",
        "research_coordinator":"review_research_package",
    }),
    "creative":("Creative Director",{
        "hook_writer":"write_creative",
        "shorts_writer":"write_creative",
        "longform_writer":"write_creative",
        "retention_editor":"write_creative",
        "thumbnail_strategist":"write_creative",
        "series_planner":"write_creative",
    }),
    "language":("Localization Manager",{
        "english_editor":"localize_text",
        "hindi_editor":"localize_text",
        "hinglish_editor":"localize_text",
        "voice_director":"localize_text",
        "subtitle_specialist":"localize_text",
        "language_reviewer":"language_review",
    }),
    "production":("Production Director",{
        "storyboard_designer":"plan_media",
        "demo_specialist":"plan_media",
        "three_d_animator":"plan_media",
        "motion_designer":"plan_media",
        "audio_specialist":"plan_media",
        "renderer":"render_media",
        "efficiency_specialist":"profile_resources",
    }),
    "quality":("Independent Quality Director",{
        "fact_reviewer":"review_facts",
        "media_inspector":"review_media",
        "audio_language_inspector":"review_media",
        "copyright_inspector":"review_rights",
        "security_inspector":"review_security",
        "release_auditor":"review_release",
    }),
    "publishing":("Operations Manager",{
        "calendar_scheduler":"draft_schedule",
        "workflow_engineer":"draft_schedule",
        "upload_specialist":"prepare_upload_only",
        "release_verifier":"plan_verification",
        "recovery_specialist":"plan_verification",
        "cost_controller":"audit_free_capacity",
    }),
    "analytics":("Growth Analytics Manager",{
        "shorts_analyst":"plan_analytics",
        "longform_analyst":"plan_analytics",
        "language_analyst":"plan_analytics",
        "community_analyst":"plan_analytics",
        "engagement_strategist":"plan_analytics",
        "reporter":"plan_analytics",
    }),
    "learning":("Continuous Improvement Director",{
        "performance_evaluator":"evaluate_candidates",
        "prompt_researcher":"evaluate_candidates",
        "experiment_designer":"evaluate_candidates",
        "regression_engineer":"test_changes",
        "knowledge_curator":"curate_metadata",
        "release_controller":"propose_rollback",
    }),
}
_DENIED=frozenset({"upload_video","publish_video","modify_oauth","charge_money",
                   "connect_provider","change_qa_policy","access_laptop"})

class WorkflowError(ValueError):
    """Stop instead of guessing handoff permissions or release state."""

class State(str,Enum):
    BLOCKED="blocked"
    READY="ready"
    RUNNING="running"
    WAITING_REVIEW="waiting_review"
    COMPLETE="complete"
    FAILED="failed"
    QUARANTINED="quarantined"

@dataclass(frozen=True)
class Role:
    department:str
    manager:str
    specialist:str
    capability:str

def registry()->dict[str,Role]:
    result={}
    for department,(manager,specialists) in _DEPARTMENTS.items():
        for specialist,capability in specialists.items():
            role_id=department+"."+specialist
            if role_id in result or capability in _DENIED:
                raise WorkflowError("Invalid specialist capability")
            result[role_id]=Role(department,manager,specialist,capability)
    return result

ROLES=registry()

@dataclass(frozen=True)
class TaskContract:
    task_id:str
    parent_id:str
    episode_id:str
    owner:str
    objective:str
    requires:tuple[str,...]
    produces:str
    evidence_required:bool=True
    priority:int=50
    resource_units:int=1
    max_retries:int=MAX_RETRIES
    deadline_utc:str|None=None
    escalation_owner:str="master"
    permissions:tuple[str,...]=()

    def validate(self)->None:
        if not re.fullmatch(r"[a-z0-9_:-]{3,128}",self.task_id):
            raise WorkflowError("Invalid task identifier")
        if not re.fullmatch(r"[A-Za-z0-9_]{2,80}",self.episode_id):
            raise WorkflowError("Invalid episode identifier")
        if self.owner not in ROLES or self.parent_id!=ROLES[self.owner].department:
            raise WorkflowError("Task owner or department mismatch")
        if not self.objective or not self.produces or len(self.requires)>MAX_FANOUT:
            raise WorkflowError("Missing output contract or excessive dependencies")
        if len(self.requires)!=len(set(self.requires)) or self.task_id in self.requires:
            raise WorkflowError("Duplicate or self-referential dependency")
        if (not 0<=self.priority<=100 or not 0<=self.resource_units<=10
                or not 0<=self.max_retries<=MAX_RETRIES):
            raise WorkflowError("Invalid bounded task budget")
        if self.permissions!=(ROLES[self.owner].capability,):
            raise WorkflowError("Task capability not authorized for owner")
        if any(p in _DENIED for p in self.permissions):
            raise WorkflowError("Privileged side effect forbidden")
        if self.deadline_utc:
            try: deadline=datetime.fromisoformat(self.deadline_utc)
            except ValueError as exc: raise WorkflowError("Unparseable deadline") from exc
            if deadline.tzinfo is None:
                raise WorkflowError("Deadline must be timezone aware")

@dataclass(frozen=True)
class Handoff:
    task_id:str
    artifact_type:str
    sha256_hex:str
    evidence_refs:tuple[str,...]
    produced_by:str
    recorded_at_utc:str
    review_state:str="UNVERIFIED_STAGING_ARTIFACT"

    def validate(self,contract:TaskContract,actor:str)->None:
        if self.task_id!=contract.task_id or self.artifact_type!=contract.produces:
            raise WorkflowError("Wrong task artifact or output type")
        if self.produced_by!=actor or actor!=contract.owner:
            raise WorkflowError("Incorrect artifact producer")
        if not re.fullmatch(r"[0-9a-f]{64}",self.sha256_hex):
            raise WorkflowError("Artifact hash missing")
        if contract.evidence_required and not self.evidence_refs:
            raise WorkflowError("Evidence references missing")
        if any(not re.fullmatch(r"sha256:[0-9a-f]{64}",ref) for ref in self.evidence_refs):
            raise WorkflowError("Only content-addressed evidence accepted")
        if self.review_state!="UNVERIFIED_STAGING_ARTIFACT":
            raise WorkflowError("Staging cannot claim independent external approval")
        try: at=datetime.fromisoformat(self.recorded_at_utc)
        except ValueError as exc: raise WorkflowError("Invalid artifact timestamp") from exc
        if at.tzinfo is None or at.utcoffset() is None:
            raise WorkflowError("Artifact timestamp must be timezone aware")

@dataclass
class TaskRun:
    status:State=State.BLOCKED
    retries:int=0
    artifact:Handoff|None=None
    last_failure:str|None=None

class Workflow:
    """Pure draft handoffs. Nothing here can connect to or publish on YouTube."""
    def __init__(self,contracts:list[TaskContract],*,channel_id:str=CHANNEL_ID):
        if channel_id!=CHANNEL_ID:
            raise WorkflowError("Unexpected FlowMinute channel")
        if not 1<=len(contracts)<=MAX_TASKS:
            raise WorkflowError("Invalid workflow size")
        self.contracts={}
        for task in contracts:
            task.validate()
            if task.task_id in self.contracts:
                raise WorkflowError("Duplicate task ID")
            self.contracts[task.task_id]=task
        self.order=self._topological_order()
        self.runs={tid:TaskRun() for tid in self.order}
        self.events:list[dict]=[]
        self._recompute_ready()

    def _topological_order(self)->tuple[str,...]:
        for task in self.contracts.values():
            if any(dep not in self.contracts for dep in task.requires):
                raise WorkflowError("Dependency is missing")
        done=set()
        result=[]
        while len(done)<len(self.contracts):
            eligible=sorted(x for x,t in self.contracts.items()
                            if x not in done and set(t.requires)<=done)
            if not eligible: raise WorkflowError("Circular task dependency")
            for tid in eligible:
                result.append(tid)
                done.add(tid)
        return tuple(result)

    def _recompute_ready(self)->None:
        for tid in self.order:
            run=self.runs[tid]
            if run.status==State.BLOCKED and all(
                self.runs[dep].status==State.COMPLETE
                for dep in self.contracts[tid].requires):
                run.status=State.READY

    def ready(self)->tuple[str,...]:
        return tuple(sorted((tid for tid in self.order
                             if self.runs[tid].status==State.READY),
                            key=lambda x:(-self.contracts[x].priority,x)))

    def claim(self,task_id:str,*,actor:str)->None:
        task=self.contracts.get(task_id)
        if task is None or task.owner!=actor or self.runs[task_id].status!=State.READY:
            raise WorkflowError("Task unavailable or actor unauthorized")
        self.runs[task_id].status=State.RUNNING
        self._event(task_id,"claimed",actor)

    def complete(self,handoff:Handoff,*,actor:str)->None:
        task=self.contracts.get(handoff.task_id)
        if task is None or self.runs[task.task_id].status!=State.RUNNING:
            raise WorkflowError("Task has not been claimed")
        handoff.validate(task,actor)
        self.runs[task.task_id].status=State.COMPLETE
        self.runs[task.task_id].artifact=handoff
        self._event(task.task_id,"staging_handoff_complete",actor)
        self._recompute_ready()

    def fail(self,task_id:str,*,actor:str,reason:str)->None:
        task=self.contracts.get(task_id)
        if task is None or task.owner!=actor or self.runs[task_id].status!=State.RUNNING:
            raise WorkflowError("Failure unauthorized or task not running")
        if not re.fullmatch(r"[A-Z_]{3,64}",reason):
            raise WorkflowError("Only bounded failure categories may be recorded")
        run=self.runs[task_id]
        run.retries+=1
        run.last_failure=reason
        run.status=State.READY if run.retries<=task.max_retries else State.QUARANTINED
        self._event(task_id,"retry_queued" if run.status==State.READY else "quarantined",actor)

    def _event(self,task_id:str,action:str,actor:str)->None:
        self.events.append({"sequence":len(self.events)+1,"task_id":task_id,
                            "action":action,"actor":actor,
                            "at_utc":datetime.now(timezone.utc).isoformat()})

    def checkpoint(self,path:str|Path)->None:
        """Local test-only SQLite checkpoint; not a cloud production store."""
        path=Path(path)
        if not path.parent.is_dir():
            raise WorkflowError("Checkpoint directory must already exist")
        obj={"contract_version":1,"channel_id":CHANNEL_ID,
             "contracts":[asdict(self.contracts[tid]) for tid in self.order],
             "runs":{tid:{"status":run.status.value,"retries":run.retries,
                          "artifact":asdict(run.artifact) if run.artifact else None,
                          "last_failure":run.last_failure} for tid,run in self.runs.items()},
             "events":self.events,"publication_authorized":False,
             "monthly_budget_inr":0}
        payload=json.dumps(obj,sort_keys=True,separators=(",",":"))
        digest=sha256(payload.encode()).hexdigest()
        with closing(sqlite3.connect(path,timeout=10)) as conn,conn:
            conn.execute("CREATE TABLE IF NOT EXISTS workflow_snapshot (id INTEGER PRIMARY KEY CHECK(id=1), data TEXT NOT NULL, digest TEXT NOT NULL)")
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("INSERT INTO workflow_snapshot (id,data,digest) VALUES (1,?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data,digest=excluded.digest",(payload,digest))

    @classmethod
    def restore(cls,path:str|Path)->"Workflow":
        with closing(sqlite3.connect(path,timeout=10)) as conn:
            row=conn.execute("SELECT data,digest FROM workflow_snapshot WHERE id=1").fetchone()
        if row is None: raise WorkflowError("Checkpoint missing")
        payload,digest=row
        if sha256(payload.encode()).hexdigest()!=digest:
            raise WorkflowError("Checkpoint digest mismatch")
        obj=json.loads(payload)
        if (obj.get("contract_version")!=1 or obj.get("channel_id")!=CHANNEL_ID
            or obj.get("publication_authorized") is not False or obj.get("monthly_budget_inr")!=0):
            raise WorkflowError("Unsafe checkpoint policy")
        workflow=cls([TaskContract(**{**t,"requires":tuple(t["requires"]),
                                     "permissions":tuple(t["permissions"])})
                      for t in obj["contracts"]])
        if set(obj["runs"])!=set(workflow.contracts):
            raise WorkflowError("Checkpoint task IDs mismatch")
        for tid,saved in obj["runs"].items():
            run=workflow.runs[tid]
            run.status=State(saved["status"])
            run.retries=saved["retries"]
            run.last_failure=saved["last_failure"]
            if saved["artifact"] is not None:
                h=saved["artifact"]
                run.artifact=Handoff(**{**h,"evidence_refs":tuple(h["evidence_refs"])})
                run.artifact.validate(workflow.contracts[tid],workflow.contracts[tid].owner)
            if run.status==State.COMPLETE and run.artifact is None:
                raise WorkflowError("Completed task missing artifact")
            if run.status!=State.COMPLETE and run.artifact is not None:
                raise WorkflowError("Noncompleted task has artifact")
        workflow.events=obj["events"]
        return workflow

    def summary(self)->dict:
        counts={s.value:sum(r.status==s for r in self.runs.values()) for s in State}
        return {"channel_id":CHANNEL_ID,"tasks":len(self.runs),"states":counts,
                "ready":list(self.ready()),"publishing_enabled":False,
                "cloud_deployed":False,"monthly_budget_inr":0,
                "evidence_level":"STAGING_HANDOFF_METADATA_ONLY"}

def episode_workflow(episode_id:str,*,kind:str,language:str)->Workflow:
    if kind not in ("short","long") or language not in ("en","hi","hinglish"):
        raise WorkflowError("Unsupported episode format or language")
    spec=[
      ("research","research.launch_researcher",(),"research.package"),
      ("fact_review","quality.fact_reviewer",("research",),"qa.fact_attestation"),
      ("script","creative.shorts_writer" if kind=="short" else "creative.longform_writer",("fact_review",),"creative.script"),
      ("hooks","creative.hook_writer",("fact_review",),"creative.hooks"),
      ("english","language.english_editor",("script",),"language.english"),
      ("hindi","language.hindi_editor",("script",),"language.hindi"),
      ("storyboard","production.storyboard_designer",("script","hooks"),"production.storyboard"),
      ("language_review","language.language_reviewer",("english","hindi"),"language.review_record"),
      ("voice_plan","language.voice_director",("language_review",),"language.voice_plan"),
      ("narration","production.audio_specialist",("voice_plan",),"production.audio_plan"),
      ("subtitle_plan","language.subtitle_specialist",("narration","english","hindi"),"language.subtitle_plan"),
      ("render_plan","production.renderer",("storyboard","narration","subtitle_plan"),"production.render_plan"),
      ("media_review","quality.media_inspector",("render_plan",),"qa.media_attestation"),
      ("rights_review","quality.copyright_inspector",("render_plan",),"qa.rights_attestation"),
      ("release_review","quality.release_auditor",("media_review","rights_review","subtitle_plan","fact_review"),"qa.release_attestation"),
      ("schedule_draft","publishing.calendar_scheduler",("release_review",),"ops.schedule_draft"),
      ("analytics_plan","analytics.shorts_analyst" if kind=="short" else "analytics.longform_analyst",("schedule_draft",),"analytics.measurement_plan"),
      ("improve","learning.experiment_designer",("analytics_plan",),"learning.experiment_proposal"),
    ]
    contracts=[]
    for stage,owner,dependencies,output in spec:
        role=ROLES[owner]
        contracts.append(TaskContract(
            task_id=f"{episode_id.lower()}:{stage}",parent_id=role.department,
            episode_id=episode_id,owner=owner,
            objective=f"Create {output} for {kind} {language} episode, subject to evidence review",
            requires=tuple(f"{episode_id.lower()}:{dep}" for dep in dependencies),
            produces=output,permissions=(role.capability,),
            priority=90 if role.department=="quality" else 60,
            max_retries=MAX_RETRIES))
    return Workflow(contracts)

@dataclass(frozen=True)
class EpisodeSpec:
    episode_id:str
    kind:str
    language:str
    priority:int=50

class MasterOrchestrator:
    """Bounded coordinator: at most three active episodes and nine queued."""
    MAX_QUEUED_EPISODES=9
    MAX_ACTIVE_EPISODES=3

    def __init__(self,episodes:tuple[EpisodeSpec,...]):
        if not 1<=len(episodes)<=self.MAX_QUEUED_EPISODES:
            raise WorkflowError("Unsafe or empty episode queue")
        ids=set()
        self.queue=[]
        self.workflows={}
        for item in episodes:
            if not 0<=item.priority<=100 or item.episode_id in ids:
                raise WorkflowError("Duplicate episode or invalid priority")
            ids.add(item.episode_id)
            self.workflows[item.episode_id]=episode_workflow(item.episode_id,kind=item.kind,language=item.language)
            self.queue.append(item)
        self.queue.sort(key=lambda x:(-x.priority,x.episode_id))

    def active(self)->tuple[EpisodeSpec,...]:
        candidates=[item for item in self.queue
                    if not all(r.status==State.COMPLETE for r in self.workflows[item.episode_id].runs.values())]
        return tuple(candidates[:self.MAX_ACTIVE_EPISODES])

    def ready_assignments(self,*,limit:int=MAX_FANOUT)->tuple[tuple[str,str,str],...]:
        if not 1<=limit<=MAX_FANOUT:
            raise WorkflowError("Excessive specialist fan-out")
        result=[]
        for item in self.active():
            wf=self.workflows[item.episode_id]
            for task_id in wf.ready():
                result.append((item.episode_id,task_id,wf.contracts[task_id].owner))
        return tuple(result[:limit])

    def summary(self)->dict:
        return {"master":"FlowMinute Master Growth Orchestrator",
                "departments":len(_DEPARTMENTS),"specialists":len(ROLES),
                "episodes_queued":len(self.queue),"episodes_active":len(self.active()),
                "ready_tasks":len(self.ready_assignments()),
                "uploads_enabled":False,"scheduling_enabled":False,
                "max_monthly_spend_inr":0,"cloud_deployed":False,
                "status":"OFFLINE_STAGING_ORCHESTRATION_ONLY"}
