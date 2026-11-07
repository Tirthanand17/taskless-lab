"""B4g0 cloud-only synthetic contact-sheet generation smoke and honesty tests."""
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import json
import unittest
from unittest.mock import patch


@unittest.skipUnless(importlib.util.find_spec("PIL"),
                     "Pillow-only original visual QA worker")
class EditorialContactTests(unittest.TestCase):
    def test_all_seventeen_source_locked_original_frames_are_exported(self):
        from PIL import Image
        from autopilot.quick_storyboard_contact_sheet_b4g0 import (
            STATUS,generate_original_contact_sheets,
        )
        with TemporaryDirectory() as folder:
            root=Path(folder)
            report=generate_original_contact_sheets(root)
            self.assertEqual(report["status"],STATUS)
            self.assertEqual(report["original_synthetic_scenes"],17)
            self.assertEqual(report["human_approved_videos"],0)
            self.assertFalse(report["publication_authorized"])
            self.assertFalse(report["actual_queued_video_render_verified_here"])
            self.assertEqual(report["live_youtube_uploads_or_modifications"],0)
            self.assertEqual([x["source_derived_scene_count"]
                              for x in report["storyboards"]],[4,9,4])
            self.assertEqual({p.name for p in root.iterdir()},
                {"REVIEW_ONLY_SHORT_AM_EDITORIAL_CONTACT.png",
                 "REVIEW_ONLY_LONG_EDITORIAL_CONTACT.png",
                 "REVIEW_ONLY_SHORT_PM_EDITORIAL_CONTACT.png",
                 "CONTACT_SHEET_VISUAL_REVIEW_ONLY.json"})
            for entry in report["storyboards"]:
                name=entry["contact_file"]
                self.assertFalse(entry["actual_original_full_mp4_generated"])
                self.assertFalse(entry["human_full_watch_completed"])
                self.assertFalse(entry["licensed_or_factual_for_publication"])
                with Image.open(root/name) as image:
                    image.load()
                    self.assertEqual(image.mode,"RGB")
                    width,height=image.size
                    if entry["slot"]=="long":
                        self.assertEqual((width,height),(1920,1230))
                    else:
                        self.assertEqual((width,height),(1080,2020))
            with self.assertRaises(Exception):
                generate_original_contact_sheets(root)

    def test_wrong_manual_workflow_context_does_not_export(self):
        from autopilot.quick_storyboard_contact_sheet_b4g0 import (
            PreviewRefused,main,
        )
        import sys
        with TemporaryDirectory() as folder, patch(
                "sys.argv",["visual-qa","--output",str(Path(folder)/"bad")]):
            with self.assertRaises(PreviewRefused),patch.dict(
                    "os.environ",
                    {"GITHUB_EVENT_NAME":"pull_request",
                     "FLOWMINUTE_VISUAL_QA_ONLY":"false"}):
                main()
        workflow=(Path(__file__).resolve().parents[1]/
            ".github/workflows/flowminute-editorial-storyboard-review-b4g0.yml").read_text()
        self.assertIn("  workflow_dispatch:",workflow)
        for token in ("  schedule:","  pull_request:","  push:",
                      "contents: write","secrets.","videos().insert("):
            self.assertNotIn(token,workflow)
        self.assertIn("  contents: read",workflow)
        self.assertIn("retention-days: 1",workflow)
        self.assertIn("persist-credentials: false",workflow)


if __name__=="__main__":
    unittest.main()
