"""Phase 3 7m12s real-scene chunk-plan and media QA tests.

Never synthesizes speech, claims license, uploads media, uses cloud apps or
creates a full 432s video in ordinary unit testing. The existing public render
workflow separately checks the complete real video from the 24 scene chunks.
"""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from autopilot.agent_org import WorkflowError
from autopilot.phase3_long_visual_assembly import (
    DURATION_S, EPISODE, SCENE_COUNT, _validate_video,
    plan_full_long_render, render_complete_long_visual,
)
from autopilot.phase3_hindi_visual_preview import render_hindi_visual_preview


class FullHindiSilentMoviePlanTests(unittest.TestCase):
    def test_twenty_four_script_bounded_segments_cover_all_432_seconds(self):
        parts=plan_full_long_render()
        self.assertEqual(len(parts),24)
        self.assertEqual(len(parts),SCENE_COUNT)
        self.assertEqual(sum(p.duration_s for p in parts),432)
        self.assertEqual(parts[0].offset_s,0)
        self.assertEqual(parts[-1].offset_s+parts[-1].duration_s,DURATION_S)
        self.assertTrue(all(p.duration_s<=24 for p in parts))
        self.assertTrue(all(p.start_frame==p.offset_s*8 for p in parts))
        self.assertTrue(all(p.frame_count==p.duration_s*8 for p in parts))
        self.assertEqual(sum(p.frame_count for p in parts),3456)

    def test_no_gaps_or_overlaps_at_every_scene_boundary(self):
        p=plan_full_long_render()
        for a,b in zip(p,p[1:]):
            self.assertEqual(a.offset_s+a.duration_s,b.offset_s)
            self.assertEqual(a.start_frame+a.frame_count,b.start_frame)

    def test_only_8fps_or_12fps_allowed_in_fixed_mode(self):
        p=plan_full_long_render(fps=12)
        self.assertEqual(sum(x.frame_count for x in p),5184)
        for fps in (0,7,13,24,True,8.0):
            with self.subTest(fps=fps),self.assertRaises(WorkflowError):
                plan_full_long_render(fps=fps)

    def test_fixed_episode_is_original_long_authored_csv(self):
        self.assertEqual(EPISODE,"csv_tutorial_long_hi")
        parts=plan_full_long_render()
        self.assertTrue(all(x.duration_s==18 for x in parts))
        self.assertEqual(parts[12].offset_s,216)

    def test_invalid_expensive_dimensions_rate_refused_before_ffmpeg(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/"not_rendered.mp4"
            for rate,width in ((24,640),(8,1280),(30,960),(8,True)):
                with self.subTest(rate=rate,width=width),self.assertRaises(WorkflowError):
                    render_complete_long_visual(out,fps=rate,width=width)
                self.assertFalse(out.exists())

    def test_no_directory_or_filename_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"already.mp4"
            target.write_bytes(b"preexisting")
            with self.assertRaises(WorkflowError):
                render_complete_long_visual(target)
            self.assertEqual(target.read_bytes(),b"preexisting")
            absent=Path(tmp)/"missing"/"new.mp4"
            with self.assertRaises(WorkflowError):
                render_complete_long_visual(absent)
            self.assertFalse(absent.parent.exists())

    def test_input_parent_or_target_symlink_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            real=root/"ordinary"
            real.mkdir()
            alias=root/"alias"
            alias.symlink_to(real,target_is_directory=True)
            with self.assertRaises(WorkflowError):
                render_complete_long_visual(alias/"output.mp4")
            target=real/"link.mp4"
            target.symlink_to(real/"nonexistent.mp4")
            with self.assertRaises(WorkflowError):
                render_complete_long_visual(target)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg/FFprobe required")
    def test_real_long_scene_clip_is_valid_and_rejects_wrong_frame_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"scene.mp4"
            render_hindi_visual_preview(
                EPISODE,path,duration_s=.5,fps=8,width=640)
            metadata=_validate_video(path,fps=8,width=640,frames=4)
            self.assertEqual(metadata["streams"][0]["codec_name"],"h264")
            with self.assertRaises(WorkflowError):
                _validate_video(path,fps=8,width=640,frames=5)
            with self.assertRaises(WorkflowError):
                _validate_video(path,fps=8,width=960,frames=4)

    def test_authored_script_explicitly_has_no_voice_or_publish_authorization(self):
        # Full-length silent video output is NOT rights/voice approved.
        import inspect
        source=inspect.getsource(render_complete_long_visual)
        self.assertIn('"has_narration_or_music": False',source)
        self.assertIn('"caption_speech_sync_verified": False',source)
        self.assertIn('"publishing_authorized": False',source)


if __name__=="__main__":
    unittest.main()
