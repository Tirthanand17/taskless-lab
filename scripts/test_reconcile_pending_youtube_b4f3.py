"""B4f3 strict manual owner read-only recovery; injected fake YouTube clients."""
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.owner_youtube_readback_b4f2 import OwnerYouTubeReadbackRefused
from scripts.reconcile_pending_youtube_b4f3 import (
    ReadonlyRecoveryRefused, validate_recovery_context,
    inspect_existing_remote_only,require_explicit_manual_readonly_context,
    _read_known_json, PENDING_FILE, EPISODE_FILE, EXPECTED_WORKFLOW,
)
from scripts.youtube_pending_checkpoint_b4f3 import (
    PendingCheckpointRefused,save_existing_caption_identity,
)
from scripts.test_owner_youtube_readback_b4f2 import (
    youtube_fake,CHANNEL,OTHER,VIDEO,CAPTION,WHEN,TITLE,DESC,
)

EPISODE="original_20261108_001"
DIGEST="a"*64


def sample():
    return (
        {"state":"UPLOAD_EXISTS_SCHEDULE_NOT_YET_VERIFIED",
         "youtube_schedule_verified":False,
         "video_id":VIDEO,
         "caption_track_id":CAPTION,
         "expected_channel_id":CHANNEL,
         "episode_id":EPISODE,
         "source_mp4_sha256":DIGEST,
         "expected_publish_at_utc":WHEN},
        {"id":EPISODE,"title":TITLE,"description":DESC,"language":"en"},
    )


class PendingReadonlyTests(unittest.TestCase):
    def test_existing_complete_private_media_requires_only_three_read_calls(self):
        pending,episode=sample()
        client=youtube_fake()
        report=inspect_existing_remote_only(client,pending,episode,CHANNEL)
        self.assertTrue(report["authenticated_preexisting_private_video_ready"])
        self.assertEqual(report["read_only_youtube_api_calls"],3)
        self.assertEqual(report["new_youtube_uploads_or_updates_or_deletions"],0)
        self.assertFalse(report["public_release_verified"])
        self.assertFalse(report["unattended_7_day_21_video_proof_achieved"])
        self.assertNotIn(VIDEO,str(report))
        self.assertNotIn(CAPTION,str(report))
        self.assertNotIn(TITLE,str(report))
        client.videos.return_value.insert.assert_not_called()
        client.videos.return_value.update.assert_not_called()
        client.videos.return_value.delete.assert_not_called()
        client.captions.return_value.insert.assert_not_called()
        client.thumbnails.return_value.set.assert_not_called()

    def test_pending_without_specific_caption_id_cannot_claim_recovered(self):
        pending,episode=sample()
        pending.pop("caption_track_id")
        client=youtube_fake()
        with self.assertRaises(ReadonlyRecoveryRefused):
            inspect_existing_remote_only(client,pending,episode,CHANNEL)
        client.channels.assert_not_called()

    def test_wrong_owner_channel_refuses_before_video_readback(self):
        pending,episode=sample()
        client=youtube_fake(channel=OTHER)
        with self.assertRaises(OwnerYouTubeReadbackRefused):
            inspect_existing_remote_only(client,pending,episode,CHANNEL)
        client.videos.assert_not_called()

    def test_processing_or_caption_not_ready_preserves_no_insert(self):
        pending,episode=sample()
        for where,state in (("processing","processing"),("caption","syncing")):
            client=youtube_fake()
            if where=="processing":
                item=client.videos.return_value.list.return_value.execute.return_value["items"][0]
                item["processingDetails"]["processingStatus"]=state
            else:
                cap=client.captions.return_value.list.return_value.execute.return_value["items"][0]
                cap["snippet"]["status"]=state
            with self.subTest(where=where),self.assertRaises(OwnerYouTubeReadbackRefused):
                inspect_existing_remote_only(client,pending,episode,CHANNEL)
            client.videos.return_value.insert.assert_not_called()

    def test_wrong_or_unknown_pending_context_rejected(self):
        changes=(
            ("state","POSSIBLY_SENT_NO_AUTOMATIC_RETRY"),
            ("video_id","ZZZZZZZZZZZ"),
            ("caption_track_id",""),
            ("source_mp4_sha256","e"*63),
            ("episode_id","original_20261109_001"),
            ("expected_channel_id",OTHER),
            ("expected_publish_at_utc","tomorrow"),
        )
        for key,value in changes:
            pending,episode=sample();pending[key]=value
            if key=="video_id":
                # Structurally valid video ID is allowed through context;
                # independent authenticated readback will detect mismatch.
                client=youtube_fake()
                with self.assertRaises(OwnerYouTubeReadbackRefused):
                    inspect_existing_remote_only(client,pending,episode,CHANNEL)
            else:
                with self.subTest(key=key),self.assertRaises(ReadonlyRecoveryRefused):
                    validate_recovery_context(pending,episode,CHANNEL)

    def test_manual_main_owner_context_required(self):
        env={
            "GITHUB_ACTIONS":"true",
            "GITHUB_REF":"refs/heads/main",
            "GITHUB_REPOSITORY":"Tirthanand17/taskless-lab",
            "GITHUB_EVENT_NAME":"workflow_dispatch",
            "GITHUB_WORKFLOW":EXPECTED_WORKFLOW,
            "FLOWMINUTE_READONLY_RECOVERY_ENABLED":"true",
        }
        require_explicit_manual_readonly_context(env)
        for k,v in (
            ("GITHUB_EVENT_NAME","schedule"),
            ("GITHUB_REF","refs/heads/other"),
            ("GITHUB_REPOSITORY","attacker/repo"),
            ("GITHUB_WORKFLOW","Wrong workflow"),
            ("FLOWMINUTE_READONLY_RECOVERY_ENABLED","false"),
        ):
            with self.subTest(k=k),self.assertRaises(ReadonlyRecoveryRefused):
                require_explicit_manual_readonly_context({**env,k:v})

    def test_restricted_repo_paths_and_symlinks(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            (root/"state/published").mkdir(parents=True)
            (root/"content/episodes").mkdir(parents=True)
            pending,ep=sample()
            p=root/"state/published/test.json.pending.json"
            p.write_text(json.dumps(pending))
            e=root/"content/episodes/test.json"
            e.write_text(json.dumps(ep))
            self.assertEqual(_read_known_json(root,"state/published/test.json.pending.json",PENDING_FILE)["video_id"],VIDEO)
            self.assertEqual(_read_known_json(root,"content/episodes/test.json",EPISODE_FILE)["id"],EPISODE)
            for target in ("../outside.json","/tmp/absolute.json","state/published/../../secret.json"):
                with self.assertRaises(ReadonlyRecoveryRefused):
                    _read_known_json(root,target,PENDING_FILE)
            p.unlink()
            p.symlink_to(e)
            with self.assertRaises(ReadonlyRecoveryRefused):
                _read_known_json(root,"state/published/test.json.pending.json",PENDING_FILE)


class CaptionCheckpointTests(unittest.TestCase):
    def test_caption_id_persisted_atomically_once_for_existing_video(self):
        with TemporaryDirectory() as folder:
            p=Path(folder)/"test.json.pending.json"
            pending,ep=sample()
            pending.pop("caption_track_id")
            p.write_text(json.dumps(pending))
            save_existing_caption_identity(p,video_id=VIDEO,caption_id=CAPTION)
            loaded=json.loads(p.read_text())
            self.assertEqual(loaded["caption_track_id"],CAPTION)
            self.assertEqual(loaded["video_id"],VIDEO)
            self.assertFalse(loaded["youtube_schedule_verified"])
            with self.assertRaises(PendingCheckpointRefused):
                save_existing_caption_identity(p,video_id=VIDEO,caption_id=CAPTION)

    def test_wrong_video_and_orphan_marker_not_clobbered(self):
        with TemporaryDirectory() as folder:
            p=Path(folder)/"test.json.pending.json"
            pending,ep=sample()
            pending.pop("caption_track_id")
            p.write_text(json.dumps(pending))
            for video,cap in ((OTHER[-11:],CAPTION),(VIDEO,"INVALID CAPTION")):
                with self.subTest(video=video),self.assertRaises(PendingCheckpointRefused):
                    save_existing_caption_identity(p,video_id=video,caption_id=cap)
            self.assertNotIn("caption_track_id",json.loads(p.read_text()))

    def test_recovery_workflow_no_writes_or_automatic_schedule(self):
        wf=(Path(__file__).resolve().parents[1]/
            ".github/workflows/flowminute-youtube-readonly-recovery-b4f3.yml").read_text()
        self.assertIn("  workflow_dispatch:",wf)
        self.assertNotIn("  schedule:",wf)
        self.assertNotIn("  push:",wf)
        self.assertNotIn("  pull_request:",wf)
        self.assertIn("permissions:\n  contents: read",wf)
        self.assertNotIn("contents: write",wf)
        self.assertIn("environment: youtube-production",wf)
        self.assertIn("vars.FLOWMINUTE_READONLY_RECOVERY_ENABLED == 'true'",wf)
        self.assertIn("persist-credentials: false",wf)
        self.assertNotIn("scripts/publish_youtube.py",wf)
        self.assertIn("python -m scripts.reconcile_pending_youtube_b4f3",wf)
        self.assertNotIn("git push",wf)

    def test_publisher_saves_track_after_insert_before_first_readback(self):
        source=(Path(__file__).parent/"publish_youtube.py").read_text()
        a=source.index("uploaded_caption=youtube.captions().insert(")
        b=source.index("save_existing_caption_identity(")
        c=source.index("verify_processed_private_schedule_and_caption(")
        self.assertTrue(a < b < c)
        self.assertIn('"expected_channel_id":args.expected_channel_id',source)


if __name__=="__main__":
    unittest.main()
