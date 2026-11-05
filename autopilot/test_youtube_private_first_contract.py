"""B4a 100% offline adversarial tests. Every passing fixture is FAKE, no publish."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone, timedelta
import unittest

from autopilot.youtube_private_first_contract import (
    ReleaseContractError, prepare_unapproved_intent, propose_first_attempt,
    note_returned_id, inspect_injected_video_readback,
)

CHANNEL = "UC" + "X" * 22
VIDEO = "abcDEF123_-"
CLOCK = datetime(2026, 11, 5, tzinfo=timezone.utc)
HASH = "a" * 64
SLOTS = {
    "short_am": "2026-11-06T05:30:00Z",
    "long": "2026-11-06T10:30:00Z",
    "short_pm": "2026-11-06T15:00:00Z",
}


def fixture(slot="short_am", **overrides):
    args = dict(
        episode_id="original_topic_20261106_001", slot=slot, channel_id=CHANNEL,
        final_mp4_sha256=HASH, captions_srt_sha256="b" * 64,
        thumbnail_sha256="c" * 64, source_review_context_sha256="d" * 64,
        title="Original independent educational demonstration",
        description="Accurate source-based and separately approved explanation",
        language="en", synthetic_media_disclosure=False,
        made_for_kids=False, publish_at_utc=SLOTS[slot], now=CLOCK,
    )
    args.update(overrides)
    return prepare_unapproved_intent(**args)


def fake_youtube(video_id=VIDEO):
    video = dict(
        id=video_id,
        snippet=dict(channelId=CHANNEL,
                     title="Original independent educational demonstration",
                     description="Accurate source-based and separately approved explanation"),
        status=dict(privacyStatus="private", uploadStatus="processed",
                    publishAt=SLOTS["short_am"], containsSyntheticMedia=False,
                    selfDeclaredMadeForKids=False),
        processingDetails=dict(processingStatus="succeeded"),
        contentDetails=dict(hasCustomThumbnail=True),
    )
    captions = dict(items=[dict(id="fake-caption-track",
                                snippet=dict(videoId=video_id, language="en",
                                             status="serving"))])
    return video, captions


class PrivateFirstIntentTests(unittest.TestCase):
    def test_exact_2_shorts_and_long_ist_slots(self):
        for slot in SLOTS:
            with self.subTest(slot=slot):
                intent = fixture(slot)
                self.assertTrue(intent.simulation_only)
                self.assertFalse(intent.real_owner_approval)
                self.assertFalse(intent.real_youtube_oauth)
                self.assertFalse(intent.release_authorized)
                self.assertEqual(len(intent.context_sha256), 64)

    def test_all_context_fields_digest_bound(self):
        base = fixture()
        self.assertEqual(fixture().context_sha256, base.context_sha256)
        for changes in (
            dict(episode_id="original_topic_20261106_002"),
            dict(final_mp4_sha256="e" * 64),
            dict(captions_srt_sha256="e" * 64),
            dict(thumbnail_sha256="e" * 64),
            dict(source_review_context_sha256="e" * 64),
            dict(title="Another original title"),
            dict(description="Another unique description"),
            dict(language="hi"),
            dict(synthetic_media_disclosure=True),
            dict(made_for_kids=True),
        ):
            with self.subTest(changes=changes):
                self.assertNotEqual(fixture(**changes).context_sha256, base.context_sha256)

    def test_invalid_or_inconsistent_inputs_fail_before_network(self):
        for changes in (
            dict(channel_id="fake"),
            dict(episode_id="../path"),
            dict(final_mp4_sha256="A" * 64),
            dict(captions_srt_sha256=""),
            dict(thumbnail_sha256=None),
            dict(source_review_context_sha256="z" * 64),
            dict(title=""),
            dict(title=" trailing "),
            dict(description=""),
            dict(language="en-US"),
            dict(made_for_kids="false"),
            dict(synthetic_media_disclosure=None),
            dict(publish_at_utc="2026-11-06T05:30:00+00:00"),
            dict(publish_at_utc="2026-11-06T11:00:00Z"),
            dict(publish_at_utc="2026-11-06T05:30:00Z", slot="long"),
            dict(now=datetime(2026, 11, 5)),
            dict(now=datetime(2026, 11, 6, 5, 30, tzinfo=timezone.utc)),
        ):
            with self.subTest(changes=changes), self.assertRaises(ReleaseContractError):
                fixture(**changes)

    def test_time_must_be_more_than_15_minutes_ahead(self):
        with self.assertRaises(ReleaseContractError):
            fixture(now=datetime(2026, 11, 6, 5, 15, tzinfo=timezone.utc))
        self.assertEqual(fixture(
            now=datetime(2026, 11, 6, 5, 14, 59, tzinfo=timezone.utc)
        ).slot, "short_am")


class OneAttemptOnlyTests(unittest.TestCase):
    def test_fence_is_recorded_before_any_network_and_must_not_retry(self):
        intent = fixture()
        fence = propose_first_attempt(intent, None)
        self.assertEqual(fence.state, "POSSIBLY_SENT_NO_RETRY")
        self.assertFalse(fence.remote_upload_proven)
        self.assertFalse(fence.release_authorized)
        with self.assertRaisesRegex(ReleaseContractError, "NEVER start"):
            propose_first_attempt(intent, fence)
        returned = note_returned_id(fence, VIDEO)
        with self.assertRaisesRegex(ReleaseContractError, "NEVER start"):
            propose_first_attempt(intent, returned)
        self.assertEqual(returned.state, "REMOTE_ID_REPORTED_UNVERIFIED")
        self.assertFalse(returned.remote_upload_proven)

    def test_no_id_and_uncertain_response_refuses_automatic_second_insert(self):
        fence = propose_first_attempt(fixture(), None)
        for video_id in (None, "", "invalid-id-with-spaces", "a" * 12):
            with self.subTest(video_id=video_id), self.assertRaises(ReleaseContractError):
                note_returned_id(fence, video_id)
        with self.assertRaises(ReleaseContractError):
            propose_first_attempt(fixture(), fence)

    def test_duplicate_id_or_transition_not_allowed(self):
        fence = note_returned_id(propose_first_attempt(fixture(), None), VIDEO)
        with self.assertRaises(ReleaseContractError):
            note_returned_id(fence, VIDEO)

    def test_unapproved_or_untyped_intent_rejected(self):
        with self.assertRaises(ReleaseContractError):
            propose_first_attempt("forge", None)
        with self.assertRaises(ReleaseContractError):
            propose_first_attempt(replace(fixture(), simulation_only=False), None)


class RemoteEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.intent = fixture()
        self.fence = note_returned_id(propose_first_attempt(self.intent, None), VIDEO)

    def test_all_matching_mock_youtube_fields_still_never_authorize_release(self):
        v, c = fake_youtube()
        state = inspect_injected_video_readback(self.intent, self.fence, v, c)
        self.assertTrue(state["synthetic_api_response_contract_matches"])
        for key, value in state.items():
            if key != "synthetic_api_response_contract_matches":
                self.assertIs(value, False, key)

    def test_individual_remote_video_mismatches_fail(self):
        v, c = fake_youtube()
        changes = [
            ("id", "wrong_ID01"),
            ("snippet.channelId", "UC" + "Y" * 22),
            ("snippet.title", "Replaced metadata"),
            ("snippet.description", "Altered description"),
            ("status.privacyStatus", "public"),
            ("status.privacyStatus", "unlisted"),
            ("status.uploadStatus", "uploaded"),
            ("status.publishAt", "2026-11-06T05:30:00+00:00"),
            ("status.publishAt", "2026-11-05T05:30:00Z"),
            ("status.publishAt", "invalid"),
            ("status.containsSyntheticMedia", True),
            ("status.containsSyntheticMedia", None),
            ("status.selfDeclaredMadeForKids", True),
            ("status.selfDeclaredMadeForKids", "false"),
            ("processingDetails.processingStatus", "processing"),
            ("contentDetails.hasCustomThumbnail", False),
        ]
        for path, value in changes:
            with self.subTest(path=path):
                bad = deepcopy(v)
                parent, field = (path.split(".") + [None])[:2] if "." in path else (None, path)
                if parent:
                    bad[parent][field] = value
                else:
                    bad[field] = value
                state = inspect_injected_video_readback(self.intent, self.fence, bad, c)
                self.assertFalse(state["synthetic_api_response_contract_matches"])
                self.assertFalse(state["release_authorized"])

    def test_caps_wrong_video_language_status_or_count_fail(self):
        v, c = fake_youtube()
        for mutation in ("wrong_video", "language", "pending", "empty", "duplicate", "missing"):
            bad = deepcopy(c)
            if mutation == "wrong_video":
                bad["items"][0]["snippet"]["videoId"] = "wrong_ID01"
            if mutation == "language":
                bad["items"][0]["snippet"]["language"] = "hi"
            if mutation == "pending":
                bad["items"][0]["snippet"]["status"] = "syncing"
            if mutation == "empty":
                bad["items"] = []
            if mutation == "duplicate":
                bad["items"].append(deepcopy(bad["items"][0]))
            if mutation == "missing":
                del bad["items"][0]["snippet"]
            with self.subTest(mutation=mutation):
                state = inspect_injected_video_readback(self.intent, self.fence, v, bad)
                self.assertFalse(state["synthetic_api_response_contract_matches"])
                self.assertFalse(state["release_authorized"])

    def test_missing_service_response_or_mismatched_context_never_passes(self):
        v, c = fake_youtube()
        for fake in ({}, {"snippet": {}}, None, [], "hello"):
            with self.subTest(fake=fake):
                if fake is None:
                    with self.assertRaises(ReleaseContractError):
                        inspect_injected_video_readback(self.intent, self.fence, fake, c)
                else:
                    self.assertFalse(inspect_injected_video_readback(
                        self.intent, self.fence, fake, c
                    )["synthetic_api_response_contract_matches"])
        with self.assertRaises(ReleaseContractError):
            inspect_injected_video_readback(
                self.intent, replace(self.fence, context_sha256="f" * 64), v, c
            )
        with self.assertRaises(ReleaseContractError):
            inspect_injected_video_readback(
                self.intent, propose_first_attempt(self.intent, None), v, c
            )


if __name__ == "__main__":
    unittest.main()
