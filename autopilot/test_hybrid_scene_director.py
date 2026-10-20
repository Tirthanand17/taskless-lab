"""Four-prompt FlowMinute hybrid visual director regression checks.

Frames are original; no reference Instagram/reel assets are harvested.
Testing scene variants does not imply natural narration, real app demos,
photorealism, ownership of third-party voices or YouTube release consent.
"""
from hashlib import sha256
from pathlib import Path
import unittest

from PIL import Image

from autopilot.agent_org import WorkflowError
from autopilot.hybrid_scene_director import (
    RECIPES,FAMILIES,render_scene_world,scene_recipe_plan,WIDTH,HEIGHT,
)
from autopilot.oct20_full_mesh_story_timeline import (
    SCENE_STORIES,_authored_cuts,draw_oct20_full_mesh_frame,
)


class HybridDirectorSourceIntegrationTests(unittest.TestCase):
    def test_seven_original_subjects_three_families_and_camera_variety(self):
        for episode in ("fm_20261020_short_en","fm_20261020_short_hi"):
            with self.subTest(episode=episode):
                plan=scene_recipe_plan(episode)
                self.assertEqual(plan["scene_count"],7)
                self.assertEqual(plan["unique_subjects"],7)
                self.assertEqual(plan["unique_compositions"],7)
                self.assertGreaterEqual(plan["different_camera_lenses"],5)
                self.assertEqual(plan["digital_scenes"],3)
                self.assertEqual(plan["mesh_or_hybrid_scenes"],4)
                self.assertFalse(plan["repeat_one_subject_all_scenes"])
                self.assertFalse(plan["genuine_cinematic_photorealism_verified"])
                self.assertFalse(plan["youtube_upload_authorized"])
                self.assertFalse(plan["youtube_publish_authorized"])
                self.assertEqual(plan["monthly_recurring_infrastructure_inr"],0)
                self.assertEqual(set(x["visual_family"]
                                     for x in plan["shot_recipes"]),FAMILIES)
                self.assertTrue(all(not x["actual_real_app_screenshot"]
                                    for x in plan["shot_recipes"]))
        self.assertEqual(len(set(r.lens for r in RECIPES)),7)
        self.assertEqual(len(set(r.motion for r in RECIPES)),7)

    def test_each_beat_has_separate_explanation_not_generic_boxes(self):
        meanings={0:"neon_agent_network",
                  1:"grocery_bag_and_food",
                  2:"shopping_draft_phone",
                  3:"decision_flow_arrows",
                  4:"large_checkout_padlock",
                  5:"feature_plan_region_grid",
                  6:"human_review_phone"}
        self.assertEqual({r.beat:r.graphic_subject for r in RECIPES},meanings)
        self.assertEqual(len(SCENE_STORIES["fm_20261020_short_en"]),7)
        self.assertEqual(len(SCENE_STORIES["fm_20261020_short_hi"]),7)

    def test_seven_real_drawn_original_scenes_generate_distinct_pixels(self):
        en="fm_20261020_short_en"
        hi="fm_20261020_short_hi"
        digests=[]
        for ep in (en,hi):
            unique=[]
            for cut in _authored_cuts(ep):
                result=draw_oct20_full_mesh_frame(ep,cut.start_frame)
                self.assertEqual(result.size,(WIDTH,HEIGHT))
                self.assertEqual(result.mode,"RGB")
                unique.append(sha256(result.tobytes()).hexdigest())
            with self.subTest(ep=ep):
                self.assertEqual(len(set(unique)),7)
            digests.extend(unique)
        self.assertEqual(len(set(digests)),14)

    def test_every_visual_family_has_genuine_in_scene_motion(self):
        for ep in ("fm_20261020_short_en","fm_20261020_short_hi"):
            for cut in _authored_cuts(ep):
                with self.subTest(ep=ep,beat=cut.scene_index):
                    frame1=draw_oct20_full_mesh_frame(ep,cut.start_frame+1)
                    frame2=draw_oct20_full_mesh_frame(ep,cut.start_frame+5)
                    self.assertNotEqual(sha256(frame1.tobytes()).hexdigest(),
                                        sha256(frame2.tobytes()).hexdigest())

    def test_draft_policy_refuses_forged_shapes_and_invalid_beat_numbers(self):
        for episode,scenes in (
            ("fm_20261020_short_en",8),
            ("fm_20261020_short_hi",True),
            ("fm_20261020_short_en",7.0),
            ("evil",7),("",7),(None,7),
        ):
            with self.subTest(episode=str(episode),scenes=scenes):
                with self.assertRaises(WorkflowError):
                    scene_recipe_plan(episode,scene_count=scenes)
        canvas=Image.new("RGBA",(WIDTH,HEIGHT))
        for beat in (-1,7,True,1.5):
            with self.subTest(beat=beat),self.assertRaises(WorkflowError):
                render_scene_world(canvas,"fm_20261020_short_en",beat,4)
        with self.assertRaises(WorkflowError):
            render_scene_world(Image.new("RGB",(WIDTH,HEIGHT)),
                               "fm_20261020_short_en",0,0)

    def test_variant_is_deterministic_and_different_by_episode(self):
        a=scene_recipe_plan("fm_20261020_short_en")
        self.assertEqual(a,scene_recipe_plan("fm_20261020_short_en"))
        self.assertNotEqual(
            a["shot_recipes"][0]["bounded_visual_variant"],
            scene_recipe_plan("fm_20261020_short_hi")
            ["shot_recipes"][0]["bounded_visual_variant"],
        )


if __name__=="__main__":
    unittest.main()
