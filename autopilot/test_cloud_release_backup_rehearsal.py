"""Synthetic SQLite in-memory backup/restore: no filesystem or live D1."""
from unittest.mock import patch
import sqlite3
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.cloud_release_backup_rehearsal import (
    rehearse_in_memory_release_restore,check_shadow_restore_integrity,
)
from autopilot.test_cloud_phase4f_private_shape_contract import row,AT,SHA

VIDEO_B="abc123def46"


def another(stage="remote_private_verified"):
    sample=list(row("scheduled_verified"))
    sample[1]="lesson_short_hi"
    sample[2]="b"*64
    sample[3]=stage
    sample[4]=VIDEO_B if stage not in (
        "planned","research_verified","script_verified",
        "media_qa_passed","upload_started",
    ) else None
    sample[5]=AT if stage in ("scheduled_verified","public_verified") else None
    return tuple(sample)


class OfflineReleaseBackupRecoveryTests(unittest.TestCase):
    def test_real_in_memory_sqlite_backup_and_restore_exact_row_parity(self):
        dataset=(another(),row("scheduled_verified"))
        result=rehearse_in_memory_release_restore(
            existing_private_ledger_rows=dataset
        )
        self.assertEqual(result["shadow_release_row_count"],2)
        self.assertEqual(result["shadow_restored_row_count"],2)
        self.assertTrue(result["entire_source_record_set_equal_in_shadow"])
        self.assertTrue(result["shadow_backup_restore_rehearsed"])
        self.assertFalse(result["production_database_backup_observed"])
        self.assertFalse(result["production_restore_executed_or_verified"])
        self.assertFalse(result["event_history_recovery_verified"])
        self.assertFalse(result["single_writer_fence_verified"])
        self.assertFalse(result["ambiguous_upload_retry_authorized"])
        self.assertFalse(result["upload_authorized"])
        self.assertFalse(result["publishing_authorized"])
        self.assertEqual(result["cloud_database_writes"],0)
        self.assertEqual(result["external_api_requests"],0)
        for secret in (AT,SHA,"lesson_short_en","lesson_short_hi"):
            self.assertNotIn(secret,str(result))

    def test_unordered_source_rows_canonicalized_not_falsely_changed(self):
        data=(another(),row("scheduled_verified"))
        result=check_shadow_restore_integrity(data,tuple(reversed(data)))
        self.assertTrue(result["entire_source_record_set_equal_in_shadow"])
        self.assertEqual(result["shadow_release_row_count"],2)

    def test_upload_started_stays_uncertain_even_after_perfect_shadow_restore(self):
        result=rehearse_in_memory_release_restore(
            existing_private_ledger_rows=(row("upload_started"),)
        )
        self.assertEqual(result["ambiguous_upload_started_count"],1)
        self.assertIn("AMBIGUOUS_UPLOAD_STARTED_MUST_NOT_AUTO_RETRY",
                      result["blockers"])
        self.assertFalse(result["ambiguous_upload_retry_authorized"])

    def test_empty_history_is_a_valid_shadow_but_no_cloud_recovery_proof(self):
        result=rehearse_in_memory_release_restore(
            existing_private_ledger_rows=()
        )
        self.assertEqual(result["shadow_restored_row_count"],0)
        self.assertIn("EMPTY_RELEASE_HISTORY_CANNOT_PROVE_RECOVERY",
                      result["blockers"])
        self.assertFalse(result["migration_authorized"])

    def test_missing_row_or_new_row_during_restore_fails_closed(self):
        data=(row("scheduled_verified"),another())
        for fake in ((data[0],),(data[0],data[1],data[1])):
            with self.subTest(count=len(fake)),self.assertRaises(WorkflowError):
                check_shadow_restore_integrity(data,fake)

    def test_restored_stage_media_or_youtube_identity_drift_rejected(self):
        baseline=row("scheduled_verified")
        for index,value in ((2,"e"*64),(3,"public_verified"),
                            (4,"aaaaaaaaaaa"),(5,"2026-10-21T03:01:00+00:00")):
            restored=list(baseline)
            restored[index]=value
            with self.subTest(index=index),self.assertRaises(WorkflowError):
                check_shadow_restore_integrity((baseline,),(tuple(restored),))

    def test_original_or_restored_record_duplicate_ownership_denied(self):
        baseline=row("scheduled_verified")
        for rows in (
            (baseline,baseline),
            (baseline,tuple(list(baseline[:1])+["lesson_short_hi"]+
                            list(baseline[2:]))),
        ):
            with self.subTest(count=len(rows)),self.assertRaises(WorkflowError):
                rehearse_in_memory_release_restore(
                    existing_private_ledger_rows=rows
                )

    def test_other_episode_reuses_source_media_but_changes_video_denied(self):
        altered=list(another())
        altered[2]=SHA
        with self.assertRaises(WorkflowError):
            rehearse_in_memory_release_restore(
                existing_private_ledger_rows=(row("scheduled_verified"),
                                               tuple(altered))
            )

    def test_invalid_timing_date_and_stage_must_not_rehearse(self):
        for index,val in ((0,"2026-02-30"),(1,"../../bad"),
                          (2,"garbage"),(3,"published"),
                          (4,"bad"),(5,"2026-10-21T08:30:00+05:30")):
            attempt=list(row("scheduled_verified"))
            attempt[index]=val
            with self.subTest(index=index),self.assertRaises(WorkflowError):
                rehearse_in_memory_release_restore(
                    existing_private_ledger_rows=(tuple(attempt),)
                )

    def test_non_tuple_unbounded_or_secret_bearing_row_denied(self):
        base=row("scheduled_verified")
        for rows in ([base],(list(base),),(base+("TOKEN",),),
                     (base,)*501):
            with self.subTest(length=len(rows)),self.assertRaises(WorkflowError):
                rehearse_in_memory_release_restore(
                    existing_private_ledger_rows=rows
                )

    def test_source_backup_failure_propagates_sanitized_no_permission(self):
        # Type/shape faults fail before opening any external provider; no
        # injected cloud resources can be opened by the rehearsal module.
        malformed=(row("scheduled_verified"),object())
        with self.assertRaises(WorkflowError) as ctx:
            rehearse_in_memory_release_restore(
                existing_private_ledger_rows=malformed
            )
        self.assertNotIn("abc123",str(ctx.exception))

    def test_shadow_restore_has_no_external_sqlite_file_paths(self):
        # Assert the actual constructor calls, rather than falsely assume
        # that an in-memory rehearsal proves Cloudflare backups.
        original=sqlite3.connect
        opened=[]
        def connect(path,*args,**kwargs):
            opened.append(path)
            return original(path,*args,**kwargs)
        with patch("autopilot.cloud_release_backup_rehearsal.sqlite3.connect",
                   side_effect=connect):
            result=rehearse_in_memory_release_restore(
                existing_private_ledger_rows=(row("scheduled_verified"),)
            )
        self.assertEqual(opened,[":memory:",":memory:"])
        self.assertEqual(result["cloud_database_writes"],0)


if __name__=="__main__":
    unittest.main()
