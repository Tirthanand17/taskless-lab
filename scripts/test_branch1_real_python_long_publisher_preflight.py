"""Synthetic mutation tests for owner-reviewed Python long publisher metadata."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from scripts.branch1_real_python_long_publisher_preflight import (
    EXPECTED_CUE_COUNT,EXPECTED_MP4,EXPECTED_SRT,EXPECTED_COVER,
    META,REVIEW,MetadataNotReleaseReady,validate,
)

class RealPythonLongPublisherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta=json.loads(META.read_text("utf8"))
        cls.review=json.loads(REVIEW.read_text("utf8"))

    def test_real_exact_source_and_caption_metadata_is_compatible_not_released(self):
        report=validate(deepcopy(self.meta),deepcopy(self.review))
        self.assertEqual(report["video_sha256"],EXPECTED_MP4)
        self.assertEqual(report["captions_sha256"],EXPECTED_SRT)
        self.assertEqual(report["thumbnail_sha256"],EXPECTED_COVER)
        self.assertEqual(report["original_caption_cues"],EXPECTED_CUE_COUNT)
        self.assertEqual(report["youtube_uploads"],0)
        self.assertEqual(report["youtube_schedules"],0)
        self.assertFalse(report["live_youtube_auth_verified"])
        self.assertFalse(report["complete_exact_media_owner_release_signed"])

    def test_no_media_substitution_or_unapproved_ownership(self):
        for key,bad in (
            ("exact_original_mp4_sha256","0"*64),
            ("exact_original_srt_sha256","e"*64),
            ("exact_actual_frame_cover_sha256","1"*64),
            ("title","This Python trick makes real invoices worth millions!"),
            ("renderer","synthetic_terminal_video"),
            ("channel_id","UC0000000000000000000000"),
            ("raw_row_count",9),
            ("unique_total_usd","1435.75"),
            ("original_github_preservation_run",0),
            ("owner_full_voice_captions_rights_facts_release_signed",True),
            ("youtube_uploaded",True),
            ("youtube_scheduled",True),
            ("actual_youtube_upload_id","ZZZZZZZZZZZ"),
            ("actual_youtube_publish_at_utc","2026-11-17T10:30:00Z"),
        ):
            with self.subTest(key=key):
                meta=deepcopy(self.meta)
                meta[key]=bad
                with self.assertRaises(MetadataNotReleaseReady):
                    validate(meta,deepcopy(self.review))

    def test_cue_changes_and_reordered_captions_refused(self):
        changes=(
            lambda d: d["captions"].pop(),
            lambda d: d["captions"][0].update({"start":1}),
            lambda d: d["captions"][3].update({"start":0}),
            lambda d: d["captions"][43].update({"end":215}),
            lambda d: d["captions"][12].update({"end":d["captions"][12]["start"]}),
        )
        for ix,change in enumerate(changes):
            with self.subTest(changed=ix):
                d=deepcopy(self.meta)
                change(d)
                with self.assertRaises(MetadataNotReleaseReady):
                    validate(d,deepcopy(self.review))

    def test_fictional_claims_and_primary_docs_required(self):
        for key,bad in (
            ("description","We actually cleaned real paying customer invoices!"),
            ("source_links",["https://example.test"]),
            ("first_party_fictional_invoice_data",False),
        ):
            with self.subTest(key=key):
                d=deepcopy(self.meta)
                d[key]=bad
                with self.assertRaises(MetadataNotReleaseReady):
                    validate(d,deepcopy(self.review))

    def test_no_new_publisher_bypass_from_metadata_validator(self):
        source=(Path(__file__).parent/"branch1_real_python_long_publisher_preflight.py").read_text("utf8")
        for forbidden in (
            "youtube.videos().insert",
            "googleapiclient",
            "oauth2",
            "gh workflow run",
            "publish_youtube(",
            "PUBLISH_ENABLED=true",
        ):
            self.assertNotIn(forbidden,source)

if __name__=="__main__":
    unittest.main()
