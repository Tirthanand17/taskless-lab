"""Phase4F public pure reconciliation contract: synthetic private-shaped inputs.

The private Phase4F glue calls reconcile_existing_private_shapes with D1's
legacy 6-column tuples and the owner read-only report. No real private
data, API tokens, connection, D1 release rows, credentials or upload here.
"""
from copy import deepcopy
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.cloud_release_snapshot_reconcile import (
    reconcile_existing_private_shapes,
)

CHANNEL="UC"+"x"*22
VID="aBC123deF45"
AT="2026-10-21T03:00:00+00:00"
SHA="a"*64
STAGES=(
    "planned","research_verified","script_verified","media_qa_passed",
    "upload_started","remote_private_verified","scheduled_verified",
    "public_verified",
)


def row(stage):
    idx=STAGES.index(stage)
    return (
        "2026-10-20","lesson_short_en",
        SHA if idx>=3 else None,stage,
        VID if idx>=5 else None,
        AT if idx>=6 else None,
    )


def youtube(*,privacy="private",processing="succeeded",
            time=AT,uncertain=False):
    videos=[{
        "youtube_id":VID,"privacy":privacy,
        "processing":processing,"publish_at_utc":time,
        "uncertain_metadata":uncertain,
    }]
    return {
        "status":"PRIVATE_READ_ONLY_RESPONSE_NOT_RELEASE_AUTHORITY",
        "channel_id":CHANNEL,"playlist_page_count":1,
        "video_count":1,"videos":videos,
        "playlist_and_details_matched":True,
        "processing_or_schedule_uncertain_count":int(uncertain),
        "live_authentication_independently_attested":False,
        "d1_release_rows_reconciled":False,
        "owner_publish_consent_verified":False,
        "migration_authorized":False,
        "private_upload_authorized":False,
        "schedule_or_public_publishing_authorized":False,
        "raw_oauth_tokens_in_output":False,
        "storage_writes":0,
    }


def evaluate(stage="scheduled_verified",youtube_result=None):
    return reconcile_existing_private_shapes(
        existing_ledger_rows=(row(stage),),
        private_youtube_inventory=youtube()
        if youtube_result is None else youtube_result,
        expected_channel_id=CHANNEL,
        local_ledger_snapshot_complete=False,
    )


class ExistingPrivateShapeIntegrationTests(unittest.TestCase):
    def test_matching_private_video_is_only_untrusted_shape_match(self):
        report=evaluate()
        self.assertEqual(report["matched_remote_video_id_count"],1)
        self.assertEqual(report["quarantined_local_release_count"],0)
        self.assertEqual(report["stage_counts"]["scheduled_verified"],1)
        self.assertIn("INCOMPLETE_LOCAL_LEDGER_SNAPSHOT",report["blocking_reasons"])
        self.assertIn("PROVIDER_AND_LEDGER_SNAPSHOT_ORIGIN_UNAUTHENTICATED",
                      report["blocking_reasons"])
        self.assertIn("NO_CROSS_PROVIDER_ATOMICITY_OR_SIGNED_SNAPSHOT_PROOF",
                      report["blocking_reasons"])
        self.assertFalse(report["safe_to_retry_any_ambiguous_upload"])
        self.assertFalse(report["release_ledger_migration_authorized"])
        self.assertFalse(report["publish_or_upload_authorized"])
        self.assertEqual(report["external_api_requests"],0)
        self.assertEqual(report["cloud_database_writes"],0)
        for protected in (VID,SHA,CHANNEL,AT,"lesson_short_en"):
            self.assertNotIn(protected,str(report))

    def test_private_unknown_processing_reports_quarantine(self):
        report=evaluate(youtube_result=youtube(
            processing="unknown",uncertain=True,
        ))
        self.assertEqual(report["quarantined_local_release_count"],1)
        self.assertIn("REMOTE_PROCESSING_NOT_CONFIRMED_SUCCEEDED",
                      report["blocking_reasons"])
        self.assertIn("UNCERTAIN_REMOTE_VIDEO_METADATA",
                      report["blocking_reasons"])
        self.assertFalse(report["publish_or_upload_authorized"])

    def test_lost_ack_upload_started_stays_ambiguous_with_empty_owner_list(self):
        inventory=youtube()
        inventory["videos"]=[]
        inventory["video_count"]=0
        inventory["processing_or_schedule_uncertain_count"]=0
        report=evaluate("upload_started",inventory)
        self.assertIn("UPLOAD_STARTED_AMBIGUOUS_NEEDS_MANUAL_RECOVERY",
                      report["blocking_reasons"])
        self.assertEqual(report["quarantined_local_release_count"],1)
        self.assertFalse(report["safe_to_retry_any_ambiguous_upload"])

    def test_previous_private_stage_row_order_not_dataclass_order(self):
        report=evaluate("remote_private_verified",youtube(
            privacy="private",time=None
        ))
        self.assertEqual(report["matched_remote_video_id_count"],1)
        self.assertEqual(report["stage_counts"]["remote_private_verified"],1)
        self.assertFalse(report["d1_release_rows_live_observed"])

    def test_schema_expected_utc_schedule_drift_quarantined(self):
        report=evaluate(youtube_result=youtube(
            time="2026-10-21T03:01:00+00:00"
        ))
        self.assertIn("REMOTE_SCHEDULE_TIMESTAMP_MISMATCH",
                      report["blocking_reasons"])
        self.assertEqual(report["quarantined_local_release_count"],1)

    def test_counterfeit_production_permission_fails_before_report(self):
        for key in (
            "live_authentication_independently_attested",
            "d1_release_rows_reconciled","owner_publish_consent_verified",
            "private_upload_authorized",
            "schedule_or_public_publishing_authorized",
        ):
            report=youtube()
            report[key]=True
            with self.subTest(key=key),self.assertRaises(WorkflowError):
                evaluate(youtube_result=report)

    def test_unknown_private_field_or_forged_uncertainty_rejected(self):
        report=youtube()
        report["oauth_refresh_token"]="NEVER_LOG"
        with self.assertRaises(WorkflowError) as caught:
            evaluate(youtube_result=report)
        self.assertNotIn("NEVER_LOG",str(caught.exception))
        report=youtube()
        report["processing_or_schedule_uncertain_count"]=1
        with self.assertRaises(WorkflowError):
            evaluate(youtube_result=report)


if __name__=="__main__":
    unittest.main()
