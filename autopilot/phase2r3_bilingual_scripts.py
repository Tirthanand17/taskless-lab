"""Phase 2R3: bilingual three-video SCRIPT-ONLY production package.

Takes existing typed Phase2 objects; checks narration/subtitle text consistency,
runtime plausibility, cited claim bindings, simulation labeling, distinct Short
narrator plans and exact artifact hashes. No audio exists, no rights are proven,
reviewers are self-asserted, no production video or publish permission exists.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
import re
import unicodedata
from typing import Sequence

from .agent_org import WorkflowError
from .phase2_pipeline import (
    ResearchPackage, FactReview, CreativeScript, LocalizedDraft, digest,
)

KINDS = frozenset(("short", "long"))
LANGUAGES = frozenset(("en", "hi"))
VISUALS = frozenset((
    "animation_3d", "motion_2d", "explanatory_diagram", "labeled_simulation",
))
LABEL = "SCRIPT_AND_CAPTIONS_DRAFT_NO_AUDIO"
ID = re.compile(r"narrator_[a-z0-9_]{2,30}\Z")
SPACE = re.compile(r"\s+")
DEVANAGARI = re.compile(r"[\u0900-\u097f]")
LETTER = re.compile(r"[a-zA-Z]")
BLOCKED_PROMISES = (
    "guaranteed viral", "guaranteed earnings", "100% free for everyone",
    "we booked your ticket", "we purchased for you",
)


def _normal(value: str) -> str:
    return SPACE.sub(" ", unicodedata.normalize("NFKC", value)).strip()


def _words(value: str) -> int:
    return len(_normal(value).split())


@dataclass(frozen=True)
class SpokenBeat:
    start_ms: int
    end_ms: int
    spoken_text: str
    subtitle_text: str
    overlay: str
    visual_mode: str
    claim_ids: tuple[str, ...]
    simulation_label_visible: bool = False

    def validate(self, *, next_start: int, accepted_claim_ids: set[str]) -> None:
        if (type(self.start_ms) is not int or type(self.end_ms) is not int
                or self.start_ms != next_start or not self.start_ms < self.end_ms
                or self.end_ms - self.start_ms > 30_000):
            raise WorkflowError("Spoken beat gap, overlap, invalid time or overlong segment")
        if (not isinstance(self.spoken_text, str)
                or not 8 <= len(self.spoken_text.strip()) <= 250
                or "\r" in self.spoken_text or "\n" in self.spoken_text
                or not isinstance(self.subtitle_text, str)
                or not 8 <= len(self.subtitle_text.strip()) <= 250
                or _normal(self.spoken_text) != _normal(self.subtitle_text)):
            raise WorkflowError("Caption must represent exactly the submitted narration")
        if (not isinstance(self.overlay, str) or not 4 <= len(self.overlay.strip()) <= 85
                or self.visual_mode not in VISUALS
                or any(not isinstance(x,str) for x in self.claim_ids)
                or len(self.claim_ids) != len(set(self.claim_ids))
                or not set(self.claim_ids) <= accepted_claim_ids
                or type(self.simulation_label_visible) is not bool):
            raise WorkflowError("Unreviewed on-screen claim or malformed visual plan")
        if self.visual_mode == "labeled_simulation" and not self.simulation_label_visible:
            raise WorkflowError("Illustrative demo must visibly say it is a simulation")
        if any(phrase in _normal(self.spoken_text).lower() for phrase in BLOCKED_PROMISES):
            raise WorkflowError("High-confidence marketing or action claims forbidden in draft")


@dataclass(frozen=True)
class VideoTextDraft:
    episode_id: str
    kind: str
    language: str
    research_sha256: str
    script_sha256: str
    localized_sha256: str
    narrator_id: str
    narrator_direction: str
    beats: tuple[SpokenBeat, ...]
    label: str = LABEL
    audio_exists: bool = False
    provider_rights_verified: bool = False
    externally_fact_approved: bool = False
    publishing_authorized: bool = False

    def validate(self, research: ResearchPackage, review: FactReview,
                 script: CreativeScript, localized: LocalizedDraft, *, now: datetime) -> dict:
        if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
            raise WorkflowError("Timezone aware research review clock required")
        if (self.episode_id != research.episode_id or self.episode_id != script.episode_id
                or self.episode_id != review.episode_id
                or self.episode_id != localized.episode_id
                or self.research_sha256 != digest(research)
                or self.script_sha256 != digest(script)
                or self.localized_sha256 != digest(localized)):
            raise WorkflowError("Script plan differs from source-backed draft content")
        if (self.kind not in KINDS or self.language not in LANGUAGES
                or self.label != LABEL or type(self.audio_exists) is not bool
                or self.audio_exists or type(self.provider_rights_verified) is not bool
                or self.provider_rights_verified
                or type(self.externally_fact_approved) is not bool
                or self.externally_fact_approved
                or type(self.publishing_authorized) is not bool
                or self.publishing_authorized):
            raise WorkflowError("Video plan cannot claim audio, rights, external fact or publish approval")
        if (not isinstance(self.narrator_id,str) or ID.fullmatch(self.narrator_id) is None
                or not isinstance(self.narrator_direction,str)
                or not 25 <= len(self.narrator_direction.strip()) <= 350):
            raise WorkflowError("Missing distinct safe narrator planning metadata")
        research.validate(now=now)
        review.validate(research)
        script.validate(research,review)
        localized.validate(script,stage="english" if self.language == "en" else "hindi")
        if not isinstance(self.beats,(tuple,list)):
            raise WorkflowError("Narration must be bounded beats")
        minimum = 4 if self.kind == "short" else 20
        maximum = 16 if self.kind == "short" else 80
        if not minimum <= len(self.beats) <= maximum:
            raise WorkflowError("Required narrative beat count missing")
        previous = 0
        total_words = 0
        has_demo=False
        for item in self.beats:
            if not isinstance(item, SpokenBeat):
                raise WorkflowError("Narration must use typed beats")
            item.validate(next_start=previous,accepted_claim_ids=set(script.used_claim_ids))
            previous=item.end_ms
            total_words += _words(item.spoken_text)
            if item.visual_mode=="labeled_simulation":
                has_demo=True
        if (self.kind=="short" and not 25_000 <= previous <= 65_000
                or self.kind=="long" and not 360_000 <= previous <= 540_000
                or not has_demo):
            raise WorkflowError("Runtime, illustrative demo or episode format invalid")
        spoken=_normal(" ".join(x.spoken_text for x in self.beats))
        if spoken != _normal(localized.narrated_text):
            raise WorkflowError("Narration beat text not identical to localized script")
        speed=total_words * 60000 / previous
        if not 65 <= speed <= 235:
            raise WorkflowError("Narration speed infeasible for natural delivery; human check still required")
        if self.language == "hi" and len(DEVANAGARI.findall(spoken)) < 10:
            raise WorkflowError("Hindi/Devanagari-language plan missing actual Hindi narration")
        if self.language == "en" and len(LETTER.findall(spoken)) < 20:
            raise WorkflowError("English-language plan missing English narration")
        return {
            "episode_id":self.episode_id,"kind":self.kind,"language":self.language,
            "duration_ms":previous,"narrator_id":self.narrator_id,
            "word_count":total_words,"estimated_wpm":round(speed,2),
            "beat_count":len(self.beats),"has_labeled_simulation":has_demo,
            "text_sha256":sha256(spoken.encode("utf-8")).hexdigest(),
        }


def review_three_video_text_drafts(
    entries: Sequence[tuple[VideoTextDraft,ResearchPackage,FactReview,CreativeScript,LocalizedDraft]],
    *,now:datetime,
) -> dict:
    """Review exactly two Shorts (Hindi+English) and one Hindi long-form SCRIPT.

    Passing means only that submitted scripts, timing and subtitle text agree.
    All external claims, creator identities and asset rights remain unverified.
    """
    if not isinstance(entries,(tuple,list)) or len(entries)!=3:
        raise WorkflowError("Exactly two Shorts and one long text draft required")
    summaries=[]
    for entry in entries:
        if not isinstance(entry,(tuple,list)) or len(entry)!=5:
            raise WorkflowError("Each video must bind to existing Phase2 artifact set")
        plan,research,review,script,localized=entry
        if not isinstance(plan,VideoTextDraft):
            raise WorkflowError("Typed script draft plan required")
        summaries.append(plan.validate(research,review,script,localized,now=now))
    combinations={(x["kind"],x["language"]) for x in summaries}
    if combinations!={("short","hi"),("short","en"),("long","hi")}:
        raise WorkflowError("Require one Hindi Short, English Short and Hindi/Hinglish long")
    if len({s["episode_id"] for s in summaries})!=3:
        raise WorkflowError("Each release must have a different immutable episode ID")
    shorts=[s for s in summaries if s["kind"]=="short"]
    if shorts[0]["narrator_id"]==shorts[1]["narrator_id"]:
        raise WorkflowError("Two Shorts require two distinct planned narrator identities")
    sorted_summaries=sorted(summaries,key=lambda x:(x["kind"],x["language"]))
    fingerprint=sha256(json.dumps(sorted_summaries,sort_keys=True,
            separators=(",",":"),ensure_ascii=True).encode("utf-8")).hexdigest()
    return {
        "status":"THREE_BILINGUAL_TEXT_DRAFTS_STRUCTURALLY_READY_ONLY",
        "episodes":sorted_summaries,
        "draft_fingerprint_sha256":fingerprint,
        "voice_or_audio_created":False,
        "voice_rights_verified":False,
        "actual_video_created":False,
        "external_claim_truth_verified":False,
        "independent_language_quality_verified":False,
        "narrator_difference_audibly_confirmed":False,
        "subtitle_speech_alignment_verified":False,
        "ready_for_rendering":False,
        "publishing_authorized":False,
        "network_calls":0,
        "spend_inr":0,
    }
