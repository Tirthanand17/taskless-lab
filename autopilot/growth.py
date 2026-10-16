"""Age-matched YouTube engagement scoring.

Never infer audience retention from raw views. Keep long videos and Shorts
separate, and demand a meaningful cohort before recommending a change.
"""
from __future__ import annotations
from dataclasses import dataclass
from statistics import median
from typing import Sequence

@dataclass(frozen=True)
class VideoMetric:
    video_id: str
    format: str
    age_hours: float
    views: int
    engaged_views: int
    average_view_duration_seconds: float
    length_seconds: float
    subscribers_gained: int
    comments: int
    impressions_ctr: float | None = None

    def validate(self):
        if not self.video_id or self.format not in ("short", "long"):
            raise ValueError("Invalid video identity or format")
        if not 0 <= self.engaged_views <= self.views or self.views < 0:
            raise ValueError("Engaged views may not exceed views")
        if self.length_seconds <= 0 or self.age_hours < 0:
            raise ValueError("Invalid duration or video age")
        if self.average_view_duration_seconds < 0 or self.comments < 0:
            raise ValueError("Invalid watch time or interactions")
        if self.impressions_ctr is not None and not 0 <= self.impressions_ctr <= 1:
            raise ValueError("CTR must be a fraction from zero to one")

    @property
    def completion_proxy(self) -> float:
        return self.average_view_duration_seconds / self.length_seconds

    @property
    def subscriber_yield(self) -> float:
        return 1000 * self.subscribers_gained / max(1, self.engaged_views)

def analyze(items: Sequence[VideoMetric], *, cutoff_hours: float = 72,
            minimum_videos: int = 6, minimum_engaged_views: int = 150) -> dict:
    """Suggest at most one experiment. Never promise improved views."""
    for item in items: item.validate()
    cohorts = {}
    for kind in ("short", "long"):
        cohort = [x for x in items
                  if x.format == kind and max(0,cutoff_hours - 12) <= x.age_hours <= cutoff_hours + 12]
        qualified = [x for x in cohort if x.engaged_views >= minimum_engaged_views]
        data = {"kind":kind, "videos_observed":len(cohort),
                "qualified":len(qualified),"age_window_hours":cutoff_hours}
        if len(qualified) < minimum_videos:
            data.update(status="insufficient_sample",experiment=None,
                        reason="Do not optimize on raw views or too few age-matched videos.")
        else:
            watch = median(x.completion_proxy for x in qualified)
            growth = median(x.subscriber_yield for x in qualified)
            # Diagnostic only; optimizing uses user-approved, one-variable experiments.
            experiment = ("Test one alternate first-three-second hook"
                          if watch < .55 else
                          "Test one content-benefit promise in title and first frame")
            data.update(status="experiment_eligible",
                        median_completion_proxy=round(watch,3),
                        median_subscribers_per_1000_engaged=round(growth,2),
                        experiment=experiment,
                        reason="Hypothesis only; validate with controlled releases.")
        cohorts[kind]=data
    return {"status":"observational_not_causal","cohorts":cohorts,
            "avoid":"No purchased views, fake comments, clickbait or claims of guaranteed virality."}
