"""CLIVOX A8: cross-run GitHub Contents upload-attempt ledger CAS CONTRACT.

Pure offline protocol: verifies a global append-only event journal, exact release
identity and blob SHA, builds a prior-blob-SHA update request, simulates stale
writer conflicts and quarantines unknown responses. NO live transport, remote
storage, Google API, source media, signer enrollment or production upload.
A mock CAS outcome is not proof GitHub's remote consistency guarantees.
"""
from __future__ import annotations

import argparse
import base64
import binascii
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from scripts.branch3_a8_private_first_dryrun import (
    CLIVOX, SHA, ID, DryRunBlocked, candidate_attempt_key, utc
)
from scripts.branch3_a2_private_ledger_cas import (
    git_blob_sha, validate_private_target, GIT_SHA
)

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "branch3/a8/private-cas-policy.json"
FILE_PATH = "clivox-private/upload-control/attempt-ledger-v1.json"
LEDGER_ID = "clivox_a8_private_upload_attempts_v1"
GENESIS = hashlib.sha256(b"CLIVOX-A8-PRIVATE-ATTEMPT-GENESIS-V1\n").hexdigest()
DOMAIN = b"CLIVOX-A8-PRIVATE-ATTEMPT-EVENT-V1\n"
MAX_EVENTS = 250
MAX_BYTES = 180_000
STATE_RESERVED = "RESERVED_NO_YOUTUBE_NETWORK"
STATE_UNKNOWN = "UNKNOWN_REMOTE_STATE_NEVER_BLIND_RETRY"
KINDS = frozenset(("RESERVE_SYNTHETIC", "MARK_UNKNOWN_NO_RETRY"))
LEDGER_FIELDS = frozenset((
    "schema_version", "channel_id", "ledger_id", "sequence",
    "head_sha256", "events"
))
EVENT_FIELDS = frozenset((
    "sequence", "prev_sha256", "kind", "attempt_key", "release_id",
    "media_sha256", "metadata_sha256", "rights_evidence_sha256",
    "recorded_at_utc", "event_sha256"
))
ANCHOR_FIELDS = frozenset(("sequence", "head_sha256"))


class PrivateCASBlocked(DryRunBlocked):
    """Cannot trust / reserve / release: halt without a YouTube API request."""


def require(ok: bool, label: str) -> None:
    if not ok:
        raise PrivateCASBlocked("CLIVOX_A8_PRIVATE_CAS_DENIED_" + label)


def canonical(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def bytes_for_ledger(ledger: dict) -> bytes:
    require(type(ledger) is dict, "LEDGER_TYPE")
    raw = canonical(ledger) + b"\n"
    require(0 < len(raw) <= MAX_BYTES, "LEDGER_BOUNDS")
    return raw


def new_ledger() -> dict:
    return {
        "schema_version": 1, "channel_id": CLIVOX,
        "ledger_id": LEDGER_ID, "sequence": 0,
        "head_sha256": GENESIS, "events": [],
    }


def validate_anchor(anchor: dict) -> None:
    require(type(anchor) is dict and set(anchor) == ANCHOR_FIELDS, "ANCHOR_FIELDS")
    require(type(anchor["sequence"]) is int
            and 0 <= anchor["sequence"] <= MAX_EVENTS,
            "ANCHOR_SEQUENCE")
    require(type(anchor["head_sha256"]) is str
            and SHA.fullmatch(anchor["head_sha256"]) is not None,
            "ANCHOR_HEAD")
    if anchor["sequence"] == 0:
        require(anchor["head_sha256"] == GENESIS, "ANCHOR_GENESIS")


def time_utc(value: object) -> datetime:
    require(type(value) is str
            and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value) is not None,
            "TIMESTAMP_FORMAT")
    try:
        return utc(value)
    except DryRunBlocked:
        raise PrivateCASBlocked("CLIVOX_A8_PRIVATE_CAS_DENIED_TIMESTAMP") from None


def event_hash(event: dict) -> str:
    require(type(event) is dict and set(event) == EVENT_FIELDS - {"event_sha256"},
            "EVENT_BODY_FIELDS")
    return hashlib.sha256(DOMAIN + canonical(event)).hexdigest()


def verify_ledger(ledger: dict, *, anchor: dict, now: datetime) -> dict:
    """Full no-write canonical event replay and caller-supplied anchor check.

    Does NOT independently prove the remote repo was private, the supplied
    anchor is durable, or any signed media / creator license exists.
    """
    require(type(now) is datetime and now.tzinfo is not None
            and now.utcoffset() is not None, "NOW_AWARE")
    validate_anchor(anchor)
    require(type(ledger) is dict and set(ledger) == LEDGER_FIELDS,
            "LEDGER_FIELDS")
    require(type(ledger["schema_version"]) is int
            and ledger["schema_version"] == 1
            and ledger["channel_id"] == CLIVOX
            and ledger["ledger_id"] == LEDGER_ID,
            "LEDGER_CHANNEL")
    events = ledger["events"]
    require(type(events) is list and len(events) <= MAX_EVENTS, "EVENT_COUNT")
    require(type(ledger["sequence"]) is int
            and ledger["sequence"] == len(events), "EVENT_SEQUENCE")
    bytes_for_ledger(ledger)
    heads = [GENESIS]
    states = {}
    releases = set()
    media_digests = set()
    last_time = None
    for seq, event in enumerate(events, 1):
        require(type(event) is dict and set(event) == EVENT_FIELDS,
                "EVENT_FIELDS")
        require(type(event["sequence"]) is int and event["sequence"] == seq,
                "NONCONTIGUOUS_SEQUENCE")
        require(event["prev_sha256"] == heads[-1], "BROKEN_CHAIN")
        require(event["kind"] in KINDS, "WRONG_EVENT_KIND")
        release, media, metadata, rights = (
            event["release_id"], event["media_sha256"],
            event["metadata_sha256"], event["rights_evidence_sha256"]
        )
        require(type(release) is str and ID.fullmatch(release) is not None,
                "RELEASE_ID")
        for field in (media, metadata, rights):
            require(type(field) is str and SHA.fullmatch(field) is not None,
                    "RELEASE_DIGEST")
        key = candidate_attempt_key(
            channel_id=CLIVOX, release_id=release,
            media_sha256=media, metadata_sha256=metadata,
            rights_evidence_sha256=rights
        )
        require(event["attempt_key"] == key, "EXACT_ATTEMPT_KEY")
        event_time = time_utc(event["recorded_at_utc"])
        require(event_time <= now.astimezone(timezone.utc)
                and (last_time is None or event_time >= last_time),
                "FUTURE_OR_REORDERED_CLOCK")
        last_time = event_time
        body = {k: v for k, v in event.items() if k != "event_sha256"}
        digest = event_hash(body)
        require(event["event_sha256"] == digest, "EVENT_DIGEST")
        heads.append(digest)
        if event["kind"] == "RESERVE_SYNTHETIC":
            require(key not in states and release not in releases
                    and media not in media_digests,
                    "DUPLICATE_RELEASE_MEDIA_OR_ATTEMPT")
            states[key] = {
                "state": STATE_RESERVED, "release_id": release,
                "media_sha256": media,
                "metadata_sha256": metadata,
                "rights_evidence_sha256": rights,
            }
            releases.add(release)
            media_digests.add(media)
        else:
            require(key in states and states[key]["state"] == STATE_RESERVED,
                    "UNKNOWN_OR_REPEATED_HOLD")
            require(states[key]["release_id"] == release
                    and states[key]["media_sha256"] == media
                    and states[key]["metadata_sha256"] == metadata
                    and states[key]["rights_evidence_sha256"] == rights,
                    "ALTERED_HOLD_SUBJECT")
            states[key]["state"] = STATE_UNKNOWN
    require(ledger["head_sha256"] == heads[-1], "WRONG_HEAD")
    n = anchor["sequence"]
    require(n <= len(events) and heads[n] == anchor["head_sha256"],
            "ROLLBACK_OR_FORK_VS_ANCHOR")
    return {
        "stage": "A8_PRIVATE_CAS_LEDGER_CONTRACT_ONLY",
        "event_count": len(events),
        "attempt_count": len(states),
        "snapshot_matches_caller_supplied_anchor": True,
        "all_attempts_hold_no_network": True,
        "independent_external_durable_anchor_verified": False,
        "production_cross_run_store_provisioned": False,
        "licensed_creators_verified": 0,
        "youtube_upload_authorized": False,
        "youtube_schedule_authorized": False,
        "youtube_publish_authorized": False,
        "actual_youtube_api_calls": 0,
    }


def append_simulated_event(
    ledger: dict, *, kind: str, release_id: str, media_sha256: str,
    metadata_sha256: str, rights_evidence_sha256: str, at_utc: str,
    anchor: dict, now: datetime
) -> dict:
    """Append to a local snapshot only. Can never authorize a live upload."""
    verify_ledger(ledger, anchor=anchor, now=now)
    require(kind in KINDS, "EVENT_KIND")
    require(len(ledger["events"]) < MAX_EVENTS, "AT_CAPACITY")
    body = {
        "sequence": len(ledger["events"]) + 1,
        "prev_sha256": ledger["head_sha256"],
        "kind": kind,
        "attempt_key": candidate_attempt_key(
            channel_id=CLIVOX, release_id=release_id,
            media_sha256=media_sha256, metadata_sha256=metadata_sha256,
            rights_evidence_sha256=rights_evidence_sha256
        ),
        "release_id": release_id, "media_sha256": media_sha256,
        "metadata_sha256": metadata_sha256,
        "rights_evidence_sha256": rights_evidence_sha256,
        "recorded_at_utc": at_utc,
    }
    event = {**body, "event_sha256": event_hash(body)}
    updated = {
        **ledger,
        "sequence": body["sequence"],
        "head_sha256": event["event_sha256"],
        "events": [*ledger["events"], event],
    }
    verify_ledger(updated, anchor=anchor, now=now)
    return updated


def decode_github_contents(reply: dict) -> tuple[dict, str]:
    """Validate GitHub's Contents file GET before even reading the ledger."""
    require(type(reply) is dict and reply.get("type") == "file"
            and reply.get("name") == "attempt-ledger-v1.json"
            and reply.get("path") == FILE_PATH
            and reply.get("encoding") == "base64",
            "WRONG_CONTENTS_OBJECT")
    sha = reply.get("sha")
    require(type(sha) is str and GIT_SHA.fullmatch(sha) is not None,
            "GITHUB_BLOB_SHA")
    encoded = reply.get("content")
    require(type(encoded) is str and 0 < len(encoded) <= 2 * MAX_BYTES,
            "BASE64_SIZE")
    try:
        raw = base64.b64decode(
            encoded.replace("\n", "").replace("\r", ""), validate=True
        )
        require(0 < len(raw) <= MAX_BYTES
                and type(reply.get("size")) is int and len(raw) == reply["size"],
                "RAW_FILE_SIZE")
        require(git_blob_sha(raw) == sha, "BLOB_BYTES_HASH")
        obj = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, binascii.Error):
        raise PrivateCASBlocked("CLIVOX_A8_PRIVATE_CAS_DENIED_BLOB_DECODE") from None
    require(type(obj) is dict, "NOT_JSON_OBJECT")
    require(bytes_for_ledger(obj) == raw, "NONCANONICAL_JSON")
    return obj, sha


def build_github_put_contract(*, existing_blob_sha: str, updated: dict) -> dict:
    """Pure GitHub Contents update body. Cannot execute a remote PUT."""
    require(type(existing_blob_sha) is str
            and GIT_SHA.fullmatch(existing_blob_sha) is not None,
            "REQUIRES_PREVIOUS_BLOB_SHA")
    return {
        "message": "clivox: reserve or hold upload attempt (no YouTube)",
        "content": base64.b64encode(bytes_for_ledger(updated)).decode("ascii"),
        "sha": existing_blob_sha,
        "branch": "main",
    }


def simulate_cas(*, current_remote_blob_sha: str, proposed_body: dict) -> str:
    """Only a mock CAS. A future live transport MUST reconcile ambiguity."""
    require(type(current_remote_blob_sha) is str
            and GIT_SHA.fullmatch(current_remote_blob_sha) is not None,
            "REMOTE_SHA")
    require(type(proposed_body) is dict
            and set(proposed_body) == {"message", "content", "sha", "branch"}
            and proposed_body["branch"] == "main"
            and proposed_body["sha"] == current_remote_blob_sha,
            "STALE_WRITE_OR_WRONG_BRANCH")
    try:
        raw = base64.b64decode(proposed_body["content"], validate=True)
        require(0 < len(raw) <= MAX_BYTES, "PROPOSAL_SIZE")
        obj = json.loads(raw.decode("utf-8"))
        require(bytes_for_ledger(obj) == raw, "PROPOSAL_CANONICAL")
    except (ValueError, UnicodeDecodeError, binascii.Error):
        raise PrivateCASBlocked("CLIVOX_A8_PRIVATE_CAS_DENIED_BAD_PROPOSAL") from None
    return git_blob_sha(raw)


def reconcile_unknown_commit(*, observed_ledger: dict,
                             attempt_key: str, anchor: dict,
                             now: datetime) -> dict:
    """No outcome from an ambiguous GitHub PUT proves upload permission.

    If a timed-out write actually committed, observe its reservation.
    If absent, stop rather than preparing another upload.
    """
    verify_ledger(observed_ledger, anchor=anchor, now=now)
    require(type(attempt_key) is str and SHA.fullmatch(attempt_key) is not None,
            "EXACT_ATTEMPT_KEY")
    seen = any(e["attempt_key"] == attempt_key
               for e in observed_ledger["events"])
    return {
        "decision": (
            "HOLD_PREVIOUS_RESERVATION_POSSIBLY_COMMITTED"
            if seen else "HOLD_COMMIT_NOT_CONFIRMED_NO_RETRY"
        ),
        "remote_ledger_contains_attempt": seen,
        "owner_manual_reconciliation_required": True,
        "authenticated_youtube_inventory_verified": False,
        "automatic_retry_allowed": False,
        "youtube_upload_authorized": False,
        "youtube_schedule_authorized": False,
        "youtube_publish_authorized": False,
    }


def validate_closed_policy(policy: dict) -> None:
    fields = frozenset((
        "schema_version", "channel_id", "phase", "private_vault_name_selected",
        "owner_private_vault_approved", "private_upload_ledger_bootstrapped",
        "dedicated_contents_write_token_configured",
        "owner_protected_upload_environment_verified",
        "real_independent_ledger_anchor_enrolled",
        "actual_github_get_put_enabled", "cross_runner_durable_ledger_verified",
        "creator_licenses_authenticated", "real_owner_video_signatures_verified",
        "real_clivox_upload_oauth_configured", "youtube_api_writes_enabled",
        "source_media_downloads_enabled", "state"
    ))
    require(type(policy) is dict and set(policy) == fields, "POLICY_FIELDS")
    require(policy["schema_version"] == 1 and policy["channel_id"] == CLIVOX
            and policy["phase"] == "A8_PRIVATE_CAS_PROTOCOL_OFFLINE_ONLY"
            and policy["state"] == "NO_LIVE_UPLOADS_OR_CROSS_RUN_STORE"
            and policy["creator_licenses_authenticated"] == 0
            and policy["real_owner_video_signatures_verified"] == 0,
            "PREMATURE_PRODUCTION_POLICY")
    for name in fields - {
        "schema_version", "channel_id", "phase", "state",
        "creator_licenses_authenticated", "real_owner_video_signatures_verified"
    }:
        require(policy[name] is False, "PRODUCTION_GATE_" + name)


def fixture_report() -> dict:
    now=datetime(2026, 11, 13, 5, 30, tzinfo=timezone.utc)
    start=new_ledger()
    verified=verify_ledger(
        start, anchor={"sequence": 0, "head_sha256": GENESIS}, now=now
    )
    return {
        "stage": "A8_CROSS_RUN_GITHUB_CONTENTS_CAS_OFFLINE_SIMULATION",
        "channel_id": CLIVOX,
        "initial_ledger_valid": verified["all_attempts_hold_no_network"],
        "github_file_blob_sha_check_implemented": True,
        "single_global_ledger_duplicate_subject_guard_implemented": True,
        "strict_existing_blob_sha_put_contract_implemented": True,
        "unknown_commit_no_blind_retry_implemented": True,
        "actual_private_cross_run_ledger_provisioned": False,
        "actual_durable_external_head_verified": False,
        "real_signed_release_or_creator_grant_verified": False,
        "actual_github_put_calls": 0,
        "actual_youtube_api_calls": 0,
        "youtube_upload_authorized": False,
        "youtube_schedule_authorized": False,
        "youtube_publish_authorized": False,
    }


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--mode", choices=("fixture",), default="fixture")
    p.parse_args()
    validate_closed_policy(json.loads(POLICY.read_text("utf-8")))
    print(json.dumps(fixture_report(), sort_keys=True))


if __name__ == "__main__":
    main()
