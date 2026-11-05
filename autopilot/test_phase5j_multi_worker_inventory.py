"""No-network Phase 5J multi-Worker threat surface tests."""
from datetime import datetime, timezone
import json
import unittest

from autopilot.phase5j_multi_worker_inventory import (
    ROLES, UnsafeInventory, inspect_workers,
)

NOW=datetime(2026,10,20,4,12,tzinfo=timezone.utc)

def evidence():
    return {
        "observed_at_utc":"2026-10-20T04:05:00Z",
        "account_list_fully_enumerated":False,
        "unrelated_workers_reviewed":False,
        "workers":{
            "upload_oauth_vault":{
                "deployed":True,"public_route":True,"d1_binding":True,
                "triggers_reviewed":False,"secrets_not_exported":True,
                "d1_mutation_routes_reviewed":False,
                "d1_writes_denied_under_zero_budget":False
            },
            "brand_readonly_probe":{
                "deployed":True,"public_route":True,"d1_binding":True,
                "triggers_reviewed":False,"secrets_not_exported":True,
                "d1_mutation_routes_reviewed":False,
                "d1_writes_denied_under_zero_budget":False
            },
            "zero_cost_controller":{
                "deployed":True,"public_route":True,"d1_binding":False,
                "triggers_reviewed":False,"secrets_not_exported":True,
                "d1_mutation_routes_reviewed":False,
                "d1_writes_denied_under_zero_budget":False
            }
        }
    }

class MultiWorkerTest(unittest.TestCase):
    def test_live_dashboard_snapshot_blocks(self):
        r=inspect_workers(evidence(),now=NOW)
        self.assertEqual(r["state"],"HOLD_MULTI_WORKER_PRODUCTION_ADMISSION")
        self.assertEqual(r["expected_worker_roles_reviewed"],3)
        self.assertIn("PUBLIC_D1_BOUND_WORKER_MAY_WRITE",r["risk_codes"])
        self.assertIn("WORKER_TRIGGERS_ROUTES_CRON_UNVERIFIED",r["risk_codes"])
        self.assertIn("CLOUDFLARE_ACCOUNT_WORKER_LIST_INCOMPLETE",r["risk_codes"])
        self.assertFalse(r["production_migration_authorized"])
        self.assertFalse(r["cloud_publisher_authorized"])

    def test_no_worker_name_is_a_security_policy(self):
        x=evidence()
        x["workers"]["zero_cost_controller"]["d1_binding"]=True
        r=inspect_workers(x,now=NOW)
        self.assertEqual(r["state"],"HOLD_MULTI_WORKER_PRODUCTION_ADMISSION")
        self.assertFalse(r["global_zero_spend_proven"])

    def test_all_positive_claims_never_grant_production_authorization(self):
        x=evidence()
        x["account_list_fully_enumerated"]=True
        x["unrelated_workers_reviewed"]=True
        for w in x["workers"].values():
            for key in w:w[key]=True
        r=inspect_workers(x,now=NOW)
        self.assertEqual(r["risk_codes"],[])
        self.assertEqual(r["state"],"HOLD_MULTI_WORKER_PRODUCTION_ADMISSION")
        self.assertFalse(r["production_migration_authorized"])
        self.assertFalse(r["cloud_autopilot_ready"])
        self.assertFalse(r["real_cloudflare_api_called"])

    def test_unknown_worker_exposes_incomplete_inventory(self):
        x=evidence()
        x["workers"]["other_upload_writer"]=x["workers"]["upload_oauth_vault"].copy()
        with self.assertRaises(UnsafeInventory):
            inspect_workers(x,now=NOW)

    def test_missing_vault_fail_closed(self):
        x=evidence()
        del x["workers"]["upload_oauth_vault"]
        with self.assertRaises(UnsafeInventory):
            inspect_workers(x,now=NOW)

    def test_stale_evidence_flagged(self):
        x=evidence()
        x["observed_at_utc"]="2026-10-18T00:00:00Z"
        self.assertIn("MULTI_WORKER_ACCOUNT_SNAPSHOT_NOT_FRESH",
                      inspect_workers(x,now=NOW)["risk_codes"])

    def test_future_evidence_flagged(self):
        x=evidence()
        x["observed_at_utc"]="2026-10-21T00:00:00Z"
        self.assertIn("MULTI_WORKER_ACCOUNT_SNAPSHOT_NOT_FRESH",
                      inspect_workers(x,now=NOW)["risk_codes"])

    def test_invalid_timestamp_rejected(self):
        x=evidence()
        x["observed_at_utc"]="2026-10-20T09:30:00+05:30"
        with self.assertRaises(UnsafeInventory):
            inspect_workers(x,now=NOW)

    def test_no_secrets_accepted_or_reflected(self):
        x=evidence()
        x["workers"]["upload_oauth_vault"]["refresh_token"]="nevercopy"
        with self.assertRaises(UnsafeInventory) as err:
            inspect_workers(x,now=NOW)
        self.assertNotIn("nevercopy",str(err.exception))

    def test_string_boolean_rejected(self):
        x=evidence()
        x["workers"]["upload_oauth_vault"]["d1_binding"]="true"
        with self.assertRaises(UnsafeInventory):
            inspect_workers(x,now=NOW)

    def test_unhashable_malformed_worker_metadata_rejected(self):
        x=evidence()
        x["workers"]["brand_readonly_probe"]=[]
        with self.assertRaises(UnsafeInventory):
            inspect_workers(x,now=NOW)

    def test_no_api_sql_video_write_or_credentials(self):
        r=inspect_workers(evidence(),now=NOW)
        for k in ("real_d1_writes","real_youtube_writes"):
            self.assertEqual(r[k],0)
        self.assertFalse(r["secrets_exported"])
        self.assertFalse(r["global_zero_spend_proven"])
        self.assertEqual(set(v["role"] for v in r["worker_evidence"]),ROLES)
        data=json.dumps(r)
        for secret in ("client_secret","oauth_refresh_token","workers.dev","account_id"):
            self.assertNotIn(secret,data)

if __name__=="__main__":
    unittest.main()
