"""Regression checks for real procedural visual-only CSV video rendering."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from autopilot.phase3_csv_visual_preview import (
    english_script_rows, visual_frame, render_visual_preview,
    _estimated_caption_at, _english_srt_timing,
)


class ProceduralCsvVideoTests(unittest.TestCase):
    def test_uses_four_authored_english_narration_beats(self):
        lines=english_script_rows()
        self.assertEqual(len(lines),4)
        self.assertIn("Your CSV",lines[0])
        self.assertIn("DictReader",lines[2])
        self.assertIn("fifty eight",lines[3])

    def test_caption_advances_within_same_long_scene(self):
        self.assertNotEqual(_estimated_caption_at(0.5),_estimated_caption_at(7))
        self.assertEqual(_english_srt_timing()[0][0],0)
        self.assertEqual(_english_srt_timing()[-1][1],42000)
        self.assertTrue(all((end-start)<=6000 for start,end,_ in _english_srt_timing()))

    def test_first_and_other_scene_are_real_distinct_pixels(self):
        a=visual_frame(2,width=360)
        b=visual_frame(23,width=360)
        self.assertEqual(a.size,(360,640))
        self.assertEqual(a.mode,"RGB")
        self.assertNotEqual(a.tobytes(),b.tobytes())

    def test_animation_changes_frames_within_same_scene(self):
        a=visual_frame(1,width=360)
        b=visual_frame(1.8,width=360)
        self.assertNotEqual(a.tobytes(),b.tobytes())

    def test_frame_repeatability_for_exact_time(self):
        self.assertEqual(visual_frame(1,width=360).tobytes(),
                         visual_frame(1,width=360).tobytes())

    def test_all_four_scenes_can_be_drawn(self):
        for moment in (1,11,21,32):
            with self.subTest(moment=moment):
                frame=visual_frame(moment,width=360)
                self.assertEqual(frame.size,(360,640))

    def test_out_of_bounds_or_wrong_aspect_denied(self):
        for width in (0,128,400,1920):
            with self.subTest(width=width),self.assertRaises(ValueError):
                visual_frame(1,width=width)
        with self.assertRaises(ValueError):
            visual_frame(42,width=360)
        with self.assertRaises(ValueError):
            visual_frame(-1,width=360)

    def test_caption_injection_requires_four_short_beats(self):
        with self.assertRaises(ValueError):
            visual_frame(1,width=360,spoken=("only one",))

    def test_render_requires_mp4_output_and_bounded_duration(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                render_visual_preview(Path(tmp)/"bad.txt")
            with self.assertRaises(ValueError):
                render_visual_preview(Path(tmp)/"too_long.mp4",duration_s=43)
            with self.assertRaises(ValueError):
                render_visual_preview(Path(tmp)/"too_fast.mp4",fps=120)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg is missing")
    def test_actual_mp4_renders_decodes_and_contains_no_audio(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"visual_only.mp4"
            result=render_visual_preview(target,duration_s=0.5,fps=8,width=360)
            self.assertEqual(result["status"],"REAL_MP4_VISUALS_ONLY_NOT_PUBLISHABLE")
            self.assertTrue(target.is_file())
            self.assertFalse(result["narration_recorded"])
            self.assertFalse(result["media_audio_present"])
            self.assertFalse(result["audio_rights_verified"])
            self.assertFalse(result["youtube_upload_authorized"])
            self.assertFalse(result["publishing_authorized"])
            v=subprocess.run(
                ["ffprobe","-v","error","-show_entries",
                 "stream=codec_type,codec_name,width,height:format=duration",
                 "-of","json",str(target)],
                capture_output=True,text=True,check=True,timeout=20)
            import json
            record=json.loads(v.stdout)
            self.assertAlmostEqual(float(record["format"]["duration"]),0.5,delta=0.15)
            self.assertEqual(len(record["streams"]),1)
            self.assertEqual(record["streams"][0]["codec_type"],"video")
            self.assertEqual(record["streams"][0]["codec_name"],"h264")
            self.assertEqual(record["streams"][0]["width"],360)
            self.assertEqual(record["streams"][0]["height"],640)
            subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(target),
                            "-f","null","-"],check=True,timeout=30)


if __name__=="__main__":
    unittest.main()
