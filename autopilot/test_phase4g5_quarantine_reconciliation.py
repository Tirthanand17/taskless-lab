"""Phase 4G.5: a quarantined release never forgets remote-side-effect risk.

Everything runs against the preexisting offline SQLite simulator only.
YouTube remote status booleans in this suite are synthetic caller claims.
"""
from datetime import datetime, timedelta, timezone
import unittest

from autopilot.core import CHANNEL_ID
from autopilot.phase4_offline_ledger import OfflineLedger, ProtocolBlocked
from autopilot.phase4g_recovery_audit import inspect_offline_release_recovery

UTC=timezone.utc
SLOT="2026-10-22T05:30:00+00:00"
SHA="d"*64
REVIEW="e"*64
VIDEO="abc123def45"


def canonical_now_minus(seconds=500):
    return (datetime.now(UTC)-timedelta(seconds=seconds)).isoformat(
        timespec="seconds")


class ReconciliationDebtSurvivesQuarantineTests(unittest.TestCase):
    def setUp(self):
        self.l=OfflineLedger(offline_test_only=True)
        self.addCleanup(self.l.close)
        self.l.reserve(channel=CHANNEL_ID,episode="video01",
                       planned_utc=SLOT,media_sha256=SHA,
                       now_utc=canonical_now_minus())
        self.v,self.f=self.l.claim_db_clock_rehearsal(
            "video01",expected_version=0,owner="worker_a",ttl_seconds=240)

    def audit(self):
        return inspect_offline_release_recovery(self.l)

    def local_ready(self):
        for stage in ("research_verified","script_verified","media_qa_passed"):
            self.v=self.l.local_step_db_clock_rehearsal(
                "video01",target=stage,expected_version=self.v,
                owner="worker_a",fence=self.f,
                review_digest=REVIEW if stage=="media_qa_passed" else None)

    def upload(self):
        self.local_ready()
        self.v=self.l.begin_upload_intent_db_clock_rehearsal(
            "video01",expected_version=self.v,owner="worker_a",
            fence=self.f,media_sha256=SHA,intent_id="upload_intent_01")

    def private_claim(self):
        self.upload()
        # This call is test-only; authenticated=True does NOT prove Google.
        now=self.l.db.execute(
            "SELECT strftime('%Y-%m-%dT%H:%M:%S+00:00','now')"
        ).fetchone()[0]
        self.v=self.l.bind_private_readback(
            "video01",expected_version=self.v,owner="worker_a",
            fence=self.f,now_utc=now,
            remote_channel=CHANNEL_ID,youtube_id=VIDEO,
            processed=True,privacy="private",authenticated=True)

    def schedule(self):
        self.private_claim()
        self.v=self.l.begin_schedule_intent_db_clock_rehearsal(
            "video01",expected_version=self.v,owner="worker_a",fence=self.f)

    def quarantine(self):
        self.v=self.l.quarantine_db_clock_rehearsal(
            "video01",expected_version=self.v,owner="worker_a",fence=self.f,
            reason="Synthetic evidence insufficient for release")

    def test_no_remote_intent_quarantine_has_no_remote_debt(self):
        self.quarantine()
        r=self.audit()
        self.assertEqual(r["terminal_quarantined_count"],1)
        self.assertEqual(r["quarantined_after_remote_intent_count"],0)
        self.assertEqual(r["needs_real_provider_reconciliation_count"],0)
        self.assertFalse(r["public_publishing_authorized"])

    def test_upload_uncertain_quarantined_still_requires_reconciliation(self):
        self.upload()
        self.quarantine()
        r=self.audit()
        self.assertEqual(r["upload_uncertain_count"],0)
        self.assertEqual(r["terminal_quarantined_count"],1)
        self.assertEqual(r["upload_intent_count"],1)
        self.assertEqual(r["needs_real_provider_reconciliation_count"],1)
        self.assertEqual(
            r["upload_intents_missing_even_simulated_remote_readback_count"],1)
        self.assertEqual(r["quarantined_after_remote_intent_count"],1)
        self.assertEqual(r["quarantined_with_unresolved_remote_intent_count"],1)
        self.assertFalse(r["safe_to_blindly_retry_upload"])
        self.assertTrue(r["release_quarantine_does_not_clear_remote_intent_debt"])

    def test_schedule_uncertain_quarantined_still_requires_reconciliation(self):
        self.schedule()
        self.quarantine()
        r=self.audit()
        self.assertEqual(r["schedule_uncertain_count"],0)
        self.assertEqual(r["needs_real_provider_reconciliation_count"],1)
        self.assertEqual(
            r["schedule_intents_missing_even_simulated_remote_readback_count"],1)
        self.assertEqual(r["quarantined_with_unresolved_remote_intent_count"],1)
        self.assertFalse(r["safe_to_blindly_retry_schedule"])

    def test_private_claim_then_quarantine_still_requires_live_readback(self):
        self.private_claim()
        self.quarantine()
        r=self.audit()
        self.assertEqual(r["upload_intent_count"],1)
        self.assertEqual(r["quarantined_after_remote_intent_count"],1)
        self.assertEqual(r["quarantined_with_unresolved_remote_intent_count"],0)
        self.assertEqual(r["needs_real_provider_reconciliation_count"],1)
        self.assertFalse(r["real_authenticated_provider_readback_verified"])

    def test_schedule_claim_then_quarantine_still_needs_live_readback(self):
        self.schedule()
        now=self.l.db.execute(
            "SELECT strftime('%Y-%m-%dT%H:%M:%S+00:00','now')"
        ).fetchone()[0]
        self.v=self.l.bind_schedule_readback(
            "video01",expected_version=self.v,owner="worker_a",
            fence=self.f,now_utc=now,youtube_id=VIDEO,
            publish_at_utc=SLOT,authenticated=True,privacy="private")
        self.quarantine()
        r=self.audit()
        self.assertEqual(
            r["schedule_intents_missing_even_simulated_remote_readback_count"],0)
        self.assertEqual(r["quarantined_with_unresolved_remote_intent_count"],0)
        self.assertEqual(r["needs_real_provider_reconciliation_count"],1)
        self.assertFalse(r["real_authenticated_provider_readback_verified"])

    def test_quarantined_upload_cannot_reclaim_or_repeat(self):
        self.upload()
        self.quarantine()
        with self.assertRaises(ProtocolBlocked):
            self.l.claim_db_clock_rehearsal(
                "video01",expected_version=self.v,owner="worker_b")
        with self.assertRaises(ProtocolBlocked):
            self.l.begin_upload_intent_db_clock_rehearsal(
                "video01",expected_version=self.v,owner="worker_a",
                fence=self.f,media_sha256=SHA,intent_id="new_intent")
        self.assertEqual(self.audit()["needs_real_provider_reconciliation_count"],1)

    def test_client_clock_forgery_not_accepted_in_quarantine(self):
        with self.assertRaises(TypeError):
            self.l.quarantine_db_clock_rehearsal(
                "video01",expected_version=self.v,owner="worker_a",
                fence=self.f,reason="Missing independent content evidence",
                now_utc="2099-01-01T00:00:00+00:00")
        self.assertEqual(self.l.get("video01")["stage"],"planned")

    def test_wrong_version_worker_fence_and_reason_rejected(self):
        cases=[
            (self.v+1,"worker_a",self.f,"Missing content rights review"),
            (self.v,"worker_b",self.f,"Missing content rights review"),
            (self.v,"worker_a",self.f+1,"Missing content rights review"),
            (self.v,"worker_a",True,"Missing content rights review"),
            (self.v,"worker_a",self.f,"short"),
            (self.v,"worker_a",self.f,"contains\x00invalid"),
        ]
        for v,owner,fence,reason in cases:
            with self.subTest(case=(v,owner,fence)),self.assertRaises(ProtocolBlocked):
                self.l.quarantine_db_clock_rehearsal(
                    "video01",expected_version=v,owner=owner,
                    fence=fence,reason=reason)
        self.assertEqual(self.l.get("video01")["version"],self.v)

    def test_terminal_quarantine_twice_rejected_and_event_history_still_complete(self):
        self.upload()
        self.quarantine()
        with self.assertRaises(ProtocolBlocked):
            self.quarantine()
        self.assertEqual(self.audit()["event_count"],len(self.l.events("video01")))
        self.assertEqual(self.audit()["database_writes"],0)
        self.assertEqual(self.audit()["network_calls"],0)

    def test_no_identifiers_or_secret_values_appear_in_report(self):
        self.schedule()
        self.quarantine()
        r=self.audit()
        for raw in ("video01",VIDEO,SHA,REVIEW,"upload_intent_01","worker_a"):
            self.assertNotIn(raw,str(r))
        self.assertFalse(r["contains_episode_ids_or_video_ids"])
        self.assertFalse(r["youtube_upload_or_scheduling_authorized"])

if __name__=="__main__":
    unittest.main()
