"""Offline adversarial tests: do not re-upload a Studio-scheduled MP4."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.known_youtube_upload_fence import (
    CHANNEL, KNOWN_EPISODE, KNOWN_SHA, KNOWN_VIDEO_ID,
    REGISTRY, KnownUploadRejected, load_known_uploads,
    refuse_if_already_uploaded,
)

ROOT = Path(__file__).resolve().parents[1]
EPISODE_PATH = "content/episodes/" + KNOWN_EPISODE + ".json"
OTHER_PATH = "content/episodes/fm_fully_distinct_new_content.json"
OTHER_SHA = "c" * 64

class KnownYoutubeUploadFenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = json.loads((ROOT / REGISTRY).read_text("utf8"))

    def create_ledger(self, folder, data):
        path = Path(folder) / REGISTRY
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf8")
        return Path(folder)

    def check(self, root, episode_path=OTHER_PATH, digest=OTHER_SHA,
              channel_id=CHANNEL):
        return refuse_if_already_uploaded(
            root=root, episode_path=episode_path,
            mp4_sha256=digest, channel_id=channel_id)

    def test_exact_actual_studio_video_is_registry_protected(self):
        records = load_known_uploads(ROOT)
        self.assertEqual(records[0]["youtube_video_id"], KNOWN_VIDEO_ID)
        self.assertEqual(records[0]["video_sha256"], KNOWN_SHA)
        self.assertEqual(records[0]["scheduled_publish_at_utc"],
                         "2026-11-19T10:30:00Z")
        self.assertEqual(records[0]["episode_path"], EPISODE_PATH)
        for episode, digest in (
            (EPISODE_PATH, KNOWN_SHA),
            (EPISODE_PATH, OTHER_SHA),
            (OTHER_PATH, KNOWN_SHA),
        ):
            with self.subTest(episode=episode, digest=digest),                  self.assertRaisesRegex(KnownUploadRejected,
                                        "ALREADY_UPLOADED_IN_OWNER_YOUTUBE_STUDIO"):
                self.check(ROOT, episode, digest)

    def test_old_episode_metadata_does_not_reopen_publishing(self):
        # Canonical source metadata still records its immutable pre-upload
        # review state. The independently verified Studio ledger takes priority.
        meta = json.loads((ROOT / EPISODE_PATH).read_text("utf8"))
        self.assertFalse(meta["youtube_uploaded"])
        self.assertFalse(meta["youtube_scheduled"])
        self.assertEqual(meta["exact_original_mp4_sha256"], KNOWN_SHA)
        with self.assertRaises(KnownUploadRejected):
            self.check(ROOT, EPISODE_PATH, KNOWN_SHA)

    def test_other_video_is_not_a_grant_to_publish(self):
        result = self.check(ROOT)
        self.assertEqual(result["status"],
                         "NOT_IN_KNOWN_OWNER_STUDIO_UPLOAD_LEDGER")
        self.assertFalse(result["owner_rights_or_cryptographic_release_approved"])
        self.assertFalse(result["live_youtube_duplicate_scan_completed"])
        self.assertEqual(result["youtube_uploads"], 0)

    def test_missing_or_modified_ledger_is_fail_closed(self):
        with TemporaryDirectory() as folder:
            with self.assertRaisesRegex(KnownUploadRejected, "LEDGER_MISSING"):
                self.check(Path(folder))
            for edit in (
                lambda d: d["records"].clear(),
                lambda d: d.update({"channel_id":"UC_NOT_AUTHORIZED"}),
                lambda d: d["records"][0].update({"youtube_video_id":"00000000000"}),
                lambda d: d["records"][0].update({"video_sha256":"e"*64}),
                lambda d: d["records"][0].update({"status_at_verification":"draft"}),
                lambda d: d["records"][0].update({"verified_source":"vidIQ_draft_only"}),
                lambda d: d["records"].append(deepcopy(d["records"][0])),
            ):
                with self.subTest(change=str(edit)):
                    data=deepcopy(self.original)
                    edit(data)
                    root=self.create_ledger(folder,data)
                    with self.assertRaises(KnownUploadRejected):
                        self.check(root)

    def test_unsafe_inputs_refused_even_with_existing_ledger(self):
        cases = [
            (EPISODE_PATH, None, CHANNEL),
            (EPISODE_PATH, "X"*64, CHANNEL),
            (EPISODE_PATH, KNOWN_SHA, "UC_wrong_channel"),
            ("../" + EPISODE_PATH, KNOWN_SHA, CHANNEL),
            ("/tmp/episode.json", KNOWN_SHA, CHANNEL),
            (EPISODE_PATH + "; rm -rf .", KNOWN_SHA, CHANNEL),
        ]
        for ep, sha, channel in cases:
            with self.subTest(ep=ep), self.assertRaises(KnownUploadRejected):
                self.check(ROOT, ep, sha, channel)

    def test_production_publisher_cannot_skip_ledger(self):
        workflow = (ROOT / ".github/workflows/publish-artifact-youtube.yml").read_text("utf8")
        publisher = (ROOT / "scripts/publish_youtube.py").read_text("utf8")
        self.assertIn("python -m scripts.known_youtube_upload_fence", workflow)
        self.assertLess(workflow.index("python -m scripts.known_youtube_upload_fence"),
                        workflow.index("Download only a successful main-branch render artifact"))
        self.assertIn("refuse_if_already_uploaded(", publisher)
        self.assertLess(publisher.index("refuse_if_already_uploaded("),
                        publisher.index("youtube=load_service()"))
        self.assertLess(publisher.index("refuse_if_already_uploaded("),
                        publisher.index("youtube.videos().insert("))
        guard = (ROOT / "scripts/known_youtube_upload_fence.py").read_text("utf8")
        for unwanted in ("googleapiclient", "youtube.videos().insert",
                         "oauth2", "YOUTUBE_TOKEN_JSON", "videos().delete"):
            self.assertNotIn(unwanted, guard)

if __name__ == "__main__":
    unittest.main()
