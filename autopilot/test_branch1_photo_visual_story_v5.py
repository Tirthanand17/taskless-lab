"""B1q5: pixel-proven photo location privacy story, no static/exact caption regressions.

Test the actual original 1080x1920 native scene renderer independently on
GitHub's no-YouTube CI. No claim of source art being final encoded MP4.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
import inspect
from pathlib import Path
import unittest

from autopilot.branch1_no_spinner_storyboard import (
    _draw_subject,draw_source_keyframe,storyboard_cues,NoSpinnerVisualRejected,
)
from autopilot.branch1_three_narrated_no_spinner_v2 import _load_source,SOURCES

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(importlib.util.find_spec("PIL") is not None,
                     "Mandatory native Pillow physical scene review in GitHub CI")
class OriginalPhotoStoryClarityTests(unittest.TestCase):
    def setUp(self):
        eid=next(eid for eid,_ in SOURCES if "photo_gps" in eid)
        self.story=_load_source(ROOT,eid)
        self.cues=storyboard_cues(self.story)

    def test_photo_source_is_exact_and_three_subjects_remain_different(self):
        from PIL import ImageChops, ImageStat
        expected=("PHOTO_METADATA_DISCOVERY","PHOTO_INFO_INSPECTOR",
                  "PHOTO_SHARE_SAFETY_ACTIONS")
        for idx,stage in zip((0,len(self.cues)//2,len(self.cues)-1),expected):
            with self.subTest(scene=stage):
                out=[]
                for phase in (.14,.55,.87):
                    frame,rec=draw_source_keyframe(
                        self.story,idx,phase,caption_layer="timed_ass_overlay")
                    self.assertEqual(frame.size,(1080,1920))
                    self.assertEqual(rec["distinct_original_visual_subject"],stage)
                    self.assertEqual(rec["original_subject_focal_zoom"],"expanded")
                    self.assertFalse(rec["hero_headline_repeats_full_spoken_sentence"])
                    self.assertTrue(rec["no_circle_spinner_drawn"])
                    self.assertTrue(rec["timed_ass_caption_overlay_required"])
                    self.assertFalse(rec["youtube_uploaded"])
                    self.assertEqual(rec["caption_source_sha256"],
                                     sha256(self.cues[idx]["source_text"].encode()).hexdigest())
                    hero=frame.crop((88,495,992,1384))
                    self.assertGreater(sum(ImageStat.Stat(hero).stddev),38,
                                       "Reject nearly blank lecture slide hero")
                    out.append(frame)
                # Only the bounded visual subject may animate. The header,
                # clean native ASS subtitle region and footer are preserved.
                for a,b in zip(out,out[1:]):
                    for bounds in ((0,0,1080,495),(0,1384,1080,1650)):
                        self.assertIsNone(ImageChops.difference(
                            a.crop(bounds),b.crop(bounds)).getbbox())
                    self.assertIsNotNone(ImageChops.difference(
                        a.crop((88,495,992,1384)),
                        b.crop((88,495,992,1384))).getbbox(),
                        "Finite, nonlooping info reveal must change actual pixels")

    def test_all_11_original_photo_beats_preserve_the_exact_pcm_source_contract(self):
        self.assertEqual(len(self.cues),11)
        self.assertIn("GPS coordinates",self.cues[1]["source_text"])
        self.assertIn("depends",self.cues[3]["source_text"])
        self.assertIn("without GPS",self.cues[9]["source_text"])
        for i,c in enumerate(self.cues):
            with self.subTest(i=i):
                frame,rec=draw_source_keyframe(
                    self.story,i,.76,caption_layer="timed_ass_overlay")
                self.assertEqual(rec["caption_source_sha256"],
                                 sha256(c["source_text"].encode()).hexdigest())
                self.assertEqual(frame.size,(1080,1920))
                self.assertTrue(rec["no_circle_spinner_drawn"])
                self.assertFalse(rec["hero_headline_repeats_full_spoken_sentence"])

    def test_no_fake_device_brand_actual_coordinates_spinner_or_upload(self):
        code=inspect.getsource(_draw_subject)
        for forbidden in ("d.arc(", "d.ellipse(", "while True:",
                          "requests.get(", "youtube.videos()", "random."):
            self.assertNotIn(forbidden,code)
        self.assertIn("MAY BE SAVED",code)
        self.assertIn("MAY BE INCLUDED",code)
        self.assertIn("CHECK SHARE OPTIONS",code)
        self.assertIn("PHOTO_METADATA_DISCOVERY",code)


if __name__=="__main__":
    unittest.main()
