"""A5 original narration beat-level audio gates: fully synthetic offline tests."""
from __future__ import annotations

from array import array
import math
from pathlib import Path
import tempfile
import unittest
import wave

from scripts.branch3_a5_narration_energy_qa import (
    NarrationEnergyDenied, audit_original_narration,
)

RATE=48_000
BEATS=[
    {"start_s":0,"end_s":2},
    {"start_s":2,"end_s":5},
    {"start_s":5,"end_s":8},
]


def fixture_wave(path:Path,*,mute_beat:int|None=None,
                 clip_beat:int|None=None,rate:int=RATE,
                 channels:int=1)->None:
    pcm=array("h")
    for i,beat in enumerate(BEATS):
        for n in range((beat["end_s"]-beat["start_s"])*rate):
            # A 1.25s fake "spoken" tone per beat, followed by a quiet
            # procedural ambience. Not real audio, language or voice.
            active=n<int(rate*1.25) and i!=mute_beat
            amp=2100 if active else 41
            x=round(amp*math.sin(2*math.pi*175*n/rate))
            if i==clip_beat and n==17:
                x=32767
            for _ in range(channels):
                pcm.append(x)
    with wave.open(str(path),"wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())


class OriginalNarrationEnergyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/"synthetic-original.wav"
        fixture_wave(self.path)

    def test_all_three_strict_beats_have_energy_but_no_claim_of_speech(self):
        report=audit_original_narration(self.path,beats=BEATS,duration=8)
        self.assertEqual(report["beat_count"],3)
        self.assertEqual(len(report["per_beat"]),3)
        self.assertTrue(report["all_beats_have_nontrivial_sound_energy"])
        self.assertTrue(report["no_near_full_scale_pcm_clipping"])
        self.assertTrue(report["voice_energy_is_not_speech_or_word_accuracy_proof"])
        for i,item in enumerate(report["per_beat"]):
            self.assertEqual(item["beat_index"],i)
            self.assertGreaterEqual(item["active_voice_proxy_windows"],3)
            self.assertGreater(item["max_quarter_second_rms"],600)
            self.assertFalse(item["caption_word_alignment_verified"])
        self.assertFalse(report["all_speech_approved_by_real_human"])
        self.assertFalse(report["commercial_soundtrack_and_voice_rights_approved"])
        self.assertFalse(report["youtube_upload_authorized"])
        self.assertFalse(report["youtube_publish_authorized"])

    def test_mute_single_middle_beat_must_fail_not_just_first_audio_window(self):
        fixture_wave(self.path,mute_beat=1)
        with self.assertRaisesRegex(NarrationEnergyDenied,
                                    "SILENT_OR_INAUDIBLE_SCENE_1"):
            audit_original_narration(self.path,beats=BEATS,duration=8)

    def test_near_max_pcm_clipping_is_rejected_in_any_beat(self):
        fixture_wave(self.path,clip_beat=2)
        with self.assertRaisesRegex(NarrationEnergyDenied,
                                    "POSSIBLE_WAV_CLIPPING_2"):
            audit_original_narration(self.path,beats=BEATS,duration=8)

    def test_wrong_sample_rate_or_channel_or_truncated_beat_rejected(self):
        for rate,channels in ((44100,1),(48000,2)):
            fixture_wave(self.path,rate=rate,channels=channels)
            with self.subTest(rate=rate,channels=channels),self.assertRaises(
                NarrationEnergyDenied
            ):
                audit_original_narration(self.path,beats=BEATS,duration=8)
        fixture_wave(self.path)
        with self.path.open("ab") as f:
            f.write(b"EXTRA")
        # Extra bytes after a valid PCM WAV RIFF need not be rejected.
        # But changing the expected timeline always must be.
        with self.assertRaises(NarrationEnergyDenied):
            audit_original_narration(self.path,beats=BEATS,duration=9)

    def test_malformed_beat_clock_and_file_symlink_rejected(self):
        for beats in (
            [],[{"start_s":0,"end_s":2},{"start_s":3,"end_s":8}],
            [{"start_s":1,"end_s":8}],
            [*BEATS,{"start_s":8,"end_s":10}],
            [{**BEATS[0],"start_s":True},*BEATS[1:]],
        ):
            with self.subTest(beats=beats),self.assertRaises(
                NarrationEnergyDenied
            ):
                audit_original_narration(self.path,beats=beats,duration=8)
        symlink=Path(self.temp.name)/"fake.wav"
        symlink.symlink_to(self.path)
        with self.assertRaises(NarrationEnergyDenied):
            audit_original_narration(symlink,beats=BEATS,duration=8)

    def test_corrupt_wav_cannot_be_used_for_release(self):
        self.path.write_bytes(b"NOT_AN_AUDIO_WAVE"*10000)
        with self.assertRaises(NarrationEnergyDenied):
            audit_original_narration(self.path,beats=BEATS,duration=8)


if __name__=="__main__":
    unittest.main()
