"""A8 SQLite transaction and no-blind-retry adversarial tests (no YouTube)."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

from scripts.branch3_a8_private_first_dryrun import CLIVOX, candidate_attempt_key, DryRunBlocked
from scripts.branch3_a8_attempt_ledger import (
    AttemptLedgerDenied, STATE_AMBIGUOUS, STATE_RESERVED,
    connect, initialize, inspect_no_retry, mark_ambiguous_no_retry,
    perform_production_upload, report_fixture, reserve_simulated_attempt
)

AT="2026-11-13T04:00:00Z"
REL="clivox_atomic_rehearsal_0000000001"


def values(release=REL, media="a"*64):
    return {
        "channel_id":CLIVOX,"release_id":release,
        "media_sha256":media,"metadata_sha256":"b"*64,
        "rights_evidence_sha256":"c"*64,"at_utc":AT
    }


def key_for(data):
    return candidate_attempt_key(
        channel_id=data["channel_id"],
        release_id=data["release_id"],
        media_sha256=data["media_sha256"],
        metadata_sha256=data["metadata_sha256"],
        rights_evidence_sha256=data["rights_evidence_sha256"]
    )


class A8AttemptLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db=Path(self.tmp.name)/"attempts.sqlite3"
        initialize(self.db)

    def reserve(self, **changes):
        data=values()
        data.update(changes)
        return reserve_simulated_attempt(self.db,**data)

    def test_atomic_insert_never_claims_live_authorization(self):
        report=self.reserve()
        self.assertTrue(report["local_reservation_inserted"])
        self.assertTrue(report["single_database_file_atomic_reservation_tested"])
        for field in (
            "durable_across_github_action_runs",
            "owner_signed_real_asset_verified",
            "real_creator_rights_verified",
            "youtube_upload_authorized",
            "youtube_schedule_authorized",
            "youtube_publish_authorized"
        ):
            self.assertFalse(report[field],field)
        self.assertEqual(report["actual_google_api_writes"],0)
        st=inspect_no_retry(self.db,attempt_key=key_for(values()))
        self.assertEqual(st["state"],STATE_RESERVED)
        self.assertFalse(st["automatic_retry_allowed"])
        self.assertEqual(
            connect(self.db).execute("SELECT COUNT(*) FROM attempts").fetchone()[0],1
        )

    def test_same_attempt_same_release_new_asset_and_same_media_all_denied(self):
        self.reserve()
        conflicts=(
            {},
            {"release_id":REL,"media_sha256":"d"*64},
            {"release_id":"clivox_atomic_rehearsal_0000000002"},
        )
        for change in conflicts:
            with self.subTest(change=change),self.assertRaisesRegex(
                    AttemptLedgerDenied,"DUPLICATE_RELEASE_MEDIA_OR_ATTEMPT"):
                self.reserve(**change)
        with connect(self.db) as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM attempts").fetchone()[0],1)

    def test_parallel_same_release_exactly_one_worker_commits(self):
        barrier=threading.Barrier(8)
        def race(_):
            barrier.wait()
            try:
                self.reserve()
                return "ONE_RESERVED"
            except AttemptLedgerDenied:
                return "CONFLICT_DENIED"
        with ThreadPoolExecutor(max_workers=8) as pool:
            outcomes=list(pool.map(race,range(8)))
        self.assertEqual(outcomes.count("ONE_RESERVED"),1)
        self.assertEqual(outcomes.count("CONFLICT_DENIED"),7)
        with connect(self.db) as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM attempts").fetchone()[0],1)

    def test_parallel_distinct_id_but_same_media_also_unique(self):
        barrier=threading.Barrier(5)
        def race(i):
            barrier.wait()
            try:
                self.reserve(release_id=f"clivox_atomic_rehearsal_{i:010d}")
                return "ONE"
            except AttemptLedgerDenied:
                return "BLOCKED"
        with ThreadPoolExecutor(max_workers=5) as pool:
            result=list(pool.map(race,range(5)))
        self.assertEqual(result.count("ONE"),1)
        self.assertEqual(result.count("BLOCKED"),4)

    def test_ambiguity_is_monotonic_and_no_second_transition(self):
        self.reserve()
        key=key_for(values())
        result=mark_ambiguous_no_retry(
            self.db,attempt_key=key,at_utc="2026-11-13T04:01:00Z"
        )
        self.assertEqual(result["state"],STATE_AMBIGUOUS)
        self.assertFalse(result["automatic_retry_allowed"])
        self.assertEqual(inspect_no_retry(self.db,attempt_key=key)["state"],
                         STATE_AMBIGUOUS)
        with self.assertRaises(AttemptLedgerDenied):
            mark_ambiguous_no_retry(
                self.db,attempt_key=key,at_utc="2026-11-13T04:02:00Z"
            )
        with self.assertRaises(AttemptLedgerDenied):
            self.reserve()

    def test_out_of_order_unknown_and_clock_rewind_fail_closed(self):
        self.reserve()
        key=key_for(values())
        with self.assertRaises(DryRunBlocked):
            mark_ambiguous_no_retry(
                self.db,attempt_key=key,at_utc="2026-11-13T03:00:00Z"
            )
        with self.assertRaises(AttemptLedgerDenied):
            mark_ambiguous_no_retry(
                self.db,attempt_key="e"*64,at_utc=AT
            )
        self.assertEqual(inspect_no_retry(self.db,attempt_key=key)["state"],
                         STATE_RESERVED)

    def test_failed_transition_rolls_back_entire_transaction(self):
        self.reserve()
        key=key_for(values())
        with self.assertRaises(DryRunBlocked):
            mark_ambiguous_no_retry(self.db,attempt_key=key,
                                    at_utc="2026-11-12T22:00:00Z")
        self.assertEqual(inspect_no_retry(self.db,attempt_key=key)["state"],
                         STATE_RESERVED)
        mark_ambiguous_no_retry(self.db,attempt_key=key,
                                at_utc="2026-11-13T05:00:00Z")
        self.assertEqual(inspect_no_retry(self.db,attempt_key=key)["state"],
                         STATE_AMBIGUOUS)

    def test_schema_protects_status_and_wrong_channel(self):
        self.reserve()
        with connect(self.db) as con:
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute("UPDATE attempts SET state='READY_TO_UPLOAD'")
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute(
                    "UPDATE attempts SET channel_id='UCCcL9Q_jqVq6LJmnYUSAFZA'"
                )
        self.assertEqual(inspect_no_retry(self.db,attempt_key=key_for(values()))["state"],
                         STATE_RESERVED)
        with self.assertRaises(DryRunBlocked):
            self.reserve(channel_id="UC"+"z"*22)

    def test_missing_schema_and_fake_public_db_location_rejected(self):
        raw=Path(self.tmp.name)/"bad.sqlite3"
        with self.assertRaises(AttemptLedgerDenied):
            reserve_simulated_attempt(raw,**values())
        with self.assertRaises(DryRunBlocked):
            initialize(Path("relative.sqlite3"))
        with self.assertRaises(DryRunBlocked):
            initialize(self.db.parent/"not-sqlite.json")
        link=Path(self.tmp.name)/"link.sqlite3"
        link.symlink_to(self.db)
        with self.assertRaises(DryRunBlocked):
            initialize(link)

    def test_bad_sha_release_and_time_are_not_reserved(self):
        for change in (
            {"media_sha256":"BAD"},
            {"metadata_sha256":"a"*63},
            {"release_id":"fake"},
            {"at_utc":"2026-11-13T04:00:00+00:00"},
            {"at_utc":"2026-11-13T04:00:00.111Z"},
        ):
            with self.subTest(change=change),self.assertRaises(DryRunBlocked):
                self.reserve(**change)
        with connect(self.db) as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM attempts").fetchone()[0],0)

    def test_replayed_db_schema_and_settings_tamper_denied(self):
        with connect(self.db) as con:
            con.execute("UPDATE settings SET value='ANOTHER_CHANNEL' WHERE name='channel_id'")
        with self.assertRaises(AttemptLedgerDenied):
            self.reserve()
        with self.assertRaises(AttemptLedgerDenied):
            initialize(self.db)

    def test_final_fixture_is_throwaway_and_production_entrypoint_denies(self):
        r=report_fixture()
        self.assertTrue(r["ephemeral_sqlite_atomic_reservation_tested"])
        self.assertFalse(r["cross_runner_durable_ledger_exists"])
        self.assertFalse(r["real_remote_inventory_reconciled"])
        self.assertEqual(r["real_creator_licenses"],0)
        self.assertEqual(r["actual_youtube_api_calls"],0)
        self.assertFalse(r["youtube_upload_authorized"])
        self.assertFalse(r["youtube_publish_authorized"])
        with self.assertRaises(AttemptLedgerDenied):
            perform_production_upload()


if __name__=="__main__":
    unittest.main()
