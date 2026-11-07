"""B4g4 adversarial encoded AAC loudnorm input measurements, no publication."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import autopilot.manual_rehearsal_review_export_b4e3 as export
from autopilot.test_manual_rehearsal_review_export_b4e3 import (
    qa_and_three_original_mp4s,
)
from autopilot.encoded_aac_loudness_review_b4g4 import (
    STATUS, REPORT_NAME, TARGET_FILTER, EncodedLoudnessRefused,
    parse_encoded_loudnorm, inspect_exact_three_mp4s,
)

SAMPLE_REPORT="""Input #0, mov,mp4, from original synthetic fixture
Stream #0:1: Audio: aac, 24000 Hz, mono
[Parsed_loudnorm_0 @ 0x1234]
{
    "input_i" : "-17.80",
    "input_tp" : "-1.82",
    "input_lra" : "3.50",
    "input_thresh" : "-28.20",
    "output_i" : "-16.00",
    "output_tp" : "-1.53",
    "output_lra" : "3.50",
    "output_thresh" : "-26.20",
    "normalization_type" : "dynamic",
    "target_offset" : "0.00"
}
video:0kB audio:0kB
"""


class StrictR128ParserTests(unittest.TestCase):
    def test_original_encoded_stream_not_filter_output(self):
        stats=parse_encoded_loudnorm(SAMPLE_REPORT)
        self.assertEqual(stats["measured_encoded_integrated_lufs"],-17.8)
        self.assertEqual(stats["measured_encoded_true_peak_dbtp"],-1.82)
        self.assertEqual(stats["measured_encoded_loudness_range_lu"],3.5)
        self.assertEqual(stats["measured_encoded_relative_gate_threshold_lufs"],-28.2)
        self.assertEqual(stats["warnings"],[])
        self.assertFalse(stats["automatic_gain_normalization_or_limiting_applied"])
        self.assertTrue(stats["measurement_is_actual_input_aac_not_normalized_output"])
        self.assertFalse(stats["human_audio_playback_review_completed"])
        self.assertFalse(stats["publication_authorized"])

    def test_true_peak_and_loudness_flags_are_advisory_not_automatic_mastering(self):
        for modified,expected in (
            (SAMPLE_REPORT.replace('"input_tp" : "-1.82"',
                                   '"input_tp" : "-0.31"'),
             "TRUE_PEAK_ABOVE_REVIEW_CEILING"),
            (SAMPLE_REPORT.replace('"input_i" : "-17.80"',
                                   '"input_i" : "-25.20"'),
             "INTEGRATED_LOUDNESS_QUIET_CHECK_ON_PHONE"),
            (SAMPLE_REPORT.replace('"input_i" : "-17.80"',
                                   '"input_i" : "-10.50"'),
             "INTEGRATED_LOUDNESS_HOT_CHECK_ON_PHONE"),
            (SAMPLE_REPORT.replace('"input_lra" : "3.50"',
                                   '"input_lra" : "19.20"'),
             "LOUDNESS_RANGE_WIDE_REVIEW_DYNAMICS"),
        ):
            with self.subTest(expected=expected):
                result=parse_encoded_loudnorm(modified)
                self.assertIn(expected,result["warnings"])
                self.assertFalse(result["publication_authorized"])

    def test_missing_bogus_infinite_duplicate_or_huge_stats_refused(self):
        variants=(
            SAMPLE_REPORT.replace('"input_tp" : "-1.82",',''),
            SAMPLE_REPORT.replace('"input_tp" : "-1.82"',
                                  '"input_tp" : "inf"'),
            SAMPLE_REPORT.replace('"input_i" : "-17.80"',
                                  '"input_i" : "NaN"'),
            SAMPLE_REPORT.replace('"input_lra" : "3.50"',
                                  '"input_lra" : "-20"'),
            SAMPLE_REPORT.replace('"input_i" : "-17.80"',
                                  '"input_i" : "true"'),
            SAMPLE_REPORT.replace('"normalization_type" : "dynamic"',
                                  '"normalization_type" : "external"'),
            SAMPLE_REPORT.replace('"input_thresh" : "-28.20"',
                                  '"input_thresh" : "-2.00"'),
            SAMPLE_REPORT+SAMPLE_REPORT,
            SAMPLE_REPORT.replace("}", "BROKEN"),
            "not a report",
            SAMPLE_REPORT*10000,
        )
        for number,bad in enumerate(variants):
            with self.subTest(variant=number),self.assertRaises(
                    EncodedLoudnessRefused):
                parse_encoded_loudnorm(bad)


class ExactOriginalThreeMP4Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.root=Path(self.tmp.name)/"test-source"
        self.folder=Path(self.tmp.name)/"owner-review"
        self.root.mkdir()
        qa=qa_and_three_original_mp4s(self.root)
        self.settings=patch.multiple(export,ROOT=self.root,TARGET=self.folder)
        self.settings.start()
        self.manifest=export.prepare_review_export(
            self.root,self.folder,qa)

    def tearDown(self):
        self.settings.stop()
        self.tmp.cleanup()

    def fake_ffmpeg(self,argv,**kwargs):
        self.assertEqual(argv[argv.index("-map")+1],"0:a:0")
        self.assertIn(TARGET_FILTER,argv)
        self.assertIn("-ar",argv)
        self.assertIn("192000",argv)
        self.assertIn("-nostdin",argv)
        self.assertEqual(kwargs["timeout"],230)
        self.assertEqual(kwargs["capture_output"],True)
        self.assertEqual(kwargs["check"],False)
        return SimpleNamespace(returncode=0,stderr=SAMPLE_REPORT)

    def test_all_three_hashes_source_clocks_and_17_scenes_bound(self):
        report=inspect_exact_three_mp4s(
            self.folder,ffmpeg="/simulated-ffmpeg",runner=self.fake_ffmpeg)
        self.assertEqual(report["status"],STATUS)
        self.assertEqual(report["videos_measured_from_real_encoded_aac"],3)
        self.assertEqual(report["original_narrated_scenes_represented"],17)
        self.assertEqual(report["three_video_integrated_lufs_spread"],0)
        self.assertEqual(report["human_audio_playback_reviews"],0)
        self.assertEqual(report["youtube_writes_or_release_authority"],0)
        self.assertTrue(report["normalization_filter_output_was_discarded_not_reencoded"])
        for row,source in zip(report["videos"],self.manifest["videos"]):
            self.assertEqual(row["slot"],source["slot"])
            self.assertEqual(row["source_mp4_sha256"],source["sha256"])
            self.assertEqual(row["source_duration_pcm_seconds"],
                             source["measured_audio_seconds"])
            self.assertFalse(row["publication_authorized"])

    def test_tampered_first_mp4_rejected_before_any_ffmpeg_call(self):
        mp4=self.folder/export.SLOT_NAMES[0][1]
        mp4.write_bytes(b"\0"*mp4.stat().st_size)
        called=[]
        with self.assertRaises(EncodedLoudnessRefused):
            inspect_exact_three_mp4s(
                self.folder,ffmpeg="ffmpeg",
                runner=lambda *args,**kwargs:called.append(True))
        self.assertEqual(called,[])

    def test_fake_release_flags_or_wrong_audio_identity_refused(self):
        path=self.folder/"REVIEW_ONLY_NO_PUBLISH.json"
        unaltered=path.read_text()
        for changed in (
            ("publishing_authorized",True),
            ("youtube_releases",1),
            ("rights_and_owner_approvals",1),
        ):
            manifest=deepcopy(self.manifest)
            manifest[changed[0]]=changed[1]
            path.write_text(json.dumps(manifest))
            with self.subTest(field=changed[0]),self.assertRaises(
                    EncodedLoudnessRefused):
                inspect_exact_three_mp4s(self.folder,ffmpeg="ffmpeg",
                                         runner=self.fake_ffmpeg)
        path.write_text(unaltered)
        manifest=deepcopy(self.manifest)
        manifest["videos"][0]["slot"]="long"
        path.write_text(json.dumps(manifest))
        with self.assertRaises(EncodedLoudnessRefused):
            inspect_exact_three_mp4s(self.folder,ffmpeg="ffmpeg",
                                     runner=self.fake_ffmpeg)

    def test_failed_real_decoder_blocks_false_loudness_report(self):
        with self.assertRaises(EncodedLoudnessRefused):
            inspect_exact_three_mp4s(
                self.folder,ffmpeg="ffmpeg",
                runner=lambda argv,**kw:SimpleNamespace(
                    returncode=1,stderr="unexpected codec"))
        self.assertFalse((self.folder/REPORT_NAME).exists())


class RealInstalledFFmpegLoudnessTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ffmpeg"),"GitHub runner installs FFmpeg")
    def test_real_22s_encoded_aac_loudnorm_json_input_fields(self):
        # A synthesized sine and synthetic color, never real voice/media.
        with TemporaryDirectory() as temporary:
            media=Path(temporary)/"synthetic-test-only.mp4"
            cmd=["ffmpeg","-hide_banner","-nostdin","-loglevel","error",
                 "-f","lavfi","-i","color=c=blue:s=96x96:r=6:d=22",
                 "-f","lavfi","-i",
                 "sine=frequency=440:sample_rate=24000:duration=22",
                 "-af","volume=0.7",
                 "-c:v","mpeg4","-q:v","7",
                 "-c:a","aac","-b:a","80k",
                 "-shortest","-y",str(media)]
            subprocess.run(cmd,capture_output=True,text=True,
                           timeout=45,check=True)
            process=subprocess.run([
                "ffmpeg","-hide_banner","-nostdin","-nostats",
                "-i",str(media),"-map","0:a:0","-vn",
                "-af",TARGET_FILTER,"-ar","192000","-f","null","-",
            ],capture_output=True,text=True,timeout=80,check=True)
            stats=parse_encoded_loudnorm(process.stderr)
            self.assertTrue(-70 < stats["measured_encoded_integrated_lufs"]<0)
            self.assertTrue(-80 < stats["measured_encoded_true_peak_dbtp"]<4)
            self.assertTrue(stats["measurement_is_actual_input_aac_not_normalized_output"])
            self.assertFalse(stats["publication_authorized"])


if __name__=="__main__":
    unittest.main()
