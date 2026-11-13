"""CLIVOX A7/A8 bounded owner-only YouTube upload inventory READ-ONLY.

Manual/main owner-protected live mode fetches Clivox channels.mine, exhausts
the uploads playlist up to a strict cap and validates status via videos.list.
No upload, file media, video edits, schedule, remote inventory IDs in output,
or assertion that YouTube has authoritative/instantaneous full inventory.
An ambiguous attempted upload always remains blocked for human reconciliation.

No owner Google OAuth secrets exist in the repo or in PR CI.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
from datetime import datetime
import http.client
import json
import os
import re
import ssl
from urllib.parse import urlencode, parse_qs, urlsplit

from scripts.branch3_a7_readonly_youtube import (
    EXPECTED_CHANNEL, OLD_CHANNEL, YOUTUBE_HOST, OAUTH_HOST, READONLY_SCOPE,
    CHANNEL_PATH, VIDEO_ID, ChannelBindingDenied, require,
    refresh_readonly_token, validate_channels_mine, MAX_JSON,
)

REPO = "Tirthanand17/taskless-lab"
WORKFLOW_REF = (REPO +
    "/.github/workflows/branch3-clivox-a8-inventory-readonly.yml@refs/heads/main")
ENABLE_ENV = "CLIVOX_A8_INVENTORY_READ_APPROVED"
ENV_VALUE = "approved-a8-inventory-readonly-v1"
CLIENT_ENV = "CLIVOX_A7_READONLY_CLIENT_ID"
SECRET_ENV = "CLIVOX_A7_READONLY_CLIENT_SECRET"
REFRESH_ENV = "CLIVOX_A7_READONLY_REFRESH_TOKEN"
UPLOADS = "UU" + EXPECTED_CHANNEL[2:]
MAX_PER_PAGE = 50
MAX_PAGES = 20
MAX_VIDEOS = MAX_PER_PAGE * MAX_PAGES
MAX_QUERY = 230
PAGE_TOKEN = re.compile(r"[A-Za-z0-9_-]{1,170}\Z")
PRIVACY = frozenset(("private", "unlisted", "public"))


def require_context(env: Mapping[str, str]) -> None:
    for key, expected in (
        ("GITHUB_ACTIONS", "true"),
        ("GITHUB_REPOSITORY", REPO),
        ("GITHUB_EVENT_NAME", "workflow_dispatch"),
        ("GITHUB_REF", "refs/heads/main"),
        ("GITHUB_WORKFLOW_REF", WORKFLOW_REF),
        ("GITHUB_ACTOR", "Tirthanand17"),
        ("GITHUB_TRIGGERING_ACTOR", "Tirthanand17"),
        ("GITHUB_RUN_ATTEMPT", "1"),
        (ENABLE_ENV, ENV_VALUE),
    ):
        require(env.get(key) == expected, "MANUAL_OWNER_CONTEXT_" + key)
    for key in (CLIENT_ENV, SECRET_ENV, REFRESH_ENV):
        val = env.get(key)
        require(type(val) is str and 16 < len(val) < 4000
                and all(c not in val for c in ("\r", "\n")),
                "MISSING_DISTINCT_SECRET_" + key)


def playlist_path(token: str | None = None) -> str:
    require(token is None or (
        type(token) is str and PAGE_TOKEN.fullmatch(token) is not None
    ), "PAGE_TOKEN")
    args = {"part":"contentDetails", "playlistId": UPLOADS,
            "maxResults": MAX_PER_PAGE}
    if token is not None:
        args["pageToken"] = token
    return "/youtube/v3/playlistItems?" + urlencode(args)


def videos_path(video_ids: tuple[str, ...]) -> str:
    require(type(video_ids) is tuple and 1 <= len(video_ids) <= MAX_PER_PAGE
            and len(set(video_ids)) == len(video_ids)
            and all(type(i) is str and VIDEO_ID.fullmatch(i) is not None
                    for i in video_ids), "VIDEO_BATCH_IDS")
    return "/youtube/v3/videos?" + urlencode({
        "part":"snippet,status", "id":",".join(video_ids)
    })


def allowlisted_http(host: str, method: str, path: str,
                     body: bytes | None = None,
                     bearer: str | None = None) -> dict:
    """Fixed Google endpoints, exact API method, no redirects or bearer logs."""
    require(type(path) is str and len(path) <= 3200
            and all(ch not in path for ch in ("\n","\r","#"))
            and "access_token" not in path
            and "refresh_token" not in path
            and "client_secret" not in path,
            "UNSAFE_GOOGLE_PATH")
    if host == OAUTH_HOST:
        require(method == "POST" and path == "/token"
                and type(body) is bytes and len(body) < 16000
                and bearer is None, "OAUTH_REFRESH_ONLY")
    else:
        require(host == YOUTUBE_HOST and method == "GET"
                and body is None and bearer is not None
                and type(bearer) is str and 20 < len(bearer) < 4096
                and not any(x in bearer for x in ("\n", "\r")),
                "YOUTUBE_READ_ONLY")
        if path != CHANNEL_PATH:
            obj = urlsplit(path)
            require(obj.path in ("/youtube/v3/playlistItems",
                                 "/youtube/v3/videos")
                    and obj.scheme == "" and obj.netloc == "",
                    "DISALLOWED_GOOGLE_ENDPOINT")
            args = parse_qs(obj.query, strict_parsing=True)
            if obj.path.endswith("playlistItems"):
                require(set(args) in (
                    {"part","playlistId","maxResults"},
                    {"part","playlistId","maxResults","pageToken"},
                ) and args["part"] == ["contentDetails"]
                and args["playlistId"] == [UPLOADS]
                and args["maxResults"] == [str(MAX_PER_PAGE)],
                "DISALLOWED_PLAYLIST_QUERY")
                token = args.get("pageToken")
                require(token is None or (
                    len(token) == 1 and PAGE_TOKEN.fullmatch(token[0]) is not None
                ), "DISALLOWED_PAGE_TOKEN")
            else:
                require(set(args) == {"part","id"}
                        and args["part"] == ["snippet,status"],
                        "DISALLOWED_VIDEOS_QUERY")
                ids=tuple(args["id"][0].split(","))
                videos_path(ids)
    conn = None
    try:
        conn = http.client.HTTPSConnection(host, timeout=12,
                                          context=ssl.create_default_context())
        headers={"Accept":"application/json",
                 "User-Agent":"clivox-a8-private-inventory-readonly"}
        if bearer is not None:
            headers["Authorization"]="Bearer "+bearer
        if body is not None:
            headers["Content-Type"]="application/x-www-form-urlencoded"
        conn.request(method, path, body=body, headers=headers)
        response=conn.getresponse()
        data=response.read(MAX_JSON + 1)
        require(response.status==200 and len(data)<=MAX_JSON,
                "API_REQUEST_FAILED_CLOSED")
        obj=json.loads(data)
        require(type(obj) is dict, "API_JSON_OBJECT")
        return obj
    except ChannelBindingDenied:
        raise
    except (OSError,TimeoutError,ValueError,http.client.HTTPException):
        # Never export credentials, private IDs, body contents or raw exceptions.
        raise ChannelBindingDenied("CLIVOX_A7_DENY_INVENTORY_NETWORK") from None
    finally:
        if conn is not None:
            conn.close()


def validate_playlist_page(page: dict, *, seen_ids: set[str],
                           previous_tokens: set[str]) -> tuple[tuple[str, ...], str | None]:
    require(type(page) is dict and page.get("kind") ==
            "youtube#playlistItemListResponse", "PLAYLIST_RESPONSE_KIND")
    items = page.get("items")
    require(type(items) is list and len(items) <= MAX_PER_PAGE,
            "PLAYLIST_PAGE_SIZE")
    ids=[]
    for item in items:
        require(type(item) is dict and type(item.get("contentDetails")) is dict,
                "PLAYLIST_ITEM_CONTENT")
        video_id=item["contentDetails"].get("videoId")
        require(type(video_id) is str
                and VIDEO_ID.fullmatch(video_id) is not None
                and video_id not in seen_ids
                and video_id not in ids,
                "DUPLICATE_OR_WRONG_VIDEO_ID")
        ids.append(video_id)
    token=page.get("nextPageToken")
    require(token is None or (
        type(token) is str and PAGE_TOKEN.fullmatch(token) is not None
        and token not in previous_tokens
    ), "INVALID_OR_REPLAYED_PAGE_TOKEN")
    return tuple(ids), token


def validate_video_batch(reply: dict, expected_ids: tuple[str, ...]) -> dict:
    require(type(reply) is dict
            and reply.get("kind") == "youtube#videoListResponse",
            "VIDEO_RESPONSE_KIND")
    items=reply.get("items")
    require(type(items) is list and len(items) == len(expected_ids),
            "VIDEO_BATCH_INCOMPLETE")
    expected=set(expected_ids)
    counted={"private":0,"unlisted":0,"public":0,"scheduled_private":0}
    seen=set()
    for item in items:
        require(type(item) is dict and type(item.get("id")) is str
                and item["id"] in expected and item["id"] not in seen,
                "WRONG_DUPLICATE_OR_OTHER_CHANNEL_VIDEO")
        seen.add(item["id"])
        snippet=item.get("snippet")
        require(type(snippet) is dict
                and snippet.get("channelId") == EXPECTED_CHANNEL,
                "WRONG_VIDEO_CHANNEL_ID")
        status=item.get("status")
        require(type(status) is dict
                and status.get("privacyStatus") in PRIVACY,
                "MISSING_VIDEO_PRIVACY")
        privacy=status["privacyStatus"]
        counted[privacy]+=1
        if "publishAt" in status and status["publishAt"] is not None:
            stamp=status["publishAt"]
            require(privacy=="private" and type(stamp) is str
                    and len(stamp) <= 40, "INVALID_SCHEDULED_STATUS")
            try:
                parsed=datetime.fromisoformat(stamp.replace("Z","+00:00"))
                require(parsed.tzinfo is not None and parsed.utcoffset() is not None,
                        "SCHEDULE_TIMEZONE")
            except ValueError:
                raise ChannelBindingDenied(
                    "CLIVOX_A7_DENY_SCHEDULE_DATE"
                ) from None
            counted["scheduled_private"]+=1
    require(seen==expected, "VIDEO_RESPONSE_ID_SET_MISMATCH")
    return counted


def inspect_uploaded_inventory(
    token: str, *, http_call=allowlisted_http
) -> dict:
    """Enumerate bounded uploads pages and video statuses; no media or IDs out."""
    require(type(token) is str and 20 < len(token) < 4096,
            "MISSING_BEARER")
    mine=http_call(YOUTUBE_HOST,"GET",CHANNEL_PATH,None,token)
    identity=validate_channels_mine(mine)
    require(identity["expected_channel_id"]==EXPECTED_CHANNEL
            and identity["uploads_playlist"] == UPLOADS,
            "CROSS_CHANNEL_UPLOADS")
    next_token=None
    visited_tokens=set()
    video_ids=[]
    seen_ids=set()
    pages=0
    total={"private":0,"unlisted":0,"public":0,"scheduled_private":0}
    while True:
        require(pages < MAX_PAGES, "UPLOADS_INVENTORY_TOO_LARGE_TO_COMPLETE")
        page=http_call(YOUTUBE_HOST,"GET",playlist_path(next_token),None,token)
        new_ids, next_token=validate_playlist_page(
            page, seen_ids=seen_ids, previous_tokens=visited_tokens
        )
        pages+=1
        video_ids.extend(new_ids)
        seen_ids.update(new_ids)
        require(len(video_ids) <= MAX_VIDEOS, "INVENTORY_CAP")
        if next_token is None:
            break
        visited_tokens.add(next_token)
    for i in range(0,len(video_ids),MAX_PER_PAGE):
        chunk=tuple(video_ids[i:i+MAX_PER_PAGE])
        response=http_call(YOUTUBE_HOST,"GET",videos_path(chunk),None,token)
        counts=validate_video_batch(response,chunk)
        for field,num in counts.items():
            total[field]+=num
    require(sum(total[k] for k in PRIVACY) == len(video_ids),
            "VIDEO_STATUS_COUNT_INCOMPLETE")
    return {
        "stage":"A8_OWNER_READONLY_CLIVOX_UPLOAD_INVENTORY_SNAPSHOT",
        "channel_id": EXPECTED_CHANNEL,
        "owner_google_channel_identity_matched":True,
        "uploaded_playlist_pagination_exhausted_within_limit":True,
        "uploaded_playlist_pages_checked":pages,
        "uploaded_playlist_videos_checked":len(video_ids),
        "statuses_checked_through_videos_list":True,
        "private_count":total["private"],
        "unlisted_count":total["unlisted"],
        "public_count":total["public"],
        "private_with_schedule_count":total["scheduled_private"],
        "youtube_readonly_get_count":1+pages+(len(video_ids)+MAX_PER_PAGE-1)//MAX_PER_PAGE,
        "real_time_remote_completeness_guaranteed":False,
        "exact_uploaded_binary_sha256_verified":False,
        "creator_licenses_verified":0,
        "ambiguous_ledger_attempt_automatically_reconciled":False,
        "automatic_duplicate_retry_authorized":False,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
        "actual_youtube_write_calls":0,
        "note":"Bounded owner-only metadata snapshot, not proof of all past uploads, absent duplicates or rights."
    }


def run_owner_inventory(env: Mapping[str,str], *,
                        http_call=allowlisted_http) -> dict:
    require_context(env)
    access=refresh_readonly_token(
        client_id=env[CLIENT_ENV],
        client_secret=env[SECRET_ENV],
        refresh_token=env[REFRESH_ENV],
        http_call=http_call
    )
    return inspect_uploaded_inventory(access,http_call=http_call)


def fixture_report() -> dict:
    return {
        "stage":"A8_EXHAUSTIVE_BOUNDED_INVENTORY_FIXTURE_NOT_CONNECTED",
        "channel_id":EXPECTED_CHANNEL,
        "read_only_pagination_implemented":True,
        "read_only_videos_status_validation_implemented":True,
        "real_owner_google_oauth_configured":False,
        "real_remote_inventory_readback_completed":False,
        "real_time_remote_completeness_guaranteed":False,
        "creator_licenses_verified":0,
        "youtube_get_calls":0,
        "youtube_write_calls":0,
        "automatic_upload_retry_authorized":False,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
    }


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("fixture","live"),default="fixture")
    args=p.parse_args()
    try:
        data=fixture_report() if args.mode=="fixture" else run_owner_inventory(os.environ)
    except (ChannelBindingDenied, TypeError, KeyError, ValueError):
        raise SystemExit("CLIVOX_A8_INVENTORY_DENIED_NO_YOUTUBE_WRITES") from None
    print(json.dumps(data,sort_keys=True))


if __name__ == "__main__":
    main()
