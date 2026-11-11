"""No-network, no-secrets staging regressions for Nov 12 owner-only assets."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.prepare_branch1_nov12_release_candidates import (
    NAMES,SLOTS_UTC,FILES,PREP_STATUS,SOURCE_STATUS,CandidateRefused,
    validate_source_run,validate_and_stage,
)
from scripts.validate_release import validate


class Nov12FlatArtifactStagingTests(unittest.TestCase):
    def _fixture(self,root):
        from scripts.prepare_branch1_nov12_release_candidates import REPO
        src=root/"source"
        src.mkdir()
        fake_repo=root/"repo"
        briefdir=fake_repo/"content/nov12_2026"
        briefdir.mkdir(parents=True)
        original=REPO/"content/nov12_2026/four_video_review_brief.json"
        briefdir.joinpath("four_video_review_brief.json").write_bytes(
            original.read_bytes())
        episodir=fake_repo/"content/episodes"
        episodir.mkdir()
        original_brief=json.loads(original.read_text("utf8"))
        entries=[]
        for i,id_ in enumerate(NAMES):
            meta=REPO/"content/episodes"/(id_+".json")
            episodir.joinpath(id_+".json").write_bytes(meta.read_bytes())
            episode=json.loads(meta.read_text("utf8"))
            self.assertEqual(episode["proposed_publish_at_utc"],SLOTS_UTC[i])
            self.assertEqual(validate(episode,[],editorial_only=False),[],
                             ("Unpublishable metadata content",id_))
            folder=src/id_
            folder.mkdir()
            fake={
                "REVIEW_ONLY_FINAL.mp4":b"\x00\x00\x00\x0cftypisom"+
                    bytes([65+i])*192,
                "ORIGINAL_SOURCE_TIMED_CAPTIONS.srt":
                    b"1\n00:00:00,000 --> 00:00:01,123\nOriginal narration\n"+
                    bytes([65+i])*128,
                "ORIGINAL_COVER.png":b"\x89PNG\r\n\x1a\n"+
                    bytes([100+i])*220,
                "ORIGINAL_SCENE_CONTACT_SHEET.png":b"\x89PNG\r\n\x1a\n"+
                    bytes([110+i])*230,
            }
            for filename,data in fake.items():
                (folder/filename).write_bytes(data)
            (folder/"READ_THIS_FIRST.txt").write_text(
                "Owner video review absent. No YouTube upload permitted.")
            files=[
                {"name":k,"bytes":len(v),"sha256":sha256(v).hexdigest()}
                for k,v in fake.items()
            ]
            entries.append({
                "episode_id":id_,
                "kind":"long" if i==2 else "short",
                "suggested_ist_slot":original_brief["episodes"][i]["time"],
                "physical_h264_aac_full_decode_passed":True,
                "human_full_watch":False,
                "rights_and_factual_owner_signoff":False,
                "youtube_scheduled":False,"release_authorized":False,
                "files":files,
                "actual_mp4_sha256":files[0]["sha256"],
                "original_mp4_aac_post_encode":{
                    "integrated_lufs_and_true_peak_within_internal_band":True},
            })
        manifest={
            "status":SOURCE_STATUS,"date_ist":"2026-11-12",
            "source_brief_sha256":sha256(original.read_bytes()).hexdigest(),
            "physical_review_mp4_count":4,
            "original_short_count":3,"original_long_count":1,
            "owner_video_and_voice_reviews_completed":0,
            "youtube_uploads":0,"youtube_schedule_writes":0,
            "release_authorized":False,
            "simulated_ui_not_real_product_screen_capture":True,
            "episode_reports":entries,
        }
        (src/"FOUR_VIDEO_REVIEW_MANIFEST.json").write_text(
            json.dumps(manifest),encoding="utf8")
        return src,fake_repo,manifest

    def test_four_distinct_source_locked_files_preserved_exactly_without_auth(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            src,repo,manifest=self._fixture(root)
            staged=validate_and_stage(src,root/"flat",repo)
            self.assertEqual(len(staged),4)
            self.assertEqual([x["proposed_publish_at_utc"] for x in staged],
                             list(SLOTS_UTC))
            self.assertEqual(
                len({x["video_sha256"] for x in staged}),4)
            for episode in staged:
                self.assertFalse(episode["owner_approval_verified"])
                self.assertFalse(episode["owner_signature_verified"])
                self.assertFalse(episode["youtube_upload_or_schedule_verified"])
                flat=root/"flat"/episode["id"]
                self.assertEqual(
                    sorted(p.name for p in flat.iterdir()),
                    sorted([*FILES,
                            "CANDIDATE_PROVENANCE_NOT_RELEASE_APPROVAL.json"]))
                for name in FILES:
                    self.assertEqual((flat/name).read_bytes(),
                                     (src/episode["id"]/name).read_bytes())
            summary=json.loads(
                (root/"flat"/"FOUR_RELEASE_CANDIDATES_NO_YOUTUBE_UPLOAD.json")
                .read_text("utf8"))
            self.assertEqual(summary["status"],PREP_STATUS)
            self.assertEqual(summary["youtube_scheduled_count"],0)
            self.assertEqual(summary["approved_release_count"],0)

    def test_untrusted_source_not_main_successful_original_workflow(self):
        correct={
            "headBranch":"main","conclusion":"success",
            "event":"workflow_dispatch",
            "headSha":"a"*40,
            "workflowName":
              "FlowMinute Branch 1 Nov12 Four Real Original Owner-Review Videos (NO YOUTUBE)",
        }
        self.assertTrue(validate_source_run(correct))
        changes=[
            {"headBranch":"unreviewed-feature"},
            {"conclusion":"failure"},
            {"event":"pull_request"},
            {"headSha":"a"*64},
            {"workflowName":"A different workflow"},
        ]
        for change in changes:
            forged={**correct,**change}
            with self.subTest(change=change):
                with self.assertRaises(CandidateRefused):
                    validate_source_run(forged)

    def test_corrupted_video_missing_rights_false_approvals_or_clock_refused(self):
        changes=[
            lambda src,meta: (
                src/NAMES[0]/"REVIEW_ONLY_FINAL.mp4").write_bytes(
                    b"\x00\x00\x00\x0cftypisom"+b"X"*192),
            lambda src,meta: meta.update(release_authorized=True),
            lambda src,meta: meta.update(youtube_uploads=1),
            lambda src,meta: meta.update(owner_video_and_voice_reviews_completed=4),
            lambda src,meta: meta["episode_reports"][1].update(
                youtube_scheduled=True),
            lambda src,meta: meta["episode_reports"][2].update(
                human_full_watch=True),
            lambda src,meta: meta["episode_reports"][0].update(
                actual_mp4_sha256="f"*64),
            lambda src,meta: meta["episode_reports"][3].update(
                suggested_ist_slot="19:00"),
        ]
        for tamper in changes:
            with TemporaryDirectory() as tmp:
                root=Path(tmp)
                src,repo,manifest=self._fixture(root)
                tamper(src,manifest)
                (src/"FOUR_VIDEO_REVIEW_MANIFEST.json").write_text(
                    json.dumps(manifest),encoding="utf8")
                with self.subTest(tamper=str(tamper)):
                    with self.assertRaises(CandidateRefused):
                        validate_and_stage(src,root/"flat",repo)
                    self.assertFalse((root/"flat").exists())

    def test_episode_metadata_approval_never_implied(self):
        from scripts.prepare_branch1_nov12_release_candidates import REPO
        for id_,utc in zip(NAMES,SLOTS_UTC):
            meta=json.loads(
                (REPO/"content/episodes"/(id_+".json"))
                .read_text("utf8"))
            self.assertFalse(meta["owner_exact_media_release_signoff_observed"])
            self.assertFalse(meta["youtube_uploaded"])
            self.assertFalse(meta["youtube_scheduled"])
            self.assertEqual(meta["proposed_publish_at_utc"],utc)


if __name__=="__main__":
    unittest.main()
