"""Real WAV waveform regression for obvious tones and silence, not ASR."""
from array import array
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import math
import sys
import unittest
import wave

from autopilot.agent_org import WorkflowError
from autopilot.phase3_voice_signal_screen import inspect_nonplaceholder_audio_candidate

RATE=16000
LENGTH=42

def wav_from_seconds(path:Path, second_chunks:list[bytes]) -> str:
    with wave.open(str(path),"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(RATE)
        for chunk in second_chunks:
            w.writeframes(chunk)
    return sha256(path.read_bytes()).hexdigest()

def second_tone(freq:float=220, *, amplitude:float=.16)->bytes:
    values=array("h",(int(32767*amplitude*math.sin(2*math.pi*freq*i/RATE))
                     for i in range(RATE)))
    if sys.byteorder!="little": values.byteswap()
    return values.tobytes()

def second_complex()->bytes:
    frequencies=((170,.07),(360,.08),(750,.10),(1210,.08))
    values=array("h",(int(32767*sum(
        volume*math.sin(2*math.pi*freq*i/RATE)
        for freq,volume in frequencies)) for i in range(RATE)))
    if sys.byteorder!="little":values.byteswap()
    return values.tobytes()

class SourceWavSignalScreenTest(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"original.wav"

    def review(self, sha:str):
        return inspect_nonplaceholder_audio_candidate(
            wav_path=self.path,
            episode_id="csv_tutorial_short_en",
            expected_sha256=sha,
        )

    def test_continuous_sine_is_rejected_even_with_valid_loud_wav(self):
        # This is precisely the placeholder that passes basic PCM energy checks.
        s=wav_from_seconds(self.path,[second_tone()]*LENGTH)
        with self.assertRaisesRegex(WorkflowError,"pure tone"):
            self.review(s)

    def test_second_frequency_sine_still_rejected(self):
        chunks=[second_tone(330 if x%2 else 220) for x in range(LENGTH)]
        s=wav_from_seconds(self.path,chunks)
        with self.assertRaisesRegex(WorkflowError,"pure tone"):
            self.review(s)

    def test_mixed_harmonics_do_not_prove_speech(self):
        s=wav_from_seconds(self.path,[second_complex()]*LENGTH)
        result=self.review(s)
        self.assertEqual(result["status"],"OBVIOUS_AUDIO_PLACEHOLDER_NOT_DETECTED_UNVERIFIED")
        self.assertEqual(result["checked_pcm_windows"],5)
        self.assertEqual(result["near_silent_windows"],0)
        self.assertFalse(result["intelligible_speech_recognized"])
        self.assertFalse(result["human_voice_naturalness_verified"])
        self.assertFalse(result["voice_license_verified"])
        self.assertFalse(result["publishing_authorized"])

    def test_silence_most_of_episode_rejected(self):
        data=[second_complex()]*8+[bytes(RATE*2)]*34
        sha=wav_from_seconds(self.path,data)
        with self.assertRaisesRegex(WorkflowError,"silent"):
            self.review(sha)

    def test_stale_sha_rejected(self):
        sha=wav_from_seconds(self.path,[second_complex()]*LENGTH)
        with self.assertRaisesRegex(WorkflowError,"changed"):
            self.review("0"*64)
        self.assertNotEqual(sha,"0"*64)

    def test_symlink_file_does_not_pass(self):
        sha=wav_from_seconds(self.path,[second_complex()]*LENGTH)
        link=self.path.with_name("link.wav")
        link.symlink_to(self.path)
        with self.assertRaises(WorkflowError):
            inspect_nonplaceholder_audio_candidate(
                wav_path=link,episode_id="csv_tutorial_short_en",
                expected_sha256=sha)

    def test_wrong_length_and_missing_original_episode_rejected(self):
        sha=wav_from_seconds(self.path,[second_complex()]*3)
        with self.assertRaises(WorkflowError):
            self.review(sha)
        with self.assertRaises(WorkflowError):
            inspect_nonplaceholder_audio_candidate(
                wav_path=self.path,episode_id="not_original",
                expected_sha256=sha)

    def test_candidate_does_not_generate_other_files_or_call_services(self):
        sha=wav_from_seconds(self.path,[second_complex()]*LENGTH)
        before=self.path.read_bytes()
        report=self.review(sha)
        self.assertEqual(self.path.read_bytes(),before)
        self.assertEqual(list(self.path.parent.iterdir()),[self.path])
        self.assertEqual(report["network_calls"],0)
        self.assertFalse(report["ready_for_mux_or_upload"])

if __name__=="__main__":
    unittest.main()
