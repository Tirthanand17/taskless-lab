"""Exact asset/release-status and metadata QA: synthetic mutations only."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from autopilot.branch1_pilot_release_manifest import (
    DEFAULT,ReleaseManifestRefused,validate,
)

class PilotReleaseManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.good=json.loads(DEFAULT.read_text("utf8"))

    def test_two_exact_files_and_no_permission_to_release(self):
        s=validate(deepcopy(self.good))
        self.assertEqual(s["status"],"HASH_LOCKED_OWNER_REVIEW_ONLY")
        self.assertEqual(s["candidates"],2)
        self.assertFalse(s["owner_approved"])
        self.assertFalse(s["audience_recovery_proven"])
        self.assertEqual(s["youtube_uploads"],0)
        self.assertEqual(s["youtube_schedules"],0)

    def test_mismatched_asset_and_provenance_rejected(self):
        for field,bad in (
            ("sha256","f"*64),("actual_seconds",26.541),
            ("episode_id","fake"),("review_artifact","https://invalid.test/file"),
        ):
            with self.subTest(field=field):
                m=deepcopy(self.good)
                m["candidates"][0][field]=bad
                with self.assertRaises(ReleaseManifestRefused):
                    validate(m)
        for field,bad in (
            ("source_main_narrated_run",0),
            ("source_independent_motion_run",0),
            ("report_date","2027-01-01"),
        ):
            m=deepcopy(self.good)
            m[field]=bad
            with self.assertRaises(ReleaseManifestRefused):
                validate(m)

    def test_owner_approval_and_channel_mutations_are_never_inferred(self):
        for key,value in (
            ("owner_full_watch_and_listen_complete",True),
            ("release_signed",True),("auto_publish_enabled",True),
            ("youtube_uploads",1),("youtube_schedules",1),
        ):
            with self.subTest(key=key):
                m=deepcopy(self.good);m[key]=value
                with self.assertRaises(ReleaseManifestRefused):
                    validate(m)
        for app_index in (0,1):
            for flag in ("owner_watched_exact_mp4","facts_reviewed",
                         "rights_reviewed","release_signed"):
                m=deepcopy(self.good);m["candidates"][app_index]["approval"][flag]=True
                with self.assertRaises(ReleaseManifestRefused):
                    validate(m)

    def test_factual_and_mobile_metadata_cannot_be_faked(self):
        bads=(
            (0,"platform_title","Microsoft Excel Fixes"),
            (1,"factual_description","Viral tip!"),
            (0,"hashtags",["#Shorts","#Shorts"]),
            (0,"mobile_cover_brief","fake cover"),
            (0,"mobile_cover_brief","genuine"),
        )
        for index,key,bad in bads:
            with self.subTest(index=index,key=key):
                m=deepcopy(self.good);m["candidates"][index][key]=bad
                with self.assertRaises(ReleaseManifestRefused):
                    validate(m)

    def test_real_postpublication_metrics_are_not_manufactured(self):
        m=deepcopy(self.good)
        m["measurement_fields"].remove("stayed_to_watch_pct")
        with self.assertRaises(ReleaseManifestRefused):
            validate(m)
        m=deepcopy(self.good)
        m["baseline_reference_not_a_target"]["short_stayed_to_watch_pct"]=80
        with self.assertRaises(ReleaseManifestRefused):
            validate(m)

if __name__=="__main__":
    unittest.main()
