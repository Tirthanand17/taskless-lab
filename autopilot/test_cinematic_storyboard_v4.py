"""B4e3 physical storyboard comparison gates: 2 Shorts and LONG.

No mock upload or human approval. Real Pillow/CairoSVG frame differences
and FFmpeg encoded media are checked in the separate hosted real-video job.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from hashlib import sha256
import tempfile
import unittest

from autopilot.primary_sourced_storyboards import build_story
from autopilot.full_topic_narrated_pack import _topic_png,TopicRenderError
from autopilot.cinematic_storyboard_v4 import STATUS


@unittest.skipUnless(
    importlib.util.find_spec("PIL") is not None and
    importlib.util.find_spec("cairosvg") is not None,
    "B4e3 physically drawn scene QA requires Pillow/CairoSVG, mandated in dedicated workflow",
)
class ActualCinematicShortAndLongFrameTests(unittest.TestCase):
    def test_three_formats_original_frames_are_distinct_and_subtitles_untouched(self):
        from PIL import Image,ImageChops
        for slot in ("short_am","long","short_pm"):
            with self.subTest(slot=slot),tempfile.TemporaryDirectory() as t:
                root=Path(t)
                story=build_story(slot)
                old=root/"classic.png";new=root/"cinematic.png"
                oldhash=_topic_png(story,0,60,old,visual_style="classic_v2")
                newhash=_topic_png(story,0,60,new,visual_style="cinematic_v3")
                self.assertNotEqual(oldhash,newhash)
                with Image.open(old) as a,Image.open(new) as b:
                    a=a.convert("RGB");b=b.convert("RGB")
                    self.assertEqual(a.size,b.size)
                    self.assertEqual(
                        a.size,(1080,1920) if story["format"]=="short" else (1920,1080))
                    top=1295 if story["format"]=="short" else 756
                    self.assertIsNone(ImageChops.difference(
                        a.crop((0,top,a.width,a.height)),
                        b.crop((0,top,b.width,b.height))
                    ).getbbox(), "cinematic images must NOT alter ASS caption-safe area")
                    # Requires materially different central ORIGINAL science art;
                    # a renamed or recolored unchanged panel is not accepted.
                    diff=ImageChops.difference(a,b).convert("L")
                    crop=(74,533,1006,1220) if story["format"]=="short" else (130,280,1790,720)
                    region=diff.crop(crop)
                    self.assertIsNotNone(region.getbbox())
                    nonzero=sum(1 for value in region.resize((140,90)).getdata()
                                if value>24)
                    self.assertGreater(nonzero,550,f"{slot} visual improvement was trivial")

    def test_all_five_long_story_shots_are_visually_distinct(self):
        from PIL import Image
        story=build_story("long")
        hashes=[]
        with tempfile.TemporaryDirectory() as t:
            for scene_index in range(5):
                p=Path(t)/f"long_source_beat_{scene_index}.png"
                _topic_png(story,scene_index,60,p,visual_style="cinematic_v3")
                with Image.open(p) as im:
                    hashes.append(sha256(im.crop((130,280,1790,720)).tobytes()).hexdigest())
        self.assertEqual(len(set(hashes)),5)

    def test_shorts_have_source_specific_scene_visuals_and_motion(self):
        from PIL import ImageChops,Image
        for slot in ("short_am","short_pm"):
            with self.subTest(slot=slot),tempfile.TemporaryDirectory() as t:
                story=build_story(slot)
                versions=[]
                for scene,tick in ((0,0),(0,60),(0,120),(1,60),(3,60)):
                    p=Path(t)/f"frame{scene}_{tick}.png"
                    _topic_png(story,scene,tick,p,visual_style="cinematic_v3")
                    with Image.open(p) as im:
                        versions.append(im.convert("RGB").crop((74,533,1006,1220)).copy())
                self.assertTrue(all(ImageChops.difference(x,y).getbbox()
                    for x,y in zip(versions,versions[1:])))

    def test_user_reference_assets_and_fake_visual_modes_are_refused(self):
        with tempfile.TemporaryDirectory() as t:
            story=build_story("short_am")
            with self.assertRaises(TopicRenderError):
                _topic_png(story,0,60,Path(t)/"wrong.png",
                           visual_style="third_party_reference")
            with self.assertRaises(TopicRenderError):
                _topic_png(story,0,60,Path(t)/"wrong2.png",
                           visual_style="copyrighted_3d_templates")

    def test_source_claim_no_release_status_is_unchanged(self):
        self.assertIn("UNAPPROVED",STATUS)
        for slot in ("short_am","long","short_pm"):
            story=build_story(slot)
            self.assertFalse(story["release_authorized"])
            self.assertFalse(story["youtube_upload_enabled"])


if __name__=="__main__":
    unittest.main()
