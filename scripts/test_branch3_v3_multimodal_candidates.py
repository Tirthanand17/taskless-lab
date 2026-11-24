import copy
import unittest
from unittest.mock import patch

from scripts.branch3_v3_multimodal_candidates import (
    baseline, demo, propose, validate, MAX_CLIPS,
)


class MultimodalTests(unittest.TestCase):
    def test_gaming_recovers_visual_moment_missing_from_v2(self):
        d = demo()
        d["semantic_events_ms"] = None
        old = baseline(d)
        new = propose(d)
        self.assertEqual(old["candidate_count"], 1)
        self.assertEqual(len(new["candidates"]), 2)
        self.assertTrue(any(c["anchor_ms"] == 75000 for c in new["candidates"]))
        self.assertIn("semantic_events_ms", new["missing_modalities"])

    def test_dialogue_uses_semantic_not_unrelated_noise_or_motion(self):
        r = propose(demo("dialogue"))
        self.assertEqual(len(r["candidates"]), 1)
        self.assertEqual(r["candidates"][0]["anchor_ms"], 75500)

    def test_reaction_fusion(self):
        r = propose(demo("reaction"))
        self.assertEqual(len(r["candidates"]), 2)
        c = r["candidates"][0]
        self.assertEqual({e["kind"] for e in c["evidence"]}, {"motion", "semantic"})

    def test_scene_cut_is_not_motion(self):
        d = demo()
        d["scene_cuts_ms"] = [75000]
        d["semantic_events_ms"] = []
        r = propose(d)
        self.assertEqual(r["event_counts"]["motion"], 0)
        self.assertEqual(len(r["candidates"]), 1)

    def test_empty_and_missing(self):
        d = demo()
        d.update(audio_rms=None, motion=None, semantic_events_ms=None,
                 editor_marks_ms=None, scene_cuts_ms=[40000])
        self.assertIsNone(baseline(d))
        r = propose(d)
        self.assertEqual(r["candidates"], [])
        self.assertEqual(len(r["missing_modalities"]), 4)

    def test_no_forged_fields_or_bool_as_int(self):
        for key, val in [("creator_rights_verified", True), ("step_ms", True),
                         ("profile", []), ("duration_ms", True),
                         ("audio_rms", [False] * 240), ("semantic_events_ms", [120000]),
                         ("editor_marks_ms", [100, 100])]:
            d = demo()
            d[key] = val
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate(d)

    def test_bounds_dedup_and_no_authority(self):
        d = demo()
        d["editor_marks_ms"] = [0, 1000, 29000, 30000, 75000, 119999]
        r = propose(d)
        self.assertEqual(r, propose(copy.deepcopy(d)))
        self.assertFalse(r["creator_rights_verified"])
        self.assertFalse(r["ready_to_render"])
        self.assertFalse(r["youtube_upload_authorized"])
        self.assertIsNone(r["viral_probability"])
        cs = sorted(r["candidates"], key=lambda c: c["start_ms"])
        self.assertLessEqual(len(cs), MAX_CLIPS)
        for a, b in zip(cs, cs[1:]):
            self.assertLessEqual(a["end_ms"], b["start_ms"])
        for c in cs:
            self.assertTrue(0 <= c["start_ms"] <= c["anchor_ms"] < c["end_ms"] <= 120000)
            self.assertTrue(all(c["start_ms"] <= e["time_ms"] < c["end_ms"] for e in c["evidence"]))
            self.assertFalse(c["render_authorized"])
            self.assertFalse(c["youtube_upload_authorized"])

    def test_policy_failure_blocks(self):
        with patch("scripts.branch3_v3_multimodal_candidates._probe_closed",
                   side_effect=ValueError("policy changed")):
            with self.assertRaises(ValueError):
                propose(demo())

    def test_flat_high_energy_not_a_highlight(self):
        d = demo()
        d.update(audio_rms=[7000] * 240, motion=[8000] * 240,
                 semantic_events_ms=[], editor_marks_ms=[])
        self.assertEqual(propose(d)["candidates"], [])


if __name__ == "__main__":
    unittest.main()
