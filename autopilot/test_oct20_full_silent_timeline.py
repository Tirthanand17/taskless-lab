"""All seven original script scenes bound to H264 silent preview timeline.

Public CI only renders a one-second original scene to bound resources.
It does NOT produce finished videos, ASR, licensed voice or YouTube uploads.
"""
from pathlib import Path
from unittest.mock import patch
import tempfile
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.oct20_full_silent_timeline import (
    FPS,HEIGHT,WIDTH,_ALLOWED,
    full_silent_scene_plan,render_silent_scene_timeline,
)


class Oct20FullSilentStoryboardTimelineTests(unittest.TestCase):
    def test_exact_english_hindi_seven_scene_script_boundaries(self):
        expected={
            "fm_20261020_short_en":[0,4,10,16,22,29,36,42],
            "fm_20261020_short_hi":[0,5,11,17,24,31,38,44],
        }
        for episode,edges in expected.items():
            with self.subTest(episode=episode):
                scenes=full_silent_scene_plan(episode)
                self.assertEqual(len(scenes),7)
                self.assertEqual(
                    [s.start_second for s in scenes]+[scenes[-1].end_second],
                    edges)
                self.assertEqual(scenes[-1].end_frame,edges[-1]*FPS)
                self.assertEqual(
                    sum(s.end_frame-s.start_frame for s in scenes),
                    edges[-1]*FPS)
                self.assertEqual(
                    [s.scene_index for s in scenes],list(range(7)))

    def test_full_video_output_specs_are_still_low_res_and_voice_free(self):
        self.assertEqual((WIDTH,HEIGHT,FPS),(432,768,24))
        self.assertEqual(set(_ALLOWED),{
            "fm_20261020_short_en","fm_20261020_short_hi"})

    def test_no_wrong_episode_long_or_undefined_workflow(self):
        for bad in ("",None,"not-real","fm_20261020_long_hi",True,123):
            with self.subTest(bad=str(bad)),self.assertRaises(WorkflowError):
                full_silent_scene_plan(bad)

    def test_existing_file_preserved_and_non_mp4_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/"do_not_replace.mp4"
            output.write_bytes(b"PRIVATE_OWNER_MEDIA_KEEP")
            with self.assertRaises(WorkflowError):
                render_silent_scene_timeline(
                    episode_id="fm_20261020_short_en",output_path=output)
            self.assertEqual(output.read_bytes(),b"PRIVATE_OWNER_MEDIA_KEEP")
            with self.assertRaises(WorkflowError):
                render_silent_scene_timeline(
                    episode_id="fm_20261020_short_en",
                    output_path=Path(folder)/"bad.avi")

    def test_bad_fake_smoke_time_must_not_render(self):
        with tempfile.TemporaryDirectory() as folder:
            for val in (0,2,42,True,"1",-1,1.0):
                with self.subTest(value=val),self.assertRaises(WorkflowError):
                    render_silent_scene_timeline(
                        episode_id="fm_20261020_short_hi",
                        output_path=Path(folder)/"test.mp4",
                        test_only_first_scene_seconds=val)
                self.assertFalse((Path(folder)/"test.mp4").exists())

    def test_no_provider_or_youtube_code_in_local_composition(self):
        import inspect
        from autopilot import oct20_full_silent_timeline as module
        src=inspect.getsource(module)
        self.assertNotIn("videos.insert",src)
        self.assertNotIn("youtube.googleapis.com",src)
        self.assertNotIn("requests.post",src)
        self.assertNotIn("cloudflare.com",src)
        self.assertIn('"youtube_upload_authorized":False',src)
        self.assertIn('"youtube_publish_authorized":False',src)
        self.assertIn('"licensed_narrator_verified":False',src)
        self.assertIn('"speech_to_srt_alignment_verified":False',src)

    def test_actual_ffmpeg_one_second_scene_renders_without_audio(self):
        import shutil
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            self.skipTest("Existing FFmpeg / FFprobe required")
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/"english_scene.mp4"
            report=render_silent_scene_timeline(
                episode_id="fm_20261020_short_en",output_path=output,
                test_only_first_scene_seconds=1)
            self.assertEqual(report["frame_count"],24)
            self.assertEqual(report["rendered_duration_seconds"],1)
            self.assertEqual(report["script_duration_seconds"],42)
            self.assertEqual(report["audio_track_count"],0)
            self.assertEqual(report["script_scene_count"],7)
            self.assertEqual(report["rendered_scene_count"],1)
            self.assertFalse(report["entire_silent_visual_timeline_rendered"])
            self.assertFalse(report["real_cinematic_3d_confirmed"])
            self.assertFalse(report["licensed_narrator_verified"])
            self.assertFalse(report["production_video_ready"])
            self.assertFalse(report["youtube_upload_authorized"])
            self.assertFalse(report["youtube_publish_authorized"])
            self.assertEqual(report["external_network_calls"],0)
            self.assertEqual(report["monthly_recurring_infrastructure_inr"],0)
            self.assertTrue(output.is_file())
            self.assertGreater(output.stat().st_size,2048)


if __name__=="__main__":
    unittest.main()
