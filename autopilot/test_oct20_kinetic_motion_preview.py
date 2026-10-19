"""Actual layered bilingual 2.5D frame and silent H264 preview tests.

Synthetic content only; no human narration, no SRT, no real YouTube/channel.
The CI renders one whole second (24 original frames), not full video,
to respect the existing free runner budget and prevent heavy preview jobs.
"""
from hashlib import sha256
from pathlib import Path
import shutil
import tempfile
import unittest

from PIL import Image

from autopilot.agent_org import WorkflowError
from autopilot.oct20_kinetic_motion_preview import (
    BEATS,CHROME,FPS,WIDTH,HEIGHT,MAX_PREVIEW_SECONDS,
    _design_valid,draw_motion_frame,render_kinetic_silent_excerpt,
)


class KineticBilingualStoryboardTests(unittest.TestCase):
    def test_beat_plan_matches_two_independently_authored_shorts(self):
        self.assertEqual(set(BEATS),{
            "fm_20261020_short_en","fm_20261020_short_hi"
        })
        self.assertEqual(len(BEATS["fm_20261020_short_en"]),3)
        self.assertEqual(len(BEATS["fm_20261020_short_hi"]),3)
        self.assertNotEqual(BEATS["fm_20261020_short_en"][0],
                            BEATS["fm_20261020_short_hi"][0])
        _design_valid("fm_20261020_short_en",9)
        _design_valid("fm_20261020_short_hi",12)

    def test_hindi_lane_keeps_approval_and_labels_in_devanagari(self):
        for label in ("concept","tagline","step","review","lock","approval","footer"):
            with self.subTest(label=label):
                hindi=CHROME["hi"][label]
                english=CHROME["en"][label]
                self.assertNotEqual(hindi,english)
                self.assertTrue(any("\u0900"<=ch<="\u097f" for ch in hindi))
        self.assertIn("अनुमति",CHROME["hi"]["approval"])
        self.assertIn("अपलोड",CHROME["hi"]["footer"])

    def test_real_english_hindi_first_frame_draws_without_font_fallback(self):
        for episode in sorted(BEATS):
            with self.subTest(episode=episode):
                frame=draw_motion_frame(episode,0)
                self.assertIs(type(frame),Image.Image)
                self.assertEqual(frame.mode,"RGB")
                self.assertEqual(frame.size,(WIDTH,HEIGHT))
                self.assertGreater(len(set(frame.getdata())),500)

    def test_depth_and_moving_camera_generate_actual_distinct_frames(self):
        for episode in sorted(BEATS):
            with self.subTest(episode=episode):
                times=(0,6,18,25,96,128,200)
                hashes=[sha256(draw_motion_frame(episode,x).tobytes()).hexdigest()
                        for x in times]
                self.assertEqual(len(set(hashes)),len(times))
                self.assertNotEqual(hashes[0],hashes[4])

    def test_frame_number_is_bounded_and_requires_known_episode(self):
        for episode,frame in (
            ("missing",0),
            ("fm_20261020_long_hi",1),
            ("fm_20261020_short_en",-1),
            ("fm_20261020_short_en",288),
            ("fm_20261020_short_hi",1.5),
        ):
            with self.subTest(episode=episode,frame=frame):
                with self.assertRaises(WorkflowError):
                    draw_motion_frame(episode,frame)

    def test_no_reuse_of_full_episode_duration_as_preview(self):
        for length in (0,13,42,44,480,3.5,True):
            with self.subTest(length=length),self.assertRaises(WorkflowError):
                _design_valid("fm_20261020_short_en",length)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg and FFprobe must already be installed")
    def test_actually_encodes_one_second_of_original_motion_without_audio(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/"original_motion_no_audio.mp4"
            result=render_kinetic_silent_excerpt(
                episode_id="fm_20261020_short_en",
                output_path=target,seconds=1,
            )
            self.assertGreater(target.stat().st_size,1500)
            self.assertEqual(result["frame_count"],24)
            self.assertEqual(result["audio_track_count"],0)
            self.assertTrue(result["has_actual_layered_motion"])
            self.assertFalse(result["full_episode_completed"])
            self.assertFalse(result["cinematic_3d_mesh_rendered"])
            self.assertFalse(result["licensed_narration_verified"])
            self.assertFalse(result["youtube_upload_authorized"])
            self.assertFalse(result["youtube_publish_authorized"])
            self.assertEqual(result["external_network_calls"],0)
            self.assertEqual(result["monthly_recurring_infrastructure_inr"],0)

    def test_refuse_existing_owner_file_before_ffmpeg(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/"preserve.mp4"
            target.write_bytes(b"OWNER_MEDIA_KEEP_UNCHANGED")
            with self.assertRaises(WorkflowError):
                render_kinetic_silent_excerpt(
                    episode_id="fm_20261020_short_hi",
                    output_path=target,seconds=2,
                )
            self.assertEqual(target.read_bytes(),b"OWNER_MEDIA_KEEP_UNCHANGED")

    def test_unsupported_episode_and_input_file_types_denied(self):
        with tempfile.TemporaryDirectory() as folder:
            for episode,out in (
                ("fm_20261020_long_hi","video.mp4"),
                ("unknown","video.mp4"),
                ("fm_20261020_short_en","video.mov"),
            ):
                with self.subTest(episode=episode,out=out):
                    with self.assertRaises(WorkflowError):
                        render_kinetic_silent_excerpt(
                            episode_id=episode,
                            output_path=Path(folder)/out,seconds=2,
                        )


if __name__=="__main__":
    unittest.main()
