"""No-network, no-video-production tests for five-day SHA-verified owner candidates."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.prepare_b1_nov13_17_release_candidates import (
    SOURCE_STATUS,DEST_STATUS,SOURCE_WORKFLOW,FILE_NAMES,
    OwnerCandidateRefused,stage_three,check_main_render_proof,DEFAULT_REPO
)
from scripts.validate_release import validate


class CandidateProofTests(unittest.TestCase):
    def fixture(self,tmp,date):
        root=Path(tmp)
        source=root/"source"
        source.mkdir()
        repo=root/"repo"
        (repo/"content/nov13_17_2026").mkdir(parents=True)
        (repo/"content/episodes").mkdir(parents=True)
        source_brief=DEFAULT_REPO/"content/nov13_17_2026"/f"day_{date}.json"
        raw=source_brief.read_bytes()
        (repo/"content/nov13_17_2026"/f"day_{date}.json").write_bytes(raw)
        day=json.loads(raw)
        episodes=[]
        for i,ep in enumerate(day["episodes"]):
            meta_path=DEFAULT_REPO/"content/episodes"/(ep["id"]+".json")
            data=meta_path.read_bytes()
            (repo/"content/episodes"/meta_path.name).write_bytes(data)
            self.assertEqual(validate(json.loads(data),[],editorial_only=False),[])
            folder=source/ep["id"]
            folder.mkdir()
            file_data={
                "REVIEW_ONLY_FINAL.mp4":
                    b"\x00\x00\x00\x18ftypisom"+bytes([21+i])*700,
                "ORIGINAL_SOURCE_TIMED_CAPTIONS.srt":
                    b"1\n00:00:00,000 --> 00:00:01,000\nA real caption.\n"+
                    bytes([65+i])*160,
                "ORIGINAL_COVER.png":
                    b"\x89PNG\r\n\x1a\n"+bytes([78+i])*280,
                "ORIGINAL_SCENE_CONTACT_SHEET.png":
                    b"\x89PNG\r\n\x1a\n"+bytes([88+i])*280,
            }
            for name,data in file_data.items():
                (folder/name).write_bytes(data)
            (folder/"README_OWNER_REVIEW_NOT_UPLOADED.txt").write_text(
                "Original educational media, NOT uploaded to YouTube.")
            claims=[
                {"name":name,"bytes":len(data),"sha256":sha256(data).hexdigest()}
                for name,data in file_data.items()
            ]
            mp4sha=claims[0]["sha256"]
            episodes.append({
                "episode_id":ep["id"],"date_ist":date,
                "kind":ep["kind"],"proposed_time_ist":ep["time_ist"],
                "title":ep["title"],"primary_source":ep["source"],
                "original_scenes":len(ep["scenes"]),
                "one_way_original_visual_states":len(ep["scenes"])*3,
                "physical_h264_aac_full_decode_passed":True,
                "actual_pcm_seconds":38.125 if i<2 else 171.123,
                "actual_mp4_sha256":mp4sha,
                "owner_final_voice_captions_facts_rights_review":False,
                "release_signed":False,"youtube_uploaded":False,
                "youtube_scheduled":False,
                "post_encoded_mastering":{
                    "status":"B4G5_FINAL_ORIGINAL_AAC_TRUE_PEAK_LIMITED_LOUDNESS_VERIFIED_NO_PUBLISH",
                    "exact_original_mp4_sha256":mp4sha,
                    "source_pcm_duration_seconds_unchanged":38.125 if i<2 else 171.123,
                    "integrated_lufs_and_true_peak_within_internal_band":True,
                    "human_listening_and_mobile_playback_verified":False,
                    "rights_and_facts_approved":False,
                    "youtube_upload_or_release_authorized":False,
                },
                "files":claims,
            })
        report={
            "status":SOURCE_STATUS,"date_ist":date,
            "source_brief_sha256":sha256(raw).hexdigest(),
            "actual_h264_aac_verified_mp4_count":3,
            "actual_original_shorts":2,"actual_original_longs":1,
            "release_owner_authorizations":0,"youtube_uploads":0,
            "youtube_scheduled_writes":0,"episodes":episodes,
        }
        (source/"DAY_ORIGINAL_THREE_REVIEW_MANIFEST.json").write_text(
            json.dumps(report,indent=2),"utf8")
        return repo,source,report

    def test_exact_3_hash_locked_assets_for_every_day(self):
        for date in [f"2026-11-{day:02d}" for day in range(13,18)]:
            with self.subTest(date=date),TemporaryDirectory() as td:
                repo,source,report=self.fixture(td,date)
                out=Path(td)/"flat"
                staged=stage_three(date,source,out,repo)
                self.assertEqual(len(staged),3)
                self.assertEqual([x["kind"] for x in staged],
                                 ["short","short","long"])
                self.assertEqual([x["future_proposed_publish_at_utc"] for x in staged],
                                 [date+"T05:30:00Z",date+"T15:00:00Z",date+"T10:30:00Z"])
                for row in staged:
                    self.assertFalse(row["owner_exact_media_approved"])
                    self.assertFalse(row["owner_release_ed25519_signed"])
                    self.assertFalse(row["youtube_scheduled_by_this_workflow"])
                    p=out/row["episode_id"]
                    self.assertEqual(set(x.name for x in p.iterdir()),
                                     {"REVIEW_ONLY_FINAL.mp4",
                                      "ORIGINAL_SOURCE_TIMED_CAPTIONS.srt",
                                      "ORIGINAL_COVER.png",
                                      "SHA_VERIFIED_NOT_RELEASE_APPROVED.json"})
                    self.assertEqual((p/"REVIEW_ONLY_FINAL.mp4").read_bytes(),
                         (source/row["episode_id"]/"REVIEW_ONLY_FINAL.mp4").read_bytes())
                summary=json.loads(
                    (out/"THREE_FLAT_RELEASE_CANDIDATES_UNAPPROVED.json").read_text())
                self.assertEqual(summary["status"],DEST_STATUS)
                self.assertEqual(summary["owner_approved_count"],0)
                self.assertEqual(summary["youtube_scheduled_count"],0)

    def test_main_approved_source_run_only_means_verified_source_not_signed_release(self):
        good={"headBranch":"main","conclusion":"success",
              "event":"workflow_dispatch","workflowName":SOURCE_WORKFLOW,
              "headSha":"a"*40}
        self.assertEqual(check_main_render_proof(good),"a"*40)
        for override in ({"headBranch":"feature/unapproved"},
                         {"conclusion":"failure"},{"event":"pull_request"},
                         {"workflowName":"Fake job"},{"headSha":"f"*64}):
            with self.subTest(override=override):
                with self.assertRaises(OwnerCandidateRefused):
                    check_main_render_proof({**good,**override})

    def test_forged_release_or_altered_mp4_refused_before_any_output(self):
        date="2026-11-13"
        for modification in ("wrong_hour","approved","changed_video",
                             "forged_sha","missing_caption",
                             "fake_master","pretend_scheduled","duplicate_video"):
            with self.subTest(modification=modification), TemporaryDirectory() as td:
                repo,src,data=self.fixture(td,date)
                row=data["episodes"][0]
                folder=src/row["episode_id"]
                if modification=="wrong_hour":row["proposed_time_ist"]="12:00"
                if modification=="approved":row["owner_final_voice_captions_facts_rights_review"]=True
                if modification=="changed_video":
                    (folder/"REVIEW_ONLY_FINAL.mp4").write_bytes(b"attack"*200)
                if modification=="forged_sha":row["actual_mp4_sha256"]="a"*64
                if modification=="missing_caption":
                    (folder/"ORIGINAL_SOURCE_TIMED_CAPTIONS.srt").unlink()
                if modification=="fake_master":
                    row["post_encoded_mastering"]["youtube_upload_or_release_authorized"]=True
                if modification=="pretend_scheduled":
                    row["youtube_scheduled"]=True
                if modification=="duplicate_video":
                    row["actual_mp4_sha256"]=data["episodes"][1]["actual_mp4_sha256"]
                    row["post_encoded_mastering"]["exact_original_mp4_sha256"]=row["actual_mp4_sha256"]
                (src/"DAY_ORIGINAL_THREE_REVIEW_MANIFEST.json").write_text(
                    json.dumps(data,indent=2),"utf8")
                out=Path(td)/"flat"
                with self.assertRaises(OwnerCandidateRefused):
                    stage_three(date,src,out,repo)
                self.assertFalse(out.exists())

    def test_episode_metadata_false_owner_signature_no_youtube_state(self):
        for day in range(13,18):
            date=f"2026-11-{day:02d}"
            source=json.loads((DEFAULT_REPO/"content/nov13_17_2026"/f"day_{date}.json").read_text())
            for ep in source["episodes"]:
                metadata=json.loads((DEFAULT_REPO/"content/episodes"/(ep["id"]+".json")).read_text())
                self.assertFalse(metadata["owner_exact_media_release_signoff_observed"])
                self.assertFalse(metadata["youtube_uploaded"])
                self.assertFalse(metadata["youtube_scheduled"])
                self.assertEqual(metadata["title"],ep["title"])
                self.assertEqual(metadata["proposed_time_ist"],ep["time_ist"])
                self.assertEqual(metadata["requested_date_ist"],date)
                self.assertEqual(validate(metadata,[],editorial_only=False),[])


if __name__=="__main__":
    unittest.main()
