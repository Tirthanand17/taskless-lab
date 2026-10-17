"""Fail-closed instructional originality, evidence and media asset gate.

A positive result permits DRAFT/RENDER ONLY, never publication or upload.
No live YouTube, network, OAuth or paid providers used.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from urllib.parse import urlparse

@dataclass(frozen=True)
class ResearchEvidence:
    url: str
    checked_on: date
    official: bool
    checked: bool

@dataclass(frozen=True)
class LicensedAsset:
    kind: str
    source: str
    license_name: str
    commercial_use_verified: bool
    attribution_ready: bool

@dataclass(frozen=True)
class Lesson:
    title: str
    kind: str
    level: str
    viewer_result: str
    steps: tuple[str, ...]
    sources: tuple[ResearchEvidence, ...]
    assets: tuple[LicensedAsset, ...]
    hook_first_seconds: float
    practical_demonstration: bool
    real_interface_capture: bool
    simulated_interface: bool
    simulation_disclosed: bool
    voice_profile: str
    captions_checked: bool
    personal_information_removed: bool
    transactions_completed: bool = False
    user_payment_approved: bool = False
    freshness_required: bool = True

@dataclass(frozen=True)
class EditorialVerdict:
    status: str
    reasons: tuple[str, ...]
    publishing_enabled: bool = False

def verify_lesson(lesson: Lesson, *, reviewed_on: date) -> EditorialVerdict:
    """Pre-render reviewer: metadata booleans are claims requiring independent QA.

    This function NEVER certifies a final MP4, music recording, or live UI screen.
    """
    issues = []
    if lesson.kind not in ('short','long') or lesson.level not in ('beginner','intermediate','advanced','project'):
        issues.append('BAD_FORMAT_OR_LESSON_LEVEL')
    if len(lesson.title.strip()) < 12 or len(lesson.viewer_result.strip()) < 30:
        issues.append('WEAK_EDUCATIONAL_VALUE')
    if len(lesson.steps)<2 or any(len(x.strip())<10 for x in lesson.steps):
        issues.append('MISSING_REPRODUCIBLE_STEPS')
    if lesson.hook_first_seconds < 0 or lesson.hook_first_seconds>2:
        issues.append('WEAK_OR_DELAYED_HOOK')
    if lesson.voice_profile not in ('energetic','explanatory'):
        issues.append('VOICE_PROFILE_UNVERIFIED')
    if not lesson.practical_demonstration:
        issues.append('NO_REAL_DEMONSTRATION')
    if lesson.simulated_interface and not lesson.simulation_disclosed:
        issues.append('UNLABELED_SIMULATED_UI')
    if not lesson.real_interface_capture and not lesson.simulated_interface:
        issues.append('UNVERIFIED_INTERFACE_DEMONSTRATION')
    if not lesson.captions_checked or not lesson.personal_information_removed:
        issues.append('CAPTION_OR_PRIVACY_QA_MISSING')
    if lesson.transactions_completed and not lesson.user_payment_approved:
        issues.append('UNAUTHORIZED_TRANSACTION_CLAIM')
    domains=set()
    official_domains=set()
    for item in lesson.sources:
        u=urlparse(item.url)
        if u.scheme!='https' or not u.hostname or u.username or u.password or not item.checked:
            issues.append('UNVERIFIED_RESEARCH_SOURCE')
            continue
        if item.checked_on > reviewed_on or (reviewed_on-item.checked_on).days > (7 if lesson.freshness_required else 365):
            issues.append('STALE_RESEARCH')
        domains.add(u.hostname.lower())
        if item.official:official_domains.add(u.hostname.lower())
    if len(domains)<2 or not official_domains or len(domains - official_domains)<1:
        issues.append('INSUFFICIENT_INDEPENDENT_EVIDENCE')
    for asset in lesson.assets:
        if asset.kind not in ('visual','music','voice','sound_effect','screen_capture') or not asset.source or not asset.license_name or not asset.commercial_use_verified or not asset.attribution_ready:
            issues.append('ASSET_RIGHTS_NOT_VERIFIED')
    if not lesson.assets:
        issues.append('NO_LICENSED_ASSET_RECORDS')
    reasons=tuple(sorted(set(issues)))
    return EditorialVerdict('BLOCKED_REVIEW' if reasons else 'PASS_FOR_RENDER_ONLY',reasons)
