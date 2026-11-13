"""Prove actual private bootstrap cannot be forged into CLIVOX production approval."""
from __future__ import annotations

import copy
import json
import unittest

from scripts.branch3_owner_closure_gate import (
    BOOTSTRAP, TRACKER, ARCH, CREATORS, RELEASE, A2_POLICY, A8_POLICY,
    ClosureDenied, check_closed_state, read_json
)


def inputs():
    return {
        "bootstrap":read_json(BOOTSTRAP),
        "tracker":read_json(TRACKER),
        "arch":read_json(ARCH),
        "creators":read_json(CREATORS),
        "release":read_json(RELEASE),
        "a2_policy":read_json(A2_POLICY),
        "a8_policy":read_json(A8_POLICY)
    }


class OwnerBootstrapClosureTests(unittest.TestCase):
    def test_verified_real_infrastructure_never_licenses_or_publishes(self):
        result=check_closed_state(**inputs())
        self.assertTrue(result["private_metadata_repository_provisioned"])
        self.assertTrue(result["empty_a2_revocation_journal_bootstrapped"])
        self.assertTrue(result["empty_a8_upload_attempt_ledger_bootstrapped"])
        self.assertFalse(result["private_media_vault_owner_approval"])
        self.assertFalse(result["nonrollbackable_external_anchor_proven"])
        self.assertFalse(result["dedicated_clivox_google_oauth_connected"])
        self.assertFalse(result["real_youtube_inventory_reconciled"])
        self.assertEqual(result["rights_holder_grants_authenticated"],0)
        self.assertEqual(result["actual_external_api_calls"],0)
        self.assertFalse(result["youtube_upload_authorized"])
        self.assertFalse(result["youtube_schedule_authorized"])
        self.assertFalse(result["youtube_publish_authorized"])
        self.assertNotIn("clivox-private-vault",json.dumps(result))
        self.assertEqual(len(result["next_human_dependencies"]),7)

    def test_public_bootstrap_can_never_assert_real_permissions(self):
        for field in (
            "approved_for_private_media_storage","approved_for_source_download",
            "approved_for_real_ledger_writes","approved_for_youtube_upload",
            "approved_for_youtube_schedule","approved_for_youtube_publish"
        ):
            data=inputs()
            data["bootstrap"][field]=True
            with self.subTest(field=field),self.assertRaises(ClosureDenied):
                check_closed_state(**data)

    def test_unverified_keys_remote_anchor_and_owner_credentials_denied(self):
        for field in (
            "production_key_independently_enrolled",
            "nonrollbackable_external_anchor_exists",
            "authenticated_live_cross_run_writer_exists"
        ):
            data=inputs();data["bootstrap"]["genesis_ledgers"][field]=True
            with self.subTest(field=field),self.assertRaises(ClosureDenied):
                check_closed_state(**data)
        for field in (
            "genuine_clivox_google_oauth_credentials_configured",
            "real_youtube_upload_inventory_readback_executed",
            "live_publication_enabled"
        ):
            data=inputs();data["bootstrap"]["channel"][field]=True
            with self.subTest(field=field),self.assertRaises(ClosureDenied):
                check_closed_state(**data)
        data=inputs()
        data["bootstrap"]["channel"]["creator_issued_commercial_licenses_verified"]=1
        with self.assertRaises(ClosureDenied):
            check_closed_state(**data)

    def test_env_or_private_repo_privacy_downgrade_denied(self):
        for name in ("clivox-vault-readonly","clivox-release"):
            data=inputs()
            data["bootstrap"]["controller_environments"][name]["admin_bypass_disabled_verified"]=False
            with self.subTest(name=name),self.assertRaises(ClosureDenied):
                check_closed_state(**data)
            data=inputs()
            data["bootstrap"]["controller_environments"][name]["environment_secret_count_at_readback"]=1
            with self.subTest(name=name),self.assertRaises(ClosureDenied):
                check_closed_state(**data)
        data=inputs()
        data["bootstrap"]["control_repository"]["privacy_and_owner_admin_checked_live"]=False
        with self.assertRaises(ClosureDenied):
            check_closed_state(**data)
        data=inputs()
        data["bootstrap"]["control_repository"]["actual_owner_approved_licensed_media_storage"]=True
        with self.assertRaises(ClosureDenied):
            check_closed_state(**data)

    def test_other_project_tokens_and_real_release_forgery_denied(self):
        for location,key,value in (
            ("tracker","publishing_enabled",True),
            ("tracker","creator_licenses_verified",1),
            ("tracker","github_private_media_vault_provisioned",True),
            ("tracker","branch1_and_branch2_paused",False),
            ("release","real_signed_releases",1),
            ("release","youtube_write_enabled",True),
            ("a2_policy","remote_github_get_or_put_enabled",True),
            ("a8_policy","cross_runner_durable_ledger_verified",True),
            ("a8_policy","youtube_api_writes_enabled",True)
        ):
            data=inputs();data[location][key]=value
            with self.subTest(location=location,key=key),self.assertRaises(ClosureDenied):
                check_closed_state(**data)
        data=inputs()
        data["arch"]["isolation"]["reuse_flowminute_youtube_tokens"]=True
        with self.assertRaises(ClosureDenied):
            check_closed_state(**data)
        data=inputs()
        data["creators"]["creators"]=[{"fake":"consent"}]
        with self.assertRaises(ClosureDenied):
            check_closed_state(**data)

    def test_not_a_live_validation_claim(self):
        result=check_closed_state(**inputs())
        self.assertTrue(result["external_provisioning_record_is_historical_not_live_verified"])
        self.assertFalse(result["first_licensed_pilot_completed"])
        self.assertEqual(result["status"],
                         "BLOCKED_MISSING_REAL_RIGHTS_OWNER_AUTH_AND_PRODUCTION_EVIDENCE")


if __name__=="__main__":
    unittest.main()
