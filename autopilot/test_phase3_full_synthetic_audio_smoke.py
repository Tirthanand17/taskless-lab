"""Real FFmpeg synthetic media tests, never human voices or real publication."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import shutil
import subprocess
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.phase3_full_synthetic_audio_smoke import (
    run_full_synthetic_tone_smoke, _probe_real_audio_energy,
)

@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "Isolated cloud runner needs existing ffmpeg/ffprobe")
class RealSyntheticAVSmokeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.mp4=self.root/"original-TEST-TONE-ONLY.mp4"
        subprocess.run([
            "ffmpeg","-nostdin","-v","error","-xerror","-n",
            "-f","lavfi","-i","color=c=navy:s=360x640:r=24:d=1",
            "-c:v","libx264","-pix_fmt","yuv420p","-frames:v","24",
            str(self.mp4),
        ],check=True,capture_output=True,timeout=40)

    def real_one_second_smoke(self):
        catalog={"csv_tutorial_short_en":(1,360,640,24,24)}
        with (
            patch("autopilot.phase3_full_synthetic_audio_smoke.EPISODES",catalog),
            patch("autopilot.phase3_full_ephemeral_audio_batch.EPISODES",catalog),
        ):
            return run_full_synthetic_tone_smoke(
                episode_id="csv_tutorial_short_en",
                silent_mp4=self.mp4,scratch_dir=self.root)

    def test_real_synthetic_h264_aac_full_decode_and_cleanup(self):
        report=self.real_one_second_smoke()
        self.assertEqual(report["video_frames"],24)
        self.assertEqual(report["video_codec"],"h264")
        self.assertEqual(report["audio_codec"],"aac")
        self.assertTrue(report["output_h264_aac_fully_decoded"])
        self.assertGreater(report["measured_audio_rms"],.002)
        self.assertTrue(report["temp_media_removed_before_return"])
        self.assertFalse(report["contains_genuine_natural_speech"])
        self.assertFalse(report["caption_alignment_verified"])
        self.assertFalse(report["publishing_authorized"])
        self.assertEqual(list(self.root.iterdir()),[self.mp4])

    def test_wrong_episode_refused(self):
        with self.assertRaises(WorkflowError):
            run_full_synthetic_tone_smoke(
                episode_id="unsupported",silent_mp4=self.mp4,
                scratch_dir=self.root)

    def test_original_with_existing_audio_refused(self):
        audio_video=self.root/"with-audio.mp4"
        subprocess.run([
            "ffmpeg","-nostdin","-v","error","-xerror","-n",
            "-f","lavfi","-i","color=c=navy:s=360x640:r=24:d=1",
            "-f","lavfi","-i","sine=frequency=220:duration=1",
            "-c:v","libx264","-pix_fmt","yuv420p",
            "-c:a","aac","-frames:v","24", "-shortest",str(audio_video),
        ],check=True,capture_output=True,timeout=40)
        with (
            patch("autopilot.phase3_full_synthetic_audio_smoke.EPISODES",
                  {"csv_tutorial_short_en":(1,360,640,24,24)}),
            self.assertRaises(WorkflowError),
        ):
            run_full_synthetic_tone_smoke(
                episode_id="csv_tutorial_short_en",
                silent_mp4=audio_video,scratch_dir=self.root)

    def test_symlink_or_missing_inputs_fail_closed(self):
        link=self.root/"alias.mp4"
        link.symlink_to(self.mp4)
        for media in (link,self.root/"not-found.mp4"):
            with (
                patch("autopilot.phase3_full_synthetic_audio_smoke.EPISODES",
                      {"csv_tutorial_short_en":(1,360,640,24,24)}),
                self.assertRaises(WorkflowError),
            ):
                run_full_synthetic_tone_smoke(
                    episode_id="csv_tutorial_short_en",
                    silent_mp4=media,scratch_dir=self.root)
        self.assertFalse(any(p.name.startswith("flowminute-synthetic-tone")
                             for p in self.root.iterdir()))

    def test_bad_scratch_does_not_create_folder(self):
        missing=self.root/"missing"
        with self.assertRaises(WorkflowError):
            run_full_synthetic_tone_smoke(
                episode_id="csv_tutorial_short_en",
                silent_mp4=self.mp4,scratch_dir=missing)
        self.assertFalse(missing.exists())

    def test_prohibited_publishing_flags_never_true(self):
        report=self.real_one_second_smoke()
        for flag in ("narrator_identity_or_language_verified",
                     "caption_alignment_verified",
                     "factual_creative_or_legal_rights_verified",
                     "commercial_release_ready","ready_for_mux_or_upload",
                     "youtube_upload_or_scheduling_authorized",
                     "publishing_authorized","new_service_or_provider_used"):
            with self.subTest(flag=flag):
                self.assertIs(report[flag],False)

if __name__=="__main__":
    unittest.main()
