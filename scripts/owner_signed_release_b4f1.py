"""B4f1 verify an OFFLINE owner Ed25519 signature over ONE exact release.

This verifier grants NO YouTube permissions or independent fact/rights attestation.
Private signing keys MUST NEVER enter the repo, workflow, or GitHub Actions.
The public verification key is separately configured in the protected
'youtube-production' environment after independent owner enrollment.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import re

SCHEMA = "FLOWMINUTE_OWNER_ED25519_EXACT_RELEASE_V1"
INTENT = "ONE_EXACT_VIDEO_PRIVATE_FUTURE_SCHEDULE"
CHECKS = (
    "human_voice_approved",
    "exact_captions_approved",
    "rights_cleared",
    "factual_review_approved",
    "final_video_approved",
    "owner_publish_authorized",
)
PAYLOAD_KEYS = {
    "intent", "channel_id", "episode_id", "mp4_sha256", "srt_sha256",
    "thumbnail_sha256", "metadata_sha256", "publish_at_utc",
    "signed_at_utc", "expires_at_utc", "checks",
}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
HEX128 = re.compile(r"[0-9a-f]{128}\Z")
UTC_TIME = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\Z")
CHANNEL = re.compile(r"UC[A-Za-z0-9_-]{22}\Z")
EPISODE = re.compile(r"[A-Za-z0-9_-]{8,100}\Z")


class OwnerSignatureRejected(ValueError):
    """No complete authenticated, content-locked owner release declaration."""


def _need(ok: bool, message: str) -> None:
    if not ok:
        raise OwnerSignatureRejected(message)


def _utc(value: object) -> datetime:
    _need(type(value) is str and UTC_TIME.fullmatch(value) is not None,
          "Owner signed timestamp must be exact whole-second UTC-Z")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc)
    except ValueError as exc:
        raise OwnerSignatureRejected("Invalid signed UTC calendar date") from exc


def _hash(value: object) -> str:
    _need(type(value) is str and HEX64.fullmatch(value) is not None,
          "Exact lowercase SHA256 is mandatory")
    return value


def canonical_owner_release_bytes(payload: dict) -> bytes:
    """Stable canonical signed message bytes; all signed fields have a schema."""
    _need(type(payload) is dict and set(payload) == PAYLOAD_KEYS,
          "Signed release payload missing or has extra keys")
    _need(payload.get("intent") == INTENT, "Only private future single-video intent")
    _need(type(payload.get("channel_id")) is str
          and CHANNEL.fullmatch(payload["channel_id"]) is not None,
          "Invalid intended owner channel ID")
    _need(type(payload.get("episode_id")) is str
          and EPISODE.fullmatch(payload["episode_id"]) is not None,
          "Invalid signed episode ID")
    for key in ("mp4_sha256","srt_sha256","thumbnail_sha256","metadata_sha256"):
        _hash(payload.get(key))
    for key in ("publish_at_utc","signed_at_utc","expires_at_utc"):
        _utc(payload.get(key))
    checks = payload.get("checks")
    _need(type(checks) is dict and set(checks) == set(CHECKS)
          and all(checks.get(key) is True for key in CHECKS),
          "Owner signature must individually affirm all six review decisions")
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def verify_owner_release_signature(
    approval: dict, *,
    public_key_hex: str | None,
    channel_id: str, episode_id: str, mp4_sha256: str,
    srt_sha256: str, thumbnail_sha256: str, metadata_sha256: str,
    publish_at_utc: str, now: datetime,
) -> dict:
    """Verify signature and EXACT media/time/context before any videos.insert.

    Private key generation/signing happens outside this repo and Actions.
    This is proof a designated key signed exact data, NOT proof that its
    signatory did the intended human viewing/fact/license review.
    """
    _need(type(approval) is dict and
          approval.get("owner_rejected_current_candidate") is not True,
          "Rejected or nonexistent owner release")
    _need(type(public_key_hex) is str
          and HEX64.fullmatch(public_key_hex) is not None,
          "Protected environment has no trusted Ed25519 public key")
    _need(type(now) is datetime and now.tzinfo is not None
          and now.utcoffset() is not None, "Aware trusted clock required")
    envelope = approval.get("signed_owner_release")
    _need(type(envelope) is dict
          and set(envelope) == {"schema","payload","signature_hex"}
          and envelope.get("schema") == SCHEMA,
          "Missing strict Ed25519 owner release envelope")
    payload = envelope["payload"]
    data = canonical_owner_release_bytes(payload)
    sign_hex = envelope["signature_hex"]
    _need(type(sign_hex) is str and HEX128.fullmatch(sign_hex) is not None,
          "Missing 64-byte Ed25519 signature")
    _need(all(approval.get(key) is True for key in CHECKS),
          "Mutable legacy owner checkboxes must also agree with signature")
    expected = {
        "channel_id":channel_id, "episode_id":episode_id,
        "mp4_sha256":_hash(mp4_sha256),
        "srt_sha256":_hash(srt_sha256),
        "thumbnail_sha256":_hash(thumbnail_sha256),
        "metadata_sha256":_hash(metadata_sha256),
        "publish_at_utc":publish_at_utc,
    }
    for key, value in expected.items():
        _need(payload[key] == value, "Signed artifact/channel/schedule mismatch")
    signed = _utc(payload["signed_at_utc"])
    expires = _utc(payload["expires_at_utc"])
    due = _utc(payload["publish_at_utc"])
    clock = now.astimezone(timezone.utc)
    _need(signed <= clock + timedelta(minutes=5) and
          expires >= clock and
          signed < expires <= signed + timedelta(hours=72) and
          due > clock + timedelta(minutes=15) and
          due <= signed + timedelta(days=30),
          "Expired, future forged, stale or unsafe signed release window")
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PublicKey,
        )
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex)).verify(
            bytes.fromhex(sign_hex), data,
        )
    except (ImportError, ValueError, InvalidSignature, TypeError) as exc:
        raise OwnerSignatureRejected(
            "Owner public-key verification failed; NO upload permitted"
        ) from exc
    return {
        "status": "B4F1_EXACT_OWNER_ED25519_SIGNATURE_CHECK_PASSED_ONLY",
        "owner_release_key_sha256": sha256(bytes.fromhex(public_key_hex)).hexdigest(),
        "signed_exact_bytes_channel_and_schedule_verified": True,
        "independent_source_facts_or_rights_review_proven": False,
        "actual_owner_full_video_watch_independently_proven": False,
        "youtube_upload_authorized_by_this_function": False,
    }
