"""Actual, synthetic local audio inspection and draft SRT formatting tests.

Generated test tones are NOT human-sounding narration, licensed content or
publishable video soundtracks.
"""
from dataclasses import replace
from pathlib import Path
import subprocess
import tempfile
import unittest

from autopilot.narration_inspection import inspect_narration
from autopilot.phase3_production import (
    SubtitleCue, subtitle_timeline_to_srt
)
from autopilot.test_phase3_production import plan_data
from autopilot.agent_org import WorkflowError

class ActualAudioInspectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder=tempfile.TemporaryDirectory()
        root=Path(cls.folder.name)
        cls.tone=root/"synthetic_440hz.wav"
        cls.silent=root/"silent.wav"
        for path,pattern in ((cls.tone,"sine=frequency=440:duration=2"),
                             (cls.silent,"anullsrc=r=48000:cl=mono:d=2")):
            r=subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
                              "-f","lavfi","-i",pattern,"-c:a","pcm_s16le","-t","2",
                              str(path)],capture_output=True,text=True,timeout=30)
            if r.returncode:
                raise RuntimeError("FFmpeg test fixture failed")

    @classmethod
    def tearDownClass(cls):
        cls.folder.cleanup()

    def test_synthetic_tone_is_technical_only(self):
        data=inspect_narration(self.tone,expected_duration_s=2)
        self.assertEqual(data.status,"PASS_AUDIO_TECHNICAL_ONLY")
        self.assertEqual(data.channels,1)
        self.assertEqual(len(data.sha256_hex),64)
        self.assertFalse(data.narration_naturalness_verified)
        self.assertFalse(data.commercial_rights_verified)
        self.assertFalse(data.publishing_authorized)

    def test_significant_silence_requires_review(self):
        out=inspect_narration(self.silent,expected_duration_s=2)
        self.assertEqual(out.status,"BLOCKED_AUDIO_TECHNICAL_QA")
        self.assertIn("SIGNIFICANT_SILENCE_REQUIRES_REVIEW",out.problems)

    def test_expected_duration_mismatch_blocks(self):
        out=inspect_narration(self.tone,expected_duration_s=15)
        self.assertIn("AUDIO_TIMING_DIFFERS_FROM_PLAN",out.problems)

    def test_missing_audio_blocks(self):
        out=inspect_narration(self.tone.parent/"missing_audio.wav")
        self.assertIn("UNSAFE_OR_MISSING_AUDIO",out.problems)

    def test_small_quota_fails_safely(self):
        out=inspect_narration(self.tone,size_ceiling=50)
        self.assertIn("AUDIO_SIZE_OUT_OF_BOUNDS",out.problems)

    def test_invalid_policy_fails_safely(self):
        out=inspect_narration(self.tone,timeout_s=0)
        self.assertIn("INVALID_INSPECTION_POLICY",out.problems)

class DraftSubtitleExportTests(unittest.TestCase):
    def test_valid_hindi_srt_syntactic_output_only(self):
        timeline=plan_data()[3]
        srt=subtitle_timeline_to_srt(timeline)
        self.assertIn("1\n00:00:00,000 --> 00:00:04,800",srt)
        self.assertIn("2\n00:00:04,900 --> 00:00:10,000",srt)
        self.assertIn("CSV फ़ाइल",srt)

    def test_srt_rejects_markup(self):
        timeline=plan_data()[3]
        bad=replace(timeline,cues=(replace(timeline.cues[0],text="<i>Fake</i>"),timeline.cues[1]))
        with self.assertRaises(WorkflowError):subtitle_timeline_to_srt(bad)

    def test_srt_rejects_overlapping_timing(self):
        timeline=plan_data()[3]
        bad=replace(timeline,cues=(replace(timeline.cues[0],end_ms=5000),timeline.cues[1]))
        with self.assertRaises(WorkflowError):subtitle_timeline_to_srt(bad)

    def test_srt_export_does_not_authorize_upload(self):
        timeline=plan_data()[3]
        srt=subtitle_timeline_to_srt(timeline)
        self.assertNotIn("publish_permission",srt)
        self.assertNotIn("Authorization:",srt)

if __name__=="__main__":
    unittest.main()
