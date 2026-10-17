"""FlowMinute Phase 3C: tamper-evident, separated technical review records.

Software staging only: this code has no signing keys, no network, no media
uploads, no billing and no publication control. Ed25519 signatures authenticate
receipt integrity against *externally provisioned* trusted public keys. They
do NOT prove somebody watched a video, owns the rights, understands Hindi,
or gave legal clearance. Actual private keys and reviewer identity onboarding
MUST be handled outside this public repository.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Mapping, Sequence
import base64
import binascii
import json
import re

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .agent_org import WorkflowError
from .media_rights_review import EvidencePacket

DIMENSIONS = frozenset(("media_visual", "audio_language", "source_accuracy", "asset_rights"))
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
SAFE_ID = re.compile(r"[a-z][a-z0-9_]{2,63}\Z")
MAX_REVIEW_AGE = timedelta(hours=24)
MAX_VALIDITY = timedelta(hours=48)


@dataclass(frozen=True)
class TrustedReviewer:
    """External trusted public-key registry entry; NEVER sourced from a receipt."""
    reviewer_id: str
    key_id: str
    public_key_ed25519_b64: str
    allowed_dimensions: tuple[str, ...]
    active: bool = True


@dataclass(frozen=True)
class ReviewClaim:
    episode_id: str
    packet_sha256: str
    final_video_sha256: str
    narration_sha256: str
    dimension: str
    reviewer_id: str
    key_id: str
    decision: str
    assessed_at_utc: str
    expires_at_utc: str
    evidence_sha256: tuple[str, ...]
    reviewer_notes: str
    receipt_id: str


@dataclass(frozen=True)
class SignedReview:
    claim: ReviewClaim
    signature_ed25519_b64: str


@dataclass(frozen=True)
class ReviewBundleResult:
    status: str
    problems: tuple[str, ...]
    valid_dimensions: tuple[str, ...]
    packet_sha256: str
    signed_reviewer_ids: tuple[str, ...]
    human_review_observed_by_software: bool = False
    license_legality_verified_by_software: bool = False
    media_content_verified_by_software: bool = False
    publishing_authorized: bool = False
    scheduling_enabled: bool = False


def _iso(value: str) -> datetime:
    if not isinstance(value, str) or len(value)>64:
        raise WorkflowError("Invalid review date")
    try:
        dt=datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError,ValueError,OverflowError) as exc:
        raise WorkflowError("Invalid review date") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise WorkflowError("Review date requires timezone")
    return dt.astimezone(timezone.utc)


def _canonical(payload: ReviewClaim) -> bytes:
    return json.dumps(asdict(payload), sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def packet_digest(packet: EvidencePacket) -> str:
    if not isinstance(packet, EvidencePacket):
        raise WorkflowError("Actual media preflight EvidencePacket required")
    return sha256(json.dumps(asdict(packet), sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def _public_key(item: TrustedReviewer) -> Ed25519PublicKey:
    if (not SAFE_ID.fullmatch(item.reviewer_id) or not SAFE_ID.fullmatch(item.key_id)
            or not 1<=len(item.allowed_dimensions)<=len(DIMENSIONS)
            or len(set(item.allowed_dimensions))!=len(item.allowed_dimensions)
            or not set(item.allowed_dimensions)<=DIMENSIONS or item.active is not True):
        raise WorkflowError("Invalid authorized reviewer record")
    try:
        key=base64.b64decode(item.public_key_ed25519_b64, validate=True)
        if len(key)!=32: raise WorkflowError("Reviewer Ed25519 key length invalid")
        return Ed25519PublicKey.from_public_bytes(key)
    except (binascii.Error,ValueError,TypeError) as exc:
        raise WorkflowError("Reviewer Ed25519 public key invalid") from exc


def _validate_claim(claim: ReviewClaim, *, now: datetime,
                    episode_id: str, packet: EvidencePacket, binding_hash: str) -> None:
    if (claim.episode_id!=episode_id or claim.packet_sha256!=binding_hash
            or claim.final_video_sha256!=packet.video.video_sha256
            or claim.narration_sha256!=packet.narration.sha256_hex):
        raise WorkflowError("Review not bound to this inspected episode or media")
    if (claim.dimension not in DIMENSIONS or claim.decision not in ("PASS","REJECT")
            or not SAFE_ID.fullmatch(claim.reviewer_id)
            or not SAFE_ID.fullmatch(claim.key_id)
            or not SAFE_ID.fullmatch(claim.receipt_id)):
        raise WorkflowError("Invalid signed review decision")
    if not isinstance(claim.reviewer_notes,str) or not 30<=len(claim.reviewer_notes.strip())<=1000:
        raise WorkflowError("Review notes missing or too long")
    if (not 1<=len(claim.evidence_sha256)<=12
            or len(set(claim.evidence_sha256))!=len(claim.evidence_sha256)
            or any(not isinstance(d,str) or not HEX64.fullmatch(d) for d in claim.evidence_sha256)):
        raise WorkflowError("Review requires bounded content-addressed supporting evidence")
    created=_iso(claim.assessed_at_utc)
    expires=_iso(claim.expires_at_utc)
    if (not timedelta(0)<=now-created<=MAX_REVIEW_AGE
            or not timedelta(0)<expires-created<=MAX_VALIDITY or expires<=now):
        raise WorkflowError("Review stale, expired, or future dated")


def verify_separated_reviews(
    *, episode_id: str, packet: EvidencePacket,
    signed_reviews: Sequence[SignedReview],
    registry: Mapping[str,TrustedReviewer],
    excluded_creator_and_publisher_ids: frozenset[str],
    now: datetime | None = None,
) -> ReviewBundleResult:
    """Verify four detached reviewer signatures, never grant release permission.

    Trust roots MUST originate in privately controlled reviewer enrollment.
    Exclusion identities MUST be authenticated by a separate production system.
    This preflight cannot independently verify real people or media semantics.
    """
    at=now or datetime.now(timezone.utc)
    if at.tzinfo is None or at.utcoffset() is None:
        raise WorkflowError("Verifier clock needs timezone")
    at=at.astimezone(timezone.utc)
    binding=packet_digest(packet)
    failures: list[str]=[]
    ok_dimensions:set[str]=set()
    reviewers:set[str]=set()
    if (packet.status!="INSPECTED_AWAITING_INDEPENDENT_REVIEW"
            or not all((packet.media_hash_verified,packet.narration_hash_verified,
                        packet.rights_documents_hash_verified,
                        packet.voice_rights_record_matched))
            or bool(packet.problems)):
        failures.append("MEDIA_OR_RIGHTS_PREFLIGHT_NOT_READY")
    if (not isinstance(episode_id,str) or not SAFE_ID.fullmatch(episode_id)
            or not isinstance(excluded_creator_and_publisher_ids,frozenset)
            or not excluded_creator_and_publisher_ids
            or any(not isinstance(x,str) or not SAFE_ID.fullmatch(x)
                   for x in excluded_creator_and_publisher_ids)):
        failures.append("REVIEW_TRUST_BOUNDARY_INVALID")
    if (not isinstance(signed_reviews,(list,tuple))
            or len(signed_reviews)>len(DIMENSIONS)+4):
        failures.append("INVALID_REVIEW_PACKET_COUNT")
        signed_reviews=()
    seen_receipts:set[str]=set()
    seen_key_pairs:set[tuple[str,str]]=set()
    for record in signed_reviews:
        if not isinstance(record,SignedReview) or not isinstance(record.claim,ReviewClaim):
            failures.append("MALFORMED_REVIEW_RECORD")
            continue
        claim=record.claim
        if claim.receipt_id in seen_receipts:
            failures.append("DUPLICATED_REVIEW_RECEIPT")
            continue
        seen_receipts.add(claim.receipt_id)
        if (claim.reviewer_id,claim.key_id) in seen_key_pairs:
            failures.append("REVIEWER_REUSED_ACROSS_DIMENSIONS")
            continue
        seen_key_pairs.add((claim.reviewer_id,claim.key_id))
        if claim.reviewer_id in excluded_creator_and_publisher_ids:
            failures.append("CREATOR_OR_PUBLISHER_ATTEMPTED_TO_REVIEW")
            continue
        enrolled=registry.get(claim.reviewer_id)
        if (enrolled is None or enrolled.reviewer_id!=claim.reviewer_id
                or enrolled.key_id!=claim.key_id
                or claim.dimension not in enrolled.allowed_dimensions):
            failures.append("REVIEWER_NOT_AUTHORIZED_FOR_DIMENSION")
            continue
        try:
            key=_public_key(enrolled)
            _validate_claim(claim,now=at,episode_id=episode_id,packet=packet,
                            binding_hash=binding)
            sig=base64.b64decode(record.signature_ed25519_b64,validate=True)
            if len(sig)!=64:
                raise WorkflowError("Invalid Ed25519 signature length")
            key.verify(sig,_canonical(claim))
        except (WorkflowError,InvalidSignature,binascii.Error,TypeError,ValueError):
            failures.append("INVALID_OR_STALE_REVIEW_SIGNATURE")
            continue
        if claim.decision=="REJECT":
            failures.append("INDEPENDENT_REVIEW_REJECTED")
            continue
        if claim.dimension in ok_dimensions:
            failures.append("DUPLICATE_REVIEW_DIMENSION")
            continue
        ok_dimensions.add(claim.dimension)
        reviewers.add(claim.reviewer_id)
    if ok_dimensions!=DIMENSIONS:
        failures.append("REQUIRED_INDEPENDENT_REVIEW_MISSING")
    if len(reviewers)!=len(DIMENSIONS):
        failures.append("FOUR_DISTINCT_REVIEWERS_REQUIRED")
    return ReviewBundleResult(
        "SIGNED_RECORDS_PRESENT_AWAITING_EXTERNAL_APPROVAL"
            if not failures else "BLOCKED_REVIEW_EVIDENCE",
        tuple(sorted(set(failures))),tuple(sorted(ok_dimensions)),binding,
        tuple(sorted(reviewers))
    )
