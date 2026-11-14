"""P8 adversarial tests: unsigned review cannot become real release authority."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.branch3_a6_signed_release import production_release, ReleaseBlocked
from scripts.branch3_v2_p8_synthetic_unsigned_review import (
    CHANNEL, CHECKS, P8Denied, QA_FIELDS, _hash_exact_synthetic_mp4,
    _read_ephemeral, canonical, closed_release_boundary,
    make_unsigned_packet, validate_unsigned_packet, validate_p7_technical_report,
    inspect_and_prepare_unsigned, EDL_FILE, QA_FILE, REVIEW_FILE, OUTPUT_NAME,
)
from scripts.branch3_v2_p6_synthetic_storyboard import draft_synthetic_storyboard
from scripts.test_branch3_v2_p5_synthetic_editorial_evaluation import detector_packet


def storyboard():
    return draft_synthetic_storyboard(detector_packet())


def p7_report():
    return {
        "stage": "CLIVOX_V2_P7_ORIGINAL_SYNTHETIC_VERTICAL_RENDER_QA_ONLY",
        "channel_id": CHANNEL,
        "synthetic_original_lavfi_only": True,
        "source_creator_media_count": 0,
        "real_creator_licenses_verified": 0,
        "original_synthetic_mp4_rendered_in_ephemeral_scratch": True,
        "synthetic_h264_aac_decode_validated": True,
        "synthetic_portrait_9_16_validated": True,
        "synthetic_original_caption_pixels_validated": True,
        "synthetic_audio_cue_and_scene_sync_validated": True,
        "preview_width": 270, "preview_height": 480, "duration_ms": 6000,
        "real_1080x1920_output_validated": False,
        "real_creator_source_processing_allowed": False,
        "real_editorial_context_verified": False,
        "owner_exact_final_media_approved": False,
        "youtube_uploads": 0, "youtube_publish_authorized": False,
        "p7_real_licensed_compositor_milestone_complete": False,
        "status": "SYNTHETIC_RENDER_QA_ONLY_NO_CREATOR_LICENSE_NO_RELEASE",
    }


VIDEO_SHA = hashlib.sha256(b"original synthetic test bytes").hexdigest()
VIDEO_SIZE = 2048


def request():
    return make_unsigned_packet(
        video_sha=VIDEO_SHA, video_bytes=VIDEO_SIZE,
        edl=storyboard(), p7_report=p7_report())


def verify(packet):
    return validate_unsigned_packet(
        packet, video_sha=VIDEO_SHA, video_bytes=VIDEO_SIZE,
        edl=storyboard(), p7_report=p7_report())


class P8UnsignedReviewTests(unittest.TestCase):
    def test_existing_a6_release_policy_remains_closed(self):
        closed_release_boundary()
        with self.assertRaises(ReleaseBlocked):
            production_release()
        item = request()
        self.assertEqual(item["domain"],
                         "CLIVOX-V2-P8-EXACT-SYNTHETIC-UNSIGNED-REVIEW-V1")
        self.assertEqual(item["channel_id"], CHANNEL)
        self.assertEqual(item["exact_synthetic_video_sha256"], VIDEO_SHA)
        self.assertIsNone(item["source_rights_evidence_sha256"])
        self.assertTrue(item["technical_preview_not_production_master"])
        self.assertEqual(item["requested_youtube_privacy"], "private")
        self.assertTrue(all(item["review_checks"][x] is False for x in CHECKS))
        self.assertFalse(item["human_owner_identity_verified"])
        self.assertFalse(item["owner_public_key_independently_enrolled"])
        self.assertIsNone(item["detached_signature_base64"])
        self.assertIsNone(item["owner_review_completed_at_utc"])
        self.assertFalse(item["owner_release_signed"])
        self.assertFalse(item["youtube_upload_authorized"])
        self.assertFalse(item["youtube_publish_authorized"])
        self.assertEqual(verify(item), item)

    def test_digest_canonicalization_is_deterministic_not_signature(self):
        first = request()
        self.assertEqual(first, request())
        self.assertEqual(first["exact_p6_storyboard_sha256"],
                         hashlib.sha256(canonical(storyboard())).hexdigest())
        self.assertEqual(first["exact_p7_qa_report_sha256"],
                         hashlib.sha256(canonical(p7_report())).hexdigest())
        self.assertEqual(len(first["exact_synthetic_video_sha256"]), 64)
        self.assertNotIn("signed_claim", first)
        self.assertNotIn("owner_secret", json.dumps(first))
        self.assertNotIn("private_key", json.dumps(first))
        self.assertNotIn("youtube.com/watch", json.dumps(first))

    def test_rejects_false_rights_and_signed_owner_review_claims(self):
        cases = [
            ("channel_id", "UChardcoded_wrongchannel"),
            ("review_state", "APPROVED_FOR_YOUTUBE"),
            ("source_scope", "CREATOR_LICENSED"),
            ("source_rights_evidence_sha256", "f" * 64),
            ("real_creator_licenses", 1),
            ("real_creator_licenses", True),
            ("human_owner_identity_verified", True),
            ("owner_public_key_independently_enrolled", True),
            ("owner_review_completed_at_utc", "2026-11-14T00:00:00Z"),
            ("detached_signature_base64", "AAAAAAAA"),
            ("owner_release_signed", True),
            ("youtube_upload_authorized", True),
            ("youtube_publish_authorized", True),
            ("publish_at_utc", "2026-11-18T12:00:00Z"),
            ("requested_youtube_privacy", "public"),
            ("technical_preview_not_production_master", False),
            ("real_rights_freshness_verified", True),
            ("exact_synthetic_video_sha256", "1" * 64),
            ("exact_video_bytes", VIDEO_SIZE + 1),
            ("exact_p6_storyboard_sha256", "2" * 64),
            ("exact_p7_qa_report_sha256", "3" * 64),
        ]
        for name, value in cases:
            packet = request()
            packet[name] = value
            with self.subTest(name=name, value=value):
                with self.assertRaises(P8Denied):
                    verify(packet)

    def test_each_review_check_must_remain_false(self):
        for key in CHECKS:
            p = request()
            p["review_checks"][key] = True
            with self.subTest(key=key), self.assertRaises(P8Denied):
                verify(p)
        p = request()
        p["review_checks"]["owner_checked_by_ai"] = False
        with self.assertRaises(P8Denied):
            verify(p)
        p = request()
        p["secret_license_url"] = "https://example.invalid"
        with self.assertRaises(P8Denied):
            verify(p)

    def test_p7_qa_report_forged_audio_video_rights_or_pixels_fails(self):
        self.assertEqual(set(p7_report()), QA_FIELDS)
        validate_p7_technical_report(p7_report())
        edits = [
            ("synthetic_original_lavfi_only", False),
            ("original_synthetic_mp4_rendered_in_ephemeral_scratch", False),
            ("synthetic_h264_aac_decode_validated", False),
            ("synthetic_portrait_9_16_validated", False),
            ("synthetic_original_caption_pixels_validated", False),
            ("synthetic_audio_cue_and_scene_sync_validated", False),
            ("source_creator_media_count", 1),
            ("real_creator_licenses_verified", 1),
            ("real_creator_licenses_verified", True),
            ("youtube_uploads", 1),
            ("real_1080x1920_output_validated", True),
            ("real_creator_source_processing_allowed", True),
            ("real_editorial_context_verified", True),
            ("owner_exact_final_media_approved", True),
            ("youtube_publish_authorized", True),
            ("p7_real_licensed_compositor_milestone_complete", True),
            ("preview_width", 1080), ("preview_height", 1920),
            ("duration_ms", 40_000), ("channel_id", "WRONG_CHANNEL"),
        ]
        for key, value in edits:
            p = p7_report()
            p[key] = value
            with self.subTest(key=key), self.assertRaises(P8Denied):
                validate_p7_technical_report(p)
        p = p7_report()
        p["creator_name"] = "private"
        with self.assertRaises(P8Denied):
            validate_p7_technical_report(p)

    def test_changed_edl_and_p7_qa_digests_invalidate_review(self):
        p = request()
        edl = storyboard()
        edl["draft_shots"][0]["original_clivox_overlay"] = "new quote"
        with self.assertRaises(P8Denied):
            validate_unsigned_packet(p, video_sha=VIDEO_SHA,
                                     video_bytes=VIDEO_SIZE, edl=edl,
                                     p7_report=p7_report())
        qa = p7_report()
        qa["synthetic_original_caption_pixels_validated"] = False
        with self.assertRaises(P8Denied):
            validate_unsigned_packet(p, video_sha=VIDEO_SHA,
                                     video_bytes=VIDEO_SIZE, edl=storyboard(),
                                     p7_report=qa)

    def test_closed_release_policy_forgery_denied_before_any_packet(self):
        with patch(
            "scripts.branch3_v2_p8_synthetic_unsigned_review.validate_quarantine_manifest",
            side_effect=ReleaseBlocked("PRODUCTION_ENABLED"),
        ):
            with self.assertRaises(P8Denied):
                closed_release_boundary()
        with patch(
            "scripts.branch3_v2_p8_synthetic_unsigned_review._probe_closed",
            side_effect=ValueError("RIGHTS_SWITCHED"),
        ):
            with self.assertRaises(ValueError):
                make_unsigned_packet(video_sha=VIDEO_SHA,
                                     video_bytes=VIDEO_SIZE, edl=storyboard(),
                                     p7_report=p7_report())

    def test_exact_local_path_hash_and_symlink_safety(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            mp4 = root / OUTPUT_NAME
            mp4.write_bytes(b"self-generated short fixture" * 18)
            expected = hashlib.sha256(mp4.read_bytes()).hexdigest()
            digest, count = _hash_exact_synthetic_mp4(root)
            self.assertEqual((digest, count), (expected, mp4.stat().st_size))
            mp4.unlink()
            outside = root / "other.mp4"
            outside.write_bytes(b"this is a different video" * 18)
            mp4.symlink_to(outside)
            with self.assertRaises(P8Denied):
                _hash_exact_synthetic_mp4(root)

    def test_json_safe_path_fixed_basenames_and_non_approval_input(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            (root / EDL_FILE).write_text(json.dumps(storyboard()), encoding="utf-8")
            (root / QA_FILE).write_text(json.dumps(p7_report()), encoding="utf-8")
            self.assertEqual(_read_ephemeral(root, EDL_FILE), storyboard())
            self.assertEqual(_read_ephemeral(root, QA_FILE), p7_report())
            for name in ("../creator.json", "token.json",
                         "/tmp/private_contract.pdf"):
                with self.subTest(name=name), self.assertRaises(P8Denied):
                    _read_ephemeral(root, name)
            (root / QA_FILE).unlink()
            (root / QA_FILE).symlink_to(root / EDL_FILE)
            with self.assertRaises(P8Denied):
                _read_ephemeral(root, QA_FILE)
            (root / QA_FILE).unlink()
            (root / QA_FILE).write_text("x" * 33000, encoding="utf-8")
            with self.assertRaises(P8Denied):
                _read_ephemeral(root, QA_FILE)

    def test_file_not_present_rejected_before_media_decode_or_approval(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            (root / EDL_FILE).write_text(json.dumps(storyboard()), encoding="utf-8")
            (root / QA_FILE).write_text(json.dumps(p7_report()), encoding="utf-8")
            with self.assertRaises(P8Denied):
                inspect_and_prepare_unsigned(scratch=root)
            self.assertFalse((root / REVIEW_FILE).exists())

    def test_empty_or_malformed_hash_rejected(self):
        for digest in ("123", "F" * 64, "", None, True):
            with self.subTest(digest=digest), self.assertRaises(P8Denied):
                make_unsigned_packet(
                    video_sha=digest, video_bytes=VIDEO_SIZE,
                    edl=storyboard(), p7_report=p7_report())
        for size in (True, -1, 0, 99999999):
            with self.subTest(size=size), self.assertRaises(P8Denied):
                make_unsigned_packet(
                    video_sha=VIDEO_SHA, video_bytes=size,
                    edl=storyboard(), p7_report=p7_report())


if __name__ == "__main__":
    unittest.main()
