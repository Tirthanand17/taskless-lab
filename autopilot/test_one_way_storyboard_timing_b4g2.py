"""B4g2 actual original scene visual progression and audio hold bounds.

Only test-time synthetic educational images; no TTS, YouTube or credentials.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
import math
import unittest

from autopilot.one_way_storyboard_timing_b4g2 import (
    OneWayStageRefused,active_focus_sequence,stage_hold_seconds,
    SOURCE_SCENE_GRAMMAR,grammar_for_original_scene,
)


class NarrationPacedDistinctStageTests(unittest.TestCase):
    def test_every_scene_has_one_way_no_repeat_hold_schedule(self):
        for grammar in ("compare","gate","matrix","steps"):
            sequence=active_focus_sequence(grammar)
            self.assertEqual(sequence[0],None)
            self.assertEqual(sequence[1:],tuple(range(len(sequence)-1)))
            self.assertEqual(len(set(sequence)),len(sequence))
            for total in (11.1,14.4,24.5,39.8):
                holds=stage_hold_seconds(total,len(sequence),.36)
                self.assertEqual(len(holds),len(sequence))
                self.assertAlmostEqual(sum(holds),total,places=6)
                self.assertEqual(holds[0],.36)
                self.assertTrue(all(x>=1.5 for x in holds[1:]))
                self.assertAlmostEqual(holds[-1],holds[-2],places=6)

    def test_duration_or_grammar_forgery_refused(self):
        invalid=((float("nan"),3,.36),(14,2,.36),(14,5,.36),
                 (14,True,.36),(14,3,True),(14,3,-1),(14,3,1.3),
                 (1,4,.36), (55.1,3,.36),(14,3,float("inf")))
        for total,n,reveal in invalid:
            with self.subTest(total=total,n=n,reveal=reveal),self.assertRaises(
                    OneWayStageRefused):
                stage_hold_seconds(total,n,reveal)
        with self.assertRaises(OneWayStageRefused):
            active_focus_sequence("ROTATE_FOREVER")
        with self.assertRaises(OneWayStageRefused):
            grammar_for_original_scene("ROTATE_FOREVER")


@unittest.skipUnless(importlib.util.find_spec("PIL"),
                     "Hosted cloud runner installs Pillow to exercise physical render")
class ActuallyDifferentPixelSceneStages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from autopilot.test_nonfactual_narration_rehearsal_b4d9 import pipeline
        from autopilot.nonfactual_narration_rehearsal import build_nonfactual_rehearsals
        from autopilot.full_original_rehearsal_media_b4e1 import (
            prepare_full_rehearsal_plan,
        )
        sources=pipeline()
        rehearsals=build_nonfactual_rehearsals(*sources)
        cls.plan=prepare_full_rehearsal_plan(*sources,rehearsals)

    def test_all_17_original_instructional_scenes_highlight_unique_choices(self):
        from PIL import ImageChops
        from autopilot.cinematic_scene_board_b4f9 import (
            BEATS,render_editorial_frame,SceneDesignRefused,
        )
        self.assertEqual({key:beat[3] for key,beat in BEATS.items()},
                         SOURCE_SCENE_GRAMMAR)
        measured=0
        for ep in self.plan["episodes"]:
            scene_count=4 if ep["kind"]=="short" else 9
            self.assertEqual(len(ep["scenes"]),scene_count)
            rect=(75,690,1005,1395) if ep["kind"]=="short" else (
                932,184,1840,705)
            cardcenter=(540,1680) if ep["kind"]=="short" else (960,883)
            for scene in ep["scenes"]:
                grammar=BEATS[scene["scene_id"]][3]
                focus_steps=active_focus_sequence(grammar)
                frames=[]
                fingerprints=[]
                for focus in focus_steps:
                    picture=render_editorial_frame(
                        ep,scene,revealed=focus is not None,
                        focus_index=focus)
                    frames.append(picture)
                    fingerprints.append(sha256(picture.tobytes()).hexdigest())
                self.assertEqual(len(set(fingerprints)),len(frames))
                for first,second in zip(frames,frames[1:]):
                    changed=ImageChops.difference(first,second).getbbox()
                    self.assertIsNotNone(changed)
                    self.assertGreaterEqual(changed[0],rect[0])
                    self.assertGreaterEqual(changed[1],rect[1])
                    self.assertLessEqual(changed[2],rect[2])
                    self.assertLessEqual(changed[3],rect[3])
                    self.assertEqual(first.getpixel(cardcenter),
                                     second.getpixel(cardcenter))
                measured+=1
            self.assertEqual(scene_count,len(ep["scenes"]))
        self.assertEqual(measured,17)

    def test_cannot_reveal_invalid_or_duplicate_focus(self):
        from autopilot.cinematic_scene_board_b4f9 import (
            SceneDesignRefused, render_editorial_frame,
        )
        ep=self.plan["episodes"][0]
        scene=ep["scenes"][0]
        for focus,revealed in ((-1,True),(2,True),(True,True),
                               (1,False),(0,False),(0,"yes")):
            with self.subTest(focus=focus,revealed=revealed),self.assertRaises(
                    SceneDesignRefused):
                render_editorial_frame(ep,scene,revealed=revealed,
                                       focus_index=focus)


if __name__=="__main__":
    unittest.main()
