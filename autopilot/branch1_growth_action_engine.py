"""Read-only real-Studio evidence -> specific, non-causal channel-growth actions.

Do not mistake video codec success, guessed "algorithm thresholds", or a channel
subscriber counter for proof of Shorts retention, long retention or discovery.
Uses the existing validated 24/72/168h owner-curated CSV. No YouTube scopes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from autopilot.branch1_age_matched_learning import read_csv, summary
from autopilot.branch1_nine_cause_diagnosis import parse_traffic_csv
from autopilot.branch1_recovery import (
    MIN_VIDEOS, MIN_SHORT_FEED_EXPOSURES, MIN_LONG_IMPRESSIONS,
    MIN_LONG_VIEWS, require,
)

# Separate videos with different viewer intent: Chrome browser-search is NOT
# baseline data-cleaning content even if it passed authentic pixel motion QA.
FIRST_PILOT={
    "short":{"series":"excel_sheets",
             "lesson":"Real LibreOffice Calc TRIM: reveal FALSE then TRUE",
             "focus":"One English beginner data-cleaning error, not mixed browser privacy"},
    "long":{"series":"python_automation",
            "lesson":"Real Python invoice CSV: duplicate/whitespace/Decimal errors",
            "focus":"One English beginner data-cleaning problem with executed proof"},
}
OTHER_CANDIDATES_HELD=("Chrome Find-in-Log Short",)
REFERENCE_ONLY={
    "historical_short_stayed_to_watch_pct":21.2,
    "historical_long_average_view_duration_seconds":58.0,
    "historical_long_ctr_pct":4.8,
}

def item(code:str,priority:int,reason:str,action:str,evidence_status:str)->dict:
    return {"code":code,"priority":priority,"reason":reason,
            "next_action":action,"evidence_status":evidence_status,
            "automated_upload_authorized":False}

def _match(rows:list[dict], fmt:str,cohort:str):
    return [r for r in rows if
            r["format"]==fmt and r["cohort"]==cohort and
            r["series"]==FIRST_PILOT[fmt]["series"] and
            r["age_target_hours"]==72]

def _group(report:dict,fmt:str,cohort:str):
    return next((g for g in report["cohorts"] if
                 g["age_target_hours"]==72 and g["format"]==fmt and
                 g["series"]==FIRST_PILOT[fmt]["series"] and
                 g["cohort"]==cohort),None)

def action_plan(rows:list[dict]|None=None,traffic:dict|None=None)->dict:
    """Specific next steps, no growth claim even when observations improve."""
    if rows is not None:
        require(type(rows) is list and bool(rows),"REAL_STUDIO_ROWS_REQUIRED")
    if traffic is not None:
        require(type(traffic) is dict,"REAL_STUDIO_TRAFFIC_TOTALS_REQUIRED")
    # The existing source validators must run before calling action_plan.
    report=summary(rows) if rows is not None else None
    actions=[]
    for fmt in ("short","long"):
        f=FIRST_PILOT[fmt]
        trial=_group(report,fmt,"pilot") if report else None
        baseline=_group(report,fmt,"baseline") if report else None
        kind="SHORT" if fmt=="short" else "LONG"
        if trial is None:
            actions.append(item(
                kind+"_NEEDS_REAL_72H_STUDIO",1,
                "No owner-authenticated, same-age published pilot metrics.",
                ("After an approved, public release, collect actual 24/72/168h "
                 "Studio metrics in a private CSV; do not infer retention from "
                 "rendered MP4 or public view counts."),
                "NOT_OBSERVED"))
            continue
        if not trial["sample_eligible"]:
            floor=(f"at least {MIN_VIDEOS} distinct same-age Shorts, "
                   f"{MIN_SHORT_FEED_EXPOSURES} observed feed appearances "
                   "and 100 engaged views"
                   if fmt=="short" else
                   f"at least {MIN_VIDEOS} distinct same-age long videos, "
                   f"{MIN_LONG_IMPRESSIONS} impressions and "
                   f"{MIN_LONG_VIEWS} views")
            actions.append(item(
                kind+"_SAMPLE_TOO_SMALL",1,
                "Pilot samples do not meet the existing project evidence floor.",
                "Keep results descriptive only; for a reliable comparison collect "+
                floor+" without duplicating or spamming uploads.",
                "INSUFFICIENT_SAMPLE"))
            continue
        if baseline is None or not baseline["sample_eligible"]:
            actions.append(item(
                kind+"_MATCHED_BASELINE_NEEDED",1,
                "Same-format, same-series 72h historical reference missing.",
                "Export comparable historical Studio observations at 72h; "
                "do not compare a Short to long-form CTR or 28-day totals.",
                "NO_AGE_MATCHED_BASELINE"))
            continue
        if fmt=="short":
            trial_stay=trial["weighted_stayed_to_watch_pct"]
            base_stay=baseline["weighted_stayed_to_watch_pct"]
            if trial_stay is not None and base_stay is not None:
                code=("SHORT_HOOK_REWORK" if trial_stay<base_stay
                      else "SHORT_HOOK_HOLD_AND_VALIDATE")
                actions.append(item(
                    code,1,
                    "Real 72h age-matched choose-to-watch is "+
                    ("below" if trial_stay<base_stay else "not below")+
                    " the same-series baseline; this is observational only.",
                    ("Re-edit only the first 0-2s of a NEW genuine software "
                     "demo: show the actual error and corrected result; "
                     "retain the title promise. Do not delete/reupload an "
                     "existing Short solely to retry distribution."
                     if trial_stay<base_stay else
                     "Keep the honest 0-2s proof-first opening for the next "
                     "candidate; monitor 3s retention and repeat over more "
                     "same-topic uploads before declaring growth."),
                    "DESCRIPTIVE_NOT_CAUSAL"))
        else:
            trial_ret=trial["median_first_30s_retention_pct"]
            base_ret=baseline["median_first_30s_retention_pct"]
            if trial_ret is None or base_ret is None:
                actions.append(item(
                    "LONG_30S_RETENTION_MISSING",1,
                    "YouTube Studio first-30-second retention absent.",
                    "Collect video-level 30s retention; a high CTR alone does "
                    "not prove that the promised tutorial satisfied viewers.",
                    "STUDIO_RETENTION_NOT_AVAILABLE"))
            else:
                needs=trial_ret<base_ret
                actions.append(item(
                    "LONG_OPENING_REWORK" if needs else "LONG_OPENING_MONITOR",1,
                    "Real 72h 30-second audience retention is "+
                    ("below" if needs else "not below")+
                    " the matched long-form reference.",
                    ("In the next original Python long video, put the real "
                     "wrong-total and corrected-total proof before explaining "
                     "setup. Tighten the first 30 seconds without inflating "
                     "views or mimicking other creators."
                     if needs else
                     "Keep the truthful payoff early; review the actual "
                     "retention curve and average duration, not just clicks."),
                    "DESCRIPTIVE_NOT_CAUSAL"))
            a,b=trial["weighted_ctr_pct"],baseline["weighted_ctr_pct"]
            if a is not None and b is not None and a<b:
                actions.append(item(
                    "LONG_TITLE_COVER_REVIEW",2,
                    "Real 72h long impressions CTR is below age-matched "
                    "same-series CTR; may reflect traffic/audience differences.",
                    "After eligible public release, consider YouTube Studio "
                    "native title/thumbnail A/B testing with up to three "
                    "truthful alternatives. Use actual executed Python output "
                    "for the cover; never apply native A/B to Shorts.",
                    "DESCRIPTIVE_NOT_CAUSAL"))
        if trial["subscriber_gains"]==0 and trial["engaged_views"]>=100:
            actions.append(item(
                kind+"_NO_SUBSCRIBER_GAINS",3,
                "Genuine engaged views were observed but no subscriber gains.",
                "Use one practical series-return promise at the end of the "
                "NEXT related video, then check authentic per-1000-engaged "
                "subscriber changes. Never fabricate likes or subscribers.",
                "DESCRIPTIVE_NOT_CAUSAL"))
    if traffic:
        # Existing traffic CSV parser enforces totals=sum(sources) and type.
        baseline=traffic.get(("baseline","long"))
        trial=traffic.get(("recovery","long"))
        if baseline and trial and min(baseline["views"],trial["views"])>=200:
            base=(baseline["suggested_views"]+baseline["browse_views"])/baseline["views"]
            now=(trial["suggested_views"]+trial["browse_views"])/trial["views"]
            if now<base:
                actions.append(item(
                    "LONG_SUGGESTED_BROWSE_SHARE_DOWN",2,
                    "Actual age-compatible long-format Suggested+Browse "
                    "traffic share is directionally lower than baseline.",
                    "Check topic promise, audience match, actual impressions, "
                    "CTR and post-click watch time before changing packaging. "
                    "Do not claim a shadowban from low views.",
                    "DESCRIPTIVE_NOT_CAUSAL"))
        else:
            actions.append(item(
                "LONG_TRAFFIC_COMPARISON_INCOMPLETE",3,
                "Missing comparable authenticated format-specific source totals.",
                "Export valid baseline and recovery traffic-source shares "
                "using exact template; do not infer from public view counters.",
                "INSUFFICIENT_OR_MISSING_TRAFFIC"))
    else:
        actions.append(item(
            "RECOMMENDATION_SOURCE_EVIDENCE_MISSING",2,
            "Private Suggested/Browse and Shorts feed counts unavailable.",
            "Use Studio Content/Reach analytics; separate feed distribution "
            "from viewer response and avoid unsupported shadowban claims.",
            "STUDIO_TRAFFIC_NOT_AVAILABLE"))
    actions.sort(key=lambda x:(x["priority"],x["code"]))
    return {
        "schema":"FLOWMINUTE_B1_READONLY_GROWTH_ACTIONS_V1",
        "status":"ACTIONABLE_NEXT_STEPS_NOT_PROVEN_GROWTH",
        "channel_id":"UCCcL9Q_jqVq6LJmnYUSAFZA",
        "viewer_intent":"English beginner spreadsheet/CSV data cleaning",
        "first_pilot":FIRST_PILOT,
        "hold_out_of_first_cohort":OTHER_CANDIDATES_HELD,
        "historical_reference_only":REFERENCE_ONLY,
        "real_age_matched_rows_supplied":rows is not None,
        "actions":actions,
        "does_not_share_video_ids_or_private_analytics":True,
        "youtube_uploads":0,"youtube_schedules":0,
        "media_qa_is_not_audience_retention":True,
        "audience_growth_proven":False,
    }

def main():
    parser=argparse.ArgumentParser(
        description="Owner-only Studio CSV -> read-only growth triage; never YouTube writes")
    parser.add_argument("--curated-csv",type=Path)
    parser.add_argument("--traffic-csv",type=Path)
    args=parser.parse_args()
    if args.traffic_csv and not args.curated_csv:
        parser.error("--traffic-csv also requires --curated-csv")
    rows=read_csv(args.curated_csv) if args.curated_csv else None
    traffic=parse_traffic_csv(args.traffic_csv) if args.traffic_csv else None
    print(json.dumps(action_plan(rows,traffic),indent=2,sort_keys=True))

if __name__=="__main__":
    main()
