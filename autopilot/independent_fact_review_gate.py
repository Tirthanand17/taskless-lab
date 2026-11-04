"""Branch 2 B3d3b: detached signed claim/surface review records (NO PUBLISH).

Only verifies cryptographic integrity and *coverage of submitted review records*.
This cannot establish real human enrollment, source truth, copyright ownership,
semantic/atomic claim completeness or provider authorization. Review signer
keys and externally authenticated trust roots must live OUTSIDE public GitHub.
No signing, network, local files, paid model, media rendering or YouTube writes.
"""
from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import re
from typing import Mapping, Sequence

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from autopilot.core import CHANNEL_ID
from autopilot.source_claim_preflight import (
    script_surface_docket, atomic_claim_docket, SourceClaimError,
    STATUS as PREFLIGHT_STATUS,
)
from autopilot.script_continuity_gate import (
    DetachedScriptSeal, TrustedScriptCustodian, ScriptContinuityError,
)

PURPOSE = "FLOWMINUTE_B3D3B_SIGNED_FACT_REVIEW_RECORDS_NO_PUBLISH_V1"
STATUS_PENDING = "SIGNED_REVIEW_RECORDS_PRESENT_AWAITING_EXTERNAL_OWNER_APPROVAL_NO_PUBLISH"
STATUS_BLOCKED = "BLOCKED_INDEPENDENT_REVIEW_RECORDS_NO_PUBLISH"
KINDS = frozenset(("surface", "claim"))
SURFACE_DECISIONS = frozenset(("NO_FACTUAL_ASSERTION", "CLAIMS_MAPPED", "REJECT"))
CLAIM_DECISIONS = frozenset(("SUPPORTED", "UNRESOLVED", "REJECT"))
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
SAFE_ID = re.compile(r"[a-z][a-z0-9_]{2,63}\Z")
MAX_REVIEW_AGE = timedelta(hours=24)
MAX_VALIDITY = timedelta(hours=48)
MAX_RECORDS = 200


class FactReviewError(ValueError):
    """An ambiguous or tampered independent review record must stop."""


@dataclass(frozen=True)
class TrustedFactReviewer:
    """Only externally enrolled and authenticated reviewer public keys qualify."""
    reviewer_id: str
    key_id: str
    public_key_ed25519_b64: str
    allowed_scopes: tuple[str, ...]
    active: bool = True


@dataclass(frozen=True)
class FactReviewClaim:
    purpose: str
    channel_id: str
    episode_id: str
    manifest_sha256: str
    review_docket_sha256: str
    scope_kind: str
    scope_id: str
    decision: str
    reviewer_id: str
    key_id: str
    assessed_at_utc: str
    expires_at_utc: str
    evidence_refs: tuple[str, ...]
    reviewer_notes: str
    receipt_id: str


@dataclass(frozen=True)
class SignedFactReview:
    claim: FactReviewClaim
    signature_ed25519_b64: str


def canonical_json(value: object) -> bytes:
    try:
        data = json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise FactReviewError("Review content cannot be canonically serialized") from exc
    if len(data) > 650_000:
        raise FactReviewError("Review content exceeds bounded size")
    return data


def review_docket_hash(surface: dict, claims: dict, excerpts: list[dict]) -> str:
    """Content binding includes even PENDING review/status flags and full sources."""
    if (not isinstance(surface, dict) or surface.get("status") != PREFLIGHT_STATUS
            or not isinstance(claims, dict) or claims.get("status") != PREFLIGHT_STATUS
            or surface.get("manifest_sha256") != claims.get("manifest_sha256")
            or surface.get("episode_id") != claims.get("episode_id")
            or not isinstance(excerpts, list)):
        raise FactReviewError("Inconsistent source/claim docket")
    return sha256(canonical_json({
        "purpose": PURPOSE, "surface_docket": surface,
        "atomic_claim_docket": claims, "source_excerpt_records": excerpts,
    })).hexdigest()


def _time(value: str) -> datetime:
    if not isinstance(value, str) or len(value) > 64:
        raise FactReviewError("Malformed reviewer date")
    try:
        when = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError, OverflowError) as exc:
        raise FactReviewError("Malformed reviewer date") from exc
    if when.tzinfo is None or when.utcoffset() is None:
        raise FactReviewError("Reviewer date requires timezone")
    return when.astimezone(timezone.utc)


def _trusted_public_key(entry: TrustedFactReviewer) -> Ed25519PublicKey:
    if (not isinstance(entry, TrustedFactReviewer) or entry.active is not True
            or not isinstance(entry.reviewer_id, str)
            or not SAFE_ID.fullmatch(entry.reviewer_id)
            or not isinstance(entry.key_id, str) or not SAFE_ID.fullmatch(entry.key_id)
            or not isinstance(entry.allowed_scopes, tuple)
            or not 1 <= len(entry.allowed_scopes) <= len(KINDS)
            or len(set(entry.allowed_scopes)) != len(entry.allowed_scopes)
            or not set(entry.allowed_scopes) <= KINDS):
        raise FactReviewError("Reviewer registry is not independently authorized")
    try:
        public = base64.b64decode(entry.public_key_ed25519_b64, validate=True)
        if len(public) != 32:
            raise FactReviewError("Reviewer public key length invalid")
        return Ed25519PublicKey.from_public_bytes(public)
    except (binascii.Error, ValueError, TypeError) as exc:
        raise FactReviewError("Reviewer public key invalid") from exc


def _validate_review(
    record: SignedFactReview, *, episode_id: str, manifest_sha256: str,
    docket_sha256: str, expected_ids: dict[str, set[str]],
    surface_claims: Mapping[str, int],
    source_refs: Mapping[str, tuple[str, ...]],
    registry: Mapping[str, TrustedFactReviewer],
    excluded: frozenset[str], at: datetime,
) -> None:
    if not isinstance(record, SignedFactReview) or not isinstance(record.claim, FactReviewClaim):
        raise FactReviewError("Review receipt missing or incorrectly typed")
    c = record.claim
    if (c.purpose != PURPOSE or c.channel_id != CHANNEL_ID
            or c.episode_id != episode_id
            or c.manifest_sha256 != manifest_sha256
            or c.review_docket_sha256 != docket_sha256
            or c.scope_kind not in KINDS or c.scope_id not in expected_ids[c.scope_kind]):
        raise FactReviewError("Review receipt does not bind to this script, slot and scope")
    if (not isinstance(c.reviewer_id, str) or not SAFE_ID.fullmatch(c.reviewer_id)
            or not isinstance(c.key_id, str) or not SAFE_ID.fullmatch(c.key_id)
            or not isinstance(c.receipt_id, str) or not SAFE_ID.fullmatch(c.receipt_id)
            or c.reviewer_id in excluded):
        raise FactReviewError("Invalid/excluded reviewer identity or receipt")
    entry = registry.get(c.reviewer_id)
    if (not isinstance(entry, TrustedFactReviewer)
            or entry.reviewer_id != c.reviewer_id
            or entry.key_id != c.key_id
            or c.scope_kind not in entry.allowed_scopes):
        raise FactReviewError("Reviewer not externally enrolled for this review scope")
    key = _trusted_public_key(entry)
    if (not isinstance(c.reviewer_notes, str)
            or not 30 <= len(c.reviewer_notes.strip()) <= 1000):
        raise FactReviewError("An independent reviewer explanation is required")
    if (not isinstance(c.evidence_refs, tuple)
            or len(c.evidence_refs) > 6
            or len(set(c.evidence_refs)) != len(c.evidence_refs)
            or not all(isinstance(x, str) for x in c.evidence_refs)):
        raise FactReviewError("Malformed bounded source excerpt references")
    if c.scope_kind == "surface":
        if (c.decision not in SURFACE_DECISIONS
                or c.evidence_refs != ()):
            raise FactReviewError("Invalid entire-surface review decision")
        mapped = surface_claims[c.scope_id]
        if ((c.decision == "NO_FACTUAL_ASSERTION" and mapped != 0)
                or (c.decision == "CLAIMS_MAPPED" and mapped == 0)):
            raise FactReviewError("Surface reviewer skipped or contradicted atomic claim inventory")
    else:
        if c.decision not in CLAIM_DECISIONS:
            raise FactReviewError("Invalid atomic-claim review decision")
        expected = source_refs[c.scope_id]
        if (c.decision == "SUPPORTED"
                and (not expected or c.evidence_refs != expected)):
            raise FactReviewError("Supported claim lacks the exact proposed cited source excerpts")
        if c.evidence_refs and any(x not in expected for x in c.evidence_refs):
            raise FactReviewError("Fact reviewer cited an unknown excerpt")
    issued, expires = _time(c.assessed_at_utc), _time(c.expires_at_utc)
    if (not timedelta(0) <= at - issued <= MAX_REVIEW_AGE
            or not timedelta(0) < expires - issued <= MAX_VALIDITY or expires <= at):
        raise FactReviewError("Independent reviewer receipt is future-dated, stale or expired")
    try:
        sig = base64.b64decode(record.signature_ed25519_b64, validate=True)
        if len(sig) != 64:
            raise FactReviewError("Invalid detached Ed25519 signature length")
        key.verify(sig, canonical_json(asdict(c)))
    except (InvalidSignature, binascii.Error, ValueError, TypeError) as exc:
        raise FactReviewError("Invalid independent detached reviewer signature") from exc


def verify_independent_fact_records(
    proposal: dict, slot: dict, observations: dict,
    *, script_seal: DetachedScriptSeal,
    external_script_anchor_sha256: str,
    script_registry: Mapping[str, TrustedScriptCustodian],
    proposed_atomic_claims: list[dict],
    source_excerpt_records: list[dict],
    signed_reviews: Sequence[SignedFactReview],
    fact_reviewer_registry: Mapping[str, TrustedFactReviewer],
    excluded_creator_and_publisher_ids: frozenset[str],
    now: datetime | None = None,
) -> dict:
    """Recalculate signed B3d1→B3d3a evidence; verify every scope's receipt.

    A successful cryptographic/coverage preflight does NOT prove the review
    signers are real humans, that source claims are true, or grant rendering.
    Private enrollment and immutable external reviewed-claim ledger are absent.
    """
    at = now if now is not None else datetime.now(timezone.utc)
    if not isinstance(at, datetime) or at.tzinfo is None or at.utcoffset() is None:
        raise FactReviewError("Review verifier requires a timezone-aware clock")
    at = at.astimezone(timezone.utc)
    if (not isinstance(excluded_creator_and_publisher_ids, frozenset)
            or not excluded_creator_and_publisher_ids
            or any(not isinstance(x, str) or not SAFE_ID.fullmatch(x)
                   for x in excluded_creator_and_publisher_ids)):
        raise FactReviewError("External creator/publisher exclusion identities required")
    if not isinstance(fact_reviewer_registry, Mapping) or not fact_reviewer_registry:
        raise FactReviewError("Separately enrolled reviewer registry required")
    try:
        surface = script_surface_docket(
            proposal, slot, observations,
            seal=script_seal, anchor_manifest_sha256=external_script_anchor_sha256,
            registry=script_registry,
            excluded_creator_and_publisher_ids=excluded_creator_and_publisher_ids,
            now=at,
        )
        claims = atomic_claim_docket(surface, proposed_atomic_claims, source_excerpt_records)
    except (SourceClaimError, ScriptContinuityError, KeyError, ValueError, TypeError) as exc:
        raise FactReviewError("Upstream signed script or exact source preflight invalid") from exc
    if (surface.get("release_authorized") is not False
            or claims.get("release_authorized") is not False
            or claims.get("atomic_claims_exhaustive") is not False):
        raise FactReviewError("Preflight unexpectedly asserts publication or editorial authority")
    digest = review_docket_hash(surface, claims, source_excerpt_records)
    expected = {
        "surface": {r["surface_id"] for r in surface["surface_rows"]},
        "claim": {r["atomic_claim_id"] for r in claims["potential_claims"]},
    }
    surface_claims = {x: 0 for x in expected["surface"]}
    claim_refs = {}
    for claim in claims["potential_claims"]:
        surface_claims[claim["surface_id"]] += 1
        claim_refs[claim["atomic_claim_id"]] = tuple(sorted(
            f'{x["source_id"]}:{x["excerpt_sha256"]}' for x in claim["cited_excerpt_links"]
        ))
    if (not isinstance(signed_reviews, (tuple, list))
            or len(signed_reviews) > MAX_RECORDS):
        raise FactReviewError("Unbounded or malformed signed reviewer records")
    if len(expected["surface"]) + len(expected["claim"]) > MAX_RECORDS:
        raise FactReviewError("Episode review surface count exceeds bound")
    valid_scopes: set[tuple[str, str]] = set()
    receipt_ids: set[str] = set()
    surface_reviewers: set[str] = set()
    claim_reviewers: set[str] = set()
    problems: set[str] = set()
    for rec in signed_reviews:
        _validate_review(
            rec, episode_id=surface["episode_id"],
            manifest_sha256=surface["manifest_sha256"],
            docket_sha256=digest, expected_ids=expected,
            surface_claims=surface_claims, source_refs=claim_refs,
            registry=fact_reviewer_registry,
            excluded=excluded_creator_and_publisher_ids, at=at,
        )
        c = rec.claim
        scope = (c.scope_kind, c.scope_id)
        if scope in valid_scopes or c.receipt_id in receipt_ids:
            raise FactReviewError("Replayed or duplicated reviewer scope/receipt")
        valid_scopes.add(scope)
        receipt_ids.add(c.receipt_id)
        if c.scope_kind == "surface":
            surface_reviewers.add(c.reviewer_id)
        else:
            claim_reviewers.add(c.reviewer_id)
        if c.decision == "REJECT":
            problems.add("SIGNED_REVIEW_REJECTED")
        if c.decision == "UNRESOLVED":
            problems.add("FACTUAL_REVIEW_UNRESOLVED")
    if any((kind, scope) not in valid_scopes for kind, ids in expected.items() for scope in ids):
        problems.add("REQUIRED_SCRIPT_SURFACE_OR_CLAIM_REVIEW_MISSING")
    if not surface_reviewers:
        problems.add("NO_INDEPENDENT_SURFACE_REVIEWER")
    if expected["claim"] and not claim_reviewers:
        problems.add("NO_INDEPENDENT_ATOMIC_FACT_REVIEWER")
    if surface_reviewers & claim_reviewers:
        problems.add("FACT_REVIEWER_NOT_SEPARATED_FROM_SCOPE_REVIEWER")
    if any(x in excluded_creator_and_publisher_ids for x in surface_reviewers | claim_reviewers):
        problems.add("CREATOR_OR_PUBLISHER_REVIEWED_OWN_CONTENT")
    return {
        "schema_version": 1,
        "status": STATUS_BLOCKED if problems else STATUS_PENDING,
        "problems": sorted(problems),
        "episode_id": surface["episode_id"],
        "script_manifest_sha256": surface["manifest_sha256"],
        "review_docket_sha256": digest,
        "expected_surface_count": len(expected["surface"]),
        "expected_atomic_claim_count": len(expected["claim"]),
        "signed_review_records_valid_count": len(valid_scopes),
        "signed_surface_reviewer_ids": sorted(surface_reviewers),
        "signed_claim_reviewer_ids": sorted(claim_reviewers),
        "signed_review_record_coverage_satisfied": not problems,
        "reviewers_real_identity_authenticated_by_software": False,
        "independent_fact_truth_verified_by_software": False,
        "independent_atomic_claim_completeness_proven": False,
        "external_private_review_ledger_deployed": False,
        "external_owner_review_and_release_grant_present": False,
        "full_final_render_or_thumbnail_reviewed": False,
        "originality_or_rights_approved": False,
        "media_render_enabled": False,
        "youtube_upload_enabled": False,
        "youtube_schedule_enabled": False,
        "release_authorized": False,
    }
