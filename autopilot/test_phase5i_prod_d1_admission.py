"""Phase 5I offline sanitized admission tests; no real provider or private IDs."""
import copy
from datetime import datetime, timezone, timedelta
import json
import unittest

from autopilot.phase5i_prod_d1_admission import (
    CHANNEL_ID, ReadinessHold, inspect
)

NOW=datetime(2026,10,19,16,45,tzinfo=timezone.utc)


def evidence():
    return {
        "channel_id":CHANNEL_ID,
        "d1":{
            "release_rows":0,"event_rows":0,"duplicate_slot_groups":0,
            "youtube_id_unique_verified":True,
            "date_slot_unique_verified":False,
            "canonical_schema_verified":True,
            "snapshot_at_utc":"2026-10-19T16:44:00Z"
        },
        "time_travel":{
            "dashboard_time_travel_visible":True,
            "reported_retention_days":7,
            "production_storage_backend_verified":False,
            "bookmark_recorded_privately":False,
            "independent_backup_recovery_proven":False,
            "disposable_restore_drill_proven":False
        },
        "writer":{
            "all_writers_identified":False,"writers_frozen":False,
            "fencing_lease_verified":False,"conflicting_writer_absent":False
        },
        "youtube":{
            "three_distinct_receipts_confirmed":True,
            "channel_title_processing_checked":True,
            "private_video_ids_protected":True,
            "all_three_media_hashes_verified":False,
            "last_owner_readback_utc":"2026-10-19T16:20:54Z"
        },
        "budget":{
            "workers_free_plan_account_verified":False,
            "no_paid_upgrade_authorized":True,
            "no_new_service_connected":True,
            "global_zero_spend_control_verified":False
        },
        "approvals":{
            "owner_approved_prod_d1_write":False,
            "maintenance_window_approved":False,
            "migration_diff_approved":False,
            "rollback_plan_independently_approved":False
        }
    }


def all_claims():
    packet=evidence()
    for section in ["time_travel","writer","youtube","budget","approvals"]:
        for k,v in list(packet[section].items()):
            if type(v) is bool:
                packet[section][k]=True
    return packet


class Phase5ITests(unittest.TestCase):
    def run_gate(self,update=None,now=NOW):
        data=evidence()
        if update:update(data)
        return inspect(data,now=now)

    def test_realistic_observation_hold_not_ready(self):
        result=self.run_gate()
        self.assertEqual(result["status"],"HOLD_PRODUCTION_D1_MIGRATION")
        self.assertIn("RECOVERY_BOOKMARK_NOT_CUSTODIED",result["risk_codes"])
        self.assertIn("SINGLE_WRITER_FREEZE_NOT_VERIFIED",result["risk_codes"])
        self.assertIn("ACCOUNT_WIDE_ZERO_SPEND_CAP_UNPROVEN",result["risk_codes"])
        self.assertIn("EXPLICIT_PRODUCTION_D1_WRITE_APPROVAL_MISSING",result["risk_codes"])
        self.assertFalse(result["cloud_autopilot_ready"])
        self.assertEqual(result["production_d1_writes"],0)
        self.assertEqual(result["youtube_uploads"],0)
        self.assertEqual(result["sql_statements_generated"],[])

    def test_true_every_claim_still_cannot_grant_production_write(self):
        result=inspect(all_claims(),now=NOW)
        self.assertEqual(result["risk_codes"],[])
        self.assertEqual(result["status"],"CLAIMS_COMPLETE_INDEPENDENT_PROVENANCE_STILL_REQUIRED")
        for key in ("production_migration_authorized","production_backfill_permitted",
                    "production_rollback_permitted","cloud_autopilot_ready"):
            self.assertFalse(result[key])
        self.assertFalse(result["live_d1_checked_by_module"])

    def test_nonzero_release_or_event_rows_hold(self):
        for key in ("release_rows","event_rows"):
            with self.subTest(key=key):
                res=self.run_gate(lambda d:d["d1"].update({key:1}))
                self.assertIn("CANONICAL_ROWS_REQUIRE_FRESH_RECONCILIATION",res["risk_codes"])

    def test_duplicate_slot_conflict_holds(self):
        res=self.run_gate(lambda d:d["d1"].update({"duplicate_slot_groups":2}))
        self.assertIn("LIVE_DUPLICATE_SLOT_CONFLICT",res["risk_codes"])

    def test_existing_unique_date_slot_index_is_schema_drift(self):
        res=self.run_gate(lambda d:d["d1"].update({"date_slot_unique_verified":True}))
        self.assertIn("UNEXPECTED_EXISTING_DATE_SLOT_INDEX_RECHECK_PLAN",res["risk_codes"])

    def test_youtube_unique_index_or_schema_missing(self):
        for key in ("youtube_id_unique_verified","canonical_schema_verified"):
            with self.subTest(key=key):
                res=self.run_gate(lambda d:d["d1"].update({key:False}))
                self.assertIn("LIVE_CANONICAL_SCHEMA_OR_UNIQUE_VIDEO_INDEX_UNVERIFIED",res["risk_codes"])

    def test_stale_or_future_d1_snapshot_blocks(self):
        for at in ("2026-10-19T16:14:59Z","2026-10-19T16:46:00Z"):
            with self.subTest(at=at):
                res=self.run_gate(lambda d:d["d1"].update({"snapshot_at_utc":at}))
                self.assertIn("LIVE_D1_EVIDENCE_NOT_FRESH",res["risk_codes"])

    def test_owner_recheck_stale_or_future(self):
        for at in ("2026-10-19T16:00:00Z","2026-10-19T17:00:00Z"):
            with self.subTest(at=at):
                res=self.run_gate(lambda d:d["youtube"].update({"last_owner_readback_utc":at}))
                self.assertIn("OWNER_READBACK_NOT_FRESH",res["risk_codes"])

    def test_time_travel_visible_not_same_as_rollback(self):
        res=self.run_gate()
        self.assertNotIn("EXPECTED_SEVEN_DAY_RECOVERY_WINDOW_UNVERIFIED",res["risk_codes"])
        for key in ("PRODUCTION_BACKEND_VERSION_UNVERIFIED","INDEPENDENT_BACKUP_NOT_VERIFIED",
                    "DISPOSABLE_RESTORE_DRILL_NOT_PROVEN"):
            self.assertIn(key,res["risk_codes"])

    def test_wrong_retention_window_blocks(self):
        for days in (0,30):
            with self.subTest(days=days):
                res=self.run_gate(lambda d:d["time_travel"].update({"reported_retention_days":days}))
                self.assertIn("EXPECTED_SEVEN_DAY_RECOVERY_WINDOW_UNVERIFIED",res["risk_codes"])

    def test_d1_writer_freeze_unverified(self):
        res=self.run_gate()
        self.assertIn("SINGLE_WRITER_FREEZE_NOT_VERIFIED",res["risk_codes"])
        self.assertIn("FENCED_CAS_AND_NO_CONFLICTING_WRITER_NOT_VERIFIED",res["risk_codes"])

    def test_backup_bookmark_alone_not_enough(self):
        res=self.run_gate(lambda d:d["time_travel"].update({"bookmark_recorded_privately":True}))
        self.assertNotIn("RECOVERY_BOOKMARK_NOT_CUSTODIED",res["risk_codes"])
        self.assertIn("INDEPENDENT_BACKUP_NOT_VERIFIED",res["risk_codes"])
        self.assertFalse(res["production_rollback_permitted"])

    def test_youtube_missing_verified_media_hashes_blocks(self):
        res=self.run_gate()
        self.assertIn("OWNER_VIDEO_AND_MEDIA_PROVENANCE_INCOMPLETE",res["risk_codes"])

    def test_even_verified_remote_id_not_write_approval(self):
        res=self.run_gate(lambda d:d["youtube"].update({"all_three_media_hashes_verified":True}))
        self.assertIn("EXPLICIT_PRODUCTION_D1_WRITE_APPROVAL_MISSING",res["risk_codes"])

    def test_global_budget_unverified_blocks(self):
        res=self.run_gate()
        self.assertIn("ACCOUNT_WIDE_ZERO_SPEND_CAP_UNPROVEN",res["risk_codes"])

    def test_no_plan_upgrade_and_no_new_service_protects(self):
        res=self.run_gate()
        self.assertIn("FREE_PLAN_OR_CHARGE_PROTECTION_UNVERIFIED",res["risk_codes"])

    def test_missing_maintenance_approval_blocks(self):
        res=self.run_gate()
        self.assertIn("WRITER_FREEZE_MAINTENANCE_APPROVAL_MISSING",res["risk_codes"])

    def test_diff_and_rollback_signoff_block(self):
        res=self.run_gate()
        self.assertIn("SIGNED_MIGRATION_AND_ROLLBACK_REVIEW_INCOMPLETE",res["risk_codes"])

    def test_malformed_extra_token_key_rejected(self):
        data=evidence();data["access_token"]="DO-NOT-DISPLAY"
        with self.assertRaises(ReadinessHold) as ctx:inspect(data,now=NOW)
        self.assertNotIn("DO-NOT-DISPLAY",str(ctx.exception))

    def test_nested_extra_secret_input_rejected(self):
        data=evidence();data["time_travel"]["private_bookmark"]="SECRET"
        with self.assertRaises(ReadinessHold) as ctx:inspect(data,now=NOW)
        self.assertNotIn("SECRET",str(ctx.exception))

    def test_non_boolean_flags_fail_closed(self):
        for value in ("true",1,None,[],{}):
            with self.subTest(value=repr(value)):
                data=evidence();data["writer"]["writers_frozen"]=value
                with self.assertRaises(ReadinessHold):inspect(data,now=NOW)

    def test_bool_or_negative_count_rejected(self):
        for value in (True,False,-1,"0",1.5,10**9):
            with self.subTest(value=repr(value)):
                data=evidence();data["d1"]["release_rows"]=value
                with self.assertRaises(ReadinessHold):inspect(data,now=NOW)

    def test_malformed_time_or_naive_clock_rejected(self):
        for value in (None,"tomorrow","2026-10-19T16:20:00+05:30","2026-13-19T16:20:00Z"):
            with self.subTest(value=value):
                data=evidence();data["d1"]["snapshot_at_utc"]=value
                with self.assertRaises(ReadinessHold):inspect(data,now=NOW)
        with self.assertRaises(ReadinessHold):
            inspect(evidence(),now=datetime(2026,10,19,16,45))

    def test_wrong_channel_rejected(self):
        data=evidence();data["channel_id"]="UCunrelated"
        with self.assertRaises(ReadinessHold):inspect(data,now=NOW)

    def test_output_redacts_names_and_no_mutations(self):
        data=evidence()
        result=inspect(data,now=NOW)
        serialized=json.dumps(result)
        for forbidden in ("oauth_token","refresh_token","private_bookmark","youtube_video_id",
                          "media_sha256","client_secret"):
            self.assertNotIn(forbidden,serialized)
        self.assertEqual(result["sql_statements_generated"],[])
        self.assertEqual(result["production_d1_writes"],0)
        self.assertEqual(result["youtube_schedule_writes"],0)

    def test_has_no_live_provider_calls_even_if_claims_true(self):
        result=inspect(all_claims(),now=NOW)
        self.assertFalse(result["live_google_checked_by_module"])
        self.assertFalse(result["live_d1_checked_by_module"])
        self.assertFalse(result["production_backup_recovered_by_module"])

if __name__=="__main__":
    unittest.main()
