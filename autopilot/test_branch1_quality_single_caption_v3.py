"""B1q3 owner screenshot corrective pass: one original caption, bigger subject."""
from __future__ import annotations
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from autopilot.branch1_three_narrated_no_spinner_v2 import _load_source,SOURCES
from autopilot.branch1_no_spinner_storyboard import (
    draw_source_keyframe,storyboard_cues,EDITORIAL_HEADLINES,EDITORIAL_STAGE,
)
from autopilot.branch1_quality_v3_gallery import (
    STATUS,render_nine_source_proofs,
)

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(importlib.util.find_spec("PIL") is not None,
                     "B1q3 original 1080p editorial geometry requires strict Pillow CI")
class RealSourceSingleCaptionAndLargeOriginalHeroTests(unittest.TestCase):
    def test_all_original_31_spoken_beats_are_not_duplicated_as_large_headings(self):
        from PIL import Image,ImageChops
        count=0
        for eid,_ in SOURCES:
            story=_load_source(ROOT,eid)
            cues=storyboard_cues(story)
            for i,c in enumerate(cues):
                with self.subTest(eid=eid,beat=i):
                    x,metadata=draw_source_keyframe(story,i,.74,caption_layer="original_source_proof")
                    self.assertEqual(x.size,(1080,1920))
                    self.assertNotEqual(metadata["editorial_headline"],c["source_text"])
                    self.assertFalse(metadata["headline_is_verbatim_audio_caption"])
                    self.assertTrue(metadata["visual_hero_enlarged_in_native_canvas"])
                    self.assertEqual(metadata["caption_source_sha256"],
                        sha256(c["source_text"].encode()).hexdigest())
                    self.assertEqual(metadata["editorial_headline_sha256"],
                        sha256(metadata["editorial_headline"].encode()).hexdigest())
                    self.assertEqual(metadata["source_episode_title_sha256"],
                        sha256(story["title"].encode()).hexdigest())
                    self.assertFalse(metadata["youtube_uploaded"])
                    native,receipt=draw_source_keyframe(story,i,.74,caption_layer="timed_ass_overlay")
                    self.assertEqual(metadata["editorial_headline"],receipt["editorial_headline"])
                    self.assertIsNone(ImageChops.difference(
                        x.crop((0,0,1080,1410)),native.crop((0,0,1080,1410))).getbbox())
                    self.assertIsNone(ImageChops.difference(
                        x.crop((0,1650,1080,1920)),native.crop((0,1650,1080,1920))).getbbox())
                    self.assertIsNotNone(ImageChops.difference(
                        x.crop((82,1410,998,1650)),
                        native.crop((82,1410,998,1650))).getbbox())
                    count+=1
        self.assertGreaterEqual(count,30)

    def test_three_original_editorial_headlines_per_video_no_template_repeat(self):
        for eid,_ in SOURCES:
            story=_load_source(ROOT,eid)
            cues=storyboard_cues(story)
            shots=[draw_source_keyframe(story,i,.8)[1] for i in (
                0,len(cues)//2,len(cues)-1)]
            self.assertEqual(len({v["editorial_headline"] for v in shots}),3)
            self.assertEqual(len({v["distinct_original_visual_subject"] for v in shots}),3)
            self.assertEqual(len(EDITORIAL_STAGE),3)
        self.assertEqual(len(EDITORIAL_HEADLINES),3)

    def test_hosted_original_nine_native_visuals_and_contact_sheet_are_readable_and_unsigned(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as p:
            out=Path(p)/"new"
            r=render_nine_source_proofs(ROOT,out)
            self.assertEqual(r["status"],STATUS)
            self.assertEqual(r["original_scene_count"],9)
            self.assertEqual(r["original_episodes_count"],3)
            self.assertFalse(r["new_video_encoded"])
            self.assertFalse(r["previous_youtube_uploaded_binary_mutated"])
            self.assertFalse(r["owner_fact_visual_voice_rights_approved"])
            self.assertEqual(len(list(out.glob("*.png"))),9)
            for item in r["scenes"]:
                name=out/item["file"]
                self.assertTrue(name.is_file() and name.stat().st_size>15000)
                self.assertEqual(item["bytes"],name.stat().st_size)
                self.assertEqual(item["sha256"],sha256(name.read_bytes()).hexdigest())
                with Image.open(name) as i:self.assertEqual(i.size,(1080,1920))
            self.assertTrue((out/r["contact_sheet"]).is_file())
            with self.assertRaises(ValueError):
                render_nine_source_proofs(ROOT,out)


if __name__=="__main__":
    unittest.main()
