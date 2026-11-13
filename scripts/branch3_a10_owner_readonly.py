"""CLIVOX A10: owner-manual private read-only YouTube Analytics REPORT preview.

A genuine live run requires distinct owner-approved OAuth for exactly
youtube.readonly + yt-analytics.readonly, and a protected main-only environment.
Only 3 HTTPS requests: refresh token, channels.mine, bounded Analytics sample.
NO upload, source media, video IDs, private metrics rows, audience identities,
auto-optimization or scheduling. Current repo has no OAuth credentials.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone, date
import http.client
import json
import os
import re
import ssl
from urllib.parse import urlencode, urlsplit, parse_qs

from scripts.branch3_a7_readonly_youtube import (
    EXPECTED_CHANNEL, YOUTUBE_HOST, OAUTH_HOST, CHANNEL_PATH,
    READONLY_SCOPE, VIDEO_ID, validate_channels_mine, ChannelBindingDenied
)
from scripts.branch3_a10_analytics import (
    METRICS, header_map, _numeric, AnalyticsDenied
)

REPO="Tirthanand17/taskless-lab"
WORKFLOW_REF=(REPO+
    "/.github/workflows/branch3-clivox-a10-owner-readonly.yml@refs/heads/main")
ANALYTICS_HOST="youtubeanalytics.googleapis.com"
ANALYTICS_SCOPE="https://www.googleapis.com/auth/yt-analytics.readonly"
APPROVAL_ENV="CLIVOX_A10_ANALYTICS_READ_APPROVED"
APPROVAL_VALUE="approved-clivox-a10-readonly-v1"
CLIENT_ENV="CLIVOX_A10_ANALYTICS_CLIENT_ID"
SECRET_ENV="CLIVOX_A10_ANALYTICS_CLIENT_SECRET"
REFRESH_ENV="CLIVOX_A10_ANALYTICS_REFRESH_TOKEN"
WINDOW_DAYS=7
LAG_DAYS=2
MAX_ROWS=50
MAX_REPLY=240_000
HEX_HEADER=re.compile(r"[A-Za-z0-9_-]{11}\Z")


class OwnerAnalyticsDenied(ValueError):
    """No credentials, private video identifiers, or raw Google data in errors."""


def require(ok:bool,reason:str)->None:
    if not ok:
        raise OwnerAnalyticsDenied("CLIVOX_A10_READONLY_DENIED_"+reason)


def require_context(env:Mapping[str,str])->None:
    for key,value in (
        ("GITHUB_ACTIONS","true"),
        ("GITHUB_REPOSITORY",REPO),
        ("GITHUB_EVENT_NAME","workflow_dispatch"),
        ("GITHUB_REF","refs/heads/main"),
        ("GITHUB_WORKFLOW_REF",WORKFLOW_REF),
        ("GITHUB_ACTOR","Tirthanand17"),
        ("GITHUB_TRIGGERING_ACTOR","Tirthanand17"),
        ("GITHUB_RUN_ATTEMPT","1"),
        (APPROVAL_ENV,APPROVAL_VALUE)
    ):
        require(env.get(key)==value,"OWNER_MANUAL_CONTEXT_"+key)
    client=env.get(CLIENT_ENV)
    require(type(client) is str
            and 20<len(client)<300
            and client.endswith(".apps.googleusercontent.com")
            and not any(c in client for c in ("\n","\r")),
            "DISTINCT_ANALYTICS_CLIENT_ID")
    for key in (SECRET_ENV,REFRESH_ENV):
        val=env.get(key)
        require(type(val) is str and 10<len(val)<4000
                and not any(c in val for c in ("\n","\r")),
                "ANALYTICS_SECRET_MISSING_"+key)


def date_window(now:datetime)->tuple[str,str]:
    require(type(now) is datetime and now.tzinfo is not None
            and now.utcoffset() is not None,"UTC_CLOCK_REQUIRED")
    require(now.year>=2026,"CLOCK_IN_PAST")
    end=now.astimezone(timezone.utc).date()-timedelta(days=LAG_DAYS)
    start=end-timedelta(days=WINDOW_DAYS-1)
    return start.isoformat(),end.isoformat()


def report_path(start:str,end:str)->str:
    try:
        st=date.fromisoformat(start)
        en=date.fromisoformat(end)
    except (ValueError,TypeError):
        raise OwnerAnalyticsDenied("CLIVOX_A10_READONLY_DENIED_BAD_DATE") from None
    require(type(start) is str and type(end) is str
            and start==st.isoformat() and end==en.isoformat()
            and (en-st).days==WINDOW_DAYS-1
            and st>=date(2026,1,1),
            "REPORT_WINDOW")
    return "/v2/reports?"+urlencode({
        "ids":"channel==MINE",
        "startDate":start,
        "endDate":end,
        "metrics":",".join(METRICS),
        "dimensions":"video",
        "sort":"-views",
        "maxResults":str(MAX_ROWS)
    })


def validate_request(host:str,method:str,path:str,
                     body:bytes|None,bearer:str|None)->None:
    require(type(path) is str and len(path)<=1500
            and all(s not in path.lower() for s in
                    ("\r","\n","#","client_secret","refresh_token","access_token")),
            "UNSAFE_QUERY")
    if host==OAUTH_HOST:
        require(method=="POST" and path=="/token"
                and type(body) is bytes and 0<len(body)<=16000
                and bearer is None,"OAUTH_REFRESH_ONLY")
    elif host==YOUTUBE_HOST:
        require(method=="GET" and path==CHANNEL_PATH
                and body is None and type(bearer) is str
                and 20<len(bearer)<4096 and not any(s in bearer for s in ("\n","\r")),
                "CLIVOX_CHANNEL_IDENTITY_GET_ONLY")
    else:
        require(host==ANALYTICS_HOST
                and method=="GET" and body is None
                and type(bearer) is str and 20<len(bearer)<4096
                and not any(s in bearer for s in ("\n","\r")),
                "ANALYTICS_GET_ONLY")
        u=urlsplit(path)
        require(u.scheme=="" and u.netloc=="" and u.fragment==""
                and u.path=="/v2/reports","ANALYTICS_ONLY_REPORTS_PATH")
        try:
            q=parse_qs(u.query,strict_parsing=True)
            require(set(q)=={
                "ids","startDate","endDate","metrics","dimensions","sort",
                "maxResults"
            } and all(len(v)==1 for v in q.values()),"METRICS_QUERY_KEYS")
            require(path==report_path(
                q["startDate"][0],q["endDate"][0]
            ),"CANONICAL_REPORT_QUERY_ONLY")
        except (ValueError,KeyError):
            raise OwnerAnalyticsDenied(
                "CLIVOX_A10_READONLY_DENIED_METRICS_QUERY"
            ) from None


def google_json(host:str,method:str,path:str,
                body:bytes|None=None,bearer:str|None=None)->dict:
    validate_request(host,method,path,body,bearer)
    connection=None
    try:
        connection=http.client.HTTPSConnection(
            host,timeout=12,context=ssl.create_default_context()
        )
        headers={"Accept":"application/json",
                 "User-Agent":"clivox-a10-owner-only-aggregated-readonly"}
        if bearer is not None:
            headers["Authorization"]="Bearer "+bearer
        if body is not None:
            headers["Content-Type"]="application/x-www-form-urlencoded"
        connection.request(method,path,body=body,headers=headers)
        response=connection.getresponse()
        raw=response.read(MAX_REPLY+1)
        require(response.status==200 and len(raw)<=MAX_REPLY,
                "REMOTE_NOT_200_OR_TOO_LARGE")
        obj=json.loads(raw.decode("utf-8"))
        require(type(obj) is dict,"GOOGLE_JSON_OBJECT")
        return obj
    except OwnerAnalyticsDenied:
        raise
    except (OSError,TimeoutError,ValueError,http.client.HTTPException):
        raise OwnerAnalyticsDenied(
            "CLIVOX_A10_READONLY_DENIED_REMOTE_AUTH_OR_NETWORK"
        ) from None
    finally:
        if connection is not None:
            connection.close()


def refresh_analytics_token(env:Mapping[str,str],*,http_call=google_json)->str:
    form=urlencode({
        "client_id":env[CLIENT_ENV],
        "client_secret":env[SECRET_ENV],
        "refresh_token":env[REFRESH_ENV],
        "grant_type":"refresh_token"
    }).encode("ascii")
    data=http_call(OAUTH_HOST,"POST","/token",form,None)
    require(type(data) is dict
            and data.get("token_type")=="Bearer"
            and type(data.get("access_token")) is str
            and 20<len(data["access_token"])<4096,
            "ACCESS_TOKEN")
    granted=data.get("scope")
    require(type(granted) is str
            and set(granted.split())=={
                READONLY_SCOPE,ANALYTICS_SCOPE
            } and len(granted.split())==2,
            "STRICT_DUAL_READONLY_SCOPES")
    return data["access_token"]


def parse_report(reply:dict)->dict:
    require(type(reply) is dict
            and reply.get("kind")=="youtubeAnalytics#resultTable",
            "REPORT_KIND")
    headers=reply.get("columnHeaders")
    try:
        mapping=header_map(headers)
    except AnalyticsDenied:
        raise OwnerAnalyticsDenied(
            "CLIVOX_A10_READONLY_DENIED_REPORT_COLUMNS"
        ) from None
    rows=reply.get("rows",[])
    require(type(rows) is list and len(rows)<=MAX_ROWS,"MAX_REPORT_ROWS")
    observed=set()
    totals={k:0 for k in (
        "views","engagedViews","shares","subscribersGained"
    )}
    known={k:0 for k in totals}
    durations=[]
    pcts=[]
    for row in rows:
        require(type(row) is list and len(row)==len(mapping),
                "REPORT_ROW_WIDTH")
        vid=row[mapping["video"]]
        require(type(vid) is str and VIDEO_ID.fullmatch(vid) is not None
                and vid not in observed,"DUPLICATE_OR_BAD_PRIVATE_ID")
        observed.add(vid)
        try:
            values={k:_numeric(row[mapping[k]],k) for k in METRICS}
        except AnalyticsDenied:
            raise OwnerAnalyticsDenied(
                "CLIVOX_A10_READONLY_DENIED_METRIC_VALUE"
            ) from None
        if values["views"] is not None and values["engagedViews"] is not None:
            require(values["engagedViews"]<=values["views"],
                    "ENGAGED_EXCEEDS_VIEWS")
        if values["shares"] is not None and values["engagedViews"] is not None:
            require(values["shares"]<=values["engagedViews"],
                    "SHARES_EXCEED_ENGAGED")
        for metric in totals:
            if values[metric] is not None:
                totals[metric]+=values[metric]
                known[metric]+=1
        if values["averageViewDuration"] is not None:
            durations.append(values["averageViewDuration"])
        if values["averageViewPercentage"] is not None:
            pcts.append(values["averageViewPercentage"])
    return {
        "sample_video_row_count":len(rows),
        "counts_in_bounded_sample":{
            k:(totals[k] if known[k]==len(rows) and len(rows)>0
               else None) for k in totals
        },
        "mean_reported_avg_view_duration_seconds":(
            round(sum(durations)/len(durations),3)
            if len(durations)==len(rows) and len(rows)>0 else None
        ),
        "mean_reported_avg_view_percentage":(
            round(sum(pcts)/len(pcts),3)
            if len(pcts)==len(rows) and len(rows)>0 else None
        ),
        "all_video_identifiers_redacted":True,
        "sample_exhaustiveness_proven":False,
        "valid_causal_ab_test_proven":False,
        "shorts_feed_swipe_or_retention_curve_available":False,
        "no_rows_means_no_observation_not_zero_channel_audience":True,
    }


def run_owner_readonly(env:Mapping[str,str], *,
                       http_call=google_json,
                       now:datetime|None=None)->dict:
    require_context(env)
    token=refresh_analytics_token(env,http_call=http_call)
    channel=http_call(YOUTUBE_HOST,"GET",CHANNEL_PATH,None,token)
    try:
        identity=validate_channels_mine(channel)
    except ChannelBindingDenied:
        raise OwnerAnalyticsDenied(
            "CLIVOX_A10_READONLY_DENIED_WRONG_AUTHORIZED_CHANNEL"
        ) from None
    require(identity["expected_channel_id"]==EXPECTED_CHANNEL,
            "WRONG_BRAND_ACCOUNT")
    start,end=date_window(
        datetime.now(timezone.utc) if now is None else now
    )
    report=http_call(
        ANALYTICS_HOST,"GET",report_path(start,end),None,token
    )
    parsed=parse_report(report)
    return {
        "stage":"A10_CLIVOX_OWNER_READONLY_BOUNDED_ACTUAL_ANALYTICS",
        "channel_id":EXPECTED_CHANNEL,
        "owner_account_identity_verified":True,
        "report_start_utc_date":start,
        "report_end_utc_date":end,
        "lag_days":LAG_DAYS,
        "youtube_readonly_scope_verified":True,
        "yt_analytics_readonly_scope_verified":True,
        "google_oauth_refresh_post_count":1,
        "youtube_identity_get_count":1,
        "youtube_analytics_get_count":1,
        "actual_google_write_calls":0,
        "report":parsed,
        "no_editorial_or_scheduling_changes_made":True,
        "no_private_video_ids_or_oauth_tokens_logged":True,
        "audience_retention_curves_verified":False,
        "real_time_complete_audience_coverage_proven":False,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
        "note":"Owner-only bounded nonmonetary sample; live mode needs real protected Clivox OAuth consent."
    }


def fixture_report()->dict:
    return {
        "stage":"A10_CLIVOX_OWNER_READONLY_ADAPTER_OFFLINE_NOT_CONNECTED",
        "channel_id":EXPECTED_CHANNEL,
        "strict_dual_readonly_scopes_required":True,
        "channel_identity_before_reports_required":True,
        "analytics_report_sample_max_rows":MAX_ROWS,
        "real_owner_google_oauth_consent_completed":False,
        "real_analytics_report_checked":False,
        "actual_google_requests":0,
        "real_clivox_video_metrics_observed":False,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
    }


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("fixture","live"),default="fixture")
    args=p.parse_args()
    try:
        result=(
            fixture_report() if args.mode=="fixture" else
            run_owner_readonly(os.environ)
        )
    except (OwnerAnalyticsDenied,ValueError,KeyError,TypeError):
        raise SystemExit(
            "CLIVOX_A10_OWNER_READONLY_DENIED_NO_GOOGLE_WRITES_NO_UPLOAD"
        ) from None
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
