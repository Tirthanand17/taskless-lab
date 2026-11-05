"""Tests for REAL author-written SRT and technically inspected external WAV.

Audio fixtures are synthetic sine waves, never natural human narrators. No
account access, no external downloads, no production voice or upload.
"""
from dataclasses import replace
from pathlib import Path
import math
import struct
import tempfile
import unittest
import wave

from autopilot.agent_org import WorkflowError
from autopilot.phase3_voice_subtitle_handoff import (
    build_subtitles_from_authored_csv, export_subtitle_files, inspect_external_voice_wav,
)


def wav_fixture(path:Path, *, seconds:float=1.0, rate:int=16000,
                level:float=0.12,channels:int=1) -> None:
    with wave.open(str(path),"wb") as out:
        out.setnchannels(channels)
        out.setsampwidth(2)
        out.setframerate(rate)
        samples=[]
        for i in range(round(seconds*rate)):
            sample=int(32767*level*math.sin(2*math.pi*220*i/rate))
            samples.append(struct.pack("<h",sample)*channels)
        out.writeframes(b"".join(samples))


class ActualScriptSrtTests(unittest.TestCase):
    def test_three_language_specific_caption_files(self):
        out=build_subtitles_from_authored_csv()
        self.assertEqual(set(out),{
            "csv_tutorial_short_hi","csv_tutorial_short_en","csv_tutorial_long_hi"
        })
        self.assertEqual(out["csv_tutorial_short_en"]["duration_ms"],42000)
        self.assertEqual(out["csv_tutorial_short_hi"]["duration_ms"],42000)
        self.assertEqual(out["csv_tutorial_long_hi"]["duration_ms"],432000)
        for r in out.values():
            self.assertTrue(r["timings_are_script_estimates"])
            self.assertFalse(r["actual_voice_alignment_verified"])
            self.assertFalse(r["actual_narration_present"])
            self.assertFalse(r["ready_for_upload"])
            self.assertGreater(r["cue_count"],4)

    def test_real_script_words_preserved_in_srt_cues(self):
        from autopilot.phase2r3_authored_pack_audit import SOURCE, TIME, _sections
        original=_sections(SOURCE.read_text(encoding="utf-8"))
        by_ep=build_subtitles_from_authored_csv()
        for segment,episode in zip(original,("csv_tutorial_short_hi","csv_tutorial_short_en","csv_tutorial_long_hi")):
            expected=" ".join(row[4] for row in TIME.findall(segment))
            lines=by_ep[episode]["srt"].splitlines()
            spoken=" ".join(line for line in lines
                            if line and not line.isdecimal() and "-->" not in line)
            self.assertEqual(spoken," ".join(expected.split()))

    def test_srt_is_deterministic_and_has_correct_end_time(self):
        a=build_subtitles_from_authored_csv()
        b=build_subtitles_from_authored_csv()
        self.assertEqual(a,b)
        self.assertIn("00:00:42,000",a["csv_tutorial_short_en"]["srt"])
        self.assertIn("00:07:12,000",a["csv_tutorial_long_hi"]["srt"])
        self.assertNotIn("https://",str({k:v["srt"] for k,v in a.items()}))

    def test_markdown_subtitle_gaps_block(self):
        from autopilot.phase2r3_authored_pack_audit import SOURCE
        content=SOURCE.read_text(encoding="utf-8")
        changed=content.replace("00:10–00:20","00:11–00:20",1)
        with self.assertRaises(WorkflowError):
            build_subtitles_from_authored_csv(markdown=changed)

    def test_uncleared_script_cannot_be_silently_promoted(self):
        from autopilot.phase2r3_authored_pack_audit import SOURCE
        content=SOURCE.read_text(encoding="utf-8")
        changed=content.replace("UNREVIEWED WRITING","REVIEWED AND APPROVED")
        with self.assertRaises(WorkflowError):
            build_subtitles_from_authored_csv(markdown=changed)

    def test_safe_export_is_explicit_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            out=export_subtitle_files(Path(root))
            self.assertEqual(len(out),3)
            p=Path(root)/"csv_tutorial_short_en.draft_estimated.srt"
            self.assertTrue(p.is_file())
            self.assertIn("00:00:42,000",p.read_text(encoding="utf-8"))
            with self.assertRaises(WorkflowError):
                export_subtitle_files(Path(root))
            self.assertEqual(len(list(Path(root).iterdir())),3)

    def test_export_requires_existing_directory(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(WorkflowError):
                export_subtitle_files(Path(root)/"not_created")


class RealWavTechnicalInspectionTests(unittest.TestCase):
    def call(self,path:Path,*,duration:float=1.0,narrator:str="narrator_hindi_a",language:str="hi"):
        return inspect_external_voice_wav(
            path,episode_id="csv_tutorial_short_hi",
            expected_seconds=duration,
            declared_narrator_id=narrator,declared_language=language,
        )

    def test_actual_sound_bytes_are_inspected_not_authenticated(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"synthetic_tone_not_voice.wav"
            wav_fixture(path)
            report=self.call(path)
            self.assertEqual(report["status"],"WAV_TECHNICAL_EVIDENCE_NOT_SPEECH_APPROVAL")
            self.assertEqual(len(report["sha256"]),64)
            self.assertGreater(report["rms_normalized"],0.02)
            for label in ("real_speech_verified","human_naturalness_verified",
                          "license_rights_verified","narrator_identity_verified",
                          "audio_caption_alignment_verified","publishable"):
                self.assertFalse(report[label])

    def test_silent_wav_refused(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"silence.wav"
            wav_fixture(path,level=0)
            with self.assertRaises(WorkflowError):
                self.call(path)

    def test_wrong_duration_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"synthetic_tone.wav"
            wav_fixture(path)
            with self.assertRaises(WorkflowError):
                self.call(path,duration=42.0)

    def test_invalid_narrator_language_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"synthetic_tone.wav"
            wav_fixture(path)
            with self.assertRaises(WorkflowError):
                self.call(path,narrator="bad")
            with self.assertRaises(WorkflowError):
                self.call(path,language="es")

    def test_unsupported_sample_rate_refused(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"synthetic_tone.wav"
            wav_fixture(path,rate=8000)
            with self.assertRaises(WorkflowError):
                self.call(path)

    def test_non_wav_and_symlink_refused(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"bad.mp3"
            path.write_bytes(b"pretend_mp3")
            with self.assertRaises(WorkflowError):
                self.call(path)
            tone=Path(root)/"tone.wav"
            wav_fixture(tone)
            link=Path(root)/"link.wav"
            link.symlink_to(tone)
            with self.assertRaises(WorkflowError):
                self.call(link)

    def test_changed_audio_changes_digest(self):
        with tempfile.TemporaryDirectory() as root:
            first=Path(root)/"first.wav"
            second=Path(root)/"second.wav"
            wav_fixture(first,level=0.08)
            wav_fixture(second,level=0.14)
            self.assertNotEqual(self.call(first)["sha256"],self.call(second)["sha256"])

    def test_boolean_falsified_duration_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"one.wav"
            wav_fixture(path)
            with self.assertRaises(WorkflowError):
                self.call(path,duration=True)


if __name__ == "__main__":
    unittest.main()
