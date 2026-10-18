"""One-database atomic master/task staging acceptance tests; no live data."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from autopilot.agent_org import EpisodeSpec, Handoff, WorkflowError
from autopilot.agent_staging_unified import UnifiedStagingCoordinator

BASE=datetime(2026,10,18,16,0,tzinfo=timezone.utc)
EPISODES=tuple(
    EpisodeSpec(f"fm_qa_{n:02d}","short" if n<7 else "long",
                "hi" if n%2 else "en",100-n)
    for n in range(1,10)
)


def handoff(coordinator,eid,tid,digests):
    contract=coordinator.contracts[eid][tid]
    digest=sha256(tid.encode()).hexdigest()
    evidence=tuple("sha256:"+digests[parent] for parent in contract.requires)
    return Handoff(tid,contract.produces,digest,evidence+("sha256:"+digest,),
                   contract.owner,BASE.isoformat())


class UnifiedStagingTests(unittest.TestCase):
    def setUp(self):
        tmp=TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path=Path(tmp.name)/"unified.sqlite3"
        self.master=UnifiedStagingCoordinator(
            self.path,episodes=EPISODES,create=True,
        )

    def test_nine_episode_queue_single_db_no_child_files(self):
        before=self.master.report()
        self.assertEqual(len(before["queued"]),9)
        self.assertEqual(before["task_count"],162)
        after=self.master.reconcile()
        self.assertEqual(after["active"],[ep.episode_id for ep in EPISODES[:3]])
        self.assertEqual(len(after["queued"]),6)
        self.assertEqual(len(list(self.path.parent.glob("*.sqlite3"))),1)
        self.assertTrue(after["single_sqlite_transaction_for_admission_and_tasks"])
        self.assertFalse(after["publish_enabled"])
        self.assertFalse(after["authenticated_worker_ids"])
        self.assertEqual(after["monthly_inr"],0)

    def test_reopen_manifest_and_pre_admission_claim_denied(self):
        eid=EPISODES[0].episode_id
        tid=f"{eid}:research"
        with self.assertRaises(WorkflowError):
            self.master.claim(eid,tid,actor="research.launch_researcher",now=BASE)
        self.master.reconcile()
        other=UnifiedStagingCoordinator(self.path,episodes=EPISODES)
        self.assertEqual(other.report(),self.master.report())
        changed=(EpisodeSpec(eid,"long","hi",99),*EPISODES[1:])
        with self.assertRaises(WorkflowError):
            UnifiedStagingCoordinator(self.path,episodes=changed)
        queued=EPISODES[3].episode_id
        with self.assertRaises(WorkflowError):
            other.claim(queued,f"{queued}:research",
                        actor="research.launch_researcher",now=BASE)

    def test_racing_workers_one_claim_and_three_video_admission(self):
        def admit(_):
            return UnifiedStagingCoordinator(self.path,episodes=EPISODES).reconcile()
        with ThreadPoolExecutor(max_workers=4) as pool:
            states=list(pool.map(admit,range(4)))
        self.assertTrue(all(x["active"]==states[0]["active"] for x in states))
        eid=EPISODES[0].episode_id
        tid=f"{eid}:research"
        def race(_):
            obj=UnifiedStagingCoordinator(self.path,episodes=EPISODES)
            try:
                return obj.claim(eid,tid,actor="research.launch_researcher",now=BASE)
            except WorkflowError:
                return None
        with ThreadPoolExecutor(max_workers=3) as pool:
            tokens=list(pool.map(race,range(3)))
        self.assertEqual(sum(x is not None for x in tokens),1)
        self.assertEqual(self.master.report()["running_tasks"],1)

    def _complete_episode(self,eid):
        prev={}
        for index,tid in enumerate(self.master.order[eid]):
            contract=self.master.contracts[eid][tid]
            at=BASE+timedelta(seconds=index*5)
            generation=self.master.claim(eid,tid,actor=contract.owner,now=at)
            h=handoff(self.master,eid,tid,prev)
            state=self.master.complete(eid,h,actor=contract.owner,
                                       generation=generation,
                                       now=at+timedelta(seconds=1))
            prev[tid]=h.sha256_hex
        return state

    def test_all_eighteen_stage_completions_atomically_admit_next_video(self):
        self.master.reconcile()
        first=EPISODES[0].episode_id
        final=self._complete_episode(first)
        self.assertEqual(final["complete"],[first])
        self.assertEqual(final["active"],[ep.episode_id for ep in EPISODES[1:4]])
        self.assertEqual(final["completed_tasks"],18)
        self.assertEqual(final["running_tasks"],0)
        self.assertEqual(final["task_count"],162)
        self.assertEqual(
            UnifiedStagingCoordinator(self.path,episodes=EPISODES).report(),final
        )
        self.assertEqual(len(list(self.path.parent.glob("*.sqlite3"))),1)

    def test_ancestor_lineage_fail_closed_before_completion(self):
        self.master.reconcile()
        eid=EPISODES[0].episode_id
        root=f"{eid}:research"
        owner="research.launch_researcher"
        gen=self.master.claim(eid,root,actor=owner,now=BASE)
        h=handoff(self.master,eid,root,{})
        self.master.complete(eid,h,actor=owner,generation=gen,
                             now=BASE+timedelta(seconds=1))
        fact=f"{eid}:fact_review"
        actor="quality.fact_reviewer"
        token=self.master.claim(eid,fact,actor=actor,
                                now=BASE+timedelta(seconds=2))
        bad=handoff(self.master,eid,fact,{root:h.sha256_hex})
        bad=replace(bad,evidence_refs=("sha256:"+bad.sha256_hex,))
        with self.assertRaises(WorkflowError):
            self.master.complete(eid,bad,actor=actor,generation=token,
                                 now=BASE+timedelta(seconds=3))
        self.assertEqual(self.master.report()["completed_tasks"],1)
        good=handoff(self.master,eid,fact,{root:h.sha256_hex})
        self.master.complete(eid,good,actor=actor,generation=token,
                             now=BASE+timedelta(seconds=4))

    def test_global_four_running_claims_and_round_robin_fairness(self):
        self.master.reconcile()
        for index,ep in enumerate(EPISODES[:2]):
            eid=ep.episode_id
            prev={}
            for s in ("research","fact_review"):
                tid=f"{eid}:{s}"
                c=self.master.contracts[eid][tid]
                at=BASE+timedelta(seconds=index*10+(0 if s=="research" else 2))
                gen=self.master.claim(eid,tid,actor=c.owner,now=at)
                h=handoff(self.master,eid,tid,prev)
                self.master.complete(eid,h,actor=c.owner,generation=gen,
                                     now=at+timedelta(seconds=1))
                prev[tid]=h.sha256_hex
        suggestions=self.master.assignments(limit=4)
        self.assertEqual(len(suggestions),4)
        self.assertEqual([x[0] for x in suggestions[:3]],
                         [ep.episode_id for ep in EPISODES[:3]])
        for index,(eid,tid,actor) in enumerate(suggestions):
            self.master.claim(eid,tid,actor=actor,
                              now=BASE+timedelta(seconds=30+index))
        self.assertEqual(self.master.assignments(),())
        self.assertEqual(self.master.report()["running_tasks"],4)

    def test_third_failure_cancels_parallel_peer_and_promotes_next(self):
        self.master.reconcile()
        eid=EPISODES[0].episode_id
        self._advance_parallel(eid)
        script=f"{eid}:script"
        hooks=f"{eid}:hooks"
        hookactor=self.master.contracts[eid][hooks].owner
        hg=self.master.claim(eid,hooks,actor=hookactor,
                             now=BASE+timedelta(seconds=10))
        actor=self.master.contracts[eid][script].owner
        for i in range(3):
            at=BASE+timedelta(seconds=11+2*i)
            gen=self.master.claim(eid,script,actor=actor,now=at)
            result=self.master.fail(eid,script,actor=actor,
                                    generation=gen,now=at+timedelta(seconds=1),
                                    category="SIMULATED_ERROR")
        self.assertEqual(result["quarantined"],[eid])
        self.assertEqual(result["active"],[e.episode_id for e in EPISODES[1:4]])
        self.assertEqual(result["running_tasks"],0)
        with self.assertRaises(WorkflowError):
            self.master.heartbeat(eid,hooks,actor=hookactor,
                                  generation=hg,now=BASE+timedelta(seconds=18))

    def _advance_parallel(self,eid):
        previous={}
        for idx,stage in enumerate(("research","fact_review")):
            tid=f"{eid}:{stage}"
            contract=self.master.contracts[eid][tid]
            at=BASE+timedelta(seconds=idx*3)
            generation=self.master.claim(eid,tid,actor=contract.owner,now=at)
            h=handoff(self.master,eid,tid,previous)
            self.master.complete(eid,h,actor=contract.owner,
                                 generation=generation,
                                 now=at+timedelta(seconds=1))
            previous[tid]=h.sha256_hex
        self.assertEqual(
            {x[1].split(":")[-1] for x in self.master.assignments()
             if x[0]==eid},
            {"script","hooks"}
        )

    def test_lease_expiry_fences_reclaim_and_rollbacks(self):
        self.master.reconcile()
        eid=EPISODES[0].episode_id
        tid=f"{eid}:research"
        actor="research.launch_researcher"
        first=self.master.claim(eid,tid,actor=actor,now=BASE,lease_seconds=10)
        self.assertEqual(self.master.recover_expired(
            now=BASE+timedelta(seconds=10)),(tid,))
        second=self.master.claim(eid,tid,actor=actor,
                                 now=BASE+timedelta(seconds=11))
        self.assertGreater(second,first)
        with self.assertRaises(WorkflowError):
            self.master.heartbeat(eid,tid,actor=actor,generation=first,
                                  now=BASE+timedelta(seconds=12))
        self.assertEqual(self.master.report()["running_tasks"],1)
        with self.assertRaises(WorkflowError):
            self.master.claim(eid,tid,actor=actor,
                              now=BASE+timedelta(seconds=12))
        with self.assertRaises(WorkflowError):
            self.master.heartbeat(eid,tid,actor=actor,generation=second,
                                  now=BASE)

    def test_bounded_fanout_types_and_denied_release_handoff(self):
        self.master.reconcile()
        with self.assertRaises(WorkflowError):
            self.master.assignments(limit=True)
        eid=EPISODES[0].episode_id
        tid=f"{eid}:research"
        actor="research.launch_researcher"
        gen=self.master.claim(eid,tid,actor=actor,now=BASE)
        h=handoff(self.master,eid,tid,{})
        with self.assertRaises(WorkflowError):
            self.master.complete(eid,replace(h,review_state="PUBLISH_APPROVED"),
                                 actor=actor,generation=gen,now=BASE)
        with self.assertRaises(WorkflowError):
            self.master.complete(EPISODES[1].episode_id,h,
                                 actor=actor,generation=gen,now=BASE)
        self.assertFalse(self.master.report()["publish_enabled"])


if __name__=="__main__":
    unittest.main()
