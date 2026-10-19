"""Real SRT drafts for Oct20 independently authored EN/HI/HI-long episodes.

Scene starts/ends are ORIGINAL SCRIPT EDITORIAL TIMINGS, not genuine acoustic
alignment. SRT is valid and useful in offline video editors, but MUST NOT be
muxed or posted as verified captions before owned licensed spoken narration,
independent transcription, per-word timing and human pronunciation review.

Only local source-locked script and bounded local file export. No Google,
YouTube, TTS, ASR model, provider, device capture, voice or internet.
"""
from __future__ import annotations

from hashlib import sha256
from math import ceil
from pathlib import Path
import re

from .agent_org import WorkflowError
from .oct20_owned_voice_handoff import create_oct20_voice_session_packet
from .phase3_voice_subtitle_handoff import _timecode

MAX_DISPLAY_CHARS=64
MAX_LINE_CHARS=36
MAX_CUE_MS=4500
MIN_CUE_MS=500
MAX_GROUP_WORDS=10
_EP=re.compile(r"fm_20261020_(?:short_en|short_hi|long_hi)\Z")


def _deny():
    raise WorkflowError("Unverified Oct20 estimated subtitle draft refused")


def _lines(words:tuple[str,...])->tuple[str,...]:
    if not words or any(not w or len(w)>MAX_LINE_CHARS or
                         "\n" in w or "\r" in w or "<" in w or ">" in w
                         for w in words):
        _deny()
    result=[""]
    for word in words:
        candidate=(result[-1]+" "+word).strip()
        if len(candidate)<=MAX_LINE_CHARS:
            result[-1]=candidate
        elif len(result)<2:
            result.append(word)
        else:
            _deny()
    if any(not line for line in result):
        _deny()
    return tuple(result)


def _group_words(words:tuple[str,...])->list[tuple[str,...]]:
    """Greedy, bounded two-line groups without changing any spoken token."""
    result=[]
    index=0
    while index<len(words):
        current=[]
        while index<len(words):
            candidate=tuple((*current,words[index]))
            if (len(candidate)>MAX_GROUP_WORDS or
                    len(" ".join(candidate))>MAX_DISPLAY_CHARS):
                break
            try:
                _lines(candidate)
            except WorkflowError:
                break
            current=list(candidate)
            index+=1
        if not current:
            _deny()
        result.append(tuple(current))
    return result


def _scene_cues(text:str,start:int,end:int)->list[tuple[int,int,str]]:
    if (type(text) is not str or type(start) is not int or
            type(end) is not int or not 0<=start<end<=600
            or text!=text.strip() or "\n" in text or "\r" in text):
        _deny()
    words=tuple(text.split())
    if not 5<=len(words)<=175:
        _deny()
    groups=_group_words(words)
    span=(end-start)*1000
    minimum=ceil(span/MAX_CUE_MS)
    while len(groups)<minimum:
        # Split the longest viable group near the middle; do not invent
        # text or stretch a cue beyond the reading limit.
        options=[(len(" ".join(group)),i) for i,group in enumerate(groups)
                 if len(group)>1]
        if not options:
            _deny()
        _,i=max(options)
        words_here=groups[i]
        at=len(words_here)//2
        groups[i:i+1]=[words_here[:at],words_here[at:]]
    if span//len(groups)<MIN_CUE_MS:
        _deny()
    if tuple(w for group in groups for w in group)!=words:
        _deny()
    cues=[]
    for index,group in enumerate(groups):
        a=start*1000+(span*index)//len(groups)
        b=start*1000+(span*(index+1))//len(groups)
        if not MIN_CUE_MS<=b-a<=MAX_CUE_MS:
            _deny()
        lines=_lines(group)
        if len(" ".join(group))>MAX_DISPLAY_CHARS:
            _deny()
        cues.append((a,b,"\n".join(lines)))
    return cues


def create_oct20_provisional_srt()->dict:
    """Build three reproducible SRT strings and redacted non-release stats."""
    packet=create_oct20_voice_session_packet()
    if (packet.get("status")!="ORIGINAL_THREE_VIDEO_NARRATOR_RECORDING_SCRIPT_ONLY"
            or packet.get("actual_wav_takes_received")!=0
            or packet.get("youtube_upload_authorized") is not False):
        _deny()
    lanes=packet["lanes"]
    if len(lanes)!=3:
        _deny()
    result={}
    for lane in lanes:
        episode=lane["episode_id"]
        if (not _EP.fullmatch(episode) or episode in result or
                lane["narrator_person_identified_or_licensed"] is not False):
            _deny()
        cues=[]
        previous_end=0
        scene_cue_counts=[]
        for scene in lane["cues"]:
            if scene["editorial_start_second"]!=previous_end:
                _deny()
            group=_scene_cues(scene["recording_text"],
                              scene["editorial_start_second"],
                              scene["editorial_end_second"])
            scene_cue_counts.append(len(group))
            cues.extend(group)
            previous_end=scene["editorial_end_second"]
        if (previous_end!=lane["target_seconds"]
                or len(scene_cue_counts)!=lane["cue_count"]
                or cues[0][0]!=0 or cues[-1][1]!=previous_end*1000
                or any(cues[i][1]!=cues[i+1][0] for i in range(len(cues)-1))):
            _deny()
        raw="\n\n".join(
            f"{i}\n{_timecode(a)} --> {_timecode(b)}\n{line}"
            for i,(a,b,line) in enumerate(cues,1)
        )+"\n"
        spoken=" ".join(" ".join(line.split("\n")) for _,_,line in cues)
        authored=" ".join(scene["recording_text"] for scene in lane["cues"])
        if spoken!=authored:
            _deny()
        if len(raw.encode("utf-8"))>60_000:
            _deny()
        result[episode]={
            "language":lane["language"],
            "target_seconds":lane["target_seconds"],
            "script_sha256":lane["script_sha256"],
            "srt_sha256":sha256(raw.encode("utf-8")).hexdigest(),
            "caption_count":len(cues),
            "original_scene_count":lane["cue_count"],
            "cues_per_scene":tuple(scene_cue_counts),
            "srt":raw,
            "scene_timing_only_estimated":True,
            "real_voice_recording_observed":False,
            "spoken_word_alignment_verified":False,
            "commercial_voice_rights_verified":False,
            "real_audio_mux_authorized":False,
            "youtube_upload_authorized":False,
            "youtube_publishing_authorized":False,
        }
    if len(result)!=3:
        _deny()
    return result


def export_oct20_estimated_srt(destination:Path)->dict:
    """Writes three clean .draft_estimated.srt assets; no preexisting files.

    Strictly an explicit local editor-only export. Never writes private WAV,
    source rights, Google credentials, or YouTube scheduling status.
    """
    if (not isinstance(destination,Path) or destination.is_symlink()
            or not destination.is_dir()):
        _deny()
    results=create_oct20_provisional_srt()
    targets={key:destination/(key+".draft_estimated.srt") for key in results}
    if any(path.exists() or path.is_symlink() for path in targets.values()):
        _deny()
    for episode,rec in results.items():
        targets[episode].write_text(rec["srt"],encoding="utf-8",newline="\n")
    return {
        "status":"THREE_ACTUAL_EDITOR_SRT_FILES_ESTIMATED_NOT_SPOKEN",
        "file_count":3,
        "caption_count":sum(r["caption_count"] for r in results.values()),
        "actual_voice_recordings_received":0,
        "real_speech_alignment_verified":False,
        "commercial_rights_verified":False,
        "youtube_upload_authorized":False,
        "youtube_publish_authorized":False,
        "external_network_calls":0,
        "monthly_recurring_infrastructure_inr":0,
    }
