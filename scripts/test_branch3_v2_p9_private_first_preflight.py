"""P9 offline negative tests: source-free dry-run can NEVER authorize upload."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.branch3_v2_p9_private_first_preflight import (
    CHANNEL, DOMAIN, ID, P9Denied, OUTCOMES, TEMPLATE, PUBLIC_REPORT_FIELDS,
    _closed_live_policies, _read_unsigned, dryrun_decision,
    production_upload_or_schedule, run_source_free_preflight,
    synthetic_attempt_fingerprint, validate_inert_template,
    validate_review_bridge,
)
from scripts.branch3_v2_p8_synthetic_unsigned_review import (
    EDL_FILE, QA_FILE, REVIEW_FILE, OUTPUT_NAME, make_unsigned_packet,
)
from scripts.branch3_a8_private_first_dryrun import (
    DryRunBlocked, perform_upload_or_schedule,
    reserve_attempt_preview, reconcile_ambiguous_attempt,
)
from scripts.branch3_a6_signed_release import ReleaseBlocked, production_release
from scripts.test_branch3_v2_p8_synthetic_unsigned_review import (
    storyboard, p7_report,
)


def packet(video_bytes: bytes = b"synthetic source-free test" * 20):
    return make_unsigned_packet(
        video_sha=hashlib.sha256(video_bytes).hexdigest(),
        video_bytes=len(video_bytes), edl=storyboard(),
        p7_report=p7_report(),
    )


def scratch_fixture(root: Path, *, contents: bytes) -> dict:
    (root / OUTPUT_NAME).write_bytes(contents)
    (root / EDL_FILE).write_text(json.dumps(storyboard()), encoding="utf-8")
    (root / QA_FILE).write_text(json.dumps(p7_report()), encoding="utf-8")
    p = packet(contents)
    (root / REVIEW_FILE).write_text(json.dumps(p), encoding="utf-8")
    return p


class P9PrivateFirstTests(unittest.TestCase):
    def test_authentic_policies_do_not_enable_uploads(self):
        _closed_live_policies()
        with self.assertRaises(P9Denied):
            production_upload_or_schedule()
        with self.assertRaises(DryRunBlocked):
            perform_upload_or_schedule()
        with self.assertRaises(ReleaseBlocked):
            production_release()

    def test_exact_inert_plan_requires_explicit_private_and_no_schedule(self):
        result = validate_inert_template(TEMPLATE)
        self.assertEqual(result["channel_id"], CHANNEL)
        self.assertEqual(result["api_concept"], "videos.insert")
        self.assertEqual(result["status"]["privacyStatus"], "private")
        self.assertIsNone(result["status"]["publishAt"])
        self.assertFalse(result["real_youtube_write_allowed"])
        self.assertFalse(result["ready_to_send"])
        self.assertFalse(result["upload_session_created"])
        self.assertEqual(result["mode"], "INERT_MODEL_NOT_HTTP_REQUEST")
        for fragment in ("https://", "Authorization", "Bearer ",
                         "access_token", "videoId"):
            self.assertNotIn(fragment, json.dumps(result))

    def test_missing_private_public_unlisted_and_publish_timestamp_denied(self):
        mutations = (
            ("privacyStatus", None), ("privacyStatus", "public"),
            ("privacyStatus", "unlisted"), ("privacyStatus", "Private"),
            ("publishAt", "2026-11-21T12:00:00Z"),
        )
        for key, value in mutations:
            model = copy.deepcopy(TEMPLATE)
            model["status"][key] = value
            with self.subTest(key=key, val=value), self.assertRaises(P9Denied):
                validate_inert_template(model)
        model = copy.deepcopy(TEMPLATE)
        del model["status"]["privacyStatus"]
        with self.assertRaises(P9Denied):
            validate_inert_template(model)
        model = copy.deepcopy(TEMPLATE)
        model["status"]["visibilityByDefault"] = "public"
        with self.assertRaises(P9Denied):
            validate_inert_template(model)

    def test_cannot_promote_upload_or_add_oauth_or_cross_channel(self):
        mutations = [
            ("channel_id", "UCCcL9Q_jqVq6LJmnYUSAFZA"),
            ("real_youtube_write_allowed", True),
            ("ready_to_send", True),
            ("upload_session_created", True),
            ("mode", "HTTP_INSERT_NOW"),
            ("source_scope", "LICENSED_CREATOR_FOOTAGE"),
        ]
        for field, value in mutations:
            model = copy.deepcopy(TEMPLATE)
            model[field] = value
            with self.subTest(field=field), self.assertRaises(P9Denied):
                validate_inert_template(model)
        for extra in (
            "oauth_refresh_token", "headers", "url", "access_token",
            "query", "onBehalfOfContentOwner", "media_upload_path",
            "approved_creator_grant", "owner_signed", "video_id",
        ):
            model = copy.deepcopy(TEMPLATE)
            model[extra] = "external"
            with self.subTest(field=extra), self.assertRaises(P9Denied):
                validate_inert_template(model)

    def test_attempt_fingerprint_is_repeatable_and_never_rights_grant(self):
        p = packet()
        first = synthetic_attempt_fingerprint(p)
        self.assertEqual(first, synthetic_attempt_fingerprint(p))
        self.assertRegex(first, r"^[a-f0-9]{64}$")
        self.assertNotEqual(first, p["exact_synthetic_video_sha256"])
        self.assertTrue(DOMAIN.startswith(b"CLIVOX-V2-P9-UNAUTHORIZED"))
        changed = copy.deepcopy(p)
        changed["exact_p6_storyboard_sha256"] = "1" * 64
        self.assertNotEqual(first, synthetic_attempt_fingerprint(changed))
        changed["exact_p6_storyboard_sha256"] = p["exact_p6_storyboard_sha256"]
        changed["exact_synthetic_video_sha256"] = "2" * 64
        self.assertNotEqual(first, synthetic_attempt_fingerprint(changed))
        for fld, val in (
            ("channel_id", "OTHER"),
            ("owner_release_signed", True),
            ("youtube_upload_authorized", True),
            ("review_state", "OWNER_APPROVED"),
        ):
            changed = copy.deepcopy(p)
            changed[fld] = val
            with self.subTest(field=fld), self.assertRaises(P9Denied):
                synthetic_attempt_fingerprint(changed)

    def test_no_attempt_duplicate_and_unknown_outcomes_all_hold(self):
        p = packet()
        self.assertEqual(OUTCOMES, {
            "NO_ATTEMPT", "DUPLICATE_LOCAL_PREVIEW",
            "UNKNOWN_REMOTE_COMMIT_PREVIEW",
        })
        for outcome in sorted(OUTCOMES):
            report = dryrun_decision(packet=p, outcome=outcome)
            self.assertEqual(set(report), PUBLIC_REPORT_FIELDS)
            self.assertEqual(report["stage"],
                             "CLIVOX_V2_P9_PRIVATE_FIRST_INERT_PREFLIGHT_ONLY")
            self.assertEqual(report["channel_id"], CHANNEL)
            self.assertTrue(report["p8_unsigned_packet_bound_to_exact_video"])
            self.assertTrue(report["inert_private_first_template_validated"])
            self.assertFalse(report["owner_signature_independently_verified"])
            self.assertFalse(report["creator_commercial_rights_verified"])
            self.assertFalse(report["clivox_upload_oauth_verified"])
            self.assertFalse(report["durable_atomic_attempt_reservation_verified"])
            self.assertFalse(report["real_remote_inventory_reconciled"])
            self.assertFalse(report["automatic_retry_enabled"])
            self.assertFalse(report["resume_session_created"])
            self.assertEqual(report["remote_http_calls"], 0)
            self.assertEqual(report["actual_youtube_uploads"], 0)
            self.assertFalse(report["youtube_upload_authorized"])
            self.assertFalse(report["youtube_schedule_authorized"])
            self.assertFalse(report["youtube_publish_authorized"])
            self.assertFalse(report["real_p9_milestone_complete"])
            self.assertEqual(report["dryrun_duplicate_detected"],
                             outcome != "NO_ATTEMPT")
            self.assertEqual(report["dryrun_remote_uncertainty_quarantined"],
                             outcome == "UNKNOWN_REMOTE_COMMIT_PREVIEW")
            self.assertNotIn(synthetic_attempt_fingerprint(p), json.dumps(report))

    def test_invalid_outcomes_never_create_request(self):
        for value in ("UPLOAD_NOW", "PUBLIC", "ALLOW_RETRY", None, True,
                      "REMOTE_INVENTORY_EMPTY", "", []):
            with self.subTest(value=value), self.assertRaises(P9Denied):
                dryrun_decision(packet=packet(), outcome=value)

    def test_existing_a8_reservation_previews_hold_for_duplicate_unknown(self):
        fp = synthetic_attempt_fingerprint(packet())
        first = reserve_attempt_preview([], fp)
        self.assertEqual(first["decision"], "DRY_RUN_ONLY_KEY_NOT_PRESENT")
        self.assertFalse(first["upload_authorized"])
        duplicate = reserve_attempt_preview(
            [{"key": fp, "status": "ATTEMPT_RESERVED"}], fp)
        self.assertEqual(duplicate["decision"],
                         "BLOCK_DUPLICATE_OR_AMBIGUOUS_ATTEMPT")
        self.assertFalse(duplicate["automatic_retry_allowed"])
        for asserted_remote in (True, False):
            out = reconcile_ambiguous_attempt(
                attempt_status="UNKNOWN_REMOTE_STATE_RECONCILE",
                remote_readback_verified=asserted_remote)
            self.assertFalse(out["upload_authorized"])
            self.assertFalse(out["blind_retry_allowed"])

    def test_exact_video_and_draft_hash_binding_rejects_forgery(self):
        original = b"locally generated source-only fixture" * 20
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            known = scratch_fixture(root, contents=original)
            self.assertEqual(validate_review_bridge(scratch=root), known)
            (root / OUTPUT_NAME).write_bytes(
                b"x" + original[1:])
            with self.assertRaises(P9Denied):
                validate_review_bridge(scratch=root)
            (root / OUTPUT_NAME).write_bytes(original)
            p = copy.deepcopy(known)
            p["detached_signature_base64"] = "AAAAAAAA"
            (root / REVIEW_FILE).write_text(json.dumps(p), encoding="utf-8")
            with self.assertRaises(P9Denied):
                validate_review_bridge(scratch=root)

    def test_owner_and_rights_fields_cannot_be_forged(self):
        original = b"generated original only" * 30
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = scratch_fixture(root, contents=original)
            for field, value in (
                ("owner_public_key_independently_enrolled", True),
                ("human_owner_identity_verified", True),
                ("owner_release_signed", True),
                ("youtube_upload_authorized", True),
                ("youtube_publish_authorized", True),
                ("real_rights_freshness_verified", True),
                ("real_creator_licenses", 1),
                ("source_rights_evidence_sha256", "a" * 64),
            ):
                modified = copy.deepcopy(baseline)
                modified[field] = value
                (root / REVIEW_FILE).write_text(
                    json.dumps(modified), encoding="utf-8")
                with self.subTest(field=field), self.assertRaises(P9Denied):
                    validate_review_bridge(scratch=root)

    def test_symlink_oversized_or_missing_unsigned_packet_denied(self):
        original = b"generated original only" * 30
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            scratch_fixture(root, contents=original)
            self.assertEqual(_read_unsigned(root)["owner_release_signed"], False)
            path = root / REVIEW_FILE
            path.unlink()
            path.symlink_to(root / EDL_FILE)
            with self.assertRaises(P9Denied):
                _read_unsigned(root)
            path.unlink()
            path.write_text("x" * 50_000, encoding="utf-8")
            with self.assertRaises(P9Denied):
                _read_unsigned(root)
            path.unlink()
            with self.assertRaises(P9Denied):
                _read_unsigned(root)

    def test_closed_real_policy_fails_before_creating_dryrun(self):
        with patch(
            "scripts.branch3_v2_p9_private_first_preflight.closed_release_boundary",
            side_effect=P9Denied("A6_REAL_RELEASE_MISSING"),
        ):
            with self.assertRaises(P9Denied):
                _closed_live_policies()
        with patch(
            "scripts.branch3_v2_p9_private_first_preflight.synthetic_fixture_report",
            return_value={
                "channel_id": CHANNEL,
                "fixture_identity_check_passed": True,
                "actual_clivox_oauth_verified": True,
                "actual_api_requests": 1,
                "upload_authorized": True, "publish_authorized": True,
            },
        ):
            with self.assertRaises(P9Denied):
                _closed_live_policies()

    def test_missing_source_is_not_substituted_with_test_plan(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises((P9Denied, ValueError)):
                run_source_free_preflight(scratch=root)
            self.assertFalse((root / "uploaded-video-id.json").exists())


if __name__ == "__main__":
    unittest.main()
