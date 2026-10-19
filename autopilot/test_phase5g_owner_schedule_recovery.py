"""Offline no-provider Phase 5G regressions. Synthetic IDs ONLY."""
import copy
from datetime import datetime,timezone,timedelta
import json
import unittest

from autopilot.phase5g_owner_schedule_recovery import (
    CHANNEL,OwnerReadbackHold,verify_scheduled_receipts
)

NOW=datetime(2026,10,19,16,20,55,tzinfo=timezone.utc)
IDS={"short_morning":"AbCdEfGhIj0","long":"KlMnOpQrSt1","short_evening":"MnOpQrStUv2"}
TARGET={"short_morning":"2026-10-20T05:30:00Z","long":"2026-10-20T10:30:00Z",
        "short_evening":"2026-10-20T15:00:00Z"}

def snapshot():
    return {"date":"2026-10-20","expected_channel_id":CHANNEL,
            "owner_channel_checked":True,
            "release_slots":[{"slot":k,"video_id":v,"expected_title":"video "+k} for k,v in IDS.items()],
            "remote_observations":[
                {"slot":k,"video_id":v,"channel_id":CHANNEL,"title":"video "+k,
                 "privacy_status":"private","upload_status":"processed",
                 "processing_status":"succeeded","publish_at_utc":TARGET[k],
                 "observed_at_utc":"2026-10-19T16:20:54Z"}
                for k,v in IDS.items()]}

class RecoveryTests(unittest.TestCase):
    def evaluate(self,updates=None):
        p=snapshot()
        if updates:
            updates(p)
        return verify_scheduled_receipts(p,now=NOW)

    def test_three_exact_scheduled_reads_need_no_write(self):
        r=self.evaluate()
        self.assertEqual(r["matched_receipts"],3)
        self.assertEqual(r["state"],"ALL_THREE_RECEIPTS_MATCHED_UNATTESTED")
        self.assertEqual(r["youtube_writes"],0)
        self.assertEqual(r["d1_writes"],0)
        self.assertFalse(r["automatic_upload_permitted"])
        self.assertFalse(r["automatic_schedule_retry_permitted"])
        self.assertFalse(r["automatic_d1_backfill_permitted"])
        self.assertFalse(r["cloud_autopilot_ready"])
        serialized=json.dumps(r)
        for video_id in IDS.values():
            self.assertNotIn(video_id,serialized)
        self.assertEqual([x["expected_publish_at_utc"] for x in r["lanes"]],list(TARGET.values()))

    def test_existing_long_private_missing_schedule_no_retry(self):
        def mod(p):p["remote_observations"][1]["publish_at_utc"]=None
        r=self.evaluate(mod)
        self.assertEqual(r["matched_receipts"],2)
        self.assertEqual(r["lanes"][1]["decision"],"HOLD_EXISTING_PRIVATE_VIDEO_NEEDS_OWNER_REVIEW")
        self.assertFalse(r["automatic_schedule_retry_permitted"])
        self.assertFalse(r["automatic_upload_permitted"])

    def test_conflicting_publish_at_holds(self):
        def mod(p):p["remote_observations"][1]["publish_at_utc"]="2026-10-20T12:00:00Z"
        r=self.evaluate(mod)
        self.assertIn("PUBLISH_AT_CONFLICT",r["lanes"][1]["reason_codes"])
        self.assertEqual(r["state"],"HOLD_FOR_OWNER_RECONCILIATION")

    def test_wrong_channel_holds(self):
        def mod(p):p["remote_observations"][0]["channel_id"]="UCother"
        r=self.evaluate(mod)
        self.assertIn("VIDEO_IDENTITY_MISMATCH",r["lanes"][0]["reason_codes"])

    def test_wrong_title_holds(self):
        def mod(p):p["remote_observations"][1]["title"]="not matched"
        r=self.evaluate(mod)
        self.assertEqual(r["matched_receipts"],2)

    def test_wrong_video_id_holds(self):
        def mod(p):p["remote_observations"][2]["video_id"]="aaaaaaaaaaa"
        r=self.evaluate(mod)
        self.assertEqual(r["matched_receipts"],2)

    def test_private_processed_required(self):
        for key,value in (("privacy_status","public"),("privacy_status","unlisted"),
                          ("upload_status","uploaded"),("processing_status","processing")):
            def mod(p):p["remote_observations"][0][key]=value
            with self.subTest(key=key,value=value):
                self.assertEqual(self.evaluate(mod)["matched_receipts"],2)

    def test_duplicate_planned_video_ids_rejected(self):
        p=snapshot();p["release_slots"][1]["video_id"]=IDS["short_morning"]
        with self.assertRaisesRegex(OwnerReadbackHold,"DUPLICATE_REMOTE_VIDEO_ID"):
            verify_scheduled_receipts(p,now=NOW)

    def test_duplicate_release_slot_rejected(self):
        p=snapshot();p["release_slots"][1]["slot"]="short_morning"
        with self.assertRaises(OwnerReadbackHold):
            verify_scheduled_receipts(p,now=NOW)

    def test_duplicate_observation_slot_rejected(self):
        p=snapshot();p["remote_observations"][1]["slot"]="short_morning"
        with self.assertRaises(OwnerReadbackHold):
            verify_scheduled_receipts(p,now=NOW)

    def test_stale_observation_holds(self):
        def mod(p):p["remote_observations"][1]["observed_at_utc"]="2026-10-19T16:00:00Z"
        self.assertIn("OWNER_OBSERVATION_STALE_OR_FUTURE",self.evaluate(mod)["lanes"][1]["reason_codes"])

    def test_future_observation_holds(self):
        def mod(p):p["remote_observations"][1]["observed_at_utc"]="2026-10-19T16:30:00Z"
        self.assertIn("OWNER_OBSERVATION_STALE_OR_FUTURE",self.evaluate(mod)["lanes"][1]["reason_codes"])

    def test_owner_account_not_checked_fails_closed(self):
        def mod(p):p["owner_channel_checked"]=False
        self.assertEqual(self.evaluate(mod)["matched_receipts"],0)

    def test_unknown_extra_credential_field_rejected(self):
        p=snapshot();p["refresh_token"]="TOP-SECRET"
        with self.assertRaises(OwnerReadbackHold) as err:
            verify_scheduled_receipts(p,now=NOW)
        self.assertNotIn("TOP-SECRET",str(err.exception))

    def test_unparseable_day_rejected(self):
        p=snapshot();p["date"]="2026-02-30"
        with self.assertRaises(OwnerReadbackHold):
            verify_scheduled_receipts(p,now=NOW)

    def test_extra_lane_denied(self):
        p=snapshot();p["release_slots"].append(p["release_slots"][0].copy())
        with self.assertRaises(OwnerReadbackHold):
            verify_scheduled_receipts(p,now=NOW)

    def test_naive_clock_rejected(self):
        with self.assertRaises(OwnerReadbackHold):
            verify_scheduled_receipts(snapshot(),now=datetime(2026,10,19,16,20))

    def test_bad_video_id_rejected(self):
        p=snapshot();p["remote_observations"][0]["video_id"]="../etc/passwd"
        with self.assertRaises(OwnerReadbackHold):
            verify_scheduled_receipts(p,now=NOW)

    def test_title_metadata_never_emitted(self):
        p=snapshot()
        p["release_slots"][0]["expected_title"]="private production title"
        p["remote_observations"][0]["title"]="private production title"
        r=verify_scheduled_receipts(p,now=NOW)
        self.assertNotIn("private production title",json.dumps(r))

    def test_not_claiming_live_google_authenticated_from_fake_data(self):
        r=self.evaluate()
        self.assertFalse(r["remote_credentials_authenticated_here"])
        self.assertEqual(r["actual_google_api_calls"],0)
        self.assertEqual(r["input_trust"],"CALLER_SUPPLIED_UNATTESTED")
        self.assertEqual(r["state"],"ALL_THREE_RECEIPTS_MATCHED_UNATTESTED")

if __name__=="__main__":
    unittest.main()
