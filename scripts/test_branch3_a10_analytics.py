"""Adversarial tests for synthetic Clivox analytics and experiment reporting.

No Google requests; no actual channel analytics. Test scores are invented.
"""
from __future__ import annotations
import copy
import json
import unittest

from scripts.branch3_a10_analytics import (
    POLICY,FIXTURE,AnalyticsDenied,validate_dataset,validate_policy,
    experiment_report,group_stats,
)

def baseline():
    return json.loads(FIXTURE.read_text("utf-8"))

def policy():
    return json.loads(POLICY.read_text("utf-8"))

class A10AnalyticsTests(unittest.TestCase):
    def test_fixture_is_not_mistaken_for_actual_clivox_performance(self):
        r=experiment_report(baseline(),policy())
        self.assertEqual(r["stage"],"A10_SYNTHETIC_ANALYTICS_EXPERIMENT_DRY_RUN")
        self.assertTrue(r["synthetic"])
        self.assertEqual(r["record_count"],12)
        self.assertEqual(r["hypothetical_date"],"2027-02-01")
        self.assertEqual(r["actual_authenticated_analytics_calls"],0)
        self.assertEqual(r["real_clivox_videos_analyzed"],0)
        self.assertFalse(r["personal_or_private_video_ids_exported"])
        self.assertFalse(r["editorial_upload_scheduling_automatic_changes"])
        self.assertFalse(r["fake_virality_or_causal_claims_made"])
        self.assertFalse(r["studio_metrics_available"])
        self.assertTrue(all(not x["enough_for_preliminary_review"]
                            for x in r["experiment_reviews"]))
        self.assertTrue(all(not x["causal_winner_declared"]
                            for x in r["experiment_reviews"]))
        self.assertEqual(r["experiment_reviews"][0]["reason"],
                         "MINIMUM_SAMPLE_NOT_MET")
        self.assertNotIn("A0000000001",json.dumps(r))

    def test_deterministic_report(self):
        self.assertEqual(experiment_report(baseline(),policy()),
                         experiment_report(copy.deepcopy(baseline()),policy()))

    def test_wrong_channel_or_fake_live_status_is_denied(self):
        for key,value in (
            ("channel_id","UCCcL9Q_jqVq6LJmnYUSAFZA"),
            ("source_kind","ACTUAL_YOUTUBE_API_REPORT"),
            ("synthetic",False),
            ("schema_version",2),
        ):
            dataset=baseline()
            dataset[key]=value
            with self.subTest(key=key),self.assertRaises(AnalyticsDenied):
                validate_dataset(dataset)
        p=policy()
        p["live_api_enabled"]=True
        with self.assertRaises(AnalyticsDenied):
            validate_policy(p)

    def test_missing_metrics_remain_null_not_zero(self):
        data=baseline()
        row=data["analytics_api_response"]["rows"][0]
        row[1:]=[None]*6
        report=experiment_report(data,policy())
        self.assertEqual(report["groups"]["comedy"]["A"]["n"],6)
        self.assertIsNone(report["groups"]["comedy"]["A"]["feed_impressions"])
        self.assertIsNone(report["groups"]["comedy"]["A"]["chose_to_view_pct"])
        self.assertIsNone(report["groups"]["comedy"]["A"]["early_retention"])
        self.assertEqual(report["groups"]["comedy"]["A"]["missing_feed_metrics_reason"],
                         "NOT_AVAILABLE_NO_STUDIO_EXPORT")

    def test_reject_forged_studio_metrics_and_percentages(self):
        for metric,value in (
            ("shown_in_feed",1000000),("chose_to_view_pct",93.8),
            ("audience_retention_curve",[100,90,82]),
        ):
            d=baseline()
            d["studio_metrics"][metric]=value
            with self.subTest(metric=metric),self.assertRaises(AnalyticsDenied):
                validate_dataset(d)
        d=baseline()
        d["studio_metrics"]["source"]="YOUTUBE_STUDIO_VERIFIED"
        with self.assertRaises(AnalyticsDenied):
            validate_dataset(d)

    def test_reject_wrong_headers_or_metric_order(self):
        for field,value in (
            ("name","likes"),("columnType","DIMENSION"),
            ("dataType","STRING"),
        ):
            d=baseline()
            d["analytics_api_response"]["columnHeaders"][1][field]=value
            with self.subTest(field=field),self.assertRaises(AnalyticsDenied):
                validate_dataset(d)
        d=baseline()
        d["analytics_api_response"]["columnHeaders"].pop()
        with self.assertRaises(AnalyticsDenied):
            validate_dataset(d)

    def test_reject_bad_metric_values(self):
        for value in (-1,True,"1200",float("nan"),float("inf"),2.7):
            d=baseline()
            d["analytics_api_response"]["rows"][0][1]=value
            with self.subTest(value=str(value)),self.assertRaises(AnalyticsDenied):
                validate_dataset(d)
        d=baseline()
        d["analytics_api_response"]["rows"][0][2]=10**9
        with self.assertRaises(AnalyticsDenied):
            validate_dataset(d)
        d=baseline()
        d["analytics_api_response"]["rows"][0][5]=10**9
        with self.assertRaises(AnalyticsDenied):
            validate_dataset(d)

    def test_no_unmatched_duplicate_or_private_ids_exported(self):
        d=baseline()
        d["analytics_api_response"]["rows"][1][0]=d["analytics_api_response"]["rows"][0][0]
        with self.assertRaises(AnalyticsDenied):
            validate_dataset(d)
        d=baseline()
        d["analytics_api_response"]["rows"][0][0]="OTHER_CHA!!"
        with self.assertRaises(AnalyticsDenied):
            validate_dataset(d)
        d=baseline()
        d["video_annotations"].append(copy.deepcopy(d["video_annotations"][0]))
        with self.assertRaises(AnalyticsDenied):
            validate_dataset(d)

    def test_no_false_editorial_approval_or_untracked_category(self):
        d=baseline()
        d["video_annotations"][0]["editorial_verified"]=True
        with self.assertRaises(AnalyticsDenied):
            validate_dataset(d)
        d=baseline()
        d["video_annotations"][0]["category"]="not_permitted"
        with self.assertRaises(AnalyticsDenied):
            validate_dataset(d)

    def test_no_premature_experiment_winner_even_with_large_sample(self):
        d=baseline()
        d["video_annotations"]=[]
        d["analytics_api_response"]["rows"]=[]
        for i in range(24):
            item=copy.deepcopy(baseline()["video_annotations"][i%12])
            item["video_id"]="A"+f"{i+1:010d}"
            d["video_annotations"].append(item)
            row=list(baseline()["analytics_api_response"]["rows"][i%12])
            row[0]=item["video_id"]
            d["analytics_api_response"]["rows"].append(row)
        result=experiment_report(d,policy())
        item=result["experiment_reviews"][0]
        self.assertTrue(item["enough_for_preliminary_review"])
        self.assertEqual(item["reason"],"HUMAN_REVIEW_REQUIRED_EVEN_AFTER_SAMPLE_THRESHOLD")
        self.assertFalse(item["causal_winner_declared"])
        self.assertFalse(item["real_optimization_decision_authorized"])

    def test_empty_group_and_zero_denominator_do_not_invent_rates(self):
        s=group_stats([
            {"views":0,"engagedViews":0,"shares":0,"subscribersGained":0,
             "averageViewPercentage":None}
        ])
        self.assertIsNone(s["median_shares_per_1000_engaged"])
        self.assertIsNone(s["median_subs_gained_per_1000_engaged"])
        self.assertEqual(s["median_engaged_views"],0)
        self.assertIsNone(s["feed_impressions"])

    def test_policy_disallows_live_or_publish(self):
        for key in (
            "source_channel_oauth_connected","live_api_enabled","publish_enabled"
        ):
            p=policy();p[key]=True
            with self.subTest(key=key),self.assertRaises(AnalyticsDenied):
                validate_policy(p)
        p=policy();p["actual_video_count"]=3
        with self.assertRaises(AnalyticsDenied):
            validate_policy(p)
        p=policy();p["analytics_scope"]="https://www.googleapis.com/auth/youtube.upload"
        with self.assertRaises(AnalyticsDenied):
            validate_policy(p)

if __name__=="__main__":
    unittest.main()
