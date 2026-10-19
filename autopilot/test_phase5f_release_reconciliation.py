"""Phase 5F: offline no-credential, no-provider release reconciliation tests."""
import copy
import json
import unittest

from autopilot.phase5f_release_reconciliation import (
    CHANNEL, ReconciliationBlocked, reconcile,
)

def input_packet():
    return {
        "release_date":"2026-10-20",
        "channel_id":CHANNEL,
        "d1":{"row_count":0,"events_count":0,"rows":[],"observations":[
            {"release_date":"2026-10-19","slot_ist":"long","status":"SCHEDULED_OBSERVED",
             "api_rechecked":False,"has_schedule":True},
            {"release_date":"2026-10-19","slot_ist":"short_evening","status":"SCHEDULED_OBSERVED",
             "api_rechecked":False,"has_schedule":True},
            {"release_date":"2026-10-19","slot_ist":"short_morning","status":"PUBLIC_OBSERVED",
             "api_rechecked":False,"has_schedule":False},
        ]},
        "external":[
            {"slot":"short_morning","episode_id":"fm_20261020_short_en",
             "youtube_id":"AbCdEfGhIj0","status":"SCHEDULED_VERIFIED",
             "publish_at_utc":"2026-10-20T05:30:00Z"},
            {"slot":"long","episode_id":"fm_20261020_long_hi",
             "youtube_id":"MnOpQrStUv2","status":"REMOTE_PRIVATE_VERIFIED","publish_at_utc":None},
            {"slot":"short_evening","episode_id":"fm_20261020_short_hi",
             "youtube_id":"KlMnOpQrSt1","status":"SCHEDULED_VERIFIED",
             "publish_at_utc":"2026-10-20T15:00:00Z"},
        ],
    }

def row(ep,slot,yid=None,state="PLANNED",at=None):
    return {"release_date":"2026-10-20","episode_id":ep,
            "channel_id":CHANNEL,"slot_ist":slot,"state":state,
            "youtube_id":yid,"publish_at_utc":at}


class Phase5FReconciliationTests(unittest.TestCase):
    def test_live_aggregate_20_oct_known_mismatch(self):
        p=input_packet()
        result=reconcile(p)
        self.assertEqual(result["status"],"BLOCKED_LEDGER_DIVERGENCE")
        self.assertEqual(result["canonical_d1_release_count"],0)
        self.assertEqual(result["canonical_d1_event_count"],0)
        self.assertEqual(result["d1_observations_total"],3)
        self.assertEqual(result["prior_day_observations"],3)
        self.assertEqual(result["current_day_recheck_timestamps"],0)
        self.assertEqual(result["missing_d1_episode_count"],3)
        self.assertEqual(result["external_video_ids_without_canonical_row"],3)
        self.assertEqual(result["private_video_schedule_unconfirmed_count"],1)
        self.assertIn("PRIVATE_UPLOAD_SCHEDULE_UNCONFIRMED",result["risk_codes"])
        self.assertFalse(result["automatic_schedule_retry_authorized"])
        self.assertFalse(result["automatic_backfill_authorized"])
        self.assertFalse(result["automatic_upload_retry_authorized"])
        self.assertFalse(result["cloud_autopilot_ready"])
        for v in ("AbCdEfGhIj0","KlMnOpQrSt1","MnOpQrStUv2","fm_20261020_short_en"):
            self.assertNotIn(v,json.dumps(result))

    def test_consistent_three_d1_records_still_not_certified(self):
        p=input_packet()
        rows=[
            row("fm_20261020_short_en","short_morning","AbCdEfGhIj0",
                "SCHEDULED_VERIFIED","2026-10-20T05:30:00Z"),
            row("fm_20261020_long_hi","long","MnOpQrStUv2","REMOTE_PRIVATE_VERIFIED"),
            row("fm_20261020_short_hi","short_evening","KlMnOpQrSt1",
                "SCHEDULED_VERIFIED","2026-10-20T15:00:00Z"),
        ]
        p["d1"].update(rows=rows,row_count=3)
        r=reconcile(p)
        self.assertEqual(r["missing_d1_episode_count"],0)
        self.assertEqual(r["external_video_ids_without_canonical_row"],0)
        self.assertEqual(r["status"],"BLOCKED_LEDGER_DIVERGENCE")
        self.assertIn("NO_SAME_DAY_AUTHENTICATED_RECHECK_TIMESTAMP",r["risk_codes"])
        self.assertFalse(r["real_owner_api_readback_performed"])
        self.assertFalse(r["canonical_ledger_write_authorized"])

    def test_duplicate_slot_surplus_detected(self):
        p=input_packet()
        p["d1"].update(row_count=2,rows=[
            row("fm_20261020_short_en","short_morning"),
            row("fm_20261020_long_hi","short_morning"),
        ])
        r=reconcile(p)
        self.assertEqual(r["d1_duplicate_slot_surplus"],1)
        self.assertIn("DUPLICATE_D1_SLOTS",r["risk_codes"])

    def test_orphan_events_risk_does_not_fabricate_rows(self):
        p=input_packet();p["d1"]["events_count"]=10
        r=reconcile(p)
        self.assertIn("EVENTS_WITHOUT_RELEASES_REVIEW",r["risk_codes"])

    def test_uncertain_upload_requires_manual_investigation(self):
        p=input_packet()
        p["d1"].update(row_count=1,rows=[
            row("fm_20261020_long_hi","long",state="UPLOAD_STARTED")
        ])
        r=reconcile(p)
        self.assertEqual(r["uncertain_upload_count"],1)
        self.assertIn("UNCERTAIN_UPLOAD_NO_RETRY",r["risk_codes"])
        self.assertFalse(r["automatic_upload_retry_authorized"])

    def test_wrong_remote_id_detected_no_secrets(self):
        p=input_packet()
        p["d1"].update(row_count=1,rows=[
            row("fm_20261020_short_en","short_morning","abcdefghijk")
        ])
        r=reconcile(p)
        self.assertEqual(r["remote_id_disagreement_count"],1)
        self.assertNotIn("abcdefghijk",json.dumps(r))

    def test_scheduled_claim_without_video_or_instant_fails_closed(self):
        for update in ({"youtube_id":None},{"publish_at_utc":None}):
            with self.subTest(update=update):
                p=input_packet();p["external"][0].update(update)
                with self.assertRaises(ReconciliationBlocked):
                    reconcile(p)

    def test_wrong_target_time_denied(self):
        p=input_packet()
        p["external"][0]["publish_at_utc"]="2026-10-20T11:00:00Z"
        with self.assertRaisesRegex(ReconciliationBlocked,"WRONG_PUBLISH"):
            reconcile(p)

    def test_incomplete_d1_snapshot_denied(self):
        p=input_packet();p["d1"]["row_count"]=4
        with self.assertRaisesRegex(ReconciliationBlocked,"NOT_COMPLETE"):
            reconcile(p)

    def test_wrong_channel_rejected(self):
        p=input_packet();p["channel_id"]="UCanother12345678901234"
        with self.assertRaisesRegex(ReconciliationBlocked,"WRONG_CHANNEL"):
            reconcile(p)

    def test_two_external_lanes_denied(self):
        p=input_packet();p["external"].pop()
        with self.assertRaises(ReconciliationBlocked):
            reconcile(p)

    def test_duplicate_external_video_id_denied(self):
        p=input_packet();p["external"][2]["youtube_id"]=p["external"][0]["youtube_id"]
        with self.assertRaisesRegex(ReconciliationBlocked,"DUPLICATE_EXTERNAL_VIDEO_ID"):
            reconcile(p)

    def test_duplicate_external_slot_denied(self):
        p=input_packet();p["external"][1]["slot"]="short_morning"
        with self.assertRaises(ReconciliationBlocked):
            reconcile(p)

    def test_unknown_fields_and_secret_inputs_denied(self):
        p=input_packet();p["google_refresh_token"]="SENSITIVE"
        with self.assertRaises(ReconciliationBlocked):
            reconcile(p)
        p=input_packet();p["d1"]["rows"].append({"password":"SENSITIVE"})
        p["d1"]["row_count"]=1
        with self.assertRaises(ReconciliationBlocked) as ex:
            reconcile(p)
        self.assertNotIn("SENSITIVE",str(ex.exception))

    def test_observation_flags_boolean_not_string(self):
        p=input_packet();p["d1"]["observations"][0]["api_rechecked"]="true"
        with self.assertRaises(ReconciliationBlocked):
            reconcile(p)

    def test_impossible_observation_day_denied(self):
        p=input_packet();p["d1"]["observations"][0]["release_date"]="2026-02-30"
        with self.assertRaises(ReconciliationBlocked):
            reconcile(p)

    def test_duplicate_d1_youtube_id_denied(self):
        p=input_packet()
        p["d1"].update(row_count=2,rows=[
            row("fm_20261020_short_en","short_morning","abcdefghijk"),
            row("fm_20261020_long_hi","long","abcdefghijk")
        ])
        with self.assertRaisesRegex(ReconciliationBlocked,"DUPLICATE_D1_VIDEO_ID"):
            reconcile(p)

    def test_d1_wrong_slot_time_detected_without_sql(self):
        p=input_packet()
        p["d1"].update(row_count=1,rows=[
            row("fm_20261020_short_en","short_morning","AbCdEfGhIj0",
                "SCHEDULED_VERIFIED","2026-10-20T06:00:00Z"),
        ])
        r=reconcile(p)
        self.assertIn("RELEASE_KEY_OR_TIME_CONFLICT",r["risk_codes"])
        self.assertEqual(r["migration_sql_generated"],[])
        self.assertEqual(r["youtube_schedule_updates"],0)

    def test_d1_has_foreign_release_day_rejected(self):
        p=input_packet()
        bad=row("fm_20261020_short_en","short_morning")
        bad["release_date"]="2026-10-19"
        p["d1"].update(row_count=1,rows=[bad])
        with self.assertRaisesRegex(ReconciliationBlocked,"WRONG_DAY"):
            reconcile(p)

    def test_quiet_snapshot_with_live_recheck_still_no_automation(self):
        p=input_packet()
        p["d1"]["observations"][0].update(release_date="2026-10-20",api_rechecked=True)
        p["external"][1].update(status="SCHEDULED_VERIFIED",publish_at_utc="2026-10-20T10:30:00Z")
        p["d1"].update(row_count=3,rows=[
            row("fm_20261020_short_en","short_morning","AbCdEfGhIj0",
                "SCHEDULED_VERIFIED","2026-10-20T05:30:00Z"),
            row("fm_20261020_long_hi","long","MnOpQrStUv2",
                "SCHEDULED_VERIFIED","2026-10-20T10:30:00Z"),
            row("fm_20261020_short_hi","short_evening","KlMnOpQrSt1",
                "SCHEDULED_VERIFIED","2026-10-20T15:00:00Z")
        ])
        r=reconcile(p)
        self.assertEqual(r["status"],"CONSISTENT_UNATTESTED_NO_WRITE")
        self.assertFalse(r["automatic_backfill_authorized"])
        self.assertFalse(r["cloud_autopilot_ready"])

    def test_private_long_must_have_immutable_id_and_no_unverified_schedule(self):
        for change in ({"youtube_id":None},{"publish_at_utc":"2026-10-20T10:30:00Z"}):
            p=input_packet()
            p["external"][1].update(change)
            with self.assertRaisesRegex(ReconciliationBlocked,"PRIVATE_VIDEO_WITHOUT_SAFE"):
                reconcile(p)

    def test_malformed_unhashable_slot_is_safe_rejection(self):
        p=input_packet()
        p["external"][1]["slot"]=["long"]
        with self.assertRaises(ReconciliationBlocked):
            reconcile(p)

if __name__=="__main__":
    unittest.main()
