"""P6 source-free editorial storyboard: reject real-rights and draft tampering."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.branch3_v2_p5_synthetic_editorial_evaluation import (
    P5EvaluationDenied,
)
from scripts.branch3_v2_p5_synthetic_moment_proposals import (
    P5Denied, _probe_closed,
)
from scripts.branch3_v2_p6_synthetic_storyboard import (
    P6Denied, SYNTHETIC_DURATION_MS, _candidate_has_generated_turn,
    draft_synthetic_storyboard, original_generated_shots, validate_storyboard,
)
from scripts.test_branch3_v2_p5_synthetic_editorial_evaluation import (
    detector_packet,
)


class SyntheticEditorialTests(unittest.TestCase):
    def test_real_p4_p5_rights_hold_before_draft(self):
        result = _probe_closed()
        self.assertEqual(result["rights_grants_verified"], 0)
        self.assertFalse(result["p4_milestone_complete"])
        with patch(
            "scripts.branch3_v2_p6_synthetic_storyboard._probe_closed",
            side_effect=P5Denied("CLIVOX_P5_DENIED_NO_CREATOR_RIGHTS"),
        ):
            with self.assertRaises(P5Denied):
                draft_synthetic_storyboard(detector_packet())

    def test_original_story_hard_labeled_synthetic_only(self):
        source = detector_packet()
        original = copy.deepcopy(source)
        output = draft_synthetic_storyboard(source)
        self.assertEqual(output["channel_id"], "UCfPEvy0SefE_5nNlYlY_CyQ")
        self.assertEqual(
            output["stage"], "CLIVOX_V2_P6_SYNTHETIC_ORIGINAL_STORYBOARD_DRAFT")
        self.assertTrue(output["synthetic_fixture_only"])
        self.assertEqual(output["source_duration_ms"], 6000)
        self.assertEqual(output["draft_duration_ms"], 6000)
        self.assertEqual(output["draft_canvas"]["width"], 1080)
        self.assertEqual(output["draft_canvas"]["height"], 1920)
        self.assertFalse(output["draft_canvas"]["rendered"])
        self.assertFalse(output["human_editor_approved"])
        self.assertFalse(output["real_editorial_context_confirmed"])
        self.assertFalse(output["licensed_clip_used"])
        self.assertFalse(output["video_rendered"])
        self.assertFalse(output["audio_rendered"])
        self.assertFalse(output["youtube_publish_authorized"])
        self.assertEqual(output["youtube_uploads"], 0)
        self.assertEqual(output["real_creator_source_files"], 0)
        self.assertEqual(output["creator_commercial_reuse_grants"], 0)
        self.assertEqual(output["candidate_reference"]["proposal_id"],
                         "synthetic_01")
        self.assertFalse(output["candidate_reference"]
                         ["validated_real_editorial_selection"])
        self.assertEqual(validate_storyboard(output), output)
        self.assertEqual(source, original)
        encoded = json.dumps(output)
        for private in (
            "youtube.com/watch", "https://", "Bearer ", "creator_email",
            "source_video_url", "source_sha256", "actual_transcript",
            "most_replayed", "licensed_creator_video",
        ):
            self.assertNotIn(private, encoded)

    def test_edl_has_no_gaps_overlap_or_quoted_creator_speech(self):
        shots = original_generated_shots()
        self.assertEqual(len(shots), 3)
        self.assertEqual([s["target_start_ms"] for s in shots],
                         [0, 2000, 3000])
        self.assertEqual([s["target_end_ms"] for s in shots],
                         [2000, 3000, 6000])
        self.assertEqual(shots[0]["source_start_ms"], 0)
        self.assertEqual(shots[-1]["source_end_ms"], SYNTHETIC_DURATION_MS)
        self.assertTrue(all(s["requires_human_review"] for s in shots))
        self.assertTrue(all(not s["creator_dialogue_used"] for s in shots))
        self.assertTrue(all(not s["licensed_media_inserted"] for s in shots))
        self.assertEqual(shots[2]["editorial_intent"], "ORIGINAL_CRITICAL_PAYOFF")
        self.assertGreater(len(shots[2]["original_clivox_overlay"]), 20)

    def test_p5_absent_or_unsupported_evidence_fails_closed(self):
        blank = detector_packet()
        blank["synthetic_candidate_windows"] = []
        blank["synthetic_technical_candidate_count"] = 0
        with self.assertRaises(P6Denied):
            draft_synthetic_storyboard(blank)
        no_scene = detector_packet()
        no_scene["synthetic_candidate_windows"][0]["evidence_kinds"] = [
            "ACOUSTIC_RMS_RISE"]
        with self.assertRaises(P6Denied):
            draft_synthetic_storyboard(no_scene)
        outside_turn = detector_packet()
        outside_turn["synthetic_candidate_windows"][0]["start_ms"] = 0
        outside_turn["synthetic_candidate_windows"][0]["end_ms"] = 1000
        with self.assertRaises(P6Denied):
            draft_synthetic_storyboard(outside_turn)

    def test_candidate_turn_requires_actual_two_signal_kinds(self):
        p = detector_packet()
        self.assertEqual(_candidate_has_generated_turn(p), "synthetic_01")
        p["synthetic_candidate_windows"][0]["evidence_kinds"] = [
            "VIDEO_LUMA_CUT"]
        with self.assertRaises(P6Denied):
            _candidate_has_generated_turn(p)

    def test_untrusted_foreign_source_transcript_or_license_rejected(self):
        attacks = [
            ("channel_id", "UC" + "9" * 22),
            ("estimated_viral_performance", 0.99),
            ("actual_creator_source_count", 1),
            ("real_creator_license_count", 1),
            ("ASR_or_VAD_performed", True),
            ("speech_or_quotes_inferred", True),
            ("youtube_uploads", 1),
            ("human_source_context_required", False),
        ]
        for field, value in attacks:
            packet = detector_packet()
            packet[field] = value
            with self.subTest(field=field):
                with self.assertRaises(P5EvaluationDenied):
                    draft_synthetic_storyboard(packet)
        injected = detector_packet()
        injected["synthetic_candidate_windows"][0]["machine_transcript"] = (
            "pretend someone said this")
        with self.assertRaises(P5EvaluationDenied):
            draft_synthetic_storyboard(injected)

    def test_forged_storyboard_editor_or_publisher_release_rejected(self):
        ok = draft_synthetic_storyboard(detector_packet())
        patches = (
            ("human_editor_approved", True),
            ("owner_final_media_approved", True),
            ("real_editorial_context_confirmed", True),
            ("real_source_dialogue_verified", True),
            ("licensed_clip_used", True),
            ("video_rendered", True),
            ("audio_rendered", True),
            ("youtube_publish_authorized", True),
            ("youtube_uploads", 1),
            ("creator_commercial_reuse_grants", True),
            ("real_creator_source_files", 1),
            ("synthetic_fixture_only", False),
            ("source_duration_ms", 6001),
            ("draft_duration_ms", 10_000),
            ("stage", "CLIVOX_V2_REAL_CREATOR_APPROVED"),
        )
        for field, value in patches:
            forged = copy.deepcopy(ok)
            forged[field] = value
            with self.subTest(field=field), self.assertRaises(P6Denied):
                validate_storyboard(forged)

    def test_edl_mutations_gap_overlap_injected_speech_and_copyright_fail(self):
        original = draft_synthetic_storyboard(detector_packet())
        for field, value in (
            ("target_start_ms", 1999),
            ("source_end_ms", 2800),
            ("original_clivox_overlay", "He said a real creator quote"),
            ("requires_human_review", False),
            ("creator_dialogue_used", True),
            ("licensed_media_inserted", True),
            ("publisher_clearance_verified", True),
            ("source_visual", "UNLICENSED_GAMING_CLIP"),
            ("sequence", 99),
            ("target_end_ms", 4100),
        ):
            forged = copy.deepcopy(original)
            forged["draft_shots"][1][field] = value
            with self.subTest(field=field), self.assertRaises(P6Denied):
                validate_storyboard(forged)
        extra = copy.deepcopy(original)
        extra["contract_filename"] = "creator_private_contract.pdf"
        with self.assertRaises(P6Denied):
            validate_storyboard(extra)
        extra = copy.deepcopy(original)
        extra["draft_shots"][0]["creator_voiceprint"] = "some_identifier"
        with self.assertRaises(P6Denied):
            validate_storyboard(extra)

    def test_candidate_reference_cannot_be_upgraded_to_real_selection(self):
        ok = draft_synthetic_storyboard(detector_packet())
        for field, value in (
            ("validated_real_editorial_selection", True),
            ("source_review_required", False),
            ("proposal_id", "real_creator_1234"),
            ("signal_kinds", ["YOUTUBE_MOST_REPLAYED"]),
        ):
            forged = copy.deepcopy(ok)
            forged["candidate_reference"][field] = value
            with self.subTest(field=field), self.assertRaises(P6Denied):
                validate_storyboard(forged)

    def test_repeated_generation_is_identical_and_read_only(self):
        p = detector_packet()
        a = draft_synthetic_storyboard(p)
        b = draft_synthetic_storyboard(p)
        self.assertEqual(a, b)
        self.assertEqual(a["draft_shots"], original_generated_shots())
        self.assertTrue(a["status"].startswith("SYNTHETIC_WRITTEN_DRAFT_ONLY"))

    def test_cli_does_not_accept_untrusted_file_path(self):
        # This test only inspects existing safe helper; no media required.
        from scripts.branch3_v2_p5_synthetic_editorial_evaluation import (
            _read_temp_report,
        )
        with tempfile.TemporaryDirectory() as folder:
            scratch = Path(folder)
            good = scratch / "quarantined-signals-only.json"
            good.write_text(json.dumps(detector_packet()), encoding="utf-8")
            self.assertEqual(
                draft_synthetic_storyboard(_read_temp_report(scratch, good.name))
                ["draft_shots"][1]["source_visual"],
                "SELF_GENERATED_WHITE_WITH_TONE",
            )
            (scratch / "shortcut.json").symlink_to(good)
            for bad in ("shortcut.json", "../secrets.json", "/etc/passwd"):
                with self.subTest(bad=bad), self.assertRaises(P5EvaluationDenied):
                    _read_temp_report(scratch, bad)


if __name__ == "__main__":
    unittest.main()
