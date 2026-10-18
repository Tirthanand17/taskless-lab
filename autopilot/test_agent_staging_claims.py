"""Bounded local multi-connection offline agent rehearsal, no production keys."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import closing
import json
import sqlite3
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

    def test_completed_handoff_metadata_survives_reopen_and_is_not_approval(self):
        token=self.staging.claim(RESEARCH,actor=OWNER,now=BASE)
        self.staging.complete(output(RESEARCH,OWNER),actor=OWNER,
                              generation=token,now=BASE+timedelta(seconds=1))
        with closing(sqlite3.connect(self.path)) as db:
            payload,digest=db.execute(
                "SELECT payload,digest FROM stage_handoffs WHERE task_id=?",
                (RESEARCH,),
            ).fetchone()
        data=json.loads(payload)
        self.assertEqual(data["task_id"],RESEARCH)
        self.assertEqual(data["review_state"],"UNVERIFIED_STAGING_ARTIFACT")
        self.assertEqual(sha256(payload.encode()).hexdigest(),digest)
        again=SQLiteStagingClaims(self.path,episode_id=EP,kind="short",language="hi")
        self.assertEqual(again.report()["durable_staging_handoffs_verified"],1)
        self.assertFalse(again.report()["evidence_independently_authenticated"])
        self.assertEqual(again.report()["ready_tasks"],[FACT])

    def test_dependent_fact_handoff_requires_exact_source_artifact_lineage(self):
        parent=output(RESEARCH,OWNER)
        token=self.staging.claim(RESEARCH,actor=OWNER,now=BASE)
        self.staging.complete(parent,actor=OWNER,generation=token,
                              now=BASE+timedelta(seconds=1))
        actor="quality.fact_reviewer"
        child_token=self.staging.claim(FACT,actor=actor,
                                       now=BASE+timedelta(seconds=2))
        unbound=output(FACT,actor)
        with self.assertRaises(WorkflowError):
            self.staging.complete(unbound,actor=actor,generation=child_token,
                                  now=BASE+timedelta(seconds=3))
        self.assertEqual(self.staging.report()["completed_count"],1)
        linked=replace(unbound,evidence_refs=(
            "sha256:"+parent.sha256_hex,"sha256:"+unbound.sha256_hex,
        ))
        self.staging.complete(linked,actor=actor,generation=child_token,
                              now=BASE+timedelta(seconds=4))
        reopened=SQLiteStagingClaims(self.path,episode_id=EP,kind="short",language="hi")
        self.assertEqual(reopened.report()["durable_staging_handoffs_verified"],2)
        self.assertEqual(set(reopened.report()["ready_tasks"]),{
            f"{EP}:script",f"{EP}:hooks",
        })

    def test_saved_forged_review_rejected_even_after_rehash(self):
        token=self.staging.claim(RESEARCH,actor=OWNER,now=BASE)
        self.staging.complete(output(RESEARCH,OWNER),actor=OWNER,
                              generation=token,now=BASE+timedelta(seconds=1))
        with closing(sqlite3.connect(self.path)) as db:
            raw=db.execute("SELECT payload FROM stage_handoffs "
                           "WHERE task_id=?",(RESEARCH,)).fetchone()[0]
            forged=json.loads(raw)
            forged["review_state"]="SIGNED_APPROVED_RELEASE"
            altered=json.dumps(forged,sort_keys=True,separators=(",",":"))
            db.execute("UPDATE stage_handoffs SET payload=?,digest=? "
                       "WHERE task_id=?",
                       (altered,sha256(altered.encode()).hexdigest(),RESEARCH))
            db.commit()
        with self.assertRaises(WorkflowError):
            SQLiteStagingClaims(self.path,episode_id=EP,kind="short",language="hi")

    def test_rehashed_child_metadata_cannot_erase_parent_lineage(self):
        parent=output(RESEARCH,OWNER)
        t1=self.staging.claim(RESEARCH,actor=OWNER,now=BASE)
        self.staging.complete(parent,actor=OWNER,generation=t1,
                              now=BASE+timedelta(seconds=1))
        actor="quality.fact_reviewer"
        t2=self.staging.claim(FACT,actor=actor,now=BASE+timedelta(seconds=2))
        child=output(FACT,actor)
        bound=replace(child,evidence_refs=("sha256:"+parent.sha256_hex,))
        self.staging.complete(bound,actor=actor,generation=t2,
                              now=BASE+timedelta(seconds=3))
        with closing(sqlite3.connect(self.path)) as db:
            raw=db.execute("SELECT payload FROM stage_handoffs "
                           "WHERE task_id=?",(FACT,)).fetchone()[0]
            modified=json.loads(raw)
            modified["evidence_refs"]=["sha256:"+child.sha256_hex]
            altered=json.dumps(modified,sort_keys=True,separators=(",",":"))
            db.execute("UPDATE stage_handoffs SET payload=?,digest=? "
                       "WHERE task_id=?",
                       (altered,sha256(altered.encode()).hexdigest(),FACT))
            db.commit()
        with self.assertRaises(WorkflowError):
            SQLiteStagingClaims(self.path,episode_id=EP,kind="short",language="hi")

    def test_evidence_ref_count_and_duplicates_bounded(self):
        token=self.staging.claim(RESEARCH,actor=OWNER,now=BASE)
        base=output(RESEARCH,OWNER)
        duplicates=replace(base,evidence_refs=base.evidence_refs*2)
        too_many=replace(base,evidence_refs=tuple(
            "sha256:"+sha256(str(i).encode()).hexdigest()
            for i in range(13)
        ))
        for candidate in (duplicates,too_many):
            with self.subTest(evidence=candidate.evidence_refs),self.assertRaises(WorkflowError):
                self.staging.complete(candidate,actor=OWNER,generation=token,now=BASE)
        self.assertEqual(self.staging.report()["completed_count"],0)

    def test_full_18_agent_staging_dag_survives_reopen_at_each_handoff(self):
        """Actual SQLite handoffs through all 18 stages, still ONLY drafts."""
        from autopilot.agent_org import Handoff
        stages=self.staging.workflow.order
        self.assertEqual(len(stages),18)
        known={}
        for index,task_id in enumerate(stages):
            with self.subTest(stage=task_id):
                # Mimic a separate ephemeral worker/CI invocation every stage.
                node=SQLiteStagingClaims(
                    self.path,episode_id=EP,kind="short",language="hi"
                )
                self.assertIn(task_id,node.report()["ready_tasks"])
                contract=node.contracts[task_id]
                now=BASE+timedelta(seconds=10*index)
                generation=node.claim(task_id,actor=contract.owner,now=now)
                digest=sha256(task_id.encode("utf-8")).hexdigest()
                parent_refs=tuple("sha256:"+known[dep]
                                  for dep in contract.requires)
                handoff=Handoff(
                    task_id,contract.produces,digest,
                    parent_refs+("sha256:"+digest,),
                    contract.owner,BASE.isoformat(),
                )
                # Four-parent independent staging release review must link
                # *every* prerequisite, and missing one fails transactionally.
                if task_id.endswith(":release_review"):
                    self.assertEqual(len(contract.requires),4)
                    corrupted=replace(
                        handoff,evidence_refs=parent_refs[:-1]+
                        ("sha256:"+digest,)
                    )
                    with self.assertRaises(WorkflowError):
                        node.complete(corrupted,actor=contract.owner,
                                      generation=generation,
                                      now=now+timedelta(seconds=1))
                node.complete(handoff,actor=contract.owner,
                              generation=generation,
                              now=now+timedelta(seconds=2))
                known[task_id]=digest
                reopened=SQLiteStagingClaims(
                    self.path,episode_id=EP,kind="short",language="hi"
                )
                self.assertEqual(
                    reopened.report()["durable_staging_handoffs_verified"],index+1
                )
                self.assertFalse(reopened.report()["youtube_publishing_authorized"])
                self.assertFalse(
                    reopened.report()["evidence_independently_authenticated"]
                )
        final=SQLiteStagingClaims(
            self.path,episode_id=EP,kind="short",language="hi"
        ).report()
        self.assertEqual(final["completed_count"],18)
        self.assertEqual(final["ready_tasks"],[])
        self.assertEqual(final["running_count"],0)
        self.assertEqual(final["quarantined_count"],0)
        self.assertFalse(final["multi_worker_d1_or_cloud_deployed"])
        self.assertEqual(final["monthly_infrastructure_inr"],0)

    def _parallel_stages(self):
        parent=output(RESEARCH,OWNER)
        t1=self.staging.claim(RESEARCH,actor=OWNER,now=BASE)
        self.staging.complete(parent,actor=OWNER,generation=t1,
                              now=BASE+timedelta(seconds=1))
        actor="quality.fact_reviewer"
        t2=self.staging.claim(FACT,actor=actor,
                              now=BASE+timedelta(seconds=2))
        review=replace(output(FACT,actor),
                       evidence_refs=("sha256:"+parent.sha256_hex,))
        self.staging.complete(review,actor=actor,generation=t2,
                              now=BASE+timedelta(seconds=3))
        return f"{EP}:script",f"{EP}:hooks"

    def test_failed_parallel_agent_quarantines_and_fences_active_sibling(self):
        script,hooks=self._parallel_stages()
        script_owner="creative.shorts_writer"
        hook_owner="creative.hook_writer"
        hook_generation=self.staging.claim(
            hooks,actor=hook_owner,now=BASE+timedelta(seconds=4))
        for attempt in range(3):
            moment=BASE+timedelta(seconds=5+2*attempt)
            script_generation=self.staging.claim(
                script,actor=script_owner,now=moment)
            self.staging.fail(
                script,actor=script_owner,generation=script_generation,
                category="STAGING_FAILURE",now=moment+timedelta(seconds=1))
        state=self.staging.report()
        self.assertEqual(state["quarantined_count"],1)
        self.assertEqual(state["cancelled_peer_count"],1)
        self.assertEqual(state["running_count"],0)
        self.assertEqual(state["ready_tasks"],[])
        self.assertTrue(state["episode_aborted"])
        with self.assertRaises(WorkflowError):
            self.staging.heartbeat(
                hooks,actor=hook_owner,generation=hook_generation,
                now=BASE+timedelta(seconds=12))
        with self.assertRaises(WorkflowError):
            self.staging.complete(
                Handoff(hooks,"creative.hooks",
                        sha256(hooks.encode()).hexdigest(),
                        ("sha256:"+sha256(hooks.encode()).hexdigest(),),
                        hook_owner,BASE.isoformat()),
                actor=hook_owner,generation=hook_generation,
                now=BASE+timedelta(seconds=13),
            )
        reopened=SQLiteStagingClaims(
            self.path,episode_id=EP,kind="short",language="hi",
        )
        self.assertEqual(reopened.report(),state)
        self.assertEqual(reopened.abort_quarantined_siblings(),())

    def test_one_expired_parallel_stage_quarantines_other_inflight_work(self):
        script,hooks=self._parallel_stages()
        actor="creative.shorts_writer"
        # Use two prior ordinary failures to consume retry allowance.
        for offset in (4,6):
            generation=self.staging.claim(
                script,actor=actor,now=BASE+timedelta(seconds=offset))
            self.staging.fail(
                script,actor=actor,generation=generation,
                category="RENDER_FAILED",now=BASE+timedelta(seconds=offset+1))
        self.staging.claim(
            hooks,actor="creative.hook_writer",
            now=BASE+timedelta(seconds=8),lease_seconds=100)
        self.staging.claim(
            script,actor=actor,now=BASE+timedelta(seconds=8),
            lease_seconds=10)
        expired=self.staging.recover_expired(
            now=BASE+timedelta(seconds=18))
        self.assertEqual(expired,(script,))
        state=self.staging.report()
        self.assertEqual(state["quarantined_count"],1)
        self.assertEqual(state["cancelled_peer_count"],1)
        self.assertEqual(state["running_count"],0)
        self.assertEqual(state["ready_tasks"],[])
        self.assertFalse(state["publishing_authorized"]
                         if "publishing_authorized" in state
                         else state["youtube_publishing_authorized"])

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
