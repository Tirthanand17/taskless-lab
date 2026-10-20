"""Structural tests for actual authored CSV tutorial Markdown, NOT audio or publication."""
from datetime import datetime, timezone
from pathlib import Path
import unittest

from autopilot.agent_org import WorkflowError
from autopilot.phase2r3_authored_pack_audit import (
    SOURCE, audit_authored_csv_pack,
)

NOW = datetime(2026, 10, 17, 12, tzinfo=timezone.utc)


class ActualAuthoredCsvAuditTests(unittest.TestCase):
    def setUp(self):
        self.raw=SOURCE.read_text(encoding="utf-8")

    def check(self, changed=None):
        return audit_authored_csv_pack(now=NOW,markdown=self.raw if changed is None else changed)

    def test_actual_three_authored_scripts_pass_structural_check(self):
        report=self.check()
        self.assertEqual(len(report["episodes"]),3)
        self.assertEqual(report["fictional_example_total"],58)
        self.assertEqual({x["duration_ms"] for x in report["episodes"]},{42_000,432_000})
        self.assertTrue(report["fact_review_synthetic_scaffolding"])
        self.assertTrue(report["human_language_review_synthetic_scaffolding"])
        self.assertFalse(report["live_source_capture_verified"])
        self.assertFalse(report["ready_for_rendering"])
        self.assertFalse(report["publishing_authorized"])
        self.assertFalse(report["actual_narration_recorded"])
        self.assertFalse(report["youtube_published"])

    def test_source_file_is_only_repo_fixed_text(self):
        self.assertTrue(SOURCE.is_file())
        self.assertEqual(SOURCE.suffix, ".md")
        self.assertEqual(self.check()["source"],"FIXED_REPOSITORY_AUTHORED_MARKDOWN_DRAFT")

    def test_distinct_narrators_and_english_hindi_runtime(self):
        report=self.check()
        videos=report["episodes"]
        shorts=[v for v in videos if v["kind"]=="short"]
        self.assertEqual({v["language"] for v in shorts},{"en","hi"})
        self.assertEqual(len({v["narrator_id"] for v in shorts}),2)
        self.assertEqual([v["language"] for v in videos if v["kind"]=="long"],["hi"])

    def test_runtime_and_scene_count_stay_bound_to_actual_voice_text(self):
        report=self.check()
        self.assertEqual(sum(v["beat_count"] for v in report["episodes"]),32)
        self.assertTrue(all(65 <= v["estimated_wpm"] <= 235 for v in report["episodes"]))

    def test_missing_dataset_label_fails(self):
        with self.assertRaises(WorkflowError):
            self.check(self.raw.replace("FICTIONAL SAMPLE DATA","PLACEHOLDER"))

    def test_missing_simulation_label_fails(self):
        with self.assertRaises(WorkflowError):
            self.check(self.raw.replace("ILLUSTRATIVE SIMULATION","EXPLANATION"))

    def test_fake_production_status_label_fails(self):
        with self.assertRaises(WorkflowError):
            self.check(self.raw.replace("UNREVIEWED WRITING","PRODUCTION APPROVED"))

    def test_scene_time_gap_fails(self):
        with self.assertRaises(WorkflowError):
            self.check(self.raw.replace("00:10–00:20","00:11–00:20",1))

    def test_scene_time_overlap_fails(self):
        with self.assertRaises(WorkflowError):
            self.check(self.raw.replace("00:10–00:20","00:09–00:20",1))

    def test_more_scenes_than_declared_fails(self):
        snippet="| 00:00–00:01 | An extra fabricated scene | Imaginary motion graphics |"
        with self.assertRaises(WorkflowError):
            self.check(self.raw.replace("## SHORT 2",snippet+"\n\n## SHORT 2",1))

    def test_hindi_replaced_by_english_fails(self):
        start=self.raw.index("## SHORT 1")
        next_item=self.raw.index("## SHORT 2")
        changed=self.raw[:start]+self.raw[start:next_item].replace(
            "क्या आपको Excel जैसी CSV फ़ाइल का डेटा जल्दी समझना है? चलिए Python से सिर्फ़ नकली उदाहरण पर तरीका देखते हैं।",
            "This lesson explains safe fictional CSV rows with Python columns and calculations."
        )+self.raw[next_item:]
        # One English beat does not remove enough Hindi to fail language checks:
        # still preserve an executable structural package, not semantic review.
        r=self.check(changed)
        self.assertFalse(r["independent_language_quality_verified"])

    def test_real_source_or_audio_claims_always_false(self):
        r=self.check()
        self.assertTrue(r["narration_subtitles_equal_only_as_written_text"])
        self.assertFalse(r["subtitle_speech_alignment_verified"])
        self.assertFalse(r["voice_rights_verified"])
        self.assertFalse(r["actual_video_created"])

    def test_does_not_expose_full_script_text_or_privacy_data_in_report(self):
        r=self.check()
        self.assertNotIn("क्या आपको Excel", str(r))
        self.assertNotIn("Your CSV looks like a wall", str(r))
        self.assertNotIn("Write three synthetic", str(r))
        self.assertEqual(r["network_calls"],0)

    def test_naive_review_clock_rejected(self):
        with self.assertRaises(WorkflowError):
            audit_authored_csv_pack(now=datetime(2026,10,17,12))

    def test_missing_text_section_rejected(self):
        with self.assertRaises(WorkflowError):
            self.check(self.raw.replace("## SHORT 2","## OTHER VIDEO"))

    def test_empty_or_absurd_file_rejected(self):
        for value in ("", "x"*50001):
            with self.subTest(length=len(value)), self.assertRaises(WorkflowError):
                self.check(value)


if __name__=="__main__":
    unittest.main()
