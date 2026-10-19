"""Phase 3X: October-20 untrusted transcript retime intake, not ASR evidence.

Binds a proposed word-timed transcript to ALL of the exact October 20 script,
SRT, episode, language and audio-digest metadata. This is a lexical and time
SHAPE check only: self-asserted words/timings, even with a SHA of a WAV, do
not demonstrate someone said them, speech identity, rights or naturalness.

No microphone, internet, Google, TTS, ASR model, voice recording, media write,
upload, scheduling, publisher, external provider or private user data.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Sequence
import re

from .agent_org import WorkflowError
from .cloud_transcript_alignment_intake import _normalized
from .oct20_estimated_subtitles import create_oct20_provisional_srt
from .oct20_owned_voice_handoff import create_oct20_voice_session_packet

ALLOWED={
    "fm_20261020_short_en":("en",42000),
    "fm_20261020_short_hi":("hi",44000),
    "fm_20261020_long_hi":("hi",480000),
}
HEX=re.compile(r"[0-9a-f]{64}\Z")
STAMP=re.compile(
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> "
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\Z")
METHODS=frozenset(("unverified_manual","unverified_asr","synthetic_test"))
MAX_WORDS=1500
MAX_SHIFT_MS=10_000


def _deny():
    raise WorkflowError("Oct20 transcript candidate HOLD; audio review unverified")


def _milliseconds(parts:tuple[str,...])->int:
    if len(parts)!=4:
        _deny()
    h,m,s,ms=map(int,parts)
    if not (0<=h<=1 and 0<=m<60 and 0<=s<60 and 0<=ms<1000):
        _deny()
    return ((h*60+m)*60+s)*1000+ms


@dataclass(frozen=True)
class Oct20Word:
    """Untrusted claimed word timing, which may be fabricated."""
    text:str
    start_ms:int
    end_ms:int


@dataclass(frozen=True,repr=False)
class Oct20TranscriptCandidate:
    episode_id:str
    language:str
    claimed_method:str
    claimed_wav_sha256:str
    exact_script_sha256:str
    exact_estimated_srt_sha256:str
    words:tuple[Oct20Word,...]

    def __repr__(self)->str:
        return "<Oct20TranscriptCandidate unverified (words and hashes redacted)>"


def current_oct20_cue_binding(episode_id:str)->dict:
    """Read BOTH generated and on-repository .srt; prevent drift or spoofing."""
    if type(episode_id) is not str or episode_id not in ALLOWED:
        _deny()
    drafts=create_oct20_provisional_srt()
    session=create_oct20_voice_session_packet()
    by_episode={x["episode_id"]:x for x in session["lanes"]}
    item=drafts.get(episode_id)
    source=by_episode.get(episode_id)
    if item is None or source is None:
        _deny()
    lang,total=ALLOWED[episode_id]
    if (item["language"]!=lang or source["language"]!=lang
            or item["target_seconds"]*1000!=total
            or source["target_seconds"]*1000!=total
            or item["script_sha256"]!=source["script_sha256"]
            or item["spoken_word_alignment_verified"] is not False):
        _deny()
    filename=Path(__file__).resolve().parents[1]/"content/production-packs/srt"/(
        episode_id+".draft_estimated.srt")
    if filename.is_symlink() or not filename.is_file():
        _deny()
    raw=filename.read_bytes()
    if (len(raw)>75000 or len(raw)<100
            or sha256(raw).hexdigest()!=item["srt_sha256"]
            or raw!=item["srt"].encode("utf-8")):
        _deny()
    boundaries=[]
    expected=[]
    last=0
    for ordinal,block in enumerate(item["srt"].strip().split("\n\n"),1):
        lines=block.splitlines()
        if (len(lines)<3 or len(lines)>4 or lines[0]!=str(ordinal)):
            _deny()
        match=STAMP.fullmatch(lines[1])
        if match is None:
            _deny()
        start=_milliseconds(match.groups()[:4])
        end=_milliseconds(match.groups()[4:])
        if (start!=last or end<=start or end>total
                or any(not line or len(line)>36 for line in lines[2:])):
            _deny()
        group=" ".join(lines[2:]).split()
        for word in group:
            expected.append((start,end,word,ordinal))
        boundaries.append((start,end))
        last=end
    if (last!=total or len(boundaries)!=item["caption_count"]
            or not 1<=len(expected)<=MAX_WORDS):
        _deny()
    original=" ".join(cue["recording_text"] for cue in source["cues"])
    if " ".join(x[2] for x in expected)!=original:
        _deny()
    return {
        "episode_id":episode_id,"language":lang,"duration_ms":total,
        "script_sha256":item["script_sha256"],
        "draft_srt_sha256":item["srt_sha256"],
        "caption_count":len(boundaries),
        "expected_words":tuple(expected),
        "caption_boundaries":tuple(boundaries),
        "script_scene_count":len(source["cues"]),
    }


def inspect_oct20_untrusted_word_timing(candidate:Oct20TranscriptCandidate)->dict:
    """Candidate compare for an editor, never proof of genuine spoken words."""
    if type(candidate) is not Oct20TranscriptCandidate:
        _deny()
    ep=candidate.episode_id
    if type(ep) is not str or ep not in ALLOWED:
        _deny()
    binding=current_oct20_cue_binding(ep)
    if (candidate.language!=binding["language"]
            or type(candidate.claimed_method) is not str
            or candidate.claimed_method not in METHODS
            or type(candidate.claimed_wav_sha256) is not str
            or HEX.fullmatch(candidate.claimed_wav_sha256) is None
            or candidate.exact_script_sha256!=binding["script_sha256"]
            or candidate.exact_estimated_srt_sha256!=binding["draft_srt_sha256"]
            or type(candidate.words) is not tuple
            or len(candidate.words)!=len(binding["expected_words"])):
        _deny()
    previous=0
    max_deviation=0
    observed_min=None
    for proposed,(a,b,source_word,_cue) in zip(
        candidate.words,binding["expected_words"],
    ):
        if (type(proposed) is not Oct20Word
                or type(proposed.start_ms) is not int
                or type(proposed.end_ms) is not int
                or not previous<=proposed.start_ms<proposed.end_ms<=binding["duration_ms"]
                or proposed.end_ms-proposed.start_ms>3000):
            _deny()
        try:
            normalized=_normalized(proposed.text)
            expected=_normalized(source_word)
        except (ValueError,TypeError,WorkflowError):
            _deny()
        if normalized!=expected:
            _deny()
        # Do NOT enforce estimated cue-window matching; actual spoken takes
        # may require editing the VIDEO scene rather than speeding speech.
        # Instead report the largest offset for manual re-editing.
        deviation=max(
            0,a-proposed.start_ms,proposed.end_ms-b,
        )
        max_deviation=max(max_deviation,deviation)
        observed_min=(proposed.start_ms if observed_min is None
                      else observed_min)
        previous=proposed.end_ms
    return {
        "status":"OCT20_CLAIMED_WORD_TIMING_EDITOR_REVIEW_ONLY",
        "episode_id":ep,
        "language":binding["language"],
        "duration_ms":binding["duration_ms"],
        "authored_scene_count":binding["script_scene_count"],
        "source_caption_count":binding["caption_count"],
        "claimed_word_count":len(candidate.words),
        "exact_script_and_srt_text_shape_matched":True,
        "largest_outside_estimated_caption_window_ms":max_deviation,
        "retime_editor_attention_required":max_deviation>900,
        "claimed_audio_sha_is_authenticated":False,
        "source_wav_technical_evidence_verified":False,
        "word_timings_observed_from_actual_audio":False,
        "ASR_provenance_authenticated":False,
        "natural_human_speech_verified":False,
        "commercial_voice_rights_authenticated":False,
        "speaker_consent_authenticated":False,
        "spoken_language_pronunciation_verified":False,
        "two_short_narrators_distinct_verified":False,
        "actual_audio_caption_alignment_verified":False,
        "ready_for_mux":False,
        "youtube_upload_authorized":False,
        "youtube_publish_authorized":False,
        "external_network_calls":0,
        "monthly_recurring_infrastructure_inr":0,
    }


def summarize_oct20_word_timing_batch(
    reviews:Sequence[dict],
)->dict:
    """Require every original episode; no single good lane unlocks publishing."""
    if type(reviews) is not tuple or len(reviews)!=3:
        _deny()
    lanes=set()
    for record in reviews:
        if (type(record) is not dict
                or record.get("status")!="OCT20_CLAIMED_WORD_TIMING_EDITOR_REVIEW_ONLY"
                or record.get("episode_id") not in ALLOWED):
            _deny()
        ep=record["episode_id"]
        if ep in lanes:
            _deny()
        binding=current_oct20_cue_binding(ep)
        if (record.get("duration_ms")!=binding["duration_ms"]
                or record.get("language")!=binding["language"]
                or record.get("authored_scene_count")!=binding["script_scene_count"]
                or record.get("source_caption_count")!=binding["caption_count"]
                or record.get("claimed_word_count")!=len(binding["expected_words"])
                or record.get("exact_script_and_srt_text_shape_matched") is not True
                or type(record.get("largest_outside_estimated_caption_window_ms")) is not int
                or record["largest_outside_estimated_caption_window_ms"]<0
                or record.get("retime_editor_attention_required") is not
                    (record["largest_outside_estimated_caption_window_ms"]>900)):
            _deny()
        for flag in (
            "claimed_audio_sha_is_authenticated",
            "source_wav_technical_evidence_verified",
            "word_timings_observed_from_actual_audio",
            "ASR_provenance_authenticated",
            "natural_human_speech_verified",
            "commercial_voice_rights_authenticated",
            "speaker_consent_authenticated",
            "spoken_language_pronunciation_verified",
            "two_short_narrators_distinct_verified",
            "actual_audio_caption_alignment_verified",
            "ready_for_mux","youtube_upload_authorized",
            "youtube_publish_authorized",
        ):
            if record.get(flag) is not False:
                _deny()
        if (record.get("external_network_calls")!=0
                or record.get("monthly_recurring_infrastructure_inr")!=0):
            _deny()
        lanes.add(ep)
    if lanes!=set(ALLOWED):
        _deny()
    return {
        "status":"OCT20_THREE_LANE_UNVERIFIED_TRANSCRIPTS_SHAPE_ONLY",
        "three_language_episodes_matched":True,
        "editor_retime_needed_in_any_lane":any(
            x["retime_editor_attention_required"] for x in reviews),
        "real_speech_transcribed_or_recognized":False,
        "rights_and_human_identity_authenticated":False,
        "real_word_to_audio_alignment_verified":False,
        "source_audio_evidence_received":False,
        "youtube_upload_authorized":False,
        "youtube_publish_authorized":False,
        "external_network_calls":0,
        "monthly_recurring_infrastructure_inr":0,
    }
