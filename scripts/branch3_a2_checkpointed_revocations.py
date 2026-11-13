"""A2 CLIVOX per-receipt revocation hash-chain and signed checkpoint PREVIEW.

Pure offline verifier; no real trusted reviewer/checkpoint keys, durable
anchor, authenticated creator license, private vault, network or media APIs.
Even a perfectly checked synthetic snapshot is NOT proof of rights or of the
absence of newer revocations. Every output keeps acquisition/publishing OFF.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timedelta, timezone

from scripts.branch3_a2_review_receipt import (
    CLIVOX_ID, SHA, REVIEW_DOMAIN, REVOKE_DOMAIN, ReviewDenied, canonical,
    parse_utc, require, review_subject, revocation_subject, verify_ed25519,
    verify_offline_receipt_preview,
)

LEDGER_ID = "clivox_a2_receipt_revocations_v1"
ENTRY_DOMAIN = b"CLIVOX-A2-REVOCATION-CHAIN-ENTRY-V1\n"
CHECKPOINT_DOMAIN = b"CLIVOX-A2-REVOCATION-CHECKPOINT-V1\n"
GENESIS_HEAD_SHA256 = hashlib.sha256(
    b"CLIVOX-A2-REVOCATION-CHAIN-GENESIS-V1\n"
).hexdigest()
MAX_ENTRIES = 200
MAX_CHECKPOINT_AGE = timedelta(minutes=15)
SNAPSHOT_FIELDS = frozenset({
    "schema_version", "channel_id", "ledger_id", "receipt_id",
    "entries", "checkpoint", "checkpoint_signature_base64"
})
ENTRY_FIELDS = frozenset({
    "sequence", "previous_head_sha256", "event",
    "revocation_signature_base64", "entry_sha256"
})
CHECKPOINT_FIELDS = frozenset({
    "schema_version", "channel_id", "ledger_id", "receipt_id",
    "sequence", "head_sha256", "signed_at_utc", "checkpoint_key_id"
})
ANCHOR_FIELDS = frozenset({"sequence", "head_sha256"})


def hash_entry(*, sequence: int, previous_head_sha256: str,
               event: dict, revocation_signature_base64: str) -> str:
    """Deterministic append-only-chain hash (a signer is still required)."""
    require(type(sequence) is int and 1 <= sequence <= MAX_ENTRIES,
            "CHAIN_SEQUENCE")
    require(type(previous_head_sha256) is str
            and SHA.fullmatch(previous_head_sha256) is not None,
            "CHAIN_PREVIOUS_DIGEST")
    require(type(event) is dict
            and type(revocation_signature_base64) is str
            and 0 < len(revocation_signature_base64) <= 120,
            "CHAIN_EVENT_OR_SIGNATURE")
    body = {
        "sequence": sequence,
        "previous_head_sha256": previous_head_sha256,
        "event": event,
        "revocation_signature_base64": revocation_signature_base64,
    }
    return hashlib.sha256(ENTRY_DOMAIN + canonical(body)).hexdigest()


def checkpoint_subject(checkpoint: dict) -> bytes:
    """Canonical complete-head attestation, mathematically signed offline."""
    require(type(checkpoint) is dict
            and set(checkpoint) == CHECKPOINT_FIELDS,
            "CHECKPOINT_EXACT_FIELDS")
    require(checkpoint["schema_version"] == 1
            and checkpoint["channel_id"] == CLIVOX_ID
            and checkpoint["ledger_id"] == LEDGER_ID,
            "CHECKPOINT_CHANNEL_OR_LEDGER")
    require(type(checkpoint["receipt_id"]) is str
            and checkpoint["receipt_id"].startswith("clivox_review_")
            and len(checkpoint["receipt_id"]) <= 90,
            "CHECKPOINT_RECEIPT_ID")
    require(type(checkpoint["sequence"]) is int
            and 0 <= checkpoint["sequence"] <= MAX_ENTRIES,
            "CHECKPOINT_SEQUENCE")
    require(type(checkpoint["head_sha256"]) is str
            and SHA.fullmatch(checkpoint["head_sha256"]) is not None,
            "CHECKPOINT_HEAD")
    key_id = checkpoint["checkpoint_key_id"]
    require(type(key_id) is str and 5 <= len(key_id) <= 56
            and key_id[0].islower()
            and all(ch.islower() or ch.isdigit() or ch in "_-" for ch in key_id),
            "CHECKPOINT_KEY_ID")
    parse_utc(checkpoint["signed_at_utc"])
    return CHECKPOINT_DOMAIN + canonical(checkpoint)


def validate_anchor(trusted_floor: dict) -> None:
    """Only a shape check. Caller must source it from independent durable trust."""
    require(type(trusted_floor) is dict
            and set(trusted_floor) == ANCHOR_FIELDS,
            "INDEPENDENT_FLOOR_REQUIRED")
    require(type(trusted_floor["sequence"]) is int
            and 0 <= trusted_floor["sequence"] <= MAX_ENTRIES,
            "INVALID_FLOOR_SEQUENCE")
    require(type(trusted_floor["head_sha256"]) is str
            and SHA.fullmatch(trusted_floor["head_sha256"]) is not None,
            "INVALID_FLOOR_HASH")
    if trusted_floor["sequence"] == 0:
        require(trusted_floor["head_sha256"] == GENESIS_HEAD_SHA256,
                "INVALID_GENESIS_FLOOR")


def verify_checkpointed_receipt_preview(
    *, case: dict, receipt: dict, review_signature_b64: str,
    reviewer_public_key: bytes, revocation_public_key: bytes,
    checkpoint_public_key: bytes, snapshot: dict, trusted_floor: dict,
    now: datetime
) -> dict:
    """Mathematical chain/signer checks only, with a caller-supplied anchor.

    Cannot authenticate identity of keys or the freshness/completeness of a
    remote ledger: trusted_floor and all public keys must eventually come from
    a separate owner-audited, persistent trust system.
    """
    require(type(now) is datetime and now.tzinfo is not None
            and now.utcoffset() is not None, "NAIVE_CLOCK")
    validate_anchor(trusted_floor)
    # Review claims and exact original A1/A2 source identity are validated
    # independently by the pre-existing Ed25519 preview.
    base = verify_offline_receipt_preview(
        case=case, receipt=receipt, signature_b64=review_signature_b64,
        reviewer_public_key=reviewer_public_key, revocations=[],
        revocation_public_key=revocation_public_key,
        now=now, last_trusted_revocation_sequence=0
    )
    require(type(snapshot) is dict
            and set(snapshot) == SNAPSHOT_FIELDS,
            "SNAPSHOT_EXACT_FIELDS")
    require(snapshot["schema_version"] == 1
            and snapshot["channel_id"] == CLIVOX_ID
            and snapshot["ledger_id"] == LEDGER_ID
            and snapshot["receipt_id"] == receipt["receipt_id"],
            "SNAPSHOT_TARGET")
    entries = snapshot["entries"]
    require(type(entries) is list and len(entries) <= MAX_ENTRIES,
            "SNAPSHOT_ENTRIES")
    heads = [GENESIS_HEAD_SHA256]
    for position, entry in enumerate(entries, start=1):
        require(type(entry) is dict and set(entry) == ENTRY_FIELDS,
                "ENTRY_FIELDS")
        require(type(entry["sequence"]) is int
                and entry["sequence"] == position,
                "NONCONTIGUOUS_OR_REPLAYED_SEQUENCE")
        require(entry["previous_head_sha256"] == heads[-1],
                "BROKEN_PREVIOUS_HASH")
        event = entry["event"]
        subject = revocation_subject(receipt, event)
        require(event["revocation_sequence"] == position,
                "MISMATCHED_EVENT_SEQUENCE")
        require(parse_utc(event["revoked_at_utc"])
                <= now.astimezone(timezone.utc),
                "FUTURE_TOMBSTONE")
        require(verify_ed25519(
            subject, entry["revocation_signature_base64"],
            revocation_public_key, REVOKE_DOMAIN
        ), "BAD_REVOCATION_SIGNATURE")
        expected = hash_entry(
            sequence=position, previous_head_sha256=heads[-1],
            event=event,
            revocation_signature_base64=entry["revocation_signature_base64"],
        )
        require(entry["entry_sha256"] == expected,
                "CHANGED_OR_REMOVED_CHAIN_ENTRY")
        heads.append(expected)
    checkpoint = snapshot["checkpoint"]
    signed = checkpoint_subject(checkpoint)
    require(checkpoint["receipt_id"] == receipt["receipt_id"]
            and checkpoint["sequence"] == len(entries)
            and checkpoint["head_sha256"] == heads[-1],
            "CHECKPOINT_NOT_MATCHING_COMPLETE_CHAIN")
    signed_time = parse_utc(checkpoint["signed_at_utc"])
    age = now.astimezone(timezone.utc) - signed_time
    require(timedelta(0) <= age <= MAX_CHECKPOINT_AGE,
            "STALE_OR_FUTURE_CHECKPOINT")
    require(verify_ed25519(
        signed, snapshot["checkpoint_signature_base64"],
        checkpoint_public_key, CHECKPOINT_DOMAIN,
    ), "BAD_CHECKPOINT_SIGNATURE")
    floor_sequence = trusted_floor["sequence"]
    require(floor_sequence <= len(entries)
            and heads[floor_sequence] == trusted_floor["head_sha256"],
            "ROLLBACK_OR_FORK_FROM_SUPPLIED_FLOOR")
    # A tombstone is permanent: no later signed checkpoint can restore rights.
    require(len(entries) == 0, "TARGET_RECEIPT_REVOKED")
    return {
        "stage": "A2_CHECKPOINTED_REVOCATION_CHAIN_OFFLINE_PREVIEW_ONLY",
        "channel_id": CLIVOX_ID,
        "synthetic_receipt_signature_mathematically_valid": base["review_signature_math_passed"],
        "synthetic_checkpoint_signature_mathematically_valid": True,
        "supplied_hash_chain_mathematically_valid": True,
        "supplied_independent_floor_matched": True,
        "supplied_revocation_event_count": len(entries),
        "real_independently_enrolled_keys": False,
        "real_external_durable_floor_verified": False,
        "remote_ledger_freshness_and_completeness_verified": False,
        "authentic_creator_license_verified": False,
        "source_media_download_authorized": False,
        "creator_registry_update_authorized": False,
        "youtube_upload_authorized": False,
        "youtube_schedule_authorized": False,
        "youtube_publish_authorized": False,
        "actual_external_api_calls": 0,
        "note": "Verified only caller-provided math; not legal or remote-ledger authority."
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("fixture",), default="fixture")
    parser.parse_args()
    result = {
        "stage": "A2_CHECKPOINTED_REVOCATION_LEDGER_NO_TRUST_FIXTURE",
        "channel_id": CLIVOX_ID,
        "real_checkpoint_keys_enrolled": False,
        "actual_revocation_snapshot_provided": False,
        "real_external_durable_floor_verified": False,
        "authentic_creator_license_verified": False,
        "real_live_checks_executed": False,
        "source_media_download_authorized": False,
        "youtube_upload_authorized": False,
        "youtube_schedule_authorized": False,
        "youtube_publish_authorized": False,
        "actual_external_api_calls": 0,
    }
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
