"""Fail-closed P5/P6 local-longform editorial review binding tests."""
import copy
import json
import unittest

from scripts.branch3_v2_p5_longform_local_signal_planner import (
    plan_longform_candidates, synthetic_demo,
)
from scripts.branch3_v2_p6_longform_editorial_intake import (
    CHECKS, EditorialIntakeDenied, HOLD,
    build_unreviewed_editorial_intake, production_editorial_approval,
    verify_candidate_binding,
)


def fixture():
    measures = synthetic_demo()
    return measures, plan_longform_candidates(measures)


class LongformEditorialIntakeTests(unittest.TestCase):
    def test_three_cards_no_consent_quotes_or_media_or_viral_predictions(self):
        measures, report = fixture()
        result = build_unreviewed_editorial_intake(
            measurements=measures, report=report)
        self.assertEqual(result["candidate_count"], 3)
        self.assertEqual(result["status"], HOLD)
        self.assertEqual(result["source_media_received"], 0)
        self.assertEqual(result["creator_licenses_verified"], 0)
        self.assertEqual(result["editorial_approvals_received"], 0)
        self.assertEqual(result["youtube_uploads"], 0)
        for field in ("human_editorial_review_completed", "real_p6_milestone_complete",
                      "output_is_a_video_edl", "ready_to_render", "ready_to_publish"):
            self.assertFalse(result[field])
        for original, card in zip(report["candidates"], result["cards"]):
            self.assertEqual(card["candidate_id"], original["candidate_id"])
            self.assertEqual(card["source_start_ms"], original["start_ms"])
            self.assertEqual(card["source_end_ms"], original["end_ms"])
            self.assertEqual(card["measured_evidence_kinds_only"],
                             original["evidence_kinds"])
            self.assertIsNone(card["suggested_original_script_text"])
            self.assertIsNone(card["actual_speaker_words"])
            self.assertIsNone(card["viral_success_probability"])
            for key in ("source_media_verified", "source_license_verified",
                        "spoken_quote_verified", "human_editor_approved",
                        "original_transformative_value_approved",
                        "render_authorized", "youtube_upload_authorized",
                        "youtube_publish_authorized"):
                self.assertIs(card[key], False)
            self.assertEqual(set(card["pending_human_checks"]), set(CHECKS))
            self.assertTrue(all(v == "NOT_PERFORMED_SOURCE_FREE_ONLY"
                                for v in card["pending_human_checks"].values()))
        serialized = json.dumps(result)
        for forbidden in ("youtube.com/watch?", "Authorization: Bearer",
                          "access_token", "recipient_address", "signed_grant"):
            self.assertNotIn(forbidden, serialized)

    def test_out_of_window_bookmark_is_not_absorbed_into_first_window(self):
        d = synthetic_demo()
        d["audio_rms"] = [120] * 360
        d["audio_rms"][80] = 7200  # local rise at 40 s; 32–68 s clip
        d["scene_cuts_ms"] = [40500]
        d["unverified_editor_marks_ms"] = [69000]  # outside that clip
        p5 = plan_longform_candidates(d)
        self.assertEqual(p5["candidate_count"], 2)
        self.assertEqual(p5["candidates"][0]["end_ms"], 68000)
        self.assertNotIn("UNVERIFIED_EDITOR_MARK",
                         p5["candidates"][0]["evidence_kinds"])
        self.assertIn("UNVERIFIED_EDITOR_MARK",
                      p5["candidates"][1]["evidence_kinds"])
        self.assertLessEqual(p5["candidates"][1]["start_ms"], 69000)
        self.assertGreaterEqual(p5["candidates"][1]["end_ms"], 69000)
        cards = build_unreviewed_editorial_intake(
            measurements=d, report=p5)["cards"]
        self.assertEqual(len(cards), 2)

    def test_event_inside_prior_candidate_is_combined_without_extra_clip(self):
        d = synthetic_demo()
        d["audio_rms"] = [120] * 360
        d["audio_rms"][80] = 7200
        d["scene_cuts_ms"] = []
        d["unverified_editor_marks_ms"] = [67000]
        p5 = plan_longform_candidates(d)
        self.assertEqual(p5["candidate_count"], 1)
        self.assertEqual(p5["candidates"][0]["evidence_kinds"],
                         ["ACOUSTIC_RISE_HEURISTIC", "UNVERIFIED_EDITOR_MARK"])

    def test_modified_p5_time_evidence_privilege_or_digest_fails(self):
        d, p5 = fixture()
        for field, value in (
            ("source_measurement_sha256_not_source_license", "0"*64),
            ("candidate_count", 20),
            ("creator_commercial_rights_authenticated", True),
            ("ready_for_render", True),
            ("youtube_upload_authorized", True),
            ("human_editorial_review_completed", True),
            ("status", "LICENSED"),
        ):
            altered = copy.deepcopy(p5)
            altered[field] = value
            with self.subTest(field=field), self.assertRaises(EditorialIntakeDenied):
                verify_candidate_binding(d, altered)
        for field, value in (
            ("start_ms", 5),
            ("end_ms", 999),
            ("evidence_kinds", ["MOST_REPLAYED"]),
            ("creator_license_authenticated", True),
            ("clip_render_authorized", True),
            ("viral_probability", 0.99),
        ):
            altered = copy.deepcopy(p5)
            altered["candidates"][0][field] = value
            with self.subTest(field=field), self.assertRaises(EditorialIntakeDenied):
                build_unreviewed_editorial_intake(measurements=d, report=altered)
        altered = copy.deepcopy(p5)
        altered["new_creator_license"] = True
        with self.assertRaises(EditorialIntakeDenied):
            verify_candidate_binding(d, altered)

    def test_measurements_change_after_plan_invalidates_all_cards(self):
        d, p5 = fixture()
        d["audio_rms"][80] = 800
        with self.assertRaises(EditorialIntakeDenied):
            build_unreviewed_editorial_intake(measurements=d, report=p5)

    def test_no_event_returns_no_invented_scene_or_story(self):
        d = synthetic_demo()
        d["audio_rms"] = [120]*360
        d["unverified_editor_marks_ms"] = []
        p5 = plan_longform_candidates(d)
        result = build_unreviewed_editorial_intake(
            measurements=d, report=p5)
        self.assertEqual(result["candidate_count"], 0)
        self.assertEqual(result["cards"], [])
        self.assertFalse(result["ready_to_render"])
        self.assertFalse(result["ready_to_publish"])

    def test_cannot_self_approve_any_real_editorial_step(self):
        for kwargs in (
            {}, {"owner_approved": True}, {"editor_identity": "human"},
            {"license_received": True, "publish": True},
            {"source_file": "/private/creator.mp4"},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(EditorialIntakeDenied):
                production_editorial_approval(**kwargs)


if __name__ == "__main__":
    unittest.main()
