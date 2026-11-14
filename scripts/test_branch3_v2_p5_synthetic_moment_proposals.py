"""P5 synthetic-only rights/edge-case tests (no real source media)."""
from __future__ import annotations

from array import array
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from scripts.branch3_v2_p5_synthetic_moment_proposals import (
    CHANNEL, FRAME_BYTES, P5Denied, HOP_MS, SAMPLE_RATE,
    _probe_closed, audio_rms_windows, detect_scene_events,
    event_windows, safe_process, scan_synthetic_moments,
)
from scripts.branch3_v2_p4_synthetic_handoff_preflight import actual_closed_boundary

BYTES = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 160
PROBE = {
    "streams": [
        {"codec_type": "video", "codec_name": "h264",
         "pix_fmt": "yuv420p", "width": 160, "height": 90},
        {"codec_type": "audio", "codec_name": "aac",
         "sample_rate": "48000", "channels": 1},
    ],
    "format": {"format_name": "mov,mp4,m4a,3gp,3g2,mj2",
               "duration": "6.000", "size": str(len(BYTES))}
}


def demo_pcm():
    samples = array("h", ([0] * (2 * SAMPLE_RATE)
                          + [1600] * SAMPLE_RATE
                          + [0] * (3 * SAMPLE_RATE)))
    import sys
    if sys.byteorder != "little":
        samples.byteswap()
    return samples.tobytes()


def demo_gray():
    return bytes([16]) * (4 * FRAME_BYTES) + bytes([235]) * (
        2 * FRAME_BYTES) + bytes([16]) * (6 * FRAME_BYTES)


def mock_runner(cmd, **kwargs):
    if cmd[0] == "ffprobe":
        return SimpleNamespace(returncode=0, stdout=json.dumps(PROBE),
                               stderr="")
    if cmd[0] != "ffmpeg":
        raise AssertionError("unapproved command")
    if kwargs.get("text") is True:
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    if "s16le" in cmd:
        return SimpleNamespace(returncode=0, stdout=demo_pcm(),
                               stderr=b"")
    if "rawvideo" in cmd:
        return SimpleNamespace(returncode=0, stdout=demo_gray(),
                               stderr=b"")
    raise AssertionError("unapproved FFmpeg command")


class P5MomentProposalTests(unittest.TestCase):
    def test_real_rights_and_media_remain_closed_before_processing(self):
        p = _probe_closed()
        self.assertFalse(p["p4_milestone_complete"])
        self.assertEqual(p["rights_grants_verified"], 0)
        self.assertFalse(p["creator_media_fetch_enabled"])
        self.assertFalse(p["youtube_upload_enabled"])

    def test_rejects_forged_upstream_activation_prior_to_any_media(self):
        legal = actual_closed_boundary()
        for field, value in (
            ("rights_grants_verified", 1),
            ("p4_milestone_complete", True),
            ("creator_media_fetch_enabled", True),
            ("creator_media_write_enabled", True),
            ("youtube_upload_enabled", True),
            ("youtube_publish_enabled", True),
        ):
            forged = dict(legal)
            forged[field] = value
            with self.subTest(field=field):
                with patch(
                    "scripts.branch3_v2_p5_synthetic_moment_proposals.actual_closed_boundary",
                    return_value=forged,
                ):
                    with self.assertRaises(P5Denied):
                        _probe_closed()

    def test_observed_audio_and_video_are_local_measurements(self):
        rms = audio_rms_windows(demo_pcm())
        cuts = detect_scene_events(demo_gray())
        self.assertEqual(len(rms), 12)
        self.assertGreater(rms[4], 900)
        self.assertEqual(rms[0], 0)
        self.assertEqual(cuts, [2000, 3000])
        proposals = event_windows(
            acoustic_rms=rms, scene_events_ms=cuts, duration_ms=6000,
        )
        self.assertEqual(len(proposals), 1)
        p = proposals[0]
        self.assertEqual(p["start_ms"], 1200)
        self.assertEqual(p["end_ms"], 4200)
        self.assertEqual(
            p["evidence_kinds"], ["ACOUSTIC_RMS_RISE", "VIDEO_LUMA_CUT"]
        )
        self.assertIsNone(p["machine_transcript"])
        self.assertFalse(p["creator_rights_verified"])
        self.assertFalse(p["ready_for_editorial_use"])
        self.assertTrue(p["human_context_review_required"])

    def test_no_peak_and_no_cut_means_no_claimed_good_moment(self):
        p = event_windows(
            acoustic_rms=[2000] * 12,
            scene_events_ms=[], duration_ms=6000,
        )
        self.assertEqual(p, [])

    def test_invalid_or_forged_event_observations_are_denied(self):
        cases = [
            dict(acoustic_rms=[False] * 12, scene_events_ms=[],
                 duration_ms=6000),
            dict(acoustic_rms=[0] * 12, scene_events_ms=[-1],
                 duration_ms=6000),
            dict(acoustic_rms=[0] * 12, scene_events_ms=[2000, 2000],
                 duration_ms=6000),
            dict(acoustic_rms=[0] * 12, scene_events_ms=[7000],
                 duration_ms=6000),
            dict(acoustic_rms=[0] * 12, scene_events_ms=[],
                 duration_ms=60_000),
            dict(acoustic_rms=[0] * 12, scene_events_ms=[2000, 1000],
                 duration_ms=6000),
            dict(acoustic_rms=[0] * 23, scene_events_ms=[],
                 duration_ms=6000),
        ]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(P5Denied):
                event_windows(**case)

    def test_pcm_and_frame_lengths_are_validated(self):
        for pcm in (b"", b"x", b"\x00\x00" * 4, b"\x00" * 180000):
            with self.subTest(pcm_length=len(pcm)), self.assertRaises(P5Denied):
                audio_rms_windows(pcm)
        for video in (b"", b"0" * 3, bytes([0]) * FRAME_BYTES,
                      bytes([1]) * (23 * FRAME_BYTES)):
            with self.subTest(frame_length=len(video)), self.assertRaises(P5Denied):
                detect_scene_events(video)

    def test_real_synthetic_local_mock_pipeline_is_quarantined(self):
        with tempfile.TemporaryDirectory() as t:
            scratch = Path(t)
            (scratch / "self_generated.mp4").write_bytes(BYTES)
            report = scan_synthetic_moments(
                scratch=scratch, basename="self_generated.mp4",
                expected_sha256=hashlib.sha256(BYTES).hexdigest(),
                expected_bytes=len(BYTES), runner=mock_runner,
            )
            self.assertEqual(report["channel_id"], CHANNEL)
            self.assertEqual(report["actual_creator_source_count"], 0)
            self.assertEqual(report["real_creator_license_count"], 0)
            self.assertEqual(report["youtube_uploads"], 0)
            self.assertFalse(report["p5_real_licensed_pipeline_complete"])
            self.assertFalse(report["ASR_or_VAD_performed"])
            self.assertFalse(report["speech_or_quotes_inferred"])
            self.assertIsNone(report["estimated_viral_performance"])
            self.assertEqual(report["synthetic_technical_candidate_count"], 1)
            self.assertEqual(len(report["synthetic_candidate_windows"]), 1)
            serialized = json.dumps(report)
            self.assertNotIn(str(scratch), serialized)
            self.assertNotIn(hashlib.sha256(BYTES).hexdigest(), serialized)
            self.assertNotIn("transcript_text", serialized)

    def test_bad_digest_wrong_size_and_path_fail_before_extraction(self):
        with tempfile.TemporaryDirectory() as t:
            scratch = Path(t)
            (scratch / "self_generated.mp4").write_bytes(BYTES)
            (scratch / "shortcut.mp4").symlink_to(scratch / "self_generated.mp4")
            args = dict(
                scratch=scratch, basename="self_generated.mp4",
                expected_sha256=hashlib.sha256(BYTES).hexdigest(),
                expected_bytes=len(BYTES), runner=mock_runner,
            )
            variations = [
                {"basename": "../../self_generated.mp4"},
                {"basename": "shortcut.mp4"},
                {"basename": "OTHER.mov"},
                {"expected_sha256": "0" * 64},
                {"expected_bytes": len(BYTES) + 1},
                {"expected_bytes": True},
            ]
            for patch_args in variations:
                with self.subTest(patch_args=patch_args):
                    with self.assertRaises(P5Denied):
                        scan_synthetic_moments(**{**args, **patch_args})

    def test_ffmpeg_failures_bounded_and_no_transcript_predictions(self):
        with tempfile.TemporaryDirectory() as t:
            scratch = Path(t)
            (scratch / "self_generated.mp4").write_bytes(BYTES)
            args = dict(
                scratch=scratch, basename="self_generated.mp4",
                expected_sha256=hashlib.sha256(BYTES).hexdigest(),
                expected_bytes=len(BYTES),
            )
            def binary_empty(cmd, **kwargs):
                if kwargs.get("text"):
                    return mock_runner(cmd, **kwargs)
                if cmd[0] == "ffprobe":
                    return mock_runner(cmd, **kwargs)
                return SimpleNamespace(returncode=0, stdout=b"", stderr=b"")
            def decoding_timeout(cmd, **kwargs):
                if kwargs.get("text") or cmd[0] == "ffprobe":
                    return mock_runner(cmd, **kwargs)
                raise subprocess.TimeoutExpired(cmd, 25)
            for runner in (binary_empty, decoding_timeout):
                with self.subTest(runner=runner.__name__), self.assertRaises(P5Denied):
                    scan_synthetic_moments(**args, runner=runner)

    def test_commands_reject_non_ffmpeg_and_error_status(self):
        with self.assertRaises(P5Denied):
            safe_process(["curl", "https://example.org/video"],
                         runner=mock_runner, max_output_bytes=1000)
        with self.assertRaises(P5Denied):
            safe_process(["ffmpeg"], runner=lambda *a, **k:
                         SimpleNamespace(returncode=1, stdout=b"1", stderr=b""),
                         max_output_bytes=1000)


if __name__ == "__main__":
    unittest.main()
