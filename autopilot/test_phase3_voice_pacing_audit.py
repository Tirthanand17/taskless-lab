"""Real full-duration PCM examples; signal checks do not verify speech."""
from array import array
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import math
import sys
import unittest
import wave

from autopilot.agent_org import WorkflowError
from autopilot.phase3_voice_pacing_audit import inspect_voice_pacing_candidate

RATE=16000
def samples(mode:str)->bytes:
    a=array("h")
    for i in range(RATE):
        phase=2*math.pi*i/RATE
        if mode=="complex":
            raw=0.10*math.sin(180*phase)+.07*math.sin(420*phase)+.09*math.sin(950*phase)
        elif mode=="clipped":
            raw=2.5*math.sin(220*phase)
        elif mode=="dc":
            raw=.24+.08*math.sin(220*phase)
        elif mode=="quiet":
            raw=0.0
        else:
            raise AssertionError("unknown synthetic test")
        a.append(max(-32768,min(32767,round(raw*32767))))
    if sys.byteorder!="little":a.byteswap()
    return a.tobytes()

class PacingAuditRealPCMTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ordinary=samples("complex")
        cls.silent=samples("quiet")
        cls.clipped=samples("clipped")
        cls.dc=samples("dc")

    def setUp(self):
        tmp=TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir=Path(tmp.name)
        self.path=self.dir/"untrusted.wav"

    def write(self,profile:list[tuple[str,int]]) -> str:
        frames={"complex":self.ordinary,"quiet":self.silent,
                "clipped":self.clipped,"dc":self.dc}
        with wave.open(str(self.path),"wb") as writer:
            writer.setnchannels(1);writer.setsampwidth(2);writer.setframerate(RATE)
            for name,amount in profile:
                for _ in range(amount):
                    writer.writeframes(frames[name])
        return sha256(self.path.read_bytes()).hexdigest()

    def check(self,digest:str,*,episode="csv_tutorial_short_en"):
        return inspect_voice_pacing_candidate(
            wav_path=self.path,episode_id=episode,
            expected_sha256=digest)

    def test_basic_complex_signal_passes_but_no_language_or_rights(self):
        sha=self.write([("complex",42)])
        report=self.check(sha)
        self.assertEqual(report["window_seconds_sampled"],42)
        self.assertEqual(report["quiet_sampled_seconds"],0)
        self.assertEqual(report["status"],"PACING_AND_WAVEFORM_TECHNICAL_SCREEN_ONLY_UNVERIFIED")
        for field in ("natural_human_speech_verified",
                      "correct_declared_language_or_narrator_verified",
                      "word_audio_alignment_verified",
                      "copyright_and_voice_rights_verified",
                      "independent_professional_audio_review_verified",
                      "ready_for_mux_or_upload","publishing_authorized"):
            self.assertFalse(report[field])
        self.assertEqual(report["files_written"],0)
        self.assertEqual(report["network_calls"],0)

    def test_normal_brief_pause_is_not_automatically_rejected(self):
        sha=self.write([("complex",13),("quiet",2),("complex",27)])
        r=self.check(sha)
        self.assertEqual(r["quiet_sampled_seconds"],2)
        self.assertEqual(r["longest_consecutive_quiet_sampled_seconds"],2)

    def test_long_middle_pause_is_rejected(self):
        sha=self.write([("complex",12),("quiet",8),("complex",22)])
        with self.assertRaisesRegex(WorkflowError,"pauses"):
            self.check(sha)

    def test_dead_intro_and_dead_tail_are_rejected(self):
        for label,contents in (
            ("intro",[("quiet",5),("complex",37)]),
            ("tail",[("complex",35),("quiet",7)]),
        ):
            with self.subTest(label=label):
                sha=self.write(contents)
                with self.assertRaisesRegex(WorkflowError,"pauses"):
                    self.check(sha)

    def test_hard_clipping_rejected(self):
        sha=self.write([("clipped",42)])
        with self.assertRaisesRegex(WorkflowError,"clipped"):
            self.check(sha)

    def test_extreme_dc_bias_rejected(self):
        sha=self.write([("dc",42)])
        with self.assertRaisesRegex(WorkflowError,"DC offset"):
            self.check(sha)

    def test_damaged_byte_hash_symlink_and_unknown_episode_rejected(self):
        sha=self.write([("complex",42)])
        with self.assertRaisesRegex(WorkflowError,"changed"):
            self.check("0"*64)
        alias=self.dir/"alias.wav"
        alias.symlink_to(self.path)
        with self.assertRaises(WorkflowError):
            inspect_voice_pacing_candidate(
                wav_path=alias,episode_id="csv_tutorial_short_en",
                expected_sha256=sha)
        with self.assertRaises(WorkflowError):
            self.check(sha,episode="unknown")

    def test_short_wav_cannot_claim_complete_episode(self):
        sha=self.write([("complex",2)])
        with self.assertRaisesRegex(WorkflowError,"format or duration"):
            self.check(sha)

    def test_long_form_432s_complete_signal_accepted_as_only_pcm(self):
        sha=self.write([("complex",432)])
        r=self.check(sha,episode="csv_tutorial_long_hi")
        self.assertEqual(r["window_seconds_sampled"],432)
        self.assertFalse(r["natural_human_speech_verified"])

    def test_long_form_silent_intro_rejected(self):
        sha=self.write([("quiet",12),("complex",420)])
        with self.assertRaisesRegex(WorkflowError,"pauses"):
            self.check(sha,episode="csv_tutorial_long_hi")

if __name__=="__main__":
    unittest.main()
