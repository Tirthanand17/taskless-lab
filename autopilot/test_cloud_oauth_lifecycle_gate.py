"""Offline no-secret cloud OAuth screen regression tests."""
from __future__ import annotations
import datetime as dt
import json
import unittest

from autopilot.cloud_oauth_lifecycle_gate import (
    OAuthScreenError, READONLY_SCOPE, UPLOAD_SCOPE, CHANNEL_ID, screen_claims,
)

NOW = dt.datetime(2026, 10, 19, 12, 0, tzinfo=dt.timezone.utc)


def claims(**changes):
    case = {
        "channel_id": CHANNEL_ID,
        "oauth_app_mode": "production",
        "token_kind": "user_oauth",
        "access_expiry_utc": "2026-10-19T13:00:00Z",
        "refresh_observed_utc": "2026-10-19T11:55:00Z",
        "channel_observed_utc": "2026-10-19T11:50:00Z",
        "secret_store_kind": "provider_managed_encrypted",
        "scope_set": [READONLY_SCOPE],
        "owner_connection_approved": True,
        "refresh_observation_success": True,
        "channel_observation_success": True,
        "durable_private_storage_confirmed": True,
        "isolated_cloud_runtime_confirmed": True,
        "zero_overage_enforced": True,
    }
    case.update(changes)
    return case


def scan(*, purpose="read_only", **changes):
    return screen_claims(claims(**changes), purpose=purpose, now=NOW)


class OAuthLifecycleGateTests(unittest.TestCase):
    def test_only_a_staging_readonly_proposal_even_when_all_claims_pass(self):
        r = scan()
        self.assertTrue(r["claim_screen_pass"])
        self.assertEqual(r["status"], "ELIGIBLE_FOR_LIVE_READONLY_PROBE")
        self.assertFalse(r["actual_provider_authenticated"])
        self.assertFalse(r["cloud_autopilot_ready"])
        self.assertFalse(r["unattended_upload_authorized"])
        self.assertFalse(r["unattended_scheduling_authorized"])
        self.assertEqual(len(r["mandatory_external_evidence"]), 4)

    def test_test_mode_must_be_blocked_despite_valid_access_token(self):
        r = scan(oauth_app_mode="testing")
        self.assertEqual(r["status"], "BLOCKED")
        self.assertIn("OAUTH_TEST_MODE_OR_UNKNOWN_REFRESH_LIFETIME", r["reasons"])

    def test_wrong_channel_and_service_account_rejected(self):
        r = scan(channel_id="UCnot_the_right_channel", token_kind="service_account")
        self.assertIn("WRONG_CHANNEL", r["reasons"])
        self.assertIn("NOT_OWNER_DELEGATED_OAUTH", r["reasons"])

    def test_missing_readonly_scope_rejected(self):
        r = scan(scope_set=[UPLOAD_SCOPE])
        self.assertIn("PURPOSE_SCOPE_MISSING", r["reasons"])

    def test_private_upload_requires_upload_scope_but_never_authorizes_upload(self):
        missing = scan(purpose="private_upload_pilot")
        self.assertFalse(missing["claim_screen_pass"])
        r = scan(purpose="private_upload_pilot", scope_set=[UPLOAD_SCOPE])
        self.assertTrue(r["claim_screen_pass"])
        self.assertEqual(r["status"], "ELIGIBLE_FOR_OWNER_APPROVED_PRIVATE_PILOT_REVIEW")
        self.assertFalse(r["unattended_upload_authorized"])

    def test_refresh_claim_failure_blocks(self):
        r = scan(refresh_observation_success=False)
        self.assertIn("OAUTH_REFRESH_HEALTH_UNVERIFIED", r["reasons"])

    def test_wrong_secret_storage_denied(self):
        for v in ("github_public_runner", "local_laptop_env", "unknown"):
            with self.subTest(v=v):
                self.assertIn("PROTECTED_CLOUD_SECRET_STORE_UNVERIFIED",
                              scan(secret_store_kind=v)["reasons"])

    def test_no_persistent_private_media_blocks(self):
        r = scan(durable_private_storage_confirmed=False)
        self.assertIn("PRIVATE_MEDIA_STORAGE_UNVERIFIED", r["reasons"])

    def test_budget_must_have_hard_zero_overage_limit(self):
        r = scan(zero_overage_enforced=False)
        self.assertIn("ZERO_BUDGET_HARD_CAP_UNVERIFIED", r["reasons"])

    def test_owner_connection_cannot_be_inferred(self):
        r = scan(owner_connection_approved=False)
        self.assertIn("OWNER_CONNECTION_NOT_APPROVED", r["reasons"])

    def test_laptop_only_not_cloud_is_denied(self):
        r = scan(isolated_cloud_runtime_confirmed=False)
        self.assertIn("LAPTOP_INDEPENDENT_ISOLATION_UNVERIFIED", r["reasons"])

    def test_near_expiry_and_expired_access_are_not_operational(self):
        for when in ("2026-10-19T11:59:59Z", "2026-10-19T12:10:00Z", "2026-10-19T12:20:00Z"):
            with self.subTest(when=when):
                self.assertIn("ACCESS_TOKEN_TOO_OLD_FOR_OPERATION", scan(access_expiry_utc=when)["reasons"])

    def test_observation_staleness_and_future_are_rejected(self):
        a = scan(refresh_observed_utc="2026-10-18T11:59:59Z")
        self.assertIn("REFRESH_OBSERVATION_OUTDATED_OR_FUTURE", a["reasons"])
        b = scan(channel_observed_utc="2026-10-19T12:00:01Z")
        self.assertIn("CHANNEL_OBSERVATION_OUTDATED_OR_FUTURE", b["reasons"])

    def test_incorrect_timestamp_and_naive_clock_fail_cleanly(self):
        for bad in ("2026-10-19T13:00:00+05:30", "2026-13-19T13:00:00Z", "tomorrow", None):
            with self.subTest(value=bad):
                with self.assertRaises(OAuthScreenError):
                    scan(access_expiry_utc=bad)
        with self.assertRaises(OAuthScreenError):
            screen_claims(claims(), purpose="read_only", now=dt.datetime(2026, 10, 19, 12))

    def test_unknown_purpose_or_extra_credential_fields_fail(self):
        with self.assertRaises(OAuthScreenError):
            scan(purpose="publish_public")
        with self.assertRaises(OAuthScreenError):
            scan(access_token="should_not_be_here")
        with self.assertRaises(OAuthScreenError):
            scan(refresh_token="should_not_be_here")

    def test_unexpected_field_and_non_bool_denied(self):
        for kwargs in ({"owner_connection_approved": 1}, {"scope_set": [READONLY_SCOPE, READONLY_SCOPE]},
                       {"scope_set": [READONLY_SCOPE, 3]}, {"channel_id": None},
                       {"refresh_observation_success": "true"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(OAuthScreenError):
                scan(**kwargs)

    def test_no_secret_material_in_report(self):
        r = scan(scope_set=[READONLY_SCOPE, UPLOAD_SCOPE], token_kind="user_oauth")
        dumped = json.dumps(r)
        self.assertNotIn("Bearer", dumped)
        self.assertNotIn("refresh_token", dumped)
        self.assertNotIn("access_token", dumped)
        self.assertFalse(r["secret_values_in_report"])

    def test_unknown_channel_probe_refused(self):
        r = scan(channel_observation_success=False)
        self.assertIn("CHANNEL_OWNER_LOOKUP_UNVERIFIED", r["reasons"])


if __name__ == "__main__":
    unittest.main()
