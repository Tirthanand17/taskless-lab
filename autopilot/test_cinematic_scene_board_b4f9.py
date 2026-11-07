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

    def test_case_bound_pixels_change_for_next_day_without_caption_animation(self):
        from datetime import date,timedelta
        from PIL import ImageChops
        from autopilot.cinematic_scene_board_b4f9 import render_editorial_frame
        from autopilot.nonfactual_narration_rehearsal import _daily_case
        for ep in self.plan["episodes"]:
            scene=ep["scenes"][0]
            before=render_editorial_frame(ep,scene,revealed=False)
            stamp=ep["episode_id"].split("_")[1]
            next_date=(date(int(stamp[:4]),int(stamp[4:6]),
                            int(stamp[6:]))+timedelta(days=1))
            next_title=_daily_case(ep["synthetic_case_family"],ep["slot"],
                                   next_date.isoformat())[0]["story_name"]
            edited={**ep,"episode_id":"fm_"+next_date.strftime("%Y%m%d")
                    +"_"+ep["slot"],"synthetic_case_title":next_title}
            self.assertNotEqual(next_title,ep["synthetic_case_title"])
            after=render_editorial_frame(edited,scene,revealed=False)
            # Same 11-grammar storyboard now physically identifies the
            # unique original fictional case in the scene-safe header.
            self.assertIsNotNone(ImageChops.difference(
                before.crop((80,608,874,684)),
                after.crop((80,608,874,684))).getbbox())
            self.assertEqual(before.getpixel((540,1680) if ep["kind"]=="short"
                                             else (960,883)),
                             after.getpixel((540,1680) if ep["kind"]=="short"
                                             else (960,883)))

    def test_real_diagram_pixels_follow_case_semantics_not_just_case_name(self):
        from PIL import ImageChops
        from datetime import date,timedelta
        from autopilot.nonfactual_narration_rehearsal import _daily_case
        from autopilot.cinematic_scene_board_b4f9 import render_editorial_frame
        for ep in self.plan["episodes"]:
            scene=ep["scenes"][0]
            first=render_editorial_frame(ep,scene,revealed=True,focus_index=0)
            stamp=ep["episode_id"].split("_")[1]
            next_date=date(int(stamp[:4]),int(stamp[4:6]),
                           int(stamp[6:]))+timedelta(days=1)
            new_title=_daily_case(ep["synthetic_case_family"],ep["slot"],
                                   next_date.isoformat())[0]["story_name"]
            varied={**ep,"episode_id":"fm_"+next_date.strftime("%Y%m%d")
                    +"_"+ep["slot"],"synthetic_case_title":new_title}
            second=render_editorial_frame(varied,scene,
                                           revealed=True,focus_index=0)
            diagram=(75,690,1005,1395) if ep["kind"]=="short" else (
                     932,184,1840,705)
            self.assertIsNotNone(ImageChops.difference(
                first.crop(diagram),second.crop(diagram)).getbbox(),
                (ep["slot"],"Case scenario chart remains generic"))
            # Neither variation is allowed to animate the actual captions.
            px=(540,1680) if ep["kind"]=="short" else (960,883)
            self.assertEqual(first.getpixel(px),second.getpixel(px))

    def test_curated_large_native_card_words_physically_fit_both_canvases(self):
        from PIL import Image,ImageDraw
        from autopilot.real_rehearsal_voice_media_b4e0 import _font
        from autopilot.synthetic_case_diagram_labels_b4h2 import CASE_STEPS
        d=ImageDraw.Draw(Image.new("RGB",(1,1)))
        for words in CASE_STEPS.values():
            for label in words:
                # Compare cards are the strictest: each column is 423/1000
                # of its graphic. 69px native portrait text, 54px landscape.
                for px,allowed in ((69,363),(54,338)):
                    bounds=d.textbbox((0,0),label,font=_font(px))
                    self.assertLessEqual(bounds[2],allowed,(label,px,bounds))

    def test_case_metadata_mismatch_invalid_date_and_article_text_rejected(self):
        from autopilot.cinematic_scene_board_b4f9 import (
            render_editorial_frame,SceneDesignRefused,
        )
        ep=self.plan["episodes"][0]
        scene=ep["scenes"][0]
        bad=[
            {**ep,"synthetic_case_family":"another topic"},
            {**ep,"synthetic_case_title":"Reported public headline here"},
            {**ep,"synthetic_case_title":""},
            {**ep,"synthetic_case_title":None},
            {**ep,"episode_id":"fm_20260230_short_am"},
            {**ep,"episode_id":"fm_20261107_long"},
            {**ep,"episode_id":"not a valid source day"},
        ]
        for forgery in bad:
            with self.subTest(forgery=repr(forgery.get("synthetic_case_title"))), self.assertRaises(SceneDesignRefused):
                render_editorial_frame(forgery,scene,revealed=False)

    def test_all_forty_two_case_labels_fit_real_native_glyph_bounds(self):
        from PIL import Image,ImageDraw
        from autopilot.real_rehearsal_voice_media_b4e0 import _font
        from autopilot.nonfactual_narration_rehearsal import CASEBOOK
        draw=ImageDraw.Draw(Image.new("RGB",(1,1)))
        for items in CASEBOOK.values():
            for case in items:
                title="CASE / "+case[0].upper()
                for portrait in (True,False):
                    x=88
                    size=29 if portrait else 28
                    bound=draw.textbbox((x,638 if portrait else 615),
                                        title,font=_font(size))
                    self.assertLessEqual(bound[2],1000 if portrait else 874,
                                         (case[0],portrait,bound))

    def test_no_generic_old_title_spilled_back_into_first_frame(self):
        from autopilot.cinematic_scene_board_b4f9 import BEATS
        first=BEATS["HOOK_QUESTION"]
        self.assertEqual(first[1],("IS IT","REALLY TRUE?"))
        self.assertNotIn("Testing a claim",repr(first))
        self.assertNotIn("simulated news result",repr(first).lower())


if __name__=="__main__":
    unittest.main()
