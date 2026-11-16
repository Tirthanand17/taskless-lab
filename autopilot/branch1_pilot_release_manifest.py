"""Validate two real, hash-locked owner-review candidates, never a publish job.

All facts, media hashes and destinations are pinned to actual successful
GitHub Actions evidence. Metadata is a working draft, not owner consent.
"""
from __future__ import annotations
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/"content"/"recovery_pilot"/"real_app_release_review_candidates.json"
EXPECTED={
    "calc":("fm_pilot_calc_trim_short_en",
            "09db1b1c86542b5b1bd0ced964c316afad22eca197b5efac286febf698636cc8",
            26.542,14222929339),
    "chrome":("fm_pilot_chrome_log_find_short_en",
              "372d93eddd1b552063f6364d334fd889ad1d78cf8f64d2c47c3f10d63246e2ed",
              20.507,14223012938),
}
FIELDS={"schema","report_date","status","series_name","language","channel",
        "source_main_narrated_run","source_independent_motion_run",
        "owner_full_watch_and_listen_complete","release_signed",
        "youtube_uploads","youtube_schedules","auto_publish_enabled",
        "baseline_reference_not_a_target","measurement_windows_hours",
        "measurement_fields","candidates"}
CANDIDATE_FIELDS={"app","episode_id","filename","actual_seconds","sha256",
                  "review_artifact","platform_title","factual_description",
                  "hashtags","pinned_comment_draft","mobile_cover_brief","approval"}
APPROVAL_FIELDS={"owner_watched_exact_mp4","facts_reviewed",
                 "rights_reviewed","release_signed"}
EXPECTED_METRICS={"shown_in_feed","stayed_to_watch_pct","engaged_views",
                  "average_view_duration_seconds","subscribers_gained",
                  "traffic_sources","retention_3s_pct"}

class ReleaseManifestRefused(ValueError):
    pass

def need(test, reason):
    if not test:
        raise ReleaseManifestRefused(reason)

def validate(data:dict)->dict:
    need(type(data) is dict and set(data)==FIELDS,"MANIFEST_SCHEMA_OR_EXTRA_DATA")
    need(data["schema"]=="FLOWMINUTE_B1_REAL_APPS_PILOT_CANDIDATES_V1"
         and data["report_date"]=="2026-11-16"
         and data["status"]=="CREATIVE_REVIEW_REQUIRED_NO_YOUTUBE"
         and data["series_name"]=="Real Data Fixes"
         and data["language"]=="en"
         and data["channel"]=="FlowMinute Lab"
         and type(data["source_main_narrated_run"]) is int
         and data["source_main_narrated_run"]==43861126654
         and type(data["source_independent_motion_run"]) is int
         and data["source_independent_motion_run"]==43861505657,
         "REVIEW_ARTIFACT_PROVENANCE_UNVERIFIED")
    need(data["owner_full_watch_and_listen_complete"] is False
         and data["release_signed"] is False
         and data["auto_publish_enabled"] is False
         and type(data["youtube_uploads"]) is int
         and data["youtube_uploads"]==0
         and type(data["youtube_schedules"]) is int
         and data["youtube_schedules"]==0,
         "OWNER_APPROVAL_CANNOT_BE_FORGED")
    need(data["measurement_windows_hours"]==[24,72,168]
         and type(data["measurement_fields"]) is list
         and set(data["measurement_fields"])==EXPECTED_METRICS
         and len(data["measurement_fields"])==len(EXPECTED_METRICS)
         and data["baseline_reference_not_a_target"]=={
             "short_stayed_to_watch_pct":21.2,
             "long_average_view_duration_seconds":58,
             "long_impressions_ctr_pct":4.8},
         "INVALID_PREEXISTING_BASELINE_OR_MEASUREMENT_PROTOCOL")
    rows=data["candidates"]
    need(type(rows) is list and len(rows)==2 and
         [x.get("app") for x in rows if type(x) is dict]==["calc","chrome"],
         "TWO_DISTINCT_REAL_VIDEO_CANDIDATES_REQUIRED")
    for row in rows:
        app=row["app"]
        need(set(row)==CANDIDATE_FIELDS,"VIDEO_METADATA_SCHEMA_CHANGED")
        episode,sha,seconds,artifact_id=EXPECTED[app]
        require_url=(f"https://github.com/Tirthanand17/taskless-lab/"
                     f"actions/runs/43861126654/artifacts/{artifact_id}")
        need(row["episode_id"]==episode and row["sha256"]==sha
             and type(row["actual_seconds"]) in (float,int)
             and abs(row["actual_seconds"]-seconds)<.0001
             and row["filename"]=="NARRATED_REAL_APP_REVIEW_ONLY.mp4"
             and row["review_artifact"]==require_url
             and re.fullmatch(r"[0-9a-f]{64}",row["sha256"]) is not None,
             "WRONG_MEDIA_HASH_OR_GITHUB_REVIEW_ARTIFACT")
        title=row["platform_title"]
        desc=row["factual_description"]
        need(type(title) is str and 25<=len(title)<=88
             and type(desc) is str and 110<=len(desc)<=700
             and ("fictional" in desc.lower())
             and "official help:" in desc.lower()
             and ("TRIM" in desc if app=="calc" else "Ctrl+G" in desc)
             and ("LibreOffice Calc" in desc if app=="calc" else "Chrome" in desc)
             and ("Excel" not in title if app=="calc" else "Chrome" in title),
             "MISLEADING_TITLE_OR_UNSUPPORTED_DEMO_DESCRIPTION")
        tags=row["hashtags"]
        need(type(tags) is list and 1<=len(tags)<=3
             and len(set(tags))==len(tags)
             and all(type(t) is str and re.fullmatch(r"#[A-Za-z0-9]{3,30}",t)
                     for t in tags)
             and "#Shorts" in tags,
             "SPAMMY_OR_UNGROUNDED_TAGS")
        need(type(row["pinned_comment_draft"]) is str
             and 30<=len(row["pinned_comment_draft"])<=300
             and type(row["mobile_cover_brief"]) is str
             and len(row["mobile_cover_brief"])>=50
             and ("real" in row["mobile_cover_brief"].lower()
                  or "genuine" in row["mobile_cover_brief"].lower()),
             "MISSING_FIRST_PARTY_MOBILE_PRESENTATION")
        flags=row["approval"]
        need(type(flags) is dict and set(flags)==APPROVAL_FIELDS
             and all(v is False for v in flags.values()),
             "CANDIDATE_RELEASE_APPROVAL_NOT_GRANTED")
    return {"status":"HASH_LOCKED_OWNER_REVIEW_ONLY",
            "candidates":len(rows),"all_strict_technical_artifact_refs_present":True,
            "owner_approved":False,"youtube_uploads":0,"youtube_schedules":0,
            "audience_recovery_proven":False}

def main():
    need(DEFAULT.is_file() and not DEFAULT.is_symlink()
         and DEFAULT.stat().st_size<12000,
         "REVIEW_MANIFEST_ABSENT_OR_UNSAFE")
    data=json.loads(DEFAULT.read_text("utf8"))
    print(json.dumps(validate(data),sort_keys=True))

if __name__=="__main__":
    main()
