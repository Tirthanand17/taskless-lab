"""Read-only, signed SHA-bound transcript *sidecar* inspection.

This stricter OPTIONAL path opens an existing bounded JSON sidecar named by
each detached Ed25519 reviewer claim. It verifies actual bytes against that
claim's signed evidence_sha256 and checks the sidecar's media, SRT, transcript,
identity and three sampled words/timestamps against the original evidence.

The sidecar is an UNTRUSTED CLAIM. Hashes and signatures cannot prove a
person listened to the audio, independently identified the speaker, verified
the language, or owns copyright. This module never certifies publishing.
"""
from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from typing import Mapping
import json
import os
import re
import stat

from .agent_org import WorkflowError
from .cloud_full_media_evidence import TechnicalFullHDObservation
from .cloud_muxed_audio_screen import MuxedAudioScreen
from .cloud_transcript_alignment_intake import CandidateWordTranscript
from .cloud_signed_transcript_reviews import (
    SignedTranscriptAttestation,TrustedTranscriptReviewer,ROLES,
    transcript_digest,verify_signed_transcript_attestations,
)

MAX_SIDECAR_BYTES=8192
SHA=re.compile(r"[0-9a-f]{64}\Z")
HEADER_KEYS=frozenset((
    "schema_version","scope","role","reviewer_id","lane","episode_id",
    "media_sha256","transcript_sha256","authored_srt_sha256",
    "claimed_method","observed_language_claim","word_anchors",
    "note","independent_real_world_listener_verified",
    "youtube_publishing_authorized",
))
ANCHOR_KEYS=frozenset(("index","text","start_ms","end_ms"))


def _unique_fields(pairs:list[tuple[str,object]])->dict:
    result={}
    for key,value in pairs:
        if key in result:
            raise WorkflowError("Duplicate transcript evidence JSON field")
        result[key]=value
    return result


def _not_constant(value:str):
    raise WorkflowError("Invalid non-finite transcript evidence value")


def _read_sidecar(path:Path)->tuple[bytes,dict]:
    path=Path(path)
    if not path.is_absolute() or path.is_symlink():
        raise WorkflowError("Existing absolute non-symlink review sidecar required")
    try:
        before=path.lstat()
        if (not stat.S_ISREG(before.st_mode)
                or not 64<=before.st_size<=MAX_SIDECAR_BYTES):
            raise WorkflowError("Sidecar is not a bounded ordinary file")
        # O_NOFOLLOW rejects a symlink swapped into place since lstat.
        flags=os.O_RDONLY|getattr(os,"O_CLOEXEC",0)|getattr(os,"O_NOFOLLOW",0)
        fd=os.open(path,flags)
        try:
            opened=os.fstat(fd)
            if (not stat.S_ISREG(opened.st_mode)
                    or (opened.st_dev,opened.st_ino,opened.st_size)!=(
                        before.st_dev,before.st_ino,before.st_size)):
                raise WorkflowError("Sidecar changed during secure opening")
            with os.fdopen(fd,"rb",closefd=False) as reader:
                raw=reader.read(MAX_SIDECAR_BYTES+1)
            after=os.fstat(fd)
        finally:
            os.close(fd)
        current=path.lstat()
        if (len(raw)!=before.st_size
                or (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)
                   !=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
                or (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)
                   !=(current.st_dev,current.st_ino,current.st_size,
                      current.st_mtime_ns)):
            raise WorkflowError("Sidecar changed during inspection")
        obj=json.loads(raw.decode("utf-8"),
                       object_pairs_hook=_unique_fields,
                       parse_constant=_not_constant)
    except (OSError,ValueError,UnicodeError,TypeError) as exc:
        raise WorkflowError("Cannot safely open signed review sidecar") from exc
    if not isinstance(obj,dict) or set(obj)!=HEADER_KEYS:
        raise WorkflowError("Missing or unknown transcript sidecar fields")
    return raw,obj


def _expected_anchor_indices(total:int)->tuple[int,int,int]:
    if type(total) is not int or total<3:
        raise WorkflowError("Too few timed words to anchor sidecar")
    return (0,total//2,total-1)


def _verify_one_sidecar(
    *,candidate:CandidateWordTranscript,
    claim,
    sidecar:Path,
)->dict:
    raw,obj=_read_sidecar(sidecar)
    digest=sha256(raw).hexdigest()
    if digest!=claim.evidence_sha256:
        raise WorkflowError("Sidecar bytes differ from signed reviewer digest")
    if (type(obj["schema_version"]) is not int or obj["schema_version"]!=1
            or obj["scope"]!="UNVERIFIED_ACOUSTIC_REVIEW_CLAIM"
            or obj["role"]!=claim.role or obj["reviewer_id"]!=claim.reviewer_id
            or obj["lane"]!=candidate.lane
            or obj["episode_id"]!=candidate.episode_id
            or obj["media_sha256"]!=candidate.media_sha256
            or obj["transcript_sha256"]!=transcript_digest(candidate)
            or obj["authored_srt_sha256"]!=candidate.authored_draft_srt_sha256
            or obj["claimed_method"] not in (
                "claimed_manual_listening","claimed_asr_review","synthetic_test"
            )
            or obj["observed_language_claim"]!=candidate.declared_language
            or obj["independent_real_world_listener_verified"] is not False
            or obj["youtube_publishing_authorized"] is not False
            or not isinstance(obj["note"],str)
            or not 35<=len(obj["note"])<=500):
        raise WorkflowError("Evidence sidecar has false, missing or mismatched scope")
    anchors=obj["word_anchors"]
    indices=_expected_anchor_indices(len(candidate.words))
    if not isinstance(anchors,list) or len(anchors)!=3:
        raise WorkflowError("Evidence sidecar needs three distinct word anchors")
    for index,anchor in zip(indices,anchors):
        word=candidate.words[index]
        if (not isinstance(anchor,dict) or set(anchor)!=ANCHOR_KEYS
                or type(anchor["index"]) is not int or anchor["index"]!=index
                or anchor["text"]!=word.text
                or type(anchor["start_ms"]) is not int
                or type(anchor["end_ms"]) is not int
                or anchor["start_ms"]!=word.start_ms
                or anchor["end_ms"]!=word.end_ms):
            raise WorkflowError("Evidence word anchor disagrees with signed transcript")
    return {
        "reviewer_id":claim.reviewer_id,
        "role":claim.role,
        "exact_signed_evidence_sha256":digest,
        "sampled_word_anchor_count":3,
        "source_media_sha256":candidate.media_sha256,
        "claim_method_not_authenticated":obj["claimed_method"],
        "actual_listening_or_asr_execution_verified":False,
    }


def verify_signed_acoustic_sidecars(
    *,candidate:CandidateWordTranscript,
    media:TechnicalFullHDObservation,
    audio_screen:MuxedAudioScreen,
    signed_attestations:tuple[SignedTranscriptAttestation,...],
    registry:Mapping[str,TrustedTranscriptReviewer],
    excluded_creator_publisher_ids:frozenset[str],
    evidence_files:Mapping[str,Path],
    now,
)->dict:
    """Additional positive SHA/file/anchor checks AFTER two-role signatures.

    Deliberately separate from original detached signature verifier and
    Phase 4 release ledger. Caller-provided paths never become permissions.
    """
    signature_report=verify_signed_transcript_attestations(
        candidate=candidate,media=media,audio_screen=audio_screen,
        signed_attestations=signed_attestations,registry=registry,
        excluded_creator_publisher_ids=excluded_creator_publisher_ids,now=now,
    )
    if signature_report["blocking_reasons"]:
        raise WorkflowError("Signed review roles or signature set rejected")
    if (not isinstance(evidence_files,Mapping)
            or type(signed_attestations) is not tuple
            or len(signed_attestations)!=2
            or set(evidence_files)!={
                entry.claim.reviewer_id for entry in signed_attestations
            }):
        raise WorkflowError("Every signed reviewer needs exactly one sidecar")
    evidence=[]
    for entry in signed_attestations:
        evidence.append(_verify_one_sidecar(
            candidate=candidate,claim=entry.claim,
            sidecar=evidence_files[entry.claim.reviewer_id],
        ))
    if {x["role"] for x in evidence}!=ROLES:
        raise WorkflowError("Sidecar roles cannot substitute for one another")
    return {
        "status":"EXACT_SIGNED_REVIEW_SIDECAR_BYTES_CHECKED_NOT_SPEECH_PROOF",
        "lane":candidate.lane,
        "media_sha256":media.video_sha256,
        "transcript_sha256":transcript_digest(candidate),
        "signed_sidecar_hashes":tuple(sorted(
            (entry["reviewer_id"],entry["exact_signed_evidence_sha256"])
            for entry in evidence
        )),
        "checked_anchor_count":sum(x["sampled_word_anchor_count"] for x in evidence),
        "signed_bytes_hash_match":True,
        "sidecar_text_and_timestamps_match":True,
        "reviewer_keys_separately_enrolled_in_supplied_registry":True,
        "registry_authority_externally_authenticated":False,
        "actual_listening_or_asr_execution_verified":False,
        "spoken_language_verified":False,
        "speech_caption_sync_verified":False,
        "real_world_reviewer_independence_verified":False,
        "voice_and_visual_rights_verified":False,
        "publishing_authorized":False,
        "youtube_upload_authorized":False,
        "monthly_recurring_infrastructure_inr":0,
    }
