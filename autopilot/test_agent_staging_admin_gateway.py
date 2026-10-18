"""Local signed admin commands, atomic one-time nonce, no secrets."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from pathlib import Path
from secrets import token_bytes
from tempfile import TemporaryDirectory
import sqlite3
from contextlib import closing
import unittest

from autopilot.agent_org import EpisodeSpec,WorkflowError
from autopilot.agent_staging_unified import UnifiedStagingCoordinator
from autopilot.agent_staging_key_policy import StagingKeyPolicy
from autopilot.agent_staging_admin_gateway import (
    SignedStagingAdminGateway,SignedStagingAdminCommand,sign_admin_command,
)

BASE=datetime(2026,10,18,16,0,tzinfo=timezone.utc)
ROLE="research.launch_researcher"
ADMIN="admin_flowminute_qa"
WORKER="worker_research"
KEY1="research_key_0001"
KEY2="research_key_0002"
KEY3="research_key_0003"


class SignedAdminPolicyTests(unittest.TestCase):
    def setUp(self):
        tmp=TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path=Path(tmp.name)/"staging.sqlite3"
        self.specs=(EpisodeSpec("admin_test_01","short","en",90),)
        self.core=UnifiedStagingCoordinator(
            self.path,episodes=self.specs,create=True
        )
        self.policy=StagingKeyPolicy(self.core)
        self.key=token_bytes(32)
        self.now=BASE
        self.gateway=SignedStagingAdminGateway(
            self.policy,admin_id=ADMIN,secret=self.key,
            clock=lambda:self.now,
        )

    def signed(self,action,nonce,*,worker=WORKER,role="",
               key_id=KEY1,new_key_id="",secret=None,expires=None):
        command=SignedStagingAdminCommand(
            ADMIN,action,worker,role,key_id,new_key_id,nonce,
            int((expires if expires is not None else
                 BASE+timedelta(seconds=60)).timestamp()),
        )
        return sign_admin_command(
            command,secret=self.key if secret is None else secret
        )

    def start(self):
        return self.gateway.apply(self.signed(
            "enroll","admin_enroll_0001",role=ROLE
        ))

    def test_signed_enroll_rotate_revoke_and_restart(self):
        enroll=self.start()
        self.assertTrue(enroll["signed_admin_command_committed"])
        rotate=self.gateway.apply(self.signed(
            "rotate","admin_rotate_0002",new_key_id=KEY2
        ))
        self.assertEqual(rotate["key_generation"],2)
        revoke=self.gateway.apply(self.signed(
            "revoke","admin_revoke_0003",key_id=KEY2
        ))
        self.assertIsNone(revoke["key_generation"])
        self.assertFalse(revoke["publishing_authorized"])
        reopened=UnifiedStagingCoordinator(self.path,episodes=self.specs)
        policy=StagingKeyPolicy(reopened)
        state=policy.status()
        self.assertEqual(state["admin_replay_nonces_consumed"],3)
        self.assertEqual(state["enrollments"][0]["state"],"revoked")
        self.assertEqual(state["enrollments"][0]["key_id"],KEY2)
        again=SignedStagingAdminGateway(
            policy,admin_id=ADMIN,secret=self.key,clock=lambda:BASE
        )
        with self.assertRaises(WorkflowError):
            again.apply(self.signed("revoke","admin_revoke_0003",key_id=KEY2))
        self.assertFalse(again.status()["remote_admin_identity_authenticated"])

    def test_forged_mac_and_changed_action_scope_denied(self):
        base=self.signed("enroll","admin_enroll_0004",role=ROLE)
        payloads=(
            replace(base,signature="0"*64),
            replace(base,worker_id="worker_swapped"),
            replace(base,action="revoke"),
            self.signed("enroll","admin_enroll_0004",role=ROLE,
                        secret=token_bytes(32)),
        )
        for payload in payloads:
            with self.subTest(value=payload),self.assertRaises(WorkflowError):
                self.gateway.apply(payload)
        self.assertEqual(self.policy.status()["admin_replay_nonces_consumed"],0)
        self.assertEqual(self.policy.status()["enrollments"],[])

    def test_expired_future_and_unauthorized_action_denied(self):
        for request in (
            self.signed("enroll","admin_expired_001",role=ROLE,
                        expires=BASE-timedelta(seconds=1)),
            self.signed("enroll","admin_future_0002",role=ROLE,
                        expires=BASE+timedelta(minutes=15)),
            self.signed("upload_video","admin_upload_0003",role=ROLE),
        ):
            with self.subTest(request=request),self.assertRaises(WorkflowError):
                self.gateway.apply(request)
        self.assertEqual(self.policy.status()["admin_replay_nonces_consumed"],0)

    def test_nonce_refused_after_same_payload_or_new_payload(self):
        self.start()
        with self.assertRaises(WorkflowError):
            self.gateway.apply(self.signed(
                "enroll","admin_enroll_0001",role=ROLE
            ))
        with self.assertRaises(WorkflowError):
            self.gateway.apply(self.signed(
                "rotate","admin_enroll_0001",new_key_id=KEY2
            ))
        self.assertEqual(self.policy.status()["admin_replay_nonces_consumed"],1)

    def test_failed_rotation_rolls_back_consumed_nonce(self):
        self.start()
        failed=self.signed(
            "rotate","admin_badrotate_001",
            key_id=KEY3,new_key_id=KEY2,
        )
        with self.assertRaises(WorkflowError):
            self.gateway.apply(failed)
        self.assertEqual(self.policy.status()["admin_replay_nonces_consumed"],1)
        self.gateway.apply(self.signed(
            "rotate","admin_badrotate_001",
            key_id=KEY1,new_key_id=KEY2,
        ))
        self.assertEqual(self.policy.status()["admin_replay_nonces_consumed"],2)
        self.assertEqual(self.policy.status()["enrollments"][0]["key_id"],KEY2)

    def test_competing_same_nonce_only_one_admin_command_applied(self):
        command=self.signed("enroll","admin_race_nonce_001",role=ROLE)
        def run(_):
            reopened=StagingKeyPolicy(UnifiedStagingCoordinator(
                self.path,episodes=self.specs,
            ))
            gateway=SignedStagingAdminGateway(
                reopened,admin_id=ADMIN,secret=self.key,clock=lambda:BASE,
            )
            try:
                return gateway.apply(command)
            except WorkflowError:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(run,range(2)))
        self.assertEqual(sum(x is not None for x in results),1)
        self.assertEqual(self.policy.status()["admin_replay_nonces_consumed"],1)
        self.assertEqual(len(self.policy.status()["enrollments"]),1)

    def test_rehashed_invalid_admin_nonce_record_rejected(self):
        self.start()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute(
                "UPDATE staging_admin_commands SET action='publish_video'"
            )
            db.commit()
        with self.assertRaises(WorkflowError):
            StagingKeyPolicy(
                UnifiedStagingCoordinator(self.path,episodes=self.specs)
            )

    def test_no_raw_hmac_secret_in_sqlite_and_audit_status_bounded(self):
        self.start()
        self.assertTrue(self.gateway.status()["offline_admin_hmac_authenticated"])
        with closing(sqlite3.connect(self.path)) as db:
            rows=db.execute(
                "SELECT nonce,admin_id,action,request_sha "
                "FROM staging_admin_commands"
            ).fetchall()
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0][1],ADMIN)
        self.assertEqual(rows[0][2],"enroll")
        self.assertNotIn(self.key.hex(),repr(rows))
        self.assertFalse(self.policy.status()["stores_secrets"])
        self.assertFalse(self.gateway.status()["youtube_publishing_authorized"])


if __name__=="__main__":
    unittest.main()
