"""Adversarial source-free long-form candidate-planning tests."""
import copy
import json
import unittest

from scripts.branch3_v2_p5_longform_local_signal_planner import (
    CHANNEL, LongformDenied, MAX_CANDIDATES, STATE, STEP_MS,
    plan_longform_candidates, production_clip_or_publish, synthetic_demo,
    validate_measurements,
)


class LocalLongformPlannerTests(unittest.TestCase):
    def test_three_synthetic_windows_never_promote_rights_or_viral_claim(self):
        d = synthetic_demo()
        report = plan_longform_candidates(d)
        self.assertEqual(report["channel_id"], CHANNEL)
        self.assertEqual(report["candidate_count"], 3)
        self.assertEqual(report["operator_bookmark_count_unverified"], 1)
        self.assertEqual(report["local_acoustic_rise_count"], 3)
        self.assertFalse(report["youtube_api_metrics_used"])
        self.assertFalse(report["youtube_most_replayed_heatmap_accessed"])
        self.assertFalse(report["actual_viral_performance_predicted"])
        self.assertFalse(report["source_media_authenticated"])
        self.assertFalse(report["creator_commercial_rights_authenticated"])
        self.assertFalse(report["ready_for_render"])
        self.assertFalse(report["youtube_upload_authorized"])
        self.assertFalse(report["p5_real_milestone_complete"])
        for item in report["candidates"]:
            self.assertGreaterEqual(item["start_ms"], 0)
            self.assertLessEqual(item["end_ms"], d["duration_ms"])
            self.assertEqual(item["end_ms"] - item["start_ms"], 36000)
            self.assertIn("VIDEO_SCENE_CHANGE_SUPPORT", item["evidence_kinds"])
            self.assertIsNone(item["viral_probability"])
            for field in (
                "source_media_sha256_authenticated",
                "creator_license_authenticated", "transcript_and_quote_verified",
                "human_editorial_context_review_completed",
                "original_clivox_story_approved", "clip_render_authorized",
                "youtube_upload_authorized",
            ):
                self.assertIs(item[field], False)
        self.assertNotIn("youtube.com/watch?", json.dumps(report))

    def test_scenes_alone_do_not_manufacture_entertainment_moments(self):
        d = synthetic_demo()
        d["audio_rms"] = [120] * 360
        d["unverified_editor_marks_ms"] = []
        r = plan_longform_candidates(d)
        self.assertEqual(r["candidate_count"], 0)
        self.assertEqual(r["status"],
                         "NO_CLEAR_LOCAL_SIGNAL_CANDIDATES_HUMAN_REVIEW_REQUIRED")
        self.assertFalse(r["ready_for_render"])

    def test_unverified_human_mark_only_is_not_creator_permission(self):
        d = synthetic_demo()
        d["audio_rms"] = [100] * 360
        d["scene_cuts_ms"] = []
        d["unverified_editor_marks_ms"] = [90000]
        r = plan_longform_candidates(d)
        self.assertEqual(r["candidate_count"], 1)
        self.assertEqual(r["candidates"][0]["evidence_kinds"],
                         ["UNVERIFIED_EDITOR_MARK"])
        self.assertFalse(r["human_editorial_review_completed"])
        self.assertFalse(r["creator_commercial_rights_authenticated"])

    def test_two_hour_bounded_input_and_20_candidate_overflow(self):
        n = (7200000 // STEP_MS)
        d = synthetic_demo()
        d["duration_ms"] = 7200000
        d["audio_rms"] = [100] * n
        d["scene_cuts_ms"] = []
        d["unverified_editor_marks_ms"] = []
        for index in (100, 7000, 14000):
            d["audio_rms"][index] = 5000
        r = plan_longform_candidates(d)
        self.assertEqual(r["candidate_count"], 3)
        self.assertLessEqual(r["candidates"][-1]["end_ms"], d["duration_ms"])
        d["duration_ms"] = 3600000
        d["audio_rms"] = [100] * (3600000 // STEP_MS)
        for i in [100 + 240 * k for k in range(26)]:
            d["audio_rms"][i] = 8000
        r = plan_longform_candidates(d)
        self.assertEqual(r["candidate_count"], MAX_CANDIDATES)
        self.assertEqual(r["candidate_overflow_omitted_count"], 6)
        self.assertFalse(r["result_is_complete_editorial_selection"])

    def test_schema_forbids_platform_analytics_viral_scores_and_identity_forgery(self):
        orig = synthetic_demo()
        for field, value in (
            ("channel_id", "OTHER"), ("schema_version", True),
            ("source_measurements_state", "YOUTUBE_PUBLIC_VIEWS"),
            ("rms_step_ms", 1000), ("rms_step_ms", True),
            ("duration_ms", 7200001), ("duration_ms", 2000),
            ("duration_ms", True), ("audio_rms", [100]),
        ):
            changed = copy.deepcopy(orig)
            changed[field] = value
            with self.subTest(field=field), self.assertRaises(LongformDenied):
                plan_longform_candidates(changed)
        for extra in ("public_view_count", "engagement_score", "viral_probability",
                      "youtube_most_replayed", "creator_license_approved",
                      "creator_email", "source_video_url", "owner_release_signed"):
            changed = copy.deepcopy(orig)
            changed[extra] = "untrusted"
            with self.subTest(extra=extra), self.assertRaises(LongformDenied):
                validate_measurements(changed)

    def test_timeline_and_sample_values_are_strict(self):
        orig = synthetic_demo()
        for field, value in (
            ("scene_cuts_ms", [110000, 40500]),
            ("scene_cuts_ms", [40500, 40500]),
            ("scene_cuts_ms", [180000]),
            ("scene_cuts_ms", [True]),
            ("unverified_editor_marks_ms", [-1]),
            ("unverified_editor_marks_ms", [90000, 90000]),
            ("audio_rms", [True] + orig["audio_rms"][1:]),
            ("audio_rms", [32768] + orig["audio_rms"][1:]),
            ("audio_rms", [-1] + orig["audio_rms"][1:]),
        ):
            doc = copy.deepcopy(orig)
            doc[field] = value
            with self.subTest(field=field), self.assertRaises(LongformDenied):
                plan_longform_candidates(doc)

    def test_same_measurements_have_deterministic_digest_and_windows(self):
        d = synthetic_demo()
        one = plan_longform_candidates(d)
        two = plan_longform_candidates(copy.deepcopy(d))
        self.assertEqual(one, two)
        self.assertEqual(len(one["source_measurement_sha256_not_source_license"]), 64)
        d["audio_rms"][80] = 2000
        changed = plan_longform_candidates(d)
        self.assertNotEqual(one["source_measurement_sha256_not_source_license"],
                            changed["source_measurement_sha256_not_source_license"])

    def test_production_clip_and_upload_never_enabled(self):
        for args in ({}, {"source_rights_granted": True},
                     {"oauth": "fake", "publish": True},
                     {"creator_file": "/private/master.mp4"}):
            with self.subTest(args=args), self.assertRaises(LongformDenied):
                production_clip_or_publish(**args)


if __name__ == "__main__":
    unittest.main()
