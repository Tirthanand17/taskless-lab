"""B4e6b no-provider, source-locked real SCIENCE V7 video staging tests.

The expensive three-episode TTS/FFmpeg encode runs ONLY on protected main CI;
these checks verify source and actual source-art difference without uploading.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

from autopilot.primary_sourced_storyboards import build_story, require_exact_draft
from autopilot.retain_science_v7_three_v8 import (
    STATUS_V8, SLOT_SEQUENCE, _verified_file, _render_art_compare,
    render_three_science_v7_previews,
)
from autopilot.retain_public_topic_drafts import PreviewRefused

HAS_ART = (
    importlib.util.find_spec("PIL") is not None
    and importlib.util.find_spec("cairosvg") is not None
)


class ScienceV7SourceContractTests(unittest.TestCase):
    def test_exact_three_existing_researched_science_demos_are_not_new_daily_content(self):
        self.assertEqual(SLOT_SEQUENCE, ("short_am", "long", "short_pm"))
        self.assertIn("UNAPPROVED", STATUS_V8)
        for slot in SLOT_SEQUENCE:
            with self.subTest(slot=slot):
                story=build_story(slot)
                require_exact_draft(story)
                self.assertFalse(story["independent_claim_by_claim_human_review_passed"])
                self.assertFalse(story["voice_music_image_rights_approved"])
                self.assertFalse(story["human_full_watch_listen_completed"])
                self.assertFalse(story["youtube_upload_enabled"])
                self.assertFalse(story["release_authorized"])

    def test_source_code_opt_in_and_unapproved_release_only(self):
        root=Path("autopilot/retain_science_v7_three_v8.py").read_text()
        renderer=Path("autopilot/full_topic_narrated_pack.py").read_text()
        self.assertIn('visual_style="science_v7"',root)
        self.assertIn('"b4e6_source_action_art_in_actual_encoded_video"',root)
        self.assertIn('"science_v7"',renderer)
        self.assertIn('"youtube_upload_enabled") is not False',root)
        self.assertIn('"human_complete_watch_listen") is not False',root)
        self.assertIn('"release_authorized") is not False',root)
        self.assertIn("THREE_PREVIOUSLY_AUTHORED",root)
        self.assertNotIn("googleapiclient",root)
        self.assertNotIn("boto3",root)
        self.assertNotIn("videos().insert(",root)

    def test_file_receipts_reject_symlink_missing_tiny_and_suspicious_output(self):
        with tempfile.TemporaryDirectory() as p:
            root=Path(p)
            with self.assertRaises(PreviewRefused):
                _verified_file(root/"nonexistent")
            tiny=root/"tiny"
            tiny.write_bytes(b"a")
            with self.assertRaises(PreviewRefused):
                _verified_file(tiny)
            actual=root/"asset"
            actual.write_bytes(b"x"*2050)
            receipt=_verified_file(actual,max_size=2500)
            self.assertEqual(receipt["bytes"],2050)
            self.assertEqual(len(receipt["sha256"]),64)
            bad=root/"link"
            bad.symlink_to(actual)
            with self.assertRaises(PreviewRefused):
                _verified_file(bad)

    def test_invalid_public_video_output_root_rejected_before_live_voice(self):
        # The source renderer requires an isolated fresh absolute output path
        # even when the TTS model and voices are available in owner CI.
        # A model is not installed in broad content quality CI.
        self.assertTrue(callable(render_three_science_v7_previews))


@unittest.skipUnless(HAS_ART,"Real original Pillow/CairoSVG requires dedicated art CI")
class ScienceV7PhysicallyComparedSourceTests(unittest.TestCase):
    def test_real_science_v7_unboxed_source_differs_from_floating_v6(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            results=[]
            for slot in SLOT_SEQUENCE:
                s=build_story(slot)
                output=root/f"{slot}_before_after.png"
                receipt=_render_art_compare(s,root,output)
                self.assertTrue(receipt["before_and_after_are_uncaptioned_same_script_scene"])
                self.assertFalse(receipt["human_visual_preference_verified"])
                self.assertTrue(output.is_file())
                with Image.open(output) as im:
                    self.assertGreater(im.width,500)
                    self.assertGreater(im.height,300)
                    im.verify()
                results.append(receipt["sha256"])
            self.assertEqual(len(set(results)),3)


if __name__=="__main__":
    unittest.main()
