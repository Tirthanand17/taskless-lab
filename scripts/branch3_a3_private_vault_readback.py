"""Clivox A3 owner-only private-vault GitHub READBACK, never media access.

The live path is manual/main-only and requires separately owner-protected
environment secrets. It performs only two GitHub API GETs: repository metadata
and the first (must be exhaustive) collaborators page. Success is a snapshot of
visibility and a conservative owner-only collaborator policy, NOT proof that all
app access is excluded or that video rights, vault usage or uploads are approved.

No GitHub token, private repository name, collaborators or raw GitHub bodies are
printed. No media download, source creation, token minting or GitHub writes.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
import http.client
import json
import os
import re
import ssl
from urllib.parse import quote

OWNER = "Tirthanand17"
CONTROLLER = OWNER + "/taskless-lab"
CHANNEL = "UCfPEvy0SefE_5nNlYlY_CyQ"
HOST = "api.github.com"
WORKFLOW_REF = (
    CONTROLLER
    + "/.github/workflows/branch3-clivox-a3-live-vault-readback.yml@refs/heads/main"
)
VAULT_NAME_ENV = "CLIVOX_A3_OWNER_APPROVED_VAULT_NAME"
TOKEN_ENV = "CLIVOX_A3_VAULT_METADATA_READ_TOKEN"
APPROVAL_ENV = "CLIVOX_A3_VAULT_READBACK_APPROVED"
VAULT_SLUG = re.compile(r"clivox-[a-z0-9][a-z0-9-]{3,48}[a-z0-9]\Z")
MAX_JSON = 200_000
API_VERSION = "2022-11-28"


class VaultReadbackDenied(ValueError):
    """A missing owner approval, unsafe GitHub context or invalid API result."""


def require(ok: bool, code: str) -> None:
    if not ok:
        raise VaultReadbackDenied("CLIVOX_A3_VAULT_DENY_" + code)


def expected_paths(vault_name: str) -> tuple[str, str]:
    require(type(vault_name) is str
            and VAULT_SLUG.fullmatch(vault_name) is not None,
            "UNAPPROVED_VAULT_NAME")
    base = "/repos/" + OWNER + "/" + quote(vault_name, safe="")
    return base, base + "/collaborators?affiliation=all&per_page=100&page=1"


def validate_manual_context(env: Mapping[str, str]) -> tuple[str, str]:
    require(env.get("GITHUB_ACTIONS") == "true", "NOT_ACTIONS")
    require(env.get("GITHUB_REPOSITORY") == CONTROLLER, "WRONG_REPO")
    require(env.get("GITHUB_EVENT_NAME") == "workflow_dispatch", "NOT_MANUAL")
    require(env.get("GITHUB_REF") == "refs/heads/main", "NOT_MAIN")
    require(env.get("GITHUB_WORKFLOW_REF") == WORKFLOW_REF, "WRONG_WORKFLOW")
    require(env.get("GITHUB_ACTOR") == OWNER
            and env.get("GITHUB_TRIGGERING_ACTOR") == OWNER,
            "NOT_OWNER_TRIGGERED")
    require(env.get("GITHUB_RUN_ATTEMPT") == "1", "RETRY_MUST_BE_FRESH_DISPATCH")
    require(env.get(APPROVAL_ENV) == "approved-a3-readonly-v1", "OWNER_NOT_OPTED_IN")
    name = env.get(VAULT_NAME_ENV)
    expected_paths(name)
    token = env.get(TOKEN_ENV)
    require(type(token) is str
            and 30 <= len(token) <= 1024
            and all(32 < ord(x) < 127 for x in token),
            "MISSING_OR_UNSAFE_DEDICATED_TOKEN")
    return name, token


def validate_private_repository(data: object, vault_name: str) -> dict:
    """Validate authenticated GET /repos/OWNER/name metadata (not a license)."""
    expected_paths(vault_name)
    require(type(data) is dict, "REPO_JSON")
    owner = data.get("owner")
    require(type(owner) is dict and owner.get("login") == OWNER
            and owner.get("type") == "User", "VAULT_OWNER")
    require(data.get("full_name") == OWNER + "/" + vault_name
            and data.get("name") == vault_name
            and data.get("full_name") != CONTROLLER,
            "WRONG_VAULT_REPOSITORY")
    require(type(data.get("id")) is int and data["id"] > 0, "REPO_ID")
    require(data.get("private") is True
            and data.get("visibility") == "private", "NOT_PRIVATE")
    require(data.get("archived") is False
            and data.get("disabled") is False
            and data.get("fork") is False
            and data.get("is_template") is False,
            "UNSAFE_REPO_STATE")
    # Authenticated metadata is evidence for private visibility at this instant
    # only; it does not prove App installations, backups or media ACLs.
    return {"authenticated_private_repo_snapshot": True}


def validate_collaborators(data: object, link_header: str) -> dict:
    """Conservatively require one owner/admin and no API pagination."""
    require(type(data) is list and len(data) == 1, "OWNER_ONLY_COLLABORATORS")
    require(type(link_header) is str and len(link_header) < 4096
            and 'rel="next"' not in link_header, "PAGINATION_NOT_EXHAUSTED")
    person = data[0]
    require(type(person) is dict and person.get("login") == OWNER,
            "UNKNOWN_COLLABORATOR")
    perms = person.get("permissions")
    require(type(perms) is dict and perms.get("admin") is True
            and person.get("role_name") in ("admin", "owner"),
            "OWNER_ADMIN_NOT_CONFIRMED")
    return {"one_owner_only_collaborator_page_observed": True}


def github_get(path: str, bearer: str) -> tuple[object, str]:
    """Fixed-host GET-only transport, zero redirect or token logging."""
    require(type(bearer) is str and 30 <= len(bearer) <= 1024
            and all(32 < ord(x) < 127 for x in bearer), "TOKEN")
    require(type(path) is str
            and path.startswith("/repos/" + OWNER + "/clivox-")
            and len(path) <= 200
            and all(x not in path for x in ("#", "%", "\r", "\n", "..")),
            "UNSAFE_REQUEST_PATH")
    require(path.endswith("/collaborators?affiliation=all&per_page=100&page=1")
            or (path.count("/") == 3 and "?" not in path),
            "ONLY_APPROVED_REPO_OR_COLLABORATOR_GET")
    conn = None
    try:
        conn = http.client.HTTPSConnection(
            HOST, timeout=12, context=ssl.create_default_context()
        )
        conn.request("GET", path, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + bearer,
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "clivox-a3-owner-readonly-github-ci",
        })
        reply = conn.getresponse()
        raw = reply.read(MAX_JSON + 1)
        require(reply.status == 200, "GITHUB_AUTH_OR_ACCESS_REJECTED")
        require(len(raw) <= MAX_JSON, "OVERSIZED_API_RESPONSE")
        return json.loads(raw), reply.getheader("Link", "")
    except VaultReadbackDenied:
        raise
    except (OSError, TimeoutError, ValueError, http.client.HTTPException):
        # Raw exceptions, response bodies and URLs can reveal private metadata.
        raise VaultReadbackDenied("CLIVOX_A3_VAULT_DENY_NETWORK_OR_JSON") from None
    finally:
        if conn is not None:
            conn.close()


def run_owner_readback(env: Mapping[str, str], *, http_get=github_get) -> dict:
    vault_name, token = validate_manual_context(env)
    repo_path, users_path = expected_paths(vault_name)
    repo_data, repo_link = http_get(repo_path, token)
    require(type(repo_link) is str and not repo_link, "REPO_METADATA_PAGINATED")
    validate_private_repository(repo_data, vault_name)
    users_data, users_link = http_get(users_path, token)
    validate_collaborators(users_data, users_link)
    # NO private identifiers, token, collaborator data or raw request URLs.
    return {
        "stage": "A3_AUTHENTICATED_OWNER_ONLY_GITHUB_READBACK",
        "target_channel_id": CHANNEL,
        "live_github_private_metadata_readback": True,
        "repo_private_observed_at_readback": True,
        "owner_only_collaborator_page_observed": True,
        "api_get_count": 2,
        "app_installations_and_external_object_access_audited": False,
        "owner_storage_usage_approval_verified": False,
        "rights_holder_grants_verified": 0,
        "source_media_download_authorized": False,
        "vault_media_write_authorized": False,
        "licensed_media_render_authorized": False,
        "youtube_upload_authorized": False,
        "youtube_schedule_authorized": False,
        "youtube_publish_authorized": False,
        "github_api_write_count": 0,
        "youtube_api_write_count": 0,
        "note": "Read-only privacy snapshot, NOT storage activation or creator permission.",
    }


def fixture_report() -> dict:
    return {
        "stage": "A3_OFFLINE_PRIVATE_VAULT_BRIDGE_FIXTURE",
        "target_channel_id": CHANNEL,
        "live_github_private_metadata_readback": False,
        "repo_private_observed_at_readback": False,
        "owner_only_collaborator_page_observed": False,
        "api_get_count": 0,
        "rights_holder_grants_verified": 0,
        "owner_storage_usage_approval_verified": False,
        "source_media_download_authorized": False,
        "vault_media_write_authorized": False,
        "youtube_upload_authorized": False,
        "youtube_schedule_authorized": False,
        "youtube_publish_authorized": False,
        "github_api_write_count": 0,
        "youtube_api_write_count": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("fixture", "live"), default="fixture")
    args = parser.parse_args()
    try:
        result = fixture_report() if args.mode == "fixture" else run_owner_readback(os.environ)
    except (VaultReadbackDenied, KeyError, TypeError):
        raise SystemExit("CLIVOX_A3_VAULT_READBACK_DENIED_NO_MEDIA_NO_YOUTUBE") from None
    print(json.dumps(result, sort_keys=True))
    print("CLIVOX_A3_READONLY_NO_SOURCE_NO_VAULT_WRITES_NO_YOUTUBE")


if __name__ == "__main__":
    main()
