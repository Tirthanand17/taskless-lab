"""Phase 3R1: three-voice OFFLINE PILOT intake; never a voice endorsement.

Only accepts supplied local WAV samples and local rights-document hashes for
the exactly authored FlowMinute CSV episodes. This is a bounded screening
contract, not a speech classifier or an authenticated rights/legal signoff.

* No network/model downloads, external login, audio creation or cloud upload.
* Model and voice assets must be pinned and inspected by an authorized operator
  outside this module. Pickle/PyTorch .pth deserialization is NOT permitted.
* Distinct bytes/narrator labels do NOT establish audibly distinct speakers.
* Even a structurally complete packet NEVER authorizes production/publishing.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import re
from typing import Sequence

from .agent_org import WorkflowError
from .phase2r3_authored_pack_audit import SECTIONS, SOURCE, TIME, _sections
from .phase3_voice_subtitle_handoff import (
    inspect_external_voice_wav,
    build_subtitles_from_authored_csv,
)

HEX = re.compile(r"[a-f0-9]{64}\Z")
REV = re.compile(r"[a-f0-9]{40}\Z")
MAX_DOC_BYTES=200_000
SAMPLE_MAX_SECONDS=8.0
ALLOWED_MODEL_LABEL="hexgrad/Kokoro-82M"
ALLOWED_LICENSES=frozenset(("Apache-2.0","CC-BY-4.0","owned-recording-contract"))
EXPECTED={
    ep:{"language":lang,"narrator_id":voice,"kind":kind}
    for kind,lang,ep,voice,_,_ in SECTIONS
}


@dataclass(frozen=True)
class VoiceSample:
    episode_id: str
    narrator_id: str
    language: str
    wav_path: Path
    expected_seconds: float
    wav_sha256: str
    bound_text_sha256: str
    source_kind: str                  # owned_recording | offline_tts
    claimed_license_spdx: str
    rights_document_path: Path
    rights_document_sha256: str
    commercial_use_claimed: bool
    adaptations_allowed_claimed: bool
    attribution_prepared: bool
    # A non-consensual model may still claim consent, so approval is external.
    consent_claimed: bool
    model_label: str = ""
    model_git_revision: str = ""
    model_weights_sha256: str = ""
    voice_style_sha256: str = ""
    model_artifact_format: str = ""    # safetensors only for controlled pilot


def _digest_local_file(path: Path, *, ceiling: int) -> str:
    if (not isinstance(path,Path) or path.is_symlink() or not path.is_file()
            or not 0<path.stat().st_size<=ceiling):
        raise WorkflowError("Safe, existing bounded local evidence file required")
    result=sha256()
    with path.open("rb") as stream:
        for data in iter(lambda:stream.read(1_048_576),b""):
            result.update(data)
    return result.hexdigest()


def _first_authored_utterance_hash(episode_id: str) -> str:
    if episode_id not in EXPECTED:
        raise WorkflowError("Unknown authored episode")
    sections=_sections(SOURCE.read_text(encoding="utf-8"))
    index=next(i for i,row in enumerate(SECTIONS) if row[2]==episode_id)
    utterances=TIME.findall(sections[index])
    if not utterances:
        raise WorkflowError("Original source screenplay has no text")
    return sha256(utterances[0][4].encode("utf-8")).hexdigest()


def review_offline_voice_pilot(
    samples: Sequence[VoiceSample], *, now: datetime,
) -> dict:
    """Validate *three* distinct sample files / declarations, no autoapproval.

    Caller declarations and local rights docs may be fabricated. A WAV can be a
    synthetic tone. Asset hashes bind bytes, not identity, safety or consent.
    """
    if (not isinstance(now,datetime) or now.tzinfo is None
            or now.utcoffset() is None):
        raise WorkflowError("Timezone-aware evaluation clock required")
    if not isinstance(samples,(tuple,list)) or len(samples)!=3:
        raise WorkflowError("Exactly 3 pilot voice sample records required")
    results=[]
    seen=set()
    audio_hashes=set()
    subtitle_plan=build_subtitles_from_authored_csv()
    for sample in samples:
        if not isinstance(sample,VoiceSample):
            raise WorkflowError("Typed three-video voice sample required")
        if sample.episode_id not in EXPECTED or sample.episode_id in seen:
            raise WorkflowError("Unexpected or duplicate authored episode")
        target=EXPECTED[sample.episode_id]
        if (sample.narrator_id!=target["narrator_id"]
                or sample.language!=target["language"]
                or sample.bound_text_sha256!=_first_authored_utterance_hash(sample.episode_id)):
            raise WorkflowError("Narrator/locale/sample script digest not bound to original screenplay")
        if (type(sample.expected_seconds) not in (float,int)
                or not 0.5<=sample.expected_seconds<=SAMPLE_MAX_SECONDS
                or not isinstance(sample.wav_sha256,str)
                or not HEX.fullmatch(sample.wav_sha256)):
            raise WorkflowError("Invalid bounded pilot sound duration/hash")
        if (sample.claimed_license_spdx not in ALLOWED_LICENSES
                or sample.claimed_license_spdx in ("CC-BY-NC-4.0","CC-BY-NC-SA-4.0")
                or type(sample.commercial_use_claimed) is not bool
                or sample.commercial_use_claimed is not True
                or type(sample.adaptations_allowed_claimed) is not bool
                or sample.adaptations_allowed_claimed is not True
                or type(sample.attribution_prepared) is not bool
                or sample.attribution_prepared is not True
                or type(sample.consent_claimed) is not bool):
            raise WorkflowError("Commercial rights, adaptation or attribution declaration invalid")
        if sample.source_kind=="owned_recording":
            if (sample.claimed_license_spdx!="owned-recording-contract"
                    or sample.consent_claimed is not True
                    or any((sample.model_label,sample.model_git_revision,
                            sample.model_weights_sha256,sample.voice_style_sha256,
                            sample.model_artifact_format))):
                raise WorkflowError("Owned speech must have declared consent and no unexplained model weights")
        elif sample.source_kind=="offline_tts":
            if (sample.model_label!=ALLOWED_MODEL_LABEL
                    or not REV.fullmatch(sample.model_git_revision)
                    or sample.claimed_license_spdx!="Apache-2.0"
                    or sample.model_artifact_format!="safetensors"
                    or not HEX.fullmatch(sample.model_weights_sha256)
                    or not HEX.fullmatch(sample.voice_style_sha256)):
                raise WorkflowError("Unpinned, noncommercial or unsafe serialized TTS model blocked")
        else:
            raise WorkflowError("Unknown audio source category; no cloud TTS providers")
        if (not isinstance(sample.rights_document_sha256,str)
                or not HEX.fullmatch(sample.rights_document_sha256)
                or _digest_local_file(sample.rights_document_path,ceiling=MAX_DOC_BYTES)
                !=sample.rights_document_sha256):
            raise WorkflowError("Local license/rights evidence is missing, changed or oversized")
        technical=inspect_external_voice_wav(
            sample.wav_path,episode_id=sample.episode_id,
            expected_seconds=sample.expected_seconds,
            declared_narrator_id=sample.narrator_id,
            declared_language=sample.language)
        if technical["sha256"] != sample.wav_sha256:
            raise WorkflowError("Pilot WAV bytes differ from submitted digest")
        if technical["sha256"] in audio_hashes:
            raise WorkflowError("Identical WAV bytes reused across episodes")
        seen.add(sample.episode_id)
        audio_hashes.add(technical["sha256"])
        results.append({
            "episode_id":sample.episode_id,
            "language":sample.language,
            "narrator_plan_id":sample.narrator_id,
            "source_kind":sample.source_kind,
            "clip_sha256":technical["sha256"],
            "duration_seconds":technical["duration_seconds"],
            "draft_srt_sha256":subtitle_plan[sample.episode_id]["srt_sha256"],
            "wav_technical_screen_passed":True,
            "claimed_rights_doc_hash_matched":True,
            "natural_speech_authenticated":False,
            "speaker_distinctness_audibly_verified":False,
        })
    if seen!=set(EXPECTED):
        raise WorkflowError("Full three-video voice pilot set required")
    results.sort(key=lambda x:x["episode_id"])
    return {
        "status":"THREE_VOICE_SAMPLES_TECHNICALLY_BOUND_UNVERIFIED",
        "episodes":results,
        "raw_voices_logged":False,
        "model_weights_downloaded":False,
        "model_deserialization_performed":False,
        "audio_provider_connected":False,
        "independent_human_listening_verified":False,
        "hindi_pronunciation_verified":False,
        "audio_speech_recognition_verified":False,
        "captions_word_aligned_to_speech":False,
        "license_legality_authenticated":False,
        "human_speaker_consent_authenticated":False,
        "real_three_video_batch_approved":False,
        "youtube_upload_authorized":False,
        "publishing_authorized":False,
        "network_calls":0,
        "spend_inr":0,
    }
