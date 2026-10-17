"""Strict provenance-aware FlowMinute engagement calculations.

Only calculates supported metrics. Missing API/Studio fields stay None.
Never presents derived values as actual YouTube observations.
"""
from __future__ import annotations
from dataclasses import dataclass
from statistics import median

@dataclass(frozen=True)
class Observation:
    video_id: str
    kind: str
    series: str
    age_hours: float
    views: int | None
    engaged_views: int | None
    likes: int | None
    comments: int | None
    shares: int | None
    subscribers_gained: int | None
    watch_time_minutes: float | None
    source: str
    def validate(self) -> None:
        if not self.video_id or self.kind not in ('short','long') or self.source not in ('official_api','studio_export','manual_observation') or self.age_hours<0:
            raise ValueError('Invalid video or source provenance')
        for name in ('views','engaged_views','likes','comments','shares','subscribers_gained'):
            value=getattr(self,name)
            if value is not None and (type(value) is not int or value<0):
                raise ValueError('Invalid '+name)
        if self.watch_time_minutes is not None and self.watch_time_minutes<0:
            raise ValueError('Invalid watch time')
        if self.views is not None and self.engaged_views is not None and self.engaged_views>self.views:
            raise ValueError('Engaged views cannot exceed public view count')

def rates(item: Observation) -> dict:
    item.validate()
    denominator=item.engaged_views
    def per_k(value):
        return round(value*1000/denominator,2) if value is not None and denominator is not None and denominator>0 else None
    return {'video_id':item.video_id,'kind':item.kind,'series':item.series,
            'source':item.source,'engaged_views':item.engaged_views,
            'likes_per_1000_engaged':per_k(item.likes),
            'comments_per_1000_engaged':per_k(item.comments),
            'shares_per_1000_engaged':per_k(item.shares),
            'subscribers_gained_per_1000_engaged':per_k(item.subscribers_gained),
            'watch_time_minutes':item.watch_time_minutes}

def comparable_cohort(items: list[Observation], *, kind: str,
                      age_hours: int=72, min_videos: int=6,
                      min_engaged_views: int=150) -> dict:
    if kind not in ('short','long') or age_hours<=0 or min_videos<2 or min_engaged_views<=0:
        raise ValueError('Invalid cohort parameters')
    for item in items:item.validate()
    eligible=[x for x in items if x.kind==kind and
              abs(x.age_hours-age_hours)<=12 and
              x.engaged_views is not None and x.engaged_views>=min_engaged_views and
              x.source in ('official_api','studio_export')]
    if len(eligible)<min_videos:
        return {'status':'INSUFFICIENT_AUTHENTIC_DATA', 'eligible_videos':len(eligible),
                'kind':kind,'estimated_improvement':None}
    return {'status':'BASELINE_ONLY_NOT_CAUSAL','kind':kind,
            'eligible_videos':len(eligible),'median_engaged_views':median(x.engaged_views for x in eligible),
            'estimated_improvement':None}
