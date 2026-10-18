"""FlowMinute Phase 3: SOURCE-BOUND, QUARANTINED video receipt.

Given an ACTUAL already-rendered silent MP4, recheck its decoded video
samples and bind its file digest to the current authored episode text and the
script-derived (NOT speech-aligned) SRT digest.

This is a *local integrity receipt*, not a signed, authenticated,
human-reviewed or legally approved production deliverable. All fields that
could imply external voice consent, source accuracy or publishing stay FALSE.
No networking, uploads, media persistence, account connection or new charges.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from .agent_org import WorkflowError
from .phase2r3_authored_pack_audit import SOURCE, SECTIONS, _sections
from .phase3_visual_signal_audit import (
    EPISODES, MAX_MEDIA_BYTES, inspect_authored_visual_signal,
)
from .phase3_voice_subtitle_handoff import build_subtitles_from_authored_csv

VERSION="flowminute-quarantine-video-receipt-v1"
MAX_SCRIPT_BYTES=50_000
MAX_RECEIPT_BYTES=10_000
EPISODE_SECTION_INDEX={item[2]:i for i,item in enumerate(SECTIONS)}
EXPECTED_SAMPLES={
    "csv_tutorial_short_en":5,
    "csv_tutorial_short_hi":5,
    "csv_tutorial_long_hi":26,
}


def _hash_file(path:Path,limit:int) -> str:
    if not isinstance(path,Path) or path.is_symlink() or not path.is_file():
        raise WorkflowError("Existing ordinary source file required")
    if not 0 < path.stat().st_size<=limit:
        raise WorkflowError("Unbounded or empty local evidence file")
    digest=sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda:file.read(1_048_576),b""):
            digest.update(chunk)
    return digest.hexdigest()


def _bound_script(episode_id:str)->tuple[str,str]:
    if episode_id not in EPISODE_SECTION_INDEX:
        raise WorkflowError("Episode not in authored screenplay")
    _hash_file(SOURCE,MAX_SCRIPT_BYTES)
    text=SOURCE.read_text(encoding="utf-8")
    section=_sections(text)[EPISODE_SECTION_INDEX[episode_id]]
    if not 100<=len(section)<=MAX_SCRIPT_BYTES:
        raise WorkflowError("Source section length changed")
    return sha256(section.encode("utf-8")).hexdigest(),sha256(text.encode("utf-8")).hexdigest()


def _current_srt_digest(episode_id:str)->str:
    if episode_id not in EPISODES:
        raise WorkflowError("Unknown authored video")
    meta=build_subtitles_from_authored_csv()[episode_id]
    checksum=meta["srt_sha256"]
    if not isinstance(checksum,str) or len(checksum)!=64:
        raise WorkflowError("Script-derived captions missing checksum")
    return checksum


def _canonical_bytes(obj:dict)->bytes:
    return json.dumps(obj,sort_keys=True,ensure_ascii=True,
                      separators=(",",":"),allow_nan=False).encode("utf-8")


def create_quarantined_video_receipt(*, episode_id:str,mp4:Path)->dict:
    """Bind actual silent media and actual video pixel QA to draft script.

    The call performs local FFprobe/FFmpeg frame sampling, but no persistence
    or publication. Caller must delete the media after this technical receipt.
    """
    if episode_id not in EPISODES or episode_id not in EXPECTED_SAMPLES:
        raise WorkflowError("Only three authored original videos supported")
    file=Path(mp4)
    video_sha=_hash_file(file,MAX_MEDIA_BYTES)
    signal=inspect_authored_visual_signal(episode_id=episode_id,path=file)
    if signal["status"]!="VISUAL_SIGNAL_QA_PASS_UNPUBLISHABLE":
        raise WorkflowError("Quarantined video has visual QA issues: "+
                            ",".join(signal["issues"]))
    if signal["visual_signal"]["sample_count"]!=EXPECTED_SAMPLES[episode_id]:
        raise WorkflowError("Incorrect authored visual sample coverage")
    if signal["publishing_authorized"]:
        raise WorkflowError("Media sampling must never authorize publishing")
    script_section_sha,script_document_sha=_bound_script(episode_id)
    duration,width,height,fps,frames=EPISODES[episode_id]
    pixel=signal["visual_signal"]
    record={
        "format_version":VERSION,
        "status":"QUARANTINED_SILENT_VIDEO_TECHNICAL_QA_ONLY",
        "episode_id":episode_id,
        "video_sha256":video_sha,
        "video_size_bytes":file.stat().st_size,
        "authored_script_section_sha256":script_section_sha,
        "authored_script_document_sha256":script_document_sha,
        "estimated_srt_sha256":_current_srt_digest(episode_id),
        "estimated_subtitles_are_speech_aligned":False,
        "video_width":width,"video_height":height,
        "video_duration_seconds":duration,
        "video_frame_rate":fps,"video_frame_count":frames,
        "actual_video_pixel_samples":EXPECTED_SAMPLES[episode_id],
        "actual_visual_signal_gate":"PASS_WITHOUT_EDITORIAL_APPROVAL",
        "minimum_adjacent_scene_rgb_change":min(
            pixel["adjacent_mean_absolute_rgb_change"]),
        "maximum_nearblack_sample_fraction":max(pixel["nearblack_fraction"]),
        "all_sample_frame_hashes_sha256":sha256(
            _canonical_bytes(pixel["sample_sha256"])).hexdigest(),
        "media_has_narration":False,
        "narrator_identity_authenticated":False,
        "two_distinct_short_voices_authenticated":False,
        "third_party_rights_authenticated":False,
        "spoken_subtitle_alignment_authenticated":False,
        "fact_editorial_approval_authenticated":False,
        "human_visual_editorial_approval_authenticated":False,
        "production_media_storage_verified":False,
        "cloud_publication_authorized":False,
        "youtube_upload_authorized":False,
        "publishing_authorized":False,
        "receipt_issuer_authenticated":False,
        "receipt_cryptographically_signed":False,
        "network_calls":0,
        "additional_paid_services_connected":False,
    }
    sealed=_canonical_bytes(record)
    if len(sealed)>MAX_RECEIPT_BYTES:
        raise WorkflowError("Oversized compact media evidence")
    record["receipt_integrity_sha256"]=sha256(sealed).hexdigest()
    return record


def verify_quarantined_receipt(*,receipt:dict,episode_id:str,mp4:Path)->dict:
    """Detect accidental local tampering, NEVER issue production authority.

    No key or trusted hardware signs this receipt. A malicious caller can
    recompute SHA-256; verification proves only local byte consistency.
    """
    if not isinstance(receipt,dict) or episode_id not in EPISODES:
        raise WorkflowError("Typed episode/media integrity receipt required")
    needed={
        "format_version","status","episode_id","video_sha256",
        "video_size_bytes","authored_script_section_sha256",
        "authored_script_document_sha256","estimated_srt_sha256",
        "receipt_integrity_sha256","publishing_authorized",
    }
    if not needed.issubset(receipt):
        raise WorkflowError("Incomplete video receipt")
    if receipt["format_version"]!=VERSION or receipt["episode_id"]!=episode_id:
        raise WorkflowError("Wrong receipt format or episode")
    if receipt["status"]!="QUARANTINED_SILENT_VIDEO_TECHNICAL_QA_ONLY":
        raise WorkflowError("Wrong unprivileged receipt status")
    if receipt["publishing_authorized"] is not False:
        raise WorkflowError("Unapproved media may never imply release")
    digest=receipt["receipt_integrity_sha256"]
    bare={k:v for k,v in receipt.items() if k!="receipt_integrity_sha256"}
    if not isinstance(digest,str) or len(digest)!=64 or sha256(_canonical_bytes(bare)).hexdigest()!=digest:
        raise WorkflowError("Local receipt field integrity mismatch")
    for flag in (
        "estimated_subtitles_are_speech_aligned",
        "media_has_narration","narrator_identity_authenticated",
        "two_distinct_short_voices_authenticated",
        "third_party_rights_authenticated",
        "spoken_subtitle_alignment_authenticated",
        "fact_editorial_approval_authenticated",
        "human_visual_editorial_approval_authenticated",
        "production_media_storage_verified","cloud_publication_authorized",
        "youtube_upload_authorized","receipt_issuer_authenticated",
        "receipt_cryptographically_signed","additional_paid_services_connected",
    ):
        if receipt.get(flag) is not False:
            raise WorkflowError("A technical receipt cannot be upgraded to approval")
    if receipt.get("network_calls")!=0:
        raise WorkflowError("Unexpected external calls in local receipt")
    if receipt["video_sha256"]!=_hash_file(Path(mp4),MAX_MEDIA_BYTES):
        raise WorkflowError("Media bytes changed after visual inspection")
    if receipt["video_size_bytes"]!=Path(mp4).stat().st_size:
        raise WorkflowError("Media size changed after inspection")
    script,document=_bound_script(episode_id)
    if (receipt["authored_script_section_sha256"]!=script
            or receipt["authored_script_document_sha256"]!=document
            or receipt["estimated_srt_sha256"]!=_current_srt_digest(episode_id)):
        raise WorkflowError("Media receipt no longer matches original screenplay/captions")
    return {
        "status":"LOCAL_QUARANTINE_INTEGRITY_RECHECK_PASS_NOT_RELEASE_APPROVAL",
        "episode_id":episode_id,
        "receipt_integrity_sha256":digest,
        "video_sha256":receipt["video_sha256"],
        "signed_by_trusted_reviewer":False,
        "voice_or_rights_verified":False,
        "publishing_authorized":False,
    }
