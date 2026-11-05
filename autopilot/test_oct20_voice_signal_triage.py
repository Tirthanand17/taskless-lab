"""Real PCM anomaly checks vs repeated square waves and clipped/silent WAV.

These are AUDIO QUALITY TECHNICAL negatives, never human speech positives.
"""
from array import array
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import wave
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.oct20_voice_signal_triage import (
    inspect_oct20_wav_signal_anomalies,
)


def write_fixture(target:Path,scenario:str,seconds:int=8):
    with wave.open(str(target),"wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        for block_index in range(4*seconds):
            if scenario=="repeat":
                amplitude=7200
                samples=array("h",(amplitude if (i//80)%2 else -amplitude
                                   for i in range(4000)))
            elif scenario=="changing":
                amplitude=4000+block_index*111
                samples=array("h",(amplitude if (i//80)%2 else -amplitude
                                   for i in range(4000)))
            elif scenario=="clipped":
                samples=array("h",(32767 if i%5==0 else
                                  (7200 if i%2 else -7200)
                                   for i in range(4000)))
            elif scenario=="mostly_silent":
                samples=array("h",((12500 if i%2 else -12500)
                                   if block_index<2 else 0
                                   for i in range(4000)))
            else:
                raise ValueError("Unsupported fixture")
            if sys.byteorder!="little":
                samples.byteswap()
            wav.writeframesraw(samples.tobytes())


class ActualOct20PCMAnomalyTests(unittest.TestCase):
    def test_perfectly_repeated_active_square_wave_is_held(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"repeated.wav"
            write_fixture(path,"repeat")
            result=inspect_oct20_wav_signal_anomalies(path)
            self.assertFalse(result["technical_anomaly_screen_passed"])
            self.assertIn("REPEATED_IDENTICAL_ACTIVE_PCM_BLOCKS",
                          result["technical_signal_holds"])
            self.assertEqual(result["max_repeated_active_block_count"],32)
            self.assertEqual(result["repeated_active_block_fraction"],1.0)
            self.assertEqual(result["inspected_pcm_quartersecond_blocks"],32)
            self.assertFalse(result["natural_human_voice_verified"])
            self.assertFalse(result["youtube_upload_authorized"])

    def test_varying_synthetic_square_wave_passes_signal_only_never_speech(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"changing.wav"
            write_fixture(path,"changing")
            result=inspect_oct20_wav_signal_anomalies(path)
            self.assertTrue(result["technical_anomaly_screen_passed"])
            self.assertEqual(result["technical_signal_holds"],())
            self.assertEqual(result["max_repeated_active_block_count"],1)
            for field in (
                "waveform_verified_as_spoken_language",
                "natural_human_voice_verified",
                "commercial_voice_rights_verified",
                "transcript_acoustic_alignment_verified",
                "ready_for_media_mux","youtube_upload_authorized",
                "youtube_publish_authorized",
            ):
                self.assertFalse(result[field])

    def test_true_full_scale_clipping_is_flagged_not_naturalness_judgment(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"clipped.wav"
            write_fixture(path,"clipped")
            result=inspect_oct20_wav_signal_anomalies(path)
            self.assertFalse(result["technical_anomaly_screen_passed"])
            self.assertIn("EXCESSIVE_FULL_SCALE_CLIPPING",
                          result["technical_signal_holds"])
            self.assertGreaterEqual(result["clipped_pcm_sample_fraction"],.19)

    def test_90_plus_percent_empty_blocks_flagged(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"mostly_silent.wav"
            write_fixture(path,"mostly_silent")
            result=inspect_oct20_wav_signal_anomalies(path)
            self.assertFalse(result["technical_anomaly_screen_passed"])
            self.assertIn("MOSTLY_SILENT_PCM",
                          result["technical_signal_holds"])
            self.assertGreater(result["near_silent_block_fraction"],.90)

    def test_refuse_symlink_or_wrong_extension_without_leaking_path(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            path=root/"original.wav"
            write_fixture(path,"changing")
            alias=root/"symbolic.wav"
            try:
                alias.symlink_to(path)
            except OSError:
                self.skipTest("Symlinks unavailable")
            for bad in (alias,root/"missing.wav",root/"fake.mp3"):
                with self.subTest(file=bad.name),self.assertRaises(WorkflowError):
                    inspect_oct20_wav_signal_anomalies(bad)

    def test_corrupt_bounded_wav_or_non_wav_bytes_are_rejected(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            for name,data in (
                ("bad.wav",b"RIFF"+b"\x00"*48),
                ("empty.wav",b""),
                ("noise.wav",b"NOT A WAV"*30),
            ):
                path=root/name
                path.write_bytes(data)
                with self.subTest(file=name),self.assertRaises(WorkflowError):
                    inspect_oct20_wav_signal_anomalies(path)

    def test_real_wav_metadata_hash_and_rms_only_never_claim_speech(self):
        from hashlib import sha256
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"changing.wav"
            write_fixture(path,"changing")
            report=inspect_oct20_wav_signal_anomalies(path)
            self.assertEqual(report["wav_sha256"],sha256(path.read_bytes()).hexdigest())
            self.assertEqual(report["duration_seconds"],8.0)
            self.assertEqual(report["sample_rate"],16000)
            self.assertEqual(report["pcm_channels"],1)
            self.assertEqual(report["external_network_calls"],0)
            self.assertEqual(report["monthly_recurring_infrastructure_inr"],0)


if __name__=="__main__":
    unittest.main()
