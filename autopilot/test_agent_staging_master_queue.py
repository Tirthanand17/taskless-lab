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
