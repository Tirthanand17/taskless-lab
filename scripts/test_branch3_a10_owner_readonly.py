"""A10 nonmonetary owner-only Google Analytics read-only adapter mocks."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
import unittest

from scripts.branch3_a7_readonly_youtube import (
    EXPECTED_CHANNEL, OLD_CHANNEL, READONLY_SCOPE,
    CHANNEL_PATH, FIXTURE_CHANNEL, YOUTUBE_HOST, OAUTH_HOST
)
from scripts.branch3_a10_analytics import METRICS
from scripts.branch3_a10_owner_readonly import (
    ANALYTICS_HOST, ANALYTICS_SCOPE, APPROVAL_ENV, APPROVAL_VALUE,
    CLIENT_ENV, SECRET_ENV, REFRESH_ENV, WORKFLOW_REF, MAX_ROWS,
    OwnerAnalyticsDenied, date_window, report_path, parse_report,
    run_owner_readonly, validate_request, require_context, fixture_report
)

ACCESS="SYNTHETIC_ACCESS_ONLY_NEVER_REAL_000001"
NOW=datetime(2026,11,13,12,tzinfo=timezone.utc)
VID1="A234567890a"
VID2="B234567890b"


def env():
    return {
        "GITHUB_ACTIONS":"true",
        "GITHUB_REPOSITORY":"Tirthanand17/taskless-lab",
        "GITHUB_EVENT_NAME":"workflow_dispatch",
        "GITHUB_REF":"refs/heads/main",
        "GITHUB_WORKFLOW_REF":WORKFLOW_REF,
        "GITHUB_ACTOR":"Tirthanand17",
        "GITHUB_TRIGGERING_ACTOR":"Tirthanand17",
        "GITHUB_RUN_ATTEMPT":"1",
        APPROVAL_ENV:APPROVAL_VALUE,
        CLIENT_ENV:"1234567890123456789-abc.apps.googleusercontent.com",
        SECRET_ENV:"SYNTHETIC_ANALYTICS_SECRET_NEVER_REAL",
        REFRESH_ENV:"SYNTHETIC_ANALYTICS_REFRESH_NEVER_REAL",
    }


def report(rows=None):
    names=["video",*METRICS]
    ints={"views","engagedViews","shares","subscribersGained"}
    headers=[{
        "name":n,
        "columnType":"DIMENSION" if i==0 else "METRIC",
        "dataType":"STRING" if i==0 else ("INTEGER" if n in ints else "FLOAT"),
    } for i,n in enumerate(names)]
    return {
        "kind":"youtubeAnalytics#resultTable",
        "columnHeaders":headers,
        "rows":[[VID1,100,60,13.2,52.0,3,1],
                [VID2,120,90,14.4,63.0,2,1]] if rows is None else rows,
    }


def synthetic_api(calls,*,kind=None,scope=None,channel=None,
                  analytics=None):
    def invoke(host,method,path,body,bearer):
        calls.append((host,method,path,body,bearer))
        if host==OAUTH_HOST:
            return {
                "token_type":"Bearer",
                "access_token":ACCESS,
                "scope":scope if scope is not None else
                        READONLY_SCOPE+" "+ANALYTICS_SCOPE
            }
        if host==YOUTUBE_HOST:
            assert method=="GET" and path==CHANNEL_PATH
            obj=json.loads(FIXTURE_CHANNEL.read_text("utf-8"))
            if channel is not None:
                obj["items"][0]["id"]=channel
            return obj
        assert host==ANALYTICS_HOST and method=="GET"
        return copy.deepcopy(report() if analytics is None else analytics)
    return invoke


class A10OwnerReadOnlyTests(unittest.TestCase):

    def test_genuine_shape_still_no_upload_or_private_rows(self):
        calls=[]
        r=run_owner_readonly(env(),http_call=synthetic_api(calls),now=NOW)
        self.assertTrue(r["owner_account_identity_verified"])
        self.assertEqual((r["report_start_utc_date"],r["report_end_utc_date"]),
                         ("2026-11-05","2026-11-11"))
        self.assertEqual(r["report"]["sample_video_row_count"],2)
        self.assertEqual(r["report"]["counts_in_bounded_sample"]["views"],220)
        self.assertEqual(r["report"]["counts_in_bounded_sample"]["engagedViews"],150)
        self.assertEqual(r["report"]["mean_reported_avg_view_duration_seconds"],13.8)
        self.assertEqual(r["report"]["mean_reported_avg_view_percentage"],57.5)
        self.assertFalse(r["real_time_complete_audience_coverage_proven"])
        self.assertFalse(r["report"]["sample_exhaustiveness_proven"])
        self.assertEqual([c[1] for c in calls],["POST","GET","GET"])
        self.assertEqual([c[0] for c in calls],
                         [OAUTH_HOST,YOUTUBE_HOST,ANALYTICS_HOST])
        self.assertEqual(calls[2][2],
                         report_path("2026-11-05","2026-11-11"))
        self.assertEqual(r["actual_google_write_calls"],0)
        for field in ("youtube_upload_authorized",
                      "youtube_schedule_authorized",
                      "youtube_publish_authorized"):
            self.assertFalse(r[field],field)
        txt=json.dumps(r)
        for secret in (ACCESS,VID1,VID2,
                       env()[REFRESH_ENV],env()[SECRET_ENV]):
            self.assertNotIn(secret,txt)

    def test_no_rows_are_unknown_not_zero(self):
        res=run_owner_readonly(env(),http_call=synthetic_api(
            [],analytics=report([])),now=NOW)
        self.assertEqual(res["report"]["sample_video_row_count"],0)
        self.assertTrue(res["report"]["no_rows_means_no_observation_not_zero_channel_audience"])
        self.assertIsNone(res["report"]["counts_in_bounded_sample"]["views"])
        self.assertIsNone(res["report"]["mean_reported_avg_view_percentage"])

    def test_missing_metrics_kept_null(self):
        d=report()
        d["rows"][1][1]=None
        res=parse_report(d)
        self.assertIsNone(res["counts_in_bounded_sample"]["views"])
        self.assertEqual(res["counts_in_bounded_sample"]["engagedViews"],150)

    def test_owner_main_manual_approval_and_distinct_secrets_required(self):
        for key,val in (
            ("GITHUB_ACTIONS","false"),
            ("GITHUB_REPOSITORY","Other/repo"),
            ("GITHUB_EVENT_NAME","pull_request"),
            ("GITHUB_REF","refs/heads/bad"),
            ("GITHUB_WORKFLOW_REF","Other/flow"),
            ("GITHUB_ACTOR","Other"),
            ("GITHUB_TRIGGERING_ACTOR","Other"),
            ("GITHUB_RUN_ATTEMPT","2"),
            (APPROVAL_ENV,"approved")
        ):
            test_env=env();test_env[key]=val
            calls=[]
            with self.subTest(key=key),self.assertRaises(OwnerAnalyticsDenied):
                run_owner_readonly(
                    test_env,http_call=synthetic_api(calls),now=NOW
                )
            self.assertEqual(calls,[])
        for key in (APPROVAL_ENV,CLIENT_ENV,SECRET_ENV,REFRESH_ENV):
            test_env=env();test_env.pop(key)
            with self.subTest(key=key),self.assertRaises(OwnerAnalyticsDenied):
                require_context(test_env)

    def test_wrong_brand_account_denied_before_analytics(self):
        calls=[]
        with self.assertRaises(OwnerAnalyticsDenied):
            run_owner_readonly(env(),http_call=synthetic_api(
                calls,channel=OLD_CHANNEL),now=NOW)
        self.assertEqual([c[0] for c in calls],[OAUTH_HOST,YOUTUBE_HOST])

    def test_only_both_exact_read_only_scopes_accepted(self):
        for scope in (
            READONLY_SCOPE,
            ANALYTICS_SCOPE,
            READONLY_SCOPE+" "+ANALYTICS_SCOPE+" https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube",
            "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
            READONLY_SCOPE+" "+READONLY_SCOPE+" "+ANALYTICS_SCOPE
        ):
            calls=[]
            with self.subTest(scope=scope),self.assertRaises(OwnerAnalyticsDenied):
                run_owner_readonly(env(),http_call=synthetic_api(
                    calls,scope=scope),now=NOW)
            self.assertEqual([c[0] for c in calls],[OAUTH_HOST])

    def test_bad_rows_video_ids_count_types_and_percentages_denied(self):
        for rows in (
            [[VID1,100,101,13.2,52.0,3,1]],
            [[VID1,100,60,13.2,52.0,61,1]],
            [[VID1,True,0,13.2,52.0,0,0]],
            [[VID1,-1,0,13.2,52.0,0,0]],
            [[VID1,100,60,13.2,10001,3,1]],
            [[VID1,100,60,13.2,52.0,3]],
            [[VID1,100,60,13.2,52.0,3,1],
             [VID1,120,90,14.4,63.0,2,1]],
            [["wrong_id",100,60,13.2,52.0,3,1]]
        ):
            with self.subTest(rows=rows),self.assertRaises(OwnerAnalyticsDenied):
                parse_report(report(rows))

    def test_bad_headers_shape_or_kind_denied(self):
        for mutate in (
            lambda d:d.update(kind="youtube#videoListResponse"),
            lambda d:d["columnHeaders"].pop(),
            lambda d:d["columnHeaders"][1].update(name="estimatedRevenue"),
            lambda d:d["columnHeaders"][2].update(columnType="DIMENSION")
        ):
            d=report();mutate(d)
            with self.assertRaises(OwnerAnalyticsDenied):
                parse_report(d)

    def test_bound_max_rows_and_unknown_exhaustiveness(self):
        many=report([[f"A{i:010d}",100,70,15.0,40.0,2,1]
                     for i in range(MAX_ROWS+1)])
        with self.assertRaises(OwnerAnalyticsDenied):
            parse_report(many)
        sample=parse_report(report())
        self.assertFalse(sample["sample_exhaustiveness_proven"])
        self.assertFalse(sample["valid_causal_ab_test_proven"])
        self.assertFalse(sample["shorts_feed_swipe_or_retention_curve_available"])

    def test_transport_allowlist_rejects_write_other_hosts_and_injection(self):
        path=report_path("2026-11-05","2026-11-11")
        for args in (
            (YOUTUBE_HOST,"POST",CHANNEL_PATH,None,ACCESS),
            (YOUTUBE_HOST,"GET","/youtube/v3/videos?part=status",None,ACCESS),
            (ANALYTICS_HOST,"POST",path,None,ACCESS),
            (ANALYTICS_HOST,"GET",path+"&id=secret",None,ACCESS),
            (ANALYTICS_HOST,"GET",path.replace("channel%3D%3DMINE","channel%3D%3DOTHER"),None,ACCESS),
            (ANALYTICS_HOST,"GET",path+"&client_secret=evil",None,ACCESS),
            (ANALYTICS_HOST,"GET",path+"#fragment",None,ACCESS),
            ("evil.example","GET",path,None,ACCESS),
            (OAUTH_HOST,"DELETE","/token",None,None)
        ):
            with self.subTest(args=args),self.assertRaises(OwnerAnalyticsDenied):
                validate_request(*args)

    def test_exact_date_window_is_immutable_and_not_future(self):
        self.assertEqual(date_window(NOW),("2026-11-05","2026-11-11"))
        for st,en in (
            ("2026-11-05","2026-11-12"),
            ("2026-11-11","2026-11-05"),
            ("2026-11-05","INVALID"),
            ("2026-11-05%00","2026-11-11")
        ):
            with self.assertRaises(OwnerAnalyticsDenied):
                report_path(st,en)

    def test_fixture_is_not_live_analytics(self):
        v=fixture_report()
        self.assertFalse(v["real_owner_google_oauth_consent_completed"])
        self.assertFalse(v["real_analytics_report_checked"])
        self.assertEqual(v["actual_google_requests"],0)
        self.assertFalse(v["real_clivox_video_metrics_observed"])
        self.assertFalse(v["youtube_publish_authorized"])


if __name__=="__main__":
    unittest.main()
