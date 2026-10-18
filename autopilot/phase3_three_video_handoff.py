"""Phase 3R3/3R4: whole-episode AV/subtitle handoff integrity gate.

Binds the actual, pre-existing silent original HD MP4 for each 42s/42s/432s
episode to its separately admitted WAV and candidate SRT. No media encoding,
subtitle burn-in, rights attestation, source approval or YouTube interaction.

The input receipts and candidate timestamps are UNSIGNED and UNVERIFIED
claims. Even a successful THREE_VIDEO_TECHNICAL_HANDOFF_ONLY status never
authorizes a mux, upload, schedule or public release. No network or writes.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Sequence

from .agent_org import WorkflowError
from .phase2r3_audience_language_lanes import prepare_audience_language_lanes
from .phase3_complete_narration_intake import (
    CompleteNarrationTake, EPISODES, review_complete_narration_takes,
)
from .phase3_caption_candidate_intake import (
    CandidateCaption, review_candidate_caption,
)
from .phase3_quarantined_video_receipt import (
    MAX_RECEIPT_BYTES, verify_quarantined_receipt, _hash_file,
)
from .phase3_visual_signal_audit import EPISODES as VISUAL_EPISODES, MAX_MEDIA_BYTES

VERSION = "flowminute-untrusted-three-episode-handoff-v1"
MAX_PATHS = 20


@dataclass(frozen=True)
class TechnicalHandoffInput:
    """Paths stay private to a permitted caller's local/cloud scratch workspace."""
    episode_id: str
    silent_video_path: Path
    video_receipt: dict
    narration_take: CompleteNarrationTake
    caption_candidate: CandidateCaption
    future_mux_path: Path


def _plain_existing(path: Path, suffix: str) -> Path:
    if (not isinstance(path, Path) or path.suffix.lower() != suffix
            or path.is_symlink() or not path.is_file()):
        raise WorkflowError("Ordinary original media input required")
    return path


def _future_target(path: Path) -> Path:
    """An uncreated, local, non-symlink future output; never create it."""
    if (not isinstance(path, Path) or path.suffix.lower() != ".mp4"
            or path.is_symlink() or path.exists()
            or not path.parent.is_dir() or path.parent.is_symlink()):
        raise WorkflowError("Fresh output in existing ordinary local folder required")
    return path


def _absolute_key(path: Path) -> str:
    if not isinstance(path, Path):
        raise WorkflowError("Only local pathlib paths permitted")
    return str(path.resolve(strict=False))


def _canonical_bytes(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",",":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def prepare_three_video_technical_handoff(
    entries: Sequence[TechnicalHandoffInput],
) -> dict:
    """Reinspect all three original video/audio/SRT inputs, return hashes only.

    Fails as a unit and never makes or modifies any output file.
    No path, voice, text, private legal document or model weight in the report.
    """
    if (not isinstance(entries, (tuple, list)) or len(entries) != 3
            or any(not isinstance(e, TechnicalHandoffInput) for e in entries)
            or {e.episode_id for e in entries} != set(EPISODES)):
        raise WorkflowError("Exactly one of each existing Hindi/English episode")
    if set(VISUAL_EPISODES) != set(EPISODES):
        raise WorkflowError("Mismatch in original video and narration catalog")
    specs = {e["episode_id"]: e for e in
             prepare_audience_language_lanes()["episodes"]}
    if set(specs) != set(EPISODES):
        raise WorkflowError("Audience-specific episode catalog drift")

    # Preflight all source/claim/target paths *before* any expensive reads.
    # Refuse path aliasing across all sources, even when different filenames.
    used = set()
    for entry in entries:
        take, cap = entry.narration_take, entry.caption_candidate
        if (not isinstance(take, CompleteNarrationTake)
                or not isinstance(cap, CandidateCaption)
                or take.episode_id != entry.episode_id
                or cap.episode_id != entry.episode_id):
            raise WorkflowError("Wrong episode for narration or candidate SRT")
        paths = (
            _plain_existing(entry.silent_video_path, ".mp4"),
            _plain_existing(take.wav_path, ".wav"),
            _plain_existing(take.rights_document_path,
                            take.rights_document_path.suffix.lower()),
            _plain_existing(cap.srt_path, ".srt"),
            _future_target(entry.future_mux_path),
        )
        for path in paths:
            identity = _absolute_key(path)
            if identity in used:
                raise WorkflowError("Source/output path reused across episodes")
            used.add(identity)
    if len(used) != 15 or len(used) > MAX_PATHS:
        raise WorkflowError("Incorrect isolated three-video source inventory")

    # Re-check actual WAV bytes and claimant rights documents, rejecting
    # forged clearance flags. This does not authenticate real commercial rights.
    takes = tuple(entry.narration_take for entry in entries)
    wav_report = review_complete_narration_takes(takes)
    if (wav_report.get("publishing_authorized") is not False
            or wav_report.get("three_licensed_human_sounding_voices_verified") is not False
            or wav_report.get("human_language_or_legal_review_verified") is not False
            or wav_report.get("complete_takes_received") != 3):
        raise WorkflowError("Untrusted WAV validator asserted release authority")
    wav_receipts = {r["episode_id"]:r for r in wav_report["episodes"]}
    if set(wav_receipts) != set(EPISODES):
        raise WorkflowError("Incomplete complete-take receipts")

    results=[]
    for item in entries:
        ep=item.episode_id
        video_receipt=item.video_receipt
        if (not isinstance(video_receipt,dict)
                or len(_canonical_bytes(video_receipt)) > MAX_RECEIPT_BYTES):
            raise WorkflowError("Missing or excessive video receipt")
        # Actual-source digest is independently re-read here, in addition to
        # upstream verify_quarantined_receipt's script/lane checks.
        actual_video_sha = _hash_file(item.silent_video_path, MAX_MEDIA_BYTES)
        checked = verify_quarantined_receipt(
            receipt=video_receipt, episode_id=ep,
            mp4=item.silent_video_path)
        if (checked.get("publishing_authorized") is not False
                or checked.get("video_sha256") != actual_video_sha
                or video_receipt.get("video_sha256") != actual_video_sha
                or video_receipt.get("media_has_narration") is not False
                or video_receipt.get("receipt_issuer_authenticated") is not False):
            raise WorkflowError("Forged or mismatched silent-video QA receipt")
        duration,width,height,fps,frames=VISUAL_EPISODES[ep]
        if (video_receipt.get("video_duration_seconds") != duration
                or video_receipt.get("video_width") != width
                or video_receipt.get("video_height") != height
                or video_receipt.get("video_frame_rate") != fps
                or video_receipt.get("video_frame_count") != frames):
            raise WorkflowError("A real full-resolution full-duration original video is required")
        voice=wav_receipts[ep]
        sub=review_candidate_caption(item.caption_candidate,voice)
        if (sub.get("publishing_authorized") is not False
                or sub.get("true_speech_to_caption_alignment_verified") is not False
                or sub.get("ready_for_mux") is not False
                or sub.get("srt_sha256") != item.caption_candidate.srt_sha256
                or sub.get("wav_sha256") != item.narration_take.wav_sha256):
            raise WorkflowError("Subtitle candidate falsely promoted or mismatched")

        lane=specs[ep]
        if (lane["original_spoken_language"] != item.narration_take.declared_language
                or lane["narrator_plan_id"] != item.narration_take.declared_narrator_id
                or sub.get("language_declared") != lane["original_spoken_language"]
                or sub.get("narrator_plan_id") != lane["narrator_plan_id"]
                or video_receipt.get("original_language_intended") != lane["original_spoken_language"]
                or video_receipt.get("narrator_plan_id") != lane["narrator_plan_id"]):
            raise WorkflowError("Cross-language Short/long subtitle or narrator mix")
        results.append({
            "episode_id":ep,
            "intended_language":lane["original_spoken_language"],
            "narrator_plan_id":lane["narrator_plan_id"],
            "duration_seconds_expected":duration,
            "silent_video_sha256":actual_video_sha,
            "wav_sha256":item.narration_take.wav_sha256,
            "candidate_srt_sha256":item.caption_candidate.srt_sha256,
            "source_original_spoken_sha256":sub["source_script_sha256"],
            "signed_source_or_editorial_attestation_available":False,
            "audibly_distinct_voices_verified":False,
            "actual_speech_timing_verified":False,
            "license_or_voice_consent_authenticated":False,
            "mux_permitted":False,
            "upload_permitted":False,
            "publishing_authorized":False,
        })
    results.sort(key=lambda x:x["episode_id"])
    if len(results)!=3 or {x["intended_language"] for x in results
                           if x["episode_id"].startswith("csv_tutorial_short")} != {"hi","en"}:
        raise WorkflowError("Native two-language Short separation violated")
    digest=sha256(_canonical_bytes({
        "version":VERSION,"episodes":results
    })).hexdigest()
    return {
        "status":"THREE_VIDEO_TECHNICAL_HANDOFF_ONLY_RELEASE_BLOCKED",
        "format_version":VERSION,
        "episodes":results,
        "source_bundle_sha256":digest,
        "all_three_media_paths_checked":True,
        "all_silent_video_receipts_revalidated":True,
        "all_narration_takes_technically_rescreened":True,
        "all_candidate_srt_cues_structurally_screened":True,
        "actual_voice_speech_language_verified":False,
        "actual_word_audio_alignment_verified":False,
        "professional_visual_or_factual_quality_verified":False,
        "legal_rights_authenticated":False,
        "final_mux_generated":False,
        "any_durable_cloud_media_stored":False,
        "youtube_upload_or_publishing_authorized":False,
        "network_calls":0,
        "files_written":0,
    }
