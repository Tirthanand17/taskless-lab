"""Phase 3R3 actual-HD performance report calculations and safe cleanup tests.

Production-size renders occur in an existing public GitHub smoke runner, never
here. Unit tests use fake bounded clips; they MUST NOT be described as video
encoding or proof of a rights-cleared narrated release.
"""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from autopilot.agent_org import WorkflowError
from autopilot.phase3_hd_capacity_benchmark import (
    CASES,FPS,analyze_hd_samples,run_hd_capacity_benchmark,
)


def simulated():
    return [
        {
            "episode_id":case.episode_id,
            "render_wall_seconds":1.25+i,
            "output_bytes":10000+i*1000,
            "width":case.width,
            "height":case.height,
            "frame_count":FPS,
            "audio_stream_count":0,
        }
        for i,case in enumerate(CASES)
    ]


class NativeHDMeasurementTests(unittest.TestCase):
    def test_three_samples_are_not_production_approval(self):
        result=analyze_hd_samples(simulated())
        self.assertEqual(result["sample_count"],3)
        self.assertEqual(result["samples"][0]["format"],"1080x1920")
        self.assertEqual(result["samples"][-1]["format"],"1920x1080")
        self.assertGreater(result["naive_linear_render_seconds_UNVALIDATED"],0)
        for flag in (
            "full_hd_daily_batch_capacity_verified",
            "sustained_zero_cost_verified",
            "voice_naturalness_verified",
            "speech_subtitle_sync_verified",
            "high_quality_3d_verified",
            "publishing_authorized",
            "youtube_upload_authorized",
        ):
            self.assertFalse(result[flag])

    def test_report_order_unchanged_by_measurement_order(self):
        x=simulated()
        self.assertEqual(analyze_hd_samples(x),analyze_hd_samples(list(reversed(x))))

    def test_frame_and_resolution_still_checked(self):
        for field,value in (("width",720),("height",720),
                            ("frame_count",23),("audio_stream_count",1),
                            ("output_bytes",1),("render_wall_seconds",0)):
            x=simulated()
            x[0][field]=value
            with self.subTest(field=field),self.assertRaises(WorkflowError):
                analyze_hd_samples(x)

    def test_nonfinite_wall_clock_rejected(self):
        for value in (float("nan"),float("inf"),float("-inf"),True):
            x=simulated()
            x[0]["render_wall_seconds"]=value
            with self.subTest(value=str(value)),self.assertRaises(WorkflowError):
                analyze_hd_samples(x)

    def test_unreasonably_long_job_rejected(self):
        x=simulated()
        x[0]["render_wall_seconds"]=1000
        with self.assertRaises(WorkflowError):
            analyze_hd_samples(x)

    def test_missing_duplicate_and_unknown_episodes_blocked(self):
        x=simulated()
        for altered in (x[:2], x+[x[0]], [x[0],x[0],x[2]],
                        [dict(x[0],episode_id="unknown"),x[1],x[2]]):
            with self.subTest(length=len(altered)),self.assertRaises(WorkflowError):
                analyze_hd_samples(altered)

    def test_negative_stated_publication_flags_are_permanent(self):
        result=analyze_hd_samples(simulated())
        self.assertEqual(result["network_calls"],0)
        self.assertFalse(result["new_paid_service_connected"])
        self.assertIn("UNVALIDATED",str(result))

    @patch("autopilot.phase3_hd_capacity_benchmark.shutil.which",return_value="/usr/bin/ffmpeg")
    @patch("autopilot.phase3_hd_capacity_benchmark._inspect_video")
    @patch("autopilot.phase3_hd_capacity_benchmark.render_hindi_visual_preview")
    @patch("autopilot.phase3_hd_capacity_benchmark.render_visual_preview")
    def test_fake_renderer_proves_all_outputs_are_deleted_without_upload(
        self,english,hindi,probe,_which
    ):
        def write_fake(*args,**kwargs):
            # These are stub bytes, *not* a real video. Media codecs are
            # separately checked on GitHub's live smoke test.
            target=args[0] if len(args)==1 else args[1]
            Path(target).write_bytes(b"x"*4096)
            return {"publishing_authorized":False}
        english.side_effect=write_fake
        hindi.side_effect=write_fake
        def synthetic_probe(path, *,case):
            return {
                "episode_id":case.episode_id,
                "width":case.width,
                "height":case.height,
                "frame_count":FPS,
                "audio_stream_count":0
            }
        probe.side_effect=synthetic_probe
        with tempfile.TemporaryDirectory() as tmp:
            report=run_hd_capacity_benchmark(Path(tmp))
            self.assertTrue(report["all_three_real_h264_hd_scenes_decoded"])
            # Above is set by runner code only AFTER _inspect_video succeeds;
            # injected test probe does not validate actual FFmpeg.
            self.assertFalse(report["publishing_authorized"])
            self.assertFalse(report["media_durable_storage_created"])
            self.assertEqual(list(Path(tmp).iterdir()),[])
            self.assertEqual(english.call_count,1)
            self.assertEqual(hindi.call_count,2)

    def test_no_auto_created_folders_or_overwritten_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with self.assertRaises(WorkflowError):
                run_hd_capacity_benchmark(root/"not_created")
            first=root/CASES[0].output_basename
            first.write_bytes(b"owner-file")
            with self.assertRaises(WorkflowError):
                run_hd_capacity_benchmark(root)
            self.assertEqual(first.read_bytes(),b"owner-file")


if __name__=="__main__":
    unittest.main()
