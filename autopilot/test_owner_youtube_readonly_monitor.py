"""Offline adversarial tests: no Google/network/account write access."""
import datetime as dt
import json
import unittest
from unittest.mock import patch
from autopilot.owner_youtube_readonly_monitor import (
    CHANNEL, OwnerYouTubeReader, ReleaseAuditError, audit_day,
)

DAY = "2026-10-20"
TITLES = {"short_morning": "English Safe Agent", "long": "Hindi Grocery Tutor", "short_evening": "Hindi Safe Agent"}
IDS = {"short_morning": "AbCdEfGhIj0", "long": "abcdefghijk", "short_evening": "KlMnOpQrSt1"}
AT = {"short_morning": "2026-10-20T05:30:00Z", "long": "2026-10-20T10:30:00Z", "short_evening": "2026-10-20T15:00:00Z"}


def manifest(missing_long=False):
    return {k: {"video_id": None if missing_long and k == "long" else IDS[k], "title": TITLES[k]}
            for k in TITLES}


class FakeOwner(OwnerYouTubeReader):
    def __init__(self, *, channel=CHANNEL, privacy="private", processing="succeeded",
                 upload="processed", missing_at=False, wrong_title=False):
        super().__init__("unit-test-not-real-token-123")
        self.channel = channel
        self.privacy = privacy
        self.processing = processing
        self.upload = upload
        self.missing_at = missing_at
        self.wrong_title = wrong_title
        self.calls = []

    def _get(self, path, params):
        self.calls.append((path, params))
        if path == "channels":
            return {"items": [{"id": self.channel}]}
        slot = next(s for s, k in IDS.items() if k == params["id"])
        return {"items": [{"id": params["id"],
                "snippet": {"channelId": self.channel,
                            "title": "INCORRECT" if self.wrong_title else TITLES[slot]},
                "status": {"privacyStatus": self.privacy, "uploadStatus": self.upload,
                           **({} if self.missing_at else {"publishAt": AT[slot]})},
                "processingDetails": {"processingStatus": self.processing}}]}


NOW = dt.datetime(2026, 10, 19, 17, tzinfo=dt.timezone.utc)


class ReadOnlyReleaseTests(unittest.TestCase):
    def test_exact_three_times_and_confirmed_video_ids(self):
        client = FakeOwner()
        r = audit_day(day=DAY, planned=manifest(), reader=client, now=NOW)
        self.assertEqual(r["verified_scheduled_count"], 3)
        self.assertEqual([x["publish_at_utc"] for x in r["lanes"]], list(AT.values()))
        self.assertFalse(r["publishing_authorized"])
        self.assertFalse(r["cloud_autopilot_ready"])
        self.assertEqual([x[0] for x in client.calls].count("channels"), 1)
        self.assertEqual([x[0] for x in client.calls].count("videos"), 3)

    def test_missing_long_is_not_counted_or_fetched(self):
        client = FakeOwner()
        r = audit_day(day=DAY, planned=manifest(missing_long=True), reader=client, now=NOW)
        self.assertEqual(r["verified_platform_state_count"], 2)
        self.assertEqual(r["lanes"][1]["status"], "MISSING_VIDEO")
        self.assertEqual([x[0] for x in client.calls].count("videos"), 2)

    def test_duplicate_id_rejected_before_account_query(self):
        m = manifest()
        m["long"]["video_id"] = m["short_morning"]["video_id"]
        client = FakeOwner()
        with self.assertRaisesRegex(ReleaseAuditError, "DUPLICATE"):
            audit_day(day=DAY, planned=m, reader=client, now=NOW)
        self.assertEqual(client.calls, [])

    def test_strict_manifest_no_extra_flags_or_wrong_id(self):
        for bad in (dict(manifest(), fourth={}),
                    {**manifest(), "long": {"video_id": "bad", "title": "a"}},
                    {**manifest(), "long": {"video_id": None, "title": TITLES["long"], "uploaded": True}}):
            with self.subTest(bad=bad), self.assertRaises(ReleaseAuditError):
                audit_day(day=DAY, planned=bad, reader=FakeOwner(), now=NOW)

    def test_unverified_account_blocks_all_even_missing_video(self):
        c = FakeOwner(channel="UC1234567890123456789012")
        r = audit_day(day=DAY, planned=manifest(missing_long=True), reader=c, now=NOW)
        self.assertEqual(r["verified_platform_state_count"], 0)
        self.assertFalse(r["account_verified"])
        self.assertEqual(len(c.calls), 1)

    def test_wrong_title_processing_upload_held(self):
        for kwargs in (dict(wrong_title=True), dict(processing="processing"),
                       dict(upload="uploaded"), dict(missing_at=True)):
            with self.subTest(kwargs=kwargs):
                r = audit_day(day=DAY, planned=manifest(), reader=FakeOwner(**kwargs), now=NOW)
                self.assertEqual(r["verified_platform_state_count"], 0)

    def test_past_private_scheduled_is_not_public(self):
        late = dt.datetime(2026, 10, 21, tzinfo=dt.timezone.utc)
        r = audit_day(day=DAY, planned=manifest(), reader=FakeOwner(), now=late)
        self.assertEqual(r["verified_platform_state_count"], 0)

    def test_public_is_only_owner_side_no_playability_claim(self):
        late = dt.datetime(2026, 10, 21, tzinfo=dt.timezone.utc)
        r = audit_day(day=DAY, planned=manifest(), reader=FakeOwner(privacy="public"), now=late)
        self.assertEqual(r["verified_public_status_count"], 3)
        self.assertFalse(r["anonymous_playability_verified"])
        self.assertFalse(r["cloud_autopilot_ready"])

    def test_public_before_release_is_not_valid(self):
        r = audit_day(day=DAY, planned=manifest(), reader=FakeOwner(privacy="public"), now=NOW)
        self.assertEqual(r["verified_platform_state_count"], 0)

    def test_wrong_clock_and_date(self):
        for bad in ("2026-10-20Z", "tomorrow", "2026-10-22T00:00:00"):
            with self.subTest(bad=bad), self.assertRaises(ReleaseAuditError):
                audit_day(day=bad, planned=manifest(), reader=FakeOwner(), now=NOW)
        with self.assertRaises(ReleaseAuditError):
            audit_day(day=DAY, planned=manifest(), reader=FakeOwner(), now=dt.datetime(2026, 10, 19))

    def test_bearer_never_disclosed_in_errors(self):
        c = FakeOwner()
        def failure(*args):
            raise RuntimeError("secret: sensitive-token-123")
        c._get = failure
        r = audit_day(day=DAY, planned=manifest(), reader=c, now=NOW)
        self.assertEqual(r["verified_platform_state_count"], 0)
        self.assertNotIn("sensitive", json.dumps(r))

    def test_wrong_reader_type_refused(self):
        with self.assertRaises(ReleaseAuditError):
            audit_day(day=DAY, planned=manifest(), reader=object(), now=NOW)

    def test_reader_input_rejects_short_tokens(self):
        with self.assertRaises(ReleaseAuditError):
            OwnerYouTubeReader("no")

    def test_endpoint_and_video_id_allowlist(self):
        c = FakeOwner()
        with self.assertRaises(ReleaseAuditError):
            OwnerYouTubeReader("long-enough-fake-access-token")._get("bad", {})
        with self.assertRaises(ReleaseAuditError):
            c.video("../etc/passwd")

    def test_read_only_http_redacts_errors(self):
        c = OwnerYouTubeReader("long-enough-fake-access-token")
        class BadOpener:
            def open(self, req, timeout):
                raise OSError("secret header: long-enough-fake-access-token")
        with patch("autopilot.owner_youtube_readonly_monitor.build_opener", return_value=BadOpener()):
            with self.assertRaisesRegex(ReleaseAuditError, "OWNER_YOUTUBE_READ_FAILED") as ctx:
                c._get("channels", {"part": "id", "mine": "true"})
            self.assertNotIn("fake-access-token", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
