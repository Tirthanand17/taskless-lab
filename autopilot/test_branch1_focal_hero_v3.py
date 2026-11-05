"""Branch 1 B1q3b physically test focal visual scale, keep B1q2b PCM fix intact."""
from __future__ import annotations
from hashlib import sha256
import importlib.util
from pathlib import Path
import tempfile
import unittest

from autopilot.branch1_no_spinner_storyboard import (
    draw_source_keyframe,storyboard_cues,NoSpinnerVisualRejected,
)
from autopilot.branch1_three_narrated_no_spinner_v2 import _load_source,SOURCES

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(importlib.util.find_spec("PIL") is not None,
                     "Native original Pillow 1080x1920 pixel proof required")
class ThreeOriginalFocalHeroClippingTests(unittest.TestCase):
    def test_every_original_narrated_beat_has_greater_source_hero_focus_and_same_safe_bands(self):
        from PIL import ImageChops
        count=0
        for eid,_ in SOURCES:
            source=_load_source(ROOT,eid)
            for i,c in enumerate(storyboard_cues(source)):
                with self.subTest(eid=eid,beat=i):
                    old,receipt_old=draw_source_keyframe(
                        source,i,.72,caption_layer="timed_ass_overlay",hero_zoom="original")
                    new,receipt_new=draw_source_keyframe(
                        source,i,.72,caption_layer="timed_ass_overlay",hero_zoom="expanded")
                    self.assertEqual(new.size,(1080,1920))
                    self.assertEqual(receipt_new["original_subject_focal_zoom"],"expanded")
                    self.assertFalse(receipt_old["original_subject_focal_zoom_bounded_to_y495_1383"])
                    self.assertTrue(receipt_new["original_subject_focal_zoom_bounded_to_y495_1383"])
                    self.assertFalse(receipt_new["hero_headline_repeats_full_spoken_sentence"])
                    self.assertFalse(receipt_new["youtube_uploaded"])
                    self.assertEqual(receipt_new["caption_source_sha256"],
                        sha256(c["source_text"].encode()).hexdigest())
                    # EXACTLY preserve source-authored upper hierarchy and
                    # independent ASS caption band y1410..1650 plus footer.
                    for safe in ((0,0,1080,495),(0,1384,1080,1920)):
                        self.assertIsNone(ImageChops.difference(
                            old.crop(safe),new.crop(safe)).getbbox(),
                            "No other original content altered by hero crop and resize")
                    changed=ImageChops.difference(
                        old.crop((0,495,1080,1384)),
                        new.crop((0,495,1080,1384)))
                    self.assertIsNotNone(changed.getbbox(),
                        "Original conceptual subject must physically differ")
                    count+=1
        self.assertEqual(count,31)

    def test_no_focal_zoom_state_outside_two_source_modes(self):
        src=_load_source(ROOT,SOURCES[0][0])
        for invalid in ("loop-zoom","360-rotation",None,""):
            with self.subTest(mode=invalid),self.assertRaises(NoSpinnerVisualRejected):
                draw_source_keyframe(src,0,.5,hero_zoom=invalid)

    def test_old_and_new_motion_same_topic_and_caption_no_new_claims(self):
        from PIL import ImageChops
        for eid,_ in SOURCES:
            source=_load_source(ROOT,eid)
            p=(0,len(storyboard_cues(source))//2,len(storyboard_cues(source))-1)
            variants=set()
            for idx in p:
                old,a=draw_source_keyframe(
                    source,idx,.8,hero_zoom="original",caption_layer="timed_ass_overlay")
                new,b=draw_source_keyframe(
                    source,idx,.8,hero_zoom="expanded",caption_layer="timed_ass_overlay")
                self.assertEqual(a["distinct_original_visual_subject"],b["distinct_original_visual_subject"])
                self.assertEqual(a["hero_editorial_headline"],b["hero_editorial_headline"])
                self.assertEqual(a["caption_source_sha256"],b["caption_source_sha256"])
                variants.add(b["distinct_original_visual_subject"])
            self.assertEqual(len(variants),3)

if __name__=="__main__":
    unittest.main()
