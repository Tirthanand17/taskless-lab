"""B4e4c actual full-video source frame integration: both Shorts and LONG.

The actual media encode runs on trusted main only after these source/caption
and original unboxed scene tests pass in GitHub PR. The entire existing
classic_v2 and cinematic_v3 behavior must remain available.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest
from hashlib import sha256

from autopilot.primary_sourced_storyboards import build_story
from autopilot.full_topic_narrated_pack import _topic_png,TopicRenderError
from autopilot.cinematic_scene_v3 import SCENE_PANEL


@unittest.skipUnless(
    importlib.util.find_spec("PIL") is not None
    and importlib.util.find_spec("cairosvg") is not None,
    "Physical source-video frame integration runs in dedicated Pillow/CairoSVG CI",
)
class RealUnboxedRenderedSourceFrameTests(unittest.TestCase):
    def test_true_native_encoded_source_frame_preserves_caption_and_heading_and_removes_box(self):
        from PIL import Image,ImageChops
        for slot in ("short_am","long","short_pm"):
            story=build_story(slot)
            caption=(0,1295,1080,1570) if story["format"]=="short" else (
                0,756,1920,935)
            r=SCENE_PANEL[story["format"]]
            with self.subTest(slot=slot),tempfile.TemporaryDirectory() as t:
                old=Path(t)/"boxed.png"
                new=Path(t)/"floating.png"
                _topic_png(story,0,60,old,visual_style="cinematic_v3")
                _topic_png(story,0,60,new,visual_style="floating_v6")
                with Image.open(old) as x,Image.open(new) as y:
                    a=x.convert("RGB");b=y.convert("RGB")
                    self.assertEqual(a.size,b.size)
                    self.assertIsNone(ImageChops.difference(
                        a.crop(caption),b.crop(caption)).getbbox(),
                        "Original ASS subtitles masked and safe in both video styles")
                    self.assertIsNone(ImageChops.difference(
                        a.crop((0,0,a.width,r[1])),
                        b.crop((0,0,b.width,r[1]))).getbbox(),
                        "B4e4a source heading and metric must remain identical")
                    self.assertIsNotNone(ImageChops.difference(
                        a.crop(r),b.crop(r)).getbbox(),
                        "New floating full-video frame differs from giant boxed stage")
                    self.assertEqual(b.getpixel((r[0]+2,r[1]+2)),
                        {"lunar_signal":(9,15,37),
                         "file_transfer":(10,27,39),
                         "quake_energy":(33,19,26)}[story["theme"]])

    def test_all_20_long_and_12_short_source_beats_produce_original_video_frame(self):
        from PIL import Image
        for slot in ("short_am","long","short_pm"):
            story=build_story(slot)
            hashes=set()
            with tempfile.TemporaryDirectory() as t:
                for idx in range(story["scene_count"]):
                    path=Path(t)/f"shot_{idx:02d}.png"
                    digest=_topic_png(story,idx,60,path,visual_style="floating_v6")
                    self.assertEqual(digest,sha256(path.read_bytes()).hexdigest())
                    with Image.open(path) as img:
                        self.assertEqual(img.size,(1080,1920)
                            if story["format"]=="short" else (1920,1080))
                        hashes.add(sha256(img.crop(SCENE_PANEL[story["format"]]).tobytes()).hexdigest())
            self.assertEqual(len(hashes),story["scene_count"])

    def test_malicious_or_unknown_visual_style_refused(self):
        story=build_story("short_am")
        with tempfile.TemporaryDirectory() as t:
            for mode in ("borrowed_copyright_video","true-3d-claimed","floating_v5"):
                with self.subTest(mode=mode),self.assertRaises(TopicRenderError):
                    _topic_png(story,0,60,Path(t)/f"{mode}.png",visual_style=mode)

if __name__=="__main__":
    unittest.main()
