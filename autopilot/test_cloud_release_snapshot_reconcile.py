"""Phase 4 release-state dry run: fabricated local and remote records only.

No private data, credentials, YouTube SDK, D1 API, network or publishing.
"""
from dataclasses import replace
import json
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.cloud_release_snapshot_reconcile import (
    ReleaseSnapshot,OwnerVideoSnapshot,reconcile_release_snapshots,
    reconcile_existing_private_shapes,
)

CHANNEL="UC"+"x"*22
OTHER_CHANNEL="UC"+"y"*22
VIDEO_A="ABC123def45"
VIDEO_B="ABC123def46"
SHA_A="a"*64
SHA_B="b"*64
SCHEDULE="2026-10-20T10:00:00+00:00"


def release(stage="scheduled_verified",*,vid=VIDEO_A,sha=SHA_A,
            episode="tutorial_short_en",schedule=SCHEDULE):
    early=("planned","research_verified","script_verified")
    return ReleaseSnapshot(
        "2026-10-20",episode,stage,None if stage in early else sha,
        None if stage in (*early,"media_qa_passed","upload_started") else vid,
        schedule if stage in ("scheduled_verified","public_verified") else None,
    )


def remote(vid=VIDEO_A,privacy="private",processing="succeeded",
           schedule=SCHEDULE,uncertain=False):
    return OwnerVideoSnapshot(vid,privacy,processing,schedule,uncertain)


def run(rows=None, owner=None, **kwargs):
    return reconcile_release_snapshots(
        (release(),) if rows is None else rows,
        (remote(),) if owner is None else owner,
        expected_channel_id=CHANNEL,observed_channel_id=CHANNEL,
        remote_pagination_complete=kwargs.get("complete",True),
        local_ledger_snapshot_complete=kwargs.get("local_complete",True),
    )


class ReleaseReconciliationDryRunTests(unittest.TestCase):
    def test_matching_scheduled_video_still_has_no_provider_or_publish_authority(self):
        result=run()
        self.assertEqual(result["matched_remote_video_id_count"],1)
        self.assertEqual(result["quarantined_local_release_count"],0)
        self.assertIn("PROVIDER_AND_LEDGER_SNAPSHOT_ORIGIN_UNAUTHENTICATED",
                      result["blocking_reasons"])
        self.assertFalse(result["safe_to_retry_any_ambiguous_upload"])
        self.assertFalse(result["release_ledger_migration_authorized"])
        self.assertFalse(result["publish_or_upload_authorized"])
        self.assertEqual(result["external_api_requests"],0)
        self.assertEqual(result["cloud_database_writes"],0)
        # No identifiers, raw episode IDs, dates, or media SHA in results.
        for private in (VIDEO_A,CHANNEL,SCHEDULE,"tutorial_short_en",SHA_A):
            self.assertNotIn(private,str(result))

    def test_ambiguous_upload_started_is_never_safe_to_retry(self):
        output=run(rows=(release("upload_started"),),owner=())
        self.assertEqual(output["quarantined_local_release_count"],1)
        self.assertIn("UPLOAD_STARTED_AMBIGUOUS_NEEDS_MANUAL_RECOVERY",
                      output["blocking_reasons"])
        self.assertFalse(output["safe_to_retry_any_ambiguous_upload"])
        self.assertFalse(output["publish_or_upload_authorized"])

    def test_missing_remote_video_is_quarantine_not_definitive_deletion(self):
        result=run(owner=(remote(VIDEO_B),))
        self.assertIn("BOUND_REMOTE_ID_NOT_FOUND_RECONCILIATION_REQUIRED",
                      result["blocking_reasons"])
        self.assertEqual(result["quarantined_local_release_count"],1)
        self.assertEqual(result["unmatched_owner_video_count"],1)
        self.assertNotIn("SAFE_TO_REUPLOAD",str(result))

    def test_private_remote_video_privacy_drift_is_detected(self):
        report=run(
            rows=(release("remote_private_verified"),),
            owner=(remote(privacy="public",schedule=None),),
        )
        self.assertIn("REMOTE_PRIVACY_DRIFT",report["blocking_reasons"])
        self.assertFalse(report["publish_or_upload_authorized"])

    def test_schedule_mismatch_or_missing_publish_at_quarantines(self):
        for value in ("2026-10-20T11:00:00+00:00",None):
            with self.subTest(value=value):
                out=run(owner=(remote(schedule=value),))
                self.assertIn("REMOTE_SCHEDULE_TIMESTAMP_MISMATCH",
                              out["blocking_reasons"])
                self.assertEqual(out["quarantined_local_release_count"],1)

    def test_remote_moved_public_before_local_readback_is_not_auto_advanced(self):
        result=run(owner=(remote(privacy="public",schedule=None),))
        self.assertIn("REMOTE_PRIVACY_DRIFT_OR_ALREADY_PUBLIC",
                      result["blocking_reasons"])
        self.assertFalse(result["release_ledger_migration_authorized"])

    def test_public_state_requires_public_remote_video(self):
        result=run(rows=(release("public_verified"),),owner=(remote(schedule=None),))
        self.assertIn("REMOTE_PUBLIC_STATE_NOT_CONFIRMED",
                      result["blocking_reasons"])
        good=run(rows=(release("public_verified"),),
                 owner=(remote(privacy="public",schedule=None),))
        self.assertEqual(good["quarantined_local_release_count"],0)
        self.assertFalse(good["publish_or_upload_authorized"])

    def test_remote_unknown_processing_and_metadata_ambiguity(self):
        result=run(owner=(remote(processing="unknown",uncertain=True),))
        self.assertIn("UNCERTAIN_REMOTE_VIDEO_METADATA",
                      result["blocking_reasons"])
        self.assertIn("REMOTE_PROCESSING_NOT_CONFIRMED_SUCCEEDED",
                      result["blocking_reasons"])
        self.assertIn("OWNER_READBACK_CONTAINS_UNCERTAIN_METADATA",
                      result["blocking_reasons"])

    def test_incomplete_snapshots_cannot_be_promoted_to_live_authority(self):
        result=run(complete=False,local_complete=False)
        self.assertIn("INCOMPLETE_REMOTE_OWNER_INVENTORY",result["blocking_reasons"])
        self.assertIn("INCOMPLETE_LOCAL_LEDGER_SNAPSHOT",result["blocking_reasons"])
        self.assertFalse(result["remote_identity_readback_authoritative"])

    def test_unknown_existing_channel_upload_requires_lineage_review(self):
        out=run(owner=(remote(),remote(VIDEO_B,privacy="public",schedule=None)))
        self.assertIn("UNMATCHED_OWNER_VIDEOS_REQUIRE_LINEAGE_REVIEW",
                      out["blocking_reasons"])
        self.assertEqual(out["unmatched_owner_video_count"],1)
        self.assertFalse(out["publish_or_upload_authorized"])

    def test_bad_channel_identity_rejected_before_assessing_release(self):
        with self.assertRaises(WorkflowError):
            reconcile_release_snapshots(
                (release(),),(remote(),),
                expected_channel_id=CHANNEL,observed_channel_id=OTHER_CHANNEL,
                remote_pagination_complete=True,
                local_ledger_snapshot_complete=True,
            )

    def test_duplicate_local_media_video_release_rows_rejected(self):
        for another in (
            release(episode="tutorial_short_hi",sha=SHA_A,vid=VIDEO_B),
            release(episode="tutorial_short_hi",sha=SHA_B,vid=VIDEO_A),
            release(episode="tutorial_short_en",sha=SHA_B,vid=VIDEO_B),
        ):
            with self.subTest(episode=another.episode_id),self.assertRaises(WorkflowError):
                run(rows=(release(),another))

    def test_duplicate_or_forged_remote_uncertainty_denied(self):
        for rows in (
            (remote(),remote()),
            (remote(privacy="public",schedule=SCHEDULE,uncertain=False),),
            (remote(processing="unknown",uncertain=False),),
        ):
            with self.assertRaises(WorkflowError):
                run(owner=rows)

    def test_local_structural_stage_id_timestamp_mismatch_denied(self):
        bad=[
            replace(release("planned"),media_sha256=SHA_A),
            replace(release(),youtube_id=None),
            replace(release(),publish_at_utc=None),
            replace(release("upload_started"),youtube_id=VIDEO_A),
            replace(release("media_qa_passed"),media_sha256=None),
            replace(release(),release_date="2026-02-30"),
            replace(release(),episode_id="../foo"),
            replace(release(),media_sha256=True),
        ]
        for item in bad:
            with self.subTest(stage=item.stage),self.assertRaises(WorkflowError):
                run(rows=(item,))

    def test_malformed_or_unbounded_inputs_denied_without_leaking_details(self):
        for rows, vids in (
            ([],(remote(),)),
            ((release(),),[remote()]),
            ((release(),)*501,(remote(),)),
            ((release(),),(remote(),)*501),
        ):
            with self.assertRaises(WorkflowError):
                run(rows=rows,owner=vids)
        out=run(rows=(),owner=())
        self.assertIn("NO_LOCAL_RELEASE_RECORDS_TO_RECONCILE",
                      out["blocking_reasons"])
        self.assertIn("NO_OWNER_VIDEOS_IN_READBACK",out["blocking_reasons"])

    def inventory(self,*,video=None,uncertain_count=0):
        listed=[{
            "youtube_id":video.youtube_id,
            "privacy":video.privacy,
            "processing":video.processing,
            "publish_at_utc":video.publish_at_utc,
            "uncertain_metadata":video.uncertain_metadata,
        }] if video is not None else []
        return {
            "status":"PRIVATE_READ_ONLY_RESPONSE_NOT_RELEASE_AUTHORITY",
            "channel_id":CHANNEL,"playlist_page_count":1,
            "video_count":len(listed),"videos":listed,
            "playlist_and_details_matched":True,
            "processing_or_schedule_uncertain_count":uncertain_count,
            "live_authentication_independently_attested":False,
            "d1_release_rows_reconciled":False,
            "owner_publish_consent_verified":False,
            "migration_authorized":False,
            "private_upload_authorized":False,
            "schedule_or_public_publishing_authorized":False,
            "raw_oauth_tokens_in_output":False,
            "storage_writes":0,
        }

    def bridge(self,*,inventory=None,releases=None):
        a=release()
        row=(a.release_date,a.episode_id,a.media_sha256,
             a.stage,a.youtube_id,a.publish_at_utc)
        return reconcile_existing_private_shapes(
            existing_ledger_rows=(row,) if releases is None else releases,
            private_youtube_inventory=self.inventory(video=remote())
                if inventory is None else inventory,
            expected_channel_id=CHANNEL,
            local_ledger_snapshot_complete=True,
        )

    def test_private_shape_bridge_uses_real_existing_ledger_row_order(self):
        outcome=self.bridge()
        self.assertEqual(outcome["matched_remote_video_id_count"],1)
        self.assertEqual(outcome["quarantined_local_release_count"],0)
        self.assertFalse(outcome["publish_or_upload_authorized"])
        self.assertFalse(outcome["owner_snapshot_origin_independently_authenticated"])
        for forbidden in (VIDEO_A,CHANNEL,SHA_A,SCHEDULE):
            self.assertNotIn(forbidden,str(outcome))

    def test_private_shape_bridge_rejects_privilege_escalation_and_unknown_keys(self):
        valid=self.inventory(video=remote())
        for name,value in (
            ("private_upload_authorized",True),
            ("owner_publish_consent_verified",True),
            ("d1_release_rows_reconciled",True),
            ("live_authentication_independently_attested",True),
            ("storage_writes",2),
            ("playlist_and_details_matched",False),
            ("video_count",7),
            ("processing_or_schedule_uncertain_count",1),
        ):
            altered=dict(valid,**{name:value})
            with self.subTest(field=name),self.assertRaises(WorkflowError):
                self.bridge(inventory=altered)
        leaking=dict(valid,oauth_secret="NEVER_ECHO")
        with self.assertRaises(WorkflowError) as e:
            self.bridge(inventory=leaking)
        self.assertNotIn("NEVER_ECHO",str(e.exception))

    def test_private_shape_bridge_unknown_or_wrong_channel_and_row_denied(self):
        valid=self.inventory(video=remote())
        for altered in (
            dict(valid,channel_id=OTHER_CHANNEL),
            dict(valid,videos=[{"youtube_id":VIDEO_A,"access_token":"XXX"}]),
            dict(valid,videos="not a list"),
        ):
            with self.assertRaises(WorkflowError):
                self.bridge(inventory=altered)
        for rows in (
            ((1,2),),
            ((release().release_date,release().episode_id),),
            ([1,2,3,4,5,6],),
        ):
            with self.assertRaises(WorkflowError):
                self.bridge(releases=rows)

    def test_private_shape_bridge_uncertain_processing_never_approves_retry(self):
        report=self.bridge(inventory=self.inventory(
            video=remote(processing="unknown",uncertain=True),
            uncertain_count=1,
        ))
        self.assertIn("UNCERTAIN_REMOTE_VIDEO_METADATA",report["blocking_reasons"])
        self.assertFalse(report["safe_to_retry_any_ambiguous_upload"])


if __name__=="__main__":
    unittest.main()
