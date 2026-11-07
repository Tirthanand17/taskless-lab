"""B4e9 fail-closed cross-run YouTube insertion attempt fence.

Future explicitly approved, manually dispatched GitHub artifact publication ONLY.
Create two GitHub tag refs atomically *before* videos.insert is attempted:
one per channel+episode, one per channel+publishAt slot. GitHub refuses
existing names; timeout, 403, 409, 422 or unknown response all STOP (NO RETRY).
No automatic deletion of these tags, even if upload never started.
This is NOT equivalent to a protected production database or owner/rights QA:
admins can delete refs; a production gateway still needs independent audit.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
import re
from typing import Callable
from urllib.request import Request, urlopen

REPO="Tirthanand17/taskless-lab"
EXACT_WORKFLOW="Publish Artifact to YouTube"
CHANNEL=re.compile(r"UC[A-Za-z0-9_-]{22}\Z")
EPISODE=re.compile(r"[A-Za-z0-9_-]{8,100}\Z")
TIME=re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\Z")
COMMIT=re.compile(r"[0-9a-f]{40}\Z")
HEX64=re.compile(r"[0-9a-f]{64}\Z")


class AttemptFenceUnavailable(ValueError):
    """No remote ref proof; do not initiate another upload."""


def _need(condition: bool, reason: str) -> None:
    if not condition:
        raise AttemptFenceUnavailable(reason)


def refs_for(channel_id: str, episode_id: str, publish_at_utc: str) -> tuple[str,str]:
    _need(type(channel_id) is str and CHANNEL.fullmatch(channel_id) is not None,
          "Invalid intended channel")
    _need(type(episode_id) is str and EPISODE.fullmatch(episode_id) is not None,
          "Invalid episode identity")
    _need(type(publish_at_utc) is str and TIME.fullmatch(publish_at_utc) is not None,
          "Expected exact UTC-Z publish slot")
    # SHA256 avoids leaking raw episode IDs/channel names in public Git refs;
    # those values may still be guessable. No secrets in ref names.
    unique_episode=sha256(("fm-b4e9-episode-v1\0"+channel_id+"\0"+episode_id)
                          .encode("utf8")).hexdigest()
    unique_slot=sha256(("fm-b4e9-slot-v1\0"+channel_id+"\0"+publish_at_utc)
                       .encode("utf8")).hexdigest()
    return (
        "refs/tags/flowminute-attempt-episode-v1/"+unique_episode,
        "refs/tags/flowminute-attempt-slot-v1/"+unique_slot,
    )


def _post_ref_api(url: str, body: bytes, headers: dict[str,str]) -> tuple[int,dict]:
    # Called ONLY after explicit Github runner context guards pass.
    req=Request(url, data=body, method="POST", headers=headers)
    with urlopen(req,timeout=12) as response:
        status=response.status
        raw=response.read(12000)
    parsed=json.loads(raw)
    if type(parsed) is not dict:
        raise AttemptFenceUnavailable("GitHub did not return a reference object")
    return status,parsed


def reserve_github_attempt_before_insert(
    *, channel_id: str, episode_id: str, publish_at_utc: str,
    approved_mp4_sha256: str, environment: dict[str,str] | None = None,
    post: Callable | None = None,
) -> dict:
    """One way GitHub tag reservations. No YouTube request is made here.

    Does not retry any ambiguous GitHub POST. If first ref was created but the
    second fails, the first remains permanently reserved, fail closed.
    """
    env=dict(os.environ if environment is None else environment)
    _need(env.get("GITHUB_ACTIONS")=="true"
          and env.get("GITHUB_EVENT_NAME")=="workflow_dispatch"
          and env.get("GITHUB_REF")=="refs/heads/main"
          and env.get("GITHUB_REPOSITORY")==REPO
          and env.get("GITHUB_WORKFLOW")==EXACT_WORKFLOW
          and env.get("PUBLISH_ENABLED")=="true",
          "Not a fully guarded manual owner production workflow")
    token=env.get("GH_TOKEN")
    sha=env.get("GITHUB_SHA")
    _need(type(token) is str and len(token)>=16 and "\n" not in token
          and "\r" not in token,
          "GitHub Actions restricted write token required")
    _need(type(sha) is str and COMMIT.fullmatch(sha) is not None,
          "Trusted main commit SHA missing")
    _need(type(approved_mp4_sha256) is str
          and HEX64.fullmatch(approved_mp4_sha256) is not None,
          "Approved exact video bytes must be pinned")
    names=refs_for(channel_id,episode_id,publish_at_utc)
    poster=_post_ref_api if post is None else post
    url="https://api.github.com/repos/"+REPO+"/git/refs"
    headers={
        "Accept":"application/vnd.github+json",
        "Content-Type":"application/json",
        "Authorization":"Bearer "+token,
        "X-GitHub-Api-Version":"2026-03-10",
    }
    # Never log request headers, raw token, URL query or body.
    for name in names:
        body=json.dumps({"ref":name,"sha":sha},
                        separators=(",",":"),sort_keys=True).encode("utf8")
        try:
            status,response=poster(url,body,headers)
            _need(status==201 and type(response) is dict
                  and response.get("ref")==name
                  and type(response.get("object")) is dict
                  and response["object"].get("sha")==sha,
                  "Remote tag was not confirmed created exactly once")
        except BaseException:
            # Never attempt a second POST after timeout/conflict/unknown reply.
            raise AttemptFenceUnavailable(
                "GitHub attempt ref rejected/ambiguous: NO NEW YOUTUBE INSERT"
            ) from None
    return {
        "status":"B4E9_GITHUB_REF_ATTEMPT_RESERVED_BEFORE_INSERT",
        "episode_ref_sha256":names[0].split("/")[-1],
        "slot_ref_sha256":names[1].split("/")[-1],
        "reservations_completed":2,
        "youtube_insert_called_by_this_function":False,
        "ref_deletion_or_retry_allowed":False,
        "cross_run_duplicate_attempt_blocked_until_tags_deleted":True,
        "independent_channel_facts_rights_or_youtube_readback_verified":False,
    }
