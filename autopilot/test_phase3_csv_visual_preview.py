"""Regression checks for real procedural visual-only CSV video rendering."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from autopilot.phase3_csv_visual_preview import (
    english_script_rows, visual_frame, render_visual_preview,
    _estimated_caption_at, _english_srt_timing, _illustrative_csv_data,
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

    def test_displayed_dataset_matches_real_executed_example(self):
        from autopilot.examples.flowminute_csv_demo import (
            COLUMNS, ROWS, demonstrate_csv_total,
        )
        bound = _illustrative_csv_data()
        calc = demonstrate_csv_total()
        self.assertEqual(COLUMNS,("product","units","price"))
        self.assertEqual(
            tuple((r["product"],r["units"],r["price"]) for r in ROWS),
            tuple(row[:3] for row in bound),
        )
        self.assertEqual(tuple(row[3] for row in bound),(20,30,8))
        self.assertEqual(sum(row[3] for row in bound),calc["total"])
        self.assertEqual(calc["total"],58)
        self.assertFalse(calc["purchased_anything"])
        self.assertFalse(calc["publishing_authorized"])

    def test_four_separate_source_relevant_visual_scenes(self):
        from autopilot.phase3_csv_visual_preview import SCENES
        self.assertEqual([(a,b) for a,b,*_ in SCENES],
                         [(0,10),(10,20),(20,30),(30,42)])
        self.assertIn("UNITS",SCENES[0][3])
        self.assertIn("PRICE",SCENES[1][3])
        self.assertIn("DICTREADER",SCENES[2][2])
        self.assertIn("TOTAL",SCENES[3][2])
        samples=[visual_frame(moment,width=360).tobytes()
                 for moment in (5,15,25,35)]
        self.assertEqual(len(set(samples)),4)

    def test_english_visual_data_tamper_fails_closed(self):
        from unittest.mock import patch
        from autopilot.phase3_csv_visual_preview import _illustrative_csv_data
        with patch("autopilot.phase3_csv_visual_preview.demonstrate_csv_total",
                   return_value={"dataset_is_fictional":True,
                                 "purchased_anything":False,
                                 "youtube_uploaded":False,
                                 "publishing_authorized":False,
                                 "total":59,
                                 "rows":[{"product":"Pen","line_total":20}]}):
            with self.assertRaises(ValueError):
                _illustrative_csv_data()

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

    def test_1080p_visual_proof_is_limited_to_36_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/"guarded.mp4"
            with self.assertRaises(ValueError):
                render_visual_preview(output,duration_s=2,fps=24,width=1080)
            self.assertFalse(output.exists())

    def test_render_does_not_overwrite_existing_or_create_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/"already.mp4"
            output.write_bytes(b"do-not-change")
            with self.assertRaises(ValueError):
                render_visual_preview(output)
            self.assertEqual(output.read_bytes(),b"do-not-change")
            missing=Path(tmp)/"new_folder"/"clip.mp4"
            with self.assertRaises(ValueError):
                render_visual_preview(missing)
            self.assertFalse(missing.parent.exists())

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
