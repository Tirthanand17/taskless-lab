"""Native full-HD 432s original silent Hindi long engineering regression.

Normal unit tests never render 432 seconds or publish anything. Real full-HD
long media is tested in a separate bounded public Actions job.
"""
from pathlib import Path
import shutil
import tempfile
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.phase3_full_hd_long_assembly import (
    EPISODE,DURATION_SECONDS,FPS,WIDTH,HEIGHT,SEGMENT_FRAMES,
    TOTAL_FRAMES,MAX_RENDER_WALL_SECONDS,plan_native_hd_long,
    _probe_exact_video,render_native_hd_long,
)
from autopilot.phase3_hindi_visual_preview import render_hindi_visual_preview


class FullHDHindiLongTests(unittest.TestCase):
    def test_exact_gapless_native_hd_scene_plan(self):
        plan=plan_native_hd_long()
        self.assertEqual(len(plan),432)
        self.assertEqual(plan,tuple(range(432)))
        self.assertEqual(plan[0],0)
        self.assertEqual(plan[-1],431)
        self.assertEqual((FPS,WIDTH,HEIGHT),(24,1920,1080))
        self.assertEqual(TOTAL_FRAMES,10368)
        self.assertEqual(TOTAL_FRAMES,len(plan)*SEGMENT_FRAMES)

    def test_full_video_keeps_explicit_absolute_bounds(self):
        self.assertEqual(EPISODE,"csv_tutorial_long_hi")
        self.assertEqual(DURATION_SECONDS,432)
        self.assertLessEqual(MAX_RENDER_WALL_SECONDS,900)

    def test_no_overwrite_any_existing_source_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/"already.mp4"
            output.write_bytes(b"do-not-overwrite")
            with self.assertRaises(WorkflowError):
                render_native_hd_long(output)
            self.assertEqual(output.read_bytes(),b"do-not-overwrite")

    def test_requires_existing_folder_and_mp4_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent=Path(tmp)
            with self.assertRaises(WorkflowError):
                render_native_hd_long(parent/"missing"/"new.mp4")
            self.assertFalse((parent/"missing").exists())
            with self.assertRaises(WorkflowError):
                render_native_hd_long(parent/"wrong.txt")

    def test_symlinks_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent=Path(tmp)
            valid=parent/"folder"
            valid.mkdir()
            alias=parent/"alias"
            alias.symlink_to(valid,target_is_directory=True)
            with self.assertRaises(WorkflowError):
                render_native_hd_long(alias/"video.mp4")
            target=valid/"other.mp4"
            target.write_bytes(b"owner")
            sym=valid/"link.mp4"
            sym.symlink_to(target)
            with self.assertRaises(WorkflowError):
                render_native_hd_long(sym)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg/FFprobe needed for real scene test")
    def test_actual_native_hd_late_scene_encodes_correct_24_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"later_scene.mp4"
            result=render_hindi_visual_preview(
                EPISODE,path,duration_s=1,fps=24,width=1920,start_s=254)
            self.assertFalse(result["audio_track_present"])
            self.assertFalse(result["publishing_authorized"])
            _probe_exact_video(path,frames=24,max_bytes=3_000_000)
            with self.assertRaises(WorkflowError):
                _probe_exact_video(path,frames=25,max_bytes=3_000_000)

    def test_never_grants_narrator_or_release_authority(self):
        import inspect
        code=inspect.getsource(render_native_hd_long)
        for marker in (
            '"actual_human_voice_present":False',
            '"voice_rights_verified":False',
            '"speech_caption_alignment_verified":False',
            '"premium_cinematic_quality_verified":False',
            '"youtube_upload_authorized":False',
            '"publishing_authorized":False',
        ):
            self.assertIn(marker,code)


if __name__=="__main__":
    unittest.main()
