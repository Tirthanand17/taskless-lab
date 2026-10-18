"""Actual in-memory SQLite reversible migration rehearsal: NO real cloud data."""
from dataclasses import replace
from hashlib import sha256
import unittest

from autopilot.phase4f_synthetic_rehearsal import (
    FIXTURE_MARKER, SyntheticLegacyRelease, rehearse_synthetic_migration,
)
from autopilot.phase4_offline_ledger import ProtocolBlocked

def fixture(episode:str, day:str, slot:str, marker:int)->SyntheticLegacyRelease:
    return SyntheticLegacyRelease(
        fixture_marker=FIXTURE_MARKER,
        episode_id=episode,
        release_date_ist=day,
        planned_utc=slot,
        media_sha256=sha256(f"EXPLICIT SYNTHETIC TEST MEDIA {marker}".encode()).hexdigest(),
    )
ONE=fixture("tutorial_a","2026-10-20","2026-10-20T04:30:00+00:00",1)
TWO=fixture("tutorial_b","2026-10-20","2026-10-20T05:00:00+00:00",2)
THREE=fixture("tutorial_c","2026-10-21","2026-10-21T04:30:00+00:00",3)

class OfflineReversibleMigrationTests(unittest.TestCase):
    def assert_safe(self,result):
        self.assertFalse(result["production_migration_authorized"])
        self.assertFalse(result["private_upload_authorized"])
        self.assertFalse(result["public_publishing_authorized"])
        self.assertFalse(result["real_d1_schema_authenticated"])
        self.assertFalse(result["legacy_video_ids_reconciled"])
        self.assertEqual(result["canonical_target_rows_after_rollback"],0)
        self.assertEqual(result["persistent_files_written"],0)
        self.assertEqual(result["production_database_writes"],0)
        self.assertEqual(result["provider_connections"],0)
        self.assertEqual(result["generated_production_sql"],[])

    def test_real_in_memory_sqlite_insert_and_rollback(self):
        r=rehearse_synthetic_migration((ONE,TWO,THREE))
        self.assertEqual(r["status"],"SYNTHETIC_SAVEPOINT_ROLLBACK_REHEARSED")
        self.assertEqual(r["staged_rows_before_rollback"],3)
        self.assertTrue(r["synthetic_source_rows_intact"])
        self.assertTrue(r["rollback_executed_and_verified"])
        self.assert_safe(r)

    def test_crash_after_two_staged_rows_rolls_back_all(self):
        r=rehearse_synthetic_migration((ONE,TWO,THREE),
                                      abort_after_canonical_inserts=2)
        self.assertEqual(r["status"],"SYNTHETIC_FAILURE_INJECTION_ROLLED_BACK")
        self.assertEqual(r["staged_rows_before_rollback"],2)
        self.assertTrue(r["synthetic_source_rows_intact"])
        self.assert_safe(r)

    def test_same_episode_different_legacy_dates_cannot_become_two_releases(self):
        later=replace(THREE,episode_id=ONE.episode_id)
        r=rehearse_synthetic_migration((ONE,later))
        self.assertEqual(r["status"],"SYNTHETIC_TARGET_IDENTITY_CONFLICT_BLOCKED")
        self.assertEqual(r["staged_rows_before_rollback"],1)
        self.assertTrue(r["synthetic_source_rows_intact"])
        self.assert_safe(r)

    def test_different_episode_same_utc_slot_is_collision(self):
        duplicate_slot=replace(TWO,planned_utc=ONE.planned_utc)
        r=rehearse_synthetic_migration((ONE,duplicate_slot))
        self.assertEqual(r["status"],"SYNTHETIC_TARGET_IDENTITY_CONFLICT_BLOCKED")
        self.assert_safe(r)

    def test_same_media_hash_reused_across_episodes_blocks(self):
        reused=replace(TWO,media_sha256=ONE.media_sha256)
        r=rehearse_synthetic_migration((ONE,reused))
        self.assertEqual(r["status"],"SYNTHETIC_TARGET_IDENTITY_CONFLICT_BLOCKED")
        self.assert_safe(r)

    def test_legacy_same_day_episode_collision_in_source_is_blocked(self):
        duplicate=replace(ONE,planned_utc="2026-10-20T05:10:00+00:00")
        r=rehearse_synthetic_migration((ONE,duplicate))
        self.assertEqual(r["status"],"SYNTHETIC_SOURCE_IDENTITY_CONFLICT_BLOCKED")
        self.assertFalse(r["rollback_executed_and_verified"])
        self.assert_safe(r)

    def test_no_guessing_ist_date_from_utc_timestamp(self):
        wrong=replace(ONE,release_date_ist="2026-10-21")
        with self.assertRaisesRegex(ProtocolBlocked,"diverge"):
            rehearse_synthetic_migration([wrong])

    def test_no_naive_or_wrong_offset_time_as_utc_slot(self):
        for time in (
            "2026-10-20T10:00:00+05:30",
            "2026-10-20T04:30:00",
            "2026-10-20T04:30:00Z",
        ):
            with self.subTest(time=time),self.assertRaises(ProtocolBlocked):
                rehearse_synthetic_migration([replace(ONE,planned_utc=time)])

    def test_real_or_uncertain_remote_video_state_never_staged(self):
        for change in (
            {"legacy_stage":"upload_started"},
            {"legacy_stage":"scheduled_verified"},
            {"legacy_stage":"media_qa_passed"},
            {"youtube_id":"abc123def45"},
        ):
            with self.subTest(change=change),self.assertRaises(ProtocolBlocked):
                rehearse_synthetic_migration([replace(ONE,**change)])

    def test_fixture_marker_and_malformed_sha_required(self):
        for change in (
            {"fixture_marker":"LIVE_D1_ROW"},
            {"media_sha256":"0"},
            {"episode_id":"bad/slash"},
            {"release_date_ist":"2026-02-30"},
        ):
            with self.subTest(change=change),self.assertRaises(ProtocolBlocked):
                rehearse_synthetic_migration([replace(ONE,**change)])

    def test_empty_and_oversized_fixture_refused(self):
        with self.assertRaises(ProtocolBlocked):
            rehearse_synthetic_migration([])
        with self.assertRaises(ProtocolBlocked):
            rehearse_synthetic_migration([ONE]*65)

    def test_fault_injection_must_be_bounded_integer(self):
        for v in (0,4,-1,True):
            with self.subTest(v=v),self.assertRaises(ProtocolBlocked):
                rehearse_synthetic_migration([ONE,TWO,THREE],abort_after_canonical_inserts=v)

    def test_ordered_fixture_is_deterministic_and_no_files_created(self):
        a=rehearse_synthetic_migration([ONE,TWO])
        b=rehearse_synthetic_migration([ONE,TWO])
        self.assertEqual(a,b)
        self.assert_safe(a)

if __name__=="__main__":
    unittest.main()
