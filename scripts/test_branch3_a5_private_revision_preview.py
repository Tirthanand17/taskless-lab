"""Synthetic and adversarial no-media CLIVOX private revision preview tests."""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.branch3_a5_private_revision_preview import (
    RevisionPreviewDenied, compile_private_revision_preview,
    predicted_cue_count, readable_words
)
from scripts.branch3_a5_cue_correction_intake import (
    CorrectionIntakeDenied, private_write_report
)
from scripts.branch3_a5_cue_review_worksheet import (
    FIELDS, WORKSHEET, VIDEO, AUDIO, SRT, make_cue_review_worksheet
)
from scripts.branch3_a6_original_handoff import (
    CATALOG, CHANNEL, PACKET_NAME, digest, sha
)
from scripts.branch3_original_arcade_pilots import draft_srt, validate_catalog


def sample_packet(ep: dict, folder: Path) -> dict:
    packet = {
        "channel_id": CHANNEL,
        "episode_id": ep["id"],
        "exact_video_sha256": sha(folder / VIDEO),
        "exact_audio_sha256": sha(folder / AUDIO),
        "exact_captions_sha256": sha(folder / SRT),
        "owner_detached_signature_present": False,
        "exact_video_human_review_confirmed": False,
        "youtube_upload_authorized": False,
        "youtube_schedule_authorized": False,
        "youtube_publish_authorized": False,
    }
    packet["packet_sha256"] = digest(packet)
    return packet


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


class PrivateRevisionPreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.episodes = validate_catalog(json.loads(CATALOG.read_text("utf-8")))
        self.folders = []
        for episode in self.episodes:
            folder = self.root / episode["id"]
            folder.mkdir()
            (folder / VIDEO).write_bytes(b"syn-fake-original-mp4")
            (folder / AUDIO).write_bytes(b"syn-fake-original-wav")
            draft_srt(episode, folder / SRT)
            packet = sample_packet(episode, folder)
            (folder / PACKET_NAME).write_text(json.dumps(packet), "utf-8")
            make_cue_review_worksheet(
                folder, episode, (folder / SRT).read_text("utf-8"), packet
            )
            self.folders.append(folder)
        self.edited = self.root / "PRIVATE-EDITED-COPY.csv"
        write_csv(self.edited, read_csv(self.folders[0] / WORKSHEET))

    def preview(self, *, index=0, selection="all", edited=None):
        with patch(
            "scripts.branch3_a5_cue_correction_intake.verify_unsigned_requests",
            return_value={
                "all_episode_video_audio_caption_metadata_and_qa_hashes_recomputed": True,
                "unsigned_checklist_files_matched_exact_media": True,
                "actual_human_video_approvals_verified": 0,
                "youtube_upload_authorized": False,
            }
        ) as check:
            out = compile_private_revision_preview(
                self.root, selection=selection,
                episode_id=self.episodes[index]["id"],
                edited_csv=edited if edited is not None else self.edited
            )
            check.assert_called_once_with(self.root, selection=selection)
        return out

    def suggest(self, row=0, text="An imaginary door tracks every choice."):
        rows = read_csv(self.edited)
        rows[row]["actual_words_and_pronunciation"] = "ISSUE"
        rows[row]["subtitle_timing"] = "OK"
        rows[row]["caption_visual_readability"] = "OK"
        rows[row]["correction_required"] = "YES"
        rows[row]["suggested_replacement_caption"] = text
        rows[row]["reviewer_issue_notes"] = "SYNTHETIC_EDITORIAL_TEST_ONLY"
        write_csv(self.edited, rows)

    def test_unchanged_csv_has_no_proposals_and_no_approval(self):
        report = self.preview()
        self.assertEqual(report["source_cue_count"], 8)
        self.assertEqual(report["candidate_spoken_rewrites_count"], 0)
        self.assertEqual(report["manual_editor_action_rows"], 0)
        self.assertEqual(report["pending_or_incomplete_rows"], 8)
        self.assertEqual(report["candidate_scene_text_diffs_not_applied"], [])
        for key in (
            "original_source_catalog_modified",
            "original_mp4_wav_srt_modified",
            "candidate_catalog_saved_to_public_repo",
            "automatic_speech_or_srt_regeneration_performed",
            "actual_word_level_alignment_verified",
            "human_reviewer_identity_authenticated",
            "owner_review_completed",
            "commercial_tool_or_audio_rights_approved",
            "a6_release_signed", "ready_to_upload",
            "ready_to_schedule", "ready_to_publish",
        ):
            self.assertIs(report[key], False, key)
        self.assertEqual(report["actual_youtube_api_calls"], 0)

    def test_one_valid_replacement_proposes_only_the_affected_scene(self):
        before_catalog = sha(CATALOG)
        before_files = {
            x: sha(self.folders[0] / x) for x in (VIDEO, AUDIO, SRT)
        }
        self.suggest()
        report = self.preview()
        self.assertEqual(report["candidate_spoken_rewrites_count"], 1)
        self.assertEqual(report["manual_editor_action_rows"], 0)
        self.assertEqual(report["pending_or_incomplete_rows"], 7)
        self.assertEqual(len(report["candidate_scene_text_diffs_not_applied"]), 1)
        diff = report["candidate_scene_text_diffs_not_applied"][0]
        self.assertEqual(diff["scene_number"], 1)
        self.assertEqual(diff["changed_cue_numbers"], [1])
        self.assertEqual(
            diff["original_spoken"], self.episodes[0]["beats"][0]["spoken"]
        )
        self.assertEqual(
            diff["candidate_spoken_not_applied"],
            "An imaginary door tracks every choice."
        )
        self.assertTrue(diff["fresh_voice_srt_mp4_a5_a6_verification_required"])
        self.assertTrue(diff["candidate_may_change_cue_index_and_all_timings"])
        self.assertEqual(before_catalog, sha(CATALOG))
        self.assertEqual(
            before_files,
            {x: sha(self.folders[0] / x) for x in (VIDEO, AUDIO, SRT)}
        )
        self.assertFalse(report["owner_review_completed"])
        self.assertFalse(report["ready_to_publish"])
        private = self.root / "my-editorial-diff.json"
        private_write_report(private, report)
        self.assertEqual(json.loads(private.read_text()), report)
        if os.name == "posix":
            self.assertEqual(private.stat().st_mode & 0o777, 0o600)
        with self.assertRaises(CorrectionIntakeDenied):
            private_write_report(private, report)

    def test_one_scene_two_caption_replacements_preserve_order(self):
        rows = read_csv(self.edited)
        self.assertEqual([r["scene_number"] for r in rows[:3]], ["1", "2", "2"])
        for index, text in (
            (1, "Red resets the game."),
            (2, "Blue stays silent, or you walk away."),
        ):
            rows[index]["actual_words_and_pronunciation"] = "ISSUE"
            rows[index]["subtitle_timing"] = "OK"
            rows[index]["caption_visual_readability"] = "OK"
            rows[index]["correction_required"] = "YES"
            rows[index]["suggested_replacement_caption"] = text
        write_csv(self.edited, rows)
        r = self.preview()
        self.assertEqual(r["candidate_spoken_rewrites_count"], 2)
        self.assertEqual(len(r["candidate_scene_text_diffs_not_applied"]), 1)
        scene = r["candidate_scene_text_diffs_not_applied"][0]
        self.assertEqual(scene["scene_number"], 2)
        self.assertEqual(scene["changed_cue_numbers"], [2, 3])
        self.assertEqual(
            scene["candidate_spoken_not_applied"],
            "Red resets the game. Blue stays silent, or you walk away."
        )

    def test_non_dialogue_issue_is_manual_even_with_suggested_text(self):
        rows = read_csv(self.edited)
        row = rows[0]
        row["actual_words_and_pronunciation"] = "OK"
        row["subtitle_timing"] = "ISSUE"
        row["caption_visual_readability"] = "OK"
        row["correction_required"] = "YES"
        row["suggested_replacement_caption"] = "Different on screen timing."
        row["reviewer_issue_notes"] = "Move caption in time, not voice."
        write_csv(self.edited, rows)
        report = self.preview()
        self.assertEqual(report["candidate_spoken_rewrites_count"], 0)
        self.assertEqual(report["manual_editor_action_rows"], 1)
        self.assertEqual(report["candidate_scene_text_diffs_not_applied"], [])
        self.assertEqual(
            report["private_manual_editor_tasks"][0]["reason"],
            "SUBTITLE_OR_LAYOUT_ONLY_REQUIRES_MANUAL_EDITOR"
        )

    def test_pronunciation_issue_without_spoken_replacement_needs_human(self):
        rows = read_csv(self.edited)
        row = rows[0]
        row["actual_words_and_pronunciation"] = "ISSUE"
        row["correction_required"] = "YES"
        row["reviewer_issue_notes"] = "Replay this name, no wording change."
        write_csv(self.edited, rows)
        out = self.preview()
        self.assertEqual(out["candidate_spoken_rewrites_count"], 0)
        self.assertEqual(out["manual_editor_action_rows"], 1)
        self.assertEqual(
            out["private_manual_editor_tasks"][0]["reason"],
            "NO_REPLACEMENT_DIALOGUE_PROPOSED"
        )

    def test_unrenderable_unsafe_or_url_replacement_denied(self):
        for text in (
            "https://example.invalid", "<img onerror=alert(1)>",
            "Turn \t the dial", "Turn \n the dial",
            "Say café and then leave.", "=1+2+3",
            "safe\\but-malformed",
            "x" * 186, "x" * 50,
        ):
            with self.subTest(text=text[:20]):
                self.suggest(text=text)
                with self.assertRaises(RevisionPreviewDenied):
                    self.preview()
        self.assertEqual(readable_words("An imaginary door opens."), "An imaginary door opens.")

    def test_srt_drift_requires_fresh_cue_timing_after_new_tts(self):
        self.suggest(text="Watch out. A much longer sentence describes the other doors, the approaching timer and the mystery of every choice.")
        report = self.preview()
        scene = report["candidate_scene_text_diffs_not_applied"][0]
        self.assertNotEqual(
            scene["original_scene_cue_count"],
            scene["predicted_rewrapped_cue_count_not_real_audio"]
        )
        self.assertTrue(scene["candidate_may_change_cue_index_and_all_timings"])
        self.assertTrue(scene["fresh_voice_srt_mp4_a5_a6_verification_required"])

    def test_other_episodes_remain_unmodified_and_correctly_counted(self):
        for index, expected in ((1, 8), (2, 23)):
            csv_path = self.root / f"editorial-{index}.csv"
            write_csv(csv_path, read_csv(self.folders[index] / WORKSHEET))
            output = self.preview(index=index, edited=csv_path)
            self.assertEqual(output["source_cue_count"], expected)
            self.assertEqual(output["candidate_spoken_rewrites_count"], 0)
            self.assertFalse(output["ready_to_publish"])
        with self.assertRaises(CorrectionIntakeDenied):
            self.preview(index=1, selection="one")

    def test_wrong_original_hashes_and_forged_approval_fail_at_intake(self):
        self.suggest()
        rows = read_csv(self.edited)
        rows[0]["exact_video_sha256"] = "f" * 64
        write_csv(self.edited, rows)
        with self.assertRaises(CorrectionIntakeDenied):
            self.preview()
        rows = read_csv(self.folders[0] / WORKSHEET)
        rows[0]["correction_required"] = "APPROVED_RELEASE"
        write_csv(self.edited, rows)
        with self.assertRaises(CorrectionIntakeDenied):
            self.preview()

    def test_predicted_wrapping_count_matches_real_generator_rule(self):
        self.assertEqual(predicted_cue_count("One two three."), 1)
        self.assertEqual(predicted_cue_count(
            "Red locks the room. Blue restarts the clock. Or you can do absolutely nothing."
        ), 2)


if __name__ == "__main__":
    unittest.main()
