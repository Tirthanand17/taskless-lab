"""B4g5 final AAC true-peak bounded mastering (NO PUBLISH), adversarial QA."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from autopilot.verified_aac_mastering_b4g5 import (
    STATUS,AUDIO_MASTERING_FILTER,AUDIO_ENCODE_HZ,
    ACCEPTED_INTEGRATED_LUFS_MIN,ACCEPTED_INTEGRATED_LUFS_MAX,
    ACCEPTED_TRUE_PEAK_DBTP_MAX,ACCEPTED_THREE_VIDEO_LUFS_SPREAD_MAX,
    EncodedMasteringRefused,
    verify_exact_encoded_master,verify_three_matching_masters,
)

# The JSON format matches one single *actual* FFmpeg EBU R128 input block.
SOURCE_MEASUREMENT="""Stream #0:1: Audio: aac
[Parsed_loudnorm_0 @ 0xabc]
{
    "input_i" : "-18.25",
    "input_tp" : "-1.42",
    "input_lra" : "2.00",
    "input_thresh" : "-28.73",
    "output_i" : "-16.38",
    "output_tp" : "-1.50",
    "output_lra" : "1.90",
    "output_thresh" : "-26.84",
    "normalization_type" : "dynamic",
    "target_offset" : "0.38"
}
video:0kB audio:0kB
"""


class ExactEncodedMasteringUnitTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.media=Path(self.tmp.name)/"final-original.mp4"
        self.media.write_bytes(b"original MP4 synthetic fixture "*18000)
        self.digest=sha256(self.media.read_bytes()).hexdigest()
        self.runs=[]

    def tearDown(self):
        self.tmp.cleanup()

    def fake_runner(self,argv,**kwargs):
        self.runs.append(argv)
        self.assertIn("-map",argv)
        self.assertEqual(argv[argv.index("-map")+1],"0:a:0")
        self.assertIn("-af",argv)
        self.assertIn("-ar",argv)
        self.assertEqual(argv[argv.index("-ar")+1],"192000")
        self.assertEqual(kwargs["timeout"],240)
        self.assertFalse(kwargs["check"])
        return SimpleNamespace(returncode=0,stderr=SOURCE_MEASUREMENT)

    def test_actual_input_measurement_is_bound_to_exact_verified_original_hash(self):
        evidence=verify_exact_encoded_master(
            "ffmpeg",self.media,self.digest,57.852,runner=self.fake_runner)
        self.assertEqual(evidence["status"],STATUS)
        self.assertEqual(evidence["exact_original_mp4_sha256"],self.digest)
        self.assertEqual(evidence["source_pcm_duration_seconds_unchanged"],57.852)
        self.assertEqual(evidence["measured_final_encoded_integrated_lufs"],-18.25)
        self.assertEqual(evidence["measured_final_encoded_oversampled_true_peak_dbtp"],-1.42)
        self.assertTrue(evidence["integrated_lufs_and_true_peak_within_internal_band"])
        self.assertFalse(evidence["human_listening_and_mobile_playback_verified"])
        self.assertFalse(evidence["youtube_upload_or_release_authorized"])
        self.assertEqual(len(self.runs),1)
        self.assertIn("linear=false",AUDIO_MASTERING_FILTER)
        self.assertIn("TP=-1.5",AUDIO_MASTERING_FILTER)
        self.assertEqual(AUDIO_ENCODE_HZ,48000)

    def test_tamper_bad_digest_infinite_time_and_deceptive_status_refused(self):
        for digest,seconds in (
            ("0"*64,57.852),
            ("not-sha",57.852),
            (self.digest,float("nan")),
            (self.digest,True),
            (self.digest,1),
            (self.digest,345),
        ):
            with self.subTest(seconds=seconds,digest=digest),self.assertRaises(
                    EncodedMasteringRefused):
                verify_exact_encoded_master(
                    "ffmpeg",self.media,digest,seconds,runner=self.fake_runner)
        self.assertEqual(len(self.runs),0)

    def test_invalid_loudness_truepeak_silent_audio_or_bad_decoder_rejected(self):
        variants=(
            SOURCE_MEASUREMENT.replace('"input_i" : "-18.25"',
                                       '"input_i" : "-26.16"'),
            SOURCE_MEASUREMENT.replace('"input_i" : "-18.25"',
                                       '"input_i" : "-12.00"'),
            SOURCE_MEASUREMENT.replace('"input_tp" : "-1.42"',
                                       '"input_tp" : "-0.15"'),
            SOURCE_MEASUREMENT.replace('"input_lra" : "2.00"',
                                       '"input_lra" : "30.00"'),
            SOURCE_MEASUREMENT.replace('"input_i" : "-18.25"',
                                       '"input_i" : "-inf"'),
            SOURCE_MEASUREMENT.replace('"input_tp" : "-1.42"',
                                       '"input_tp" : "nan"'),
            SOURCE_MEASUREMENT.replace('"input_i" : "-18.25",',''),
            SOURCE_MEASUREMENT+SOURCE_MEASUREMENT,
        )
        for log in variants:
            with self.subTest(log=log[-55:]),self.assertRaises(
                    EncodedMasteringRefused):
                verify_exact_encoded_master("ffmpeg",self.media,self.digest,
                    57.852,runner=lambda argv,**kwargs:
                        SimpleNamespace(returncode=0,stderr=log))
        with self.assertRaises(EncodedMasteringRefused):
            verify_exact_encoded_master("ffmpeg",self.media,self.digest,
                57.852,runner=lambda argv,**kwargs:
                    SimpleNamespace(returncode=1,stderr="PRIVATE_TOKEN"))
        with self.assertRaises(EncodedMasteringRefused):
            verify_exact_encoded_master("ffmpeg",self.media,self.digest,
                57.852,runner=lambda argv,**kwargs:(_ for _ in ()).throw(
                    subprocess.TimeoutExpired("ffmpeg",240)))

    def test_three_video_cross_master_consistency_and_no_auto_approval(self):
        sources=[]
        for slot,seconds,lufs in (
            ("short_am",57.852,-18.25),
            ("long",241.95,-18.33),
            ("short_pm",57.296,-18.14),
        ):
            source_hash=slot.encode("ascii").hex().ljust(64,"a")[:64]
            report={
                "status":STATUS,
                "exact_original_mp4_sha256":source_hash,
                "source_pcm_duration_seconds_unchanged":seconds,
                "integrated_lufs_and_true_peak_within_internal_band":True,
                "measured_final_encoded_integrated_lufs":lufs,
                "human_listening_and_mobile_playback_verified":False,
                "youtube_upload_or_release_authorized":False,
            }
            sources.append({
                "slot":slot,"encoded_h264_aac_sha256":source_hash,
                "real_pcm_measured_seconds":seconds,
                "original_audio_encoded_mastering":report,
            })
        summary=verify_three_matching_masters(sources)
        self.assertAlmostEqual(summary["actual_final_three_video_integrated_lufs_spread"],.19,places=2)
        self.assertFalse(summary["youtube_release_authorized"])
        altered=deepcopy(sources)
        altered[1]["original_audio_encoded_mastering"]["measured_final_encoded_integrated_lufs"]=-23.5
        with self.assertRaises(EncodedMasteringRefused):
            verify_three_matching_masters(altered)
        changed=deepcopy(sources)
        changed[0]["original_audio_encoded_mastering"]["exact_original_mp4_sha256"]="f"*64
        with self.assertRaises(EncodedMasteringRefused):
            verify_three_matching_masters(changed)
        changed=deepcopy(sources)
        changed[2]["original_audio_encoded_mastering"]["human_listening_and_mobile_playback_verified"]=True
        with self.assertRaises(EncodedMasteringRefused):
            verify_three_matching_masters(changed)
        changed=deepcopy(sources)
        changed[2]["original_audio_encoded_mastering"]["youtube_upload_or_release_authorized"]=True
        with self.assertRaises(EncodedMasteringRefused):
            verify_three_matching_masters(changed)

    def test_target_is_internal_bounded_review_range_not_platform_standard(self):
        self.assertEqual((ACCEPTED_INTEGRATED_LUFS_MIN,
                          ACCEPTED_INTEGRATED_LUFS_MAX),(-20.5,-15.5))
        self.assertEqual(ACCEPTED_TRUE_PEAK_DBTP_MAX,-1.0)
        self.assertEqual(ACCEPTED_THREE_VIDEO_LUFS_SPREAD_MAX,4.0)


class PhysicalFFmpegNormalizationTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ffmpeg"),"Physical FFmpeg not installed")
    def test_actual_original_22s_quiet_aac_is_normalized_and_remeasured(self):
        # Offline synthetic blue image + generated sine. No owner media or
        # source article, no actual voice, no YouTube or external sample.
        with TemporaryDirectory() as dirname:
            root=Path(dirname)
            quiet=root/"original-22s-quiet.mp4"
            corrected=root/"original-22s-corrected.mp4"
            subprocess.run([
                "ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
                "-f","lavfi","-i","color=c=blue:s=96x96:r=8:d=22",
                "-f","lavfi","-i",
                "sine=frequency=260:sample_rate=24000:duration=22",
                "-af","volume=0.18","-c:v","mpeg4","-q:v","6",
                "-c:a","aac","-b:a","80k","-shortest",str(quiet),
            ],check=True,capture_output=True,text=True,timeout=50)
            subprocess.run([
                "ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
                "-i",str(quiet),"-map","0:v:0","-map","0:a:0",
                "-c:v","copy",
                "-af",AUDIO_MASTERING_FILTER,"-ar",str(AUDIO_ENCODE_HZ),
                "-c:a","aac","-b:a","112k","-movflags","+faststart",
                str(corrected),
            ],check=True,capture_output=True,text=True,timeout=60)
            proof=verify_exact_encoded_master(
                "ffmpeg",corrected,
                sha256(corrected.read_bytes()).hexdigest(),
                22.0)
            self.assertGreater(
                proof["measured_final_encoded_integrated_lufs"],-20.5)
            self.assertLessEqual(
                proof["measured_final_encoded_oversampled_true_peak_dbtp"],-1)
            self.assertFalse(proof["youtube_upload_or_release_authorized"])


if __name__=="__main__":
    unittest.main()
