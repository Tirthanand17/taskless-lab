"""Fail-closed read-only review manifest for a physically verified Python long.

Never treats a codec/motion pass as permission to upload or an audience win.
The canonical exact SHA and GitHub artifact run are based on REAL main video.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"content"/"recovery_pilot"/"real_python_long_release_review_candidate.json"
EXPECTED_SHA="1a20dedf886f3228445ed718e1f2e93a7e38cd74abf8aeb211540e32b6683f42"
RUN=43880108409
ARTIFACT=14232431513
EXPECTED_CHAPTERS=("Why the CSV total is wrong",
                   "Hidden spaces and repeated invoice IDs",
                   "Parse money with Decimal",
                   "Normalize, deduplicate and verify",
                   "Save and check the cleaned file")

class LongReviewRefused(ValueError):
    pass

def need(valid,reason):
    if not valid:
        raise LongReviewRefused(reason)

def validate(data:dict)->dict:
    allowed={"schema","status","audience","series","pilot_phase",
             "title","description","keywords","cover","chapters",
             "episode_id","app","file","seconds","sha256","run_id",
             "artifact_id","artifact_url","source_data","QA","approval",
             "youtube_uploads","youtube_schedules","audience_growth_proven"}
    need(type(data) is dict and set(data)==allowed,
         "UNEXPECTED_LONG_REVIEW_SCHEMA")
    need(data["schema"]=="FLOWMINUTE_B1_REAL_PYTHON_LONG_REVIEW_V1"
         and data["status"]=="EXACT_LONG_MEDIA_REVIEW_ONLY_NO_YOUTUBE"
         and data["audience"]=="English beginner data-cleaning workflows"
         and data["series"]=="Real Data Fixes"
         and data["pilot_phase"]=="first_coherent_calc_short_plus_python_long",
         "MIXED_AUDIENCE_OR_RELEASE_STATUS")
    need(data["episode_id"]=="fm_real_python_csv_three_bugs_long_en"
         and data["app"]=="python_terminal"
         and data["file"]=="REAL_PYTHON_LONG_NARRATED_REVIEW_ONLY.mp4"
         and data["sha256"]==EXPECTED_SHA
         and re.fullmatch(r"[a-f0-9]{64}",data["sha256"]) is not None
         and type(data["seconds"]) in (int,float)
         and abs(data["seconds"]-214.833)<.001
         and type(data["run_id"]) is int and data["run_id"]==RUN
         and type(data["artifact_id"]) is int and data["artifact_id"]==ARTIFACT
         and data["artifact_url"]==(
            f"https://github.com/Tirthanand17/taskless-lab/actions/runs/"
            f"{RUN}/artifacts/{ARTIFACT}"),
         "EXACT_FINAL_VIDEO_IDENTITY_NOT_VERIFIED")
    src=data["source_data"]
    need(type(src) is dict and src=={
        "fictional":True,"raw_rows":8,"clean_rows":6,
        "naive_usd":"2656.25","clean_usd":"1430.75",
        "duplicate_count":2},
        "REAL_PYTHON_SAMPLE_FACTS_CHANGED")
    qa=data["QA"]
    need(type(qa) is dict and set(qa)=={
        "h264_aac_verified","measured_duration_seconds","lufs",
        "true_peak_dbtp","static_source_pair_share",
        "longest_frozen_seconds","first_three_seconds_source_moving",
        "owner_full_watch_listen"}
         and qa["h264_aac_verified"] is True
         and qa["first_three_seconds_source_moving"] is True
         and qa["owner_full_watch_listen"] is False
         and all(type(qa[x]) in (float,int) and math.isfinite(qa[x])
                 for x in ("measured_duration_seconds","lufs",
                           "true_peak_dbtp","static_source_pair_share",
                           "longest_frozen_seconds"))
         and abs(qa["measured_duration_seconds"]-214.833)<.001
         and abs(qa["lufs"]-(-18.08))<.001
         and abs(qa["true_peak_dbtp"]-(-1.4))<.001
         and abs(qa["static_source_pair_share"]-.338)<.001
         and abs(qa["longest_frozen_seconds"]-6)<.001,
         "LONG_MEDIA_PHYSICAL_PROOF_NOT_PINNED")
    need(type(data["title"]) is str
         and data["title"]=="Why Your CSV Total Is Wrong: 3 Data-Cleaning Bugs in Python"
         and type(data["description"]) is str
         and 250<=len(data["description"])<=950
         and "fictional" in data["description"].lower()
         and all(term in data["description"] for term in (
             "8-row","$2,656.25","$1,430.75","Decimal",
             "https://docs.python.org/3/library/csv.html",
             "https://docs.python.org/3/library/decimal.html"))
         and type(data["keywords"]) is list
         and data["keywords"]==["Python","CSV","data cleaning",
                                "duplicate invoices","Decimal"]
         and type(data["cover"]) is str
         and len(data["cover"])>=90
         and "actual recorded Python terminal" in data["cover"]
         and "fictional" in data["cover"],
         "EXAGGERATED_LONG_TITLE_COVER_OR_UNVERIFIED_FINANCIAL_FACTS")
    chapters=data["chapters"]
    need(type(chapters) is list and len(chapters)==5
         and all(type(c) is dict and set(c)=={"start_seconds","label"}
                 and type(c["start_seconds"]) is int for c in chapters)
         and tuple(c["label"] for c in chapters)==EXPECTED_CHAPTERS
         and [c["start_seconds"] for c in chapters]==[0,32,72,115,170]
         and chapters[-1]["start_seconds"]<data["seconds"],
         "MISLEADING_OR_NONMONOTONIC_LONG_CHAPTERS")
    approval=data["approval"]
    need(type(approval) is dict and approval=={
        "owner_watched_exact_video":False,"facts_reviewed":False,
        "rights_reviewed":False,"publishing_authorized":False}
         and type(data["youtube_uploads"]) is int
         and data["youtube_uploads"]==0
         and type(data["youtube_schedules"]) is int
         and data["youtube_schedules"]==0
         and data["audience_growth_proven"] is False,
         "FORGED_RELEASE_OR_GROWTH_EVIDENCE")
    return {
        "status":"EXACT_LONG_MEDIA_READY_FOR_HUMAN_REVIEW_NOT_RELEASE",
        "sha256":EXPECTED_SHA,"run_id":RUN,
        "owner_authorized":False,"audience_growth_proven":False,
        "youtube_uploads":0,"youtube_schedules":0,
    }

def main():
    need(MANIFEST.is_file() and not MANIFEST.is_symlink()
         and 0<MANIFEST.stat().st_size<=12000,
         "REVIEW_MANIFEST_MISSING_OR_UNSAFE")
    print(json.dumps(validate(json.loads(MANIFEST.read_text("utf8"))),
                     sort_keys=True,indent=2))

if __name__=="__main__":
    main()
