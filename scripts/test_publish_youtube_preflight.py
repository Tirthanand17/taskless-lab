"""No-network YouTube release-preflight regression tests.

This suite never imports the Google API client or triggers remote publication.
"""
from __future__ import annotations
import datetime as dt
import unittest

from scripts.publish_youtube import (
    CAPTION_LANGUAGES, approval_allows_exact_video,
    caption_snippet_for_language, parse_scheduled_utc,
    verify_youtube_schedule,
)

HASH = "a" * 64


class CaptionLanguageTests(unittest.TestCase):
    def test_english_captions_are_english(self):
        self.assertEqual(
            caption_snippet_for_language("en", "verified_video_id"),
            {"videoId": "verified_video_id", "language": "en",
             "name": "English", "isDraft": False},
        )

    def test_hindi_captions_are_hindi(self):
        self.assertEqual(
            caption_snippet_for_language("hi", "verified_video_id"),
            {"videoId": "verified_video_id", "language": "hi",
             "name": "Hindi", "isDraft": False},
        )

    def test_unknown_caption_language_fails_closed(self):
        for language in ("", "unknown", "en-US", None, 3, "HI", "hi-IN"):
            with self.subTest(language=language), self.assertRaises(ValueError):
                caption_snippet_for_language(language, "fake")

    def test_missing_video_id_fails_closed(self):
        for video_id in ("", None, "   "):
            with self.subTest(video_id=video_id), self.assertRaises(ValueError):
                caption_snippet_for_language("hi", video_id)


class ApprovalTests(unittest.TestCase):
    def test_owner_preview_alone_is_not_all_five_gates(self):
        approval = {
            "approved_video_sha256": HASH,
            "final_video_approved": True,
            "owner_approval_observed": True,
            "human_voice_approved": False,
            "exact_captions_approved": False,
            "rights_cleared": False,
            "factual_review_approved": False,
        }
        self.assertFalse(approval_allows_exact_video(approval, HASH))

    def test_exact_sha_and_all_five_required(self):
        approved = {
            "approved_video_sha256": HASH,
            "human_voice_approved": True,
            "exact_captions_approved": True,
            "rights_cleared": True,
            "factual_review_approved": True,
            "final_video_approved": True,
        }
        self.assertTrue(approval_allows_exact_video(approved, HASH))
        self.assertFalse(approval_allows_exact_video(approved, "b" * 64))
        approved["owner_rejected_current_candidate"] = True
        self.assertFalse(approval_allows_exact_video(approved, HASH))


class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.now = dt.datetime(2026, 11, 2, 12, 0, tzinfo=dt.timezone.utc)

    def test_future_utc_schedule_required(self):
        self.assertEqual(
            parse_scheduled_utc("2026-11-02T12:16:00Z", now=self.now),
            "2026-11-02T12:16:00Z",
        )
        for when in ("2026-11-02T12:14:59Z", "2026-11-02T12:15:00Z",
                     "2026-11-02T12:16:00+00:00", "tomorrow"):
            with self.subTest(when=when), self.assertRaises(ValueError):
                parse_scheduled_utc(when, now=self.now)

    def test_remote_readback_checks_channel_and_private_status(self):
        schedule = "2026-11-02T12:16:00Z"
        channel = "UC" + "X" * 22
        video = {
            "snippet": {"channelId": channel},
            "status": {"privacyStatus": "private", "publishAt": schedule,
                       "uploadStatus": "processed"}
        }
        self.assertTrue(verify_youtube_schedule(video, schedule, channel))
        self.assertFalse(verify_youtube_schedule(video, schedule, "UC" + "Y" * 22))
        video["status"]["privacyStatus"] = "public"
        self.assertFalse(verify_youtube_schedule(video, schedule, channel))


if __name__ == "__main__":
    unittest.main()
