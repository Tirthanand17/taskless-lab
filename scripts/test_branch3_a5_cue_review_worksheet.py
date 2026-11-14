"""Adversarial, no-media tests for CLIVOX 39-cue editorial worksheet."""
from __future__ import annotations

import copy
import csv
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from scripts.branch3_a5_cue_review_worksheet import (
    CueWorksheetBlocked, FIELDS, WORKSHEET, VIDEO, AUDIO, SRT,
    make_cue_review_worksheet, safe_csv_cell
)
from scripts.branch3_a6_original_handoff import (
    CATALOG, CHANNEL, digest, sha
)
from scripts.branch3_original_arcade_pilots import (
    draft_srt, validate_catalog
)


def handoff(episode: dict, folder: Path) -> dict:
    source = {
        "channel_id": CHANNEL,
        "episode_id": episode["id"],
        "exact_video_sha256": sha(folder / VIDEO),
        "exact_audio_sha256": sha(folder / AUDIO),
        "exact_captions_sha256": sha(folder / SRT),
        "owner_detached_signature_present": False,
        "exact_video_human_review_confirmed": False,
        "youtube_upload_authorized": False,
        "youtube_schedule_authorized": False,
        "youtube_publish_authorized": False,
    }
    source["packet_sha256"] = digest(source)
    return source


class CueHumanCorrectionWorksheetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.episodes = validate_catalog(json.loads(CATALOG.read_text("utf-8")))
        self.folders = []
        for episode in self.episodes:
            folder = self.root / episode["id"]
            folder.mkdir()
            (folder / VIDEO).write_bytes(b"synthetic-local-video-only")
            (folder / AUDIO).write_bytes(b"synthetic-local-audio-only")
            draft_srt(episode, folder / SRT)
            self.folders.append(folder)

    def test_all_three_exact_hash_bound_csv_and_39_local_cue_links(self):
        counts = []
        for episode, folder, expected in zip(
            self.episodes, self.folders, (8, 8, 23), strict=True
        ):
            markup, count = make_cue_review_worksheet(
                folder, episode, (folder / SRT).read_text("utf-8"),
                handoff(episode, folder)
            )
            self.assertEqual(count, expected)
            self.assertEqual(markup.count('class="cue-row"'), expected)
            self.assertEqual(markup.count("#t="), expected)
            self.assertNotIn("<script", markup.lower())
            self.assertNotIn("http://", markup.lower())
            self.assertNotIn("https://", markup.lower())
            self.assertIn("NOT a signed release", markup)
            csv_path = folder / WORKSHEET
            self.assertTrue(csv_path.is_file())
            with csv_path.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.assertEqual(tuple(reader.fieldnames), FIELDS)
                rows = list(reader)
            self.assertEqual(len(rows), expected)
            self.assertEqual([int(row["cue_number"]) for row in rows],
                             list(range(1, expected+1)))
            for row in rows:
                self.assertEqual(row["purpose"],
                                 "EDITORIAL_CORRECTION_ONLY_NOT_APPROVAL")
                self.assertEqual(row["exact_video_sha256"],
                                 sha(folder / VIDEO))
                self.assertEqual(row["exact_audio_sha256"],
                                 sha(folder / AUDIO))
                self.assertEqual(row["exact_srt_sha256"],
                                 sha(folder / SRT))
                for field in ("actual_words_and_pronunciation",
                              "subtitle_timing",
                              "caption_visual_readability",
                              "correction_required"):
                    self.assertEqual(row[field], "NOT_REVIEWED")
                self.assertEqual(row["suggested_replacement_caption"], "")
                self.assertEqual(row["reviewer_issue_notes"], "")
            counts.append(count)
        self.assertEqual(counts, [8, 8, 23])
        self.assertEqual(sum(counts), 39)

    def test_stale_exact_media_and_source_draft_rejected(self):
        ep = self.episodes[0]
        folder = self.folders[0]
        original = (folder / SRT).read_text("utf-8")
        pkt = handoff(ep, folder)
        (folder / SRT).write_text(original + "TAMPER", encoding="utf-8")
        with self.assertRaisesRegex(CueWorksheetBlocked,
                                    "EXACT_MEDIA_CHANGED"):
            make_cue_review_worksheet(
                folder, ep, (folder / SRT).read_text("utf-8"), pkt
            )
        (folder / SRT).write_text(original, encoding="utf-8")
        with self.assertRaisesRegex(CueWorksheetBlocked,
                                    "SRT_TEXT_CHANGED"):
            make_cue_review_worksheet(folder, ep, original + "TAMPER", pkt)
        (folder / VIDEO).write_bytes(b"replaced-video")
        with self.assertRaisesRegex(CueWorksheetBlocked,
                                    "EXACT_MEDIA_CHANGED"):
            make_cue_review_worksheet(folder, ep, original, pkt)

    def test_tampered_packet_approval_flag_and_wrong_channel_rejected(self):
        ep = self.episodes[0]
        folder = self.folders[0]
        text = (folder / SRT).read_text("utf-8")
        for field, value in (
            ("youtube_upload_authorized", True),
            ("youtube_schedule_authorized", True),
            ("youtube_publish_authorized", True),
            ("owner_detached_signature_present", True),
            ("exact_video_human_review_confirmed", True),
            ("channel_id", "OTHER"),
            ("exact_video_sha256", "0" * 64),
        ):
            packet = handoff(ep, folder)
            packet[field] = value
            packet["packet_sha256"] = digest({
                k: v for k, v in packet.items() if k != "packet_sha256"
            })
            with self.subTest(field=field), self.assertRaises(
                CueWorksheetBlocked
            ):
                make_cue_review_worksheet(folder, ep, text, packet)

    def test_missing_middle_sentence_not_a_valid_storyboard_review(self):
        ep = self.episodes[0]
        folder = self.folders[0]
        current = (folder / SRT).read_text("utf-8")
        # Edit a middle subtitle and rehash so this tests narrative
        # coherence, not only media digests.
        altered = current.replace("Red locks the room.", "Gold opens the room.")
        self.assertNotEqual(altered, current)
        (folder / SRT).write_text(altered, encoding="utf-8")
        with self.assertRaisesRegex(CueWorksheetBlocked, "SCRIPT_SRT_DIFFER"):
            make_cue_review_worksheet(
                folder, ep, altered, handoff(ep, folder)
            )

    def test_csv_formula_injection_escaped(self):
        for value in (
            "=HYPERLINK('x')", "+2+3", "-1+2", "@SUM(A1:A2)",
            "  =cmd", "\t=2+2", "\n=2+2"
        ):
            with self.subTest(value=value):
                safe = safe_csv_cell(value)
                self.assertTrue(safe.startswith("'"))
                buf = StringIO(newline="")
                csv.writer(buf).writerow([safe])
                self.assertTrue(next(csv.reader(StringIO(buf.getvalue())))
                                [0].startswith("'"))
        self.assertEqual(safe_csv_cell("Normal words"), "Normal words")

    def test_repeated_run_and_symlink_no_overwrite(self):
        ep, folder = self.episodes[0], self.folders[0]
        text = (folder / SRT).read_text("utf-8")
        packet = handoff(ep, folder)
        make_cue_review_worksheet(folder, ep, text, packet)
        with self.assertRaisesRegex(CueWorksheetBlocked, "NO_OVERWRITE"):
            make_cue_review_worksheet(folder, ep, text, packet)
        (folder / WORKSHEET).unlink()
        (folder / WORKSHEET).symlink_to(folder / SRT)
        with self.assertRaisesRegex(CueWorksheetBlocked, "NO_OVERWRITE"):
            make_cue_review_worksheet(folder, ep, text, packet)

    def test_wrong_episode_folder_rejected(self):
        ep = self.episodes[0]
        folder = self.folders[0]
        spoof = copy.deepcopy(ep)
        spoof["id"] = "clivox_original_unrelated_s00"
        with self.assertRaisesRegex(CueWorksheetBlocked, "EPISODE_ID"):
            make_cue_review_worksheet(
                folder, spoof, (folder / SRT).read_text("utf-8"),
                handoff(ep, folder)
            )


if __name__ == "__main__":
    unittest.main()
