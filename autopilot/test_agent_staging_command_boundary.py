"""No-network tests of narrow signed JSON staging command protocol."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from datetime import timedelta
from hashlib import sha256
from pathlib import Path
from secrets import token_bytes
from tempfile import TemporaryDirectory
import json
import unittest

from autopilot.agent_org import EpisodeSpec,Handoff,WorkflowError
from autopilot.agent_staging_unified import UnifiedStagingCoordinator
from autopilot.agent_staging_auth_gateway import (
    SignedStagingRequest,sign_staging_request,handoff_digest,
)
from autopilot.agent_staging_admin_gateway import (
    SignedStagingAdminCommand,sign_admin_command,
)
from autopilot.agent_staging_command_boundary import (
    SQLiteHostClock,StagingLocalCommandBoundary,
)


class LocalBoundaryTests(unittest.TestCase):
    def setUp(self):
        tmp=TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path=Path(tmp.name)/"offline.sqlite3"
        self.episodes=(EpisodeSpec("secure_video_01","short","en",90),)
        self.core=UnifiedStagingCoordinator(
            self.path,episodes=self.episodes,create=True
        )
        self.core.reconcile()
        self.worker_key=token_bytes(32)
        self.admin_key=token_bytes(32)
        self.eid="secure_video_01"
        self.task=self.eid+":research"
        self.actor="research.launch_researcher"
        self.worker="worker_research"
        self.key_id="key_research_001"
        self.admin="admin_flowminute"
        self.boundary=self.new_boundary(self.core)

    def new_boundary(self, core):
        return StagingLocalCommandBoundary(
            core,worker_keys={
                self.worker:(self.actor,self.key_id,self.worker_key)
            },admin_id=self.admin,admin_secret=self.admin_key,
        )

    def make_envelope(self,action,signed,handoff=None):
        return json.dumps({
            "action":action,"signed":asdict(signed),
            "handoff":asdict(handoff) if handoff is not None else None,
        },sort_keys=True,separators=(",",":"))

    def admin_cmd(self,action,nonce,*,role="",key_id=None,new_id=""):
        now=SQLiteHostClock(self.core).now()
        return sign_admin_command(
            SignedStagingAdminCommand(
                self.admin,action,self.worker,role,key_id or self.key_id,
                new_id,nonce,int((now+timedelta(seconds=60)).timestamp()),
            ),secret=self.admin_key,
        )

    def worker_cmd(self,action="claim",*,generation=0,digest="",
                   receipt="",expiry=60):
        now=SQLiteHostClock(self.core).now()
        return sign_staging_request(SignedStagingRequest(
            self.worker,action,self.eid,self.task,generation,
            int((now+timedelta(seconds=expiry)).timestamp()),
            120 if action=="claim" else 0,digest,receipt,self.key_id,
        ),key=self.worker_key)

    def handoff(self):
        digest=sha256(self.task.encode("utf-8")).hexdigest()
        return Handoff(self.task,"research.package",digest,
                       ("sha256:"+digest,),self.actor,
                       SQLiteHostClock(self.core).now().isoformat())

    def enroll(self,nonce="admin_enroll_00001"):
        return self.boundary.execute(self.make_envelope(
            "admin.apply",self.admin_cmd("enroll",nonce,role=self.actor),
        ))

    def test_signed_enroll_claim_complete_and_restart_ack(self):
        self.assertFalse(self.enroll()["publish_enabled"])
        grant=self.boundary.execute(self.make_envelope(
            "worker.claim",self.worker_cmd(),
        ))
        self.assertEqual(grant["generation"],1)
        handoff=self.handoff()
        command=self.worker_cmd(
            "complete",generation=1,digest=handoff_digest(handoff),
            receipt="completion_safe_0001",
        )
        payload=self.make_envelope("worker.complete",command,handoff)
        first=self.boundary.execute(payload)
        self.assertEqual(first["outcome"]["completed_tasks"],1)
        another=self.new_boundary(
            UnifiedStagingCoordinator(self.path,episodes=self.episodes)
        )
        self.assertEqual(another.execute(payload),first)
        self.assertFalse(another.safety()["isolated_service"])
        self.assertFalse(another.safety()["youtube_publishing_authorized"])

    def test_duplicate_json_unknown_actions_bad_fields_and_limit(self):
        for payload in (
            '{"action":"worker.claim","action":"worker.complete","signed":{},"handoff":null}',
            '{"action":"upload_video","signed":{},"handoff":null}',
            '{"action":"worker.heartbeat","signed":{},"handoff":null}',
            '{"action":"admin.apply","signed":{},"handoff":null,"sql":"DROP TABLE x"}',
            '{"action":"worker.claim","signed":NaN,"handoff":null}',
            "x"*8193,
        ):
            with self.subTest(text=payload[:40]),self.assertRaises(WorkflowError):
                self.boundary.execute(payload)

    def test_signature_expired_or_oversized_ttl_rejected(self):
        self.enroll("admin_enroll_00002")
        for expiry in (-2,200):
            with self.subTest(expiry=expiry),self.assertRaises(WorkflowError):
                self.boundary.execute(self.make_envelope(
                    "worker.claim",self.worker_cmd(expiry=expiry),
                ))
        self.assertEqual(self.core.report()["running_tasks"],0)

    def test_key_rotation_invalidates_old_signed_claim(self):
        self.enroll("admin_enroll_00003")
        signed=self.worker_cmd()
        self.boundary.execute(self.make_envelope(
            "admin.apply",
            self.admin_cmd("rotate","admin_rotate_00004",
                           new_id="key_research_002"),
        ))
        with self.assertRaises(WorkflowError):
            self.boundary.execute(self.make_envelope("worker.claim",signed))
        self.assertEqual(self.core.report()["running_tasks"],0)

    def test_admin_one_time_nonce_replay(self):
        cmd=self.admin_cmd("enroll","admin_enroll_00005",role=self.actor)
        payload=self.make_envelope("admin.apply",cmd)
        self.boundary.execute(payload)
        with self.assertRaises(WorkflowError):
            self.boundary.execute(payload)

    def test_independent_signed_clients_one_task_claim(self):
        self.enroll("admin_enroll_00006")
        payload=self.make_envelope("worker.claim",self.worker_cmd())
        def contender(_):
            other=self.new_boundary(
                UnifiedStagingCoordinator(self.path,episodes=self.episodes)
            )
            try:
                return other.execute(payload)
            except WorkflowError:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(contender,range(2)))
        self.assertEqual(sum(x is not None for x in results),1)
        self.assertEqual(self.core.report()["running_tasks"],1)

    def test_safety_report_explicitly_does_not_claim_cloud_auth(self):
        safety=self.boundary.safety()
        self.assertEqual(safety["allowed_actions"],
                         ("worker.claim","worker.complete","admin.apply"))
        self.assertFalse(safety["isolated_service"])
        self.assertFalse(safety["direct_database_access_protected"])
        self.assertFalse(safety["remotely_trusted_database_clock"])
        self.assertFalse(safety["youtube_publishing_authorized"])
        self.assertEqual(safety["monthly_recurring_infrastructure_inr"],0)


if __name__=="__main__":
    unittest.main()
