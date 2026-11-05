"""B4d2 test actual file copies vs hashes and unapproved-only review pack.

The fast PR tests use invented bytes only; the separate main-branch hosted
integration job must truly render and decode 3 different original MP4 videos.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from autopilot.primary_sourced_storyboards import build_story
from autopilot.full_topic_narrated_pack import STATUS
from autopilot.retain_public_topic_drafts import (
    SOURCE_MEDIA, PreviewRefused, STATUS_RETAINED, _retain_one,
    _require_true_technical_report, _hash_file,
)

def fixture():
    story=build_story("short_am")
    data={
        "UNAPPROVED_FULL_EDUCATION_TEST.mp4":b"fake video fixture is not real playable MP4"*50,
        "scene_captions.srt":b"1\n00:00:00,000 --> 00:00:01,000\nSynthetic fixture never publish\n",
        "UNAPPROVED_THUMBNAIL_TEST.png":b"not-a-real-PNG test data"*50,
    }
    report={
        "status":STATUS,
        "episode":story["episode_id"],
        "original_source_story_draft_sha256":story["draft_sha256"],
        "original_research_topics":story["theme"],
        "actual_full_encoded_h264_aac_with_captions_and_animation":True,
        "actual_narration_text_and_srt_matched":True,
        "original_svg_frames_really_animated":True,
        "human_complete_watch_listen":False,
        "human_original_visual_semantics_review":False,
        "independently_verified_model_voice_music_rights":False,
        "live_primary_sources_human_claim_reviewed":False,
        "provider_live_api_called":False,
        "youtube_upload_enabled":False,
        "youtube_schedule_enabled":False,
        "release_authorized":False,
        "video_sha256":sha256(data["UNAPPROVED_FULL_EDUCATION_TEST.mp4"]).hexdigest(),
        "original_unreviewed_thumbnail_sha256":
            sha256(data["UNAPPROVED_THUMBNAIL_TEST.png"]).hexdigest(),
    }
    return story,data,report


class PublicPreviewRetentionTests(unittest.TestCase):
    def test_original_draft_file_copy_preserves_hashes_with_no_upload(self):
        story,data,report=fixture()
        with tempfile.TemporaryDirectory() as root:
            root=Path(root)
            source=root/story["episode_id"]
            source.mkdir()
            for name,blob in data.items():
                (source/name).write_bytes(blob)
            destination=root/"public-artifact"/story["episode_id"]
            record=_retain_one(story,report,source,destination)
            self.assertEqual(record["episode_id"],story["episode_id"])
            self.assertFalse(record["release_authorized"])
            self.assertFalse(record["media_and_voice_rights_approved"])
            self.assertFalse(record["source_claims_human_fact_verified"])
            self.assertFalse(record["owner_full_watch_completed"])
            self.assertEqual({x["filename"] for x in record["files"]},set(SOURCE_MEDIA))
            self.assertEqual(len(record["files"]),3)
            for f in record["files"]:
                self.assertEqual((destination/f["filename"]).read_bytes(),
                                 data[SOURCE_MEDIA[f["filename"]]])
                self.assertEqual(f["sha256"],
                                 sha256((destination/f["filename"]).read_bytes()).hexdigest())
            with self.assertRaises(PreviewRefused):
                _retain_one(story,report,source,destination)

    def test_technical_forgery_and_release_escalation_denied_before_copy(self):
        story,_,base=fixture()
        for name,value in (
            ("status","RELEASE_APPROVED"),
            ("episode","other"),
            ("original_source_story_draft_sha256","a"*64),
            ("original_research_topics","different"),
            ("actual_full_encoded_h264_aac_with_captions_and_animation",False),
            ("actual_narration_text_and_srt_matched",False),
            ("original_svg_frames_really_animated",False),
            ("human_complete_watch_listen",True),
            ("human_original_visual_semantics_review",True),
            ("independently_verified_model_voice_music_rights",True),
            ("live_primary_sources_human_claim_reviewed",True),
            ("provider_live_api_called",True),
            ("youtube_upload_enabled",True),
            ("youtube_schedule_enabled",True),
            ("release_authorized",True),
            ("video_sha256","wrong"),
            ("original_unreviewed_thumbnail_sha256","wrong"),
        ):
            with self.subTest(name=name):
                r=dict(base)
                r[name]=value
                with self.assertRaises(PreviewRefused):
                    _require_true_technical_report(story,r)

    def test_tampered_media_or_thumbnail_hash_refuses_public_review_copy(self):
        story,data,report=fixture()
        for filename in ("UNAPPROVED_FULL_EDUCATION_TEST.mp4",
                         "UNAPPROVED_THUMBNAIL_TEST.png"):
            with self.subTest(filename=filename):
                with tempfile.TemporaryDirectory() as root:
                    root=Path(root)
                    source=root/story["episode_id"]
                    source.mkdir()
                    for key,blob in data.items():
                        (source/key).write_bytes(blob)
                    (source/filename).write_bytes(data[filename]+b"altered")
                    with self.assertRaises(PreviewRefused):
                        _retain_one(story,report,source,root/"output")

    def test_symlink_fake_assets_not_accepted(self):
        story,data,report=fixture()
        with tempfile.TemporaryDirectory() as root:
            root=Path(root)
            source=root/story["episode_id"]
            source.mkdir()
            for name,blob in data.items():
                (source/name).write_bytes(blob)
            outsider=root/"other.mp4"
            outsider.write_bytes(data["UNAPPROVED_FULL_EDUCATION_TEST.mp4"])
            (source/"UNAPPROVED_FULL_EDUCATION_TEST.mp4").unlink()
            (source/"UNAPPROVED_FULL_EDUCATION_TEST.mp4").symlink_to(outsider)
            with self.assertRaises(PreviewRefused):
                _retain_one(story,report,source,root/"out")

    def test_missing_empty_or_too_large_media_refused(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/"blob.bin"
            p.write_bytes(b"tiny")
            with self.assertRaises(PreviewRefused):
                _hash_file(p,10)
            p.write_bytes(b"abc"*100)
            with self.assertRaises(PreviewRefused):
                _hash_file(p,50)
            d,n=_hash_file(p,300)
            self.assertEqual(n,300)
            self.assertEqual(d,sha256(b"abc"*100).hexdigest())

    def test_public_preview_contract_never_names_youtube_publish_authority(self):
        self.assertEqual(len(SOURCE_MEDIA),3)
        self.assertIn("NOT_RELEASE_APPROVED",STATUS_RETAINED)
        self.assertTrue(all(p.startswith(("PREVIEW_UNAPPROVED",
                                         "CAPTIONS_UNAPPROVED",
                                         "THUMBNAIL_UNAPPROVED")) for p in SOURCE_MEDIA))


if __name__=="__main__":
    unittest.main()
