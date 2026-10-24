"""FFmpeg integration tests using tiny synthetic videos, never YouTube uploads."""
from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import unittest

from autopilot.flow_clip_intake import inspect_flow_clip, redacted_json
from autopilot.flow_cinematic_handoff import FlowHandoffError

PACK = (Path(__file__).resolve().parents[1] / "content" / "flow"
        / "oct24_cinematic_flow_scene_package.json")


def package():
    return json.loads(PACK.read_text(encoding="utf-8"))


class FlowClipIntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("ffprobe") or not shutil.which("ffmpeg"):
            raise unittest.SkipTest("ffmpeg / ffprobe required for actual media tests")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        def make(name, dimensions, duration=9.98, audio=True):
            output = cls.root / name
            command = ["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
                       "-f","lavfi","-i",f"color=c=blue:s={dimensions}:r=24"]
            if audio:
                command += ["-f","lavfi","-i","sine=frequency=440:sample_rate=32000"]
            command += ["-t",str(duration),"-c:v","libx264","-preset","ultrafast",
                        "-threads","1","-pix_fmt","yuv420p"]
            if audio:
                command += ["-c:a","aac","-shortest"]
            command += ["-y",str(output)]
            p = subprocess.run(command,capture_output=True,text=True,timeout=60)
            if p.returncode:
                raise RuntimeError(p.stderr[-1500:])
            return output
        cls.good = make("correct_vertical.mp4","360x640")
        cls.wrong = make("wrong_landscape.mp4","640x360")
        cls.silent = make("silent_vertical.mp4","360x640",audio=False)
        cls.short = make("short_vertical.mp4","360x640",duration=5)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls,"tmp"):
            cls.tmp.cleanup()

    def inspect(self, media, **options):
        return inspect_flow_clip(media, package(), episode_id="fm_20261024_short_en",
                                 clip_id="01", **options)

    def test_correct_mp4_has_byte_hash_but_no_release(self):
        result = self.inspect(self.good)
        self.assertEqual(result.status,"PASS_MEDIA_INTAKE_PENDING_INDEPENDENT_QA")
        self.assertEqual((result.width,result.height),(360,640))
        self.assertEqual(len(result.media_sha256),64)
        self.assertTrue(result.technical_candidate)
        self.assertFalse(result.character_consistency_verified)
        self.assertFalse(result.natural_voice_verified)
        self.assertFalse(result.release_authorized)
        self.assertFalse(result.youtube_scheduled)

    def test_landscape_is_not_our_vertical_short(self):
        result = self.inspect(self.wrong)
        self.assertIn("WRONG_ASPECT_RATIO",result.errors)
        self.assertFalse(result.technical_candidate)

    def test_silent_source_needs_narration(self):
        result=self.inspect(self.silent)
        self.assertIn("NARRATION_AUDIO_MISSING",result.warnings)
        self.assertFalse(result.natural_voice_verified)

    def test_five_seconds_rejected(self):
        self.assertIn("INVALID_CLIP_DURATION",self.inspect(self.short).errors)

    def test_unrecognized_source_cannot_be_attested(self):
        with self.assertRaises(FlowHandoffError):
            self.inspect(self.good,source="official_youtube")

    def test_unknown_scene_cannot_be_imported(self):
        with self.assertRaises(FlowHandoffError):
            inspect_flow_clip(self.good,package(),episode_id="fm_20261024_short_hi",
                              clip_id="01",mode="pilot")

    def test_hindi_supported_in_lean_plan(self):
        result=inspect_flow_clip(self.good,package(),
                                 episode_id="fm_20261024_short_hi",clip_id="01",
                                 mode="lean_day")
        self.assertTrue(result.technical_candidate)

    def test_invalid_filename(self):
        self.assertIn("UNSAFE_OR_MISSING_MP4",
                      self.inspect(self.root/"missing video.mp4").errors)

    def test_missing_mp4(self):
        self.assertIn("UNSAFE_OR_MISSING_MP4",
                      self.inspect(self.root/"missing.mp4").errors)

    def test_corrupt_mp4(self):
        corrupt=self.root/"corrupt.mp4"
        corrupt.write_bytes(b"x"*300)
        self.assertIn("FFPROBE_FAILED",self.inspect(corrupt).errors)

    def test_reject_symlink(self):
        link=self.root/"badlink.mp4"
        try:
            link.symlink_to(self.good)
        except (OSError,NotImplementedError):
            self.skipTest("Filesystem disallows symlink")
        self.assertIn("UNSAFE_OR_MISSING_MP4",self.inspect(link).errors)

    def test_report_does_not_leak_file_directory(self):
        text=json.dumps(redacted_json(self.inspect(self.good)))
        self.assertNotIn(str(self.root),text)
        self.assertIn("correct_vertical.mp4",text)


if __name__ == "__main__":
    unittest.main()
