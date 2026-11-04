"""B3d1: externally anchored, detached-signed *script* continuity preflight.

Builds on B3c editorial dossiers. Reuses the installed cryptography Ed25519
verification pattern from signed_review_gate, but this is NOT a fact/rights
review and NEVER enables rendering or YouTube. Trusted anchors and reviewer
public keys must come from an independently authenticated private authority.
No signer, key, ledger, paid service, network or media is created here.
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

from autopilot.claim_review_dossier import build_review_dossier, EditorialGateError
from autopilot.core import CHANNEL_ID, slot_utc

HEX = re.compile(r"[0-9a-f]{64}\Z")
ID = re.compile(r"[a-z][a-z0-9_]{2,63}\Z")
EP = re.compile(r"fm_(\d{4})(\d{2})(\d{2})_(short_am|long|short_pm)\Z")
PURPOSE = "FLOWMINUTE_B3D1_SCRIPT_CONTINUITY_NOT_EDITORIAL_APPROVAL_V1"
STATUS = "SIGNED_SCRIPT_CONTINUITY_ONLY_EDITORIAL_PENDING_NO_PUBLISH"
SLOTS = {
    "short_am": ("short", "11:00"),
    "long": ("long", "16:00"),
    "short_pm": ("short", "20:30"),
}


class ScriptContinuityError(ValueError):
    """Invalid content identity, trust root, signature or scope."""


@dataclass(frozen=True)
class TrustedScriptCustodian:
    """Out-of-band trust root; do not load it from user/model/source artifacts."""
    custodian_id: str
    key_id: str
    public_key_ed25519_b64: str
    active: bool = True


@dataclass(frozen=True)
class ScriptSealClaim:
    purpose: str
    manifest_sha256: str
    episode_id: str
    channel_id: str
    release_slot: str
    release_utc: str
    custodian_id: str
    key_id: str
    issued_at_utc: str
    expires_at_utc: str


@dataclass(frozen=True)
class DetachedScriptSeal:
    claim: ScriptSealClaim
    signature_ed25519_b64: str


def _json_bytes(value: object) -> bytes:
    try:
        encoded = json.dumps(value, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (ValueError, TypeError, RecursionError, OverflowError) as exc:
        raise ScriptContinuityError("Unserializable script or source metadata") from exc
    if len(encoded) > 256_000:
        raise ScriptContinuityError("Unbounded script/evidence manifest")
    return encoded


def _hash(value: object) -> str:
    return sha256(_json_bytes(value)).hexdigest()


def _parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or len(value) > 45:
        raise ScriptContinuityError("Invalid seal timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ScriptContinuityError("Invalid seal timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ScriptContinuityError("Seal timestamp must carry timezone")
    return parsed.astimezone(timezone.utc)


def freeze_script_manifest(proposal: object, slot: object, observations: object) -> dict:
    """Bind exact B3c draft, source observations and one actual IST calendar slot."""
    if not isinstance(slot, dict):
        raise ScriptContinuityError("A precise planned slot is required")
    episode_id = slot.get("episode_id")
    match = EP.fullmatch(episode_id) if isinstance(episode_id, str) else None
    if match is None:
        raise ScriptContinuityError("Invalid episode key")
    year, month, day, release_slot = match.groups()
    day_ist = f"{year}-{month}-{day}"
    kind, local = SLOTS[release_slot]
    try:
        expected_utc = slot_utc(day_ist, release_slot)
    except (TypeError, ValueError) as exc:
        raise ScriptContinuityError("Invalid IST release date") from exc
    if (slot.get("release_slot") != release_slot
            or slot.get("format") != kind
            or slot.get("local_ist") != local
            or slot.get("release_utc") != expected_utc
            or slot.get("release_authorized") is not False
            or slot.get("real_media_exists") is not False):
        raise ScriptContinuityError("Replayed, moved or privilege-escalated slot")
    try:
        dossier = build_review_dossier(proposal, slot, observations)
    except (EditorialGateError, KeyError, TypeError, ValueError) as exc:
        raise ScriptContinuityError("B3c source and proposal dossier invalid") from exc
    if (dossier.get("release_authorized") is not False
            or dossier.get("all_claims_verified") is not False
            or dossier.get("rights_and_originality_review_complete") is not False):
        raise ScriptContinuityError("Dossier illegally claims editorial approval")
    if not isinstance(proposal, dict) or not isinstance(observations, dict):
        raise ScriptContinuityError("Unusable proposal or source observations")
    return {
        "schema_version": 1,
        "purpose": PURPOSE,
        "channel_id": CHANNEL_ID,
        "episode_id": episode_id,
        "format": kind,
        "release_day_ist": day_ist,
        "release_slot": release_slot,
        "release_utc": expected_utc,
        "draft_sha256": _hash(proposal),
        "narration_sha256": sha256(proposal["narration"].encode("utf-8")).hexdigest(),
        "source_observations_sha256": _hash(observations),
        "b3c_dossier_sha256": _hash(dossier),
        "candidate_claim_count": dossier["proposed_claim_count"],
        "claimed_fact_check_complete": False,
        "human_editorial_review_complete": False,
        "rights_clearance_complete": False,
        "release_authorized": False,
        "youtube_upload_enabled": False,
        "youtube_schedule_enabled": False,
    }


def verify_script_seal(
    proposal: object, slot: object, observations: object,
    *, seal: DetachedScriptSeal,
    anchor_manifest_sha256: str,
    registry: Mapping[str, TrustedScriptCustodian],
    excluded_creator_and_publisher_ids: frozenset[str],
    now: datetime | None = None,
) -> dict:
    """Confirm provenance continuity only; independent fact/rights review pending.

    The expected digest AND trusted custodian registry must come from a
    separately secured private ledger or owner-controlled trust service.
    An attacker who supplies both the artifact and its anchor can of course
    defeat this check; callers may not take either trust root from the script.
    """
    manifest = freeze_script_manifest(proposal, slot, observations)
    digest = _hash(manifest)
    if not isinstance(anchor_manifest_sha256, str) or not HEX.fullmatch(anchor_manifest_sha256):
        raise ScriptContinuityError("External immutable manifest anchor required")
    if digest != anchor_manifest_sha256:
        raise ScriptContinuityError("Content diverges from external anchored digest")
    if (not isinstance(registry, Mapping) or not isinstance(seal, DetachedScriptSeal)
            or not isinstance(seal.claim, ScriptSealClaim)):
        raise ScriptContinuityError("Detached seal and external trust registry required")
    if (not isinstance(excluded_creator_and_publisher_ids, frozenset)
            or not excluded_creator_and_publisher_ids
            or any(not isinstance(x, str) or not ID.fullmatch(x)
                   for x in excluded_creator_and_publisher_ids)):
        raise ScriptContinuityError("Authenticated creator/publisher exclusion required")
    claim = seal.claim
    if (claim.purpose != PURPOSE
            or claim.manifest_sha256 != digest
            or claim.episode_id != manifest["episode_id"]
            or claim.channel_id != CHANNEL_ID
            or claim.release_slot != manifest["release_slot"]
            or claim.release_utc != manifest["release_utc"]):
        raise ScriptContinuityError("Signed claim not bound to this exact FlowMinute script")
    if (not isinstance(claim.custodian_id, str) or not ID.fullmatch(claim.custodian_id)
            or not isinstance(claim.key_id, str) or not ID.fullmatch(claim.key_id)
            or claim.custodian_id in excluded_creator_and_publisher_ids):
        raise ScriptContinuityError("Missing or untrusted independent signer identity")
    root = registry.get(claim.custodian_id)
    if (not isinstance(root, TrustedScriptCustodian)
            or root.active is not True
            or root.custodian_id != claim.custodian_id
            or root.key_id != claim.key_id):
        raise ScriptContinuityError("Custodian not externally authorized")
    at = now if now is not None else datetime.now(timezone.utc)
    if not isinstance(at, datetime) or at.tzinfo is None or at.utcoffset() is None:
        raise ScriptContinuityError("Verifier requires a timezone-aware clock")
    at = at.astimezone(timezone.utc)
    issued, expires = _parse_utc(claim.issued_at_utc), _parse_utc(claim.expires_at_utc)
    if (not timedelta(0) <= at - issued <= timedelta(hours=24)
            or not timedelta(0) < expires - issued <= timedelta(hours=48)
            or expires <= at):
        raise ScriptContinuityError("Expired, future or stale continuity seal")
    try:
        public = base64.b64decode(root.public_key_ed25519_b64, validate=True)
        signature = base64.b64decode(seal.signature_ed25519_b64, validate=True)
        if len(public) != 32 or len(signature) != 64:
            raise ScriptContinuityError("Invalid Ed25519 public key or signature length")
        key = Ed25519PublicKey.from_public_bytes(public)
        key.verify(signature, _json_bytes(asdict(claim)))
    except (InvalidSignature, binascii.Error, TypeError, ValueError) as exc:
        raise ScriptContinuityError("Detached continuity signature invalid") from exc
    return {
        "schema_version": 1,
        "status": STATUS,
        "manifest_sha256": digest,
        "episode_id": manifest["episode_id"],
        "release_slot": manifest["release_slot"],
        "custodian_id": claim.custodian_id,
        "authenticity_of_external_trust_root_verified_by_software": False,
        "external_append_only_ledger_deployed": False,
        "immutable_content_binding_checked": True,
        "claim_level_independent_fact_review_complete": False,
        "human_editorial_review_complete": False,
        "rights_and_originality_review_complete": False,
        "media_render_enabled": False,
        "youtube_upload_enabled": False,
        "youtube_schedule_enabled": False,
        "release_authorized": False,
        "next_gate": "Independent source-level fact, script originality/rights and owner-controlled signing & ledger",
    }
