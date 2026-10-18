"""Signed staging gateway tests with fresh ephemeral keys, no accounts."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from secrets import token_bytes
from tempfile import TemporaryDirectory
import unittest

from autopilot.agent_org import EpisodeSpec, Handoff, WorkflowError
from autopilot.agent_staging_unified import UnifiedStagingCoordinator
from autopilot.agent_staging_auth_gateway import (
    SignedStagingGateway, SignedStagingRequest,
    sign_staging_request, handoff_digest,
)

BASE = datetime(2026, 10, 18, 16, tzinfo=timezone.utc)
EP = "signed_qa_01"
TID = EP + ":research"
OWNER = "research.launch_researcher"
REVIEWER = "quality.fact_reviewer"


class SignedWorkerGatewayTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db = Path(tmp.name) / "unified.sqlite3"
        self.episodes = (EpisodeSpec(EP, "short", "hi", 99),)
        self.core = UnifiedStagingCoordinator(
            self.db, episodes=self.episodes, create=True
        )
        self.core.reconcile()
        self.now = BASE
        self.key = token_bytes(32)
        self.other_key = token_bytes(32)
        self.registry = {
            "worker_research": (OWNER, self.key),
            "worker_review": (REVIEWER, self.other_key),
        }
        self.gateway = SignedStagingGateway(
            self.core, worker_keys=self.registry, clock=lambda: self.now
        )

    def sign(self, *, action="claim", worker="worker_research",
             task=TID, generation=0, lease=120, handoff_sha="",
             request_id="", expires=None, key=None):
        request = SignedStagingRequest(
            worker, action, EP, task, generation,
            int((expires or BASE + timedelta(seconds=60)).timestamp()),
            lease, handoff_sha, request_id,
        )
        return sign_staging_request(
            request, key=self.key if key is None else key
        )

    def artifact(self):
        digest = sha256(TID.encode("utf-8")).hexdigest()
        return Handoff(
            TID, "research.package", digest, ("sha256:" + digest,),
            OWNER, BASE.isoformat()
        )

    def test_signed_claim_complete_and_lost_ack_replay(self):
        token = self.gateway.claim(self.sign())
        self.assertEqual(token, 1)
        self.now = BASE + timedelta(seconds=5)
        h = self.artifact()
        completed = self.sign(
            action="complete", generation=token, lease=0,
            handoff_sha=handoff_digest(h), request_id="signed-ack-001"
        )
        first = self.gateway.complete(completed, h)
        reopened = UnifiedStagingCoordinator(self.db, episodes=self.episodes)
        second = SignedStagingGateway(
            reopened, worker_keys=self.registry, clock=lambda: self.now
        )
        self.assertEqual(second.complete(completed, h), first)
        self.assertEqual(reopened.report()["completed_tasks"], 1)
        self.assertFalse(first["publish_enabled"])
        self.assertFalse(second.status()["direct_coordinator_access_blocked"])
        self.assertFalse(second.status()["youtube_publishing_authorized"])

    def test_forged_mac_modified_task_or_wrong_secret_denied(self):
        signed = self.sign()
        for forged in (
            replace(signed, signature="0" * 64),
            replace(signed, task=EP + ":fact_review"),
            replace(signed, worker_id="worker_review"),
            self.sign(key=self.other_key),
        ):
            with self.subTest(payload=forged), self.assertRaises(WorkflowError):
                self.gateway.claim(forged)
        self.assertEqual(self.core.report()["running_tasks"], 0)

    def test_valid_other_worker_signature_wrong_role_denied(self):
        forged = self.sign(worker="worker_review", key=self.other_key)
        with self.assertRaises(WorkflowError):
            self.gateway.claim(forged)

    def test_expired_far_future_unsigned_and_upload_action_denied(self):
        candidates = (
            self.sign(expires=BASE - timedelta(seconds=1)),
            self.sign(expires=BASE + timedelta(minutes=10)),
            replace(self.sign(), signature=""),
            self.sign(action="upload_video"),
        )
        for request in candidates:
            with self.subTest(request=request), self.assertRaises(WorkflowError):
                self.gateway.claim(request)
        self.assertEqual(self.core.report()["running_tasks"], 0)

    def test_stale_signed_claim_after_failed_attempt_denied(self):
        previous = self.sign(generation=0)
        token = self.gateway.claim(previous)
        self.core.fail(EP, TID, actor=OWNER, generation=token,
                       now=BASE, category="FAKE_FAILURE")
        with self.assertRaises(WorkflowError):
            self.gateway.claim(previous)
        second = self.gateway.claim(self.sign(generation=2))
        self.assertGreater(second, token)

    def test_mismatched_completion_payload_refused(self):
        token = self.gateway.claim(self.sign())
        h = self.artifact()
        self.now = BASE + timedelta(seconds=1)
        request = self.sign(
            action="complete", generation=token, lease=0,
            handoff_sha=handoff_digest(h), request_id="signed-ack-002"
        )
        tampered = replace(h, sha256_hex=sha256(b"wrong").hexdigest())
        with self.assertRaises(WorkflowError):
            self.gateway.complete(request, tampered)
        self.assertEqual(self.core.report()["completed_tasks"], 0)
        self.gateway.complete(request, h)
        self.assertEqual(self.core.report()["completed_tasks"], 1)

    def test_registry_key_uniqueness_and_weak_key_denied(self):
        for workers in (
            {"worker_research": (OWNER, b"short")},
            {"worker_research": (OWNER, self.key),
             "worker_second": (OWNER, self.key)},
            {"worker_fake": ("publishing.publish_video", token_bytes(32))},
        ):
            with self.subTest(workers=tuple(workers)), self.assertRaises(WorkflowError):
                SignedStagingGateway(self.core, worker_keys=workers)
        self.assertFalse(self.gateway.status()["real_remote_worker_identity_authenticated"])

    def test_competing_authenticated_claims_only_one_succeeds(self):
        signed = self.sign()
        def attempt(_):
            stage = UnifiedStagingCoordinator(self.db, episodes=self.episodes)
            gate = SignedStagingGateway(
                stage, worker_keys=self.registry, clock=lambda: BASE
            )
            try:
                return gate.claim(signed)
            except WorkflowError:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcome = list(pool.map(attempt, range(2)))
        self.assertEqual(sum(x is not None for x in outcome), 1)
        self.assertEqual(self.core.report()["running_tasks"], 1)

    def test_optimistic_claim_generation_strict(self):
        with self.assertRaises(WorkflowError):
            self.core.claim(EP, TID, actor=OWNER, now=BASE,
                            expected_generation=True)
        with self.assertRaises(WorkflowError):
            self.core.claim(EP, TID, actor=OWNER, now=BASE,
                            expected_generation=5)
        self.assertEqual(self.gateway.claim(self.sign()), 1)


if __name__ == "__main__":
    unittest.main()
