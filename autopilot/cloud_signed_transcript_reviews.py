"""Detached Ed25519 attestation rehearsal for untrusted word transcripts.

The trusted public-key registry must be supplied by a separate authority.
Signatures bind exact candidate words/timings, source video SHA, draft SRT
and evidence digest. Requiring distinct transcriber and independent reviewer
cannot prove identities or actually listening to the audio; such trust is
OUT OF SCOPE. No keys, voices, network, upload or publishing actions here.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Mapping
import base64
import binascii
import json
import re

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .agent_org import WorkflowError
from .cloud_transcript_alignment_intake import (
    CandidateWordTranscript,validate_candidate_word_alignment,
)
from .cloud_full_media_evidence import TechnicalFullHDObservation
from .cloud_muxed_audio_screen import MuxedAudioScreen

HEX64=re.compile(r"[0-9a-f]{64}\Z")
SAFE_ID=re.compile(r"[a-z][a-z0-9_]{2,63}\Z")
ROLES=frozenset(("transcriber","independent_listener"))
DECISIONS=frozenset(("ACCEPT","REJECT"))
MAX_AGE=timedelta(hours=24)
MAX_VALIDITY=timedelta(hours=48)


@dataclass(frozen=True)
class TrustedTranscriptReviewer:
    reviewer_id:str
    key_id:str
    role:str
    ed25519_public_key_b64:str
    active:bool=True


@dataclass(frozen=True)
class TranscriptAttestationClaim:
    transcript_sha256:str
    lane:str
    episode_id:str
    media_sha256:str
    authored_srt_sha256:str
    reviewer_id:str
    key_id:str
    role:str
    decision:str
    assessed_at_utc:str
    expires_at_utc:str
    evidence_sha256:str
    review_notes:str
    receipt_id:str


@dataclass(frozen=True)
class SignedTranscriptAttestation:
    claim:TranscriptAttestationClaim
    signature_ed25519_b64:str


def transcript_digest(candidate:CandidateWordTranscript)->str:
    """Canonical digest of EVERY word and timestamp, never just summary."""
    if not isinstance(candidate,CandidateWordTranscript):
        raise WorkflowError("Typed candidate transcript required")
    try:
        payload=json.dumps(asdict(candidate),sort_keys=True,
                           ensure_ascii=False,separators=(",",":"),
                           allow_nan=False).encode("utf-8")
    except (TypeError,ValueError) as exc:
        raise WorkflowError("Malformed canonical candidate transcript") from exc
    if len(payload)>600_000:
        raise WorkflowError("Transcript evidence exceeds digest bound")
    return sha256(payload).hexdigest()


def _canonical(claim:TranscriptAttestationClaim)->bytes:
    return json.dumps(asdict(claim),sort_keys=True,ensure_ascii=False,
                      separators=(",",":"),allow_nan=False).encode("utf-8")


def _time(value:str)->datetime:
    if not isinstance(value,str) or len(value)>64:
        raise WorkflowError("Invalid transcript review time")
    try:
        parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
    except (ValueError,TypeError,OverflowError) as exc:
        raise WorkflowError("Malformed signed transcript review date") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise WorkflowError("Signed transcript review timestamp lacks timezone")
    return parsed.astimezone(timezone.utc)


def _reviewer_key(item:TrustedTranscriptReviewer)->Ed25519PublicKey:
    if (not isinstance(item,TrustedTranscriptReviewer)
            or not all(isinstance(x,str) and SAFE_ID.fullmatch(x)
                       for x in (item.reviewer_id,item.key_id))
            or item.role not in ROLES or item.active is not True):
        raise WorkflowError("Unknown or revoked external reviewer")
    try:
        raw=base64.b64decode(item.ed25519_public_key_b64,validate=True)
        if len(raw)!=32:
            raise WorkflowError("Invalid Ed25519 public-key size")
        return Ed25519PublicKey.from_public_bytes(raw)
    except (binascii.Error,TypeError,ValueError) as exc:
        raise WorkflowError("Untrusted Ed25519 public-key encoding") from exc


def verify_signed_transcript_attestations(
    *,candidate:CandidateWordTranscript,
    media:TechnicalFullHDObservation,
    audio_screen:MuxedAudioScreen,
    signed_attestations:tuple[SignedTranscriptAttestation,...],
    registry:Mapping[str,TrustedTranscriptReviewer],
    excluded_creator_publisher_ids:frozenset[str],
    now:datetime,
)->dict:
    """Verify two detached roles and exact text hash; never authorize release.

    A reviewer may truthfully or falsely say ACCEPT. A valid signature
    authenticates a key, not a real person, language or voice recording.
    """
    # Every claim must first match the current original author-subtitle and
    # the same separately probed/decoded MP4 and waveform hash.
    aligned=validate_candidate_word_alignment(candidate,media,audio_screen)
    digest=transcript_digest(candidate)
    if (not isinstance(registry,Mapping)
            or not isinstance(signed_attestations,tuple)
            or len(signed_attestations)>2
            or not isinstance(excluded_creator_publisher_ids,frozenset)
            or not excluded_creator_publisher_ids
            or not all(isinstance(x,str) and SAFE_ID.fullmatch(x)
                       for x in excluded_creator_publisher_ids)
            or not isinstance(now,datetime)
            or now.tzinfo is None or now.utcoffset() is None):
        raise WorkflowError("Invalid transcript signing trust boundary")
    at=now.astimezone(timezone.utc)
    ok_roles=set()
    ok_reviewers=set()
    seen_receipts=set()
    problems=[]
    for entry in signed_attestations:
        if (not isinstance(entry,SignedTranscriptAttestation)
                or not isinstance(entry.claim,TranscriptAttestationClaim)):
            problems.append("MALFORMED_TRANSCRIPT_ATTESTATION")
            continue
        claim=entry.claim
        if not isinstance(claim.receipt_id,str) or not SAFE_ID.fullmatch(claim.receipt_id):
            problems.append("INVALID_TRANSCRIPT_RECEIPT_ID")
            continue
        if claim.receipt_id in seen_receipts:
            problems.append("DUPLICATE_TRANSCRIPT_RECEIPT")
            continue
        seen_receipts.add(claim.receipt_id)
        if (claim.role in ok_roles or claim.reviewer_id in ok_reviewers):
            problems.append("TRANSCRIPT_REVIEWER_OR_ROLE_REUSED")
            continue
        if (claim.reviewer_id in excluded_creator_publisher_ids):
            problems.append("CREATOR_PUBLISHER_CANNOT_ATTEST_TRANSCRIPT")
            continue
        enrolled=registry.get(claim.reviewer_id)
        if (not isinstance(enrolled,TrustedTranscriptReviewer)
                or enrolled.reviewer_id!=claim.reviewer_id
                or enrolled.key_id!=claim.key_id
                or enrolled.role!=claim.role):
            problems.append("TRANSCRIPT_REVIEWER_NOT_ENROLLED_FOR_ROLE")
            continue
        try:
            key=_reviewer_key(enrolled)
            if (claim.transcript_sha256!=digest
                    or claim.lane!=candidate.lane
                    or claim.episode_id!=candidate.episode_id
                    or claim.media_sha256!=media.video_sha256
                    or claim.authored_srt_sha256!=candidate.authored_draft_srt_sha256
                    or claim.role not in ROLES
                    or claim.decision not in DECISIONS
                    or not isinstance(claim.evidence_sha256,str)
                    or HEX64.fullmatch(claim.evidence_sha256) is None
                    or not isinstance(claim.review_notes,str)
                    or not 30<=len(claim.review_notes.strip())<=1000):
                raise WorkflowError("Signed transcript review scope mismatch")
            created=_time(claim.assessed_at_utc)
            expires=_time(claim.expires_at_utc)
            if (not timedelta(0)<=at-created<=MAX_AGE
                    or not timedelta(0)<expires-created<=MAX_VALIDITY
                    or expires<=at):
                raise WorkflowError("Stale/future/replayed transcript attestations")
            signature=base64.b64decode(entry.signature_ed25519_b64,validate=True)
            if len(signature)!=64:
                raise WorkflowError("Invalid transcript signature size")
            key.verify(signature,_canonical(claim))
        except (WorkflowError,InvalidSignature,binascii.Error,
                ValueError,TypeError,OverflowError):
            problems.append("INVALID_OR_STALE_TRANSCRIPT_SIGNATURE")
            continue
        if claim.decision=="REJECT":
            problems.append("INDEPENDENT_TRANSCRIPT_REVIEW_REJECTED")
            continue
        ok_roles.add(claim.role)
        ok_reviewers.add(claim.reviewer_id)
    if ok_roles!=ROLES:
        problems.append("TRANSCRIBER_AND_INDEPENDENT_LISTENER_REQUIRED")
    if len(ok_reviewers)!=2:
        problems.append("TWO_DISTINCT_TRANSCRIPT_REVIEWERS_REQUIRED")
    problems=tuple(sorted(set(problems)))
    return {
        "status":("SIGNED_TRANSCRIPT_RECORDS_AWAITING_REAL_WORLD_VERIFICATION"
                  if not problems else "SIGNED_TRANSCRIPT_EVIDENCE_BLOCKED"),
        "blocking_reasons":problems,
        "candidate_transcript_sha256":digest,
        "media_sha256":aligned["media_sha256"],
        "draft_srt_sha256":aligned["draft_srt_sha256"],
        "valid_roles":tuple(sorted(ok_roles)),
        "valid_reviewer_ids":tuple(sorted(ok_reviewers)),
        "identity_attestation_authenticated_to_provisioned_keys":not problems,
        "real_transcriber_or_listener_identity_independently_verified":False,
        "actual_audio_words_verified":False,
        "spoken_language_verified":False,
        "spoken_word_subtitle_sync_verified":False,
        "voice_consent_and_asset_rights_verified":False,
        "publishing_authorized":False,
        "youtube_upload_authorized":False,
        "monthly_recurring_infrastructure_inr":0,
    }
