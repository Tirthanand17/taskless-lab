"""Offline master queue: nine total / three active / fenced per-video stores."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import datetime,timedelta,timezone
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sqlite3
import unittest

from autopilot.agent_org import EpisodeSpec, Handoff, WorkflowError
from autopilot.agent_staging_master_queue import SQLiteStagingMasterQueue
from autopilot.agent_staging_claims import SQLiteStagingClaims

BASE=datetime(2026,10,18,16,tzinfo=timezone.utc)
EPISODES=tuple(
    EpisodeSpec(
        episode_id=f"fm_video_{n:02d}",
        kind="short" if n<7 else "long",
        language="hi" if n%2 else "en",
        priority=95-n,
    ) for n in range(1,10)
)


class MasterQueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"master.sqlite3"
        self.master=SQLiteStagingMasterQueue(
            self.path,episodes=EPISODES,create=True,
        )

    def test_admits_only_first_three_from_nine_and_preserves_priority(self):
        initial=self.master.report()
        self.assertEqual(len(initial["queued"]),9)
        self.assertEqual(initial["active"],[])
        accepted=self.master.reconcile()
        self.assertEqual(accepted["active"],[ep.episode_id for ep in EPISODES[:3]])
        self.assertEqual(accepted["queued"],[ep.episode_id for ep in EPISODES[3:]])
        self.assertEqual(accepted["active_cap"],3)
        self.assertFalse(accepted["publication_enabled"])
        self.assertEqual(accepted["monthly_budget_inr"],0)
        self.assertFalse(accepted["separate_child_dbs_atomically_committed"])
        self.assertEqual(self.master.reconcile(),accepted)
        self.assertEqual(len(self.master.ready_assignments()),3)

    def test_master_restart_preserves_exact_manifest_and_priorities(self):
        expected=self.master.reconcile()
        again=SQLiteStagingMasterQueue(self.path,episodes=EPISODES)
        self.assertEqual(again.report(),expected)
        with self.assertRaises(WorkflowError):
            SQLiteStagingMasterQueue(
                self.path,episodes=tuple(reversed(EPISODES[:4])),
            )
        changed=(EpisodeSpec(EPISODES[0].episode_id,"long","hi",95),
                 *EPISODES[1:])
        with self.assertRaises(WorkflowError):
            SQLiteStagingMasterQueue(self.path,episodes=changed)
        with self.assertRaises(WorkflowError):
            SQLiteStagingMasterQueue(self.path,episodes=EPISODES,create=True)

    def test_competing_master_admissions_never_exceed_three_slots(self):
        def contender(_):
            node=SQLiteStagingMasterQueue(self.path,episodes=EPISODES)
            return node.reconcile()
        with ThreadPoolExecutor(max_workers=4) as pool:
            states=list(pool.map(contender,range(4)))
        self.assertTrue(all(len(result["active"])==3 for result in states))
        self.assertTrue(all(state==states[0] for state in states))
        self.assertEqual(len(list(self.path.parent.glob("master-fm_video_*.sqlite3"))),3)

    def test_master_assignments_contended_by_two_actual_worker_connections(self):
        self.master.reconcile()
        ep,task_id,actor=self.master.ready_assignments()[0]
        info=next(x for x in EPISODES if x.episode_id==ep)
        path=self.master.children[ep]
        def attempt(_):
            client=SQLiteStagingClaims(
                path,episode_id=ep,kind=info.kind,language=info.language
            )
            try:
                return client.claim(task_id,actor=actor,now=BASE)
            except WorkflowError:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            tokens=list(pool.map(attempt,range(2)))
        self.assertEqual(sum(token is not None for token in tokens),1)
        self.assertEqual(self.master.report()["active"],[e.episode_id
                                                          for e in EPISODES[:3]])
        self.assertEqual(len(self.master.ready_assignments()),2)

    def _complete_episode(self, ep:EpisodeSpec)->None:
        client=SQLiteStagingClaims(
            self.master.children[ep.episode_id],
            episode_id=ep.episode_id,kind=ep.kind,language=ep.language
        )
        digests={}
        for index,tid in enumerate(client.workflow.order):
            contract=client.contracts[tid]
            now=BASE+timedelta(seconds=5*index)
            generation=client.claim(tid,actor=contract.owner,now=now)
            digest=sha256(tid.encode()).hexdigest()
            evidence=tuple("sha256:"+digests[dep]
                           for dep in contract.requires)+("sha256:"+digest,)
            handoff=Handoff(
                tid,contract.produces,digest,evidence,contract.owner,
                BASE.isoformat(),
            )
            client.complete(handoff,actor=contract.owner,
                            generation=generation,
                            now=now+timedelta(seconds=1))
            digests[tid]=digest

    def test_finishing_one_full_episode_promotes_exactly_next_queued(self):
        self.master.reconcile()
        self._complete_episode(EPISODES[0])
        before=self.master.report()
        self.assertEqual(before["active"],[ep.episode_id for ep in EPISODES[:3]])
        after=self.master.reconcile()
        self.assertEqual(after["complete"],[EPISODES[0].episode_id])
        self.assertEqual(after["active"],[ep.episode_id for ep in EPISODES[1:4]])
        self.assertEqual(len(after["queued"]),5)
        self.assertFalse(after["publication_enabled"])
        reopened=SQLiteStagingMasterQueue(self.path,episodes=EPISODES)
        self.assertEqual(reopened.report(),after)

    def test_quarantined_stage_pauses_episode_and_admits_next_draft(self):
        self.master.reconcile()
        first=EPISODES[0]
        client=SQLiteStagingClaims(
            self.master.children[first.episode_id],
            episode_id=first.episode_id,kind=first.kind,
            language=first.language,
        )
        task_id=f"{first.episode_id}:research"
        owner=client.contracts[task_id].owner
        for i in range(3):
            now=BASE+timedelta(seconds=i*200)
            generation=client.claim(task_id,actor=owner,now=now)
            self.assertGreater(generation,0)
            self.assertEqual(client.recover_expired(
                now=now+timedelta(seconds=120)),(task_id,))
        outcome=self.master.reconcile()
        self.assertEqual(outcome["quarantined"],[first.episode_id])
        self.assertEqual(outcome["active"],[ep.episode_id for ep in EPISODES[1:4]])
        self.assertEqual(len(outcome["queued"]),5)

    def test_interrupted_admission_child_store_is_reused_not_overwritten(self):
        # Simulate a crash after SQLite child creation but BEFORE the
        # transaction recording queue status ACTIVE commits.
        first=EPISODES[0]
        child=SQLiteStagingClaims(
            self.master.children[first.episode_id],episode_id=first.episode_id,
            kind=first.kind,language=first.language,create=True,
        )
        claimed=child.claim(f"{first.episode_id}:research",
                            actor="research.launch_researcher",now=BASE)
        self.assertGreater(claimed,0)
        states=self.master.reconcile()
        self.assertIn(first.episode_id,states["active"])
        self.assertEqual(child.report()["running_count"],1)
        reopened=SQLiteStagingClaims(
            self.master.children[first.episode_id],
            episode_id=first.episode_id,kind=first.kind,language=first.language,
        )
        self.assertEqual(reopened.report()["running_count"],1)

    def test_bad_episode_specs_and_master_tamper_denied(self):
        bad=((EpisodeSpec("UPPER","short","en",20),),
             (EpisodeSpec("foo","short","en",True),),
             (EpisodeSpec("valid_foo","short","en"),)*10)
        for specs in bad:
            with self.subTest(specs=specs),self.assertRaises(WorkflowError):
                SQLiteStagingMasterQueue(
                    Path(self.tmp.name)/"other.sqlite3",episodes=specs,create=True
                )
        self.master.reconcile()
        with closing(sqlite3.connect(self.path)) as conn:
            for ep in EPISODES[3:5]:
                conn.execute(
                    "UPDATE episode_queue SET status='active' WHERE episode_id=?",
                    (ep.episode_id,),
                )
            conn.commit()
        with self.assertRaises(WorkflowError):
            self.master.report()

    def _advance_to_two_parallel_tasks(self,ep:EpisodeSpec)->None:
        """Reach script + hooks using original evidence-fenced contracts."""
        child=SQLiteStagingClaims(
            self.master.children[ep.episode_id],episode_id=ep.episode_id,
            kind=ep.kind,language=ep.language,
        )
        previous={}
        for index,stage in enumerate(("research","fact_review")):
            tid=f"{ep.episode_id}:{stage}"
            contract=child.contracts[tid]
            at=BASE+timedelta(seconds=index*4)
            gen=self.master.claim_active(ep.episode_id,tid,actor=contract.owner,
                                         now=at)
            digest=sha256(tid.encode()).hexdigest()
            parents=tuple("sha256:"+previous[dep] for dep in contract.requires)
            handoff=Handoff(tid,contract.produces,digest,
                            parents+("sha256:"+digest,),contract.owner,
                            BASE.isoformat())
            self.master.complete_active(ep.episode_id,handoff,
                                        actor=contract.owner,generation=gen,
                                        now=at+timedelta(seconds=1))
            previous[tid]=digest
        self.assertEqual(
            {tid.split(":")[-1] for tid in child.report()["ready_tasks"]},
            {"script","hooks"},
        )

    def test_unadmitted_and_queued_videos_cannot_claim_master_tasks(self):
        first=EPISODES[0]
        tid=f"{first.episode_id}:research"
        with self.assertRaises(WorkflowError):
            self.master.claim_active(first.episode_id,tid,
                                      actor="research.launch_researcher",now=BASE)
        self.master.reconcile()
        waiting=EPISODES[3]
        with self.assertRaises(WorkflowError):
            self.master.claim_active(waiting.episode_id,
                                      f"{waiting.episode_id}:research",
                                      actor="research.launch_researcher",now=BASE)
        with self.assertRaises(WorkflowError):
            self.master.recover_expired_active(waiting.episode_id,now=BASE)
        self.assertFalse(self.master.children[waiting.episode_id].exists())

    def test_master_only_releases_next_episode_when_reconciled(self):
        self.master.reconcile()
        first=EPISODES[0]
        self._complete_episode(first)
        self.master.reconcile()
        with self.assertRaises(WorkflowError):
            self.master.claim_active(first.episode_id,
                                      f"{first.episode_id}:research",
                                      actor="research.launch_researcher",now=BASE)
        promoted=EPISODES[3]
        token=self.master.claim_active(
            promoted.episode_id,f"{promoted.episode_id}:research",
            actor="research.launch_researcher",now=BASE)
        self.assertGreater(token,0)

    def test_round_robin_fairness_and_four_total_inflight_tasks(self):
        self.master.reconcile()
        self._advance_to_two_parallel_tasks(EPISODES[0])
        self._advance_to_two_parallel_tasks(EPISODES[1])
        suggestions=self.master.ready_assignments(limit=4)
        self.assertEqual(len(suggestions),4)
        self.assertEqual(
            [ep for ep,_,_ in suggestions[:3]],
            [ep.episode_id for ep in EPISODES[:3]]
        )
        self.assertEqual(suggestions[3][0],EPISODES[0].episode_id)
        tokens=[]
        for index,(ep,task,owner) in enumerate(suggestions):
            token=self.master.claim_active(ep,task,actor=owner,
                                           now=BASE+timedelta(seconds=10+index))
            tokens.append((ep,task,owner,token))
        self.assertEqual(self.master.ready_assignments(),())
        spare=f"{EPISODES[1].episode_id}:script"
        if spare==tokens[1][1]:
            spare=f"{EPISODES[1].episode_id}:hooks"
        with self.assertRaises(WorkflowError):
            self.master.claim_active(EPISODES[1].episode_id,spare,
                actor="creative.shorts_writer" if spare.endswith(":script")
                else "creative.hook_writer",now=BASE+timedelta(seconds=16))
        ep,task,owner,token=tokens[0]
        self.master.fail_active(ep,task,actor=owner,generation=token,
                               category="STAGING_RETRY",now=BASE+timedelta(seconds=17))
        # One free slot becomes available after explicit fail.
        self.assertEqual(len(self.master.ready_assignments(limit=4)),1)

    def test_master_gated_two_contenders_cannot_both_claim(self):
        self.master.reconcile()
        ep=EPISODES[0]
        task=f"{ep.episode_id}:research"
        def contender(_):
            worker=SQLiteStagingMasterQueue(self.path,episodes=EPISODES)
            try:
                return worker.claim_active(ep.episode_id,task,
                     actor="research.launch_researcher",now=BASE)
            except WorkflowError:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            tokens=list(pool.map(contender,range(2)))
        self.assertEqual(sum(x is not None for x in tokens),1)
        self.assertEqual(len(self.master.ready_assignments()),2)

    def test_master_gated_heartbeat_recovery_and_stale_token(self):
        self.master.reconcile()
        ep=EPISODES[0]
        task=f"{ep.episode_id}:research"
        actor="research.launch_researcher"
        first=self.master.claim_active(ep.episode_id,task,actor=actor,
                                        now=BASE,lease_seconds=10)
        self.master.heartbeat_active(
            ep.episode_id,task,actor=actor,generation=first,
            now=BASE+timedelta(seconds=8),lease_seconds=30)
        self.assertEqual(self.master.recover_expired_active(
            ep.episode_id,now=BASE+timedelta(seconds=20)),())
        self.assertEqual(self.master.recover_expired_active(
            ep.episode_id,now=BASE+timedelta(seconds=38)),(task,))
        second=self.master.claim_active(ep.episode_id,task,actor=actor,
                                        now=BASE+timedelta(seconds=39))
        self.assertGreater(second,first)
        with self.assertRaises(WorkflowError):
            self.master.fail_active(ep.episode_id,task,actor=actor,
                generation=first,category="STAGING_RETRY",
                now=BASE+timedelta(seconds=40))

    def test_cross_episode_handoffs_cannot_complete_active_stage(self):
        self.master.reconcile()
        a,b=EPISODES[:2]
        tid=f"{a.episode_id}:research"
        generation=self.master.claim_active(
            a.episode_id,tid,actor="research.launch_researcher",now=BASE)
        foreign=f"{b.episode_id}:research"
        digest=sha256(foreign.encode()).hexdigest()
        wrong=Handoff(foreign,"research.package",digest,
                      ("sha256:"+digest,),"research.launch_researcher",
                      BASE.isoformat())
        with self.assertRaises(WorkflowError):
            self.master.complete_active(a.episode_id,wrong,
                actor="research.launch_researcher",
                generation=generation,now=BASE+timedelta(seconds=1))
        self.assertEqual(self.master.report()["active"],
                         [ep.episode_id for ep in EPISODES[:3]])

    def test_fanout_and_release_remain_disabled(self):
        with self.assertRaises(WorkflowError):
            self.master.ready_assignments(limit=5)
        with self.assertRaises(WorkflowError):
            self.master.ready_assignments(limit=True)
        self.master.reconcile()
        assignments=self.master.ready_assignments(limit=2)
        self.assertEqual(len(assignments),2)
        self.assertEqual(len({ep for ep,_,_ in assignments}),2)
        state=self.master.report()
        self.assertTrue(state["staging_only"])
        self.assertFalse(state["cloud_deployed"])
        self.assertFalse(state["worker_identities_authenticated"])
        self.assertFalse(state["trusted_server_clock"])


if __name__=="__main__":
    unittest.main()
