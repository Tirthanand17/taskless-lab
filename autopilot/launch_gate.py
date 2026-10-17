"""Evidence-backed technology launch triage; feed headlines never publish.

Accepts independent human/research attestations, not unverified RSS as facts.
Scoring prioritizes a review queue only. It cannot trigger upload/schedule.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone,timedelta
from urllib.parse import urlparse

@dataclass(frozen=True)
class Citation:
    url: str
    official: bool
    reviewed: bool
    supports_release_claim: bool

@dataclass(frozen=True)
class Launch:
    title: str
    announced_at: datetime
    released_at: datetime | None
    citations: tuple[Citation,...]
    audience_problem: str
    access_confirmed: bool
    demonstration_possible: bool
    original_example: str
    pricing_confirmed: bool
    region_confirmed: bool
    source_label: str = 'researcher_checked'

@dataclass(frozen=True)
class LaunchVerdict:
    state: str
    review_priority: int | None
    reasons: tuple[str,...]
    upload_authorized: bool = False

def check_launch(item: Launch, *, now: datetime, prior_titles: tuple[str,...]=()) -> LaunchVerdict:
    problems=[]
    if now.tzinfo is None or item.announced_at.tzinfo is None:
        problems.append('TIMEZONE_UNVERIFIED')
    else:
        announced=item.announced_at.astimezone(timezone.utc)
        current=now.astimezone(timezone.utc)
        if announced>current or announced<current-timedelta(days=30):
            problems.append('UNVERIFIED_ANNOUNCEMENT_DATE')
        if item.released_at is None or item.released_at.tzinfo is None or item.released_at.astimezone(timezone.utc)>current:
            problems.append('RELEASE_OR_ACCESS_NOT_CONFIRMED')
    if not item.access_confirmed or not item.pricing_confirmed or not item.region_confirmed:
        problems.append('AVAILABILITY_UNCONFIRMED')
    if not item.demonstration_possible or len(item.original_example.strip())<25:
        problems.append('NO_ORIGINAL_DEMONSTRATION')
    if len(item.title.strip())<12 or len(item.audience_problem.strip())<30:
        problems.append('WEAK_VIEWER_BENEFIT')
    if item.title.casefold().strip() in {x.casefold().strip() for x in prior_titles}:
        problems.append('DUPLICATE_EXISTING_STORY')
    sites=set();official=set();independent=set()
    for source in item.citations:
        url=urlparse(source.url)
        if (url.scheme!='https' or not url.hostname or url.username or url.password or
            not source.reviewed or not source.supports_release_claim):
            problems.append('CITATION_NOT_VERIFIED')
            continue
        hostname=url.hostname.lower();sites.add(hostname)
        (official if source.official else independent).add(hostname)
    if not official or not independent or len(sites)<2:
        problems.append('MISSING_OFFICIAL_AND_INDEPENDENT_EVIDENCE')
    problems=tuple(sorted(set(problems)))
    if problems:return LaunchVerdict('BLOCKED_UNVERIFIED',None,problems)
    age=(now-item.announced_at).total_seconds()/3600
    priority=1 if age<=24 else 2 if age<=72 else 3
    return LaunchVerdict('READY_FOR_EDITORIAL_REVIEW',priority,())
