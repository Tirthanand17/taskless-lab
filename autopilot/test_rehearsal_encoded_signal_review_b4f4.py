"""B4f4 final encoded MP4 diagnostics: no external FFmpeg/media/credentials in tests."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import autopilot.manual_rehearsal_review_export_b4e3 as export
from autopilot.test_manual_rehearsal_review_export_b4e3 import qa_and_three_original_mp4s
from autopilot.rehearsal_encoded_signal_review_b4f4 import (
    SignalReviewRefused, STATUS, REPORT_NAME,
    parse_ffmpeg_signals, inspect_review_directory,
)


LOG = """Input #0, mov,mp4,m4a,3gp,3g2,mj2, from fake:
  Stream #0:0: Video: h264
  Stream #0:1: Audio: aac
[blackdetect] black_start:1 black_end:1.9 black_duration:0.9
[freezedetect] freeze_start: 12.0
[freezedetect] freeze_end: 18 | freeze_duration: 6
[silencedetect] silence_end: 23.0 | silence_duration: 2.2
[Parsed_volumedetect] mean_volume: -18.9 dB
[Parsed_volumedetect] max_volume: -0.2 dB
frame=900 video:123kB audio:45kB subtitle:0kB
"""


class FFmpegParserTests(unittest.TestCase):
    def test_detects_real_av_signal_event_locations_without_claiming_approval(self):
        report=parse_ffmpeg_signals(LOG,duration=57.8)
        self.assertEqual(report["warning_codes"],[
            "BLACK_SEGMENT_REVIEW",
            "POTENTIALLY_STATIC_OR_FROZEN_VISUAL_REVIEW",
            "LONG_SILENCE_LISTEN_AND_CHECK",
        ])
        self.assertEqual(report["audio_silence_intervals"][0]["start_seconds"],20.8)
        self.assertEqual(report["freeze_intervals"][0]["duration_seconds"],6)
        self.assertFalse(report["human_full_audio_visual_watch_completed"])
        self.assertFalse(report["final_rights_or_facts_approved"])

    def test_unfinished_final_static_frame_is_advisory(self):
        data=LOG.replace(
            "[freezedetect] freeze_end: 18 | freeze_duration: 6\n","")
        result=parse_ffmpeg_signals(data,duration=57.8)
        self.assertTrue(result["freeze_intervals"][0]["unfinished_at_video_end"])
        self.assertEqual(result["freeze_intervals"][0]["start_seconds"],12)

    def test_near_clipping_audio_is_marked_review_required(self):
        data=LOG.replace("max_volume: -0.2 dB","max_volume: 0.0 dB")
        result=parse_ffmpeg_signals(data,duration=57.8)
        self.assertIn("SAMPLE_PEAK_NEAR_ZERO_CLIPPING_RISK",result["warning_codes"])
        self.assertTrue(result["sample_peak_is_not_true_peak"] if "sample_peak_is_not_true_peak" in result else
                        result["technical_anomaly_detector_is_not_a_human_judgment"])

    def test_missing_audio_or_video_measurement_fails_closed(self):
        for bad in (
            LOG.replace("max_volume: -0.2 dB",""),
            LOG.replace("mean_volume: -18.9 dB",""),
            LOG.replace("video:123kB","not-video-summary"),
            LOG.replace("black_end:1.9","black_end:99"),
            LOG.replace("freeze_duration: 6","freeze_duration: 20"),
            LOG.replace("silence_duration: 2.2","silence_duration: 223"),
            LOG.replace("max_volume: -0.2 dB","max_volume: -inf dB"),
        ):
            with self.subTest(bad=bad[-120:]),self.assertRaises(SignalReviewRefused):
                parse_ffmpeg_signals(bad,duration=57.8)

    def test_no_events_is_not_editorial_approval(self):
        minimal="\n".join(line for line in LOG.splitlines()
                          if not any(key in line for key in (
                              "black_start","freeze_start","freeze_end","silence_end")))
        report=parse_ffmpeg_signals(minimal,duration=57.8)
        self.assertEqual(report["warning_codes"],[])
        self.assertFalse(report["human_full_audio_visual_watch_completed"])


class ActualHostedFFmpegProbeTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg not installed")
    def test_actual_23_second_full_decoded_video_static_black_event(self):
        # Original generated sound/image ONLY; 96px, no human likeness.
        # This proves installed FFmpeg filters emit parseable real signals.
        with TemporaryDirectory() as directory:
            output=Path(directory)/"synthetic-test-only.mp4"
            subprocess.run([
                "ffmpeg","-hide_banner","-nostdin","-loglevel","error",
                "-f","lavfi","-i","color=c=black:s=96x96:r=6:d=23",
                "-f","lavfi","-i","sine=frequency=440:sample_rate=16000:duration=23",
                "-c:v","mpeg4","-q:v","7","-c:a","aac",
                "-shortest","-y",str(output),
            ],capture_output=True,text=True,check=True,timeout=40)
            probe=subprocess.run([
                "ffmpeg","-hide_banner","-nostdin","-nostats",
                "-i",str(output),
                "-map","0:v:0","-map","0:a:0",
                "-vf","blackdetect=d=0.8:pix_th=0.1:pic_th=0.99,"
                      "freezedetect=n=-60dB:d=5",
                "-af","silencedetect=noise=-48dB:d=1.6,volumedetect",
                "-f","null","-",
            ],capture_output=True,text=True,check=True,timeout=40)
            evidence=parse_ffmpeg_signals(probe.stderr,duration=23)
            self.assertIn("BLACK_SEGMENT_REVIEW",evidence["warning_codes"])
            self.assertIn("POTENTIALLY_STATIC_OR_FROZEN_VISUAL_REVIEW",
                          evidence["warning_codes"])
            self.assertFalse(evidence["human_full_audio_visual_watch_completed"])


class StrictManualArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.root=Path(self.temp.name)/"three-real-source-fixture-bytes"
        self.target=Path(self.temp.name)/"review-artifact"
        self.root.mkdir()
        self.qa=qa_and_three_original_mp4s(self.root)
        self.scope=patch.multiple(export,ROOT=self.root,TARGET=self.target)
        self.scope.start()
        self.manifest=export.prepare_review_export(self.root,self.target,self.qa)

    def tearDown(self):
        self.scope.stop()
        self.temp.cleanup()

    def fake_runner(self,argv,**kwargs):
        self.assertIn("-vf",argv)
        self.assertIn("blackdetect=d=0.8:pix_th=0.1:pic_th=0.99,freezedetect=n=-60dB:d=5",
                      argv)
        self.assertIn("-af",argv)
        self.assertIn("silencedetect=noise=-48dB:d=1.6,volumedetect",argv)
        self.assertIn("-nostdin",argv)
        self.assertIn("-f",argv)
        self.assertEqual(kwargs["timeout"],230)
        return SimpleNamespace(returncode=0,stderr=LOG)

    def test_three_sha_bound_real_byte_files_and_signal_rows(self):
        result=inspect_review_directory(self.target,ffmpeg="/injected/ffmpeg",
                                        runner=self.fake_runner)
        self.assertEqual(result["status"],STATUS)
        self.assertEqual(result["physical_original_encoded_mp4s_independently_decoded_for_signals"],3)
        self.assertEqual(result["original_scenes_represented"],17)
        self.assertEqual([x["original_voiced_scene_count"] for x in result["videos"]],[4,9,4])
        self.assertTrue(all(x["warning_codes"] for x in result["videos"]))
        self.assertEqual(result["human_full_video_reviews"],0)
        self.assertEqual(result["youtube_uploads_or_release_authority"],0)
        for row,origin in zip(result["videos"],self.manifest["videos"]):
            self.assertEqual(row["source_mp4_sha256"],origin["sha256"])
            self.assertFalse(row["human_full_audio_visual_watch_completed"])
        self.assertEqual(REPORT_NAME,"ENCODED_MP4_SIGNAL_WARNINGS_UNAPPROVED.json")

    def test_substituted_mp4_rejected_before_ffmpeg(self):
        video=self.target/export.SLOT_NAMES[1][1]
        video.write_bytes(b"\x00"*video.stat().st_size)
        calls=[]
        with self.assertRaises(SignalReviewRefused):
            inspect_review_directory(
                self.target,ffmpeg="ffmpeg",
                runner=lambda *args,**kwargs:calls.append(True))
        self.assertEqual(calls,[])

    def test_manifest_forged_release_state_rejected(self):
        path=self.target/"REVIEW_ONLY_NO_PUBLISH.json"
        doc=json.loads(path.read_text())
        doc["publishing_authorized"]=True
        path.write_text(json.dumps(doc))
        with self.assertRaises(SignalReviewRefused):
            inspect_review_directory(self.target,ffmpeg="ffmpeg",
                                     runner=self.fake_runner)

    def test_decoder_failure_refused_no_false_quality_report(self):
        with self.assertRaises(SignalReviewRefused):
            inspect_review_directory(
                self.target,ffmpeg="ffmpeg",
                runner=lambda *args,**kwargs:SimpleNamespace(
                    returncode=1,stderr="unknown filter"))
        self.assertFalse((self.target/REPORT_NAME).exists())


if __name__=="__main__":
    unittest.main()
