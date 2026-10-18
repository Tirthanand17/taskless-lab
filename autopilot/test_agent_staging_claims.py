"""Bounded local multi-connection offline agent rehearsal, no production keys."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from dataclasses import replace
import unittest

from autopilot.agent_org import Handoff, WorkflowError
from autopilot.agent_staging_claims import SQLiteStagingClaims

BASE=datetime(2026,10,18,14,tzinfo=timezone.utc)
EP="csv_tutorial_short_hi"
RESEARCH=f"{EP}:research"
FACT=f"{EP}:fact_review"
OWNER="research.launch_researcher"


def output(task: str, actor: str) -> Handoff:
    digest=sha256(task.encode("utf-8")).hexdigest()
    kind={"research":"research.package","fact_review":"qa.fact_attestation"}[
        task.split(":")[-1]]
    return Handoff(task,kind,digest,("sha256:"+digest,),actor,BASE.isoformat())


class StagingLocalLeaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"stage.db"
        self.staging=SQLiteStagingClaims(
            self.path,episode_id=EP,kind="short",language="hi",create=True,
        )

    def test_create_and_reopen_enforces_original_contract(self):
        r=self.staging.report()
        self.assertEqual(r["tasks"],18)
        self.assertEqual(r["ready_tasks"],[RESEARCH])
        self.assertEqual(r["monthly_infrastructure_inr"],0)
        for k in ("worker_identities_authenticated","clock_independently_trusted",
                  "multi_worker_d1_or_cloud_deployed",
                  "youtube_publishing_authorized"):
            self.assertIs(r[k],False)
        reopened=SQLiteStagingClaims(self.path,episode_id=EP,kind="short",language="hi")
        self.assertEqual(reopened.report(),r)
        with self.assertRaises(WorkflowError):
            SQLiteStagingClaims(self.path,episode_id=EP,kind="short",language="en")
        with self.assertRaises(WorkflowError):
            SQLiteStagingClaims(self.path,episode_id=EP,kind="short",language="hi",create=True)

    def test_atomic_two_competing_connections_one_wins(self):
        def attempt(_):
            c=SQLiteStagingClaims(self.path,episode_id=EP,kind="short",language="hi")
            try:
                return c.claim(RESEARCH,actor=OWNER,now=BASE)
            except WorkflowError:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            tokens=list(pool.map(attempt,range(2)))
        self.assertEqual(sum(x is not None for x in tokens),1)
        self.assertEqual(self.staging.report()["running_count"],1)

    def test_fenced_handoff_unblocks_only_completed_dependencies(self):
        token=self.staging.claim(RESEARCH,actor=OWNER,now=BASE)
        self.assertIsInstance(token,int)
        self.assertNotIn(FACT,self.staging.report()["ready_tasks"])
        self.staging.complete(output(RESEARCH,OWNER),actor=OWNER,
                              generation=token,now=BASE+timedelta(seconds=30))
        r=self.staging.report()
        self.assertEqual(r["completed_count"],1)
        self.assertEqual(r["ready_tasks"],[FACT])
        with self.assertRaises(WorkflowError):
            self.staging.complete(output(RESEARCH,OWNER),actor=OWNER,
                                  generation=token,now=BASE+timedelta(seconds=31))

    def test_lease_expiry_charges_retry_and_stale_generation_refused(self):
        token=self.staging.claim(RESEARCH,actor=OWNER,now=BASE,lease_seconds=10)
        self.assertEqual(self.staging.recover_expired(
            now=BASE+timedelta(seconds=10)),(RESEARCH,))
        self.assertEqual(self.staging.report()["ready_tasks"],[RESEARCH])
        with self.assertRaises(WorkflowError):
            self.staging.complete(output(RESEARCH,OWNER),actor=OWNER,
                                  generation=token,now=BASE+timedelta(seconds=11))
        newer=self.staging.claim(
            RESEARCH,actor=OWNER,now=BASE+timedelta(seconds=12))
        self.assertGreater(newer,token)
        with self.assertRaises(WorkflowError):
            self.staging.heartbeat(RESEARCH,actor=OWNER,generation=token,
                                   now=BASE+timedelta(seconds=13))
        self.staging.complete(output(RESEARCH,OWNER),actor=OWNER,
                              generation=newer,now=BASE+timedelta(seconds=14))

    def test_heartbeat_renews_fenced_lease(self):
        old=self.staging.claim(RESEARCH,actor=OWNER,now=BASE,lease_seconds=10)
        self.staging.heartbeat(RESEARCH,actor=OWNER,generation=old,
                               now=BASE+timedelta(seconds=9),
                               lease_seconds=30)
        self.assertEqual(self.staging.recover_expired(
            now=BASE+timedelta(seconds=20)),())
        self.staging.complete(output(RESEARCH,OWNER),actor=OWNER,
                              generation=old,now=BASE+timedelta(seconds=32))

    def test_three_lost_workers_are_bounded_and_quarantined(self):
        for number in (1,2,3):
            token=self.staging.claim(RESEARCH,actor=OWNER,
                now=BASE+timedelta(seconds=number*200))
            expired=BASE+timedelta(seconds=number*200+120)
            self.assertEqual(self.staging.recover_expired(now=expired),(RESEARCH,))
        report=self.staging.report()
        self.assertEqual(report["quarantined_count"],1)
        self.assertEqual(report["ready_tasks"],[])
        with self.assertRaises(WorkflowError):
            self.staging.claim(RESEARCH,actor=OWNER,now=BASE+timedelta(minutes=20))

    def test_wrong_owner_fake_release_handoff_and_no_unreviewed_promotion(self):
        with self.assertRaises(WorkflowError):
            self.staging.claim(RESEARCH,actor="publishing.upload_specialist",now=BASE)
        token=self.staging.claim(RESEARCH,actor=OWNER,now=BASE)
        for bad in (
            replace(output(RESEARCH,OWNER),review_state="EXTERNAL_VERIFIED"),
            replace(output(RESEARCH,OWNER),artifact_type="publish.video"),
            replace(output(RESEARCH,OWNER),evidence_refs=()),
        ):
            with self.subTest(value=bad),self.assertRaises(WorkflowError):
                self.staging.complete(bad,actor=OWNER,generation=token,now=BASE)
        self.assertEqual(self.staging.report()["completed_count"],0)

    def test_failure_requeues_and_invalid_category_or_old_generation_denied(self):
        token=self.staging.claim(RESEARCH,actor=OWNER,now=BASE)
        with self.assertRaises(WorkflowError):
            self.staging.fail(RESEARCH,actor=OWNER,generation=token,
                              category="token:secret-raw",now=BASE)
        self.staging.fail(RESEARCH,actor=OWNER,generation=token,
                          category="SOURCE_UNAVAILABLE",now=BASE)
        self.assertEqual(self.staging.report()["ready_tasks"],[RESEARCH])
        with self.assertRaises(WorkflowError):
            self.staging.complete(output(RESEARCH,OWNER),actor=OWNER,
                                  generation=token,now=BASE)
        reopened=SQLiteStagingClaims(self.path,episode_id=EP,kind="short",language="hi")
        self.assertEqual(reopened.report()["ready_tasks"],[RESEARCH])

    def test_lease_window_timezone_wrong_types_and_clock_rollback_denied(self):
        with self.assertRaises(WorkflowError):
            self.staging.claim(RESEARCH,actor=OWNER,now=BASE,lease_seconds=True)
        with self.assertRaises(WorkflowError):
            self.staging.claim(RESEARCH,actor=OWNER,
                               now=BASE.replace(tzinfo=None))
        token=self.staging.claim(RESEARCH,actor=OWNER,
                                 now=BASE+timedelta(seconds=10))
        with self.assertRaises(WorkflowError):
            self.staging.heartbeat(RESEARCH,actor=OWNER,generation=token,
                                   now=BASE)
        self.assertEqual(self.staging.report()["running_count"],1)

    def test_stale_owner_cannot_replay_after_explicit_failure(self):
        first=self.staging.claim(RESEARCH,actor=OWNER,now=BASE)
        self.staging.fail(RESEARCH,actor=OWNER,generation=first,
                          category="RENDER_ERROR",now=BASE)
        second=self.staging.claim(RESEARCH,actor=OWNER,
                                  now=BASE+timedelta(seconds=1))
        self.assertGreater(second,first)
        with self.assertRaises(WorkflowError):
            self.staging.complete(output(RESEARCH,OWNER),actor=OWNER,
                                  generation=first,
                                  now=BASE+timedelta(seconds=2))
        self.staging.complete(output(RESEARCH,OWNER),actor=OWNER,
                              generation=second,
                              now=BASE+timedelta(seconds=3))


if __name__=="__main__":
    unittest.main()
