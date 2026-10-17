"""Phase 4D: OFFLINE read-only observation signature gate.

This validates the integrity of detached inspection receipts against a separately
supplied trusted public-key registry. It does NOT connect to Cloudflare/YouTube,
verify that a collector actually contacted either provider, or authorize any
D1 migration, upload, release, billing, OAuth change or schedule change.
"""
from __future__ import annotations

import base64
import binascii
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import re
from typing import Mapping, Sequence

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .core import CHANNEL_ID

KINDS = frozenset(("d1_schema", "youtube_history"))
IDENTITY = re.compile(r"[a-z][a-z0-9_]{2,63}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
MAX_AGE = timedelta(minutes=15)
MAX_TTL = timedelta(minutes=30)


class ObservationBlocked(ValueError):
    """A receipt was malformed, forged, stale, or otherwise unsuitable."""


@dataclass(frozen=True)
class CollectorTrust:
    collector_id: str
    key_id: str
    public_key_b64: str
    allowed_kind: str
    enabled: bool = True


@dataclass(frozen=True)
class ObservationClaim:
    schema_version: int
    kind: str
    channel_id: str
    collector_id: str
    key_id: str
    payload_sha256: str
    request_nonce: str
    collected_at_utc: str
    expires_at_utc: str
    access_mode: str = "read_only"


@dataclass(frozen=True)
class SignedObservation:
    claim: ObservationClaim
    signature_b64: str


@dataclass(frozen=True)
class ObservationBundleResult:
    status: str
    payload_sha256: tuple[tuple[str, str], ...]
    collector_ids: tuple[str, ...]
    signature_integrity_valid: bool
    provider_connection_observed: bool = False
    authenticated_channel_readback: bool = False
    production_migration_ready: bool = False
    production_upload_ready: bool = False
    production_schedule_ready: bool = False


def _instant(value: str) -> datetime:
    if not isinstance(value, str) or len(value) > 40:
        raise ObservationBlocked("Canonical UTC instant required")
    try:
        instant = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ObservationBlocked("Invalid receipt instant") from exc
    if instant.tzinfo is None or instant.utcoffset() != timedelta(0):
        raise ObservationBlocked("UTC time with timezone required")
    if value != instant.isoformat(timespec="seconds"):
        raise ObservationBlocked("Canonical second-precision +00:00 required")
    return instant


def _canonical(value: ObservationClaim) -> bytes:
    return json.dumps(asdict(value), ensure_ascii=True, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _key(trust: CollectorTrust) -> Ed25519PublicKey:
    if (not isinstance(trust, CollectorTrust)
            or not IDENTITY.fullmatch(trust.collector_id)
            or not IDENTITY.fullmatch(trust.key_id)
            or trust.allowed_kind not in KINDS
            or trust.enabled is not True):
        raise ObservationBlocked("Collector trust registry entry invalid or disabled")
    try:
        value = base64.b64decode(trust.public_key_b64, validate=True)
        if len(value) != 32:
            raise ObservationBlocked("Invalid pinned public key length")
        return Ed25519PublicKey.from_public_bytes(value)
    except (binascii.Error, TypeError, ValueError) as exc:
        raise ObservationBlocked("Invalid pinned public key") from exc


def verify_readonly_observation_bundle(
    *, receipts: Sequence[SignedObservation],
    trusted_registry: Mapping[str, CollectorTrust],
    expected_payload_sha256: Mapping[str, str],
    expected_nonce: str,
    already_seen_nonces: frozenset[str] = frozenset(),
    now: datetime,
) -> ObservationBundleResult:
    """Verify two independently signed, bounded metadata inspection receipts.

    All trust roots must be configured OUTSIDE the submitted receipt; real provider
    access, collector identity enrollment and durable nonce tracking are absent.
    This returns cryptographic INTEGRITY only, never real provider authenticity.
    """
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ObservationBlocked("Trusted timezone-aware verifier clock required")
    now = now.astimezone(timezone.utc)
    if (not isinstance(expected_nonce, str) or not IDENTITY.fullmatch(expected_nonce)
            or expected_nonce in already_seen_nonces):
        raise ObservationBlocked("Unknown, malformed or replayed request nonce")
    if (not isinstance(receipts, (list, tuple)) or len(receipts) != 2
            or not isinstance(trusted_registry, Mapping)
            or set(expected_payload_sha256) != KINDS
            or any(not isinstance(v, str) or not HEX64.fullmatch(v)
                   for v in expected_payload_sha256.values())):
        raise ObservationBlocked("Exactly two expected signed metadata observations required")
    seen_kind: set[str] = set()
    seen_collectors: set[str] = set()
    seen_public_keys: set[bytes] = set()
    valid_hashes: list[tuple[str, str]] = []
    for item in receipts:
        if not isinstance(item, SignedObservation) or not isinstance(item.claim, ObservationClaim):
            raise ObservationBlocked("Invalid signed receipt structure")
        claim = item.claim
        if (type(claim.schema_version) is not int or claim.schema_version != 1
                or claim.kind not in KINDS or claim.channel_id != CHANNEL_ID
                or claim.access_mode != "read_only"
                or not isinstance(claim.payload_sha256, str)
                or not HEX64.fullmatch(claim.payload_sha256)
                or claim.payload_sha256 != expected_payload_sha256.get(claim.kind)
                or not isinstance(claim.collector_id, str)
                or not IDENTITY.fullmatch(claim.collector_id)
                or not isinstance(claim.key_id, str)
                or not IDENTITY.fullmatch(claim.key_id)
                or claim.request_nonce != expected_nonce):
            raise ObservationBlocked("Receipt purpose, identity, hash or request mismatch")
        if claim.kind in seen_kind or claim.collector_id in seen_collectors:
            raise ObservationBlocked("Duplicate observation kind or collector")
        issued,expires = _instant(claim.collected_at_utc),_instant(claim.expires_at_utc)
        if (not timedelta(0) <= now-issued <= MAX_AGE
                or not timedelta(0) < expires-issued <= MAX_TTL
                or expires <= now):
            raise ObservationBlocked("Expired, future-dated or stale observation")
        trust = trusted_registry.get(claim.collector_id)
        if (not isinstance(trust, CollectorTrust) or trust.collector_id != claim.collector_id
                or trust.key_id != claim.key_id or trust.allowed_kind != claim.kind):
            raise ObservationBlocked("Collector not enrolled for this observation kind")
        public_key = _key(trust)
        public_key_material = base64.b64decode(trust.public_key_b64, validate=True)
        if public_key_material in seen_public_keys:
            raise ObservationBlocked("Both provider collectors must use independent signing keys")
        seen_public_keys.add(public_key_material)
        try:
            if not isinstance(item.signature_b64, str):
                raise ObservationBlocked("Receipt signature required")
            signature=base64.b64decode(item.signature_b64, validate=True)
            if len(signature) != 64:
                raise ObservationBlocked("Invalid signature length")
            public_key.verify(signature, _canonical(claim))
        except (binascii.Error, InvalidSignature, TypeError, ValueError) as exc:
            raise ObservationBlocked("Invalid detached receipt signature") from exc
        seen_kind.add(claim.kind)
        seen_collectors.add(claim.collector_id)
        valid_hashes.append((claim.kind, claim.payload_sha256))
    if seen_kind != KINDS:
        raise ObservationBlocked("Both independent provider receipt kinds are required")
    return ObservationBundleResult(
        status="SIGNED_INTEGRITY_ONLY_PROVIDER_ACCESS_UNVERIFIED",
        payload_sha256=tuple(sorted(valid_hashes)),
        collector_ids=tuple(sorted(seen_collectors)),
        signature_integrity_valid=True,
    )


def sanitized_snapshot_hash(value: object) -> str:
    """SHA-256 of sanitized JSON metadata; does not remove secrets automatically.

    The caller MUST sanitize before invoking. Not a proof of actual D1/YouTube
    access and not a substitute for authenticated provider readback.
    """
    try:
        canonical = json.dumps(value, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=True, allow_nan=False).encode("utf-8")
    except (ValueError, TypeError) as exc:
        raise ObservationBlocked("Metadata snapshot must be safe JSON") from exc
    if len(canonical) > 256_000:
        raise ObservationBlocked("Bounded sanitized metadata snapshot required")
    return sha256(canonical).hexdigest()
