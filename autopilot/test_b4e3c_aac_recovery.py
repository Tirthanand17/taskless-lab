"""B4e3c: unsafe encoded AAC can be *measured* for repair, not approved.

The before/after gate is intentionally asymmetric. Before correction the
lossy AAC can exceed 0 dBTP, which must be read without incorrectly declaring
the media acceptable. After correction it MUST be checked with the existing
independent strict validator and still be rejected unless within -20..-12
LUFS and <= -1.5 dBTP. No YouTube, real owner approval or external audio.
"""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch,Mock
import shutil

from autopilot.full_topic_narrated_pack import (
    TopicRenderError,_encoded_audio_loudness,
    _repair_if_encoded_audio_out_of_band,
)
from autopilot.independent_av_review import ReviewerError

def _ffmpeg_json(lufs="-16.7",peak="0.17",lra="2.1"):
    return ('[Parsed_loudnorm_0 @ 0x9]\n'
            '{\n  "input_i" : "'+lufs+'",\n'
            '  "input_tp" : "'+peak+'",\n'
            '  "input_lra" : "'+lra+'",\n'
            '  "input_thresh" : "-26.7",\n'
            '  "output_i" : "-16.0",\n'
            '  "output_tp" : "-3.8",\n'
            '  "output_lra" : "2.1",\n'
            '  "output_thresh" : "-26.0",\n'
            '  "normalization_type" : "dynamic",\n'
            '  "target_offset" : "0.0"\n}\n')


class RealEncodedAudioPreflightAsymmetricGateTests(unittest.TestCase):
    def _file(self,root):
        path=Path(root)/"actual-encoded-audio.mp4"
        path.write_bytes(b"real-data-placeholder-for-test-only"*2400)
        return path

    def test_unsafe_encoded_true_peak_is_measurable_not_approved(self):
        with tempfile.TemporaryDirectory() as root:
            mp4=self._file(root)
            with patch("subprocess.run",return_value=Mock(stderr=_ffmpeg_json())):
                raw=_encoded_audio_loudness(mp4)
                self.assertEqual(raw["true_peak_dbtp"],0.17)
                self.assertEqual(raw["integrated_lufs"],-16.7)
                self.assertFalse(raw["typical_online_video_target_diagnostic"])
                self.assertTrue(raw["raw_over_ceiling_only_for_repair"])
                with self.assertRaises(ReviewerError):
                    _encoded_audio_loudness(mp4,strict=True)

    def test_actual_safe_measurement_and_independent_strict_agree(self):
        with tempfile.TemporaryDirectory() as root:
            mp4=self._file(root)
            with patch("subprocess.run",return_value=Mock(stderr=_ffmpeg_json("-16.2","-3.2"))):
                raw=_encoded_audio_loudness(mp4)
                strict=_encoded_audio_loudness(mp4,strict=True)
                self.assertTrue(raw["typical_online_video_target_diagnostic"])
                self.assertFalse(raw["raw_over_ceiling_only_for_repair"])
                self.assertTrue(strict["typical_online_video_target_diagnostic"])
                self.assertEqual(strict["true_peak_dbtp"],-3.2)

    def test_forged_bad_silent_or_nonfinite_observations_are_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            mp4=self._file(root)
            for loud,peak,lra in [
                ("-inf","0.1","2.1"),("-42","0.0","2.1"),
                ("-16.3","inf","2.1"),("-16.3","6.1","2.1"),
                ("-16.3","0.0","-1"),("-6.0","-3.0","1.0"),
            ]:
                with self.subTest(loud=loud,peak=peak,lra=lra):
                    with patch("subprocess.run",return_value=Mock(
                        stderr=_ffmpeg_json(loud,peak,lra)
                    )),self.assertRaises(TopicRenderError):
                        _encoded_audio_loudness(mp4)
            with patch("subprocess.run",return_value=Mock(stderr="not a valid FFmpeg log")),self.assertRaises(TopicRenderError):
                _encoded_audio_loudness(mp4)

    def test_preexisting_file_must_be_regular_and_local(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/"no.mp4"
            with self.assertRaises(TopicRenderError):
                _encoded_audio_loudness(p)
            p.symlink_to(Path(root)/"invalid")
            with self.assertRaises(TopicRenderError):
                _encoded_audio_loudness(p)

    def test_one_actual_audio_only_correction_rechecks_strict_before_replace(self):
        with tempfile.TemporaryDirectory() as root:
            original=self._file(root)
            data=original.read_bytes()
            unsafe={"integrated_lufs":-16.7,
                    "true_peak_dbtp":.17,
                    "typical_online_video_target_diagnostic":False}
            safe={"integrated_lufs":-16.1,
                  "true_peak_dbtp":-3.2,
                  "typical_online_video_target_diagnostic":True}
            def fake_ffmpeg(cmd,*,timeout):
                self.assertIn("-c:v",cmd)
                self.assertEqual(cmd[cmd.index("-c:v")+1],"copy")
                self.assertIn("-map",cmd)
                shutil.copyfile(original,Path(cmd[-1]))
            with patch("autopilot.full_topic_narrated_pack._encoded_audio_loudness",
                       side_effect=[unsafe,safe,safe]) as measure,patch(
                       "autopilot.full_topic_narrated_pack.run",side_effect=fake_ffmpeg
                       ) as render:
                result=_repair_if_encoded_audio_out_of_band(original)
                self.assertTrue(result["aac_normalized_after_encode"])
                self.assertEqual(result["aac_loudness_repair_passes"],1)
                self.assertEqual(original.read_bytes(),data)
                self.assertEqual(measure.call_count,3)
                self.assertEqual(measure.call_args_list[1].kwargs,{})
                self.assertEqual(measure.call_args_list[2].kwargs,{"strict":True})
                self.assertEqual(render.call_count,1)

    def test_unsafe_repair_result_does_not_overwrite_original(self):
        with tempfile.TemporaryDirectory() as root:
            original=self._file(root)
            first=original.read_bytes()
            unsafe={"integrated_lufs":-16.3,
                    "true_peak_dbtp":.17,
                    "typical_online_video_target_diagnostic":False}
            still_unsafe={"integrated_lufs":-16.8,
                          "true_peak_dbtp":-0.3,
                          "typical_online_video_target_diagnostic":False}
            def fake_ffmpeg(cmd,*,timeout):
                Path(cmd[-1]).write_bytes(b"other audio"*10000)
            with patch("autopilot.full_topic_narrated_pack._encoded_audio_loudness",
                       side_effect=[unsafe,still_unsafe]) as observer,patch(
                       "autopilot.full_topic_narrated_pack.run",side_effect=fake_ffmpeg):
                with self.assertRaises(TopicRenderError):
                    _repair_if_encoded_audio_out_of_band(original)
                self.assertEqual(original.read_bytes(),first)
                self.assertEqual(observer.call_args_list[1].kwargs,{})

    def test_at_most_two_real_audio_only_corrections_before_strict_gate(self):
        with tempfile.TemporaryDirectory() as root:
            original=self._file(root)
            first=original.read_bytes()
            raw={"integrated_lufs":-16.0,"true_peak_dbtp":0.17,
                 "typical_online_video_target_diagnostic":False}
            still_hot={"integrated_lufs":-15.7,"true_peak_dbtp":-0.7,
                       "typical_online_video_target_diagnostic":False}
            good={"integrated_lufs":-18.5,"true_peak_dbtp":-3.5,
                  "typical_online_video_target_diagnostic":True}
            def fake_ffmpeg(cmd,*,timeout):
                self.assertIn("-c:v",cmd)
                self.assertEqual(cmd[cmd.index("-c:v")+1],"copy")
                Path(cmd[-1]).write_bytes(b"safe generated AAC proxy"*3600)
            with patch("autopilot.full_topic_narrated_pack._encoded_audio_loudness",
                       side_effect=[raw,still_hot,good]) as observe,patch(
                       "autopilot.full_topic_narrated_pack.run",
                       side_effect=fake_ffmpeg) as ffmpeg:
                result=_repair_if_encoded_audio_out_of_band(original)
                self.assertEqual(result["aac_loudness_repair_passes"],1)
                self.assertEqual(ffmpeg.call_count,2)
                self.assertEqual(observe.call_count,3)
                self.assertEqual(observe.call_args_list[-1].kwargs,{"strict":True})
                self.assertNotEqual(original.read_bytes(),first)
                self.assertTrue(original.read_bytes().startswith(b"safe generated AAC proxy"))

    def test_already_safe_aac_never_reencoded(self):
        with tempfile.TemporaryDirectory() as root:
            original=self._file(root)
            safe={"integrated_lufs":-17,
                  "true_peak_dbtp":-3,
                  "typical_online_video_target_diagnostic":True}
            with patch("autopilot.full_topic_narrated_pack._encoded_audio_loudness",
                       return_value=safe),patch(
                       "autopilot.full_topic_narrated_pack.run"
                       ) as render:
                result=_repair_if_encoded_audio_out_of_band(original)
                self.assertEqual(result["aac_loudness_repair_passes"],0)
                render.assert_not_called()

if __name__=="__main__":
    unittest.main()
