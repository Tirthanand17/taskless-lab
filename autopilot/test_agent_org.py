"""FlowMinute offline agent coordination and safety regression tests."""
import sqlite3
import tempfile
import unittest
from contextlib import closing
from dataclasses import replace
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import Path
from autopilot.agent_org import (
    CHANNEL_ID,Handoff,ROLES,State,TaskContract,Workflow,WorkflowError,
    episode_workflow,registry,MasterOrchestrator,EpisodeSpec
)
from autopilot.agent_org_demo import preview

def receipt(flow,task_id,*,evidence=True,actor=None,output=None):
    task=flow.contracts[task_id]
    actor=actor or task.owner
    digest=sha256((task_id+task.produces).encode()).hexdigest()
    return Handoff(task_id,output or task.produces,digest,
                   ("sha256:"+digest,) if evidence else (),actor,
                   datetime(2026,10,17,12,tzinfo=timezone.utc).isoformat())

class AgentOrgTests(unittest.TestCase):
    def setUp(self):
        self.w=episode_workflow("oct17_ep01",kind="short",language="hi")

    def test_eight_departments_and_bounded_specialists(self):
        self.assertEqual(len({r.department for r in ROLES.values()}),8)
        self.assertEqual(len(ROLES),48)
        self.assertEqual(registry(),ROLES)
        self.assertNotIn("upload_video",{r.capability for r in ROLES.values()})
    def test_dag_and_master_visibility(self):
        self.assertEqual(len(self.w.order),18)
        self.assertEqual(self.w.ready(),("oct17_ep01:research",))
        self.assertFalse(self.w.summary()["publishing_enabled"])
        self.assertFalse(self.w.summary()["cloud_deployed"])
    def test_wrong_actor_cannot_claim(self):
        with self.assertRaises(WorkflowError):
            self.w.claim("oct17_ep01:research",actor="creative.shorts_writer")
    def test_wrong_actor_cannot_complete(self):
        tid=self.w.ready()[0]
        self.w.claim(tid,actor=self.w.contracts[tid].owner)
        with self.assertRaises(WorkflowError):
            self.w.complete(receipt(self.w,tid,actor="creative.shorts_writer"),
                            actor="creative.shorts_writer")
    def test_missing_evidence_blocks_next_stage(self):
        tid=self.w.ready()[0];owner=self.w.contracts[tid].owner
        self.w.claim(tid,actor=owner)
        with self.assertRaises(WorkflowError):
            self.w.complete(receipt(self.w,tid,evidence=False),actor=owner)
        self.assertEqual(self.w.runs["oct17_ep01:fact_review"].status,State.BLOCKED)
    def test_fact_review_independent(self):
        self.assertNotEqual(self.w.contracts["oct17_ep01:research"].parent_id,
                            self.w.contracts["oct17_ep01:fact_review"].parent_id)
        self.assertEqual(self.w.contracts["oct17_ep01:release_review"].owner,
                         "quality.release_auditor")
    def test_creative_tasks_unblock_in_parallel(self):
        for stage in ("research","fact_review"):
            tid="oct17_ep01:"+stage;owner=self.w.contracts[tid].owner
            self.w.claim(tid,actor=owner)
            self.w.complete(receipt(self.w,tid),actor=owner)
        self.assertEqual(set(self.w.ready()),{"oct17_ep01:script","oct17_ep01:hooks"})
    def test_voice_plan_requires_separate_language_review(self):
        review = self.w.contracts["oct17_ep01:language_review"]
        voice = self.w.contracts["oct17_ep01:voice_plan"]
        self.assertEqual(set(review.requires),
                         {"oct17_ep01:english", "oct17_ep01:hindi"})
        self.assertEqual(voice.requires,("oct17_ep01:language_review",))
        self.assertEqual(review.owner,"language.language_reviewer")
    def test_complete_staging_graph_but_no_upload(self):
        n=0
        while self.w.ready():
            for tid in self.w.ready():
                owner=self.w.contracts[tid].owner
                self.w.claim(tid,actor=owner)
                self.w.complete(receipt(self.w,tid),actor=owner)
                n+=1
        self.assertEqual(n,18)
        self.assertEqual(len(self.w.events),36)
        self.assertEqual(self.w.summary()["states"]["complete"],18)
        self.assertFalse(hasattr(self.w,"upload"))
        self.assertFalse(hasattr(self.w,"schedule"))
    def test_cannot_forge_external_review_or_output_type(self):
        tid=self.w.ready()[0];owner=self.w.contracts[tid].owner
        self.w.claim(tid,actor=owner)
        for bad in (replace(receipt(self.w,tid),review_state="EXTERNAL_PASS"),
                    replace(receipt(self.w,tid),artifact_type="qa.release_attestation")):
            with self.assertRaises(WorkflowError):self.w.complete(bad,actor=owner)
    def test_only_content_addressed_evidence(self):
        tid=self.w.ready()[0];owner=self.w.contracts[tid].owner
        self.w.claim(tid,actor=owner)
        with self.assertRaises(WorkflowError):
            self.w.complete(replace(receipt(self.w,tid),evidence_refs=("https://example.com/",)),actor=owner)
    def test_retries_quarantine_without_dependents(self):
        tid=self.w.ready()[0];owner=self.w.contracts[tid].owner
        for _ in range(3):
            self.w.claim(tid,actor=owner)
            self.w.fail(tid,actor=owner,reason="SOURCE_UNAVAILABLE")
        self.assertEqual(self.w.runs[tid].status,State.QUARANTINED)
        self.assertEqual(self.w.ready(),())
    def test_failure_reason_does_not_log_tokens(self):
        tid=self.w.ready()[0];owner=self.w.contracts[tid].owner
        self.w.claim(tid,actor=owner)
        with self.assertRaises(WorkflowError):
            self.w.fail(tid,actor=owner,reason="secret access token here")
        self.assertEqual(self.w.runs[tid].retries,0)
    def test_wrong_format_language_or_channel(self):
        for kind,language in (("story","hi"),("short","bad")):
            with self.assertRaises(WorkflowError):
                episode_workflow("episode_01",kind=kind,language=language)
        with self.assertRaises(WorkflowError):
            Workflow(list(self.w.contracts.values()),channel_id="UCwrong")
    def test_privileged_permissions_denied(self):
        c=self.w.contracts["oct17_ep01:research"]
        for changes in ({"permissions":("publish_video",)},{"parent_id":"quality"}):
            with self.assertRaises(WorkflowError):replace(c,**changes).validate()
    def test_cycles_and_missing_dependencies_rejected(self):
        a=self.w.contracts["oct17_ep01:research"]
        b=self.w.contracts["oct17_ep01:fact_review"]
        with self.assertRaises(WorkflowError):
            Workflow([replace(a,requires=(b.task_id,)),replace(b,requires=(a.task_id,))])
        with self.assertRaises(WorkflowError):
            Workflow([replace(a,requires=("missing:dependency",))])
    def test_duplicate_task_id_rejected(self):
        task=self.w.contracts["oct17_ep01:research"]
        with self.assertRaises(WorkflowError):Workflow([task,task])
    def test_checkpoint_roundtrip(self):
        tid=self.w.ready()[0];owner=self.w.contracts[tid].owner
        self.w.claim(tid,actor=owner);self.w.complete(receipt(self.w,tid),actor=owner)
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"staging.db";self.w.checkpoint(path)
            other=Workflow.restore(path)
            self.assertEqual(other.summary(),self.w.summary())
            self.assertEqual(other.runs[tid].artifact,self.w.runs[tid].artifact)
    def test_restore_recovers_orphan_running_staging_task(self):
        tid=self.w.ready()[0]
        owner=self.w.contracts[tid].owner
        self.w.claim(tid,actor=owner)
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"staging.db"
            self.w.checkpoint(path)
            recovered=Workflow.restore(path)
            self.assertEqual(recovered.runs[tid].status,State.READY)
            self.assertEqual(recovered.runs[tid].retries,1)
            self.assertEqual(recovered.runs[tid].last_failure,
                             "INTERRUPTED_STAGING_RUN")
            self.assertEqual(recovered.events[-1]["action"],"recovered_retry")
            self.assertEqual(recovered.ready(),(tid,))
            self.assertEqual(recovered.runs[tid].artifact,None)
            self.assertFalse(recovered.summary()["publishing_enabled"])
            # Restarted state is an in-memory recovery; persist checkpoint
            # explicitly before another no-side-effect staging attempt.
            recovered.checkpoint(path)
            resumed=Workflow.restore(path)
            self.assertEqual(resumed.runs[tid].retries,1)
            resumed.claim(tid,actor=owner)
            resumed.complete(receipt(resumed,tid),actor=owner)
            self.assertEqual(resumed.runs[tid].status,State.COMPLETE)
            self.assertIn("oct17_ep01:fact_review",resumed.ready())

    def test_second_crash_uses_last_retry_and_third_quarantines(self):
        tid=self.w.ready()[0]
        owner=self.w.contracts[tid].owner
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"staging.db"
            for number in (1,2,3):
                self.w.claim(tid,actor=owner)
                self.w.checkpoint(path)
                recovered=Workflow.restore(path)
                self.assertEqual(recovered.runs[tid].retries,number)
                self.assertFalse(recovered.summary()["publishing_enabled"])
                self.assertEqual(recovered.events[-1]["action"],
                    "recovered_quarantined" if number==3 else "recovered_retry")
                self.assertEqual(
                    recovered.runs[tid].status,
                    State.QUARANTINED if number==3 else State.READY
                )
                recovered.checkpoint(path)
                self.w=recovered
            self.assertEqual(self.w.ready(),())
            self.assertEqual(self.w.runs[tid].status,State.QUARANTINED)
            self.assertEqual(Workflow.restore(path).runs[tid].retries,3)

    def test_checkpoint_dependency_inconsistency_denied_even_rehashed(self):
        # A local SHA can detect changes, not authenticate a checkpoint.
        # Regression simulates a coherently rehashed *invalid* DAG snapshot.
        import json
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"staging.db"
            self.w.checkpoint(path)
            with closing(sqlite3.connect(path)) as c,c:
                row=c.execute("SELECT data FROM workflow_snapshot").fetchone()
                data=json.loads(row[0])
                task="oct17_ep01:fact_review"
                for new_state in ("ready","complete","running"):
                    modified=json.loads(row[0])
                    modified["runs"][task]["status"]=new_state
                    if new_state=="complete":
                        # Missing artifact is another fail-closed condition.
                        modified["runs"][task]["artifact"]=None
                    payload=json.dumps(modified,sort_keys=True,
                                       separators=(",",":"))
                    c.execute("UPDATE workflow_snapshot SET data=?,digest=?",
                        (payload,sha256(payload.encode()).hexdigest()))
                    with self.subTest(state=new_state),self.assertRaises(WorkflowError):
                        Workflow.restore(path)

    def test_checkpoint_retry_counter_invalid_even_rehashed(self):
        import json
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"staging.db"
            self.w.checkpoint(path)
            with closing(sqlite3.connect(path)) as c,c:
                row=c.execute("SELECT data FROM workflow_snapshot").fetchone()
                for retries in (-1,True,100):
                    mutated=json.loads(row[0])
                    task="oct17_ep01:research"
                    mutated["runs"][task]["retries"]=retries
                    payload=json.dumps(mutated,sort_keys=True,
                                       separators=(",",":"))
                    c.execute("UPDATE workflow_snapshot SET data=?,digest=?",
                              (payload,sha256(payload.encode()).hexdigest()))
                    with self.subTest(retries=retries),self.assertRaises(WorkflowError):
                        Workflow.restore(path)

    def test_checkpoint_tampering_refused(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"staging.db";self.w.checkpoint(path)
            with closing(sqlite3.connect(path)) as c,c:
                c.execute("UPDATE workflow_snapshot SET data=?",('{"publication_authorized":true}',))
            with self.assertRaises(WorkflowError):Workflow.restore(path)

class MasterTests(unittest.TestCase):
    def test_three_episode_default(self):
        master=MasterOrchestrator(tuple(EpisodeSpec(f"ep_{i:02d}","short","en") for i in range(3)))
        self.assertEqual(len(master.active()),3)
        self.assertEqual(len(master.ready_assignments()),3)
        self.assertFalse(master.summary()["uploads_enabled"])
    def test_nine_episode_queue_throttled_to_three(self):
        master=MasterOrchestrator(tuple(EpisodeSpec(f"ep_{i:02d}","short" if i<6 else "long","hi") for i in range(9)))
        self.assertEqual(master.summary()["episodes_queued"],9)
        self.assertEqual(master.summary()["episodes_active"],3)
        self.assertEqual(master.summary()["max_monthly_spend_inr"],0)
    def test_completed_episode_releases_next_queue_slot(self):
        master=MasterOrchestrator(tuple(EpisodeSpec(f"ep_{i:02d}","short","en") for i in range(4)))
        first=master.active()[0].episode_id
        flow=master.workflows[first]
        while flow.ready():
            for tid in flow.ready():
                owner=flow.contracts[tid].owner
                flow.claim(tid,actor=owner)
                flow.complete(receipt(flow,tid),actor=owner)
        self.assertEqual(len(master.active()),3)
        self.assertNotIn(first,{x.episode_id for x in master.active()})
        self.assertIn("ep_03",{x.episode_id for x in master.active()})
    def test_duplicate_or_unbounded_workloads_refused(self):
        with self.assertRaises(WorkflowError):
            MasterOrchestrator(tuple(EpisodeSpec(f"ep_{i:02d}","short","en") for i in range(10)))
        with self.assertRaises(WorkflowError):
            MasterOrchestrator((EpisodeSpec("ep_01","short","en"),EpisodeSpec("ep_01","short","en")))
    def test_excessive_fanout_refused(self):
        master=MasterOrchestrator((EpisodeSpec("ep_01","short","en"),))
        with self.assertRaises(WorkflowError):master.ready_assignments(limit=100)
    def test_preview_zero_upload(self):
        info=preview(9)
        self.assertEqual((info["videos_uploaded"],info["videos_scheduled"]),(0,0))
        self.assertEqual(info["episodes_active"],3)
        self.assertEqual(info["specialists"],48)
    def test_preview_volume_bounds(self):
        with self.assertRaises(ValueError):preview(90)

if __name__=="__main__":unittest.main()
