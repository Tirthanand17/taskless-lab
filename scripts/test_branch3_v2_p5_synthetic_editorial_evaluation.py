"""Adversarial offline P5 evaluation: synthetic golden references only."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.branch3_v2_p5_synthetic_editorial_evaluation import (
    P5EvaluationDenied, _read_temp_report, assess_generated_p5_packet,
    evaluate_synthetic_sources, validate_detector_report,
)
from scripts.branch3_v2_p5_synthetic_moment_proposals import _probe_closed


def detector_packet():
    return {
        "stage": "CLIVOX_V2_P5_SYNTHETIC_SIGNAL_CANDIDATES_ONLY",
        "channel_id": "UCfPEvy0SefE_5nNlYlY_CyQ",
        "synthetic_original_fixture_only": True,
        "actual_creator_source_count": 0,
        "real_creator_license_count": 0,
        "third_party_video_downloads": 0,
        "outreach_messages_sent": 0,
        "youtube_api_calls": 0,
        "youtube_uploads": 0,
        "p5_real_licensed_pipeline_complete": False,
        "p5_real_editor_label_evaluation_complete": False,
        "ASR_or_VAD_performed": False,
        "speech_or_quotes_inferred": False,
        "youtube_replay_heatmap_inferred": False,
        "estimated_viral_performance": None,
        "human_source_context_required": True,
        "synthetic_technical_candidate_count": 1,
        "synthetic_candidate_windows": [{
            "start_ms": 1200, "end_ms": 4200,
            "evidence_kinds": ["ACOUSTIC_RMS_RISE", "VIDEO_LUMA_CUT"],
            "proposal_id": "synthetic_01",
            "machine_transcript": None,
            "transcript_verified": False,
            "creator_rights_verified": False,
            "ready_for_editorial_use": False,
            "human_context_review_required": True,
        }],
        "status": "PRIVATE_LICENSING_REQUIRED_NO_REAL_CLIP_RELEASE",
    }


def source(sid, *, predictions=None, refs=None, duration=6000):
    return {
        "source_id": sid, "duration_ms": duration,
        "reference_kind": "SYNTHETIC_GOLDEN_EVENT_TIMECODES_NOT_EDITOR_LABELS",
        "predictions": predictions if predictions is not None else [],
        "reference_windows": refs if refs is not None else [],
        "split": "SYNTHETIC_HELDOUT_TEST",
        "actual_human_review_completed": False,
        "real_source_media_accessed": False,
    }


def window(a, b):
    return {"start_ms": a, "end_ms": b}


class SyntheticEvaluatorTests(unittest.TestCase):
    def test_upstream_rights_closed(self):
        p = _probe_closed()
        self.assertFalse(p["p4_milestone_complete"])
        self.assertEqual(p["rights_grants_verified"], 0)

    def test_valid_real_p5_schema_one_synthetic_golden_event(self):
        p = detector_packet()
        before = copy.deepcopy(p)
        windows = validate_detector_report(p)
        self.assertEqual(windows, [window(1200, 4200)])
        report = assess_generated_p5_packet(p)
        self.assertEqual(report["stage"],
                         "CLIVOX_V2_P5_SYNTHETIC_REFERENCE_EVALUATION_ONLY")
        self.assertEqual(report["test_sources"], 1)
        self.assertEqual(report["actual_human_editor_labels"], 0)
        self.assertFalse(report["training_performed"])
        self.assertFalse(report["real_world_precision_recall_validated"])
        self.assertFalse(report["media_access_or_youtube_upload_authorized"])
        self.assertEqual(report["real_creator_sources"], 0)
        self.assertEqual(report["real_creator_licenses"], 0)
        self.assertFalse(report["p5_real_milestone_complete"])
        self.assertIsNone(report["viral_performance_prediction"])
        values = report["synthetic_test_metrics"][0]
        self.assertEqual(values["matched_events"], 1)
        self.assertEqual(values["precision_of_available_top_five"], 1.0)
        self.assertEqual(values["recall_of_synthetic_reference_events"], 1.0)
        self.assertEqual(before, p)

    def test_forged_rights_live_media_or_platform_metrics_rejected(self):
        values = (
            ("actual_creator_source_count", 1),
            ("actual_creator_source_count", False),
            ("real_creator_license_count", 1),
            ("third_party_video_downloads", 1),
            ("outreach_messages_sent", 1),
            ("youtube_api_calls", 1),
            ("youtube_uploads", 1),
            ("p5_real_licensed_pipeline_complete", True),
            ("p5_real_editor_label_evaluation_complete", True),
            ("ASR_or_VAD_performed", True),
            ("speech_or_quotes_inferred", True),
            ("youtube_replay_heatmap_inferred", True),
            ("estimated_viral_performance", .99),
            ("synthetic_original_fixture_only", False),
            ("human_source_context_required", False),
            ("channel_id", "UC" + "a" * 22),
            ("synthetic_technical_candidate_count", 20),
        )
        for name, value in values:
            p = detector_packet()
            p[name] = value
            with self.subTest(name=name), self.assertRaises(P5EvaluationDenied):
                validate_detector_report(p)
        for unexpected in (
            "source_url", "creator_name", "source_video_id",
            "public_youtube_view_count", "most_replayed_timestamp",
            "creator_license_granted", "auth_token",
        ):
            p = detector_packet()
            p[unexpected] = "example"
            with self.subTest(field=unexpected), self.assertRaises(P5EvaluationDenied):
                validate_detector_report(p)

    def test_forged_candidate_transcripts_license_and_bad_times(self):
        values = (
            ("machine_transcript", "real quote"),
            ("transcript_verified", True),
            ("creator_rights_verified", True),
            ("ready_for_editorial_use", True),
            ("human_context_review_required", False),
            ("proposal_id", "external_01"),
            ("start_ms", -1),
            ("start_ms", True),
            ("end_ms", 7000),
            ("end_ms", 1200),
            ("evidence_kinds", ["MOST_REPLAYED"]),
            ("evidence_kinds", ["VIDEO_LUMA_CUT", "VIDEO_LUMA_CUT"]),
        )
        for name, value in values:
            p = detector_packet()
            p["synthetic_candidate_windows"][0][name] = value
            with self.subTest(name=name), self.assertRaises(P5EvaluationDenied):
                validate_detector_report(p)
        p = detector_packet()
        p["synthetic_candidate_windows"][0]["creator_contact_email"] = "x@example.org"
        with self.assertRaises(P5EvaluationDenied):
            validate_detector_report(p)

    def test_no_detector_suggestions_is_not_a_zero_popularity_claim(self):
        p = detector_packet()
        p["synthetic_technical_candidate_count"] = 0
        p["synthetic_candidate_windows"] = []
        result = assess_generated_p5_packet(p)
        value = result["synthetic_test_metrics"][0]
        self.assertIsNone(value["precision_of_available_top_five"])
        self.assertEqual(value["recall_of_synthetic_reference_events"], 0.0)
        self.assertEqual(value["missed_reference_events"], 1)

    def test_one_to_one_no_double_credit_and_false_positives(self):
        # 2 held-out synthetic sources; one false positive and one missed reference.
        rows = [
            source("synthetic_testalpha",
                   predictions=[window(0, 750), window(2000, 3000)],
                   refs=[window(0, 1000), window(4000, 5000)]),
            source("synthetic_testbeta",
                   predictions=[window(1300, 2800)],
                   refs=[window(1000, 3000)]),
        ]
        result = evaluate_synthetic_sources(rows)
        a, b = result["synthetic_test_metrics"]
        self.assertEqual(a["matched_events"], 1)
        self.assertEqual(a["unmatched_proposals"], 1)
        self.assertEqual(a["missed_reference_events"], 1)
        self.assertEqual(a["precision_of_available_top_five"], 0.5)
        self.assertEqual(a["recall_of_synthetic_reference_events"], 0.5)
        self.assertEqual(b["matched_events"], 1)
        self.assertEqual(b["precision_of_available_top_five"], 1.0)
        self.assertEqual(b["recall_of_synthetic_reference_events"], 1.0)
        self.assertEqual(result["actual_human_editor_labels"], 0)

    def test_empty_references_are_unknown_recall_not_zero(self):
        result = evaluate_synthetic_sources([
            source("synthetic_testonly", predictions=[window(500, 1500)], refs=[]),
        ])
        r = result["synthetic_test_metrics"][0]
        self.assertIsNone(r["recall_of_synthetic_reference_events"])
        self.assertEqual(r["precision_of_available_top_five"], 0.0)
        self.assertEqual(r["missed_reference_events"], 0)

    def test_invalid_duplicate_sources_and_leaked_metadata_rejected(self):
        a = source("synthetic_testalpha", predictions=[window(0, 800)],
                   refs=[window(0, 800)])
        scenarios = [
            [a, copy.deepcopy(a)],
            [{**a, "source_id": "real_creator_name"}],
            [{**a, "source_id": "synthetic_a"}],
            [{**a, "duration_ms": True}],
            [{**a, "split": "TRAIN_ON_HELDOUT_SOURCE"}],
            [{**a, "reference_kind": "ACTUAL_HUMAN_EDITOR_LABEL"}],
            [{**a, "actual_human_review_completed": True}],
            [{**a, "real_source_media_accessed": True}],
            [{**a, "platform_api_stats": {"views": 100}}],
            [{**a, "creator_permission": "approved"}],
            [{**a, "reference_windows": [window(-1, 100)]}],
            [{**a, "predictions": [window(500, 500)]}],
            [{**a, "predictions": [window(0, 2000), window(1900, 2500)]}],
        ]
        for i, item in enumerate(scenarios):
            with self.subTest(i=i), self.assertRaises(P5EvaluationDenied):
                evaluate_synthetic_sources(item)

    def test_source_io_only_bounded_ephemeral_json(self):
        with tempfile.TemporaryDirectory() as temp:
            scratch = Path(temp)
            real = scratch / "quarantined-signals-only.json"
            real.write_text(json.dumps(detector_packet()), encoding="utf-8")
            self.assertEqual(_read_temp_report(scratch, real.name), detector_packet())
            (scratch / "fake.json").symlink_to(real)
            for name in ("../../quarantined-signals-only.json",
                         "fake.json", "/tmp/secrets.json"):
                with self.subTest(name=name), self.assertRaises(P5EvaluationDenied):
                    _read_temp_report(scratch, name)
            real.write_text("x" * 33_000, encoding="utf-8")
            with self.assertRaises(P5EvaluationDenied):
                _read_temp_report(scratch, real.name)

    def test_input_does_not_mutate_across_calls(self):
        a = source("synthetic_testalpha", predictions=[window(1000, 2000)],
                   refs=[window(1200, 1800)])
        packet = [a]
        saved = copy.deepcopy(packet)
        one = evaluate_synthetic_sources(packet)
        two = evaluate_synthetic_sources(packet)
        self.assertEqual(packet, saved)
        self.assertEqual(one, two)


if __name__ == "__main__":
    unittest.main()
