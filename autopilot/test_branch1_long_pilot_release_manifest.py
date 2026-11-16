"""Source-only adversarial checks for real Python long release packaging."""
from copy import deepcopy
import json
import unittest

from autopilot.branch1_long_pilot_release_manifest import (
    MANIFEST,LongReviewRefused,validate,EXPECTED_SHA
)

class LongPilotReleaseManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.good=json.loads(MANIFEST.read_text("utf8"))

    def test_exact_real_long_is_review_only(self):
        report=validate(deepcopy(self.good))
        self.assertEqual(report["sha256"],EXPECTED_SHA)
        self.assertEqual(report["run_id"],43880108409)
        self.assertFalse(report["owner_authorized"])
        self.assertFalse(report["audience_growth_proven"])
        self.assertEqual(report["youtube_uploads"],0)
        self.assertEqual(report["youtube_schedules"],0)

    def test_real_media_forgery_and_metric_forgery_refused(self):
        for path,value in (
            (("sha256",),"f"*64),
            (("seconds",),214.831),
            (("artifact_id",),14232431514),
            (("run_id",),0),
            (("app",),"mocked_terminal"),
            (("source_data","raw_rows"),9),
            (("source_data","clean_usd"),"1000.00"),
            (("QA","lufs"),-8.0),
            (("QA","true_peak_dbtp"),0.1),
            (("QA","h264_aac_verified"),False),
            (("QA","static_source_pair_share"),0.99),
            (("QA","owner_full_watch_listen"),True),
            (("audience_growth_proven",),True),
        ):
            with self.subTest(path=path):
                changed=deepcopy(self.good)
                target=changed
                for key in path[:-1]:
                    target=target[key]
                target[path[-1]]=value
                with self.assertRaises(LongReviewRefused):
                    validate(changed)

    def test_no_approval_inferred_from_green_ci(self):
        for field in ("owner_watched_exact_video","facts_reviewed",
                      "rights_reviewed","publishing_authorized"):
            candidate=deepcopy(self.good)
            candidate["approval"][field]=True
            with self.assertRaises(LongReviewRefused):
                validate(candidate)
        for key in ("youtube_uploads","youtube_schedules"):
            candidate=deepcopy(self.good)
            candidate[key]=1
            with self.assertRaises(LongReviewRefused):
                validate(candidate)

    def test_factual_title_cover_and_chapters_bounded(self):
        for path,bad in (
            (("title",),"We Earned $2,656.25 with This Trick"),
            (("description",),"Guaranteed viral real customer profits"),
            (("cover",),"use a fake terminal screenshot"),
            (("chapters",),self.good["chapters"][:4]),
        ):
            candidate=deepcopy(self.good)
            candidate[path[0]]=bad
            with self.assertRaises(LongReviewRefused):
                validate(candidate)
        candidate=deepcopy(self.good)
        candidate["chapters"][2]["start_seconds"]=220
        with self.assertRaises(LongReviewRefused):
            validate(candidate)

if __name__=="__main__":
    unittest.main()
