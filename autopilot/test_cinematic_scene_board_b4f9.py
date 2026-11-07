"""B4f9 physically validate 17 distinct editable original storyboard frames.

A visual quality failure is a FAIL, not an automatic owner approval.
All test scenes are synthetic; no rights, internet, OAuth or YouTube.
"""
from __future__ import annotations
from hashlib import sha256
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from autopilot.nonfactual_narration_rehearsal import build_nonfactual_rehearsals
from autopilot.test_nonfactual_narration_rehearsal_b4d9 import pipeline
from autopilot.full_original_rehearsal_media_b4e1 import (
    SCENE_CARD_WORDS, FullRehearsalRefused,
    _draw_original_full_scene, prepare_full_rehearsal_plan,
)


@unittest.skipUnless(importlib.util.find_spec("PIL"),
                     "Pillow installed only in the real media CI worker")
class EditorialSceneIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from autopilot.cinematic_scene_board_b4f9 import BEATS, CARD_WORDS, THEMES
        cls.BEATS=BEATS
        cls.CARD_WORDS=CARD_WORDS
        cls.THEMES=THEMES
        cls.original=pipeline()
        cls.rehearsals=build_nonfactual_rehearsals(*cls.original)
        cls.plan=prepare_full_rehearsal_plan(*cls.original,cls.rehearsals)

    def test_all_eleven_scene_beats_have_distinct_titles_and_four_layouts(self):
        self.assertEqual(set(self.BEATS),set(SCENE_CARD_WORDS))
        self.assertEqual(self.CARD_WORDS,SCENE_CARD_WORDS)
        self.assertEqual(set(self.THEMES),{"short_am","long","short_pm"})
        names=[tuple(v[1]) for v in self.BEATS.values()]
        self.assertEqual(len(set(names)),11)
        self.assertEqual({x[3] for x in self.BEATS.values()},
                         {"compare","steps","matrix","gate"})
        self.assertTrue(all(len(v[1])==2 for v in self.BEATS.values()))

    def test_actual_pillow_17_original_unique_scenes_and_once_only_reveals(self):
        from PIL import Image,ImageChops
        with TemporaryDirectory() as directory:
            out=Path(directory)
            count=0
            for ep in self.plan["episodes"]:
                all_hashes=[]
                expected=(1080,1920) if ep["kind"]=="short" else (1920,1080)
                for scene in ep["scenes"]:
                    base=out/ep["slot"]/f"{scene['scene']}-base.png"
                    highlight=out/ep["slot"]/f"{scene['scene']}-highlight.png"
                    before=_draw_original_full_scene(
                        ep,scene,base,revealed=False)
                    after=_draw_original_full_scene(
                        ep,scene,highlight,revealed=True)
                    self.assertNotEqual(before,after)
                    all_hashes.append(after)
                    with Image.open(base) as a,Image.open(highlight) as b:
                        a.load();b.load()
                        self.assertEqual(a.size,expected)
                        self.assertEqual(b.size,expected)
                        self.assertEqual(a.mode,"RGB")
                        self.assertEqual(b.mode,"RGB")
                        # All animation changes happen in one original scene
                        # diagram, never inside B4f7 native subtitle card.
                        diff=ImageChops.difference(a,b)
                        bbox=diff.getbbox()
                        self.assertIsNotNone(bbox)
                        if ep["kind"]=="short":
                            self.assertGreaterEqual(bbox[1],690)
                            self.assertLessEqual(bbox[3],1395)
                        else:
                            self.assertGreaterEqual(bbox[1],184)
                            self.assertLessEqual(bbox[3],705)
                        # The subtitle card stays a clean nonanimated panel.
                        center=(540,1680) if ep["kind"]=="short" else (960,883)
                        self.assertEqual(a.getpixel(center),b.getpixel(center))
                    count+=1
                self.assertEqual(len(set(all_hashes)),ep["all_scene_count"])
            self.assertEqual(count,17)

    def test_untrusted_scene_metadata_never_generates_an_approved_image(self):
        from autopilot.cinematic_scene_board_b4f9 import (
            render_editorial_frame,SceneDesignRefused,
        )
        ep=self.plan["episodes"][0]
        scene=ep["scenes"][0]
        mutations=[
            ({**ep,"slot":"random"},scene),
            ({**ep,"all_scene_count":99},scene),
            ({**ep,"size":[1440,1920]},scene),
            (ep,{**scene,"scene_id":"FAKE_APPROVED_NEWS"}),
            (ep,{**scene,"scene":-1}),
            (ep,{**scene,"scene":True}),
        ]
        for changed,beat in mutations:
            with self.subTest(changed=changed,beat=beat),self.assertRaises(
                  SceneDesignRefused):
                render_editorial_frame(changed,beat,revealed=False)
        with self.assertRaises(SceneDesignRefused):
            render_editorial_frame(ep,scene,revealed="yes")

    def test_no_generic_old_title_spilled_back_into_first_frame(self):
        from autopilot.cinematic_scene_board_b4f9 import BEATS
        first=BEATS["HOOK_QUESTION"]
        self.assertEqual(first[1],("IS IT","REALLY TRUE?"))
        self.assertNotIn("Testing a claim",repr(first))
        self.assertNotIn("simulated news result",repr(first).lower())


if __name__=="__main__":
    unittest.main()
