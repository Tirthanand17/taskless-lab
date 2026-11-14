"""Adversarial offline CLIVOX A5 private revision sandbox tests.

The mock tests never fetch the network, real video, human notes or keys.
The original-video workflow separately renders a genuine synthetic example
and performs independent decoded-frame and postmix WAV checks.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.branch3_a5_revision_sandbox import (
    RevisionSandboxDenied, rehearse_private_revision,
    stage_candidate_episode
)
from scripts.branch3_a5_cue_review_worksheet import VIDEO, AUDIO, SRT
from scripts.branch3_a6_original_handoff import CATALOG, ROOT, sha
from scripts.branch3_original_arcade_pilots import validate_catalog


class PrivateRevisionSandboxTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.review = self.root / "review"
        self.review.mkdir()
        self.out = self.root / "quarantined"
        self.out.mkdir()
        self.source = json.loads(CATALOG.read_text("utf-8"))
        self.episode = validate_catalog(self.source)[0]
        self.folder = self.review / self.episode["id"]
        self.folder.mkdir()
        for name, data in (
            (VIDEO, b"old-original-video"),
            (AUDIO, b"old-original-voice"),
            (SRT, b"old-original-subtitle"),
        ):
            (self.folder / name).write_bytes(data)
        self.preview = {
            "schema_version": 1,
            "domain": "CLIVOX-A5-PRIVATE-SCENE-REVISION-PREVIEW-NEVER-APPLY",
            "episode_id": self.episode["id"],
            "source_catalog_sha256": sha(CATALOG),
            "candidate_spoken_rewrites_count": 1,
            "original_source_catalog_modified": False,
            "original_mp4_wav_srt_modified": False,
            "human_reviewer_identity_authenticated": False,
            "owner_review_completed": False,
            "ready_to_upload": False,
            "ready_to_schedule": False,
            "ready_to_publish": False,
            "actual_youtube_api_calls": 0,
            "candidate_scene_text_diffs_not_applied": [{
                "scene_number": 1,
                "scene_start_s": 0,
                "scene_end_s": 3,
                "changed_cue_numbers": [1],
                "original_spoken": self.episode["beats"][0]["spoken"],
                "candidate_spoken_not_applied":
                    "A strange door learns your choices.",
                "fresh_voice_srt_mp4_a5_a6_verification_required": True,
                "human_editor_must_accept_or_rewrite": True,
            }],
            "exact_review_packet_sha256": "1" * 64,
            "exact_review_video_sha256": sha(self.folder / VIDEO),
            "exact_review_audio_sha256": sha(self.folder / AUDIO),
            "exact_review_srt_sha256": sha(self.folder / SRT),
            "edited_correction_csv_sha256": "2" * 64,
            "pending_or_incomplete_rows": 7,
        }
        self.edited_csv = self.root / "private-notes.csv"
        self.edited_csv.write_text("SYNTHETIC_ONLY", encoding="utf-8")
        self.mock_media_report = {
            "actual_ffprobe_checks_passed": True,
            "youtube_upload_authorized": False,
            "youtube_schedule_authorized": False,
            "youtube_publish_authorized": False,
            "decoded_actual_frame_caption_safezone_qa": {
                "every_draft_caption_cue_visible_in_safe_zone": True,
                "actual_encoded_frames_checked": 8,
                "draft_caption_cue_count": 8,
                "per_cue_samples": [{} for _ in range(8)],
            },
            "independent_mixed_audio_vs_srt_speech_boundary_qa": {
                "draft_caption_cue_count": 8,
                "all_draft_cues_have_recovered_speech_activity": True,
                "per_cue": [{} for _ in range(8)],
                "phoneme_forced_alignment_or_asr_performed": False,
            },
        }
        self.before_catalog = sha(CATALOG)
        self.before_prior = {
            x: sha(self.folder / x) for x in (VIDEO, AUDIO, SRT)
        }
        self.render_seen = []

    def stub_render(self, ep, folder, mode):
        self.render_seen.append(deepcopy(ep))
        self.assertEqual(mode, "preview")
        self.assertEqual(ep["beats"][0]["spoken"],
                         "A strange door learns your choices.")
        self.assertEqual(ep["beats"][1:], self.episode["beats"][1:])
        (folder / VIDEO).write_bytes(b"NEW_SYNTHETIC_MP4")
        (folder / AUDIO).write_bytes(b"NEW_SYNTHETIC_WAV")
        (folder / SRT).write_text("1\nDRAFT_ONLY\n", encoding="utf-8")
        return {"youtube_upload_authorized": False}

    def rehearse(self, *, preview=None):
        p = self.preview if preview is None else preview
        with patch(
            "scripts.branch3_a5_revision_sandbox.compile_private_revision_preview",
            return_value=p
        ) as verified, patch(
            "scripts.branch3_a5_revision_sandbox.render_episode",
            side_effect=self.stub_render
        ), patch(
            "scripts.branch3_a5_revision_sandbox.probe",
            return_value={"streams": []}
        ), patch(
            "scripts.branch3_a5_revision_sandbox.validate_episode_report",
            return_value=self.mock_media_report
        ):
            result = rehearse_private_revision(
                self.review, selection="all",
                episode_id=self.episode["id"],
                edited_csv=self.edited_csv,
                output_root=self.out
            )
            verified.assert_called_once_with(
                self.review, selection="all",
                episode_id=self.episode["id"],
                edited_csv=self.edited_csv
            )
        return result

    def test_revision_rehearsal_keeps_all_original_bytes_and_release_false(self):
        result = self.rehearse()
        self.assertEqual(result["candidate_spoken_rewrites_count"], 1)
        self.assertEqual(result["candidate_scene_changes"], 1)
        self.assertEqual(result["pending_or_incomplete_original_review_rows"], 7)
        self.assertEqual(result["new_real_encoded_subtitle_cues_checked"], 8)
        self.assertEqual(result["new_real_mixed_audio_cues_checked"], 8)
        self.assertNotEqual(result["candidate_video_sha256"],
                            result["original_video_sha256"])
        self.assertTrue(result["candidate_sandbox_is_not_release_master"])
        self.assertTrue(result["no_owner_a6_reuse_or_release_packet_created"])
        self.assertEqual(sha(CATALOG), self.before_catalog)
        self.assertEqual(
            {x: sha(self.folder / x) for x in self.before_prior},
            self.before_prior
        )
        for flag in (
            "human_editorial_acceptance_verified",
            "original_signed_release_exists",
            "third_party_rights_or_licenses_verified",
            "human_voice_words_or_phoneme_alignment_verified",
            "youtube_upload_authorized", "youtube_schedule_authorized",
            "youtube_publish_authorized",
        ):
            self.assertIs(result[flag], False, flag)
        self.assertEqual(result["actual_google_api_calls"], 0)
        self.assertEqual(len(self.render_seen), 1)
        path = self.out / "PRIVATE-SANDBOX-TECHNICAL-REPORT.json"
        self.assertEqual(json.loads(path.read_text("utf-8")), result)
        self.assertFalse((self.out / self.episode["id"] /
                          "owner-handoff-quarantined.json").exists())
        self.assertFalse((self.out / self.episode["id"] /
                          "owner-editorial-review-UNSIGNED.json").exists())

    def test_refuses_reuse_output_or_review_tree_or_repo(self):
        (self.out / "leftover.txt").write_text("old", encoding="utf-8")
        with self.assertRaisesRegex(RevisionSandboxDenied, "EMPTY_NEW"):
            self.rehearse()
        with self.assertRaisesRegex(RevisionSandboxDenied, "OVERLAP"):
            with patch(
                "scripts.branch3_a5_revision_sandbox.compile_private_revision_preview",
                return_value=self.preview
            ):
                rehearse_private_revision(
                    self.review, selection="all",
                    episode_id=self.episode["id"],
                    edited_csv=self.edited_csv, output_root=self.review
                )
        with self.assertRaises(RevisionSandboxDenied):
            with patch(
                "scripts.branch3_a5_revision_sandbox.compile_private_revision_preview",
                return_value=self.preview
            ):
                rehearse_private_revision(
                    self.review, selection="all",
                    episode_id=self.episode["id"],
                    edited_csv=self.edited_csv, output_root=ROOT
                )

    def test_forged_approval_bad_sha_no_issues_and_duplicate_scene_denied(self):
        cases = (
            {"ready_to_publish": True},
            {"owner_review_completed": True},
            {"human_reviewer_identity_authenticated": True},
            {"source_catalog_sha256": "f" * 64},
            {"candidate_spoken_rewrites_count": 0},
            {"actual_youtube_api_calls": 1},
        )
        for changed in cases:
            self.out = self.root / ("isolated" + str(len(changed)))
            # Use a different private dir for each; test denied before
            # creating output, so the same empty directory can be reused.
            self.out.mkdir(exist_ok=True)
            p = {**self.preview, **changed}
            with self.subTest(changed=changed), self.assertRaises(
                RevisionSandboxDenied
            ):
                self.rehearse(preview=p)
        p = deepcopy(self.preview)
        p["candidate_scene_text_diffs_not_applied"].append(
            deepcopy(p["candidate_scene_text_diffs_not_applied"][0])
        )
        with self.assertRaises(RevisionSandboxDenied):
            self.rehearse(preview=p)

    def test_changed_original_spoken_or_other_field_denied(self):
        original = self.source
        cases = [
            {"original_spoken": "forged original sentence"},
            {"candidate_spoken_not_applied": "x" * 186},
            {"fresh_voice_srt_mp4_a5_a6_verification_required": False},
            {"human_editor_must_accept_or_rewrite": False},
        ]
        for mod in cases:
            p = deepcopy(self.preview)
            p["candidate_scene_text_diffs_not_applied"][0].update(mod)
            with self.subTest(mod=mod), self.assertRaises(
                (RevisionSandboxDenied, ValueError)
            ):
                stage_candidate_episode(
                    p, episode_id=self.episode["id"], source=original
                )
        self.assertEqual(sha(CATALOG), self.before_catalog)

    def test_missing_or_failed_media_qa_does_not_create_release(self):
        self.mock_media_report[
            "decoded_actual_frame_caption_safezone_qa"
        ]["every_draft_caption_cue_visible_in_safe_zone"] = False
        with self.assertRaises(RevisionSandboxDenied):
            self.rehearse()
        self.assertFalse(
            (self.out / "PRIVATE-SANDBOX-TECHNICAL-REPORT.json").exists()
        )
        self.assertFalse(
            (self.out / self.episode["id"] /
             "owner-handoff-quarantined.json").exists()
        )

    def test_modified_original_media_during_render_is_denied(self):
        old_render = self.stub_render
        def tampering_render(ep, folder, mode):
            manifest = old_render(ep, folder, mode)
            (self.folder / AUDIO).write_bytes(b"CHANGED ORIGINAL")
            return manifest
        with patch(
            "scripts.branch3_a5_revision_sandbox.compile_private_revision_preview",
            return_value=self.preview
        ), patch(
            "scripts.branch3_a5_revision_sandbox.render_episode",
            side_effect=tampering_render
        ), patch(
            "scripts.branch3_a5_revision_sandbox.probe",
            return_value={}
        ), patch(
            "scripts.branch3_a5_revision_sandbox.validate_episode_report",
            return_value=self.mock_media_report
        ), self.assertRaisesRegex(RevisionSandboxDenied, "SOURCE_REVIEW_MEDIA"):
            rehearse_private_revision(
                self.review, selection="all",
                episode_id=self.episode["id"],
                edited_csv=self.edited_csv, output_root=self.out
            )


if __name__ == "__main__":
    unittest.main()
