"""B4e6 source-lock and native pixel regression tests for story-action visuals."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import os
import tempfile
import unittest

from autopilot.primary_sourced_storyboards import build_story, render_original_svg
from autopilot.action_specific_floating_v7 import (
    MOTIFS, SPECIALIZED, STATUS, paint_action_specific_source_scene,
)
from autopilot.retain_action_specific_three_v8 import (
    EXAMPLES, build_action_specific_visual_review,
)
from autopilot.cinematic_scene_v3 import SCENE_PANEL, CinematicSceneRejected
from autopilot.visual_motion_review_v7 import MotionReviewRefused

REAL=(os.getenv("FLOWMINUTE_B4E6_NATIVE_ART")=="1"
      and importlib.util.find_spec("PIL") is not None
      and importlib.util.find_spec("cairosvg") is not None)


class StoryActionScopeTests(unittest.TestCase):
    def test_19_science_visual_actions_from_exact_source_drafts(self):
        counts={}
        for slot in ("short_am","long","short_pm"):
            s=build_story(slot)
            count=sum(x["visual_action"] in MOTIFS[s["theme"]] for x in s["scenes"])
            counts[slot]=count
            self.assertFalse(s["release_authorized"])
            self.assertFalse(s["human_full_watch_listen_completed"])
        self.assertEqual(counts,{"short_am":4,"long":11,"short_pm":4})
        self.assertEqual(len(SPECIALIZED),19)
        self.assertEqual(len(EXAMPLES),8)
        self.assertTrue(SPECIALIZED.issuperset({
            "signal_sweep","damage_caveat","formula_pipeline","two_timers"}))

    def test_reviewer_never_approves_frozen_source(self):
        from autopilot.full_topic_narrated_pack import TopicRenderError
        with self.assertRaises(TopicRenderError):
            from autopilot.full_topic_narrated_pack import render_full_topic_video
            render_full_topic_video(build_story("short_am"),None,Path("fake"),
                                    visual_style="NO_OWNER_APPROVAL")

    def test_outputs_reject_existing_or_relative_folder(self):
        with self.assertRaises(MotionReviewRefused):
            build_action_specific_visual_review(Path("relative"))
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            child=root/"already"
            child.mkdir()
            (child/"sentinel").write_text("fixed")
            with self.assertRaises(MotionReviewRefused):
                build_action_specific_visual_review(child)
            self.assertEqual((child/"sentinel").read_text(),"fixed")


@unittest.skipUnless(REAL,"Run physical action source visuals ONLY on unprivileged GitHub runner")
class FullNativeActionSpecificArtReview(unittest.TestCase):
    def test_all_32_art_frames_and_19_different_original_scenes(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/"source-art"
            result=build_action_specific_visual_review(root)
            self.assertEqual(result["scene_hero_motifs_physically_changed"],19)
            self.assertEqual(result["untouched_original_hero_motifs"],13)
            self.assertEqual(result["total_physical_original_beats"],32)
            self.assertEqual(result["contact_sheets"],3)
            self.assertEqual(len(result["before_after_original_source_art_pairs"]),8)
            self.assertFalse(result["release_authorized"])
            self.assertFalse(result["generic_spinner_freedom_human_confirmed"])
            self.assertFalse(result["source_topics_are_new_daily_content"])
            self.assertFalse(result["youtube_upload_or_schedule"])
            self.assertFalse(result["three_full_encoded_mp4_created_by_this_job"])
            self.assertEqual(len(list(root.glob("*.png"))),11)
            for e in result["episodes"]:
                with self.subTest(slot=e["slot"]):
                    self.assertEqual(e["scene_count"],len(e["scenes"]))
                    self.assertFalse(e["release_authorized"])
                    self.assertTrue((root/e["contact_sheet"]["filename"]).is_file())
                    for s in e["scenes"]:
                        self.assertFalse(s["human_visual_approval"])
                        self.assertTrue(s["all_outside_hero_source_pixels_unchanged"])
            with self.assertRaises(MotionReviewRefused):
                build_action_specific_visual_review(root)

    def test_encoded_renderer_uses_exact_v7_style_while_old_stays_unmodified(self):
        from autopilot.full_topic_narrated_pack import _topic_png
        from PIL import Image, ImageChops
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for slot,idx in (("short_am",2),("short_pm",4),("long",18)):
                with self.subTest(slot=slot,scene=idx):
                    s=build_story(slot)
                    before=root/"v6.png";after=root/"v7.png"
                    hash_before=_topic_png(s,idx,60,before,visual_style="floating_v6")
                    hash_after=_topic_png(s,idx,60,after,visual_style="science_v7")
                    self.assertNotEqual(hash_before,hash_after)
                    with Image.open(before) as b,Image.open(after) as a:
                        b=b.convert("RGB");a=a.convert("RGB")
                        h=SCENE_PANEL[s["format"]]
                        self.assertIsNotNone(ImageChops.difference(
                            b.crop(h),a.crop(h)).getbbox())
                        for outside in ((0,0,b.width,h[1]),
                                        (0,h[3],b.width,b.height)):
                            self.assertIsNone(ImageChops.difference(
                                b.crop(outside),a.crop(outside)).getbbox())


if __name__ == "__main__":
    unittest.main()
