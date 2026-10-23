"""Offline structural tests for original, multi-character 3D FlowMinute lessons."""
from copy import deepcopy
from pathlib import Path
import json
import unittest

from autopilot.story3d import Story3DError, validate_3d_lesson

PACK = (Path(__file__).resolve().parents[1] / "content" / "episodes"
        / "oct24_multicharacter_3d_plans.json")


def sample(index=0):
    return deepcopy(json.loads(PACK.read_text(encoding="utf-8"))["episodes"][index])


class SceneContractTests(unittest.TestCase):
    def test_all_three_oct24_episodes_are_storyboard_only(self):
        pack = json.loads(PACK.read_text(encoding="utf-8"))
        self.assertEqual(len(pack["episodes"]), 3)
        ids = [e["episode_id"] for e in pack["episodes"]]
        self.assertEqual(len(set(ids)), 3)
        for doc in pack["episodes"]:
            result = validate_3d_lesson(doc)
            self.assertFalse(result["publish_ready"])
            self.assertFalse(result["upload_authorized_by_validator"])
            self.assertEqual(result["stage"], "STORYBOARD_ONLY_NOT_RENDERED")
            self.assertGreaterEqual(result["characters"], 2)
            self.assertGreater(result["character_object_interactions"], 1)
            self.assertIn("render_decode", result["required_qa_pending"])
            self.assertIn("source_rights", result["required_qa_pending"])

    def test_short_and_long_durations(self):
        self.assertEqual(validate_3d_lesson(sample(0))["duration_seconds"], 48)
        self.assertEqual(validate_3d_lesson(sample(1))["duration_seconds"], 48)
        self.assertEqual(validate_3d_lesson(sample(2))["duration_seconds"], 300)

    def test_cannot_replace_real_3d_with_flat_screens(self):
        doc = sample()
        for shot in doc["shots"]:
            shot["mode"] = "motion_2d"
        with self.assertRaisesRegex(Story3DError, "real 3D"):
            validate_3d_lesson(doc)

    def test_every_true_3d_scene_requires_object_action(self):
        doc = sample()
        doc["shots"][0]["object_interactions"] = []
        with self.assertRaisesRegex(Story3DError, "object interaction"):
            validate_3d_lesson(doc)

    def test_multiple_humans_must_speak(self):
        doc = sample()
        for shot in doc["shots"]:
            shot["dialogue"] = [line for line in shot["dialogue"]
                                if line["speaker"] != "jay"]
        with self.assertRaisesRegex(Story3DError, "multi-character"):
            validate_3d_lesson(doc)

    def test_learner_role_is_required(self):
        doc = sample()
        doc["characters"][1]["role"] = "expert"
        with self.assertRaisesRegex(Story3DError, "instructor and learner"):
            validate_3d_lesson(doc)

    def test_a_fake_app_screen_cannot_look_real(self):
        doc = sample()
        doc["shots"][4]["simulation_label_visible"] = False
        with self.assertRaisesRegex(Story3DError, "Simulated UI"):
            validate_3d_lesson(doc)

    def test_practical_tutorial_requires_actual_capture(self):
        doc = sample()
        doc["lesson_type"] = "practical_tutorial"
        with self.assertRaisesRegex(Story3DError, "genuine software"):
            validate_3d_lesson(doc)

    def test_real_capture_requires_evidence(self):
        doc = sample()
        doc["shots"][4]["mode"] = "real_screen_capture"
        with self.assertRaisesRegex(Story3DError, "capture reference"):
            validate_3d_lesson(doc)

    def test_no_self_certified_publication(self):
        doc = sample()
        doc["qa_gates"]["release_receipt"] = True
        with self.assertRaisesRegex(Story3DError, "cannot be attested"):
            validate_3d_lesson(doc)

    def test_missing_qa_flags_are_not_implicitly_green(self):
        doc = sample()
        del doc["qa_gates"]["source_rights"]
        with self.assertRaisesRegex(Story3DError, "nine review gates"):
            validate_3d_lesson(doc)

    def test_bad_beat_order_is_rejected(self):
        doc = sample()
        doc["shots"][1]["beat"] = "verification"
        with self.assertRaisesRegex(Story3DError, "appear in order"):
            validate_3d_lesson(doc)

    def test_source_urls_must_use_https(self):
        doc = sample()
        doc["source_urls"] = ["http://example.org/story"]
        with self.assertRaisesRegex(Story3DError, "Source URLs"):
            validate_3d_lesson(doc)


if __name__ == "__main__":
    unittest.main()
