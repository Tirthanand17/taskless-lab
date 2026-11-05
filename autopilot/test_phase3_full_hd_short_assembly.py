"""A full-HD 42s Short may be assembled only in ephemeral public CI.

Normal unit tests cover fixed 42-scene plans, safe file preflight and one
real 1s H264 segment. They do NOT produce 42-second assets or release audio.
"""
from pathlib import Path
import shutil
import tempfile
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.phase3_full_hd_short_assembly import (
    ENGLISH,HINDI,DURATION_SECONDS,FPS,WIDTH,HEIGHT,TOTAL_FRAMES,
    ONE_SECOND_FRAME_COUNT,hd_short_plan,render_full_hd_short,
    _check_h264_silent,
)
from autopilot.phase3_csv_visual_preview import render_visual_preview


class FullNativeHDShortTests(unittest.TestCase):
    def test_exact_two_authored_full_length_short_plans(self):
        for episode in (ENGLISH,HINDI):
            with self.subTest(episode=episode):
                plan=hd_short_plan(episode)
                self.assertEqual(len(plan),42)
                self.assertEqual(plan[0].offset_seconds,0)
                self.assertEqual(plan[-1].offset_seconds,41)
                self.assertEqual(sum(p.duration_seconds for p in plan),42)
                self.assertEqual(sum(p.frame_count for p in plan),1008)
                self.assertTrue(all(p.frame_count==24 for p in plan))
                self.assertEqual([p.number for p in plan],list(range(1,43)))
                self.assertEqual([p.offset_seconds for p in plan],list(range(42)))

    def test_unreviewed_long_or_unknown_episode_is_not_a_short(self):
        for bad in ("csv_tutorial_long_hi","other","",None):
            with self.subTest(bad=bad),self.assertRaises(WorkflowError):
                hd_short_plan(bad)

    def test_native_framerate_and_resolution_contract(self):
        self.assertEqual((WIDTH,HEIGHT,FPS),(1080,1920,24))
        self.assertEqual(TOTAL_FRAMES,DURATION_SECONDS*FPS)
        self.assertEqual(ONE_SECOND_FRAME_COUNT,24)

    def test_refuses_overwrite_without_deleting_owner_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"do_not_replace.mp4"
            path.write_bytes(b"existing-owner-content")
            with self.assertRaises(WorkflowError):
                render_full_hd_short(ENGLISH,path)
            self.assertEqual(path.read_bytes(),b"existing-owner-content")

    def test_refuses_non_existing_folder_symlinks_and_invalid_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with self.assertRaises(WorkflowError):
                render_full_hd_short(ENGLISH,root/"missing"/"video.mp4")
            owner=root/"owner.mp4"
            owner.write_bytes(b"test")
            link=root/"link.mp4"
            link.symlink_to(owner)
            with self.assertRaises(WorkflowError):
                render_full_hd_short(HINDI,link)
            with self.assertRaises(WorkflowError):
                render_full_hd_short(HINDI,root/"wrong.txt")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg/FFprobe required")
    def test_one_actual_original_1080p_h264_chunk_is_validated(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"real_24_frame_english.mp4"
            result=render_visual_preview(
                path,duration_s=1,fps=FPS,width=WIDTH,start_s=22)
            self.assertFalse(result["media_audio_present"])
            self.assertFalse(result["publishing_authorized"])
            _check_h264_silent(path,expected_frames=ONE_SECOND_FRAME_COUNT)
            with self.assertRaises(WorkflowError):
                _check_h264_silent(path,expected_frames=TOTAL_FRAMES)

    def test_module_cannot_infer_voice_rights_from_silent_movie(self):
        import inspect
        source=inspect.getsource(render_full_hd_short)
        for required in (
            '"has_spoken_voice":False',
            '"has_any_audio":False',
            '"two_licensed_distinct_narrators_verified":False',
            '"actual_subtitle_speech_alignment_verified":False',
            '"publishing_authorized":False',
        ):
            self.assertIn(required,source)


if __name__=="__main__":
    unittest.main()
