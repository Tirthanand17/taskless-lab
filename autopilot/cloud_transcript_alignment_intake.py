"""Untrusted word-timing TRANSCRIPT candidate cross-check, not ASR.

Binds a submitted word-timed candidate to the current author-script-derived
SRT and the exact SHA-256 of a separately observed, AAC-screened MP4.
Checks content order, lane, cue windows and stale source hashes.

Crucial: matching externally supplied words to script does NOT prove those
words were uttered in the audio. ASR/human identity, language recognition,
speaker distinctness, consent, legal rights and publishing remain UNVERIFIED.
No model/provider, network, voice, file write or real media processing here.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from typing import Sequence
import re
import unicodedata

from .agent_org import WorkflowError
from .cloud_capacity_admission import FPS,LANES
from .cloud_full_media_evidence import TechnicalFullHDObservation
from .cloud_muxed_audio_screen import MuxedAudioScreen,POSITIONS
from .phase3_voice_subtitle_handoff import build_subtitles_from_authored_csv

MAX_WORDS=4500
MAX_WORD_CHARS=96
MAX_WORD_DURATION_MS=3000
CUE_WINDOW_TOLERANCE_MS=900
HEX64=re.compile(r"[0-9a-f]{64}\Z")
TIME=re.compile(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> "
                r"(\d{2}):(\d{2}):(\d{2}),(\d{3})$")
LANE_EPISODE={
    "short_en":("csv_tutorial_short_en","en"),
    "short_hi":("csv_tutorial_short_hi","hi"),
    "long_hi":("csv_tutorial_long_hi","hi"),
}
SPECS={lane.lane:lane for lane in LANES}


@dataclass(frozen=True)
class TimedTranscriptWord:
    text:str
    start_ms:int
    end_ms:int


@dataclass(frozen=True)
class CandidateWordTranscript:
    """Untrusted ASR/manual/synthetic text claimed against final MP4 audio."""
    lane:str
    episode_id:str
    declared_language:str
    media_sha256:str
    authored_draft_srt_sha256:str
    claimed_method:str
    words:tuple[TimedTranscriptWord,...]


def _time_ms(h:str,m:str,s:str,ms:str)->int:
    values=[int(h),int(m),int(s),int(ms)]
    if values[1]>59 or values[2]>59 or values[3]>999:
        raise WorkflowError("Invalid authored SRT timecode")
    return ((values[0]*60+values[1])*60+values[2])*1000+values[3]


def _draft_cues(episode:str)->tuple[tuple[int,int,tuple[str,...]],...]:
    """Parse the EXACT checked-in authored SRT, no external file or writer."""
    plans=build_subtitles_from_authored_csv()
    if episode not in plans:
        raise WorkflowError("Unknown original subtitle episode")
    item=plans[episode]
    srt=item["srt"]
    if sha256(srt.encode("utf-8")).hexdigest()!=item["srt_sha256"]:
        raise WorkflowError("Authored SRT digest changed during intake")
    blocks=srt.strip().split("\n\n")
    result=[]
    previous=0
    for i,block in enumerate(blocks,1):
        lines=block.split("\n")
        if len(lines)!=3 or lines[0]!=str(i):
            raise WorkflowError("Malformed canonical authored SRT")
        match=TIME.fullmatch(lines[1])
        if match is None:
            raise WorkflowError("Invalid authored SRT cue time")
        a=_time_ms(*match.groups()[:4])
        b=_time_ms(*match.groups()[4:])
        words=tuple(lines[2].split())
        if a!=previous or b<=a or not words:
            raise WorkflowError("Gap, overlap or empty authored subtitle")
        previous=b
        result.append((a,b,words))
    if not result or previous!=item["duration_ms"]:
        raise WorkflowError("Authored SRT does not cover entire episode")
    return tuple(result)


def _normalized(text:str)->str:
    """Unicode-preserving per-token equality (Hindi combining marks kept)."""
    if (not isinstance(text,str) or not 1<=len(text)<=MAX_WORD_CHARS
            or any(ch.isspace() or unicodedata.category(ch)=="Cc"
                   for ch in text)):
        raise WorkflowError("Invalid bounded transcript word")
    value=unicodedata.normalize("NFC",text).casefold()
    while value and (unicodedata.category(value[0]).startswith("P")
                     or unicodedata.category(value[0]).startswith("S")):
        value=value[1:]
    while value and (unicodedata.category(value[-1]).startswith("P")
                     or unicodedata.category(value[-1]).startswith("S")):
        value=value[:-1]
    if not value:
        raise WorkflowError("Transcript word has no lexical content")
    return value


def validate_candidate_word_alignment(
    transcript:CandidateWordTranscript,
    observation:TechnicalFullHDObservation,
    audio_screen:MuxedAudioScreen,
)->dict:
    """Fail on drift, omissions and cross-language reuse, NEVER attest speech."""
    if (not isinstance(transcript,CandidateWordTranscript)
            or not isinstance(observation,TechnicalFullHDObservation)
            or not isinstance(audio_screen,MuxedAudioScreen)):
        raise WorkflowError("Typed transcript and original media required")
    lane=transcript.lane
    if lane not in LANE_EPISODE or lane not in SPECS:
        raise WorkflowError("Transcript from unsupported author language lane")
    episode,language=LANE_EPISODE[lane]
    spec=SPECS[lane]
    drafts=build_subtitles_from_authored_csv()
    target=drafts[episode]
    if (transcript.episode_id!=episode
            or transcript.declared_language!=language
            or transcript.claimed_method not in (
                "unverified_asr","unverified_manual","synthetic_test"
            )
            or transcript.authored_draft_srt_sha256!=target["srt_sha256"]
            or not isinstance(transcript.media_sha256,str)
            or HEX64.fullmatch(transcript.media_sha256) is None
            or observation.lane!=lane or audio_screen.lane!=lane
            or observation.video_sha256!=transcript.media_sha256
            or audio_screen.video_sha256!=transcript.media_sha256
            or observation.width!=spec.width or observation.height!=spec.height
            or observation.frames_decoded_or_counted!=spec.duration_s*FPS
            or observation.whole_media_ffmpeg_decode_passed is not True
            or observation.original_file_unchanged_after_inspection is not True
            or audio_screen.samples_checked!=len(POSITIONS)
            or audio_screen.technical_signal_pass is not True
            or audio_screen.blockers
            or observation.publishing_authorized is not False
            or audio_screen.publishing_authorized is not False):
        raise WorkflowError("Transcript stale, cross-language or media unbound")
    if any(getattr(audio_screen,key) is not False for key in (
        "actual_speech_recognized","intended_language_verified",
        "distinct_short_narrators_verified",
        "spoken_caption_alignment_verified","commercial_rights_verified",
    )):
        raise WorkflowError("Technical sound screen cannot attest real speech")
    if (not isinstance(transcript.words,tuple)
            or not 1<=len(transcript.words)<=MAX_WORDS):
        raise WorkflowError("Bounded ordered transcript words required")
    cues=_draft_cues(episode)
    expected=[(lo,hi,word)
              for lo,hi,cue in cues for word in cue]
    if len(transcript.words)!=len(expected):
        raise WorkflowError("Transcript omitted or invented authored words")
    previous_end=0
    max_deviation=0
    for timed,(cue_start,cue_end,source_word) in zip(transcript.words,expected):
        if (not isinstance(timed,TimedTranscriptWord)
                or type(timed.start_ms) is not int
                or type(timed.end_ms) is not int
                or not 0<=timed.start_ms<timed.end_ms<=spec.duration_s*1000
                or timed.end_ms-timed.start_ms>MAX_WORD_DURATION_MS
                or timed.start_ms<previous_end):
            raise WorkflowError("Transcript has invalid or overlapping word times")
        previous_end=timed.end_ms
        if _normalized(timed.text)!=_normalized(source_word):
            raise WorkflowError("Transcript word differs from authored SRT")
        if (timed.start_ms<max(0,cue_start-CUE_WINDOW_TOLERANCE_MS)
                or timed.end_ms>min(spec.duration_s*1000,
                                    cue_end+CUE_WINDOW_TOLERANCE_MS)):
            raise WorkflowError("Transcript word shifted beyond cue window")
        deviation=max(0,cue_start-timed.start_ms,
                      timed.end_ms-cue_end)
        max_deviation=max(max_deviation,deviation)
    return {
        "status":"TRANSCRIPT_CANDIDATE_TEXT_AND_TIME_SHAPE_ONLY",
        "lane":lane,
        "episode_id":episode,
        "media_sha256":transcript.media_sha256,
        "draft_srt_sha256":transcript.authored_draft_srt_sha256,
        "claimed_provenance_unverified":transcript.claimed_method,
        "checked_word_count":len(expected),
        "checked_cue_count":len(cues),
        "greatest_cue_boundary_overshoot_ms":max_deviation,
        "actual_audio_words_verified":False,
        "ASR_or_human_transcriber_identity_authenticated":False,
        "spoken_language_verified":False,
        "spoken_word_subtitle_sync_verified":False,
        "two_distinct_natural_short_narrators_verified":False,
        "commercial_voice_and_visual_rights_verified":False,
        "upload_authorized":False,
        "publishing_authorized":False,
        "recurring_infrastructure_cost_inr":0,
    }


def summarize_candidate_transcript_batch(records:Sequence[dict])->dict:
    """All three original language lanes must be present; no release rights."""
    if not isinstance(records,tuple) or len(records)>len(LANE_EPISODE):
        raise WorkflowError("Bounded tuple of transcript summaries required")
    seen=set()
    for record in records:
        if (not isinstance(record,dict)
                or set(record)!={
                    "status","lane","episode_id","media_sha256",
                    "draft_srt_sha256","claimed_provenance_unverified",
                    "checked_word_count","checked_cue_count",
                    "greatest_cue_boundary_overshoot_ms",
                    "actual_audio_words_verified",
                    "ASR_or_human_transcriber_identity_authenticated",
                    "spoken_language_verified","spoken_word_subtitle_sync_verified",
                    "two_distinct_natural_short_narrators_verified",
                    "commercial_voice_and_visual_rights_verified",
                    "upload_authorized","publishing_authorized",
                    "recurring_infrastructure_cost_inr",
                }):
            raise WorkflowError("Unknown/corrupted transcript evidence summary")
        lane=record["lane"]
        if lane not in LANE_EPISODE or lane in seen:
            raise WorkflowError("Duplicate or unsupported language transcript")
        episode,language=LANE_EPISODE[lane]
        if (record["status"]!="TRANSCRIPT_CANDIDATE_TEXT_AND_TIME_SHAPE_ONLY"
                or record["episode_id"]!=episode
                or HEX64.fullmatch(str(record["media_sha256"])) is None
                or record["draft_srt_sha256"]!=
                    build_subtitles_from_authored_csv()[episode]["srt_sha256"]
                or type(record["checked_word_count"]) is not int
                or record["checked_word_count"]<=0
                or type(record["checked_cue_count"]) is not int
                or record["checked_cue_count"]<=0
                or type(record["greatest_cue_boundary_overshoot_ms"]) is not int
                or not 0<=record["greatest_cue_boundary_overshoot_ms"]<=
                    CUE_WINDOW_TOLERANCE_MS
                or record["claimed_provenance_unverified"] not in (
                    "unverified_asr","unverified_manual","synthetic_test"
                )
                or record["recurring_infrastructure_cost_inr"]!=0
                or any(record[k] is not False for k in (
                    "actual_audio_words_verified",
                    "ASR_or_human_transcriber_identity_authenticated",
                    "spoken_language_verified",
                    "spoken_word_subtitle_sync_verified",
                    "two_distinct_natural_short_narrators_verified",
                    "commercial_voice_and_visual_rights_verified",
                    "upload_authorized","publishing_authorized",
                ))):
            raise WorkflowError("Transcript packet attempted to promote approval")
        seen.add(lane)
    return {
        "status":"THREE_LANE_TRANSCRIPT_SHAPE_PREFLIGHT_ONLY",
        "candidate_lanes_received":tuple(sorted(seen)),
        "missing_lanes":tuple(sorted(set(LANE_EPISODE)-seen)),
        "all_three_candidate_shapes_present":seen==set(LANE_EPISODE),
        "actual_spoken_language_and_alignment_verified":False,
        "real_narrator_identity_and_rights_verified":False,
        "independent_review_signatures_verified":False,
        "youtube_publishing_authorized":False,
        "monthly_recurring_infrastructure_inr":0,
    }
