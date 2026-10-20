"""No-secret policy rotation/revocation with signed staging task races."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from hashlib import sha256
from pathlib import Path
from secrets import token_bytes
from tempfile import TemporaryDirectory
import sqlite3
from contextlib import closing
import unittest

from autopilot.agent_org import EpisodeSpec,Handoff,WorkflowError
from autopilot.agent_staging_unified import UnifiedStagingCoordinator
from autopilot.agent_staging_auth_gateway import (
    SignedStagingGateway,SignedStagingRequest,sign_staging_request,
    handoff_digest,
)
from autopilot.agent_staging_key_policy import StagingKeyPolicy

BASE=datetime(2026,10,18,16,0,tzinfo=timezone.utc)
EP="policy_qa_01"
ROOT=f"{EP}:research"
ACTOR="research.launch_researcher"
KID_A="key_research_001"
KID_B="key_research_002"
KID_C="key_research_003"


class DurableKeyLifecycleTests(unittest.TestCase):
    def setUp(self):
        tmp=TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path=Path(tmp.name)/"unified.sqlite3"
        self.episodes=(EpisodeSpec(EP,"short","hi",90),)
        self.core=UnifiedStagingCoordinator(
            self.path,episodes=self.episodes,create=True
        )
        self.core.reconcile()
        self.policy=StagingKeyPolicy(self.core)
        self.policy.enroll("worker_research",ACTOR,KID_A)
        self.key_a=token_bytes(32)
        self.key_b=token_bytes(32)
        self.now=BASE
        self.gateway_a=self.gateway(self.key_a,KID_A)

    def gateway(self,key,key_id):
        return SignedStagingGateway(
            self.core,worker_keys={"worker_research":(ACTOR,key_id,key)},
            key_policy=self.policy,clock=lambda:self.now
        )

    def signed(self,key,key_id,*,action="claim",generation=0,
               expiry=BASE+timedelta(seconds=60),handoff_sha="",receipt=""):
        return sign_staging_request(
            SignedStagingRequest(
                "worker_research",action,EP,ROOT,generation,
                int(expiry.timestamp()),
                120 if action=="claim" else 0,
                handoff_sha,receipt,key_id
            ),key=key
        )

    def handoff(self):
        digest=sha256(ROOT.encode()).hexdigest()
        return Handoff(ROOT,"research.package",digest,
                       ("sha256:"+digest,),ACTOR,BASE.isoformat())

    def test_enrolled_key_claims_and_nonsecret_policy_survives_reopen(self):
        before=self.policy.status()
        self.assertEqual(before["enrollments"][0]["state"],"active")
        self.assertFalse(before["stores_secrets"])
        with closing(sqlite3.connect(self.path)) as db:
            schema=" ".join(row[0] for row in db.execute(
                "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL"
            ).fetchall())
        self.assertNotIn(self.key_a.hex(),schema)
        reopened=UnifiedStagingCoordinator(self.path,episodes=self.episodes)
        policy=StagingKeyPolicy(reopened)
        self.assertEqual(policy.status(),before)
        self.assertEqual(self.gateway_a.claim(
            self.signed(self.key_a,KID_A)),1)

    def test_rotation_revokes_previous_signed_claim_and_allows_new_key(self):
        old=self.signed(self.key_a,KID_A)
        self.assertEqual(self.policy.rotate(
            "worker_research",old_key_id=KID_A,new_key_id=KID_B),2)
        with self.assertRaises(WorkflowError):
            self.gateway_a.claim(old)
        good=self.gateway(self.key_b,KID_B)
        self.assertEqual(good.claim(self.signed(self.key_b,KID_B)),1)
        status=self.policy.status()
        self.assertEqual(status["enrollments"][0]["generation"],2)
        with self.assertRaises(WorkflowError):
            self.policy.rotate("worker_research",old_key_id=KID_B,new_key_id=KID_A)
        with self.assertRaises(WorkflowError):
            self.policy.enroll("worker_new",ACTOR,KID_A)

    def test_revoked_worker_cannot_replay_signed_completion_receipt(self):
        token=self.gateway_a.claim(self.signed(self.key_a,KID_A))
        self.now=BASE+timedelta(seconds=5)
        h=self.handoff()
        end=self.signed(self.key_a,KID_A,action="complete",
                        generation=token,handoff_sha=handoff_digest(h),
                        receipt="receipt-policy-001")
        first=self.gateway_a.complete(end,h)
        self.assertEqual(first["completed_tasks"],1)
        self.policy.revoke("worker_research",expected_key_id=KID_A)
        with self.assertRaises(WorkflowError):
            self.gateway_a.complete(end,h)
        self.assertEqual(self.core.report()["completed_tasks"],1)
        again=StagingKeyPolicy(
            UnifiedStagingCoordinator(self.path,episodes=self.episodes)
        )
        self.assertEqual(again.status()["enrollments"][0]["state"],"revoked")

    def test_revocation_blocks_in_flight_completion_and_reenrollment(self):
        token=self.gateway_a.claim(self.signed(self.key_a,KID_A))
        self.policy.revoke("worker_research",expected_key_id=KID_A)
        self.now=BASE+timedelta(seconds=4)
        h=self.handoff()
        with self.assertRaises(WorkflowError):
            self.gateway_a.complete(self.signed(
                self.key_a,KID_A,action="complete",generation=token,
                handoff_sha=handoff_digest(h),receipt="receipt-policy-002"
            ),h)
        self.assertEqual(self.core.report()["running_tasks"],1)
        with self.assertRaises(WorkflowError):
            self.policy.enroll("worker_research",ACTOR,KID_C)
        with self.assertRaises(WorkflowError):
            self.policy.rotate("worker_research",old_key_id=KID_A,new_key_id=KID_C)

    def test_two_concurrent_old_and_new_claims_at_rotation(self):
        old=self.signed(self.key_a,KID_A)
        with ThreadPoolExecutor(max_workers=2) as pool:
            # One local claim either precedes rotation (and gets fenced
            # by the current active generation) or follows it and is denied.
            futures=[
                pool.submit(lambda:self.policy.rotate(
                    "worker_research",old_key_id=KID_A,new_key_id=KID_B)),
                pool.submit(lambda:self._try_old_claim(old)),
            ]
            results=[f.result() for f in futures]
        self.assertEqual(results[0],2)
        self.assertIn(results[1],(None,1))
        with self.assertRaises(WorkflowError):
            self.gateway_a.claim(old)
        self.assertEqual(self.policy.status()["enrollments"][0]["key_id"],KID_B)

    def _try_old_claim(self,request):
        try:
            return self.gateway_a.claim(request)
        except WorkflowError:
            return None

    def test_invalid_operators_and_tombstone_duplicate_denied(self):
        for work,role,key in (
            ("x",ACTOR,KID_C),
            ("worker_new","publishing.publish_video",KID_C),
            ("worker_new",ACTOR,"weak"),
        ):
            with self.assertRaises(WorkflowError):
                self.policy.enroll(work,role,key)
        with self.assertRaises(WorkflowError):
            self.policy.revoke("worker_research",expected_key_id=KID_B)
        self.assertFalse(self.policy.status()["admin_calls_remotely_authenticated"])

    def test_policy_binding_refuses_other_coordinator_database(self):
        other=TemporaryDirectory()
        self.addCleanup(other.cleanup)
        db=Path(other.name)/"other.sqlite3"
        separate=UnifiedStagingCoordinator(db,episodes=self.episodes,create=True)
        with self.assertRaises(WorkflowError):
            SignedStagingGateway(
                separate,worker_keys={
                    "worker_research":(ACTOR,KID_A,self.key_a)
                },key_policy=self.policy,clock=lambda:BASE
            )


if __name__=="__main__":
    unittest.main()
