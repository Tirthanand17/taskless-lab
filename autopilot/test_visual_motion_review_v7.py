"""B4e5 source-only motion and contact-sheet regression tests.

Fast tests are synthetic; the 96-frame physical art test runs explicitly in
the separate GitHub public-art QA workflow, NEVER invoking external accounts.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

from autopilot.visual_motion_review_v7 import (
    COUNTS, SLOTS, STATUS, TICKS, SCENE_DAY,
    MotionReviewRefused, _checked_story, _hero_sha, _contact_sheet,
    changed_motion_fraction, review_all_32_original_scenes,
)

PIL_AVAILABLE = importlib.util.find_spec("PIL") is not None
CAIRO_AVAILABLE = importlib.util.find_spec("cairosvg") is not None
PHYSICAL = os.environ.get("FLOWMINUTE_B4E5_PHYSICAL_REVIEW") == "1"


class SourceReviewBoundaryTests(unittest.TestCase):
    def test_three_original_source_drafts_not_fresh_or_approved(self):
        self.assertEqual(tuple(COUNTS), SLOTS)
        self.assertEqual(sum(COUNTS.values()), 32)
        self.assertEqual(TICKS, (0,60,120))
        self.assertEqual(SCENE_DAY, "2026-11-12")
        for slot in SLOTS:
            story = _checked_story(slot)
            self.assertEqual(story["scene_count"], COUNTS[slot])
            self.assertFalse(story["human_full_watch_listen_completed"])
            self.assertFalse(story["release_authorized"])
            self.assertFalse(story["youtube_upload_enabled"])

    def test_unknown_scene_not_promoted_to_original_source(self):
        for slot in ("", "short_night", "long_am", "2026-11-12"):
            with self.subTest(slot=slot), self.assertRaises(MotionReviewRefused):
                _checked_story(slot)

    def test_existing_destination_refused_without_modification(self):
        with tempfile.TemporaryDirectory() as p:
            root = Path(p)
            existing = root/"existing"
            existing.mkdir()
            (existing/"sentinel.txt").write_text("unchanged")
            with self.assertRaises(MotionReviewRefused):
                review_all_32_original_scenes(existing)
            self.assertEqual((existing/"sentinel.txt").read_text(), "unchanged")

    def test_relative_output_path_does_not_start_rendering(self):
        with self.assertRaises(MotionReviewRefused):
            review_all_32_original_scenes(Path("relative/unapproved"))

    def test_no_unnecessary_cloud_or_youtube_module_import(self):
        import ast
        s=Path("autopilot/visual_motion_review_v7.py").read_text()
        tree=ast.parse(s)
        forbidden=("boto3","botocore","google","requests","urllib",
                   "socket","aiohttp","httpx","http.client","youtube")
        for node in ast.walk(tree):
            modules=([a.name for a in node.names] if isinstance(node,ast.Import)
                     else [node.module or ""] if isinstance(node,ast.ImportFrom) else [])
            for name in modules:
                self.assertFalse(name.startswith(forbidden),name)


@unittest.skipUnless(PIL_AVAILABLE, "Pillow only on visual QA runner")
class PixelChangeMetricTests(unittest.TestCase):
    def test_real_pixel_changed_fraction_not_fabricated(self):
        from PIL import Image, ImageDraw
        a=Image.new("RGB",(320,224),(7,16,28))
        b=a.copy()
        ImageDraw.Draw(b).rectangle((35,30,130,100),fill=(240,204,31))
        f=changed_motion_fraction(a,b,(0,0,320,224))
        self.assertGreater(f,.04)
        self.assertLess(f,.45)
        self.assertEqual(changed_motion_fraction(a,a,(0,0,320,224)),0)
        self.assertNotEqual(_hero_sha(a,(0,0,320,224)),_hero_sha(b,(0,0,320,224)))

    def test_bad_geometry_and_source_crop_fail_closed(self):
        from PIL import Image
        a=Image.new("RGB",(320,224))
        b=Image.new("RGB",(320,225))
        with self.assertRaises(MotionReviewRefused):
            changed_motion_fraction(a,b,(0,0,320,224))
        for bad in ((-1,0,10,10),(0,0,321,224),(20,30,20,60),
                    (0,0,320,225)):
            with self.subTest(rect=bad),self.assertRaises(MotionReviewRefused):
                changed_motion_fraction(a,a,bad)

    def test_contact_sheet_makes_a_real_review_image(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as p:
            story=_checked_story("short_am")
            size=(1080,1920)
            samples=[Image.new("RGB",size,(i*27+40,60,95)) for i in range(6)]
            path=Path(p)/"contact.png"
            result=_contact_sheet(story,samples,path)
            self.assertTrue(path.is_file())
            self.assertEqual(result["scene_count"],6)
            self.assertFalse(result["human_visual_approval"])
            self.assertEqual(len(result["sha256"]),64)


@unittest.skipUnless(PIL_AVAILABLE and CAIRO_AVAILABLE and PHYSICAL,
                     "Run full 96-frame proof ONLY in dedicated hosted visual CI")
class PhysicallyGeneratedAll32OriginalScenes(unittest.TestCase):
    def test_every_original_scene_has_three_real_frames_and_3_contact_sheets(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as p:
            output=Path(p)/"original-32-scene-review"
            report=review_all_32_original_scenes(output)
            self.assertEqual(report["status"],STATUS)
            self.assertEqual(report["shots_checked"],32)
            self.assertEqual(report["source_motion_frames_physically_rendered"],96)
            self.assertEqual(report["episode_order"],list(SLOTS))
            self.assertEqual(len(report["episodes"]),3)
            self.assertEqual(sum(
                len(x["scenes"]) for x in report["episodes"]),32)
            self.assertFalse(report["automated_spinner_free_certification"])
            self.assertFalse(report["human_creative_approval"])
            self.assertFalse(report["human_claim_rights_and_listen_review"])
            self.assertFalse(report["daily_fresh_content_produced"])
            self.assertFalse(report["release_authorized"])
            self.assertEqual(report["real_youtube_uploads"],0)
            self.assertTrue((output/"UNAPPROVED_32_SCENE_MOTION_REPORT.json").is_file())
            contacts=[]
            for entry in report["episodes"]:
                with self.subTest(slot=entry["slot"]):
                    self.assertEqual(len(entry["scenes"]),COUNTS[entry["slot"]])
                    self.assertFalse(entry["actual_encoded_mp4_playback_reviewed"])
                    self.assertFalse(entry["human_final_review_complete"])
                    x=entry["contact_sheet"]
                    path=output/x["filename"]
                    self.assertTrue(path.is_file())
                    self.assertGreater(path.stat().st_size,20_000)
                    with Image.open(path) as image:
                        image.verify()
                    contacts.append(x["sha256"])
                    for scene in entry["scenes"]:
                        self.assertEqual(scene["distinct_full_native_hero_frames"],3)
                        self.assertEqual(scene["3_samples"],[0,60,120])
                        self.assertGreater(scene["changed_hero_pixel_fraction_first_half"],0)
                        self.assertGreater(scene["changed_hero_pixel_fraction_second_half"],0)
                        self.assertFalse(scene["visual_spinner_absence_human_confirmed"])
                        self.assertFalse(scene["release_authorized"])
            self.assertEqual(len(set(contacts)),3)
            self.assertEqual(len(list(output.glob("*.png"))),3)
            saved=json.loads((output/"UNAPPROVED_32_SCENE_MOTION_REPORT.json").read_text())
            self.assertEqual(saved,report)
            with self.assertRaises(MotionReviewRefused):
                review_all_32_original_scenes(output)


if __name__ == "__main__":
    unittest.main()
