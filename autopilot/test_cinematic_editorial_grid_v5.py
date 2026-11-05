"""B4e4a physical original source typography grid and exact subtitle-safe tests.

This tests the REAL pixel-level output for ALL 32 script scenes: 20 long,
6+6 Shorts; the old screenshot showed title overlapping the brand and footer
text underneath the broken progress bar. New cinematic art and ASS band are
never touched by overlay repair. Legacy v2 source remains unchanged.
"""
from __future__ import annotations

import importlib.util
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest

from autopilot.cinematic_editorial_grid_v5 import (
    EditorialAlignmentRejected,STATUS,apply_source_cinematic_editorial_grid,
)
from autopilot.primary_sourced_storyboards import build_story
from autopilot.full_topic_narrated_pack import _topic_png


@unittest.skipUnless(
    importlib.util.find_spec("PIL") is not None
    and importlib.util.find_spec("cairosvg") is not None,
    "Real pixel typography mandatory in dedicated Pillow/CairoSVG hosted action",
)
class NoOverlapSourceEditorialGridTests(unittest.TestCase):
    def test_all_32_original_title_value_and_scene_label_have_no_collisions(self):
        from PIL import Image,ImageChops
        total=0
        for slot in ("short_am","long","short_pm"):
            story=build_story(slot)
            for idx in range(story["scene_count"]):
                with self.subTest(slot=slot,scene=idx):
                    w,h=(1080,1920) if story["format"]=="short" else (1920,1080)
                    # Make distinct yellow signal/hero sample bytes that
                    # must survive even a top/footer repaint.
                    im=Image.new("RGB",(w,h),(23,37,51))
                    if story["format"]=="long":
                        hero=(0,280,w,720);captions=(0,756,w,935)
                    else:
                        hero=(0,533,w,1220);captions=(0,1295,w,1570)
                    p=im.load()
                    p[hero[0]+100,hero[1]+125]=(244,199,33)
                    p[50,captions[1]+15]=(177,88,224)
                    before=im.copy()
                    rec=apply_source_cinematic_editorial_grid(
                        im,story=story,scene_index=idx)
                    self.assertEqual(rec["status"],STATUS)
                    self.assertEqual(rec["original_source_story_draft_sha256"],
                                     story["draft_sha256"])
                    self.assertEqual(rec["source_title_exact_text_sha256"],
                        sha256(story["scenes"][idx]["display_title"].encode()).hexdigest())
                    self.assertEqual(rec["source_metric_exact_text_sha256"],
                        sha256(story["scenes"][idx]["display_value"].encode()).hexdigest())
                    self.assertFalse(rec["brand_and_title_collisions"])
                    self.assertFalse(rec["footer_caption_collision"])
                    self.assertFalse(rec["release_authorized"])
                    self.assertTrue(rec["original_hero_untouched"])
                    self.assertIsNone(ImageChops.difference(
                        before.crop(hero),im.crop(hero)).getbbox())
                    self.assertIsNone(ImageChops.difference(
                        before.crop(captions),im.crop(captions)).getbbox())
                    self.assertLessEqual(len(rec["title_bounding_rectangles"]),2)
                    total+=1
        self.assertEqual(total,32)

    def test_source_long_scene_00_physical_new_top_and_footer_differ(self):
        from PIL import Image,ImageChops
        story=build_story("long")
        with tempfile.TemporaryDirectory() as t:
            a=Path(t)/"classic.png";b=Path(t)/"cinematic.png"
            _topic_png(story,0,60,a,visual_style="classic_v2")
            _topic_png(story,0,60,b,visual_style="cinematic_v3")
            with Image.open(a) as x,Image.open(b) as y:
                # Original SVG brands overlap (top W1080/H608). The new
                # 1920x1080 grid moves labels, and footer is intentionally
                # distinct. But pure ASS band remains exact bitwise.
                self.assertIsNotNone(ImageChops.difference(
                    x.crop((0,0,1920,270)),
                    y.crop((0,0,1920,270))
                ).getbbox())
                self.assertIsNotNone(ImageChops.difference(
                    x.crop((0,936,1920,1080)),
                    y.crop((0,936,1920,1080))
                ).getbbox())
                self.assertIsNone(ImageChops.difference(
                    x.crop((0,756,1920,935)),
                    y.crop((0,756,1920,935))
                ).getbbox())

    def test_bad_source_mode_index_dimensions_or_reference_title_rejected(self):
        from PIL import Image
        story=build_story("short_am")
        cases=[
            {"scene_index":-1},
            {"scene_index":6},
            {"scene_index":0,"image":Image.new("RGB",(450,806))},
            {"scene_index":0,"image":Image.new("RGBA",(1080,1920))},
        ]
        for case in cases:
            with self.subTest(case=str(case["scene_index"])):
                im=case.get("image",Image.new("RGB",(1080,1920)))
                with self.assertRaises(EditorialAlignmentRejected):
                    apply_source_cinematic_editorial_grid(
                        im,story=story,scene_index=case["scene_index"])


if __name__=="__main__":
    unittest.main()
