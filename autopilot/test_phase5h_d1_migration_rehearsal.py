"""Offline Phase5H rehearsal tests. No Cloudflare, OAuth, media or real IDs."""
from __future__ import annotations
import copy
from datetime import datetime, timedelta, timezone
import json
import unittest

from autopilot.phase5h_d1_migration_rehearsal import (
    CHANNEL, COLUMNS, INDEXES, MigrationHold, rehearse,
)

NOW=datetime(2026,10,19,18,10,tzinfo=timezone.utc)
VIDS=("AbCdEfGhIj0","KlMnOpQrSt1","MnOpQrStUv2")
EPISODES=("fm_20261020_short_en","fm_20261020_long_hi","fm_20261020_short_hi")
SLOTS=("short_morning","long","short_evening")
TIMES=("2026-10-20T05:30:00Z","2026-10-20T10:30:00Z","2026-10-20T15:00:00Z")


def data():
    return {
      "release_date":"2026-10-20","channel_id":CHANNEL,
      "source_verified_by_this_module":False,
      "canonical_d1_metadata":{
        "release_rows":0,"event_rows":0,"column_names":sorted(COLUMNS),
        "release_indexes":sorted(INDEXES),
        "date_slot_unique_index_exists":False,
        "snapshot_timestamp_utc":"2026-10-19T18:00:00Z"},
      "owner_receipts":[
        {"slot":SLOTS[i],"episode_id":EPISODES[i],
         "youtube_video_id":VIDS[i],"media_sha256":str(i+1)*64,
         "channel_id":CHANNEL,"publish_at_utc":TIMES[i],
         "owner_observed_at_utc":"2026-10-19T18:04:00Z",
         "privacy_status":"private","upload_status":"processed",
         "processing_status":"succeeded"}
        for i in range(3)]
    }


class RecoveryRehearsalTests(unittest.TestCase):
    def call(self,changed=None,**kwargs):
        x=data()
        if changed:changed(x)
        return rehearse(x,now=NOW,**kwargs)

    def test_three_receipts_rehearsed_and_slot_constraint_proven(self):
        r=self.call()
        self.assertEqual(r["status"],"ISOLATED_SQLITE_REHEARSAL_PASSED")
        self.assertEqual(r["sqlite_rows_after_simulation"],3)
        self.assertEqual(r["sqlite_event_rows_after_simulation"],3)
        self.assertTrue(r["unique_date_slot_index_enforced_in_sqlite"])
        self.assertTrue(r["simulated_index_present"])
        self.assertFalse(r["real_d1_index_created"])
        self.assertEqual(r["production_d1_rows_written"],0)
        self.assertEqual(r["real_cloudflare_queries"],0)
        self.assertFalse(r["production_backfill_authorized"])
        self.assertFalse(r["cloud_autopilot_ready"])
        self.assertFalse(r["owner_api_authenticated_in_this_module"])

    def test_rollback_before_index_removes_everything(self):
        r=self.call(fault_at="before_index")
        self.assertEqual(r["status"],"SIMULATED_FAULT_ROLLED_BACK")
        self.assertTrue(r["transaction_rollback_observed"])
        self.assertEqual(r["sqlite_rows_after_simulation"],0)
        self.assertEqual(r["sqlite_event_rows_after_simulation"],0)
        self.assertFalse(r["simulated_index_present"])

    def test_rollback_mid_insert_removes_everything(self):
        r=self.call(fault_at="after_first_record")
        self.assertEqual(r["sqlite_rows_after_simulation"],0)
        self.assertEqual(r["sqlite_event_rows_after_simulation"],0)
        self.assertFalse(r["simulated_index_present"])
        self.assertTrue(r["transaction_rollback_observed"])

    def test_rollback_before_commit_removes_everything(self):
        r=self.call(fault_at="before_commit")
        self.assertEqual(r["sqlite_rows_after_simulation"],0)
        self.assertEqual(r["sqlite_event_rows_after_simulation"],0)
        self.assertTrue(r["transaction_rollback_observed"])

    def test_unrecognized_fault_injection_rejected(self):
        with self.assertRaises(MigrationHold):
            self.call(fault_at="real_cloudflare")

    def test_real_d1_nonzero_rows_hold(self):
        for field in ("release_rows","event_rows"):
            with self.subTest(field=field), self.assertRaisesRegex(
                MigrationHold,"NONEMPTY_D1"
            ):
                self.call(lambda d:d["canonical_d1_metadata"].update({field:1}))

    def test_d1_zero_counts_must_be_literal_integers(self):
        for value in (False,True,"0",-1,10**7):
            with self.subTest(value=value), self.assertRaises(MigrationHold):
                self.call(lambda d:d["canonical_d1_metadata"].update({"release_rows":value}))

    def test_existing_date_slot_unique_index_changes_rehearsal(self):
        with self.assertRaisesRegex(MigrationHold,"CONSTRAINT_ALREADY_CHANGED"):
            self.call(lambda d:d["canonical_d1_metadata"].update(
                {"date_slot_unique_index_exists":True}))

    def test_wrong_schema_columns_hold(self):
        for changed in (
            lambda c:c.remove("youtube_id"),
            lambda c:c.append("oauth_refresh_token"),
            lambda c:c.append(["bad"]),
        ):
            with self.subTest(changed=changed), self.assertRaises(MigrationHold):
                self.call(lambda d:changed(d["canonical_d1_metadata"]["column_names"]))

    def test_wrong_indexes_hold(self):
        for changed in (lambda i:i.remove("sqlite_autoindex_releases_2"),
                        lambda i:i.append({"bad":"index"}),
                        lambda i:i.append("idx_overwritten")):
            with self.subTest(changed=changed), self.assertRaises(MigrationHold):
                self.call(lambda d:changed(d["canonical_d1_metadata"]["release_indexes"]))

    def test_stale_schema_evidence_hold(self):
        with self.assertRaisesRegex(MigrationHold,"SNAPSHOT_STALE"):
            self.call(lambda d:d["canonical_d1_metadata"].update(
                {"snapshot_timestamp_utc":"2026-10-19T01:00:00Z"}))

    def test_future_schema_evidence_hold(self):
        with self.assertRaisesRegex(MigrationHold,"SNAPSHOT_STALE"):
            self.call(lambda d:d["canonical_d1_metadata"].update(
                {"snapshot_timestamp_utc":"2026-10-19T18:11:00Z"}))

    def test_never_accept_user_assertion_as_provider_auth(self):
        with self.assertRaisesRegex(MigrationHold,"PROVENANCE"):
            self.call(lambda d:d.update({"source_verified_by_this_module":True}))

    def test_wrong_channel_hold(self):
        with self.assertRaisesRegex(MigrationHold,"WRONG_CHANNEL"):
            self.call(lambda d:d.update({"channel_id":"UCnotowner01234567890123"}))

    def test_wrong_release_day_hold(self):
        with self.assertRaisesRegex(MigrationHold,"INVALID_DATE"):
            self.call(lambda d:d.update({"release_date":"2026-02-30"}))

    def test_wrong_episode_day_hold(self):
        with self.assertRaisesRegex(MigrationHold,"INVALID_OR_DUPLICATE_EPISODE"):
            self.call(lambda d:d["owner_receipts"][0].update(
                {"episode_id":"fm_20261019_short_en"}))

    def test_duplicate_release_slot_hold(self):
        with self.assertRaisesRegex(MigrationHold,"INVALID_OR_DUPLICATE_SLOT"):
            self.call(lambda d:d["owner_receipts"][1].update(
                {"slot":"short_morning"}))

    def test_duplicate_video_id_hold(self):
        with self.assertRaisesRegex(MigrationHold,"INVALID_OR_DUPLICATE_REMOTE_ID"):
            self.call(lambda d:d["owner_receipts"][1].update(
                {"youtube_video_id":VIDS[0]}))

    def test_invalid_media_sha256_hold(self):
        for s in ("123","G"*64,bytes.fromhex("aa"*32)):
            with self.subTest(value=str(s)[:25]),self.assertRaises(MigrationHold):
                self.call(lambda d:d["owner_receipts"][1].update({"media_sha256":s}))

    def test_wrong_utc_time_hold(self):
        for s in ("2026-10-20T15:00:00Z","2026-10-20T16:00:00+05:30"):
            with self.subTest(value=s),self.assertRaises(MigrationHold):
                self.call(lambda d:d["owner_receipts"][1].update(
                    {"publish_at_utc":s}))

    def test_stale_owner_observation_hold(self):
        with self.assertRaisesRegex(MigrationHold,"STALE_OR_FUTURE_OWNER"):
            self.call(lambda d:d["owner_receipts"][1].update(
                {"owner_observed_at_utc":"2026-10-18T00:00:00Z"}))

    def test_future_owner_observation_hold(self):
        with self.assertRaisesRegex(MigrationHold,"STALE_OR_FUTURE_OWNER"):
            self.call(lambda d:d["owner_receipts"][1].update(
                {"owner_observed_at_utc":"2026-10-19T19:00:00Z"}))

    def test_unprocessed_video_holds(self):
        for field,value in (("privacy_status","unlisted"),
                            ("upload_status","uploaded"),
                            ("processing_status","processing")):
            with self.subTest(field=field),self.assertRaisesRegex(
                MigrationHold,"UNVERIFIED_PRIVATE_PROCESSED_RELEASE"
            ):
                self.call(lambda d:d["owner_receipts"][1].update({field:value}))

    def test_episode_kind_slot_mismatch_hold(self):
        with self.assertRaisesRegex(MigrationHold,"EPISODE_TYPE_SLOT_MISMATCH"):
            self.call(lambda d:d["owner_receipts"][1].update(
                {"episode_id":"fm_20261020_short_hi"}))

    def test_unexpected_secret_field_fails_closed(self):
        def change(d):d["owner_receipts"][0]["refresh_token"]="SENSITIVE"
        with self.assertRaises(MigrationHold) as err:
            self.call(change)
        self.assertNotIn("SENSITIVE",str(err.exception))

    def test_output_redacts_private_receipts_and_hash(self):
        r=self.call()
        text=json.dumps(r)
        for value in VIDS+EPISODES+("1"*64,"2"*64,"3"*64):
            self.assertNotIn(value,text)
        self.assertEqual(r["production_d1_rows_written"],0)
        self.assertEqual(r["youtube_upload_authorized"],False)
        self.assertEqual(r["youtube_schedule_authorized"],False)

    def test_missing_and_extra_receipts_hold(self):
        for modifier in (lambda x:x.pop(), lambda x:x.append(copy.deepcopy(x[0]))):
            with self.subTest(modifier=modifier),self.assertRaises(MigrationHold):
                self.call(lambda d:modifier(d["owner_receipts"]))

    def test_bad_snapshot_and_unaware_clock(self):
        x=data()
        with self.assertRaises(MigrationHold):
            rehearse(x,now=datetime(2026,10,19,18,10))
        x["canonical_d1_metadata"]["snapshot_timestamp_utc"]="invalid"
        with self.assertRaises(MigrationHold):
            rehearse(x,now=NOW)

if __name__ == "__main__":
    unittest.main()
