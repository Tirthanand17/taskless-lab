"""Actual mechanical short-scene WAV time audit, never final voice approval."""
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
import shutil
import struct
import unittest
import wave

from autopilot.agent_org import WorkflowError
from autopilot.oct20_mechanical_scene_pacing import (
    FRAME_RATE,VOICE_CONFIG,_decode_actual_espeak_stdout,
    measure_oct20_mechanical_scene_pacing,
    propose_scene_frame_retime,
)


class MechanicalSevenSceneReframeTests(unittest.TestCase):
    def test_expected_two_different_original_language_shorts(self):
        self.assertEqual(set(VOICE_CONFIG),{
            "fm_20261020_short_en","fm_20261020_short_hi",
        })
        self.assertEqual(VOICE_CONFIG["fm_20261020_short_en"],(
            "en-us",150,"en",42))
        self.assertEqual(VOICE_CONFIG["fm_20261020_short_hi"],(
            "hi",135,"hi",44))

    def test_original_frame_totals_remain_exact_short_duration(self):
        en=(4,6,6,6,7,7,6)
        hi=(5,6,6,7,7,7,6)
        observed_en=(5396,4483,4978,4661,5724,6179,4177)
        observed_hi=(5686,4542,5214,5810,6347,6381,5449)
        for expected,measured,total in (
            (en,observed_en,42),
            (hi,observed_hi,44),
        ):
            plans=tuple(x*FRAME_RATE for x in expected)
            result=propose_scene_frame_retime(
                planned_frames=plans,actual_observed_ms=measured)
            with self.subTest(expected=expected):
                self.assertEqual(sum(plans),total*24)
                self.assertEqual(sum(result),total*24)
                self.assertEqual(len(result),7)
                self.assertGreater(result[0],plans[0])
                self.assertTrue(any(result[i]<plans[i] for i in range(1,7)))
                self.assertTrue(all(
                    size*1000>=24*(t+250)
                    for size,t in zip(result,measured)
                ))
                self.assertNotEqual(result,plans)

    def test_overfull_genuinely_recorded_timing_must_fail_not_force_speed(self):
        original=(96,144,144,144,168,168,144)
        for claimed in (
            (120000,)*7,
            (42000,)*7,
            (8000,)*7,
        ):
            with self.subTest(claimed=claimed[0]),self.assertRaises(WorkflowError):
                propose_scene_frame_retime(
                    planned_frames=original,actual_observed_ms=claimed)

    def test_nonfinite_bad_timing_and_wrong_length_fail(self):
        valid=(96,144,144,144,168,168,144)
        base=(5396,4483,4978,4661,5724,6179,4177)
        for wrong in (
            base[:6],base+(3,), (True,)+base[1:],
            (0,)+base[1:],(1.1,)+base[1:],
        ):
            with self.subTest(wrong=wrong),self.assertRaises(WorkflowError):
                propose_scene_frame_retime(
                    planned_frames=valid,actual_observed_ms=wrong)
        for frame in (0,False,96.0):
            with self.subTest(frame=frame),self.assertRaises(WorkflowError):
                propose_scene_frame_retime(
                    planned_frames=(frame,)+valid[1:],
                    actual_observed_ms=base)

    def test_retiming_exactly_reproducible_never_changes_script(self):
        p=(120,144,144,168,168,168,144)
        d=(5686,4542,5214,5810,6347,6381,5449)
        one=propose_scene_frame_retime(planned_frames=p,actual_observed_ms=d)
        two=propose_scene_frame_retime(planned_frames=p,actual_observed_ms=d)
        self.assertEqual(one,two)
        self.assertEqual(sum(one),1056)

    def test_checked_in_actual_14_scene_benchmark_evidence_is_consistent(self):
        import json
        root=Path(__file__).resolve().parents[1]
        record=json.loads((root/"state/production/"
            "oct20_rejected_mechanical_scene_pacing_2026_10_19.json"
        ).read_text(encoding="utf-8"))
        self.assertEqual(record["status"],
                         "REJECTED_MECHANICAL_ESPEAK_SCENE_PACING_EXPERIMENT_ONLY")
        self.assertEqual(record["video_fps"],24)
        self.assertEqual(record["breath_pause_allowance_ms_per_scene"],250)
        self.assertFalse(record["normal_voice_quality_accepted"])
        self.assertFalse(record["automated_publishing_authorized"])
        self.assertFalse(record["shorts_completed"])
        self.assertEqual(record["external_network_calls"],0)
        self.assertEqual(record["monthly_recurring_infrastructure_inr"],0)
        self.assertEqual(len(record["episodes"]),2)
        for entry in record["episodes"]:
            with self.subTest(episode=entry["episode_id"]):
                original=tuple(s*24 for s in entry["plan"])
                observed=tuple(entry["observed"])
                recommended=propose_scene_frame_retime(
                    planned_frames=original,actual_observed_ms=observed)
                self.assertEqual(tuple(entry["recommended_visual_frames"]),
                                 recommended)
                starts=[0]
                for frames in recommended:
                    starts.append(starts[-1]+frames)
                self.assertEqual(entry["recommended_cuts_frames"],starts)
                self.assertEqual(entry["mechanical_total_ms"],sum(observed))
                self.assertEqual(entry["mechanical_total_script_slack_ms"],
                                 sum(entry["plan"])*1000-sum(observed))
                self.assertEqual(sum(entry["scenes_over_target"]),1)

    def test_invalid_audio_bytes_and_fake_header_are_not_accepted(self):
        for data in (
            b"",b"garbage" * 20,
            b"RIFF"+b"x"*100,
            b"not RIFF"+b"\x00"*200,
        ):
            with self.subTest(kind=data[:15]),self.assertRaises(WorkflowError):
                _decode_actual_espeak_stdout(data)

    def test_decode_bounded_real_sample_data_not_unseekable_fake_riff_length(self):
        # A 250-ms PCM16 mono WAV with a STREAMING placeholder RIFF length,
        # such as eSpeak --stdout. Header reports huge bogus size. Reader
        # should instead count 5512 or 5513 ACTUAL stored sample frames.
        stream=BytesIO()
        with wave.open(stream,"wb") as writer:
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(22050)
            writer.writeframes(b"\x01\x00"*6000)
        data=bytearray(stream.getvalue())
        struct.pack_into("<I",data,4,0x7ffff024)
        struct.pack_into("<I",data,40,0x7ffff000)
        frames,rate=_decode_actual_espeak_stdout(bytes(data))
        self.assertEqual(frames,6000)
        self.assertEqual(rate,22050)
        self.assertNotEqual(frames,0x7ffff000//2)

    def test_absent_engine_must_refuse_without_fallback_download(self):
        with patch("autopilot.oct20_mechanical_scene_pacing.shutil.which",
                   return_value=None):
            with self.assertRaises(WorkflowError):
                measure_oct20_mechanical_scene_pacing(
                    episode_id="fm_20261020_short_en")

    def test_long_480_or_unknown_episode_cannot_be_processed(self):
        for episode in ("fm_20261020_long_hi","csv_tutorial_short_en",
                        "fake",None,True):
            with self.subTest(episode=str(episode)),self.assertRaises(WorkflowError):
                measure_oct20_mechanical_scene_pacing(episode_id=episode)

    @unittest.skipUnless(shutil.which("espeak"),
                         "Already installed offline eSpeak binary required")
    def test_actual_all_fourteen_original_scenes_without_download(self):
        for episode in VOICE_CONFIG:
            receipt=measure_oct20_mechanical_scene_pacing(episode_id=episode)
            with self.subTest(episode=episode):
                self.assertEqual(
                    receipt["status"],
                    "ACTUAL_SEVEN_SCENE_ESPEAK_MECHANICAL_BASELINE_REJECTED",
                )
                self.assertEqual(len(receipt["mechanical_scene_ms"]),7)
                self.assertEqual(len(receipt["script_scene_sha256s"]),7)
                self.assertEqual(len(receipt["actual_audio_wave_sha256s"]),7)
                self.assertEqual(receipt["mechanical_scene_overrun_count"],1)
                self.assertTrue(
                    receipt["measured_from_actual_pcm_bytes_not_header_sentinel"])
                self.assertEqual(
                    sum(receipt["proposed_silent_visual_scene_frames"]),
                    receipt["planned_video_frames"],
                )
                self.assertGreater(receipt["opening_scene_overrun_ms"],0)
                self.assertFalse(receipt["proposed_actual_narration_timing_verified"])
                self.assertFalse(receipt["natural_sounding_voice_verified"])
                self.assertFalse(receipt["commercial_voice_rights_verified"])
                self.assertFalse(receipt["ready_for_mux"])
                self.assertFalse(receipt["youtube_upload_authorized"])
                self.assertFalse(receipt["youtube_publishing_authorized"])
                self.assertEqual(receipt["audio_files_persisted"],0)
                self.assertEqual(receipt["external_network_calls"],0)
                self.assertEqual(receipt["new_models_downloaded"],0)


if __name__=="__main__":
    unittest.main()
