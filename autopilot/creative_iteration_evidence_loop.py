"""Evidence-based, bounded creative-feedback cycle; never reward hacked view counts.

Research foundation: official YouTube Analytics defines engagedViews,
averageViewPercentage and averageViewDuration (duration excludes loops);
since Mar 2025 Shorts 'views' counts starts/replays with no minimum watch
time, so raw views alone MUST NOT be the optimization objective.

This is NOT a reinforcement-learning agent with automatic publication. It
is a conservative observability + candidate-evaluation gate whose input
requires real owner-authenticated Analytics or an attributed Studio export.
No fake metrics, no self-generating engagement, no guaranteed virality.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import median
import math
import re

STATUS_HOLD="NEEDS_AUTHENTIC_COMPARABLE_72H_AUDIENCE_DATA"
STATUS_REVIEW="OBSERVATIONAL_VARIATION_REVIEW_NOT_CAUSAL_OR_APPROVED"
VERSION="NO_REPEAT_CIRCLE_V1"
BASELINE="LEGACY_REPEATED_CIRCLE"
MIN_VIDEOS_PER_ARM=6
MIN_ENGAGED_PER_VIDEO=150


class CreativeCycleRejected(ValueError):
    pass


@dataclass(frozen=True)
class MeasuredShort:
    video_id:str
    topic_family:str
    visual_variant:str
    age_hours:float
    engaged_views:int | None
    views:int | None
    average_view_percentage:float | None
    average_view_duration:float | None
    source:str

    def validate(self):
        if (type(self.video_id) is not str or
            not re.fullmatch(r"[A-Za-z0-9_-]{11}",self.video_id)
            or type(self.topic_family) is not str
            or not re.fullmatch(r"[a-z_]{3,40}",self.topic_family)
            or self.visual_variant not in (BASELINE,VERSION)
            or self.source not in ("official_youtube_analytics","owner_studio_export")
            or type(self.age_hours) not in (float,int)
            or not math.isfinite(self.age_hours)
            or self.age_hours<0):
            raise CreativeCycleRejected("Invalid/unauthenticated Short audience observation")
        for field in ("views","engaged_views"):
            value=getattr(self,field)
            if value is not None and (type(value) is not int or value<0):
                raise CreativeCycleRejected("Invalid "+field)
        if (self.views is not None and self.engaged_views is not None
            and self.engaged_views>self.views):
            raise CreativeCycleRejected("Engaged views cannot exceed total views")
        for field in ("average_view_percentage","average_view_duration"):
            value=getattr(self,field)
            if value is not None and (type(value) not in (float,int)
                or not math.isfinite(value) or value<0 or value> (600 if field=="average_view_percentage" else 600)):
                raise CreativeCycleRejected("Invalid "+field)


def compare_creative_versions(records:list[MeasuredShort],*,topic_family:str,
                              observed_at_hours:int=72)->dict:
    if (type(records) is not list or len(records)>3000
        or not re.fullmatch("[a-z_]{3,40}",topic_family or "")
        or type(observed_at_hours) is not int or not 48<=observed_at_hours<=168):
        raise CreativeCycleRejected("Unbounded/invalid creative evaluation cohort")
    ids=set()
    for item in records:
        if type(item) is not MeasuredShort:
            raise CreativeCycleRejected("Only authenticated structured per-video measurements")
        item.validate()
        if item.video_id in ids:
            raise CreativeCycleRejected("Duplicate video would bias apparent improvement")
        ids.add(item.video_id)
    cohort=[r for r in records
            if r.topic_family==topic_family
            and abs(r.age_hours-observed_at_hours)<=12
            and r.engaged_views is not None
            and r.engaged_views>=MIN_ENGAGED_PER_VIDEO
            and r.views is not None and r.views>0
            and r.average_view_percentage is not None
            and r.average_view_duration is not None]
    old=[x for x in cohort if x.visual_variant==BASELINE]
    new=[x for x in cohort if x.visual_variant==VERSION]
    common={
        "source":"Real owner Analytics or attributed Studio export ONLY",
        "age_hours":observed_at_hours,
        "age_tolerance_hours":12,
        "min_videos_per_variant":MIN_VIDEOS_PER_ARM,
        "min_engaged_views_per_video":MIN_ENGAGED_PER_VIDEO,
        "variant_counts":{BASELINE:len(old),VERSION:len(new)},
        "topic_family":topic_family,
        "no_automatic_creative_approval_or_publish":True,
        "new_replacement_uploads_authorized":False,
        "metrics_not_derived_from_view_count_alone":True,
        "true_randomized_ab_test_conducted":False,
        "claimed_incremental_causal_engagement_lift":None,
    }
    if len(old)<MIN_VIDEOS_PER_ARM or len(new)<MIN_VIDEOS_PER_ARM:
        return {"status":STATUS_HOLD,
                "next_action":"Collect 72-hour owner-authenticated comparable audience observations; do NOT rank candidates yet.",
                "candidate_approved":False,
                **common}
    def describe(group:list[MeasuredShort])->dict:
        return {
            "median_average_view_percentage":round(
                median(x.average_view_percentage for x in group),2),
            "median_engaged_start_fraction":round(
                median(x.engaged_views/x.views for x in group),4),
            "median_average_view_duration_seconds":round(
                median(x.average_view_duration for x in group),2),
            "median_engaged_views":median(x.engaged_views for x in group),
            "n_videos":len(group),
        }
    before=describe(old);after=describe(new)
    percentage_delta=round(after["median_average_view_percentage"]-
                           before["median_average_view_percentage"],2)
    engaged_delta=round(after["median_engaged_start_fraction"]-
                        before["median_engaged_start_fraction"],4)
    # Observational only: cohort may be confounded by subject, hook and
    # posting date. Never optimize for view start/replay inflation.
    recommendation=("Candidate merits independent editorial examination"
        if percentage_delta>=5 and engaged_delta>=0
        else "No robust positive signal; retain or revise only one creative variable")
    return {
        "status":STATUS_REVIEW,
        "baseline":before,"candidate":after,
        "observed_percentage_point_difference_not_causal":percentage_delta,
        "observed_engaged_start_fraction_difference_not_causal":engaged_delta,
        "next_action":recommendation,
        "candidate_approved":False,
        **common,
    }


def iterate_once(*,records:list[MeasuredShort],topic_family:str,
                 latest_candidate:str,already_changed_this_cycle:bool=False)->dict:
    if latest_candidate not in (VERSION,BASELINE) or type(already_changed_this_cycle) is not bool:
        raise CreativeCycleRejected("Source-proven variant and explicit previous-cycle status required")
    score=compare_creative_versions(records,topic_family=topic_family)
    if already_changed_this_cycle:
        return {**score,"status":"ONE_CHANGE_PER_CYCLE_ALREADY_USED",
                "next_action":"Hold new edits until fresh 72-hour observations.",
                "candidate_approved":False}
    if score["status"]==STATUS_HOLD:
        return score
    return {**score,
            "single_allowed_hypothesis":
                "A topic-specific finite evidence reveal instead of the repeating central circle may improve audience comprehension.",
            "next_review_requires_human_watch_listen_and_claim_approval":True,
            "auto_publish":False,
            "auto_delete_or_reschedule":False,
            "auto_change_second_variable":False}
