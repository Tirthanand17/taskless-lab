"""Offline tests: no Azure or Edge TTS calls, no network access."""
from array import array
from pathlib import Path
import json
import sys
import tempfile
import unittest
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "motion-v2"))
import natural_narration as n


class NaturalNarrationTests(unittest.TestCase):
    def test_empty_script_rejected(self):
        with self.assertRaises(n.NarrationError):
            n.sentences("   \n ")
    def test_paragraphs_and_punctuation(self):
        chunks=n.plan_segments("What if this really worked? Here is the example. "
                               "Now try changing the number. Do you see the result?", "curious-short")
        self.assertEqual(" ".join(c["text"] for c in chunks),
                         "What if this really worked? Here is the example. "
                         "Now try changing the number. Do you see the result?")
        self.assertEqual(chunks[-1]["pause_ms"],0)
    def test_long_episodes_are_chunked(self):
        text=("Imagine a new approach to data. " * 45).strip()
        chunks=n.plan_segments(text,"warm-explainer")
        self.assertGreater(len(chunks),5)
        self.assertTrue(all(c["words"] <= 85 for c in chunks))
    def test_pacing_variation_is_bounded(self):
        text=("What happens next? " * 32)
        chunks=n.plan_segments(text,"curious-short")
        rates={c["rate_percent"] for c in chunks}
        self.assertGreater(len(rates),1)
        self.assertTrue(all(-8 <= x <= 4 for x in rates))
    def test_question_pause(self):
        chunks=n.plan_segments("Can it work? " + "This is the answer. "*8,"calm-tutorial")
        self.assertGreaterEqual(chunks[0]["pause_ms"],350)
    def test_last_chunk_never_has_trailing_silence(self):
        chunks=n.plan_segments("One thought. Two thoughts.", "warm-explainer")
        self.assertEqual(chunks[-1]["pause_ms"],0)
    def test_abbreviation_handling(self):
        chunks=n.sentences("Ask Dr. Green before you continue. Then review the output.")
        self.assertEqual(len(chunks),2)
        self.assertIn("Dr. Green",chunks[0])
    def test_wave_assembly_silence_and_length(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            wavs=[]
            for i in range(2):
                wav=p/f"chunk{i}.wav"
                with wave.open(str(wav),"wb") as f:
                    f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000)
                    f.writeframes(array("h",[2000]*4800).tobytes())
                wavs.append(wav)
            merged=p/"joined.wav"
            dur=n.join_pcm_wavs(wavs,[{"pause_ms":250},{"pause_ms":0}],merged)
            self.assertAlmostEqual(dur,.45,places=2)
            with wave.open(str(merged),"rb") as f:
                self.assertEqual(f.getnframes(),21600)
                self.assertEqual(f.getframerate(),48000)
    def test_mismatch_and_unexpected_wav_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            with self.assertRaises(n.NarrationError):
                n.join_pcm_wavs([],[],p/"no.wav")
            wav=p/"wrong.wav"
            with wave.open(str(wav),"wb") as f:
                f.setnchannels(1); f.setsampwidth(2); f.setframerate(44100)
                f.writeframes(array("h",[100]*100).tobytes())
            with self.assertRaisesRegex(n.NarrationError,"Unexpected PCM"):
                n.join_pcm_wavs([wav],[{"pause_ms":0}],p/"out.wav")
    def test_offline_dry_run_no_output_writes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/"script.txt").write_text("Here's the idea. Imagine a useful result.",encoding="utf-8")
            self.assertEqual(n.main(["--script",str(p/"script.txt"),"--output",str(p/"audio.mp3"),
                                     "--report",str(p/"report.json"),"--dry-run"]),0)
            self.assertFalse((p/"audio.mp3").exists())
            result=json.loads((p/"report.json").read_text())
            self.assertEqual(result["human_listening_review"],"REQUIRED_BEFORE_PUBLICATION")
            self.assertTrue(result["synthetic_narration"])
            self.assertIsNone(result["audio_duration_seconds"])
    def test_report_preserves_script_hash(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"sample.txt";p.write_text("A clear example.",encoding="utf-8")
            r=n.report_for(p,Path(d)/"audio.mp3","calm-tutorial","en-US-ChristopherNeural",
                           [{"words":3,"pause_ms":0,"rate_percent":-5,"text":"A clear example."}],
                           duration=2.5,dry_run=False)
            self.assertEqual(r["number_of_chunks"],1)
            self.assertEqual(r["audio_duration_seconds"],2.5)
            self.assertEqual(len(r["source_sha256"]),64)


if __name__ == "__main__":
    unittest.main()
