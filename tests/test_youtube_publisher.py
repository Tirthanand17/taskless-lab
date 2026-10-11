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
    def __init__(self, *, wrong_title=False, wrong_channel=False, existing_publish=None, privacy="private", processing="succeeded"):
        self.calls = []
        self.video = {
            "id": VID, "snippet": {
                "title": "Safe AI walkthrough",
                "channelId": CHANNEL if not wrong_channel else "UC" + "b" * 22
            },
            "processingDetails": {"processingStatus": processing},
            "status": {
                "uploadStatus": "processed" if processing=="succeeded" else "uploaded",
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
    def queue_fixture(self, *, privacy="private", schedule_delta=0, title="Safe AI walkthrough"):
        date = (dt.datetime.now(yp.UTC) + dt.timedelta(days=3)).isoformat()
        expected = yp.as_rfc3339(yp.parse_utc(date))
        vid=VID
        receipts=self.base/"receipts"
        receipts.mkdir(exist_ok=True)
        (receipts/"pilot_123.json").write_text(json.dumps({
            "id":"pilot_123", "date_local":"2030-10-12",
            "youtube_video_id":vid, "title_in_studio":"Safe AI walkthrough",
            "scheduled_local":date
        }))
        class QueueAPI:
            def channels(self): return self
            def videos(self): return self
            def list(self, **kwargs):
                if kwargs.get("mine"): return Call({"items":[{"id":CHANNEL}]})
                return Call({"items":[{
                    "id":vid, "snippet":{"channelId":CHANNEL,"title":title},
                    "status":{
                        "uploadStatus":"processed","privacyStatus":privacy,
                        "publishAt":yp.as_rfc3339(yp.parse_utc(date) +
                                  dt.timedelta(minutes=schedule_delta))
                    }
                }]})
        return QueueAPI(), receipts

    def test_read_only_queue_reports_correct_schedule(self):
        api, folder = self.queue_fixture()
        report = yp.verify_receipt_queue(api, folder, CHANNEL)
        self.assertEqual(report["checked"], 1)
        self.assertEqual(report["passed"], 1)
        self.assertEqual(report["items"][0]["status"], "scheduled_verified")

    def test_read_only_queue_detects_wrong_time(self):
        api, folder = self.queue_fixture(schedule_delta=60)
        report = yp.verify_receipt_queue(api, folder, CHANNEL)
        self.assertEqual(report["needs_attention"],1)
        self.assertEqual(report["items"][0]["status"], "schedule_mismatch")

    def test_read_only_queue_detects_early_public(self):
        api, folder = self.queue_fixture(privacy="public")
        report = yp.verify_receipt_queue(api, folder, CHANNEL)
        self.assertEqual(report["needs_attention"],1)

    def test_default_ledger_is_home_anchored(self):
        # Desktop Commander executes commands from its own node_modules directory.
        self.assertTrue(yp.DEFAULT_LEDGER.is_absolute())
        self.assertEqual(yp.DEFAULT_LEDGER,
                         Path.home() / ".flowminute-private" / "youtube-ledger.json")

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
    def test_srt_accepts_sequential_timed_cues(self):
        p = self.base / "captions.srt"
        p.write_text("1\n00:00:00,000 --> 00:00:01,000\nFirst caption\n\n"
                     "2\n00:00:01,200 --> 00:00:02,300\nSecond caption\n",
                     encoding="utf-8")
        self.assertEqual(yp.validate_srt_file(p), 2)
        self.doc["caption_path"] = "captions.srt"
        self.doc["captions_reviewed"] = True
        self.doc["caption_sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
        self.save()
        self.assertEqual(self.plan()["caption_path"], p)

    def test_srt_rejects_overlaps(self):
        p = self.base / "bad.srt"
        p.write_text("1\n00:00:00,000 --> 00:00:03,000\nOne\n\n"
                     "2\n00:00:02,000 --> 00:00:04,000\nTwo\n")
        with self.assertRaisesRegex(yp.PublisherError, "overlap"):
            yp.validate_srt_file(p)

    def test_srt_rejects_bad_timestamp_format(self):
        p = self.base / "bad.srt"
        p.write_text("1\n00:00:00.000 --> 00:00:01.000\nWrong separator\n")
        with self.assertRaisesRegex(yp.PublisherError, "HH:MM:SS"):
            yp.validate_srt_file(p)

    def test_utf8_description_byte_limit(self):
        ep = self.base / "episode.json"
        meta=json.loads(ep.read_text())
        meta["description"] = "é"*3000
        ep.write_text(json.dumps(meta),encoding="utf-8")
        with self.assertRaisesRegex(yp.PublisherError, "byte limit"):
            self.plan()

    def test_metadata_angle_brackets_blocked(self):
        ep=self.base/"episode.json"
        meta=json.loads(ep.read_text())
        meta["title"]="A <B> headline"
        ep.write_text(json.dumps(meta),encoding="utf-8")
        with self.assertRaisesRegex(yp.PublisherError, "angle brackets"):
            self.plan()

    def test_offline_oauth_health_never_prints_secrets(self):
        t=self.base/"publish_token.json"
        t.write_text(json.dumps({
            "scopes":[yp.WRITE_SCOPE],
            "refresh_token":"SECRET_REFRESH_DO_NOT_PRINT",
            "token":"SECRET_ACCESS_DO_NOT_PRINT",
            "expiry":"2026-10-11T16:01:00Z"
        }))
        report=yp.credential_health(t,expected_scope=yp.WRITE_SCOPE)
        self.assertTrue(report["publish_scope"])
        self.assertTrue(report["refresh_token_present"])
        self.assertFalse(report["refresh_token_expiry_known"])
        self.assertNotIn("SECRET",json.dumps(report))
        self.assertEqual(yp.cli(["auth-health","--token-file",str(t),"--mode","publish"]),0)

    def test_no_auto_subtitle_until_reviewed(self):
        (self.base / "subs.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nhello\n")
        self.doc["caption_path"] = "subs.srt"; self.save()
        with self.assertRaisesRegex(yp.PublisherError, "reviewed"): self.plan()
    def test_existing_youtube_studio_receipt_blocks_duplicate(self):
        # The repo already has a confirmed receipt for pilot_015; never reupload it.
        self.doc["episode_id"] = "pilot_015"
        (self.base/"episode.json").write_text(json.dumps({
            "id":"pilot_015","title":"Safe AI walkthrough",
            "description":"A test","type":"short"
        }))
        self.save()
        with self.assertRaisesRegex(yp.PublisherError, "already scheduled"):
            self.plan()

    def test_thumbnail_hash_and_caption_review_gates(self):
        (self.base/"thumb.png").write_bytes(b"image")
        self.doc["thumbnail_path"]="thumb.png"
        self.doc["thumbnail_sha256"]="0"*64
        self.save()
        with self.assertRaisesRegex(yp.PublisherError, "Thumbnail differs"):
            self.plan()
        self.doc["thumbnail_sha256"] = hashlib.sha256(b"image").hexdigest()
        self.save()
        self.assertEqual(self.plan()["thumbnail_path"], self.base/"thumb.png")

    def test_assets_requires_explicit_confirmation(self):
        self.assertEqual(yp.cli(["assets", str(self.manifest), "--token-file", "missing"]), 2)

    def test_duplicate_upload_blocked(self):
        self.reserve()
        l = yp.get_ledger(self.ledger_path())
        with self.assertRaisesRegex(yp.PublisherError, "duplicate-upload"):
            yp.create_upload_reservation(l, self.plan())
    def test_duplicate_sha_across_different_episode_ids_is_blocked(self):
        self.reserve()
        ledger = yp.get_ledger(self.ledger_path())
        plan = dict(self.plan())
        plan["episode_id"] = "pilot_other"
        with self.assertRaisesRegex(yp.PublisherError, "duplicate media"):
            yp.create_upload_reservation(ledger, plan)

    def test_uploaded_title_is_immutable(self):
        self.reserve()
        plan = dict(self.plan())
        plan["title"] = "Different title after approval"
        with self.assertRaisesRegex(yp.PublisherError, "title changed"):
            yp.require_matching_record(yp.get_ledger(self.ledger_path()), plan)

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
    def test_schedule_processing_gate_blocks_incomplete(self):
        self.reserve()
        api = FakeAPI(processing="processing")
        with self.assertRaisesRegex(yp.PublisherError, "processing"):
            yp.schedule_private(api, self.plan(), self.ledger_path())
        self.assertNotIn("update", [x[0] for x in api.calls])
        self.assertEqual(yp.get_ledger(self.ledger_path())["episodes"]["pilot_123"]["state"], "uploaded_private")

    def test_schedule_freshness_revalidated_at_execution(self):
        with self.assertRaisesRegex(yp.PublisherError, "at least 30"):
            yp.ensure_future_schedule((dt.datetime.now(yp.UTC) + dt.timedelta(minutes=2)).isoformat())

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
    def test_inspect_release_private_safe_without_writes(self):
        self.reserve()
        api = FakeAPI()
        info = yp.inspect_release(api, self.plan(), self.ledger_path())
        self.assertEqual(info["video_id"], VID)
        self.assertEqual(info["remote_privacy"], "private")
        self.assertFalse(info["safe_for_publication"])
        self.assertNotIn("update", [name for name, _ in api.calls])

    def test_inspect_release_detects_remote_mismatch(self):
        self.reserve()
        api = FakeAPI(existing_publish="2030-01-01T00:00:00Z")
        with self.assertRaisesRegex(yp.PublisherError, "scheduled or not private"):
            yp.inspect_release(api, self.plan(), self.ledger_path())

    def test_private_api_pilot_can_never_schedule(self):
        self.doc["episode_id"] = "api_private_test_001"
        (self.base / "episode.json").write_text(json.dumps({
            "id": "api_private_test_001", "title": "Safe AI walkthrough",
            "description": "Private testing only", "type": "long"}), encoding="utf-8")
        self.save()
        api = FakeAPI()
        with self.assertRaisesRegex(yp.PublisherError, "cannot be scheduled"):
            yp.schedule_private(api, self.plan(), self.ledger_path())
        self.assertFalse(any(action=="update" for action,_ in api.calls))
        self.assertFalse(self.ledger_path().exists())

    def test_unresolved_state_prevents_retry(self):
        self.reserve(); api=FakeAPI(privacy="public")
        with self.assertRaisesRegex(yp.PublisherError,"not private"):
            yp.schedule_private(api,self.plan(),self.ledger_path())
        self.assertEqual(yp.get_ledger(self.ledger_path())["episodes"]["pilot_123"]["state"], "uploaded_private")


if __name__ == "__main__":
    unittest.main(verbosity=2)
