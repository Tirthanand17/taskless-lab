"""Clivox A10: safe YouTube Analytics reports parser + experiment review.

NO network, OAuth, publishing, media or actual channel analytics. The only
accepted dataset in this milestone is unmistakably SYNTHETIC. Output never
contains private video IDs or claims real Clivox audience measurements.

Analytics API source format: https://developers.google.com/youtube/analytics/reference/reports/query
Analytics metrics: https://developers.google.com/youtube/analytics/metrics
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
from datetime import date
import hashlib
import json
from pathlib import Path
import re
from statistics import median

CHANNEL="UCfPEvy0SefE_5nNlYlY_CyQ"
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/"branch3/a10/fixtures/synthetic-analytics-export.json"
POLICY=ROOT/"branch3/a10/analytics-policy.json"
CATEGORIES=frozenset({"gaming","livestream","comedy","entertainment","podcast_interview"})
METRICS=("views","engagedViews","averageViewDuration","averageViewPercentage",
         "shares","subscribersGained")
DIMENSIONS=("video",)
MAX_RECORDS=250
VID=re.compile(r"[A-Za-z0-9_-]{11}\Z")

class AnalyticsDenied(ValueError):
    pass

def require(ok:bool,why:str)->None:
    if not ok: raise AnalyticsDenied("CLIVOX_A10_DENY_"+why)

def read_json(path:Path)->dict:
    require(path.is_file() and not path.is_symlink() and
            path.stat().st_size<300_000,"INPUT_FILE")
    d=json.loads(path.read_text("utf-8"))
    require(type(d) is dict,"INPUT_OBJECT")
    return d

def validate_policy(p:dict)->None:
    require(type(p) is dict and set(p)=={
        "schema_version","channel_id","stage","execution_mode",
        "analytics_scope","video_report_metrics","studio_only_metrics",
        "minimum_examples_per_arm","reported_windows_days",
        "source_channel_oauth_connected","live_api_enabled",
        "actual_video_count","synthetic_testing_only","publish_enabled",
        "public_ci_outputs_no_video_ids","handling_missing_metrics","notes"
    },"POLICY_FIELDS")
    require(p["schema_version"]==1 and p["channel_id"]==CHANNEL
            and p["stage"]=="A10_EXPERIMENT_EVALUATOR"
            and p["execution_mode"]=="SYNTHETIC_OFFLINE_ONLY","STAGE")
    require(p["analytics_scope"]=="https://www.googleapis.com/auth/yt-analytics.readonly"
            and p["video_report_metrics"]==list(METRICS),"API_SCOPE_OR_METRICS")
    require(p["studio_only_metrics"]==[
        "shown_in_feed","chose_to_view_pct","audience_retention_curve"
    ],"STUDIO_NOT_SEPARATE")
    require(p["reported_windows_days"]==[1,3,7,14]
            and p["minimum_examples_per_arm"]==10,"WINDOW_OR_THRESHOLD")
    for key in ("source_channel_oauth_connected","live_api_enabled","publish_enabled"):
        require(p[key] is False,"LIVE_ACCESS_"+key)
    require(p["actual_video_count"]==0 and p["synthetic_testing_only"] is True
            and p["public_ci_outputs_no_video_ids"] is True
            and p["handling_missing_metrics"]=="NULL_NEVER_ZERO","FAKE_LIVE_DATA")

def header_map(headers:list)->dict:
    require(type(headers) is list and len(headers)==1+len(METRICS),
            "API_HEADERS_LENGTH")
    expected=["video",*METRICS]
    mapping={}
    for n,h in enumerate(headers):
        require(type(h) is dict and set(h)>={"name","columnType","dataType"},
                "API_HEADER")
        name=h["name"]
        require(name==expected[n],"API_HEADER_ORDER")
        require(h["columnType"]==("DIMENSION" if n==0 else "METRIC"),
                "API_COLUMN_TYPE")
        require(h["dataType"] in (("STRING",) if n==0 else ("INTEGER","FLOAT")),
                "API_DATA_TYPE")
        mapping[name]=n
    return mapping

def _numeric(v:object,metric:str)->int|float|None:
    if v is None: return None
    require(type(v) in (int,float) and v==v
            and v not in (float("inf"),-float("inf")) and v>=0,
            "METRIC_INVALID_"+metric)
    if metric in ("views","engagedViews","shares","subscribersGained"):
        require(type(v) is int,"COUNT_MUST_BE_INTEGER_"+metric)
    if metric=="averageViewPercentage":
        # It can exceed 100 with repeat viewing / loops in some reports;
        # do not arbitrarily cap to 100.
        require(v<=10000,"VIEW_PERCENT_PLAUSIBILITY")
    elif metric=="averageViewDuration":
        require(v<=3600*12,"DURATION_PLAUSIBILITY")
    return v

def validate_dataset(d:dict)->list[dict]:
    require(type(d) is dict and set(d)=={
        "schema_version","channel_id","source_kind","synthetic",
        "hypothetical_observation_date","window_days",
        "video_annotations","analytics_api_response","studio_metrics"
    },"DATASET_FIELDS")
    require(d["schema_version"]==1 and d["channel_id"]==CHANNEL
            and d["source_kind"]=="SYNTHETIC_YOUTUBE_ANALYTICS_API_RESPONSE"
            and d["synthetic"] is True,"NOT_SYNTHETIC_OR_WRONG_CHANNEL")
    require(type(d["hypothetical_observation_date"]) is str
            and date.fromisoformat(d["hypothetical_observation_date"])>=date(2027,1,1),
            "INVALID_SYNTHETIC_DATE")
    require(d["window_days"] in (1,3,7,14) and type(d["window_days"]) is int,
            "UNSUPPORTED_WINDOW")
    annotations=d["video_annotations"]
    require(type(annotations) is list and 1<=len(annotations)<=MAX_RECORDS,"ANNOTATIONS")
    by_id={}
    for a in annotations:
        require(type(a) is dict and set(a)=={
            "video_id","category","hook_variant","duration_seconds","editorial_verified"
        },"ANNOTATION_FIELDS")
        vid=a["video_id"]
        require(type(vid) is str and VID.fullmatch(vid) is not None and
                vid not in by_id,"VIDEO_ID_DUP")
        require(a["category"] in CATEGORIES and a["hook_variant"] in ("A","B"),
                "GROUP")
        require(type(a["duration_seconds"]) is int
                and 10<=a["duration_seconds"]<=180,"DURATION")
        require(a["editorial_verified"] is False,"FORGED_ACTUAL_EDITORIAL")
        by_id[vid]=a
    api=d["analytics_api_response"]
    require(type(api) is dict and set(api)=={"kind","columnHeaders","rows"},
            "API_FIELDS")
    require(api["kind"]=="youtubeAnalytics#resultTable","API_KIND")
    m=header_map(api["columnHeaders"])
    rows=api["rows"]
    require(type(rows) is list and len(rows)==len(by_id),"API_ROWS")
    observed=set()
    records=[]
    for row in rows:
        require(type(row) is list and len(row)==len(m),"API_ROW_COLUMNS")
        vid=row[0]
        require(type(vid) is str and vid in by_id and vid not in observed,
                "UNMATCHED_OR_DUPLICATE_ID")
        observed.add(vid)
        values={metric:_numeric(row[m[metric]],metric) for metric in METRICS}
        if values["engagedViews"] is not None and values["views"] is not None:
            require(values["engagedViews"]<=values["views"],"ENGAGED_EXCEEDS_VIEWS")
        if values["shares"] is not None and values["engagedViews"] is not None:
            require(values["shares"]<=values["engagedViews"],"SHARES_EXCEED_ENGAGED")
        records.append({**by_id[vid],**values})
    studio=d["studio_metrics"]
    require(type(studio) is dict and set(studio)=={
        "source","shown_in_feed","chose_to_view_pct","audience_retention_curve"
    },"STUDIO_FIELDS")
    require(studio["source"]=="NOT_AVAILABLE_NO_STUDIO_EXPORT" and
            all(studio[k] is None for k in (
                "shown_in_feed","chose_to_view_pct","audience_retention_curve"
            )),"FAKE_STUDIO_METRICS")
    return records

def median_or_none(values:list)->int|float|None:
    return median(values) if values else None

def group_stats(rows:list[dict])->dict:
    # Null when data is genuinely unavailable; never infer missing as zero.
    views=[x["views"] for x in rows if x["views"] is not None]
    engaged=[x["engagedViews"] for x in rows if x["engagedViews"] is not None]
    pcts=[x["averageViewPercentage"] for x in rows
          if x["averageViewPercentage"] is not None]
    share_rates=[round(1000*x["shares"]/x["engagedViews"],4)
                 for x in rows if x["shares"] is not None
                 and x["engagedViews"] is not None and x["engagedViews"]>0]
    sub_rates=[round(1000*x["subscribersGained"]/x["engagedViews"],4)
               for x in rows if x["subscribersGained"] is not None
               and x["engagedViews"] is not None and x["engagedViews"]>0]
    return {
        "n":len(rows),
        "median_views":median_or_none(views),
        "median_engaged_views":median_or_none(engaged),
        "median_avg_view_pct":median_or_none(pcts),
        "median_shares_per_1000_engaged":median_or_none(share_rates),
        "median_subs_gained_per_1000_engaged":median_or_none(sub_rates),
        "feed_impressions":None,"chose_to_view_pct":None,
        "early_retention":None,
        "missing_feed_metrics_reason":"NOT_AVAILABLE_NO_STUDIO_EXPORT"
    }

def experiment_report(d:dict,p:dict)->dict:
    validate_policy(p)
    records=validate_dataset(d)
    # Editorial-only groups; don't compare categories with dissimilar subjects.
    groups=defaultdict(list)
    for item in records:
        groups[(item["category"],item["hook_variant"])].append(item)
    stats={category: {
        variant:group_stats(groups.get((category,variant),[]))
        for variant in ("A","B")
    } for category in sorted(set(x["category"] for x in records))}
    candidates=[]
    for category,arms in stats.items():
        n_a,n_b=arms["A"]["n"],arms["B"]["n"]
        eligible=n_a>=p["minimum_examples_per_arm"] and n_b>=p["minimum_examples_per_arm"]
        candidates.append({
            "category":category,
            "arm_A_n":n_a,"arm_B_n":n_b,
            "minimum_per_arm":p["minimum_examples_per_arm"],
            "enough_for_preliminary_review":eligible,
            "causal_winner_declared":False,
            "real_optimization_decision_authorized":False,
            "reason":"MINIMUM_SAMPLE_NOT_MET" if not eligible
              else "HUMAN_REVIEW_REQUIRED_EVEN_AFTER_SAMPLE_THRESHOLD"
        })
    digest=hashlib.sha256(json.dumps(d,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return {
        "schema_version":1,"channel_id":CHANNEL,
        "stage":"A10_SYNTHETIC_ANALYTICS_EXPERIMENT_DRY_RUN",
        "source":"SYNTHETIC_TEST_FIXTURE_NO_REAL_CLIVOX_ANALYTICS",
        "synthetic":True,
        "hypothetical_date":d["hypothetical_observation_date"],
        "window_days":d["window_days"],
        "record_count":len(records),
        "groups":stats,
        "experiment_reviews":candidates,
        "studio_metrics_available":False,
        "actual_authenticated_analytics_calls":0,
        "real_clivox_videos_analyzed":0,
        "personal_or_private_video_ids_exported":False,
        "fake_virality_or_causal_claims_made":False,
        "editorial_upload_scheduling_automatic_changes":False,
        "dataset_sha256":digest,
        "notes":"Test values are invented simulation for code tests ONLY. Median differences, sample thresholds and correlations are not evidence of causation or real reach. YouTube Studio feed metrics remain null."
    }

def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=FIXTURE)
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    report=experiment_report(read_json(args.input),read_json(POLICY))
    contents=json.dumps(report,indent=2)+"\n"
    if args.out:
        require(not args.out.is_symlink(),"OUTPUT_LINK")
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(contents,encoding="utf-8")
    else:
        print(contents,end="")
    print("CLIVOX_A10_SYNTHETIC_ANALYTICS_NO_REAL_ACCOUNT_NO_PUBLISH")

if __name__=="__main__":
    main()
