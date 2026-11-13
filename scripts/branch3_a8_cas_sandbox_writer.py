"""CLIVOX A8: owner-protected GitHub CAS *SANDBOX ONLY* write verifier.

Unlike the offline SHA contract, this module has an optional tightly gated
real GitHub Contents PUT transport, but it can write ONLY an isolated,
no-media, no-release, no-upload sandbox probe on an existing non-main branch.

NEVER writes the actual private upload attempt ledger, main branch, source
video, rights, Google OAuth, schedule, or YouTube. It is *not* an upload writer.
A protected env has NO token provisioned, so live dispatch fails closed.
"""
from __future__ import annotations

import argparse
import base64
import binascii
from collections.abc import Mapping
from datetime import datetime
import http.client
import json
import os
import re
import ssl

from scripts.branch3_a3_private_vault_readback import (
    API_VERSION, CONTROLLER, HOST, OWNER, expected_paths as a3_expected_paths,
    validate_collaborators, validate_private_repository, VaultReadbackDenied,
)
from scripts.branch3_a2_private_ledger_cas import git_blob_sha
from scripts.branch3_a8_private_cas_ledger import canonical
from scripts.branch3_a8_live_attempt_readonly import (
    AttemptBridgeDenied,
)

WORKFLOW_REF = (CONTROLLER +
    "/.github/workflows/branch3-clivox-a8-cas-sandbox-verify.yml@refs/heads/main")
BRANCH = "sandbox/b3-a8-cas-probe-20261113"
FILE_PATH = "clivox-private/sandbox/cas-probe-v1.json"
APPROVAL = "approved-clivox-a8-cas-sandbox-no-youtube-v1"
NAME_ENV = "CLIVOX_A8_CAS_SANDBOX_PRIVATE_REPO_NAME"
TOKEN_ENV = "CLIVOX_A8_CAS_SANDBOX_CONTENTS_WRITE_TOKEN"
APPROVAL_ENV = "CLIVOX_A8_CAS_SANDBOX_WRITE_APPROVED"
SERIAL_ENV = "CLIVOX_A8_CAS_SANDBOX_EXPECTED_SERIAL"
SHA_ENV = "CLIVOX_A8_CAS_SANDBOX_EXPECTED_BLOB_SHA"
CLIVOX = "UCfPEvy0SefE_5nNlYlY_CyQ"
HEADER_LIMIT = 4800
MAX_RESPONSE = 140_000
SHA40 = re.compile(r"[a-f0-9]{40}\Z")
FIELDS = frozenset((
    "schema_version", "channel_id", "test_only", "production_ledger",
    "youtube_upload_authorized", "write_serial", "writer", "subject"
))
WRITERS = frozenset(("sandbox-probe-first", "owner-sandbox-verified"))
SUBJECT = "no-media-no-release-cas-probe"


class SandboxWriteBlocked(ValueError):
    """Fail closed without exposing any token, repo, video or secret."""


class SandboxCASConflict(SandboxWriteBlocked):
    """Only represents a GitHub HTTP 409. No retries permitted."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise SandboxWriteBlocked("CLIVOX_A8_SANDBOX_DENIED_" + reason)


def canonical_bytes(item: dict) -> bytes:
    require(type(item) is dict, "SERIALIZED_OBJECT")
    data = canonical(item) + b"\n"
    require(0 < len(data) <= 6_000, "JSON_TOO_LONG")
    return data


def validate_probe(probe: dict) -> None:
    require(type(probe) is dict and set(probe) == FIELDS,
            "EXACT_SANDBOX_FIELDS")
    require(type(probe["schema_version"]) is int
            and probe["schema_version"] == 1
            and probe["channel_id"] == CLIVOX
            and probe["test_only"] is True
            and probe["production_ledger"] is False
            and probe["youtube_upload_authorized"] is False
            and type(probe["write_serial"]) is int
            and 1 <= probe["write_serial"] <= 1_000
            and probe["writer"] in WRITERS
            and probe["subject"] == SUBJECT,
            "NOT_ISOLATED_SANDBOX_PROBE")


def decode_probe(file: dict) -> tuple[dict, str]:
    require(type(file) is dict
            and file.get("type") == "file"
            and file.get("name") == "cas-probe-v1.json"
            and file.get("path") == FILE_PATH
            and file.get("encoding") == "base64",
            "EXACT_PRIVATE_SANDBOX_CONTENT")
    blob_sha=file.get("sha")
    require(type(blob_sha) is str and SHA40.fullmatch(blob_sha) is not None,
            "BLOB_SHA40")
    encoded=file.get("content")
    require(type(encoded) is str and 0 < len(encoded) < 10000,
            "BASE64_FILE")
    try:
        raw=base64.b64decode(
            encoded.replace("\r","").replace("\n",""),validate=True
        )
        require(type(file.get("size")) is int and
                file["size"] == len(raw) and 0 < len(raw) < 6000,
                "REMOTE_BYTE_SIZE")
        require(git_blob_sha(raw)==blob_sha,"REMOTE_BLOB_HASH")
        probe=json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, binascii.Error, TypeError):
        raise SandboxWriteBlocked(
            "CLIVOX_A8_SANDBOX_DENIED_PRIVATE_FILE_DECODE"
        ) from None
    validate_probe(probe)
    require(canonical_bytes(probe)==raw,"NOT_CANONICAL_REMOTE_FILE")
    return probe,blob_sha


def fixed_paths(name: str) -> tuple[str,str,str]:
    repo_path,collab_path=a3_expected_paths(name)
    return (repo_path,collab_path,
            repo_path+"/contents/"+FILE_PATH+"?ref="+BRANCH)


def validate_manual_context(env: Mapping[str,str]) -> dict:
    for key,value in (
        ("GITHUB_ACTIONS","true"),
        ("GITHUB_REPOSITORY",CONTROLLER),
        ("GITHUB_REF","refs/heads/main"),
        ("GITHUB_EVENT_NAME","workflow_dispatch"),
        ("GITHUB_WORKFLOW_REF",WORKFLOW_REF),
        ("GITHUB_ACTOR",OWNER),
        ("GITHUB_TRIGGERING_ACTOR",OWNER),
        ("GITHUB_RUN_ATTEMPT","1"),
        (APPROVAL_ENV,APPROVAL),
    ):
        require(env.get(key)==value,"OWNER_MAIN_MANUAL_"+key)
    name=env.get(NAME_ENV)
    require(type(name) is str,"NAME_ENV")
    fixed_paths(name)
    token=env.get(TOKEN_ENV)
    require(type(token) is str and 30<=len(token)<=1024
            and all(32<ord(c)<127 for c in token),
            "MISSING_DEDICATED_SANDBOX_TOKEN")
    serial=env.get(SERIAL_ENV)
    require(type(serial) is str and re.fullmatch(
        r"[1-9][0-9]{0,2}|1000",serial
    ) is not None,"EXPECTED_SERIAL_STRING")
    blob_sha=env.get(SHA_ENV)
    require(type(blob_sha) is str and SHA40.fullmatch(blob_sha) is not None,
            "EXPECTED_BLOB_SHA")
    return {"vault":name,"token":token,"serial":int(serial),"sha":blob_sha}


def allowed_path(name: str, path: str) -> bool:
    return path in fixed_paths(name)


def validate_put(name: str,path: str,body: dict) -> None:
    require(path==fixed_paths(name)[2].split("?ref=")[0],
            "ONLY_EXISTING_SANDBOX_FILE")
    require(type(body) is dict
            and set(body)=={"message","content","sha","branch"}
            and body["branch"]==BRANCH
            and type(body["sha"]) is str
            and SHA40.fullmatch(body["sha"]) is not None
            and body["message"]==
                "clivox: isolated CAS sandbox probe, no media or YouTube",
            "PUT_EXACT_BODY")
    encoded=body["content"]
    require(type(encoded) is str and 0<len(encoded)<10000,
            "PROPOSAL_B64")
    try:
        raw=base64.b64decode(encoded,validate=True)
        obj=json.loads(raw)
    except (ValueError,binascii.Error,UnicodeDecodeError,TypeError):
        raise SandboxWriteBlocked(
            "CLIVOX_A8_SANDBOX_DENIED_PROPOSAL_DECODE"
        ) from None
    validate_probe(obj)
    require(canonical_bytes(obj)==raw,"PROPOSAL_NOT_CANONICAL")
    require(obj["writer"]=="owner-sandbox-verified",
            "WRITER_SANDBOX_ONLY")


def http_get(path: str, token: str) -> tuple[object,str]:
    # The private slug is restricted by the A3 parser and path is a single
    # exact GET from the validated manual context. No redirects or retries.
    require(type(path) is str and len(path)<360
            and not any(c in path for c in ("%","#","..","\r","\n")),
            "UNSAFE_GITHUB_GET_PATH")
    require(type(token) is str and 30<=len(token)<=1024,
            "MISSING_GITHUB_READ_ID")
    require(re.fullmatch(
        r"/repos/" + OWNER +
        r"/clivox-[a-z0-9][a-z0-9-]{3,48}[a-z0-9]"
        r"(/collaborators\?affiliation=all&per_page=100&page=1|"
        r"/contents/clivox-private/sandbox/cas-probe-v1\.json\?ref="
        r"sandbox/b3-a8-cas-probe-20261113)?",
        path
    ) is not None,"DISALLOWED_GET_PATH")
    conn=None
    try:
        conn=http.client.HTTPSConnection(HOST,timeout=12,
                                      context=ssl.create_default_context())
        conn.request("GET",path,headers={
            "Accept":"application/vnd.github+json",
            "Authorization":"Bearer "+token,
            "X-GitHub-Api-Version":API_VERSION,
            "User-Agent":"clivox-a8-cas-sandbox-no-media",
        })
        reply=conn.getresponse()
        raw=reply.read(MAX_RESPONSE+1)
        require(reply.status==200 and len(raw)<=MAX_RESPONSE,
                "PRIVATE_GITHUB_GET_FAIL")
        return json.loads(raw),reply.getheader("Link","")
    except SandboxWriteBlocked:
        raise
    except (OSError,TimeoutError,ValueError,http.client.HTTPException):
        raise SandboxWriteBlocked(
            "CLIVOX_A8_SANDBOX_DENIED_GET_NETWORK_OR_JSON"
        ) from None
    finally:
        if conn is not None:
            conn.close()


def http_put(path: str,token: str,body: dict,*,vault_name: str)->dict:
    validate_put(vault_name,path,body)
    require(type(token) is str and 30<=len(token)<=1024,
            "MISSING_PUT_TOKEN")
    conn=None
    try:
        conn=http.client.HTTPSConnection(HOST,timeout=12,
                                      context=ssl.create_default_context())
        conn.request("PUT",path,body=json.dumps(
            body,separators=(",",":")
        ).encode("utf-8"),headers={
            "Accept":"application/vnd.github+json",
            "Authorization":"Bearer "+token,
            "X-GitHub-Api-Version":API_VERSION,
            "Content-Type":"application/json",
            "User-Agent":"clivox-a8-cas-sandbox-no-media",
        })
        response=conn.getresponse()
        raw=response.read(MAX_RESPONSE+1)
        if response.status==409:
            raise SandboxCASConflict(
                "CLIVOX_A8_SANDBOX_DENIED_STALE_SHA_HTTP_409_NO_RETRY"
            )
        require(response.status==200 and len(raw)<=MAX_RESPONSE,
                "PUT_NO_ACCEPTED_CONFIRMATION")
        parsed=json.loads(raw)
        require(type(parsed) is dict,"PUT_JSON")
        return parsed
    except SandboxCASConflict:
        raise
    except SandboxWriteBlocked:
        raise
    except (OSError,TimeoutError,ValueError,http.client.HTTPException):
        # Unknown PUT outcome => NEVER another write; human must read back.
        raise SandboxWriteBlocked(
            "CLIVOX_A8_SANDBOX_DENIED_UNKNOWN_PUT_OUTCOME_NO_RETRY"
        ) from None
    finally:
        if conn is not None:
            conn.close()


def propose_update(probe:dict,blob_sha:str) -> tuple[dict,dict]:
    validate_probe(probe)
    require(type(blob_sha) is str and SHA40.fullmatch(blob_sha) is not None,
            "PRIOR_GIT_BLOB")
    require(probe["write_serial"]<1000,"SANDBOX_CAP_REACHED")
    proposed={**probe,"write_serial":probe["write_serial"]+1,
              "writer":"owner-sandbox-verified"}
    validate_probe(proposed)
    body={
        "message":"clivox: isolated CAS sandbox probe, no media or YouTube",
        "content":base64.b64encode(canonical_bytes(proposed)).decode("ascii"),
        "sha":blob_sha,
        "branch":BRANCH,
    }
    return proposed,body


def run_owner_sandbox(env:Mapping[str,str], *, get=http_get,
                      put=http_put) -> dict:
    context=validate_manual_context(env)
    paths=fixed_paths(context["vault"])
    repo,repo_link=get(paths[0],context["token"])
    require(repo_link=="","REPO_LIST_PAGINATION")
    validate_private_repository(repo,context["vault"])
    collaborators,collab_link=get(paths[1],context["token"])
    validate_collaborators(collaborators,collab_link)
    contents,content_link=get(paths[2],context["token"])
    require(content_link=="","CONTENT_PAGINATION")
    current,sha=decode_probe(contents)
    require(current["write_serial"]==context["serial"]
            and sha==context["sha"],"STALE_OWNER_FLOOR_NO_PUT")
    proposed,body=propose_update(current,sha)
    put_path=paths[2].split("?ref=")[0]
    validate_put(context["vault"],put_path,body)
    try:
        result=put(put_path,context["token"],body,vault_name=context["vault"])
    except SandboxCASConflict:
        return {
            "stage":"A8_REAL_GITHUB_SANDBOX_CAS_409_HOLD",
            "conflict_observed":True,
            "owner_manual_readback_required":True,
            "automatic_retry_allowed":False,
            "actual_github_put_attempts":1,
            "actual_youtube_api_calls":0,
            "youtube_upload_authorized":False,
            "youtube_schedule_authorized":False,
            "youtube_publish_authorized":False,
        }
    require(type(result) is dict and
            type(result.get("content")) is dict and
            result["content"].get("sha")==git_blob_sha(canonical_bytes(proposed))
            and result["content"].get("path")==FILE_PATH
            and type(result.get("commit")) is dict
            and type(result["commit"].get("sha")) is str
            and SHA40.fullmatch(result["commit"]["sha"]) is not None,
            "PUT_COMMIT_CONFIRMATION_UNTRUSTED")
    observed,link=get(paths[2],context["token"])
    require(link=="","POSTPUT_PAGINATION")
    actual,readback_sha=decode_probe(observed)
    require(actual==proposed
            and readback_sha==result["content"]["sha"],
            "POSTPUT_READBACK_DIFFERS_NO_RETRY")
    return {
        "stage":"A8_REAL_GITHUB_PRIVATE_SANDBOX_CAS_PROBE_ONLY",
        "sandbox_branch_not_main":True,
        "only_test_probe_changed":True,
        "private_metadata_repository_owner_and_acl_validated":True,
        "prior_git_blob_sha_checked_before_put":True,
        "server_put_response_commit_and_blob_verified":True,
        "postput_authenticated_readback_matches":True,
        "new_sandbox_serial":actual["write_serial"],
        "actual_github_get_count":4,
        "actual_github_put_attempts":1,
        "real_production_attempt_ledger_changed":False,
        "independent_external_immutable_anchor_proven":False,
        "real_cross_runner_linearizability_proven":False,
        "automatic_retry_allowed":False,
        "actual_youtube_api_calls":0,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
    }


def fixture_report() -> dict:
    return {
        "stage":"A8_PRIVATE_CAS_SANDBOX_WRITER_FIXTURE_NO_NETWORK",
        "separate_sandbox_branch_and_metadata_file_enforced":True,
        "real_private_github_stale_sha_409_observed_externally":True,
        "actual_live_sandbox_job_executed":False,
        "production_ledger_put_implemented":False,
        "production_cross_runner_global_reservation_proven":False,
        "actual_github_get_count":0,
        "actual_github_put_count":0,
        "actual_youtube_api_calls":0,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
    }


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("fixture","live"),default="fixture")
    args=p.parse_args()
    try:
        output=fixture_report() if args.mode=="fixture" else run_owner_sandbox(os.environ)
    except (SandboxWriteBlocked,VaultReadbackDenied,AttemptBridgeDenied,
            ValueError,KeyError,TypeError):
        raise SystemExit(
            "CLIVOX_A8_SANDBOX_CAS_DENIED_NO_PRODUCTION_LEDGER_NO_YOUTUBE"
        ) from None
    print(json.dumps(output,sort_keys=True))


if __name__=="__main__":
    main()
