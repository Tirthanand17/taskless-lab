"""Branch 2 B3d4c2a: externally anchored owner-signed model-use *preflight*.

The signature establishes integrity against a separately enrolled owner key;
it DOES NOT prove a real person gave consent, a Google project has free tier,
billing is disabled, terms are acceptable, or a provider secret is available.

NO provider HTTP request, no signing private keys, no storage, no scheduled
jobs, no YouTube, no video production, and no publishing authorization.
A PRIVATE durable lease/fenced budget service, owner key enrollment and vault
are required to deploy an eventual real inference adapter. CI keys are fake.
"""
from __future__ import annotations

import base64
import binascii
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import re
from typing import Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from autopilot.core import CHANNEL_ID
from autopilot.script_draft_agent import (
    ALLOWED_MODELS, DRAFT_STATUS, ScriptDraftError, build_draft_input,
)

PURPOSE = "FLOWMINUTE_B3D4C2A_EXTERNAL_OWNER_GEMINI_ZERO_COST_LEASE_V1"
STATUS = "OWNER_SIGNATURE_CHECKED_PRIVATE_ENTITLEMENT_AND_LEDGER_PENDING_NO_INFERENCE"
SAFE_ID = re.compile(r"[a-z][a-z0-9_]{2,63}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
EPISODE = re.compile(r"fm_[0-9]{8}_(short_am|long|short_pm)\Z")
MAX_LEASE_AGE = timedelta(minutes=45)
MAX_VALIDITY = timedelta(hours=2)
MAX_CONTEXT_BYTES = 18_000


class ModelLeaseError(ValueError):
    """The owner approval authority or request context is untrusted."""


@dataclass(frozen=True)
class TrustedProviderOwner:
    """Externally enrolled owner public-key record, never from AI response."""
    owner_id: str
    key_id: str
    public_key_ed25519_b64: str
    active: bool = True


@dataclass(frozen=True)
class ProviderLeaseTerms:
    purpose: str
    channel_id: str
    episode_id: str
    model_id: str
    provider_id: str
    draft_context_sha256: str
    owner_id: str
    key_id: str
    lease_id: str
    free_tier_billing_project_fingerprint_sha256: str
    free_tier_entitlement_attestation_sha256: str
    provider_data_terms_snapshot_sha256: str
    owner_provider_data_use_consent_record_sha256: str
    private_secret_custody_policy_sha256: str
    allowed_data_class: str
    requests_allowed: int
    incremental_paid_budget_cents: int
    accepts_provider_improvement_use: bool
    owner_grants_external_inference: bool
    issued_at_utc: str
    expires_at_utc: str


@dataclass(frozen=True)
class SignedProviderLease:
    terms: ProviderLeaseTerms
    signature_ed25519_b64: str


def canonical_bytes(value: object) -> bytes:
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (ValueError, TypeError, OverflowError, RecursionError) as exc:
        raise ModelLeaseError("Cannot canonically encode provider lease") from exc
    if len(encoded) > MAX_CONTEXT_BYTES:
        raise ModelLeaseError("Provider lease or input context exceeds cap")
    return encoded


def digest(value: object) -> str:
    return sha256(canonical_bytes(value)).hexdigest()


def _time(value: str) -> datetime:
    if not isinstance(value, str) or not 1 <= len(value) <= 50:
        raise ModelLeaseError("Invalid lease timestamp")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError, OverflowError) as exc:
        raise ModelLeaseError("Malformed lease time") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ModelLeaseError("Owner lease timestamps must have UTC offsets")
    return dt.astimezone(timezone.utc)


def _public_key(record: TrustedProviderOwner) -> Ed25519PublicKey:
    if (not isinstance(record, TrustedProviderOwner)
            or record.active is not True
            or not isinstance(record.owner_id, str)
            or not SAFE_ID.fullmatch(record.owner_id)
            or not isinstance(record.key_id, str)
            or not SAFE_ID.fullmatch(record.key_id)):
        raise ModelLeaseError("Invalid or revoked independent owner enrollment")
    try:
        raw = base64.b64decode(record.public_key_ed25519_b64, validate=True)
        if len(raw) != 32:
            raise ModelLeaseError("Invalid public key size")
        return Ed25519PublicKey.from_public_bytes(raw)
    except (TypeError, ValueError, binascii.Error) as exc:
        raise ModelLeaseError("Owner public-key material invalid") from exc


def verify_owner_provider_lease(
    *, slot: dict, observations: dict,
    signed_lease: SignedProviderLease,
    external_lease_anchor_sha256: str,
    owner_registry: Mapping[str, TrustedProviderOwner],
    excluded_automated_agent_ids: frozenset[str],
    now: datetime | None = None,
) -> dict:
    """Rebuild exact unverified public-metadata-only context and check signature.

    The immutable anchor, owner registry and identity exclusions must be read
    from separately authenticated private owner-controlled systems. They
    cannot be reconstructed from model output or a public PR's assertions.
    """
    at = now if now is not None else datetime.now(timezone.utc)
    if (not isinstance(at, datetime) or at.tzinfo is None
            or at.utcoffset() is None):
        raise ModelLeaseError("Timezone-aware verifier clock required")
    at = at.astimezone(timezone.utc)
    if (not isinstance(signed_lease, SignedProviderLease)
            or not isinstance(signed_lease.terms, ProviderLeaseTerms)
            or not isinstance(owner_registry, Mapping) or not owner_registry
            or not isinstance(excluded_automated_agent_ids, frozenset)
            or not excluded_automated_agent_ids
            or any(not isinstance(x, str) or not SAFE_ID.fullmatch(x)
                   for x in excluded_automated_agent_ids)):
        raise ModelLeaseError("Private owner enrollment and automation exclusions required")
    try:
        draft_input = build_draft_input(slot, observations)
    except (ScriptDraftError, KeyError, ValueError, TypeError) as exc:
        raise ModelLeaseError("Invalid or privileged source context for lease") from exc
    if (draft_input.get("source_claims_approved") is not False
            or draft_input.get("rights_approved") is not False
            or draft_input.get("publication_authorized") is not False
            or not isinstance(draft_input.get("untrusted_source_records"), list)):
        raise ModelLeaseError("Model-source context elevated its factual approval")
    context_sha = digest(draft_input)
    t = signed_lease.terms
    if (t.purpose != PURPOSE or t.channel_id != CHANNEL_ID
            or t.episode_id != slot.get("episode_id")
            or not EPISODE.fullmatch(t.episode_id)
            or t.draft_context_sha256 != context_sha
            or t.provider_id != "google_gemini_developer_api"
            or t.model_id not in ALLOWED_MODELS
            or t.allowed_data_class != "PUBLIC_HEADLINE_METADATA_ONLY"
            or t.accepts_provider_improvement_use is not True
            or t.owner_grants_external_inference is not True
            or type(t.requests_allowed) is not int or t.requests_allowed != 1
            or type(t.incremental_paid_budget_cents) is not int
            or t.incremental_paid_budget_cents != 0):
        raise ModelLeaseError("Owner lease does not cover this exact zero-cost draft request")
    # The owner signature covers the fingerprint of separately reviewed
    # pricing/consent/project/custody records. It does not make them true.
    for field in (
        "free_tier_billing_project_fingerprint_sha256",
        "free_tier_entitlement_attestation_sha256",
        "provider_data_terms_snapshot_sha256",
        "owner_provider_data_use_consent_record_sha256",
        "private_secret_custody_policy_sha256",
    ):
        raw = getattr(t, field)
        if not isinstance(raw, str) or not HEX64.fullmatch(raw):
            raise ModelLeaseError("Missing exact private entitlement or data consent record digest")
    if (not isinstance(t.owner_id, str) or not SAFE_ID.fullmatch(t.owner_id)
            or not isinstance(t.key_id, str) or not SAFE_ID.fullmatch(t.key_id)
            or not isinstance(t.lease_id, str) or not SAFE_ID.fullmatch(t.lease_id)
            or t.owner_id in excluded_automated_agent_ids):
        raise ModelLeaseError("Untrusted or automated owner lease signer")
    record = owner_registry.get(t.owner_id)
    if not isinstance(record, TrustedProviderOwner) or (
        record.owner_id != t.owner_id or record.key_id != t.key_id
    ):
        raise ModelLeaseError("Lease signature does not match independent owner enrollment")
    key = _public_key(record)
    created, expires = _time(t.issued_at_utc), _time(t.expires_at_utc)
    if (not timedelta(0) <= at - created <= MAX_LEASE_AGE
            or not timedelta(0) < expires - created <= MAX_VALIDITY
            or expires <= at):
        raise ModelLeaseError("Owner consent lease expired, stale or future-dated")
    if (not isinstance(external_lease_anchor_sha256, str)
            or not HEX64.fullmatch(external_lease_anchor_sha256)
            or digest(asdict(t)) != external_lease_anchor_sha256):
        raise ModelLeaseError("Signed owner lease is not externally anchored")
    try:
        signature = base64.b64decode(signed_lease.signature_ed25519_b64, validate=True)
        if len(signature) != 64:
            raise ModelLeaseError("Detached owner signature length invalid")
        key.verify(signature, canonical_bytes(asdict(t)))
    except (InvalidSignature, ValueError, TypeError, binascii.Error) as exc:
        raise ModelLeaseError("Invalid owner-signed provider lease") from exc
    return {
        "schema_version": 1,
        "status": STATUS,
        "lease_id": t.lease_id,
        "episode_id": t.episode_id,
        "channel_id": CHANNEL_ID,
        "model_id": t.model_id,
        "draft_context_sha256": context_sha,
        "external_lease_anchor_sha256": external_lease_anchor_sha256,
        "provider_owner_key_signature_valid": True,
        "signed_scope_limit_requests": 1,
        "signed_max_incremental_paid_budget_cents": 0,
        "owner_identity_real_world_authenticated_by_software": False,
        "private_entitlement_records_independently_validated": False,
        "actual_provider_project_and_zero_spend_verified": False,
        "private_immutable_request_ledger_connected": False,
        "private_key_vault_connected": False,
        "provider_terms_real_consent_verified": False,
        "provider_live_call_enabled": False,
        "youtube_upload_enabled": False,
        "youtube_schedule_enabled": False,
        "release_authorized": False,
    }


def verify_three_daily_owner_lease_packets(packets: list[dict]) -> dict:
    """Check distinct preflight reports only: not a ledger or live entitlement."""
    if not isinstance(packets, list) or len(packets) != 3:
        raise ModelLeaseError("Requires exactly the three different daily slots")
    seen_episode: set[str] = set()
    seen_lease: set[str] = set()
    seen_context: set[str] = set()
    days: set[str] = set()
    for item in packets:
        if (not isinstance(item, dict) or item.get("status") != STATUS
                or item.get("provider_owner_key_signature_valid") is not True
                or item.get("provider_live_call_enabled") is not False
                or item.get("release_authorized") is not False
                or item.get("youtube_upload_enabled") is not False):
            raise ModelLeaseError("Three-slot model preflight packet invalid")
        episode, lease_id, context = (
            item.get("episode_id"), item.get("lease_id"),
            item.get("draft_context_sha256"),
        )
        if (not isinstance(episode, str) or not EPISODE.fullmatch(episode)
                or not isinstance(lease_id, str) or not SAFE_ID.fullmatch(lease_id)
                or not isinstance(context, str) or not HEX64.fullmatch(context)):
            raise ModelLeaseError("Three-slot packet lacks exact individual identities")
        if episode in seen_episode or lease_id in seen_lease or context in seen_context:
            raise ModelLeaseError("Replay, duplicate lease or duplicated episode context")
        seen_episode.add(episode)
        seen_lease.add(lease_id)
        seen_context.add(context)
        days.add(episode[3:11])
    if len(days) != 1 or {x.split("_", 2)[2] for x in seen_episode} != {
        "short_am", "long", "short_pm"
    }:
        raise ModelLeaseError("A full three-slot owner lease set must share one IST day")
    return {
        "status": "THREE_DISTINCT_OWNER_LEASE_SIGNED_RECORDS_ONLY_NO_MODEL_CALL",
        "episode_ids": sorted(seen_episode),
        "signed_lease_count": 3,
        "provider_inference_executed": False,
        "real_provider_data_use_consent_verified": False,
        "budget_lease_atomically_consumed": False,
        "youtube_upload_enabled": False,
        "release_authorized": False,
    }
