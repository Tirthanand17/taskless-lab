"""Read-only owner-curated YouTube Studio longitudinal experiment ledger.

Unlike the legacy single-observation 72h CSV parser, this validates the SAME
video at 24h,72h,168h without double-counting samples as different videos.
Follows age-matched cohorts; reports descriptive changes, never causal proof.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import re
from statistics import median

from autopilot.branch1_recovery import (
    COLUMNS,MIN_VIDEOS,MIN_SHORT_FEED_EXPOSURES,
    MIN_LONG_IMPRESSIONS,MIN_LONG_VIEWS,RecoveryRefused,
    SERIES,VIDEO,require,
)

HEADER=("video_id","cohort")+tuple(COLUMNS[1:])
ANCHORS=((24,6),(72,12),(168,24))
INTEGER_FIELDS=("views","engaged_views","shown_in_feed",
                "impressions","subscribers_gained")
FLOAT_FIELDS=("age_hours","duration_seconds","stayed_to_watch_pct",
              "impressions_ctr_pct","average_view_duration_seconds",
              "retention_3s_pct","retention_30s_pct")
OPTIONAL=("shown_in_feed","stayed_to_watch_pct","impressions",
          "impressions_ctr_pct","retention_3s_pct","retention_30s_pct")
CUMULATIVE=("views","engaged_views","shown_in_feed",
            "impressions","subscribers_gained")

def exact_number(raw,field,integer,nullable):
    if raw=="" and nullable:
        return None
    require(type(raw) is str and re.fullmatch(
        r"[0-9]{1,10}" if integer else r"[0-9]{1,8}(?:\.[0-9]{1,5})?",
        raw) is not None,"INVALID_STUDIO_"+field)
    value=int(raw) if integer else float(raw)
    require(value<=1_000_000_000,"METRIC_OUT_OF_RANGE_"+field)
    return value

def age_anchor(age):
    matches=[anchor for anchor,span in ANCHORS if abs(age-anchor)<=span]
    require(len(matches)==1,"AGE_NOT_IN_DISTINCT_24H_72H_168H_WINDOW")
    return matches[0]

def read_csv(path:Path)->list[dict]:
    require(path.is_file() and not path.is_symlink()
            and 0<path.stat().st_size<=250000,"UNSAFE_LONGITUDINAL_STUDIO_FILE")
    observations=[]
    seen=set()
    registry={}
    with path.open("r",encoding="utf-8-sig",newline="") as stream:
        reader=csv.DictReader(stream)
        require(tuple(reader.fieldnames or ())==HEADER,
                "UNEXPECTED_LONGITUDINAL_CSV_OR_PRIVATE_COLUMNS")
        for line in reader:
            require(None not in line and set(line)==set(HEADER)
                    and len(observations)<1500,
                    "LONGITUDINAL_ROW_SCHEMA")
            video=line["video_id"]
            cohort=line["cohort"]
            fmt=line["format"]
            series=line["series"]
            require(VIDEO.fullmatch(video or "") is not None
                    and cohort in ("baseline","pilot")
                    and fmt in ("short","long") and series in SERIES,
                    "WRONG_VIDEO_OR_EXPERIMENT_COHORT")
            obj={"cohort":cohort,"format":fmt,"series":series}
            for key in INTEGER_FIELDS:
                obj[key]=exact_number(line[key],key,True,key in OPTIONAL)
            for key in FLOAT_FIELDS:
                obj[key]=exact_number(line[key],key,False,key in OPTIONAL)
            clock=age_anchor(obj["age_hours"])
            obj["age_target_hours"]=clock
            key=(video,clock)
            require(key not in seen,"DUPLICATE_SAME_VIDEO_AGE_OBSERVATION")
            seen.add(key)
            details=(cohort,fmt,series,obj["duration_seconds"])
            if video in registry:
                require(registry[video]["details"]==details,
                        "VIDEO_REASSIGNED_COHORT_FORMAT_SERIES_OR_LENGTH")
                prior=registry[video]["rows"]
            else:
                prior=[]
                registry[video]={"details":details,"rows":prior}
            require(10<=obj["duration_seconds"]<=(
                    180 if fmt=="short" else 7200)
                    and obj["engaged_views"]<=obj["views"]
                    and obj["average_view_duration_seconds"]<=86400,
                    "IMPOSSIBLE_AGE_MATCHED_VIDEO_DATA")
            for pct in ("stayed_to_watch_pct","impressions_ctr_pct",
                        "retention_3s_pct","retention_30s_pct"):
                require(obj[pct] is None or 0<=obj[pct]<=100,
                        "INVALID_STUDIO_PERCENTAGE")
            if fmt=="short":
                require(obj["impressions"] is None
                        and obj["impressions_ctr_pct"] is None
                        and (obj["stayed_to_watch_pct"] is None or
                             obj["shown_in_feed"] is not None and
                             obj["shown_in_feed"]>0),
                        "SHORTS_METRIC_NOT_FROM_SHORTS_STUDIO")
            else:
                require(obj["shown_in_feed"] is None
                        and obj["stayed_to_watch_pct"] is None
                        and (obj["impressions_ctr_pct"] is None or
                             obj["impressions"] is not None and
                             obj["impressions"]>0),
                        "LONG_FORM_CTR_OR_IMPRESSIONS_MISSING")
            prior.append(obj)
            observations.append(obj)
    require(observations,"EMPTY_STUDIO_EXPERIMENT")
    for meta in registry.values():
        rows=sorted(meta["rows"],key=lambda o:o["age_target_hours"])
        for old,new in zip(rows,rows[1:]):
            for field in CUMULATIVE:
                if old[field] is not None and new[field] is not None:
                    require(new[field]>=old[field],
                            "CUMULATIVE_METRIC_WENT_BACKWARDS_"+field)
    return observations

def summary(rows:list[dict])->dict:
    require(type(rows) is list and bool(rows),
            "REAL_STUDIO_AGE_MATCHED_INPUT_REQUIRED")
    cohorts=[]
    comparisons=[]
    for anchor,_ in ANCHORS:
        for fmt in ("short","long"):
            for series in sorted(SERIES):
                groups={}
                for cohort in ("baseline","pilot"):
                    matches=[r for r in rows
                             if r["age_target_hours"]==anchor
                             and r["format"]==fmt
                             and r["series"]==series
                             and r["cohort"]==cohort]
                    if not matches:
                        continue
                    videos=len(matches)
                    engaged=sum(r["engaged_views"] for r in matches)
                    views=sum(r["views"] for r in matches)
                    subs=sum(r["subscribers_gained"] for r in matches)
                    data={
                        "age_target_hours":anchor,
                        "format":fmt,"series":series,"cohort":cohort,
                        "videos":videos,"views":views,
                        "engaged_views":engaged,
                        "subscriber_gains":subs,
                        "subscribers_per_1000_engaged":
                            round(1000*subs/engaged,2) if engaged else None,
                        "median_average_view_duration_seconds":
                            round(median(x["average_view_duration_seconds"]
                                         for x in matches),2),
                    }
                    if fmt=="short":
                        full=[x for x in matches if x["shown_in_feed"] is not None
                              and x["stayed_to_watch_pct"] is not None]
                        feed=sum(x["shown_in_feed"] for x in full)
                        data["shown_in_feed"]=feed
                        data["weighted_stayed_to_watch_pct"]=(
                            round(sum(x["shown_in_feed"]*x["stayed_to_watch_pct"]
                                      for x in full)/feed,2)
                            if feed else None)
                        data["sample_eligible"]=(
                            len(full)==videos and videos>=MIN_VIDEOS
                            and feed>=MIN_SHORT_FEED_EXPOSURES
                            and engaged>=100)
                    else:
                        full=[x for x in matches if x["impressions"] is not None
                              and x["impressions_ctr_pct"] is not None]
                        impressions=sum(x["impressions"] for x in full)
                        data["impressions"]=impressions
                        data["weighted_ctr_pct"]=(
                            round(sum(x["impressions"]*x["impressions_ctr_pct"]
                                      for x in full)/impressions,2)
                            if impressions else None)
                        data["median_first_30s_retention_pct"]=(
                            round(median(x["retention_30s_pct"] for x in matches),2)
                            if all(x["retention_30s_pct"] is not None
                                   for x in matches) else None)
                        data["sample_eligible"]=(
                            len(full)==videos and videos>=MIN_VIDEOS
                            and impressions>=MIN_LONG_IMPRESSIONS
                            and views>=MIN_LONG_VIEWS)
                    groups[cohort]=data
                    cohorts.append(data)
                if "baseline" in groups and "pilot" in groups:
                    before=groups["baseline"];after=groups["pilot"]
                    sufficient=before["sample_eligible"] and after["sample_eligible"]
                    key=("weighted_stayed_to_watch_pct" if fmt=="short"
                         else "median_first_30s_retention_pct")
                    metric=None
                    if sufficient and before.get(key) is not None and after.get(key) is not None:
                        metric=round(after[key]-before[key],2)
                    comparisons.append({
                        "age_target_hours":anchor,"format":fmt,"series":series,
                        "status":("DESCRIPTIVE_ONLY_NOT_CAUSAL" if metric is not None
                                  else "INSUFFICIENT_OR_INCOMPLETE_STUDIO_DATA"),
                        "primary_metric":key,
                        "pilot_minus_baseline_percentage_points":metric,
                        "no_experimental_winner_claim":True,
                    })
    return {
        "schema":"FLOWMINUTE_B1_24_72_168_AGE_MATCHED_LEARNING_V1",
        "status":"OWNER_STUDIO_OBSERVATIONS_ONLY",
        "cohorts":cohorts,"comparisons":comparisons,
        "warning":"Age-matched descriptive signals are not randomized results. Returning viewers and satisfaction remain separate.",
        "no_video_ids_or_audience_private_data_in_output":True,
        "no_cross_format_ctr_comparisons":True,
        "audience_recovery_proven":False,
        "youtube_uploads":0,"youtube_schedules":0,
    }

def main():
    p=argparse.ArgumentParser(description="Read-only owner Studio CSV, never publish")
    p.add_argument("--curated-csv",required=True,type=Path)
    args=p.parse_args()
    print(json.dumps(summary(read_csv(args.curated_csv)),indent=2,sort_keys=True))

if __name__=="__main__":
    main()
