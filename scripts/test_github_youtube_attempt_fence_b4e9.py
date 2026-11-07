"""B4e9 safe no-network GitHub tag attempt fence tests."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.github_youtube_attempt_fence_b4e9 import (
    AttemptFenceUnavailable, refs_for, reserve_github_attempt_before_insert,
)
from scripts.publish_youtube import reserve_local_pending_before_insert

CHANNEL="UC"+"x"*22
EPISODE="fm_20261108_short_am"
WHEN="2026-11-08T05:30:00Z"
HASH="a"*64
ENV={
    "GITHUB_ACTIONS":"true",
    "GITHUB_EVENT_NAME":"workflow_dispatch",
    "GITHUB_REF":"refs/heads/main",
    "GITHUB_REPOSITORY":"Tirthanand17/taskless-lab",
    "GITHUB_WORKFLOW":"Publish Artifact to YouTube",
    "GITHUB_SHA":"a"*40,
    "PUBLISH_ENABLED":"true",
    "GH_TOKEN":"fake-token-for-offline-mock-only",
}
BASE=dict(channel_id=CHANNEL,episode_id=EPISODE,publish_at_utc=WHEN,
          approved_mp4_sha256=HASH,environment=ENV)


class RemoteRefTests(unittest.TestCase):
    def test_both_refs_are_hashed_and_scoped(self):
        episode,slot=refs_for(CHANNEL,EPISODE,WHEN)
        self.assertTrue(episode.startswith("refs/tags/flowminute-attempt-episode-v1/"))
        self.assertTrue(slot.startswith("refs/tags/flowminute-attempt-slot-v1/"))
        self.assertNotIn(CHANNEL+EPISODE+WHEN,episode+slot)
        self.assertNotEqual(episode,slot)
        self.assertEqual(len(slot.rsplit("/",1)[-1]),64)

    def test_success_requires_two_exact_201_creates(self):
        called=[]
        def fake(url,body,headers):
            payload=json.loads(body)
            self.assertEqual(url,"https://api.github.com/repos/Tirthanand17/taskless-lab/git/refs")
            self.assertEqual(payload["sha"],ENV["GITHUB_SHA"])
            self.assertIn("Bearer fake-token",headers["Authorization"])
            called.append(payload["ref"])
            return 201,{"ref":payload["ref"],"object":{"sha":payload["sha"]}}
        report=reserve_github_attempt_before_insert(**BASE,post=fake)
        self.assertEqual(len(called),2)
        self.assertEqual(report["reservations_completed"],2)
        self.assertFalse(report["youtube_insert_called_by_this_function"])
        self.assertFalse(report["ref_deletion_or_retry_allowed"])
        self.assertNotIn("fake-token",str(report))

    def test_duplicate_tag_fails_before_second_youtube_attempt(self):
        created=set()
        def fake(url,body,headers):
            p=json.loads(body)
            if p["ref"] in created:return 422,{"message":"exists"}
            created.add(p["ref"])
            return 201,{"ref":p["ref"],"object":{"sha":p["sha"]}}
        reserve_github_attempt_before_insert(**BASE,post=fake)
        with self.assertRaises(AttemptFenceUnavailable):
            reserve_github_attempt_before_insert(**BASE,post=fake)
        self.assertEqual(len(created),2)

    def test_partial_ref_success_or_timeout_fails_closed(self):
        called=[]
        def fake(url,body,headers):
            p=json.loads(body);called.append(p["ref"])
            if len(called)==2:raise TimeoutError("ambiguous")
            return 201,{"ref":p["ref"],"object":{"sha":p["sha"]}}
        with self.assertRaisesRegex(AttemptFenceUnavailable,"NO NEW YOUTUBE INSERT"):
            reserve_github_attempt_before_insert(**BASE,post=fake)
        self.assertEqual(len(called),2)

    def test_wrong_context_cannot_start_http(self):
        for change in (
            dict(GITHUB_ACTIONS="false"),dict(GITHUB_REF="refs/heads/fake"),
            dict(GITHUB_EVENT_NAME="push"),dict(GITHUB_REPOSITORY="bad/repo"),
            dict(GITHUB_WORKFLOW="Wrong workflow"),dict(PUBLISH_ENABLED="false"),
            dict(GH_TOKEN=""),dict(GITHUB_SHA="bad"),
        ):
            calls=[]
            def impossible(*args):
                calls.append(True)
                raise AssertionError("network called")
            with self.subTest(change=change),self.assertRaises(AttemptFenceUnavailable):
                reserve_github_attempt_before_insert(**{
                    **BASE,"environment":{**ENV,**change},"post":impossible})
            self.assertEqual(calls,[])

    def test_invalid_ids_sha_and_server_reply_block(self):
        for change in (
            dict(channel_id="BAD"),dict(episode_id="../evil"),
            dict(publish_at_utc="tomorrow"),dict(approved_mp4_sha256="z"*64),
        ):
            with self.subTest(change=change),self.assertRaises(AttemptFenceUnavailable):
                reserve_github_attempt_before_insert(**{
                    **BASE,**change,
                    "post":lambda *args:(201,{}),
                })
        with self.assertRaises(AttemptFenceUnavailable):
            reserve_github_attempt_before_insert(
                **BASE,post=lambda *args:(201,{"ref":"wrong","object":{"sha":ENV["GITHUB_SHA"]}}))


class LocalCheckpointTests(unittest.TestCase):
    def test_exclusive_file_cannot_be_overwritten_by_second_process(self):
        with TemporaryDirectory() as root:
            path=Path(root)/"state/published/test.json.pending.json"
            record={"state":"POSSIBLY_SENT_NO_AUTOMATIC_RETRY",
                    "youtube_schedule_verified":False}
            reserve_local_pending_before_insert(path,record)
            self.assertEqual(json.loads(path.read_text())["state"],record["state"])
            with self.assertRaises(ValueError):
                reserve_local_pending_before_insert(path,record)
            self.assertTrue(path.exists())

    def test_failed_approval_cannot_write_checkpoint(self):
        with TemporaryDirectory() as root:
            path=Path(root)/"pending.json"
            with self.assertRaises(ValueError):
                reserve_local_pending_before_insert(path,{
                    "state":"VERIFIED", "youtube_schedule_verified":True})
            self.assertFalse(path.exists())

    def test_source_orders_both_barriers_before_insert(self):
        s=(Path(__file__).parent/"publish_youtube.py").read_text()
        at=s.index("req=youtube.videos().insert(")
        self.assertLess(s.index("reserve_local_pending_before_insert(pending_path"),at)
        self.assertLess(s.index("reserve_github_attempt_before_insert("),at)
        self.assertIn('if args.privacy != "private":',s)

    def test_manual_workflow_only_supplies_github_tag_write_token(self):
        y=(Path(__file__).resolve().parents[1]/".github/workflows/publish-artifact-youtube.yml").read_text()
        self.assertIn("GH_TOKEN: $"+"{{ github.token }}",y)
        self.assertIn("environment: youtube-production",y)
        self.assertIn("group: flowminute-youtube-verified-publication",y)


if __name__=="__main__":
    unittest.main()
