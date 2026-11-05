"""B1q4 genuine 1080p voice-call-opening composition regression tests.

The real encoded B1q3b nine-frame collage showed a tiny anonymous floating
waveform in a largely empty opening. Replace just that source-original
semantic hero with a finite, non-branded phone/identity image. This is not
a separate voice approval, verified caller-ID service, or remote YouTube edit.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
import inspect
from pathlib import Path
import unittest

from autopilot.branch1_no_spinner_storyboard import (
    _draw_subject, draw_source_keyframe, storyboard_cues,
)
from autopilot.branch1_three_narrated_no_spinner_v2 import SOURCES, _load_source

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(importlib.util.find_spec("PIL") is not None,
                     "Actual 1080x1920 native Pillow pixel tests run in CI")
class OriginalPhoneCallHeroTests(unittest.TestCase):
    def test_new_voice_hook_is_semantic_and_finite_and_source_bound(self):
        from PIL import ImageChops, ImageStat
        voice_id = next(eid for eid, _ in SOURCES if "voice_cloning" in eid)
        story = _load_source(ROOT, voice_id)
        self.assertTrue(storyboard_cues(story)[0]["source_text"].startswith(
            "That urgent call"))
        frames = []
        for phase in (0.10, 0.50, 0.90):
            image, receipt = draw_source_keyframe(
                story, 0, phase, caption_layer="timed_ass_overlay")
            self.assertEqual(image.size, (1080, 1920))
            self.assertEqual(receipt["distinct_original_visual_subject"],
                             "VOICE_PHONE_CALL_IDENTITY_HOOK")
            self.assertTrue(receipt["no_circle_spinner_drawn"])
            self.assertTrue(receipt["timed_ass_caption_overlay_required"])
            self.assertFalse(receipt["hero_headline_repeats_full_spoken_sentence"])
            self.assertFalse(receipt["youtube_uploaded"])
            self.assertEqual(receipt["caption_source_sha256"],
                             sha256(story["captions"][0]["text"].encode()).hexdigest())
            hero = image.crop((0, 495, 1080, 1384))
            # Make a genuinely populated visual, not a blank dark lecture slide.
            self.assertGreater(sum(ImageStat.Stat(hero).stddev), 35)
            frames.append(image)
        for i in (1, 2):
            diff = ImageChops.difference(
                frames[i-1].crop((0, 495, 1080, 1384)),
                frames[i].crop((0, 495, 1080, 1384)))
            self.assertIsNotNone(diff.getbbox(), "Finite phone reveal should visibly move")
            for bounds in ((0, 0, 1080, 495), (0, 1384, 1080, 1650)):
                self.assertIsNone(ImageChops.difference(
                    frames[i-1].crop(bounds), frames[i].crop(bounds)).getbbox(),
                    "Title and single native ASS subtitle reserve remain fixed")

    def test_other_subjects_and_final_call_action_still_distinct(self):
        expected = {
            "voice": ("VOICE_PHONE_CALL_IDENTITY_HOOK",
                      "TWO_STEP_CALL_VERIFICATION", "VERIFIED_CALLER_CHECKLIST"),
            "photo": ("PHOTO_METADATA_DISCOVERY", "PHOTO_INFO_INSPECTOR",
                      "PHOTO_SHARE_SAFETY_ACTIONS"),
            "incognito": ("PRIVATE_BROWSER_TAB_HOOK", "DEVICE_SAVED_INFORMATION",
                          "BROWSER_PRIVACY_DIFFERENCE"),
        }
        for eid, _ in SOURCES:
            story = _load_source(ROOT, eid)
            plan = storyboard_cues(story)
            actual = []
            for index in (0, len(plan)//2, len(plan)-1):
                _, evidence = draw_source_keyframe(
                    story, index, .74, caption_layer="timed_ass_overlay")
                actual.append(evidence["distinct_original_visual_subject"])
            match = ("voice" if "voice_cloning" in eid
                     else "photo" if "photo_gps" in eid else "incognito")
            self.assertEqual(tuple(actual), expected[match])

    def test_no_spinning_or_remote_side_effect_hidden_in_new_original_artist(self):
        src = inspect.getsource(_draw_subject)
        for banned in ("d.arc(", "d.ellipse(", "while True:", "requests.",
                       "videos().insert(", "youtube.", "random."):
            self.assertNotIn(banned, src)
        self.assertIn("VOICE_PHONE_CALL_IDENTITY_HOOK", src)


if __name__ == "__main__":
    unittest.main()
