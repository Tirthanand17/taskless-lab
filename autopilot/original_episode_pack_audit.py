"""Offline original FlowMinute 3-video editorial pack QA — NOT media QA.

Validates a real drafted October 20 source-linked script/storyboard, checks
separate Hindi/English Shorts and Hindi long lesson, scene coverage, fact
source binding, mock-interface labels, source provenance and hard-unverified
voice/audio/render/publishing flags. Does NOT create WAV, MP4, SRT, thumbnails,
Google sessions, external service calls, model downloads or live publishing.

This is lexical/script QA. It does NOT prove source claim truth, reviewer
identity, accent, voiced-language, voice consent, spoken timing, copyright
ownership of future footage or video originality on YouTube.
"""
from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
import json
import re

from .agent_org import WorkflowError

PACK=Path(__file__).resolve().parents[1]/"content/production-packs/2026-10-20-gemini-agent-control.json"
VERSION="flowminute-original-editorial-pack-v1"
DATE="2026-10-20"
EXPECTED={
    "fm_20261020_short_en":("short","en",42),
    "fm_20261020_short_hi":("short","hi",44),
    "fm_20261020_long_hi":("long","hi",480),
}
SOURCES={
    "google_argon_app":"https://blog.google/innovation-and-ai/products/gemini-app/gemini-4-argon-availability/",
    "google_workspace_agent":"https://cloud.google.com/blog/products/ai-machine-learning/welcome-to-gemini-at-work-2026",
    "youtube_original_short":"https://support.google.com/youtube/blog/470890423/prioritizing-original-content-on-shorts?hl=en",
}
FALSE_FLAGS=(
    "original_footage_and_audio_available","prerecorded_voice_exists",
    "real_asr_word_timing_checked","license_and_consent_verified",
    "actual_provider_demo_executed","original_narrator_identity_verified",
    "actual_thumbnail_rendered","actual_media_encoded",
    "youtube_schedule_verified","private_upload_authorized",
    "public_publish_authorized",
)
TRUE_FLAGS=(
    "two_separate_shorts_one_hindi_one_english","one_hindi_long",
    "original_illustration_only",
)
ALLOWED_ASPECT={"short":"9:16","long":"16:9"}
_EP_KEYS=frozenset((
    "episode_id","kind","original_spoken_language","narrator_plan_id",
    "target_duration_seconds","title","thumbnail_copy","description",
    "hook_strategy","aspect_ratio","segments",
))
_SEGMENT_KEYS=frozenset((
    "start_second","end_second","narration","visual_guide",
    "source_ids","original_research_demo",
))
_CORE_KEYS=frozenset((
    "schema_version","date_local","timezone","project","status",
    "source_checked_on","topical_reason","sources",
    "content_release_policy","visualization_direction","episodes",
))
_SRC_KEYS=frozenset(("id","publisher","published_date","url","use"))
_POLICY_KEYS=frozenset(TRUE_FLAGS+FALSE_FLAGS+("recurring_infrastructure_inr",))
_REQUIRED_VISUAL=frozenset((
    "editorial_style","shorts","long","rights","speech",
))
_BIDI=re.compile("[\u202a-\u202e\u2066-\u2069]")
_LINK=re.compile(r"(?:https?://|www\.)",re.IGNORECASE)
_SHA=re.compile(r"\b[a-f0-9]{64}\b",re.IGNORECASE)
LABELS=("MOCK","CONCEPT","DEMO","HYPOTHETICAL","NOT CONNECTED","काल्पनिक")
_SPOKEN_DENY=("guaranteed viral","100% accurate","unlimited free",
             "सबको मुफ्त","one click buy",
             "fully automated purchase")


def _deny():
    raise WorkflowError("Original episode pack not admitted; editorial holds remain")


def _safe_text(text, *,limit=6000):
    return (type(text) is str and 1<=len(text.strip())<=limit
            and "\x00" not in text
            and not _BIDI.search(text))


def _strict_day(value):
    try:
        if type(value) is not str or len(value)!=10:
            return False
        return date.fromisoformat(value).isoformat()==value
    except (ValueError,OverflowError):
        return False


def audit_original_editorial_pack(*,source_json:str|None=None)->dict:
    """Only a script/storyboard review gate; every publishing bit is FALSE."""
    if source_json is None:
        source_json=PACK.read_text(encoding="utf-8")
    if type(source_json) is not str or not 4000<=len(source_json)<=120000:
        _deny()
    try:
        payload=json.loads(source_json)
    except (ValueError,UnicodeError):
        _deny()
    if (type(payload) is not dict or set(payload)!=_CORE_KEYS
            or payload["schema_version"]!=VERSION
            or payload["date_local"]!=DATE
            or payload["timezone"]!="Asia/Kolkata"
            or payload["project"]!="FlowMinute Lab"
            or payload["status"]!="SCRIPT_AND_STORYBOARD_CANDIDATE_ONLY"
            or not _strict_day(payload["source_checked_on"])
            or payload["source_checked_on"]>DATE
            or not _safe_text(payload["topical_reason"],limit=500)
            or type(payload["visualization_direction"]) is not dict
            or set(payload["visualization_direction"])!=_REQUIRED_VISUAL
            or any(not _safe_text(v,limit=800) for v in payload["visualization_direction"].values())):
        _deny()
    policy=payload["content_release_policy"]
    if (type(policy) is not dict or set(policy)!=_POLICY_KEYS
            or any(policy[k] is not False for k in FALSE_FLAGS)
            or any(policy[k] is not True for k in TRUE_FLAGS)
            or type(policy["recurring_infrastructure_inr"]) is not int
            or policy["recurring_infrastructure_inr"]!=0):
        _deny()
    sources=payload["sources"]
    if type(sources) is not list or len(sources)!=len(SOURCES):
        _deny()
    known={}
    for src in sources:
        if (type(src) is not dict or set(src)!=_SRC_KEYS
                or type(src.get("id")) is not str
                or src["id"] not in SOURCES or src["id"] in known
                or src.get("url")!=SOURCES[src["id"]]
                or not _safe_text(src.get("publisher"),limit=80)
                or not _safe_text(src.get("use"),limit=320)
                or not _strict_day(src.get("published_date"))
                or src["published_date"]>payload["source_checked_on"]):
            _deny()
        parsed=urlsplit(src["url"])
        if parsed.scheme!="https" or not parsed.hostname or parsed.username:
            _deny()
        known[src["id"]]=src
    if set(known)!=set(SOURCES):
        _deny()
    episodes=payload["episodes"]
    if type(episodes) is not list or len(episodes)!=3:
        _deny()
    seen={}
    narrators=set()
    titles=set()
    counts=Counter()
    source_usage=Counter()
    for ep in episodes:
        if type(ep) is not dict or set(ep)!=_EP_KEYS:
            _deny()
        episode_id=ep["episode_id"]
        if (type(episode_id) is not str or episode_id not in EXPECTED
                or episode_id in seen
                or type(ep["target_duration_seconds"]) is not int):
            _deny()
        kind,lang,duration=EXPECTED[episode_id]
        if (ep["kind"],ep["original_spoken_language"],
                ep["target_duration_seconds"])!=(kind,lang,duration):
            _deny()
        if (not _safe_text(ep["title"],limit=105)
                or not _safe_text(ep["description"],limit=2200)
                or not _safe_text(ep["thumbnail_copy"],limit=60)
                or not _safe_text(ep["hook_strategy"],limit=230)
                or type(ep["narrator_plan_id"]) is not str
                or not ep["narrator_plan_id"].startswith("voice_")
                or not ep["narrator_plan_id"].endswith("_unlicensed")
                or ep["narrator_plan_id"] in narrators
                or ep["title"] in titles
                or ep["aspect_ratio"]!=ALLOWED_ASPECT[kind]):
            _deny()
        titles.add(ep["title"])
        narrators.add(ep["narrator_plan_id"])
        scenes=ep["segments"]
        if (type(scenes) is not list or
                not (7<=len(scenes)<=13) or
                (kind=="short" and len(scenes)!=7) or
                (kind=="long" and len(scenes)<10)):
            _deny()
        prior=0
        total_words=0
        concatenated=[]
        cited=0
        demos=0
        for chapter in scenes:
            if (type(chapter) is not dict or set(chapter)!=_SEGMENT_KEYS
                    or type(chapter["start_second"]) is not int
                    or type(chapter["end_second"]) is not int
                    or chapter["start_second"]!=prior
                    or chapter["end_second"]<=prior
                    or not _safe_text(chapter["narration"],limit=1200)
                    or not _safe_text(chapter["visual_guide"],limit=900)
                    or type(chapter["original_research_demo"]) is not bool
                    or type(chapter["source_ids"]) is not list
                    or len(chapter["source_ids"])>3
                    or len(chapter["source_ids"])!=len(set(
                        str(x) for x in chapter["source_ids"]))):
                _deny()
            if any(type(s) is not str or s not in SOURCES
                   for s in chapter["source_ids"]):
                _deny()
            if chapter["original_research_demo"]:
                demos+=1
                if not any(label in chapter["visual_guide"].upper()
                           for label in LABELS):
                    _deny()
            for ref in chapter["source_ids"]:
                source_usage[ref]+=1
                cited+=1
            prior=chapter["end_second"]
            chapter_words=len(chapter["narration"].split())
            if chapter_words<5 or chapter_words>(65 if kind=="short" else 175):
                _deny()
            total_words+=chapter_words
            concatenated.append(chapter["narration"])
        if prior!=duration or demos<3 or cited<2:
            _deny()
        narration=" ".join(concatenated)
        if (any(bad in narration.lower() for bad in _SPOKEN_DENY)
                or _LINK.search(narration) or _BIDI.search(narration)
                or _SHA.search(narration)):
            _deny()
        devan=sum("\u0900"<=c<="\u097f" for c in narration)
        latin=sum(c.isascii() and c.isalpha() for c in narration)
        if (lang=="hi" and not devan>=max(100,2*latin)
                or lang=="en" and (devan!=0 or latin<100)):
            _deny()
        if kind=="short" and not 60<=total_words<=120:
            _deny()
        if kind=="long" and not 650<=total_words<=1000:
            _deny()
        seen[episode_id]=True
        counts[kind]+=1
    if set(seen)!=set(EXPECTED) or counts!=Counter({"short":2,"long":1}):
        _deny()
    if not all(source_usage[k]>=1 for k in (
            "google_argon_app","google_workspace_agent")):
        _deny()
    # This reports editorial preparation only, never media/readiness.
    return {
        "status":"ORIGINAL_EDITED_SCRIPT_AND_SCENE_PLAN_ONLY",
        "production_date_local":DATE,
        "source_checked_date":"2026-10-19",
        "independent_language_lanes":3,
        "hindi_short_count":1,
        "english_short_count":1,
        "hindi_long_count":1,
        "narrator_plan_labels_distinct":len(narrators)==3,
        "source_reference_count":len(sources),
        "source_bound_scene_count":sum(
            bool(scene["source_ids"]) for e in episodes for scene in e["segments"]),
        "total_storyboard_scenes":sum(len(e["segments"]) for e in episodes),
        "complete_scene_timing_drafts":True,
        "all_visual_demonstrations_are_marked_mockups":True,
        "licensed_narration_recordings_observed":False,
        "natural_distinct_voice_verified":False,
        "spoken_words_independently_transcribed":False,
        "actual_srt_alignment_verified":False,
        "real_hd_media_rendered":False,
        "rights_or_creator_identity_authored":False,
        "actual_provider_tasks_demo_verified":False,
        "youtube_upload_authorized":False,
        "youtube_publishing_authorized":False,
        "cloud_audio_or_video_jobs_executed":0,
        "external_api_calls":0,
        "monthly_recurring_infrastructure_inr":0,
    }
