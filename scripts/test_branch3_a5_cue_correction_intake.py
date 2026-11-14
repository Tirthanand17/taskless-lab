"""No-network, adversarial CLIVOX correction intake tests; synthetic assets only.

CI must never import real private reviewer notes, copyrighted video or creds.
The real A6 package checker is always invoked by production but patched in
synthetic tests because fake MP4s are intentionally not FFprobe-decodable.
"""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.branch3_a5_cue_correction_intake import (
    CorrectionIntakeDenied, ASSESSMENTS, compile_private_issue_plan,
    private_write_report
)
from scripts.branch3_a5_cue_review_worksheet import (
    FIELDS, WORKSHEET, VIDEO, SRT, AUDIO, make_cue_review_worksheet
)
from scripts.branch3_original_arcade_pilots import draft_srt, validate_catalog
from scripts.branch3_a6_original_handoff import (
    CATALOG, CHANNEL, PACKET_NAME, digest, sha, ROOT
)


def fake_packet(ep: dict, folder: Path) -> dict:
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
    with path.open("r", newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as dest:
        writer = csv.DictWriter(dest, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


class OfflineCorrectionIntakeTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        self.episodes = validate_catalog(json.loads(CATALOG.read_text("utf-8")))
        self.folders = []
        for ep in self.episodes:
            folder = self.root / ep["id"]
            folder.mkdir()
            (folder / VIDEO).write_bytes(b"synthetic-review-video-not-real")
            (folder / AUDIO).write_bytes(b"synthetic-review-original-voice")
            draft_srt(ep, folder / SRT)
            packet = fake_packet(ep, folder)
            (folder / PACKET_NAME).write_text(
                json.dumps(packet), encoding="utf-8"
            )
            make_cue_review_worksheet(
                folder, ep, (folder / SRT).read_text("utf-8"), packet
            )
            self.folders.append(folder)
        self.edited = self.root / "REVIEWER-EDITED-DO-NOT-UPLOAD.csv"
        write_csv(self.edited, read_csv(self.folders[0] / WORKSHEET))

    def verified(self):
        return patch(
            "scripts.branch3_a5_cue_correction_intake.verify_unsigned_requests",
            return_value={
                "all_episode_video_audio_caption_metadata_and_qa_hashes_recomputed": True,
                "unsigned_checklist_files_matched_exact_media": True,
                "actual_human_video_approvals_verified": 0,
                "youtube_upload_authorized": False,
            }
        )

    def compile(self, index=0, *, selection="all", edited=None):
        with self.verified() as proof:
            report = compile_private_issue_plan(
                self.root, selection=selection,
                episode_id=self.episodes[index]["id"],
                edited_csv=edited or self.edited
            )
            proof.assert_called_once_with(self.root, selection=selection)
        return report

    def test_untouched_worksheet_stays_pending_and_never_approved(self):
        p = self.compile()
        self.assertEqual(p["total_cue_rows"], 8)
        self.assertEqual(p["pending_or_incomplete_rows"], 8)
        self.assertEqual(p["issue_rows"], 0)
        self.assertEqual(p["proposed_editorial_changes_private"], [])
        self.assertFalse(p["human_review_identity_authenticated"])
        self.assertFalse(p["owner_review_completed"])
        self.assertFalse(p["ready_to_upload"])
        self.assertFalse(p["ready_to_schedule"])
        self.assertFalse(p["ready_to_publish"])
        self.assertEqual(p["actual_youtube_api_calls"], 0)

    def test_only_real_issue_cells_generate_a_private_action_plan(self):
        rows = read_csv(self.edited)
        target = rows[2]
        target["actual_words_and_pronunciation"] = "ISSUE"
        target["subtitle_timing"] = "OK"
        target["caption_visual_readability"] = "OK"
        target["correction_required"] = "YES"
        target["suggested_replacement_caption"] = "Let's try the blue door."
        target["reviewer_issue_notes"] = "VOICE: mispronounces the door choice."
        write_csv(self.edited, rows)
        p = self.compile()
        self.assertEqual(p["pending_or_incomplete_rows"], 7)
        self.assertEqual(p["self_reported_filled_rows_not_authenticated"], 1)
        self.assertEqual(p["issue_rows"], 1)
        issue = p["proposed_editorial_changes_private"][0]
        self.assertEqual(issue["cue_number"], 3)
        self.assertEqual(issue["issue_categories"],
                         ["actual_words_and_pronunciation"])
        self.assertEqual(issue["suggested_replacement_caption"],
                         "Let's try the blue door.")
        self.assertTrue(
            issue["requires_source_script_voice_srt_mp4_regeneration"]
        )
        self.assertFalse(p["owner_review_completed"])
        target_path = self.root / "PRIVATE-CORRECTION-PLAN.json"
        private_write_report(target_path, p)
        self.assertTrue(target_path.is_file())
        self.assertEqual(json.loads(target_path.read_text()), p)
        if os.name == "posix":
            self.assertEqual(target_path.stat().st_mode & 0o777, 0o600)
        with self.assertRaisesRegex(CorrectionIntakeDenied, "NO_OVERWRITE"):
            private_write_report(target_path, p)

    def test_all_rows_filled_still_is_not_verified_human_review(self):
        rows = read_csv(self.edited)
        for row in rows:
            for name in ASSESSMENTS:
                row[name] = "OK"
            row["correction_required"] = "NO"
        write_csv(self.edited, rows)
        p = self.compile()
        self.assertEqual(p["total_cue_rows"], 8)
        self.assertEqual(p["pending_or_incomplete_rows"], 0)
        self.assertEqual(p["self_reported_filled_rows_not_authenticated"], 8)
        self.assertEqual(p["issue_rows"], 0)
        self.assertFalse(p["human_review_identity_authenticated"])
        self.assertFalse(p["owner_review_completed"])
        self.assertFalse(p["rights_licenses_validated"])
        self.assertFalse(p["ready_to_publish"])

    def test_all_three_episode_cue_counts(self):
        for index, count in enumerate((8, 8, 23)):
            path = self.root / ("edited-" + str(index) + ".csv")
            write_csv(path, read_csv(self.folders[index] / WORKSHEET))
            r = self.compile(index, edited=path)
            self.assertEqual(r["total_cue_rows"], count)
            self.assertEqual(r["pending_or_incomplete_rows"], count)
            self.assertFalse(r["ready_to_publish"])
        with self.assertRaisesRegex(
            CorrectionIntakeDenied, "EPISODE_NOT_IN_VERIFIED_SELECTION"
        ):
            self.compile(1, selection="one")

    def test_immutable_identity_time_script_and_sha_cannot_be_edited(self):
        original = read_csv(self.edited)
        for field, value in (
            ("purpose", "OWNER_APPROVED"),
            ("episode_id", self.episodes[1]["id"]),
            ("exact_video_sha256", "0" * 64),
            ("exact_audio_sha256", "1" * 64),
            ("exact_srt_sha256", "2" * 64),
            ("cue_number", "999"),
            ("scene_number", "9"),
            ("cue_start", "00:00:00.001"),
            ("cue_end", "00:00:35.999"),
            ("draft_caption", "<script>alert(1)</script>"),
        ):
            modified = [dict(row) for row in original]
            modified[0][field] = value
            write_csv(self.edited, modified)
            with self.subTest(field=field), self.assertRaisesRegex(
                CorrectionIntakeDenied, "IMMUTABLE_CUE_CHANGED"
            ):
                self.compile()
        write_csv(self.edited, original)

    def test_invalid_review_claims_or_unsupported_states_fail_closed(self):
        original = read_csv(self.edited)
        examples = (
            {"actual_words_and_pronunciation": "YES"},
            {"correction_required": "YES"},
            {"correction_required": "NO"},
            {"correction_required": "NO",
             "actual_words_and_pronunciation": "ISSUE",
             "subtitle_timing": "OK", "caption_visual_readability": "OK"},
            {"correction_required": "YES",
             "actual_words_and_pronunciation": "ISSUE",
             "subtitle_timing": "OK", "caption_visual_readability": "OK"},
            {"correction_required": "NOT_REVIEWED",
             "reviewer_issue_notes": "not actually listened"},
            {"correction_required": "NOT_REVIEWED",
             "subtitle_timing": "OK"},
        )
        for variant in examples:
            rows = [dict(row) for row in original]
            rows[0].update(variant)
            write_csv(self.edited, rows)
            with self.subTest(variant=variant), self.assertRaises(
                CorrectionIntakeDenied
            ):
                self.compile()

    def test_partial_fix_is_tracked_as_pending_not_approved(self):
        rows = read_csv(self.edited)
        rows[0]["actual_words_and_pronunciation"] = "ISSUE"
        rows[0]["correction_required"] = "YES"
        rows[0]["reviewer_issue_notes"] = "requires speech correction"
        write_csv(self.edited, rows)
        p = self.compile()
        self.assertEqual(p["issue_rows"], 1)
        self.assertEqual(p["pending_or_incomplete_rows"], 8)
        self.assertEqual(p["self_reported_filled_rows_not_authenticated"], 0)
        self.assertFalse(p["owner_review_completed"])

    def test_deleted_duplicate_extra_columns_baseline_injection_rejected(self):
        source = read_csv(self.edited)
        for modified in (
            source[:-1],
            [source[0], *source],
            [source[0], source[0], *source[2:]],
        ):
            write_csv(self.edited, modified)
            with self.assertRaises(CorrectionIntakeDenied):
                self.compile()
        write_csv(self.edited, source)
        # A forged original template cannot hide a wrong cue timestamp.
        template = self.folders[0] / WORKSHEET
        original = read_csv(template)
        corrupted = [dict(row) for row in original]
        corrupted[1]["cue_start"] = "00:00:59.000"
        write_csv(template, corrupted)
        with self.assertRaisesRegex(
            CorrectionIntakeDenied, "IMMUTABLE_CUE_CHANGED"
        ):
            self.compile()
        write_csv(template, original)
        with self.edited.open("a", encoding="utf-8") as dst:
            dst.write("garbage,extra,columns\n")
        with self.assertRaises(CorrectionIntakeDenied):
            self.compile()

    def test_verified_owner_request_or_packet_tamper_rejected(self):
        with patch(
            "scripts.branch3_a5_cue_correction_intake.verify_unsigned_requests",
            return_value={
                "all_episode_video_audio_caption_metadata_and_qa_hashes_recomputed": False,
                "unsigned_checklist_files_matched_exact_media": False,
                "actual_human_video_approvals_verified": 1,
                "youtube_upload_authorized": True,
            }
        ), self.assertRaisesRegex(CorrectionIntakeDenied, "A6_MEDIA"):
            compile_private_issue_plan(
                self.root, selection="all",
                episode_id=self.episodes[0]["id"], edited_csv=self.edited
            )
        packet_path = self.folders[0] / PACKET_NAME
        old = json.loads(packet_path.read_text())
        changed = {**old, "youtube_upload_authorized": True}
        packet_path.write_text(json.dumps(changed))
        with self.assertRaisesRegex(
            CorrectionIntakeDenied, "WRONG_PACKET_IDENTITY_OR_APPROVAL"
        ):
            self.compile()

    def test_source_change_and_same_file_and_symlink_rejected(self):
        with self.assertRaisesRegex(
            CorrectionIntakeDenied, "REQUIRES_SEPARATE_EDITED_COPY"
        ):
            self.compile(edited=self.folders[0] / WORKSHEET)
        symlink = self.root / "edited-symlink.csv"
        symlink.symlink_to(self.edited)
        with self.assertRaisesRegex(CorrectionIntakeDenied, "SYMLINK"):
            self.compile(edited=symlink)
        original = (self.folders[0] / SRT).read_text("utf-8")
        mutated = original.replace("Red locks the room.", "Blue opens the room.")
        self.assertNotEqual(mutated, original)
        (self.folders[0] / SRT).write_text(mutated, encoding="utf-8")
        # Production A6 verification would detect hash tampering; independent
        # source-vs-script comparison must also reject when A6 is mocked.
        with self.assertRaisesRegex(
            CorrectionIntakeDenied, "SOURCE_SCRIPT_DIFFERS"
        ):
            self.compile()

    def test_private_writer_blocks_source_repo_and_symlink(self):
        report = self.compile()
        with self.assertRaises(CorrectionIntakeDenied):
            private_write_report(ROOT / "unsafe-public-note.json", report)
        target = self.root / "private.json"
        target.symlink_to(self.edited)
        with self.assertRaisesRegex(CorrectionIntakeDenied, "SYMLINK"):
            private_write_report(target, report)


if __name__ == "__main__":
    unittest.main()
