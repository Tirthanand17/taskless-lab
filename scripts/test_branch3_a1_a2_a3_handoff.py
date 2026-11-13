"""Adversarial source->rights->storage handoff tests. No network or Google OAuth."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
import unittest

from scripts.branch3_discovery import build_report, mock_fixture
from scripts.branch3_rights_case_intake import build_rights_cases
from scripts.branch3_a1_a2_a3_handoff import (
    HandoffDenied, audit_handoff, public_discovery_shape
)
from scripts.branch3_media_storage_preflight import (
    POLICY, MANIFEST, CREATOR_PERMS, CHANNEL_STATE, read_json,
    BRANDING_ALLOWLIST, StorageDenied,
)

NOW = datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)
CASE_TIME = "2026-11-12T12:02:00Z"


def baseline() -> dict:
    discovery = build_report(mock_fixture(), category="gaming", mode="fixture",
                             query="", now=NOW, fixture=True)
    return {
        "discovery": discovery,
        "rights_cases": build_rights_cases(discovery, generated_at_utc=CASE_TIME),
        "storage_policy": read_json(POLICY),
        "storage_manifest": read_json(MANIFEST),
        "creator_registry": read_json(CREATOR_PERMS),
        "channel_state": read_json(CHANNEL_STATE),
        "public_paths": list(sorted(BRANDING_ALLOWLIST))
                        + ["branch3/creator_permissions.json"],
    }


class A123HandoffTests(unittest.TestCase):
    def test_valid_synthetic_handoff_is_still_quarantined(self):
        r = audit_handoff(**baseline())
        self.assertEqual(r["pending_review_cases"], 2)
        self.assertEqual(r["source_candidates_count"], 2)
        self.assertTrue(r["synthetic_test_fixture"])
        self.assertEqual(r["status"],
                         "CONSISTENT_PENDING_HUMAN_REVIEW_NO_LICENSE_NO_MEDIA")
        self.assertEqual(r["actual_creator_grants_verified"], 0)
        self.assertFalse(r["private_media_vault_provisioned"])
        for key in (
            "source_media_fetch_authorized",
            "original_editorial_release_authorized",
            "youtube_upload_authorized",
            "youtube_schedule_authorized",
            "youtube_publish_authorized",
        ):
            self.assertFalse(r[key], key)
        self.assertEqual(r["source_media_downloads"], 0)
        self.assertEqual(r["google_or_youtube_api_writes"], 0)
        self.assertEqual(len(r["source_report_sha256"]), 64)

    def test_a1_mutation_after_rights_case_generation_blocks(self):
        r = baseline()
        r["discovery"]["candidates"][0]["source_title"] = "Altered source"
        with self.assertRaises(HandoffDenied):
            audit_handoff(**r)

    def test_a2_mutation_or_forged_grant_blocks(self):
        mutations = (
            ("source_report_sha256", "0"*64),
            ("creator_permission_grants_issued_by_this_workflow", 1),
            ("release_enabled", True),
            ("media_downloads", 1),
            ("youtube_writes", 1),
        )
        for k, v in mutations:
            r = baseline()
            r["rights_cases"][k] = v
            with self.subTest(field=k), self.assertRaises(HandoffDenied):
                audit_handoff(**r)
        for field, value in (
            ("case_state", "RIGHTS_VERIFIED"),
            ("permission_evidence_sha256", "1"*64),
            ("actual_grant_document_available", True),
            ("media_acquisition_authorized", True),
            ("owner_clip_release_signed", True),
            ("youtube_upload_authorized", True),
        ):
            r = baseline()
            r["rights_cases"]["cases"][0][field] = value
            with self.subTest(case_field=field), self.assertRaises(HandoffDenied):
                audit_handoff(**r)

    def test_reject_missing_or_swapped_cases(self):
        for action in ("drop", "duplicate", "swap_sources"):
            r = baseline()
            cases = r["rights_cases"]["cases"]
            if action == "drop":
                cases.pop()
            elif action == "duplicate":
                cases.append(copy.deepcopy(cases[0]))
            else:
                cases[0]["source_video_id"] = cases[1]["source_video_id"]
            with self.subTest(action=action), self.assertRaises(HandoffDenied):
                audit_handoff(**r)

    def test_discovery_extra_private_fields_block_even_if_recomputed(self):
        for location in ("top", "candidate", "nested"):
            r = baseline()
            d = r["discovery"]
            if location == "top":
                d["refresh_token"] = "must never be in public metadata"
            elif location == "candidate":
                d["candidates"][0]["private_contract"] = "secret bytes"
            else:
                d["candidates"][0]["public_stats"]["private_contact"] = "no"
            r["rights_cases"] = build_rights_cases(d, generated_at_utc=CASE_TIME)
            with self.subTest(location=location), self.assertRaises(HandoffDenied):
                audit_handoff(**r)

    def test_cross_channel_or_unverified_creator_flags_block(self):
        for location, field, value in (
            ("discovery", "channel_id", "UCCcL9Q_jqVq6LJmnYUSAFZA"),
            ("discovery", "channel_handle", "@FlowMinuteLab"),
            ("discovery", "upstream_clip_rights_human_review_required", False),
            ("rights_cases", "target_channel_id", "UCCcL9Q_jqVq6LJmnYUSAFZA"),
        ):
            r = baseline()
            r[location][field] = value
            with self.subTest(field=field), self.assertRaises(HandoffDenied):
                audit_handoff(**r)

    def test_review_cases_before_discovery_or_too_old_block(self):
        for timestamp in ("2026-11-12T11:59:00Z", "2026-11-14T12:02:00Z",
                          "2026-11-12T12:02:00+00:00", "bad"):
            r = baseline()
            r["rights_cases"]["generated_at_utc"] = timestamp
            with self.subTest(timestamp=timestamp), self.assertRaises(HandoffDenied):
                audit_handoff(**r)

    def test_forged_storage_or_allowlist_blocks(self):
        scenarios = (
            ("storage_policy", "media_fetch_enabled", True),
            ("storage_policy", "private_vault_owner_approved", True),
            ("storage_policy", "private_vault_repository", "Tirthanand17/clivox-vault"),
            ("storage_manifest", "status", "RIGHTS_VERIFIED"),
        )
        for part, key, value in scenarios:
            r = baseline()
            r[part][key] = value
            with self.subTest(field=key), self.assertRaises(StorageDenied):
                audit_handoff(**r)
        r = baseline()
        r["creator_registry"]["creators"] = [{"creator_id": "fake"}]
        with self.assertRaises(StorageDenied):
            audit_handoff(**r)
        r = baseline()
        r["public_paths"].append("branch3/source_media.mp4")
        with self.assertRaises(StorageDenied):
            audit_handoff(**r)

    def test_empty_candidate_report_allowed_no_grant(self):
        r = baseline()
        r["discovery"]["candidates"] = []
        r["rights_cases"] = build_rights_cases(
            r["discovery"], generated_at_utc=CASE_TIME
        )
        result = audit_handoff(**r)
        self.assertEqual(result["pending_review_cases"], 0)
        self.assertFalse(result["youtube_upload_authorized"])

    def test_no_writes_ever_on_success(self):
        r = audit_handoff(**baseline())
        payload = json.dumps(r)
        self.assertNotIn("refresh_token", payload)
        self.assertNotIn("private_contract", payload)
        self.assertNotIn("access_token", payload)
        self.assertNotIn("SOURCE_ELIGIBLE", payload)


if __name__ == "__main__":
    unittest.main()
