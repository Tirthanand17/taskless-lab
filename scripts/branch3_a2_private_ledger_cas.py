"""CLIVOX A2: private GitHub Contents revocation-ledger CAS protocol (OFFLINE).

Implements bounded, signed append-only global revocation journal and a strict
GitHub Contents API blob-SHA compare-and-swap *request preview*. The CLI
cannot perform network calls, create a vault, acquire rights or write media.
Future production wiring must authenticate private repository metadata,
pin a genuinely external nonrollbackable journal anchor, verify signer role,
and obtain the owner's distinct protected-environment approval.
"""
from __future__ import annotations

import argparse
import base64
import binascii
from datetime import datetime, timezone
import hashlib
import json
import re

from scripts.branch3_a2_review_receipt import (
    CLIVOX_ID, SHA, REASONS, REVOKE_FIELDS, REVOKE_DOMAIN,
    ReviewDenied, canonical, parse_utc, require, verify_ed25519
)
from scripts.branch3_a2_checkpointed_revocations import GENESIS_HEAD_SHA256
from scripts.branch3_media_storage_preflight import inspect_private_repo_metadata, StorageDenied

OWNER = "Tirthanand17"
PUBLIC_REPO = OWNER + "/taskless-lab"
FILE_PATH = "clivox-private/rights/revocation-journal-v1.json"
LEDGER_ID = "clivox_a2_global_revocation_journal_v1"
ENTRY_DOMAIN = b"CLIVOX-A2-GLOBAL-REVOCATION-ENTRY-V1\n"
MAX_ENTRIES = 250
MAX_BYTES = 220_000
GIT_SHA = re.compile(r"[0-9a-f]{40}\Z")
PRIVATE_REPO = re.compile(r"clivox-[a-z0-9][a-z0-9-]{3,48}[a-z0-9]\Z")
RECEIPT_ID = re.compile(r"clivox_review_[a-z0-9_-]{10,75}\Z")
LEDGER_FIELDS = frozenset({
    "schema_version", "channel_id", "ledger_id", "sequence",
    "head_sha256", "entries"
})
ENTRY_FIELDS = frozenset({
    "previous_head_sha256", "event", "revocation_signature_base64", "entry_sha256"
})
ANCHOR_FIELDS = frozenset({"sequence", "head_sha256"})


def canonical_ledger(ledger: dict) -> bytes:
    require(type(ledger) is dict, "LEDGER_NOT_OBJECT")
    raw = canonical(ledger) + b"\n"
    require(len(raw) <= MAX_BYTES, "LEDGER_OVERSIZED")
    return raw


def git_blob_sha(raw: bytes) -> str:
    require(type(raw) is bytes and len(raw) <= MAX_BYTES,
            "UNSAFE_BLOB_BYTES")
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw
    ).hexdigest()


def initial_ledger() -> dict:
    return {
        "schema_version": 1,
        "channel_id": CLIVOX_ID,
        "ledger_id": LEDGER_ID,
        "sequence": 0,
        "head_sha256": GENESIS_HEAD_SHA256,
        "entries": [],
    }


def validate_revocation_event(event: dict, *, expected_sequence: int,
                              now: datetime) -> bytes:
    require(type(event) is dict and set(event) == REVOKE_FIELDS,
            "EVENT_FIELDS")
    require(event["schema_version"] == 1
            and event["channel_id"] == CLIVOX_ID,
            "WRONG_CHANNEL")
    require(type(event["revocation_sequence"]) is int
            and event["revocation_sequence"] == expected_sequence
            and 1 <= expected_sequence <= MAX_ENTRIES,
            "WRONG_EVENT_SEQUENCE")
    require(type(event["receipt_id"]) is str
            and RECEIPT_ID.fullmatch(event["receipt_id"]) is not None,
            "BAD_RECEIPT_ID")
    require(type(event["case_sha256"]) is str
            and SHA.fullmatch(event["case_sha256"]) is not None,
            "BAD_CASE_DIGEST")
    require(event["reason_code"] in REASONS, "BAD_REASON")
    require(parse_utc(event["revoked_at_utc"])
            <= now.astimezone(timezone.utc),
            "FUTURE_TOMBSTONE")
    return REVOKE_DOMAIN + canonical(event)


def entry_sha(*, prev: str, event: dict, signature: str) -> str:
    require(type(prev) is str and SHA.fullmatch(prev) is not None,
            "PREVIOUS_HASH")
    require(type(signature) is str and len(signature) <= 120
            and len(signature) > 0, "SIGNATURE_SIZE")
    return hashlib.sha256(ENTRY_DOMAIN + canonical({
        "previous_head_sha256": prev,
        "event": event,
        "revocation_signature_base64": signature,
    })).hexdigest()


def validate_floor(floor: dict) -> None:
    require(type(floor) is dict and set(floor) == ANCHOR_FIELDS,
            "EXTERNAL_ANCHOR_REQUIRED")
    require(type(floor["sequence"]) is int
            and 0 <= floor["sequence"] <= MAX_ENTRIES,
            "ANCHOR_SEQUENCE")
    require(type(floor["head_sha256"]) is str
            and SHA.fullmatch(floor["head_sha256"]) is not None,
            "ANCHOR_DIGEST")
    if floor["sequence"] == 0:
        require(floor["head_sha256"] == GENESIS_HEAD_SHA256,
                "ANCHOR_GENESIS")


def verify_journal(
    ledger: dict, *, revocation_public_key: bytes, trusted_floor: dict,
    now: datetime
) -> dict:
    """Verify exactly supplied bytes, Ed25519 signatures and caller-supplied pin.

    Does not authenticate the signer or floor, or prove remote completeness.
    """
    require(type(now) is datetime and now.tzinfo is not None
            and now.utcoffset() is not None, "CLOCK")
    validate_floor(trusted_floor)
    require(type(ledger) is dict and set(ledger) == LEDGER_FIELDS,
            "LEDGER_FIELDS")
    require(ledger["schema_version"] == 1
            and ledger["channel_id"] == CLIVOX_ID
            and ledger["ledger_id"] == LEDGER_ID,
            "LEDGER_IDENTITY")
    entries = ledger["entries"]
    require(type(entries) is list and len(entries) <= MAX_ENTRIES,
            "JOURNAL_LENGTH")
    require(type(ledger["sequence"]) is int
            and ledger["sequence"] == len(entries),
            "JOURNAL_SEQUENCE")
    canonical_ledger(ledger)
    seen = set()
    heads = [GENESIS_HEAD_SHA256]
    for seq, entry in enumerate(entries, 1):
        require(type(entry) is dict and set(entry) == ENTRY_FIELDS,
                "ENTRY_FIELDS")
        require(entry["previous_head_sha256"] == heads[-1],
                "HASH_CHAIN_BROKEN")
        event = entry["event"]
        payload = validate_revocation_event(
            event, expected_sequence=seq, now=now
        )
        receipt_id = event["receipt_id"]
        require(receipt_id not in seen, "REVOKED_RECEIPT_REPEATED")
        seen.add(receipt_id)
        require(verify_ed25519(
            payload, entry["revocation_signature_base64"],
            revocation_public_key, REVOKE_DOMAIN,
        ), "TOMBSTONE_SIGNATURE")
        expect = entry_sha(
            prev=heads[-1], event=event,
            signature=entry["revocation_signature_base64"]
        )
        require(entry["entry_sha256"] == expect, "ENTRY_SHA_TAMPERED")
        heads.append(expect)
    require(ledger["head_sha256"] == heads[-1],
            "JOURNAL_HEAD_INCORRECT")
    floor_seq = trusted_floor["sequence"]
    require(floor_seq <= len(entries)
            and heads[floor_seq] == trusted_floor["head_sha256"],
            "STALE_OR_FORKED_VS_EXTERNAL_ANCHOR")
    return {
        "stage": "A2_PRIVATE_JOURNAL_CAS_PREVIEW",
        "channel_id": CLIVOX_ID,
        "supplied_events_signature_math_checked": len(entries),
        "supplied_head_chain_valid": True,
        "supplied_floor_matches": True,
        "real_issuer_enrollment_verified": False,
        "real_external_anchor_durability_verified": False,
        "complete_remote_journal_verified": False,
        "authentic_creator_licenses_verified": 0,
        "source_download_authorized": False,
        "private_media_access_authorized": False,
        "youtube_upload_authorized": False,
        "youtube_publish_authorized": False,
        "actual_github_write_calls": 0,
    }


def prepare_append(
    ledger: dict, *, signed_event: dict,
    revocation_public_key: bytes, trusted_floor: dict, now: datetime
) -> dict:
    """Add a signed tombstone in memory only; real GitHub PUT not performed."""
    verify_journal(
        ledger, revocation_public_key=revocation_public_key,
        trusted_floor=trusted_floor, now=now,
    )
    require(type(signed_event) is dict
            and set(signed_event) == {"event", "signature_base64"},
            "SIGNED_EVENT_FIELDS")
    event = signed_event["event"]
    signature = signed_event["signature_base64"]
    next_seq = ledger["sequence"] + 1
    payload = validate_revocation_event(
        event, expected_sequence=next_seq, now=now
    )
    require(all(
        item["event"]["receipt_id"] != event["receipt_id"]
        for item in ledger["entries"]
    ), "ALREADY_REVOKED")
    require(verify_ed25519(
        payload, signature, revocation_public_key, REVOKE_DOMAIN,
    ), "TOMBSTONE_SIGNATURE")
    prev = ledger["head_sha256"]
    h = entry_sha(prev=prev, event=event, signature=signature)
    updated = {
        **ledger, "sequence": next_seq, "head_sha256": h,
        "entries": [*ledger["entries"], {
            "previous_head_sha256": prev,
            "event": event, "revocation_signature_base64": signature,
            "entry_sha256": h,
        }],
    }
    verify_journal(
        updated, revocation_public_key=revocation_public_key,
        trusted_floor=trusted_floor, now=now,
    )
    return updated


def validate_private_target(repo_metadata: dict, vault_name: str) -> None:
    """Shape validation only; production MUST source via authenticated GET."""
    require(type(vault_name) is str
            and PRIVATE_REPO.fullmatch(vault_name) is not None,
            "VAULT_NAME")
    require(OWNER + "/" + vault_name != PUBLIC_REPO, "PUBLIC_CONTROLLER")
    try:
        inspect_private_repo_metadata(
            repo_metadata, expected_full_name=OWNER + "/" + vault_name
        )
    except (StorageDenied, KeyError, TypeError, ValueError):
        raise ReviewDenied("CLIVOX_A2_REVIEW_DENIED_NOT_OWNER_PRIVATE_VAULT") from None


def decode_github_contents(reply: dict) -> tuple[dict, str]:
    """Strict existing GitHub Contents GET response, including Git blob SHA."""
    require(type(reply) is dict and reply.get("type") == "file"
            and reply.get("path") == FILE_PATH
            and reply.get("name") == "revocation-journal-v1.json"
            and reply.get("encoding") == "base64",
            "UNEXPECTED_GITHUB_CONTENT_TYPE")
    sha = reply.get("sha")
    require(type(sha) is str and GIT_SHA.fullmatch(sha) is not None,
            "MISSING_GITHUB_BLOB_SHA")
    encoded = reply.get("content")
    require(type(encoded) is str and 0 < len(encoded) <= MAX_BYTES * 2,
            "ENCODED_CONTENT_BOUNDS")
    try:
        raw = base64.b64decode(encoded, validate=False)
        require(0 < len(raw) <= MAX_BYTES, "RAW_CONTENT_BOUNDS")
        require(type(reply.get("size")) is int and reply["size"] == len(raw),
                "GITHUB_BLOB_SIZE")
        require(git_blob_sha(raw) == sha, "GITHUB_BLOB_SHA")
        data = json.loads(raw)
    except (binascii.Error, UnicodeDecodeError, ValueError, TypeError):
        raise ReviewDenied("CLIVOX_A2_REVIEW_DENIED_GITHUB_BLOB_DECODE") from None
    require(type(data) is dict, "CONTENTS_NOT_JSON_OBJECT")
    return data, sha


def build_cas_put_body(*, original_sha: str, new_ledger: dict) -> dict:
    """Exact GitHub Contents REST PUT contract; caller does NOT get a write."""
    require(type(original_sha) is str
            and GIT_SHA.fullmatch(original_sha) is not None, "CAS_SHA_REQUIRED")
    raw = canonical_ledger(new_ledger)
    return {
        "message": "clivox: append owner-reviewed signed revocation tombstone",
        "content": base64.b64encode(raw).decode("ascii"),
        "sha": original_sha,
        "branch": "main",
    }


def simulate_github_cas(
    *, server_blob_sha: str, proposed_put: dict
) -> str:
    """Pure deterministic stale-write failure. Not an authenticated GitHub API."""
    require(type(server_blob_sha) is str
            and GIT_SHA.fullmatch(server_blob_sha) is not None,
            "SERVER_SHA")
    require(type(proposed_put) is dict
            and set(proposed_put) == {"message", "content", "sha", "branch"}
            and proposed_put["branch"] == "main"
            and proposed_put["sha"] == server_blob_sha,
            "GITHUB_CAS_STALE_OR_REJECTED")
    raw = base64.b64decode(proposed_put["content"], validate=True)
    return git_blob_sha(raw)


def fixture_report() -> dict:
    return {
        "stage": "A2_PRIVATE_LEDGER_CAS_UNCONFIGURED",
        "channel_id": CLIVOX_ID,
        "git_contents_read_and_cas_contract_implemented": True,
        "real_private_ledger_file_present": False,
        "owner_approved_private_storage_provisioned": False,
        "live_github_contents_put_configured": False,
        "trusted_signer_enrolled": False,
        "real_external_checkpoint_pin_enrolled": False,
        "real_license_grants_verified": 0,
        "creator_source_acquisition_authorized": False,
        "youtube_upload_authorized": False,
        "youtube_schedule_authorized": False,
        "youtube_publish_authorized": False,
        "github_api_calls": 0,
        "youtube_api_calls": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("fixture",), default="fixture")
    parser.parse_args()
    print(json.dumps(fixture_report(), sort_keys=True))


if __name__ == "__main__":
    main()
