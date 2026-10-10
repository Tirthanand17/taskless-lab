"""Offline safety tests for FlowMinute's YouTube API publisher (no OAuth/API calls)."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import youtube_publisher as yp


CHANNEL = "UC" + "a" * 22
VID = "abcde123456"


class Call:
    def __init__(self, value):
        self.value = value
    def execute(self):
        return self.value


class FakeAPI:
    def __init__(self, *, wrong_title=False, wrong_channel=False, existing_publish=None, privacy="private"):
        self.calls = []
        self.video = {
            "id": VID, "snippet": {
                "title": "Safe AI walkthrough",
                "channelId": CHANNEL if not wrong_channel else "UC" + "b" * 22
            },
            "status": {
                "privacyStatus": privacy, "selfDeclaredMadeForKids": False,
                "license": "youtube", "publicStatsViewable": False,
                "containsSyntheticMedia": True,
            }
        }
        if wrong_title:
            self.video["snippet"]["title"] = "Another creator's video"
        if existing_publish:
            self.video["status"]["publishAt"] = existing_publish
    def channels(self): return self
    def videos(self): return self
    def list(self, **kwargs):
        self.calls.append(("list", kwargs))
        if kwargs.get("mine"):
            return Call({"items": [{"id": CHANNEL}]})
        if kwargs.get("id"):
            return Call({"items": [json.loads(json.dumps(self.video))]})
        raise AssertionError("Unexpected list call")
    def update(self, **kwargs):
        self.calls.append(("update", kwargs))
        self.video["status"] = kwargs["body"]["status"]
        return Call(json.loads(json.dumps(self.video)))


class TestPublisher(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        (self.base / "video.mp4").write_bytes(b"fake-video-content-not-a-real-video")
        (self.base / "episode.json").write_text(json.dumps({
            "id": "pilot_123", "title": "Safe AI walkthrough",
            "description": "Clearly labelled illustrative tutorial", "type": "short",
        }), encoding="utf-8")
        self.schedule = (dt.datetime.now(yp.UTC) + dt.timedelta(days=3)).isoformat()
        self.doc = {
            "episode_id": "pilot_123", "expected_channel_id": CHANNEL,
            "episode_path": "episode.json", "video_path": "video.mp4",
            "publish_at": self.schedule, "made_for_kids": False, "synthetic_media": True,
            "qa_approved": True, "captions_reviewed": False,
            "video_sha256": hashlib.sha256((self.base/"video.mp4").read_bytes()).hexdigest()
        }
        self.manifest = self.base / "release.json"
        self.save()
    def tearDown(self): self.tmp.cleanup()
    def save(self): self.manifest.write_text(json.dumps(self.doc), encoding="utf-8")
    def plan(self): return yp.validate_manifest(self.manifest)
    def ledger_path(self): return self.base / "secret-ledger.json"
    def reserve(self):
        with yp.exclusive_ledger(self.ledger_path()):
            ledger = yp.get_ledger(self.ledger_path())
            yp.create_upload_reservation(ledger, self.plan())
            ledger["episodes"]["pilot_123"].update({"state": "uploaded_private", "video_id": VID})
            yp.write_json_secure(self.ledger_path(), ledger)
    def test_happy_plan(self):
        plan = self.plan()
        self.assertEqual(plan["episode_id"], "pilot_123")
        self.assertTrue(plan["publish_at"].endswith("Z"))
        self.assertEqual(plan["expected_channel_id"], CHANNEL)
    def test_dry_run_no_oauth(self):
        self.assertEqual(yp.cli(["prepare", str(self.manifest)]), 0)
    def test_upload_is_gated(self):
        self.assertEqual(yp.cli(["upload", str(self.manifest), "--token-file", "missing"]), 2)
    def test_schedule_is_gated(self):
        self.assertEqual(yp.cli(["schedule", str(self.manifest), "--token-file", "missing"]), 2)
    def test_requires_QA(self):
        self.doc["qa_approved"] = False; self.save()
        with self.assertRaisesRegex(yp.PublisherError, "qa_approved"): self.plan()
    def test_requires_explicit_kids(self):
        self.doc.pop("made_for_kids"); self.save()
        with self.assertRaisesRegex(yp.PublisherError, "made_for_kids"): self.plan()
    def test_requires_explicit_synthetic_media(self):
        self.doc.pop("synthetic_media"); self.save()
        with self.assertRaisesRegex(yp.PublisherError, "synthetic_media"): self.plan()
    def test_no_past_publication(self):
        self.doc["publish_at"] = "2020-01-01T00:00:00+05:30"; self.save()
        with self.assertRaisesRegex(yp.PublisherError, "over 30 minutes"): self.plan()
    def test_no_naive_datetime(self):
        self.doc["publish_at"] = "2031-01-01T00:00:00"; self.save()
        with self.assertRaisesRegex(yp.PublisherError, "timezone offset"): self.plan()
    def test_strict_sha256(self):
        (self.base / "video.mp4").write_bytes(b"changed after approval")
        with self.assertRaisesRegex(yp.PublisherError, "SHA-256"): self.plan()
    def test_no_auto_subtitle_until_reviewed(self):
        (self.base / "subs.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nhello\n")
        self.doc["caption_path"] = "subs.srt"; self.save()
        with self.assertRaisesRegex(yp.PublisherError, "reviewed"): self.plan()
    def test_duplicate_upload_blocked(self):
        self.reserve()
        l = yp.get_ledger(self.ledger_path())
        with self.assertRaisesRegex(yp.PublisherError, "duplicate-upload"):
            yp.create_upload_reservation(l, self.plan())
    def test_stale_lock_blocks(self):
        lock = self.ledger_path().with_suffix(".json.lock")
        lock.write_text("old pid\n")
        with self.assertRaisesRegex(yp.PublisherError, "Publisher busy"):
            with yp.exclusive_ledger(self.ledger_path()): pass
    def test_preserved_status(self):
        status = {"license":"youtube","selfDeclaredMadeForKids":False,
                  "publicStatsViewable":False, "containsSyntheticMedia":True}
        x = yp.preserved_status(status, "2027-01-01T00:00:00Z")
        self.assertEqual(x["license"], "youtube")
        self.assertTrue(x["containsSyntheticMedia"])
        self.assertIs(x["selfDeclaredMadeForKids"], False)
        self.assertEqual(x["privacyStatus"], "private")
    def test_schedule_success_with_confirmed_readback(self):
        self.reserve()
        api = FakeAPI()
        yp.schedule_private(api, self.plan(), self.ledger_path())
        self.assertEqual(yp.get_ledger(self.ledger_path())["episodes"]["pilot_123"]["state"], "scheduled_verified")
        self.assertEqual([x[0] for x in api.calls].count("update"), 1)
        self.assertEqual(api.video["status"]["privacyStatus"], "private")
    def test_schedule_wrong_title_never_updates(self):
        self.reserve(); api=FakeAPI(wrong_title=True)
        with self.assertRaisesRegex(yp.PublisherError, "title"): yp.schedule_private(api,self.plan(),self.ledger_path())
        self.assertNotIn("update", [x[0] for x in api.calls])
    def test_schedule_wrong_channel_never_updates(self):
        self.reserve(); api=FakeAPI(wrong_channel=True)
        with self.assertRaisesRegex(yp.PublisherError, "different channel"):
            yp.schedule_private(api,self.plan(),self.ledger_path())
        self.assertNotIn("update", [x[0] for x in api.calls])
    def test_never_reschedule_existing(self):
        self.reserve(); api=FakeAPI(existing_publish="2027-01-01T00:00:00Z")
        with self.assertRaisesRegex(yp.PublisherError,"already has a schedule"):
            yp.schedule_private(api,self.plan(),self.ledger_path())
        self.assertNotIn("update", [x[0] for x in api.calls])
    def test_unresolved_state_prevents_retry(self):
        self.reserve(); api=FakeAPI(privacy="public")
        with self.assertRaisesRegex(yp.PublisherError,"not private"):
            yp.schedule_private(api,self.plan(),self.ledger_path())
        self.assertEqual(yp.get_ledger(self.ledger_path())["episodes"]["pilot_123"]["state"], "uploaded_private")


if __name__ == "__main__":
    unittest.main(verbosity=2)
