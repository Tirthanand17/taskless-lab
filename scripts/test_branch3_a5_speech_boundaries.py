"""A5 original acoustic draft captions: synthetic, source-free adversarial tests.

No prerecorded voice assets, no external music, video, API, or owner release.
"""
from __future__ import annotations

from array import array
from pathlib import Path
import math
import tempfile
import unittest
import wave

from scripts.branch3_a5_speech_boundaries import (
    RATE, FRAME, SpeechBoundaryDenied,
    measure_unmixed_speech_activity, audit_mixed_speech_caption_bounds,
    bed_sample_without_speech, parse_srt_intervals,
)

BEATS=[
    {"start_s":0,"end_s":2},
    {"start_s":2,"end_s":5},
    {"start_s":5,"end_s":8}
]
VOICE_TIMES=((.20,1.50),(2.12,3.80),(5.10,7.10))
SRT="""1
00:00:00,200 --> 00:00:01,500
Original test voice.

2
00:00:02,120 --> 00:00:03,800
Synthetic scene.

3
00:00:05,100 --> 00:00:07,100
Do not publish.
"""


def synthetic_wave(
    path:Path,*,mute_index:int|None=None,amplitude:int=4_000,
    rate:int=RATE,from_bed:bool=True
)->None:
    pcm=array("h")
    for sample in range(rate*8):
        t=sample/rate
        beat=next(i for i,b in enumerate(BEATS)
                  if b["start_s"]<=t<b["end_s"])
        start,end=VOICE_TIMES[beat]
        voice=round(amplitude*math.sin(2*math.pi*175*t)) if (
            start<=t<end and beat!=mute_index
        ) else 0
        procedural=bed_sample_without_speech(
            sample,BEATS[beat]["start_s"]
        ) if from_bed and rate==RATE else 0
        pcm.append(max(-32768,min(32767,voice+procedural)))
    with wave.open(str(path),"wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(pcm.tobytes())


class OriginalAcousticBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.wav=Path(self.temp.name)/"totally-synthetic-original.wav"
        synthetic_wave(self.wav)

    def test_raw_pcm_activity_discards_wav_trailing_silence(self):
        pcm=array("h",[0])*(2*RATE)
        for i in range(int(.2*RATE),int(1.5*RATE)):
            pcm[i]=round(3500*math.sin(2*math.pi*175*i/RATE))
        a,b=measure_unmixed_speech_activity(pcm)
        self.assertAlmostEqual(a,.2,delta=.021)
        self.assertAlmostEqual(b,1.5,delta=.021)
        self.assertGreater(2.0-b,.4)
        # Existing draft was based on full WAV duration, not active speech.
        # This regression catches that >300ms trailing cue issue.

    def test_all_beats_original_mixed_audio_matches_real_speech_activity(self):
        d=audit_mixed_speech_caption_bounds(
            self.wav,beats=BEATS,duration=8,srt=SRT
        )
        self.assertEqual(d["beat_count"],3)
        self.assertTrue(d["all_scenes_recovered_speech_like_activity_above_procedural_bed"])
        self.assertTrue(d["draft_caption_onset_offset_within_140ms_of_detected_activity"])
        self.assertFalse(d["individual_spoken_words_verified"])
        self.assertFalse(d["phoneme_forced_alignment_or_asr_performed"])
        self.assertFalse(d["commercial_speech_rights_verified"])
        self.assertFalse(d["human_edit_and_caption_approval_complete"])
        self.assertFalse(d["youtube_upload_authorized"])
        self.assertFalse(d["youtube_publish_authorized"])
        for i,beat in enumerate(d["per_beat"]):
            self.assertEqual(beat["beat_index"],i)
            self.assertGreater(beat["active_speech_like_windows"],10)
            self.assertGreater(beat["max_recovered_speech_rms"],1000)
            self.assertAlmostEqual(
                beat["signal_end_s"],VOICE_TIMES[i][1],delta=.021
            )
            self.assertFalse(beat["spoken_words_or_phonemes_forced_aligned"])

    def test_bed_only_with_original_chime_cannot_masquerade_as_voice(self):
        synthetic_wave(self.wav,mute_index=1)
        with self.assertRaisesRegex(
            SpeechBoundaryDenied,
            "NO_TTS_LIKE_SIGNAL_AFTER_BED_SUBTRACTION_1"
        ):
            audit_mixed_speech_caption_bounds(
                self.wav,beats=BEATS,duration=8,srt=SRT
            )
        synthetic_wave(self.wav,amplitude=0)
        with self.assertRaisesRegex(
            SpeechBoundaryDenied,
            "NO_TTS_LIKE_SIGNAL_AFTER_BED_SUBTRACTION_0"
        ):
            audit_mixed_speech_caption_bounds(
                self.wav,beats=BEATS,duration=8,srt=SRT
            )

    def test_draft_caption_end_after_real_speech_fails(self):
        invalid=SRT.replace(
            "00:00:01,500","00:00:01,820"
        )
        with self.assertRaisesRegex(
            SpeechBoundaryDenied,"CAPTION_END_NOT_ANCHORED_TO_SPEECH_0"
        ):
            audit_mixed_speech_caption_bounds(
                self.wav,beats=BEATS,duration=8,srt=invalid
            )

    def test_caption_early_or_delayed_start_fails(self):
        for val in ("00:00:00,000","00:00:00,550"):
            changed=SRT.replace("00:00:00,200",val)
            with self.subTest(start=val),self.assertRaisesRegex(
                SpeechBoundaryDenied,"CAPTION_START_NOT_ANCHORED_TO_SPEECH_0"
            ):
                audit_mixed_speech_caption_bounds(
                    self.wav,beats=BEATS,duration=8,srt=changed
                )

    def test_srt_no_overlap_wrong_clock_no_extra_cue(self):
        self.assertEqual(len(parse_srt_intervals(SRT)),3)
        for bad in (
            "",
            SRT.replace("00:00:01,500","00:00:02,800"),
            SRT.replace("00:00:00,200","99:99:99,999"),
            SRT.replace("00:00:02,120","00:00:03,950"),
            SRT.replace("2\n00:00:02,120","4\n00:00:02,120"),
            SRT.replace(" --> "," ---> ",1),
        ):
            with self.subTest(bad=bad[:30]),self.assertRaises(SpeechBoundaryDenied):
                parse_srt_intervals(bad)

    def test_dry_speech_energy_rejects_one_click_and_silence(self):
        silent=array("h",[0])*(2*RATE)
        with self.assertRaisesRegex(
            SpeechBoundaryDenied,"NO_MEANINGFUL_DRY_SPEECH_ACTIVITY"
        ):
            measure_unmixed_speech_activity(silent)
        for i in range(100,100+FRAME):
            silent[i]=3100
        with self.assertRaises(SpeechBoundaryDenied):
            measure_unmixed_speech_activity(silent)

    def test_corrupt_wrong_format_and_bad_beat_clock_fail(self):
        for malformed in (
            [],
            [{**BEATS[0],"start_s":1},*BEATS[1:]],
            [BEATS[0],{**BEATS[1],"start_s":3},BEATS[2]],
            [BEATS[0],BEATS[1]],
        ):
            with self.subTest(malformed=malformed),self.assertRaises(
                SpeechBoundaryDenied
            ):
                audit_mixed_speech_caption_bounds(
                    self.wav,beats=malformed,duration=8,srt=SRT
                )
        symlink=Path(self.temp.name)/"faked.wav"
        symlink.symlink_to(self.wav)
        with self.assertRaises(SpeechBoundaryDenied):
            audit_mixed_speech_caption_bounds(
                symlink,beats=BEATS,duration=8,srt=SRT
            )
        self.wav.write_bytes(b"CORRUPT WAVE"*50_000)
        with self.assertRaises(SpeechBoundaryDenied):
            audit_mixed_speech_caption_bounds(
                self.wav,beats=BEATS,duration=8,srt=SRT
            )


if __name__=="__main__":
    unittest.main()
