"""Major Phase 5 real-schema compatibility regression tests; no providers."""
from pathlib import Path
import json
from tempfile import TemporaryDirectory
import unittest

from autopilot.phase5_major_schema_compatibility import inspect, UnsafeSchema

ROOT=Path(__file__).resolve().parents[1]
LIVE=["releases","release_events","youtube_release_observations","audit_heartbeats",
      "fm_upload_auth_attempts","fm_oauth_channel_proofs"]

class RealSchemaGateTests(unittest.TestCase):
    def test_current_candidate_legacy_shadow_lease_is_not_deployable(self):
        x=inspect(LIVE,repo_root=ROOT)
        self.assertEqual(x["state"],"HOLD_MAJOR_PHASE5_SCHEMA_AND_WRITE_ADMISSION")
        self.assertIn("STAGED_SQL_REFERENCES_MISSING_LIVE_TABLES",x["blocking_risk_codes"])
        self.assertEqual(set(x["staged_sql_missing_live_tables"]),
                         {"fm_release_writer_lease","fm_writer_release_shadow"})
        self.assertFalse(x["cloud_autopilot_ready"])
        self.assertFalse(x["writer_deployment_allowed"])
        self.assertEqual(x["production_d1_writes"],0)

    def test_do_not_confuse_youtube_unique_key_with_slot_uniqueness(self):
        x=inspect(LIVE,repo_root=ROOT)
        self.assertTrue(x["canonical_table_presence_confirmed_in_input"])
        self.assertFalse(x["production_schema_migration_authorized"])

    def test_any_claim_to_reuse_old_shadow_tables_is_not_live_evidence(self):
        expanded=LIVE+["fm_release_writer_lease","fm_writer_release_shadow"]
        x=inspect(expanded,repo_root=ROOT)
        self.assertEqual(x["staged_sql_missing_live_tables"],[])
        self.assertFalse(x["writer_deployment_allowed"])
        self.assertFalse(x["cloud_autopilot_ready"])

    def test_actual_missing_canonical_table_is_a_blocker(self):
        x=inspect([i for i in LIVE if i!="releases"],repo_root=ROOT)
        self.assertIn("CANONICAL_D1_SCHEMA_MISSING",x["blocking_risk_codes"])

    def test_reject_extra_secret_bearing_table_metadata(self):
        with self.assertRaises(UnsafeSchema):
            inspect(LIVE+["Bearer sk_sensitive"],repo_root=ROOT)

    def test_reject_boolean_or_duplicate_schema_fields(self):
        for value in (["releases","releases"],["releases",False],[],"releases",{}):
            with self.subTest(value=str(value)[:30]),self.assertRaises(UnsafeSchema):
                inspect(value,repo_root=ROOT)

    def test_reject_untrusted_repository_path(self):
        with self.assertRaises(UnsafeSchema):
            inspect(LIVE,repo_root=str(ROOT))

    def test_missing_candidate_is_hold_not_silent_pass(self):
        with TemporaryDirectory() as folder:
            with self.assertRaises(UnsafeSchema):
                inspect(LIVE,repo_root=Path(folder))

    def test_all_outputs_sanitized_and_no_auth(self):
        x=inspect(LIVE,repo_root=ROOT)
        encoded=json.dumps(x)
        for field in ("refresh_token","client_secret","access_token",
                      "videos.insert","youtube_video_id"):
            self.assertNotIn(field,encoded)
        self.assertFalse(x["observed_live_table_metadata_authenticated_here"])
        self.assertFalse(x["youtube_uploads_authorized"])
        self.assertFalse(x["youtube_schedule_writes_authorized"])

    def test_no_public_workflow_or_cloud_network_side_effects(self):
        x=inspect(LIVE,repo_root=ROOT)
        self.assertEqual(x["production_d1_writes"],0)
        self.assertFalse(x["production_worker_deployed"])
        self.assertFalse(x["production_database_backfill_authorized"])

if __name__=="__main__":
    unittest.main()
