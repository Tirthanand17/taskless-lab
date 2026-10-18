"""Phase 4G.4 real SQLite DB-clock transitions. Offline simulator ONLY."""
import json
import unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from autopilot.core import CHANNEL_ID
from autopilot.phase4_offline_ledger import OfflineLedger,ProtocolBlocked
from autopilot.phase4g_recovery_audit import inspect_offline_release_recovery

UTC=timezone.utc
SLOT="2026-10-22T05:30:00+00:00"
SHA="b"*64
REVIEW="c"*64
VID="abc123def45"
def ago(seconds):
    return (datetime.now(UTC)-timedelta(seconds=seconds)).isoformat(timespec="seconds")

class OfflineDatabaseClockTransitionsTests(unittest.TestCase):
    def setUp(self):
        self.ledger=OfflineLedger(offline_test_only=True)
        self.addCleanup(self.ledger.close)
        self.ledger.reserve(channel=CHANNEL_ID,episode="video01",planned_utc=SLOT,
            media_sha256=SHA,now_utc=ago(600))
        self.version,self.fence=self.ledger.claim_db_clock_rehearsal(
            "video01",expected_version=0,owner="worker_A",ttl_seconds=240)

    def step(self,name):
        self.version=self.ledger.local_step_db_clock_rehearsal(
            "video01",target=name,expected_version=self.version,
            owner="worker_A",fence=self.fence,
            review_digest=REVIEW if name=="media_qa_passed" else None)

    def ready(self):
        for name in ("research_verified","script_verified","media_qa_passed"):
            self.step(name)

    def test_all_three_local_steps_preserve_event_chain(self):
        self.ready()
        row=self.ledger.get("video01")
        self.assertEqual(row["stage"],"media_qa_passed")
        self.assertEqual(row["review_digest"],REVIEW)
        last=self.ledger.events("video01")[-1]
        self.assertEqual(json.loads(last["detail_json"])["review_digest"],REVIEW)
        report=inspect_offline_release_recovery(self.ledger)
        self.assertEqual(report["event_count"],5)
        self.assertFalse(report["real_server_clock_enforced"])
        self.assertFalse(report["real_authenticated_provider_readback_verified"])
        self.assertFalse(report["public_publishing_authorized"])
        self.assertEqual(report["network_calls"],0)

    def test_client_supplied_time_cannot_bypass_real_lease(self):
        with self.assertRaises(TypeError):
            self.ledger.local_step_db_clock_rehearsal(
                "video01",target="research_verified",
                expected_version=self.version,owner="worker_A",
                fence=self.fence,now_utc="2099-01-01T00:00:00+00:00")
        self.assertEqual(self.ledger.get("video01")["stage"],"planned")

    def test_no_stage_skip_or_review_approval_forgery(self):
        for target,digest in (
            ("script_verified",None),
            ("media_qa_passed",REVIEW),
            ("public_verified",None),
            ("research_verified",REVIEW),
        ):
            with self.subTest(target=target,digest=digest):
                with self.assertRaises(ProtocolBlocked):
                    self.ledger.local_step_db_clock_rehearsal(
                        "video01",target=target,expected_version=self.version,
                        owner="worker_A",fence=self.fence,review_digest=digest)
        self.assertEqual(self.ledger.get("video01")["stage"],"planned")

    def test_stale_version_wrong_owner_and_fence_rejected(self):
        for args in (
            {"expected_version":self.version+1,"owner":"worker_A","fence":self.fence},
            {"expected_version":self.version,"owner":"worker_B","fence":self.fence},
            {"expected_version":self.version,"owner":"worker_A","fence":self.fence+1},
            {"expected_version":self.version,"owner":"worker_A","fence":True},
        ):
            with self.subTest(args=args),self.assertRaises(ProtocolBlocked):
                self.ledger.local_step_db_clock_rehearsal(
                    "video01",target="research_verified",**args)
        self.assertEqual(len(self.ledger.events("video01")),2)

    def test_forced_expired_fixture_lease_cannot_be_extended_by_worker_clock(self):
        self.ledger.db.execute("UPDATE phase4_releases SET lease_until=?",(ago(60),))
        with self.assertRaisesRegex(ProtocolBlocked,"Expired/stale"):
            self.ledger.local_step_db_clock_rehearsal(
                "video01",target="research_verified",
                expected_version=self.version,owner="worker_A",fence=self.fence)
        self.assertEqual(self.ledger.get("video01")["version"],1)

    def test_upload_intent_reserves_once_without_network(self):
        self.ready()
        self.version=self.ledger.begin_upload_intent_db_clock_rehearsal(
            "video01",expected_version=self.version,owner="worker_A",
            fence=self.fence,media_sha256=SHA,intent_id="upload_once_01")
        state=self.ledger.get("video01")
        self.assertEqual(state["stage"],"upload_uncertain")
        self.assertEqual(state["intent_id"],"upload_once_01")
        with self.assertRaises(ProtocolBlocked):
            self.ledger.begin_upload_intent_db_clock_rehearsal(
                "video01",expected_version=self.version,owner="worker_A",
                fence=self.fence,media_sha256=SHA,intent_id="upload_again")
        report=inspect_offline_release_recovery(self.ledger)
        self.assertEqual(report["upload_uncertain_count"],1)
        self.assertFalse(report["safe_to_blindly_retry_upload"])
        self.assertFalse(report["youtube_upload_or_scheduling_authorized"])

    def test_upload_intent_requires_qa_and_exact_hash(self):
        with self.assertRaises(ProtocolBlocked):
            self.ledger.begin_upload_intent_db_clock_rehearsal(
                "video01",expected_version=self.version,owner="worker_A",
                fence=self.fence,media_sha256=SHA,intent_id="first")
        self.ready()
        with self.assertRaises(ProtocolBlocked):
            self.ledger.begin_upload_intent_db_clock_rehearsal(
                "video01",expected_version=self.version,owner="worker_A",
                fence=self.fence,media_sha256="a"*64,intent_id="first")
        with self.assertRaises(TypeError):
            self.ledger.begin_upload_intent_db_clock_rehearsal(
                "video01",expected_version=self.version,owner="worker_A",
                fence=self.fence,media_sha256=SHA,intent_id="first",
                now_utc="2099-01-01T00:00:00+00:00")

    def test_schedule_intent_requires_existing_simulated_private_state(self):
        with self.assertRaises(ProtocolBlocked):
            self.ledger.begin_schedule_intent_db_clock_rehearsal(
                "video01",expected_version=self.version,owner="worker_A",
                fence=self.fence)
        self.ready()
        self.version=self.ledger.begin_upload_intent_db_clock_rehearsal(
            "video01",expected_version=self.version,owner="worker_A",
            fence=self.fence,media_sha256=SHA,intent_id="intent_for_schedule")
        # Caller 'authenticated=True' below is MOCK ONLY, not live Google proof.
        now=datetime.now(UTC).isoformat(timespec="seconds")
        self.version=self.ledger.bind_private_readback(
            "video01",expected_version=self.version,
            owner="worker_A",fence=self.fence,now_utc=now,
            remote_channel=CHANNEL_ID,youtube_id=VID,
            processed=True,privacy="private",authenticated=True)
        self.version=self.ledger.begin_schedule_intent_db_clock_rehearsal(
            "video01",expected_version=self.version,owner="worker_A",
            fence=self.fence)
        self.assertEqual(self.ledger.get("video01")["stage"],"schedule_uncertain")
        with self.assertRaises(ProtocolBlocked):
            self.ledger.begin_schedule_intent_db_clock_rehearsal(
                "video01",expected_version=self.version,owner="worker_A",
                fence=self.fence)
        report=inspect_offline_release_recovery(self.ledger)
        self.assertEqual(report["schedule_uncertain_count"],1)
        self.assertFalse(report["safe_to_blindly_retry_schedule"])
        self.assertFalse(report["real_authenticated_provider_readback_verified"])

    def test_reclaimed_worker_does_not_let_old_fence_resume(self):
        separate=OfflineLedger(offline_test_only=True)
        self.addCleanup(separate.close)
        separate.reserve(channel=CHANNEL_ID,episode="expired_fixture",
                         planned_utc=SLOT,media_sha256=SHA,now_utc=ago(700))
        version,fence=separate.claim(
            "expired_fixture",expected_version=0,owner="retired",
            now_utc=ago(350),ttl_seconds=30)
        new_version,new_fence=separate.claim_db_clock_rehearsal(
            "expired_fixture",expected_version=version,owner="replacement")
        with self.assertRaises(ProtocolBlocked):
            separate.local_step_db_clock_rehearsal(
                "expired_fixture",target="research_verified",
                expected_version=version,owner="retired",fence=fence)
        version=separate.local_step_db_clock_rehearsal(
            "expired_fixture",target="research_verified",
            expected_version=new_version,owner="replacement",fence=new_fence)
        self.assertEqual(separate.get("expired_fixture")["stage"],"research_verified")
        self.assertFalse(inspect_offline_release_recovery(separate)[
            "real_authenticated_provider_readback_verified"])

    def test_competing_connections_only_one_transition_succeeds(self):
        with TemporaryDirectory() as temp:
            path=Path(temp)/"fixture.sqlite"
            a=OfflineLedger(path,offline_test_only=True)
            b=OfflineLedger(path,offline_test_only=True)
            try:
                a.reserve(channel=CHANNEL_ID,episode="shared_ep",
                          planned_utc=SLOT,media_sha256=SHA,now_utc=ago(600))
                version,fence=a.claim_db_clock_rehearsal(
                    "shared_ep",expected_version=0,owner="runner_A")
                version2=a.local_step_db_clock_rehearsal(
                    "shared_ep",target="research_verified",
                    expected_version=version,owner="runner_A",fence=fence)
                with self.assertRaises(ProtocolBlocked):
                    b.local_step_db_clock_rehearsal(
                        "shared_ep",target="research_verified",
                        expected_version=version,owner="runner_A",fence=fence)
                self.assertEqual(a.get("shared_ep")["version"],version2)
                self.assertEqual(len(a.events("shared_ep")),3)
            finally:
                b.close()
                a.close()

if __name__=="__main__":
    unittest.main()
