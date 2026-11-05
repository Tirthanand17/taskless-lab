"""Two synthetic Cloudflare/YouTube snapshots: no network, no real identities."""
from copy import deepcopy
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.cloud_release_double_read import compare_private_release_read_rounds
from autopilot.test_cloud_phase4f_private_shape_contract import (
    row,youtube,VID,AT,SHA,CHANNEL,
)


def evaluate(*,first_rows=None,second_rows=None,
             first_youtube=None,second_youtube=None):
    return compare_private_release_read_rounds(
        initial_release_rows=(row("scheduled_verified"),)
            if first_rows is None else first_rows,
        initial_youtube_inventory=youtube()
            if first_youtube is None else first_youtube,
        repeat_release_rows=(row("scheduled_verified"),)
            if second_rows is None else second_rows,
        repeat_youtube_inventory=youtube()
            if second_youtube is None else second_youtube,
        expected_channel_id=CHANNEL,
    )


def other_row(stage="remote_private_verified"):
    raw=list(row("scheduled_verified"))
    raw[1]="lesson_short_hi"
    raw[2]="b"*64
    raw[3]=stage
    raw[4]="abc123def46" if stage not in (
        "planned","research_verified","script_verified",
        "media_qa_passed","upload_started",
    ) else None
    raw[5]=AT if stage in ("scheduled_verified","public_verified") else None
    return tuple(raw)


def added_inventory():
    inventory=youtube()
    inventory["videos"].append({
        "youtube_id":"abc123def46","privacy":"private",
        "processing":"succeeded","publish_at_utc":None,
        "uncertain_metadata":False,
    })
    inventory["video_count"]=2
    return inventory


class TwoRoundReadOnlyDriftTests(unittest.TestCase):
    def test_identical_passing_rounds_do_not_claim_atomic_snapshot(self):
        result=evaluate()
        self.assertFalse(result["any_snapshot_drift_detected"])
        self.assertEqual(result["double_read_sample_count"],2)
        for flag in (
            "observed_source_is_cryptographically_authenticated",
            "two_rounds_prove_consistent_database_snapshot",
            "two_rounds_prove_atomic_cross_provider_snapshot",
            "durable_cloud_lease_and_writer_verified",
            "backup_restore_verified","any_ambiguous_upload_safe_to_retry",
            "migration_authorized","youtube_upload_authorized",
            "scheduling_or_publishing_authorized",
        ):
            self.assertFalse(result[flag])
        self.assertIn("D1_YOUTUBE_CROSS_PROVIDER_ATOMICITY_UNPROVEN",
                      result["blocking_reason_codes"])
        self.assertEqual(result["network_calls"],0)
        self.assertEqual(result["database_writes"],0)
        for secret in (CHANNEL,VID,SHA,AT,"lesson_short_en"):
            self.assertNotIn(secret,str(result))

    def test_second_d1_stage_update_detected_even_if_remote_unchanged(self):
        out=evaluate(second_rows=(row("public_verified"),))
        self.assertTrue(out["any_snapshot_drift_detected"])
        self.assertEqual(out["d1_release_row_changed_count"],1)
        self.assertEqual(out["youtube_video_changed_count"],0)
        self.assertIn("D1_RELEASE_ROWS_CHANGED_BETWEEN_READ_ROUNDS",
                      out["blocking_reason_codes"])
        self.assertFalse(out["migration_authorized"])

    def test_second_d1_media_digest_change_detected_without_leaking_sha(self):
        altered=list(row("scheduled_verified"))
        altered[2]="f"*64
        out=evaluate(second_rows=(tuple(altered),))
        self.assertEqual(out["d1_release_row_changed_count"],1)
        self.assertNotIn("f"*64,str(out))
        self.assertFalse(out["youtube_upload_authorized"])

    def test_second_youtube_privacy_public_detected(self):
        response=youtube()
        response["videos"][0]["privacy"]="public"
        # Private API uncertainty must reflect schedule+privacy.
        response["videos"][0]["uncertain_metadata"]=True
        response["processing_or_schedule_uncertain_count"]=1
        out=evaluate(second_youtube=response)
        self.assertEqual(out["youtube_video_changed_count"],1)
        self.assertTrue(out["release_reconciliation_quarantine_seen"])
        self.assertIn("YOUTUBE_OWNER_INVENTORY_CHANGED_BETWEEN_READ_ROUNDS",
                      out["blocking_reason_codes"])

    def test_changed_remote_schedule_detected(self):
        response=youtube()
        response["videos"][0]["publish_at_utc"]="2026-10-22T03:00:00+00:00"
        out=evaluate(second_youtube=response)
        self.assertEqual(out["youtube_video_changed_count"],1)
        self.assertTrue(out["release_reconciliation_quarantine_seen"])

    def test_release_appeared_between_reads(self):
        out=evaluate(second_rows=(
            row("scheduled_verified"),other_row()
        ))
        self.assertEqual(out["d1_release_row_added_count"],1)
        self.assertEqual(out["d1_release_row_removed_count"],0)
        self.assertTrue(out["any_snapshot_drift_detected"])

    def test_release_disappeared_between_reads(self):
        out=evaluate(first_rows=(
            row("scheduled_verified"),other_row(),
        ))
        self.assertEqual(out["d1_release_row_removed_count"],1)
        self.assertTrue(out["any_snapshot_drift_detected"])

    def test_owner_video_appeared_or_disappeared_between_reads(self):
        more=added_inventory()
        appeared=evaluate(second_youtube=more)
        self.assertEqual(appeared["youtube_video_added_count"],1)
        self.assertTrue(appeared["unmatched_owner_upload_seen"])
        removed=evaluate(first_youtube=more)
        self.assertEqual(removed["youtube_video_removed_count"],1)
        self.assertTrue(removed["unmatched_owner_upload_seen"])

    def test_read_order_of_owner_videos_does_not_cause_false_drift(self):
        first=added_inventory()
        second=deepcopy(first)
        second["videos"].reverse()
        out=evaluate(first_youtube=first,second_youtube=second)
        self.assertFalse(out["any_snapshot_drift_detected"])
        self.assertTrue(out["unmatched_owner_upload_seen"])

    def test_ambiguous_upload_started_in_both_rounds_stays_quarantined(self):
        out=evaluate(first_rows=(row("upload_started"),),
                     second_rows=(row("upload_started"),))
        self.assertFalse(out["any_snapshot_drift_detected"])
        self.assertTrue(out["release_reconciliation_quarantine_seen"])
        self.assertIn("AMBIGUOUS_UPLOAD_PRESENT_NO_AUTO_RETRY",
                      out["blocking_reason_codes"])
        self.assertFalse(out["any_ambiguous_upload_safe_to_retry"])

    def test_empty_but_matching_snapshots_not_accepted_as_history_proof(self):
        blank=youtube()
        blank["videos"]=[]
        blank["video_count"]=0
        out=evaluate(first_rows=(),second_rows=(),
                     first_youtube=blank,second_youtube=blank)
        self.assertIn("EMPTY_READ_ROUND_REQUIRES_HISTORY_REVIEW",
                      out["blocking_reason_codes"])
        self.assertFalse(out["scheduling_or_publishing_authorized"])

    def test_invalid_second_channel_owner_or_forged_permission_rejected(self):
        modified=youtube()
        modified["channel_id"]="UC"+"y"*22
        with self.assertRaises(WorkflowError):
            evaluate(second_youtube=modified)
        modified=youtube()
        modified["private_upload_authorized"]=True
        with self.assertRaises(WorkflowError):
            evaluate(second_youtube=modified)

    def test_corrupt_duplicate_or_inconsistent_read_round_refused(self):
        with self.assertRaises(WorkflowError):
            evaluate(second_rows=(
                row("scheduled_verified"),row("scheduled_verified"),
            ))
        forged=youtube()
        forged["processing_or_schedule_uncertain_count"]=1
        with self.assertRaises(WorkflowError):
            evaluate(second_youtube=forged)


if __name__=="__main__":
    unittest.main()
