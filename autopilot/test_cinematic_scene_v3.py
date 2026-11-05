"""B4e2 adversarial physical ORIGINAL dimensional art and safe-zone tests."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest

from autopilot.cinematic_scene_v3 import (
    CinematicSceneRejected,PALETTE,SCENE_PANEL,SIZES,STATUS,
    paint_original_premium_scene,render_real_source_scene_preview_set,
)


class OriginalCinematicSceneTests(unittest.TestCase):
    def test_all_three_original_topics_have_real_distinct_pixel_art(self):
        from PIL import Image,ImageChops
        hashes=[]
        for theme,kind in (
            ("lunar_signal","short"),
            ("file_transfer","long"),
            ("quake_energy","short"),
        ):
            with self.subTest(theme=theme):
                dims=SIZES[kind]
                bg=PALETTE[theme]["bg"]
                x0,y0,x1,y1=SCENE_PANEL[kind]
                img=Image.new("RGB",dims,bg)
                old=img.copy()
                r=paint_original_premium_scene(
                    img,theme=theme,kind=kind,
                    scene_index=0,scene_count=6 if kind=="short" else 20,
                    tick=60)
                self.assertEqual(r["status"],STATUS)
                self.assertFalse(r["reference_clip_assets_copied"])
                self.assertFalse(r["human_visual_review_completed"])
                self.assertFalse(r["release_authorized"])
                self.assertEqual(img.size,dims)
                self.assertIsNone(ImageChops.difference(
                    img.crop((0,0,dims[0],y0-3)),
                    old.crop((0,0,dims[0],y0-3)),
                ).getbbox())
                caption_top=1295 if kind=="short" else 756
                self.assertIsNone(ImageChops.difference(
                    img.crop((0,caption_top,dims[0],dims[1])),
                    old.crop((0,caption_top,dims[0],dims[1])),
                ).getbbox())
                center=img.crop((x0,y0,x1,y1))
                self.assertGreater(len(center.getcolors(1000000) or []),80)
                self.assertNotEqual(center.getpixel((30,30)),center.getpixel(
                    ((x1-x0)//2,(y1-y0)//2)))
                hashes.append(sha256(center.tobytes()).hexdigest())
        self.assertEqual(len(set(hashes)),3)

    def test_perspective_subject_animation_has_bounded_actual_pixel_motion(self):
        from PIL import Image,ImageChops
        for theme,kind in (
            ("lunar_signal","short"),
            ("quake_energy","short"),
            ("file_transfer","long"),
        ):
            images=[]
            for tick in (0,60,120):
                base=Image.new("RGB",SIZES[kind],PALETTE[theme]["bg"])
                paint_original_premium_scene(base,theme=theme,
                    kind=kind,scene_index=2,scene_count=6 if kind=="short" else 20,
                    tick=tick)
                images.append(base)
            rect=SCENE_PANEL[kind]
            for left,right in zip(images,images[1:]):
                diff=ImageChops.difference(left.crop(rect),right.crop(rect))
                self.assertIsNotNone(diff.getbbox(),f"{theme} is static")
                # Deliberate movement, not full-frame strobing.
                self.assertGreater(sum(1 for px in diff.convert("L").getdata() if px>35),120)

    def test_invalid_storyboard_theme_format_timing_or_owner_injection_fails(self):
        from PIL import Image
        image=Image.new("RGB",(1080,1920),(1,2,3))
        bad_cases=(
            {"theme":"copyrighted_creator_reference"},
            {"kind":"landscape-but-portrait"},
            {"scene_index":-1},
            {"scene_index":8},
            {"scene_count":0},
            {"scene_count":100},
            {"tick":-1},
            {"tick":121},
            {"tick":1.1},
        )
        defaults=dict(theme="lunar_signal",kind="short",scene_index=0,
                      scene_count=6,tick=30)
        for i,change in enumerate(bad_cases):
            args=defaults.copy()
            args.update(change)
            with self.subTest(index=i),self.assertRaises(CinematicSceneRejected):
                paint_original_premium_scene(image.copy(),**args)
        with self.assertRaises(CinematicSceneRejected):
            paint_original_premium_scene(Image.new("RGB",(450,806)),
                **defaults)

    def test_actual_fixed_public_original_scene_artifacts_are_previewable(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/"source-visual-proofs"
            try:
                result=render_real_source_scene_preview_set(root)
            except ImportError:
                self.fail("Dedicated test environment must install original CairoSVG and Pillow")
            self.assertEqual(result["status"],STATUS)
            self.assertEqual(len(result["prototypes"]),3)
            self.assertEqual([x["format"] for x in result["prototypes"]],
                             ["short","long","short"])
            self.assertFalse(result["actual_3d_modeling_claimed"])
            self.assertFalse(result["release_authorized"])
            for item in result["prototypes"]:
                path=root/item["file"]
                self.assertGreater(item["bytes"],40000)
                self.assertEqual(sha256(path.read_bytes()).hexdigest(),
                                 item["sha256"])
                with Image.open(path) as actual:
                    self.assertEqual(actual.size,SIZES[item["format"]])
                self.assertFalse(item["actual_human_approved"])
            with self.assertRaises(CinematicSceneRejected):
                render_real_source_scene_preview_set(root)

    def test_public_review_is_not_an_owner_signed_approval_or_3d_claim(self):
        self.assertTrue("ORIGINAL_PIL_2POINT5D" in STATUS)
        self.assertEqual(set(PALETTE),{"lunar_signal","file_transfer","quake_energy"})
        self.assertEqual(set(SCENE_PANEL),{"short","long"})


if __name__=="__main__":
    unittest.main()
