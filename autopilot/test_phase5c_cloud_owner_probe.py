"""No-network Phase 5C credential lease/owner readback adversarial cases."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import unittest
from unittest.mock import patch

from autopilot.cloud_oauth_lifecycle_gate import CHANNEL_ID, READONLY_SCOPE
from autopilot.owner_youtube_readonly_monitor import OwnerYouTubeReader
from autopilot.phase5c_cloud_owner_probe import inspect_owner_readonly

NOW = datetime(2026, 10, 19, 13, 0, tzinfo=timezone.utc)
DAY = "2026-10-20"
IDS = {"short_morning": "DUd_Gb9yo_g", "long": "ABCDEFGHIJK", "short_evening": "zg8YD4_iVbI"}
TIMES = {"short_morning": "2026-10-20T05:30:00Z",
         "long": "2026-10-20T10:30:00Z", "short_evening": "2026-10-20T15:00:00Z"}
SECRET = "TEST-ONLY-TOKEN-NEVER-REPORT-123456789"


def manifest(missing_long=True):
    return {s: {"video_id": None if missing_long and s == "long" else id_,
                "title": "video " + s} for s, id_ in IDS.items()}


def claim(**kwargs):
    item = {
        "channel_id": CHANNEL_ID,
        "oauth_app_mode": "production",
        "token_kind": "user_oauth",
        "access_expiry_utc": "2026-10-19T14:00:00Z",
        "refresh_observed_utc": "2026-10-19T12:50:00Z",
        "channel_observed_utc": "2026-10-19T12:50:00Z",
        "secret_store_kind": "provider_managed_encrypted",
        "scope_set": [READONLY_SCOPE],
        "owner_connection_approved": True,
        "refresh_observation_success": True,
        "channel_observation_success": True,
        "durable_private_storage_confirmed": True,
        "isolated_cloud_runtime_confirmed": True,
        "zero_overage_enforced": True,
    }
    item.update(kwargs)
    return item


class MockProvider:
    def __init__(self, token=SECRET, failure=False):
        self.borrowed = 0
        self.released = 0
        self.requests = []
        self.token = token
        self.failure = failure

    @contextmanager
    def borrow_readonly(self, *, channel_id, scope):
        self.borrowed += 1
        self.requests.append((channel_id, scope))
        if self.failure:
            raise RuntimeError("VERY-SECRET " + SECRET)
        try:
            yield self.token
        finally:
            self.released += 1


class FixtureReader(OwnerYouTubeReader):
    def __init__(self, access_token):
        super().__init__(access_token)
        self.requests = []
        self.bad_owner = False
        self.remote_failure = False

    def _get(self, path, params):
        self.requests.append((path, dict(params)))
        if self.remote_failure:
            raise RuntimeError("BEARER " + SECRET)
        if path == "channels":
            return {"items": [{"id": "UCwrong" if self.bad_owner else CHANNEL_ID}]}
        slot = next(s for s, vid in IDS.items() if vid == params["id"])
        return {
            "items": [
                {
                    "id": params["id"],
                    "snippet": {"title": "video " + slot, "channelId": CHANNEL_ID},
                    "status": {"privacyStatus": "private", "uploadStatus": "processed",
                               "publishAt": TIMES[slot]},
                    "processingDetails": {"processingStatus": "succeeded"},
                }
            ]
        }


class CloudOwnerIntegrationTests(unittest.TestCase):
    def probe(self, provider=None, *, planned=None, sanitized_claims=None, now=NOW):
        provider = provider if provider is not None else MockProvider()
        with patch("autopilot.phase5c_cloud_owner_probe.OwnerYouTubeReader",
                   side_effect=FixtureReader):
            r = inspect_owner_readonly(day=DAY, planned=planned if planned is not None else manifest(),
                                       sanitized_claims=sanitized_claims if sanitized_claims is not None else claim(),
                                       provider=provider, now=now)
        return r, provider

    def test_valid_two_short_owner_read_does_not_promote_or_publish(self):
        result, p = self.probe()
        self.assertEqual(result["state"], "OWNER_READ_OBSERVED_UNATTESTED")
        self.assertEqual(result["platform_state_count"], 2)
        self.assertEqual(result["slots"][1]["state"], "MISSING_VIDEO")
        self.assertEqual((p.borrowed, p.released), (1, 1))
        self.assertEqual(p.requests, [(CHANNEL_ID, READONLY_SCOPE)])
        self.assertFalse(result["production_autopilot_ready"])
        self.assertFalse(result["production_upload_authorized"])
        self.assertEqual(result["mutating_youtube_requests"], 0)
        self.assertNotIn(SECRET, json.dumps(result))
        self.assertNotIn(IDS["short_morning"], json.dumps(result))

    def test_complete_three_lane_read_remains_unattested(self):
        result, provider = self.probe(planned=manifest(False))
        self.assertEqual(result["platform_state_count"], 3)
        self.assertFalse(result["provider_collector_enrolled"])
        self.assertFalse(result["live_cloud_deployment_verified"])
        self.assertEqual(provider.released, 1)

    def test_no_secret_lease_when_oauth_testing_blocked(self):
        p = MockProvider()
        r, _ = self.probe(p, sanitized_claims=claim(oauth_app_mode="testing"))
        self.assertEqual(r["state"], "HOLD_UNVERIFIED")
        self.assertEqual(p.borrowed, 0)

    def test_no_secret_lease_when_zero_overage_unknown(self):
        p = MockProvider()
        r, _ = self.probe(p, sanitized_claims=claim(zero_overage_enforced=False))
        self.assertIn("ZERO_BUDGET_HARD_CAP_UNVERIFIED", r["claim_reasons"])
        self.assertEqual(p.borrowed, 0)

    def test_no_secret_lease_when_expired(self):
        p = MockProvider()
        r, _ = self.probe(p, sanitized_claims=claim(access_expiry_utc="2026-10-19T13:10:00Z"))
        self.assertIn("ACCESS_TOKEN_TOO_OLD_FOR_OPERATION", r["claim_reasons"])
        self.assertEqual(p.borrowed, 0)

    def test_malformed_claims_denied_before_lease(self):
        p = MockProvider()
        r, _ = self.probe(p, sanitized_claims=claim(refresh_token=SECRET))
        self.assertEqual(r["reason"], "INVALID_SANITIZED_CLAIMS")
        self.assertEqual(p.borrowed, 0)
        self.assertNotIn(SECRET, json.dumps(r))

    def test_manifest_duplicate_refused_before_lease(self):
        p = MockProvider()
        m = manifest(False)
        m["long"]["video_id"] = m["short_morning"]["video_id"]
        r, _ = self.probe(p, planned=m)
        self.assertEqual(r["reason"], "DUPLICATE_VIDEO_ID")
        self.assertEqual(p.borrowed, 0)

    def test_manifest_unexpected_field_refused_before_lease(self):
        p = MockProvider()
        m = manifest()
        m["long"]["uploader_secret"] = SECRET
        r, _ = self.probe(p, planned=m)
        self.assertEqual(r["reason"], "UNSAFE_RELEASE_MANIFEST")
        self.assertEqual(p.borrowed, 0)
        self.assertNotIn(SECRET, json.dumps(r))

    def test_wrong_day_refused_before_lease(self):
        p = MockProvider()
        with patch("autopilot.phase5c_cloud_owner_probe.OwnerYouTubeReader", side_effect=FixtureReader):
            r = inspect_owner_readonly(day="tomorrow", planned=manifest(), sanitized_claims=claim(),
                                       provider=p, now=NOW)
        self.assertEqual(r["reason"], "INVALID_RELEASE_DAY")
        self.assertEqual(p.borrowed, 0)

    def test_credential_provider_failure_never_leaks_dynamic_error(self):
        r, p = self.probe(MockProvider(failure=True))
        self.assertEqual(r["reason"], "PROVIDER_OR_OWNER_READ_FAILED")
        self.assertNotIn(SECRET, json.dumps(r))

    def test_nonstring_ephemeral_token_refused_and_released(self):
        r, p = self.probe(MockProvider(token=b"not-allowed"))
        self.assertEqual(r["reason"], "INVALID_EPHEMERAL_ACCESS_TOKEN")
        self.assertEqual((p.borrowed, p.released), (1, 1))

    def test_invalid_token_released_and_redacted(self):
        r, p = self.probe(MockProvider(token="invalid"))
        self.assertEqual(r["reason"], "PROVIDER_OR_OWNER_READ_FAILED")
        self.assertEqual(p.released, 1)

    def test_reader_raises_secret_and_context_still_releases(self):
        class ExplodingReader(FixtureReader):
            def _get(self, path, params):
                raise RuntimeError("LEAK " + SECRET)
        p = MockProvider()
        with patch("autopilot.phase5c_cloud_owner_probe.OwnerYouTubeReader", side_effect=ExplodingReader):
            r = inspect_owner_readonly(day=DAY, planned=manifest(), sanitized_claims=claim(),
                                       provider=p, now=NOW)
        self.assertEqual(r["state"], "HOLD_UNVERIFIED")
        self.assertFalse(r["owner_api_observation"])
        self.assertNotIn(SECRET, json.dumps(r))
        self.assertEqual(p.released, 1)

    def test_missing_lease_function_blocked(self):
        r, _ = self.probe(object())
        self.assertEqual(r["reason"], "PROVIDER_CREDENTIAL_LEASE_UNAVAILABLE")

    def test_naive_clock_refused_without_leasing(self):
        p = MockProvider()
        with self.assertRaisesRegex(ValueError, "AWARE_TIME_REQUIRED"):
            self.probe(p, now=datetime(2026, 10, 19, 13, 0))
        self.assertEqual(p.borrowed, 0)

    def test_token_and_full_private_video_metadata_never_emitted(self):
        r, _ = self.probe()
        data=json.dumps(r)
        for forbidden in (SECRET, "access_token", "refresh_token", "client_secret",
                          "video short_morning", IDS["short_evening"]):
            self.assertNotIn(forbidden, data)

    def test_short_circuit_without_any_cloud_worker_approval(self):
        p = MockProvider()
        r, _ = self.probe(p, sanitized_claims=claim(isolated_cloud_runtime_confirmed=False))
        self.assertEqual(r["state"], "HOLD_UNVERIFIED")
        self.assertEqual(p.borrowed, 0)

    def test_token_lease_has_no_refresh_or_write_abilities(self):
        p = MockProvider()
        r, _ = self.probe(p)
        self.assertIn("mutating_youtube_requests", r)
        self.assertEqual(r["mutating_youtube_requests"], 0)
        self.assertFalse(hasattr(p, "upload_video"))
        self.assertFalse(hasattr(p, "refresh_token"))


if __name__ == "__main__":
    unittest.main()
