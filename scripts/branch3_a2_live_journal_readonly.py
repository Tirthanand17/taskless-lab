"""CLIVOX A2 owner-approved private revocation journal READ-ONLY bridge.

Live mode requires an owner-reviewed GitHub environment, a dedicated read-only
private-repository Contents token, an explicitly pinned public verification key,
and a separately supplied prior journal anchor. It performs exactly 3 HTTPS
GETs and NEVER downloads media, creates a repository or uploads to YouTube.

A successful response is only a contemporaneous *integrity snapshot* using
owner-supplied key/anchor claims. It does not independently establish that the
signing key belongs to a rights holder, that the anchor is nonrollbackable, or
that the remote ledger is complete or legally grants commercial clipping.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import http.client
import json
import os
import re
import ssl
from collections.abc import Mapping
from urllib.parse import quote

from scripts.branch3_a3_private_vault_readback import (
    OWNER, CONTROLLER, HOST, API_VERSION, expected_paths,
    validate_private_repository, validate_collaborators, VaultReadbackDenied,
)
from scripts.branch3_a2_private_ledger_cas import (
    FILE_PATH, MAX_BYTES, decode_github_contents, verify_journal,
    validate_floor, ReviewDenied
)
from scripts.branch3_a2_review_receipt import CLIVOX_ID, SHA

WORKFLOW_REF = (CONTROLLER +
    "/.github/workflows/branch3-clivox-a2-live-journal-readonly.yml@refs/heads/main")
VAULT_ENV = "CLIVOX_A2_APPROVED_PRIVATE_VAULT_NAME"
TOKEN_ENV = "CLIVOX_A2_PRIVATE_CONTENTS_READ_TOKEN"
APPROVAL_ENV = "CLIVOX_A2_JOURNAL_READ_APPROVED"
KEY_ENV = "CLIVOX_A2_PINNED_REVOCATION_PUBKEY_HEX"
ANCHOR_SEQ_ENV = "CLIVOX_A2_OWNER_PINNED_ANCHOR_SEQ"
ANCHOR_SHA_ENV = "CLIVOX_A2_OWNER_PINNED_ANCHOR_SHA256"
APPROVED_VALUE = "approved-clivox-journal-readonly-v1"
MAX_REPLY = 420_000
MAX_BODY_PATH = 250


class JournalBridgeDenied(ValueError):
    """Fail closed; no raw tokens, private paths or HTTP bodies in messages."""


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise JournalBridgeDenied("CLIVOX_A2_LIVE_READONLY_DENIED_" + reason)


def expected_journal_paths(name: str) -> tuple[str, str, str]:
    repo_path, collaborators_path = expected_paths(name)
    return (repo_path, collaborators_path,
            repo_path + "/contents/" + FILE_PATH + "?ref=main")


def validate_manual_context(env: Mapping[str, str]) -> dict:
    for label, expected in (
        ("GITHUB_ACTIONS", "true"),
        ("GITHUB_REPOSITORY", CONTROLLER),
        ("GITHUB_REF", "refs/heads/main"),
        ("GITHUB_EVENT_NAME", "workflow_dispatch"),
        ("GITHUB_WORKFLOW_REF", WORKFLOW_REF),
        ("GITHUB_ACTOR", OWNER),
        ("GITHUB_TRIGGERING_ACTOR", OWNER),
        ("GITHUB_RUN_ATTEMPT", "1"),
        (APPROVAL_ENV, APPROVED_VALUE),
    ):
        require(env.get(label) == expected, "MANUAL_CONTEXT_" + label)
    name = env.get(VAULT_ENV)
    require(type(name) is str, "VAULT_NAME")
    expected_journal_paths(name)
    token = env.get(TOKEN_ENV)
    require(type(token) is str and 30 <= len(token) <= 1024
            and all(32 < ord(c) < 127 for c in token),
            "SEPARATE_READONLY_TOKEN")
    raw_key = env.get(KEY_ENV)
    require(type(raw_key) is str
            and re.fullmatch(r"[a-f0-9]{64}", raw_key) is not None,
            "REVIEWED_PUBKEY_BYTES")
    seq = env.get(ANCHOR_SEQ_ENV)
    require(type(seq) is str and re.fullmatch(r"0|[1-9][0-9]{0,2}", seq) is not None,
            "PINNED_ANCHOR_SEQUENCE")
    digest = env.get(ANCHOR_SHA_ENV)
    require(type(digest) is str and SHA.fullmatch(digest) is not None,
            "PINNED_ANCHOR_DIGEST")
    anchor = {"sequence": int(seq), "head_sha256": digest}
    try:
        validate_floor(anchor)
    except ReviewDenied:
        raise JournalBridgeDenied("CLIVOX_A2_LIVE_READONLY_DENIED_ANCHOR") from None
    return {"vault_name": name, "token": token,
            "public_key": bytes.fromhex(raw_key), "floor": anchor}


def github_get(path: str, bearer: str) -> tuple[object, str]:
    """Hardcoded GitHub host; GET only; no redirects, retries or raw API logs."""
    require(type(path) is str and len(path) <= MAX_BODY_PATH
            and "\r" not in path and "\n" not in path
            and "#" not in path and "%" not in path
            and ".." not in path, "INVALID_GITHUB_PATH")
    m = re.fullmatch(
        r"/repos/" + OWNER +
        r"/(clivox-[a-z0-9][a-z0-9-]{3,48}[a-z0-9])"
        r"(/collaborators\?affiliation=all&per_page=100&page=1|"
        r"/contents/clivox-private/rights/revocation-journal-v1\.json\?ref=main)?",
        path,
    )
    require(m is not None, "UNAPPROVED_GITHUB_GET")
    require(type(bearer) is str and 30 <= len(bearer) <= 1024
            and all(32 < ord(c) < 127 for c in bearer),
            "INVALID_READ_TOKEN")
    conn = None
    try:
        conn = http.client.HTTPSConnection(
            HOST, timeout=12, context=ssl.create_default_context()
        )
        conn.request("GET", path, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + bearer,
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "clivox-a2-owner-private-journal-readonly",
        })
        response = conn.getresponse()
        raw = response.read(MAX_REPLY + 1)
        require(response.status == 200, "GITHUB_ACCESS_DENIED_OR_MISSING")
        require(len(raw) <= MAX_REPLY, "BOUNDED_GITHUB_API_BODY")
        obj = json.loads(raw)
        return obj, response.getheader("Link", "")
    except JournalBridgeDenied:
        raise
    except (OSError, ValueError, http.client.HTTPException):
        raise JournalBridgeDenied(
            "CLIVOX_A2_LIVE_READONLY_DENIED_NETWORK_OR_JSON"
        ) from None
    finally:
        if conn is not None:
            conn.close()


def run_owner_readonly(
    env: Mapping[str, str], *, http_get=github_get,
    now: datetime | None = None
) -> dict:
    """Check owner, collaborators and signed private journal; no other I/O."""
    settings = validate_manual_context(env)
    repo_path, collaborators_path, contents_path = expected_journal_paths(
        settings["vault_name"]
    )
    repo, repo_link = http_get(repo_path, settings["token"])
    require(type(repo_link) is str and repo_link == "", "REPO_LINK")
    validate_private_repository(repo, settings["vault_name"])
    users, users_link = http_get(collaborators_path, settings["token"])
    validate_collaborators(users, users_link)
    contents, contents_link = http_get(contents_path, settings["token"])
    require(type(contents_link) is str and contents_link == "", "CONTENTS_LINK")
    ledger, blob_sha = decode_github_contents(contents)
    require(type(blob_sha) is str and len(blob_sha) == 40, "BLOB_SHA")
    check = verify_journal(
        ledger, revocation_public_key=settings["public_key"],
        trusted_floor=settings["floor"],
        now=datetime.now(timezone.utc) if now is None else now
    )
    require(check["supplied_head_chain_valid"] is True
            and check["supplied_floor_matches"] is True,
            "JOURNAL_CHAIN_OR_PIN")
    # Never output private object IDs, repo name, bearer, key or hash values.
    return {
        "stage": "A2_OWNER_APPROVED_LIVE_PRIVATE_JOURNAL_READONLY",
        "channel_id": CLIVOX_ID,
        "authenticated_github_private_repo_metadata_observed": True,
        "owner_only_collaborators_observed": True,
        "private_journal_blob_integrity_observed": True,
        "supplied_revocation_signatures_mathematically_valid": True,
        "supplied_anchor_matches_observed_journal": True,
        "actual_github_get_count": 3,
        "actual_github_write_count": 0,
        "owner_pinned_key_independently_authenticated": False,
        "anchor_external_nonrollbackable_storage_proven": False,
        "remote_journal_completeness_proven": False,
        "genuine_creator_licenses_verified": 0,
        "private_vault_owner_usage_approved_by_this_check": False,
        "source_media_download_authorized": False,
        "youtube_upload_authorized": False,
        "youtube_schedule_authorized": False,
        "youtube_publish_authorized": False,
        "note": "Contemporaneous owner-credentialled integrity read; NEVER a rights clearance."
    }


def fixture_report() -> dict:
    return {
        "stage": "A2_LIVE_READONLY_BRIDGE_FIXTURE_NOT_CONNECTED",
        "channel_id": CLIVOX_ID,
        "actual_github_get_count": 0,
        "actual_github_write_count": 0,
        "live_private_journal_verified": False,
        "independent_anchor_durability_verified": False,
        "genuine_creator_licenses_verified": 0,
        "source_media_download_authorized": False,
        "youtube_upload_authorized": False,
        "youtube_schedule_authorized": False,
        "youtube_publish_authorized": False,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("fixture", "live"), default="fixture")
    args = p.parse_args()
    try:
        output = fixture_report() if args.mode == "fixture" else run_owner_readonly(os.environ)
    except (JournalBridgeDenied, VaultReadbackDenied, ReviewDenied,
            ValueError, TypeError, KeyError):
        raise SystemExit("CLIVOX_A2_JOURNAL_DENIED_NO_MEDIA_NO_YOUTUBE") from None
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
