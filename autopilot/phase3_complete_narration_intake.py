"""Phase 3R1: three complete language-specific narration WAV take preflight.

Offline intake ONLY. Matches each entire 42s/42s/432s planned recording to
the exact original English/Hindi episode, intended narrator identity, and
declared license-file bytes. Checks PCM WAV format, actual duration and audio
energy via existing technical inspector.

IMPORTANT: WAV bytes, licenses and narrator labels are all caller-provided.
No classifier, listening judge, ASR, signature or legal reviewer verifies actual
speech, speaker identity, consent, commercial rights, or subtitle word timing.
Synthetic sine tones can pass technical PCM checks; they are NOT voices.
This module must never authorize mux, upload, public release or publishing.
No network/models/providers, media creation or file writes.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
from typing import Sequence

from .agent_org import WorkflowError
from .phase2r3_audience_language_lanes import prepare_audience_language_lanes
from .phase3_voice_subtitle_handoff import inspect_external_voice_wav

EPISODES={
    "csv_tutorial_short_hi":42,
    "csv_tutorial_short_en":42,
    "csv_tutorial_long_hi":432,
}
HEX=re.compile(r"[0-9a-f]{64}\Z")
MAX_RIGHTS_BYTES=200_000
ACCEPTED_SOURCES=frozenset(("owned_recording","offline_tts"))
SOURCE_RIGHTS={
    "owned_recording":"owned-recording-contract",
    "offline_tts":"Apache-2.0",
}


@dataclass(frozen=True)
class CompleteNarrationTake:
    episode_id:str
    wav_path:Path
    wav_sha256:str
    declared_language:str
    declared_narrator_id:str
    source_kind:str
    claimed_license_spdx:str
    rights_document_path:Path
    rights_document_sha256:str
    commercial_use_claimed:bool
    adaptation_allowed_claimed:bool
    attribution_prepared:bool
    speaker_consent_claimed:bool
    # Metadata-only declared model references; they cannot establish rights,
    # provenance or verify which engine generated the audio.
    offline_model_sha256:str=""


def _hash_existing(path:Path,limit:int)->str:
    if (not isinstance(path,Path) or path.is_symlink()
            or not path.is_file() or not 0<path.stat().st_size<=limit):
        raise WorkflowError("Untrusted, missing or oversized local evidence")
    value=sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1_048_576),b""):
            value.update(chunk)
    return value.hexdigest()


def review_complete_narration_takes(takes:Sequence[CompleteNarrationTake])->dict:
    """Inspect ALL three full WAV takes as untrusted technical evidence.

    No real WAVs or signed human rights record exist in the repository; this
    function is a validator waiting for separately authorized supplied assets.
    """
    if not isinstance(takes,(tuple,list)) or len(takes)!=3:
        raise WorkflowError("Require exactly Hindi/English Shorts and Hindi long WAV")
    planned=prepare_audience_language_lanes()["episodes"]
    lanes={x["episode_id"]:x for x in planned}
    if set(lanes)!=set(EPISODES):
        raise WorkflowError("Original three-video audience plan changed")
    seen=set()
    digests=set()
    narrator_labels=set()
    receipts=[]
    for take in takes:
        if not isinstance(take,CompleteNarrationTake):
            raise WorkflowError("Typed complete take required")
        ep=take.episode_id
        if ep not in lanes or ep in seen:
            raise WorkflowError("Unknown or repeated full narration episode")
        lane=lanes[ep]
        if (take.declared_language!=lane["original_spoken_language"]
                or take.declared_narrator_id!=lane["narrator_plan_id"]):
            raise WorkflowError("Wrong narrator or language for the original episode")
        if take.declared_narrator_id in narrator_labels:
            raise WorkflowError("Same narrator label reused across episodes")
        if not isinstance(take.wav_sha256,str) or not HEX.fullmatch(take.wav_sha256):
            raise WorkflowError("Invalid declared complete WAV digest")
        if take.source_kind not in ACCEPTED_SOURCES or (
            take.claimed_license_spdx!=SOURCE_RIGHTS[take.source_kind]
        ):
            raise WorkflowError("Unsupported declared provenance/license combination")
        for claim in (
            take.commercial_use_claimed,take.adaptation_allowed_claimed,
            take.attribution_prepared,
        ):
            if claim is not True:
                raise WorkflowError("Commercial reuse and attribution declaration missing")
        if type(take.speaker_consent_claimed) is not bool:
            raise WorkflowError("Speaker consent declaration must be Boolean")
        if take.source_kind=="owned_recording":
            if take.speaker_consent_claimed is not True or take.offline_model_sha256:
                raise WorkflowError("Owned human voice requires declared consent and no model")
        else:
            if not HEX.fullmatch(take.offline_model_sha256):
                raise WorkflowError("Offline voice requires a pinned model-byte declaration")
        if (not isinstance(take.rights_document_sha256,str)
                or not HEX.fullmatch(take.rights_document_sha256)
                or _hash_existing(take.rights_document_path,MAX_RIGHTS_BYTES)
                !=take.rights_document_sha256):
            raise WorkflowError("Rights evidence file missing or changed")
        inspected=inspect_external_voice_wav(
            take.wav_path,
            episode_id=ep,
            expected_seconds=EPISODES[ep],
            declared_narrator_id=take.declared_narrator_id,
            declared_language=take.declared_language,
        )
        if inspected["sha256"]!=take.wav_sha256 or (
            inspected["duration_seconds"] < EPISODES[ep]-1.5
            or inspected["duration_seconds"] > EPISODES[ep]+1.5
        ):
            raise WorkflowError("Full take WAV duration/digest mismatch")
        if inspected["sha256"] in digests:
            raise WorkflowError("Identical WAV bytes cannot be assigned to multiple voices")
        if inspected["real_speech_verified"] or inspected["license_rights_verified"]:
            raise WorkflowError("Low-level WAV preflight must never claim voice approval")
        seen.add(ep)
        digests.add(inspected["sha256"])
        narrator_labels.add(take.declared_narrator_id)
        receipts.append({
            "episode_id":ep,
            "original_language_declared":take.declared_language,
            "intended_narrator_id":take.declared_narrator_id,
            "source_kind_claimed":take.source_kind,
            "clip_sha256":inspected["sha256"],
            "duration_seconds":inspected["duration_seconds"],
            "technical_wav_screen_passed":True,
            "rights_document_hash_matched":True,
            "draft_srt_sha256":lane["draft_srt_sha256"],
            "audio_content_recognized_as_speech":False,
            "voice_naturalness_verified":False,
            "speaker_distinctness_audibly_verified":False,
            "native_language_pronunciation_verified":False,
            "commercial_voice_rights_legally_verified":False,
            "human_consent_authenticated":False,
            "spoken_subtitles_word_aligned":False,
            "approved_for_audio_mux":False,
            "publishing_authorized":False,
        })
    if seen!=set(EPISODES):
        raise WorkflowError("Three full narration WAV recordings not complete")
    receipts.sort(key=lambda x:x["episode_id"])
    return {
        "status":"COMPLETE_AUDIO_WAV_TECHNICAL_SCREEN_ONLY_VOICES_UNVERIFIED",
        "episodes":receipts,
        "complete_takes_received":len(receipts),
        "distinct_audio_byte_hashes":len(digests),
        "three_licensed_human_sounding_voices_verified":False,
        "two_distinct_short_narrators_audibly_verified":False,
        "human_language_or_legal_review_verified":False,
        "real_audio_caption_alignment_verified":False,
        "external_provenance_authenticated":False,
        "public_or_private_upload_authorized":False,
        "any_video_ready_for_publication":False,
        "publishing_authorized":False,
        "provider_or_model_download_performed":False,
        "cloud_media_artifacts_stored":False,
        "network_calls":0,
    }
