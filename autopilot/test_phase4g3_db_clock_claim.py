"""Actual SQLite transaction tests for Phase 4G.3 database-clock lease claims.

This is only the pre-existing OFFLINE reference simulator. No real D1 binding,
Google API, cloud writer, uploading, account authorization or billing.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from autopilot.core import CHANNEL_ID
from autopilot.phase4_offline_ledger import OfflineLedger, ProtocolBlocked
from autopilot.phase4g_recovery_audit import inspect_offline_release_recovery

SLOT="2026-10-22T05:30:00+00:00"
MEDIA="a"*64
UTC=timezone.utc


def iso_ago(seconds: int) -> str:
    return (datetime.now(UTC)-timedelta(seconds=seconds)).isoformat(
        timespec="seconds")


class DatabaseClockLeaseRehearsalTests(unittest.TestCase):
    def setUp(self):
        self.ledger=OfflineLedger(":memory:",offline_test_only=True)
        self.addCleanup(self.ledger.close)
        self.ledger.reserve(channel=CHANNEL_ID,episode="example_01",
                            planned_utc=SLOT,media_sha256=MEDIA,
                            now_utc=iso_ago(400))

    def db_time(self):
        return datetime.fromisoformat(self.ledger.db.execute(
            "SELECT strftime('%Y-%m-%dT%H:%M:%S+00:00','now')"
        ).fetchone()[0])

    def test_time_from_same_database_not_caller(self):
        before=self.db_time()
        version,fence=self.ledger.claim_db_clock_rehearsal(
            "example_01",expected_version=0,owner="worker_one",ttl_seconds=120)
        after=self.db_time()
        row=self.ledger.get("example_01")
        claimed=datetime.fromisoformat(self.ledger.events("example_01")[-1]["at_utc"])
        self.assertEqual((version,fence),(1,1))
        self.assertLessEqual(before,claimed)
        self.assertLessEqual(claimed,after)
        self.assertEqual(row["version"],1)
        self.assertEqual(row["fence"],1)
        self.assertEqual(row["stage"],"planned")
        self.assertEqual(datetime.fromisoformat(row["lease_until"])-claimed,
                         timedelta(seconds=120))
        audit=inspect_offline_release_recovery(self.ledger)
        self.assertEqual(audit["release_count"],1)
        self.assertEqual(audit["lease_fences_seen"],1)
        self.assertFalse(audit["real_server_clock_enforced"])
        self.assertFalse(audit["public_publishing_authorized"])
        self.assertEqual(audit["network_calls"],0)

    def test_untrusted_caller_clock_parameter_is_not_accepted(self):
        with self.assertRaises(TypeError):
            self.ledger.claim_db_clock_rehearsal(
                "example_01",expected_version=0,owner="worker_one",
                now_utc="2099-01-01T00:00:00+00:00")
        self.assertEqual(self.ledger.get("example_01")["version"],0)

    def test_active_db_clock_lease_rejects_same_worker_and_new_worker(self):
        self.ledger.claim_db_clock_rehearsal(
            "example_01",expected_version=0,owner="worker_one")
        for name in ("worker_one","worker_two"):
            with self.subTest(name=name),self.assertRaises(ProtocolBlocked):
                self.ledger.claim_db_clock_rehearsal(
                    "example_01",expected_version=1,owner=name)
        self.assertEqual(len(self.ledger.events("example_01")),2)

    def test_reclaim_historical_expired_fixture_uses_db_current_time(self):
        # The existing legacy simulator accepts timestamps from test callers.
        # This fixture claims an already-expired lease; it is NOT remotely
        # trusted, and the new method must ignore the fixture's clock.
        fixture_time=iso_ago(300)
        self.ledger.claim("example_01",expected_version=0,
                          owner="stale_worker",now_utc=fixture_time,
                          ttl_seconds=30)
        v,f=self.ledger.claim_db_clock_rehearsal(
            "example_01",expected_version=1,owner="replacement_worker")
        self.assertEqual((v,f),(2,2))
        self.assertEqual(self.ledger.get("example_01")["lease_owner"],
                         "replacement_worker")
        report=inspect_offline_release_recovery(self.ledger)
        self.assertEqual(report["lease_fences_seen"],2)
        self.assertFalse(report["safe_to_blindly_retry_upload"])

    def test_new_claim_cannot_prove_it_is_safe_to_retry_upload(self):
        self.ledger.claim_db_clock_rehearsal(
            "example_01",expected_version=0,owner="worker_one")
        result=inspect_offline_release_recovery(self.ledger)
        self.assertFalse(result["youtube_upload_or_scheduling_authorized"])
        self.assertFalse(result["production_cloud_ledger_writer_deployed"])
        self.assertFalse(result["real_authenticated_provider_readback_verified"])

    def test_stale_version_and_invalid_ids_ttl_fail(self):
        cases=[
            {"expected_version":1,"owner":"worker_one"},
            {"expected_version":0,"owner":"bad/slash"},
            {"expected_version":0,"owner":"worker_one","ttl_seconds":True},
            {"expected_version":0,"owner":"worker_one","ttl_seconds":301},
            {"expected_version":-1,"owner":"worker_one"},
        ]
        for case in cases:
            with self.subTest(case=case),self.assertRaises(ProtocolBlocked):
                self.ledger.claim_db_clock_rehearsal("example_01",**case)
        self.assertEqual(self.ledger.get("example_01")["version"],0)

    def test_terminal_quarantined_offline_release_stays_unclaimable(self):
        v,f=self.ledger.claim_db_clock_rehearsal(
            "example_01",expected_version=0,owner="worker_one")
        now=self.db_time().isoformat(timespec="seconds")
        v=self.ledger.quarantine("example_01",expected_version=v,
                owner="worker_one",fence=f,now_utc=now,
                reason="Offline synthetic review cancelled production")
        with self.assertRaises(ProtocolBlocked):
            self.ledger.claim_db_clock_rehearsal(
                "example_01",expected_version=v,owner="other_worker")
        self.assertEqual(self.ledger.get("example_01")["stage"],"quarantined")

    def test_two_connections_only_one_lease_wins(self):
        with TemporaryDirectory() as temp:
            path=Path(temp)/"only_test.sqlite"
            first=OfflineLedger(path,offline_test_only=True)
            self.addCleanup(first.close)
            first.reserve(channel=CHANNEL_ID,episode="only_one",
                          planned_utc=SLOT,media_sha256=MEDIA,
                          now_utc=iso_ago(400))
            second=OfflineLedger(path,offline_test_only=True)
            self.addCleanup(second.close)
            first.claim_db_clock_rehearsal(
                "only_one",expected_version=0,owner="runner_a")
            with self.assertRaises(ProtocolBlocked):
                second.claim_db_clock_rehearsal(
                    "only_one",expected_version=0,owner="runner_b")
            self.assertEqual(first.get("only_one")["version"],1)
            self.assertEqual(len(first.events("only_one")),2)

if __name__=="__main__":
    unittest.main()
