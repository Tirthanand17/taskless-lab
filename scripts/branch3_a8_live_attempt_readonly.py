"""CLIVOX A8: owner/main protected private upload-attempt ledger READ-ONLY bridge.

Three fixed GitHub API HTTPS GETs validate private repo owner/ACL, exact
Contents blob bytes and SHA-256 chained attempt history against an owner-supplied
sequence/head floor. No CAS writes, no token minting, no media, no YouTube API.

The supplied anchor has NOT been independently proven immutable or signed.
A valid journal is NOT authorization to upload or a real cross-run writer.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
from datetime import datetime, timezone
import http.client
import json
import os
import re
import ssl

from scripts.branch3_a3_private_vault_readback import (
    OWNER, CONTROLLER, HOST, API_VERSION, expected_paths,
    validate_private_repository, validate_collaborators, VaultReadbackDenied,
)
from scripts.branch3_a8_private_cas_ledger import (
    CLIVOX, FILE_PATH, GENESIS, PrivateCASBlocked, decode_github_contents,
    validate_anchor, verify_ledger,
)

WORKFLOW_REF = (CONTROLLER +
    "/.github/workflows/branch3-clivox-a8-live-attempt-readonly.yml@refs/heads/main")
VAULT_ENV = "CLIVOX_A8_APPROVED_PRIVATE_VAULT_NAME"
TOKEN_ENV = "CLIVOX_A8_PRIVATE_CONTENTS_READ_TOKEN"
APPROVAL_ENV = "CLIVOX_A8_ATTEMPT_LEDGER_READ_APPROVED"
ANCHOR_SEQ_ENV = "CLIVOX_A8_OWNER_PINNED_ATTEMPT_SEQ"
ANCHOR_SHA_ENV = "CLIVOX_A8_OWNER_PINNED_ATTEMPT_SHA256"
APPROVED_VALUE = "approved-clivox-a8-attempt-readonly-v1"
MAX_REPLY = 420_000
MAX_PATH = 260
STRICT_GET = re.compile(
    r"/repos/" + OWNER +
    r"/(clivox-[a-z0-9][a-z0-9-]{3,48}[a-z0-9])"
    r"(/collaborators\?affiliation=all&per_page=100&page=1|"
    r"/contents/clivox-private/upload-control/attempt-ledger-v1\.json\?ref=main)?\Z"
)


class AttemptBridgeDenied(ValueError):
    """Reject unapproved read, forged ACL, rollback or unexpected GitHub API."""


def require(ok: bool, label: str) -> None:
    if not ok:
        raise AttemptBridgeDenied("CLIVOX_A8_LIVE_ATTEMPT_DENIED_" + label)


def expected_attempt_paths(vault_name: str) -> tuple[str, str, str]:
    repo_path, collaborators_path = expected_paths(vault_name)
    return (repo_path, collaborators_path,
            repo_path + "/contents/" + FILE_PATH + "?ref=main")


def validate_manual_context(env: Mapping[str, str]) -> dict:
    for key, required in (
        ("GITHUB_ACTIONS", "true"),
        ("GITHUB_REPOSITORY", CONTROLLER),
        ("GITHUB_EVENT_NAME", "workflow_dispatch"),
        ("GITHUB_REF", "refs/heads/main"),
        ("GITHUB_WORKFLOW_REF", WORKFLOW_REF),
        ("GITHUB_ACTOR", OWNER),
        ("GITHUB_TRIGGERING_ACTOR", OWNER),
        ("GITHUB_RUN_ATTEMPT", "1"),
        (APPROVAL_ENV, APPROVED_VALUE),
    ):
        require(env.get(key) == required, "MANUAL_OWNER_CONTEXT_" + key)
    vault_name = env.get(VAULT_ENV)
    require(type(vault_name) is str, "MISSING_VAULT_NAME")
    expected_attempt_paths(vault_name)
    token = env.get(TOKEN_ENV)
    require(type(token) is str and 30 <= len(token) <= 1024
            and all(32 < ord(c) < 127 for c in token),
            "MISSING_OWNER_DEDICATED_READ_TOKEN")
    seq = env.get(ANCHOR_SEQ_ENV)
    require(type(seq) is str and
            re.fullmatch(r"0|[1-9][0-9]{0,2}", seq) is not None,
            "OWNER_HEAD_SEQ")
    head = env.get(ANCHOR_SHA_ENV)
    require(type(head) is str and re.fullmatch(r"[a-f0-9]{64}", head) is not None,
            "OWNER_HEAD_SHA")
    floor = {"sequence": int(seq), "head_sha256": head}
    try:
        validate_anchor(floor)
    except PrivateCASBlocked:
        raise AttemptBridgeDenied(
            "CLIVOX_A8_LIVE_ATTEMPT_DENIED_UNTRUSTED_FLOOR"
        ) from None
    return {"vault_name": vault_name, "token": token, "floor": floor}


def github_get(path: str, bearer: str) -> tuple[object, str]:
    """GitHub only; exact A8 metadata URLs; GET only, no redirects/retries."""
    require(type(path) is str and len(path) <= MAX_PATH
            and STRICT_GET.fullmatch(path) is not None
            and all(x not in path for x in ("#", "%", "..", "\r", "\n")),
            "GITHUB_URL_ALLOWLIST")
    require(type(bearer) is str and 30 <= len(bearer) <= 1024
            and all(32 < ord(c) < 127 for c in bearer),
            "GITHUB_READ_TOKEN")
    connection = None
    try:
        connection = http.client.HTTPSConnection(
            HOST, timeout=12, context=ssl.create_default_context()
        )
        connection.request("GET", path, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + bearer,
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "clivox-a8-private-attempt-owner-readonly",
        })
        response = connection.getresponse()
        raw = response.read(MAX_REPLY + 1)
        require(response.status == 200, "PRIVATE_GITHUB_ACCESS_DENIED")
        require(len(raw) <= MAX_REPLY, "GITHUB_BODY_TOO_LARGE")
        obj = json.loads(raw)
        return obj, response.getheader("Link", "")
    except AttemptBridgeDenied:
        raise
    except (OSError, TimeoutError, ValueError, http.client.HTTPException):
        # No leaked bearer, private repo name, remote response or path.
        raise AttemptBridgeDenied(
            "CLIVOX_A8_LIVE_ATTEMPT_DENIED_NETWORK_OR_JSON"
        ) from None
    finally:
        if connection is not None:
            connection.close()


def run_owner_readonly(
    env: Mapping[str, str], *, http_get=github_get,
    now: datetime | None = None
) -> dict:
    """Conservative authenticated state read, not an upload reservation."""
    settings = validate_manual_context(env)
    repo_path, users_path, ledger_path = expected_attempt_paths(
        settings["vault_name"]
    )
    repo, repo_link = http_get(repo_path, settings["token"])
    require(type(repo_link) is str and repo_link == "", "REPO_PAGINATION")
    validate_private_repository(repo, settings["vault_name"])
    users, users_link = http_get(users_path, settings["token"])
    validate_collaborators(users, users_link)
    file_response, file_link = http_get(ledger_path, settings["token"])
    require(type(file_link) is str and file_link == "", "FILE_PAGINATION")
    ledger, blob_sha = decode_github_contents(file_response)
    require(type(blob_sha) is str and len(blob_sha) == 40,
            "BLOB_ID_REQUIRED")
    check = verify_ledger(
        ledger, anchor=settings["floor"],
        now=datetime.now(timezone.utc) if now is None else now
    )
    require(check["snapshot_matches_caller_supplied_anchor"] is True
            and check["all_attempts_hold_no_network"] is True,
            "JOURNAL_CHAIN_OR_ANCHOR")
    return {
        "stage": "A8_OWNER_APPROVED_PRIVATE_ATTEMPT_LEDGER_READONLY",
        "channel_id": CLIVOX,
        "authenticated_private_control_repository_observed": True,
        "owner_only_collaborator_acl_observed": True,
        "actual_private_contents_file_sha_verified": True,
        "exact_global_attempt_chain_replayed": True,
        "provided_prior_head_sequence_anchor_verified": True,
        "observed_event_count": check["event_count"],
        "observed_attempt_count": check["attempt_count"],
        "actual_github_get_count": 3,
        "actual_github_put_count": 0,
        "independent_external_anchor_durability_verified": False,
        "remote_atomic_cas_writer_deployed": False,
        "github_repo_app_installations_or_backups_audited": False,
        "readback_is_transactional_or_latest_snapshot": False,
        "legitimate_owner_media_release_verified": False,
        "genuine_licensed_creator_grants_verified": 0,
        "can_clear_ambiguous_upload_attempts": False,
        "automatic_retry_allowed": False,
        "can_approve_private_media_storage": False,
        "source_media_download_authorized": False,
        "youtube_upload_authorized": False,
        "youtube_schedule_authorized": False,
        "youtube_publish_authorized": False,
        "actual_youtube_api_calls": 0,
        "note": "Owner-consented read-only snapshot. No upload authorization or real writer."
    }


def fixture_report() -> dict:
    return {
        "stage": "A8_PRIVATE_ATTEMPT_LIVE_BRIDGE_FIXTURE_NOT_CONNECTED",
        "channel_id": CLIVOX,
        "actual_github_get_count": 0,
        "actual_github_put_count": 0,
        "real_authenticated_private_attempt_ledger_readback": False,
        "independent_external_anchor_durability_verified": False,
        "genuine_licensed_creator_grants_verified": 0,
        "automatic_retry_allowed": False,
        "youtube_upload_authorized": False,
        "youtube_schedule_authorized": False,
        "youtube_publish_authorized": False,
        "actual_youtube_api_calls": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("fixture", "live"), default="fixture")
    args = parser.parse_args()
    try:
        result = fixture_report() if args.mode == "fixture" else run_owner_readonly(os.environ)
    except (AttemptBridgeDenied, VaultReadbackDenied, PrivateCASBlocked,
            ValueError, KeyError, TypeError):
        raise SystemExit(
            "CLIVOX_A8_PRIVATE_ATTEMPT_DENIED_NO_GITHUB_WRITES_NO_YOUTUBE"
        ) from None
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
