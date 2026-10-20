"""Phase 5J synthetic, no-network admission and publishing-source regressions."""
import copy
import tempfile
import unittest
from datetime import datetime,timezone
from pathlib import Path
from autopilot.phase5j_readonly_guard import assess, InvalidEvidence, WORKFLOWS, CHANNEL

NOW=datetime(2026,10,20,3,30,tzinfo=timezone.utc)
ROOT=Path(__file__).resolve().parents[1]

def fixture():
    return {"channel":CHANNEL,"checked_at_utc":"2026-10-20T03:20:00Z",
     "cloudflare":{"worker_seen":True,"uploads_off":True,"budget_flag_zero":True,
      "all_workers_seen":False,"cron_triggers_checked":False,
      "no_other_d1_writer_proven":False},
     "github":{"live_publish_variable_off":False,"environment_rules_verified":False,
               "other_writer_repos_reviewed":False},
     "backup":{"seven_day_window_seen":True,"bookmark_custodied":False,
               "backend_verified":False,"independent_restore_tested":False},
     "budget":{"free_plan_verified":False,"free_d1_limits_verified":False,
               "paid_services_excluded":False,"hard_zero_charge_cap_verified":False}}

class Phase5JGuardTests(unittest.TestCase):
    def check(self,payload=None,repo=ROOT,now=NOW):
        return assess(payload if payload is not None else fixture(),repo,now=now)

    def test_real_repo_source_manual_dispatch_guards(self):
        r=self.check()
        self.assertEqual(len(r["workflows"]),4)
        self.assertTrue(all(w["source_guard_present"] for w in r["workflows"]))

    def test_account_control_gaps_remain_hold(self):
        r=self.check()
        self.assertEqual(r["state"],"HOLD_WRITER_BACKUP_AND_COST")
        self.assertIn("CLOUDFLARE_WRITER_INVENTORY_INCOMPLETE",r["issues"])
        self.assertIn("GITHUB_PRODUCTION_VARIABLES_OR_WRITERS_UNVERIFIED",r["issues"])
        self.assertIn("BACKUP_AND_DISPOSABLE_RESTORE_UNVERIFIED",r["issues"])
        self.assertIn("ACCOUNT_WIDE_ZERO_SPEND_NOT_PROVEN",r["issues"])

    def test_even_all_true_never_approves_production(self):
        f=fixture()
        for part in ("cloudflare","github","backup","budget"):
            for name in f[part]:f[part][name]=True
        r=self.check(f)
        self.assertEqual(r["issues"],[])
        self.assertFalse(r["production_migration_authorized"])
        self.assertFalse(r["cloud_publishing_authorized"])
        self.assertFalse(r["cloud_autopilot_ready"])

    def test_flag_zero_is_not_global_cost_proof(self):
        r=self.check()
        self.assertIn("ACCOUNT_WIDE_ZERO_SPEND_NOT_PROVEN",r["issues"])

    def test_one_worker_seen_does_not_prove_all_writers(self):
        f=fixture()
        f["cloudflare"]["all_workers_seen"]=True
        r=self.check(f)
        self.assertIn("CLOUDFLARE_WRITER_INVENTORY_INCOMPLETE",r["issues"])

    def test_github_source_guard_is_not_live_variable_readback(self):
        self.assertIn("GITHUB_PRODUCTION_VARIABLES_OR_WRITERS_UNVERIFIED",
                      self.check()["issues"])

    def test_seven_day_ui_does_not_prove_restore(self):
        self.assertIn("BACKUP_AND_DISPOSABLE_RESTORE_UNVERIFIED",
                      self.check()["issues"])

    def test_no_video_or_sql_side_effects(self):
        r=self.check()
        self.assertEqual(r["production_d1_writes"],0)
        self.assertEqual(r["youtube_upload_attempts"],0)

    def test_no_extra_secret_field_allowed(self):
        f=fixture();f["refresh_token"]="example-private"
        with self.assertRaises(InvalidEvidence) as c:self.check(f)
        self.assertNotIn("example-private",str(c.exception))

    def test_nested_extra_field_disallowed(self):
        f=fixture();f["github"]["token"]="secret"
        with self.assertRaises(InvalidEvidence):self.check(f)

    def test_malformed_channel_rejected(self):
        f=fixture();f["channel"]="UCunrelated"
        with self.assertRaises(InvalidEvidence):self.check(f)

    def test_stale_check_requires_refresh(self):
        f=fixture();f["checked_at_utc"]="2026-10-18T01:00:00Z"
        self.assertIn("EVIDENCE_STALE",self.check(f)["issues"])

    def test_future_check_requires_refresh(self):
        f=fixture();f["checked_at_utc"]="2026-10-21T00:00:00Z"
        self.assertIn("EVIDENCE_STALE",self.check(f)["issues"])

    def test_timezone_offset_metadata_rejected(self):
        f=fixture();f["checked_at_utc"]="2026-10-20T08:50:00+05:30"
        with self.assertRaises(InvalidEvidence):self.check(f)

    def test_invalid_timestamp_rejected(self):
        f=fixture();f["checked_at_utc"]="2026-13-99T99:99:99Z"
        with self.assertRaises(InvalidEvidence):self.check(f)

    def test_boolean_not_coerced_from_string(self):
        f=fixture();f["cloudflare"]["uploads_off"]="true"
        with self.assertRaises(InvalidEvidence):self.check(f)

    def test_integer_not_coerced_to_boolean(self):
        f=fixture();f["github"]["live_publish_variable_off"]=1
        with self.assertRaises(InvalidEvidence):self.check(f)

    def test_source_missing_never_approves(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=self.check(repo=Path(tmp))
        self.assertIn("GITHUB_PUBLISH_SOURCE_GUARD_MISSING",r["issues"])

    def test_tampered_publisher_workflow_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/".github"/"workflows";root.mkdir(parents=True)
            for name,gate in WORKFLOWS.items():
                original=(ROOT/".github"/"workflows"/name).read_text()
                (root/name).write_text(original.replace("vars."+gate+" == 'true'","true"))
            r=self.check(repo=Path(tmp))
        self.assertIn("GITHUB_PUBLISH_SOURCE_GUARD_MISSING",r["issues"])

    def test_mutating_scout_not_in_required_publisher_list(self):
        self.assertEqual(set(WORKFLOWS),{"publish-youtube.yml",
           "publish-artifact-youtube.yml","configure-youtube.yml","collect-metrics.yml"})

    def test_payload_does_not_return_credential_values(self):
        import json
        result=json.dumps(self.check())
        for value in ("YOUTUBE_TOKEN_JSON","FM_ENCRYPTION_KEY","oauth_refresh","media_sha256"):
            self.assertNotIn(value,result)

if __name__=="__main__":
    unittest.main()
