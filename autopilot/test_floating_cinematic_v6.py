"""B4e4b physical editorial demo of 32 unboxed source-authored visual beats."""
from __future__ import annotations
import importlib.util
from pathlib import Path
from hashlib import sha256
import json
import tempfile
import unittest

from autopilot.floating_cinematic_v6 import (
    STATUS,paint_floating_original_beat,render_floating_source_proofs,
)
from autopilot.cinematic_editorial_grid_v5 import (
    STYLE,apply_source_cinematic_editorial_grid,
)
from autopilot.cinematic_scene_v3 import SCENE_PANEL,CinematicSceneRejected
from autopilot.primary_sourced_storyboards import (
    build_story,render_original_svg,
)


@unittest.skipUnless(
    importlib.util.find_spec("PIL") is not None
    and importlib.util.find_spec("cairosvg") is not None,
    "Real 1080p/portrait original art requires hosted Pillow and CairoSVG",
)
class OriginalNoBoxArtProofTests(unittest.TestCase):
    def _image(self,story,idx,tick=60):
        import io,cairosvg
        from PIL import Image
        return Image.open(io.BytesIO(cairosvg.svg2png(
            bytestring=render_original_svg(story,idx,tick).encode()))).convert("RGB")

    def test_all_32_source_scenes_have_no_giant_frame_or_caption_leakage(self):
        from PIL import ImageChops
        count=0
        for slot in ("short_am","long","short_pm"):
            story=build_story(slot)
            p=STYLE[story["theme"]]
            r=SCENE_PANEL[story["format"]]
            caption=(0,1295,1080,1570) if story["format"]=="short" else (
                0,756,1920,935)
            for idx in range(story["scene_count"]):
                with self.subTest(slot=slot,index=idx):
                    img=self._image(story,idx)
                    before=img.copy()
                    report=paint_floating_original_beat(
                        img,story=story,scene_index=idx,tick=60)
                    self.assertEqual(report["status"],STATUS)
                    self.assertTrue(report["old_bordered_presentation_panel_removed"])
                    self.assertFalse(report["reference_clip_media_reused"])
                    self.assertFalse(report["release_authorized"])
                    self.assertEqual(report["source_story_draft_sha256"],story["draft_sha256"])
                    # Old panel had a mint/blue frame at the entire outer
                    # rectangle. New source doesn't draw any perimeter.
                    self.assertEqual(img.getpixel((r[0]+2,r[1]+2)),p["bg"])
                    self.assertEqual(img.getpixel((r[2]-3,r[1]+2)),p["bg"])
                    self.assertIsNone(ImageChops.difference(
                        before.crop(caption),img.crop(caption)).getbbox())
                    self.assertIsNotNone(ImageChops.difference(
                        before.crop(r),img.crop(r)).getbbox())
                    pre_hero=img.copy()
                    edit=apply_source_cinematic_editorial_grid(
                        img,story=story,scene_index=idx)
                    self.assertTrue(edit["original_hero_untouched"])
                    self.assertEqual(pre_hero.crop(r).tobytes(),img.crop(r).tobytes())
                    count+=1
        self.assertEqual(count,32)

    def test_floating_object_and_light_move_across_voice_synchronized_ticks(self):
        from PIL import ImageChops
        for slot in ("short_am","long","short_pm"):
            story=build_story(slot)
            for scene in (0,3):
                with self.subTest(slot=slot,scene=scene):
                    hashes=[]
                    r=SCENE_PANEL[story["format"]]
                    for tick in (0,60,120):
                        im=self._image(story,scene,tick)
                        paint_floating_original_beat(
                            im,story=story,scene_index=scene,tick=tick)
                        hashes.append(sha256(im.crop(r).tobytes()).hexdigest())
                    self.assertEqual(len(set(hashes)),3)

    def test_six_shot_variations_not_identical_and_source_facts_unchanged(self):
        for slot in ("short_am","short_pm"):
            story=build_story(slot)
            hashes=set()
            for scene in range(6):
                im=self._image(story,scene)
                result=paint_floating_original_beat(
                    im,story=story,scene_index=scene,tick=60)
                hashes.add(sha256(im.crop(SCENE_PANEL["short"]).tobytes()).hexdigest())
                self.assertEqual(result["source_visible_metric_sha256"],
                    sha256(story["scenes"][scene]["display_value"].encode()).hexdigest())
            self.assertEqual(len(hashes),6)
        story=build_story("long")
        hashes=set()
        for scene in range(story["scene_count"]):
            im=self._image(story,scene)
            paint_floating_original_beat(im,story=story,scene_index=scene,tick=60)
            hashes.add(sha256(im.crop(SCENE_PANEL["long"]).tobytes()).hexdigest())
        self.assertEqual(len(hashes),20)

    def test_unknown_user_reference_and_tampered_scene_rejected(self):
        from PIL import Image
        story=build_story("short_am")
        original=Image.new("RGB",(1080,1920))
        for idx,tick in ((-1,60),(6,60),(0,-1),(0,121),(0,3.5)):
            with self.subTest(scene=idx,tick=tick),self.assertRaises(
                CinematicSceneRejected
            ):
                paint_floating_original_beat(
                    original.copy(),story=story,scene_index=idx,tick=tick)
        with self.assertRaises(CinematicSceneRejected):
            paint_floating_original_beat(
                Image.new("RGB",(450,806)),
                story=story,scene_index=0,tick=60)

    def test_actual_public_before_after_samples_are_drawn_and_not_owner_approved(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/"new-visual-proof"
            result=render_floating_source_proofs(out)
            self.assertEqual(result["status"],STATUS)
            self.assertEqual(len(result["source_only_real_visual_previews"]),7)
            self.assertFalse(result["owner_visual_approved"])
            self.assertFalse(result["full_movie_video_encoded"])
            self.assertFalse(result["youtube_upload_enabled"])
            image_files=list(out.glob("*.png"))
            self.assertEqual(len(image_files),21)
            for shot in result["source_only_real_visual_previews"]:
                self.assertFalse(shot["reference_clip_copied"])
                self.assertFalse(shot["release_authorized"])
                for field in ("before_image","after_image","comparison_image"):
                    p=out/shot[field]
                    self.assertTrue(p.is_file())
                    self.assertGreater(p.stat().st_size,12000)
            saved=json.loads((out/"UNAPPROVED_FLOATING_STORYBOARD_MANIFEST.json").read_text())
            self.assertFalse(saved["full_movie_video_encoded"])
            with self.assertRaises(CinematicSceneRejected):
                render_floating_source_proofs(out)


if __name__=="__main__":
    unittest.main()
