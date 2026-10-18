"""FlowMinute Phase 2R3 / 3R1: audience-language lanes WITHOUT audience targeting.

The owner wants one original Hindi/Hinglish Short for Hindi-speaking viewers
and a separate English Short for English-speaking viewers. Use correctly
localized spoken scripts, SRT, metadata, and future distinct narrators.
YouTube can *infer* viewer language; it cannot promise exclusive delivery.
No upload, distribution account, licensed speech, auto-dubbing, Analytics
connection or new service is used here.

Docs: https://support.google.com/youtube/answer/6304325
https://support.google.com/youtube/answer/7296123
https://developers.google.com/youtube/data/reference/rest/v3/videos
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any

from .agent_org import WorkflowError
from .phase2r3_authored_pack_audit import SOURCE, SECTIONS, TIME, _sections
from .phase3_voice_subtitle_handoff import build_subtitles_from_authored_csv

GROUP="csv_practical_bilingual_education"
LANES={
    "csv_tutorial_short_hi": {
        "kind":"short","language":"hi","target_audience_language":"hi",
        "title":"Python से CSV फ़ाइल समझें | आसान डेटा टिप",
        "description":(
            "Python से CSV फ़ाइल, कॉलम और नकली डेटा का आसान उदाहरण सीखें। "
            "यह केवल काल्पनिक शिक्षा का उदाहरण है, असली ग्राहक या खरीदारी डेटा नहीं। "
            "हिंदी में पूरी CSV सीखने के लिए हमारी हिंदी ट्यूटोरियल देखें।"
        ),
        "thumbnail_language":"hi",
        "caption_language":"hi",
        "discovery_lane":"hindi_viewer_language_intent",
        "long_video_followup":"csv_tutorial_long_hi",
    },
    "csv_tutorial_short_en":{
        "kind":"short","language":"en","target_audience_language":"en",
        "title":"Understand CSV Files in 42 Seconds | Python Tip",
        "description":(
            "Learn the Python CSV DictReader basics using fictional example data. "
            "See how columns and simple arithmetic work without uploading private files. "
            "Follow for more English Python and automation lessons."
        ),
        "thumbnail_language":"en",
        "caption_language":"en",
        "discovery_lane":"english_viewer_language_intent",
        # The ONLY authored long tutorial is currently Hindi; do not mislead
        # English viewers into believing an English full lesson exists.
        "long_video_followup":None,
    },
    "csv_tutorial_long_hi":{
        "kind":"long","language":"hi","target_audience_language":"hi",
        "title":"Python से CSV Automation सीखें | हिंदी पूरी गाइड",
        "description":(
            "हिंदी में Python CSV फ़ाइल पढ़ना, कॉलम समझना, DictReader, "
            "DictWriter और नकली डेटा पर गणना करना सीखें। यह केवल "
            "शिक्षण के लिए काल्पनिक उदाहरण है, असली लेनदेन नहीं।"
        ),
        "thumbnail_language":"hi",
        "caption_language":"hi",
        "discovery_lane":"hindi_viewer_language_intent",
        "long_video_followup":None,
    },
}
DEVANAGARI=re.compile(r"[\u0904-\u0939\u0958-\u0961]")
LATIN=re.compile(r"[A-Za-z]")
TAGS={
    "hi":("Python","CSV","डेटा","हिंदी","ऑटोमेशन"),
    "en":("Python","CSV","data","automation","tutorial"),
}


def _spoken_language_check(text:str,expected:str)->dict:
    if not isinstance(text,str) or len(text)<80:
        raise WorkflowError("Insufficient authored original spoken language text")
    count_deva=len(DEVANAGARI.findall(text))
    count_latin=len(LATIN.findall(text))
    if expected=="hi":
        # Hinglish technical terms (CSV, Python, DictReader) are legitimate.
        if count_deva<100 or count_deva/(count_deva+count_latin)<.5:
            raise WorkflowError("Hindi narration text is not predominantly Hindi")
    elif expected=="en":
        # No Hindi-language spoken text should leak into English Short.
        if count_deva or count_latin<100:
            raise WorkflowError("English narrator screenplay contains Hindi/too little English")
    else:
        raise WorkflowError("Unapproved spoken language")
    return {"devanagari_letters":count_deva,"latin_letters":count_latin}


def _metadata_language_check(language:str,title:str,description:str)->None:
    if not isinstance(title,str) or not 12<=len(title)<=100:
        raise WorkflowError("Unapproved title length")
    if not isinstance(description,str) or not 80<=len(description)<=1500:
        raise WorkflowError("Unapproved audience-language description")
    title_dev=len(DEVANAGARI.findall(title))
    desc_dev=len(DEVANAGARI.findall(description))
    if language=="hi":
        if title_dev<6 or desc_dev<35:
            raise WorkflowError("Hindi lane must have actual native-script metadata")
    elif language=="en":
        if title_dev or desc_dev:
            raise WorkflowError("English lane metadata must not be cross-language")
    else:
        raise WorkflowError("Unsupported language")


def prepare_audience_language_lanes(*,markdown:str|None=None,
                                    lane_specs:dict|None=None)->dict[str,Any]:
    """Build a deterministic, SHA-bound metadata *proposal*, NOT an upload.

    The candidate YouTube snippet defaultLanguage is valid only after the
    final narrator/video is approved. defaultAudioLanguage is left unset:
    no genuine recording exists and the current video proofs are SILENT.
    """
    raw=SOURCE.read_text(encoding="utf-8") if markdown is None else markdown
    sections=_sections(raw)
    specs=LANES if lane_specs is None else lane_specs
    ids={s[2] for s in SECTIONS}
    if not isinstance(specs,dict) or set(specs)!=ids or len(specs)!=3:
        raise WorkflowError("Exactly one Hindi Short, one English Short, Hindi long required")
    subtitles=build_subtitles_from_authored_csv(markdown=raw)
    episodes=[]
    narrators=set()
    for section,(kind,lang,episode,narrator,duration,beats) in zip(sections,SECTIONS):
        info=specs[episode]
        if not isinstance(info,dict) or any(
            info.get(key)!=value for key,value in (
                ("kind",kind),("language",lang),
                ("target_audience_language",lang),("caption_language",lang),
                ("thumbnail_language",lang),
            )
        ):
            raise WorkflowError("Cross-language thumbnail, captions or audience lane")
        if info.get("discovery_lane")!=("hindi_viewer_language_intent" if lang=="hi" else "english_viewer_language_intent"):
            raise WorkflowError("Mismatched audience language intent")
        expected_follow="csv_tutorial_long_hi" if episode=="csv_tutorial_short_hi" else None
        if info.get("long_video_followup")!=expected_follow:
            raise WorkflowError("Language-crossing unsupported long-video recommendation")
        title,description=info.get("title"),info.get("description")
        _metadata_language_check(lang,title,description)
        scene=TIME.findall(section)
        if len(scene)!=beats:
            raise WorkflowError("Script count drift during localization")
        spoken=" ".join(row[4] for row in scene)
        _spoken_language_check(spoken,lang)
        caption=subtitles[episode]
        if caption["language"]!=lang or caption["narrator_plan_id"]!=narrator:
            raise WorkflowError("Narrator or subtitles do not match target language")
        if not caption["timings_are_script_estimates"] or caption["actual_voice_alignment_verified"]:
            raise WorkflowError("Draft captions cannot claim real speech synchronization")
        if narrator in narrators:
            raise WorkflowError("Distinct episodes require distinct planned narrator IDs")
        narrators.add(narrator)
        lane={
            "episode_id":episode,"episode_kind":kind,
            "content_group_id":GROUP,
            "original_spoken_language":lang,
            "intended_viewer_language":lang,
            "title":title,"description":description,
            "tags":TAGS[lang],
            "subtitle_language":lang,"thumbnail_language":lang,
            "narrator_plan_id":narrator,
            "related_long_episode_id":expected_follow,
            "script_section_sha256":sha256(section.encode("utf-8")).hexdigest(),
            "script_spoken_text_sha256":sha256(spoken.encode("utf-8")).hexdigest(),
            "draft_srt_sha256":caption["srt_sha256"],
            "video_default_language_proposed":lang,
            "video_default_audio_language_proposed":lang,
            "actual_audio_language_verified":False,
            "youtube_snippet_default_audio_language_set":False,
            "speech_to_caption_alignment_verified":False,
            "independent_native_language_editor_verified":False,
            "licensed_distinct_narrator_verified":False,
            "translated_metadata_reviewed_by_human":False,
            "geographic_or_language_audience_exclusivity_guaranteed":False,
            "actual_audience_language_distribution_measured":False,
            "ready_for_upload":False,
            "publishing_authorized":False,
        }
        episodes.append(lane)
    if len({e["episode_id"] for e in episodes})!=3 or len(narrators)!=3:
        raise WorkflowError("Episode and narrator collisions")
    if {e["original_spoken_language"] for e in episodes if e["episode_kind"]=="short"}!={"hi","en"}:
        raise WorkflowError("Both target Short languages mandatory")
    # Treat metadata as metadata. Never claim a ready-to-send live YouTube
    # resource or actual platform delivery to language-specific viewers.
    return {
        "status":"TWO_SEPARATE_SHORT_LANGUAGE_LANES_DRAFT_NOT_UPLOADED",
        "policy":"Hindi Short for Hindi-speaking audience; English Short for English-speaking audience; separately validated original content",
        "episodes":episodes,
        "intended_daily_shorts":2,
        "intended_hindi_shorts":1,
        "intended_english_shorts":1,
        "recommended_single_channel":True,
        "auto_dub_enabled_or_toggled":False,
        "separate_youtube_channels_created":False,
        "youtube_language_matching_guaranteed":False,
        "real_analytics_or_geo_measurement_available":False,
        "actual_uploaded_videos":0,
        "network_calls":0,
        "publishing_authorized":False,
    }


def report_language_tracking_plan()->dict:
    """Metrics schema only; no fabricated YouTube Analytics observations."""
    return {
        "language_lanes":("hi","en"),
        "metrics_per_lane":(
            "views","shorts_shown_in_feed","viewed_vs_swiped_away",
            "average_view_duration","average_percentage_viewed",
            "subscribers_gained","traffic_geography_if_available",
            "audience_subtitle_language_if_available",
        ),
        "data_connected":False,
        "youtube_analytics_readback_verified":False,
        "counts":None,
        "no_guaranteed_language_only_distribution":True,
        "publishing_authorized":False,
    }
