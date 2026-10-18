"""Phase 4G recovery snapshot audit against actual EXISTING SQLite simulator."""
import unittest

from autopilot.core import CHANNEL_ID
from autopilot.phase4_offline_ledger import OfflineLedger,ProtocolBlocked
from autopilot.phase4g_recovery_audit import inspect_offline_release_recovery

NOW="2026-10-18T08:00:00+00:00"
LATER="2026-10-18T08:00:25+00:00"
EXPIRED="2026-10-18T08:04:00+00:00"
SLOT="2026-10-20T05:30:00+00:00"
MEDIA="a"*64
QA="b"*64
VID="abc123def45"

class ExistingReleaseRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.ledger=OfflineLedger(offline_test_only=True)
        self.addCleanup(self.ledger.close)
        self.ledger.reserve(channel=CHANNEL_ID,episode="tut_01",
                            planned_utc=SLOT,media_sha256=MEDIA,now_utc=NOW)
        self.version,self.fence=self.ledger.claim(
            "tut_01",expected_version=0,owner="worker_one",now_utc=NOW)

    def audit(self):
        return inspect_offline_release_recovery(self.ledger)

    def ready(self):
        for stage in ("research_verified","script_verified","media_qa_passed"):
            self.version=self.ledger.local_step(
                "tut_01",target=stage,expected_version=self.version,
                owner="worker_one",fence=self.fence,now_utc=LATER,
                review_digest=QA if stage=="media_qa_passed" else None)

    def begin_upload(self):
        self.ready()
        self.version=self.ledger.begin_upload_once(
            "tut_01",expected_version=self.version,
            owner="worker_one",fence=self.fence,now_utc=LATER,
            media_sha256=MEDIA,intent_id="intent_one")

    def private(self):
        self.begin_upload()
        self.version=self.ledger.bind_private_readback(
            "tut_01",expected_version=self.version,
            owner="worker_one",fence=self.fence,now_utc=LATER,
            remote_channel=CHANNEL_ID,youtube_id=VID,
            processed=True,privacy="private",authenticated=True)

    def test_initial_reservation_and_lease_rebuild(self):
        r=self.audit()
        self.assertEqual(r["release_count"],1)
        self.assertEqual(r["event_count"],2)
        self.assertEqual(r["lease_fences_seen"],1)
        self.assertEqual(r["needs_real_provider_reconciliation_count"],0)
        self.assertTrue(r["client_clock_trusted_by_simulator"])
        self.assertFalse(r["real_server_clock_enforced"])
        self.assertFalse(r["safe_to_blindly_retry_upload"])
        self.assertFalse(r["public_publishing_authorized"])
        self.assertFalse(r["production_cloud_ledger_writer_deployed"])
        self.assertEqual(r["network_calls"],0)
        self.assertEqual(r["database_writes"],0)
        self.assertNotIn("tut_01",str(r))
        self.assertNotIn(VID,str(r))

    def test_upload_crash_uncertainty_blocks_duplicate_retry(self):
        self.begin_upload()
        r=self.audit()
        self.assertEqual(r["upload_uncertain_count"],1)
        self.assertEqual(r["upload_intent_count"],1)
        self.assertEqual(r["needs_real_provider_reconciliation_count"],1)
        self.assertFalse(r["safe_to_blindly_retry_upload"])

    def test_expired_lease_new_worker_still_cannot_reupload(self):
        self.begin_upload()
        v,f=self.ledger.claim("tut_01",expected_version=self.version,
                              owner="worker_two",now_utc=EXPIRED)
        with self.assertRaises(ProtocolBlocked):
            self.ledger.begin_upload_once(
                "tut_01",expected_version=v,owner="worker_two",
                fence=f,media_sha256=MEDIA,intent_id="other_intent",
                now_utc=EXPIRED)
        r=self.audit()
        self.assertEqual(r["upload_intent_count"],1)
        self.assertEqual(r["lease_fences_seen"],2)

    def test_schedule_uncertainty_prevents_unsafe_repeat(self):
        self.private()
        self.version=self.ledger.begin_schedule_once(
            "tut_01",expected_version=self.version,owner="worker_one",
            fence=self.fence,now_utc=LATER)
        r=self.audit()
        self.assertEqual(r["schedule_uncertain_count"],1)
        self.assertEqual(r["needs_real_provider_reconciliation_count"],1)
        self.assertFalse(r["safe_to_blindly_retry_schedule"])

    def test_public_state_is_not_real_youtube_proof(self):
        self.private()
        self.version=self.ledger.begin_schedule_once(
            "tut_01",expected_version=self.version,owner="worker_one",
            fence=self.fence,now_utc=LATER)
        self.version=self.ledger.bind_schedule_readback(
            "tut_01",expected_version=self.version,owner="worker_one",
            fence=self.fence,now_utc=LATER,youtube_id=VID,
            publish_at_utc=SLOT,authenticated=True,privacy="private")
        self.version=self.ledger.bind_public_readback(
            "tut_01",expected_version=self.version,owner="worker_one",
            fence=self.fence,now_utc=LATER,youtube_id=VID,
            authenticated=True,playable=True,privacy="public")
        r=self.audit()
        self.assertEqual(r["terminal_public_claim_count"],1)
        self.assertFalse(r["real_authenticated_provider_readback_verified"])
        self.assertFalse(r["public_publishing_authorized"])

    def test_quarantine_is_terminal_and_does_not_approve(self):
        self.version=self.ledger.quarantine(
            "tut_01",expected_version=self.version,
            owner="worker_one",fence=self.fence,now_utc=LATER,
            reason="The media could not be independently verified")
        r=self.audit()
        self.assertEqual(r["terminal_quarantined_count"],1)
        self.assertFalse(r["youtube_upload_or_scheduling_authorized"])

    def test_release_row_stage_tamper_detected(self):
        self.begin_upload()
        self.ledger.db.execute("UPDATE phase4_releases SET stage='public_verified'")
        with self.assertRaisesRegex(ProtocolBlocked,"integrity inconsistent"):
            self.audit()

    def test_release_version_tamper_detected(self):
        self.ledger.db.execute("UPDATE phase4_releases SET version=900")
        with self.assertRaises(ProtocolBlocked):
            self.audit()

    def test_release_fence_tamper_detected(self):
        self.ledger.db.execute("UPDATE phase4_releases SET fence=99")
        with self.assertRaises(ProtocolBlocked):
            self.audit()

    def test_release_media_sha_tamper_detected(self):
        self.ledger.db.execute(
            "UPDATE phase4_releases SET media_sha256=?",("c"*64,))
        with self.assertRaises(ProtocolBlocked):
            self.audit()

    def test_release_remote_video_tamper_detected(self):
        self.private()
        self.ledger.db.execute("UPDATE phase4_releases SET youtube_id=?",
                               ("zyx987hgf65",))
        with self.assertRaises(ProtocolBlocked):
            self.audit()

    def test_release_upload_intent_tamper_detected(self):
        self.begin_upload()
        self.ledger.db.execute("UPDATE phase4_releases SET intent_id=?",
                               ("forged_intent",))
        with self.assertRaises(ProtocolBlocked):
            self.audit()

    def test_false_existing_lease_owner_tamper_detected(self):
        self.ledger.db.execute("UPDATE phase4_releases SET lease_owner=?",
                               ("intruder_worker",))
        with self.assertRaises(ProtocolBlocked):
            self.audit()

    def test_untracked_orphan_release_detected(self):
        self.ledger.db.execute(
            "INSERT INTO phase4_releases "
            "(channel_id,episode_id,planned_utc,media_sha256,stage) "
            "VALUES (?,?,?,?,?)",
            (CHANNEL_ID,"orphan_ep","2026-10-21T05:30:00+00:00","c"*64,"planned"))
        with self.assertRaises(ProtocolBlocked):
            self.audit()

    def test_reject_if_inside_other_transaction(self):
        self.ledger.db.execute("BEGIN")
        try:
            with self.assertRaisesRegex(ProtocolBlocked,"another transaction"):
                self.audit()
        finally:
            self.ledger.db.execute("ROLLBACK")

    def test_reject_unrelated_objects_or_unbounded_history(self):
        with self.assertRaises(ProtocolBlocked):
            inspect_offline_release_recovery(object())
        # Never claims live Cloudflare D1 adapter support.
        self.assertFalse(self.audit()["production_cloud_ledger_writer_deployed"])

if __name__=="__main__":
    unittest.main()
