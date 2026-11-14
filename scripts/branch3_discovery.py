"""Clivox A1: bounded, YouTube API policy-conservative source references.

Public video metadata and verbatim official statistics are **not** a computed
engagement score, segment retention graph, clip license or future Shorts success.
No API-data-derived metrics, cross-owner aggregation, third-party media download,
creator consent, OAuth write access, video upload or publishing.
Unlicensed metadata has a 7-day expiry in the disposable Actions artifact.
Standard library only, suitable for GitHub-hosted Actions.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import html
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

TARGET_CHANNEL = "UCfPEvy0SefE_5nNlYlY_CyQ"
FLOWMINUTE_CHANNEL = "UCCcL9Q_jqVq6LJmnYUSAFZA"
API_ORIGIN = "https://www.googleapis.com/youtube/v3/"
VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}\Z")
CHANNEL_ID = re.compile(r"UC[A-Za-z0-9_-]{22}\Z")
CATEGORIES = {
    "gaming": ("gaming", "gta", "gta 6", "clutch", "gameplay", "speedrun", "win", "fail"),
    "livestream": ("livestream", "stream", "live", "reaction", "challenge", "streamer"),
    "comedy": ("comedy", "funny", "joke", "laugh", "standup", "podcast", "story"),
    "entertainment": ("entertainment", "surprise", "viral", "reaction", "behind the scenes"),
    "podcast_interview": ("podcast", "interview", "conversation", "episode", "debate"),
}
MAX_VIDEO_IDS = 30
MAX_SEARCH_RESULTS = 10
MAX_API_RESPONSE = 2_000_000
MAX_REPORT_BYTES = 200_000
NON_AUTHORIZED_API_DATA_RETENTION_DAYS = 7  # Artifact expiration, within 30-day ceiling.


class DiscoveryBlocked(ValueError):
    """Fail closed: do not mask errors by inventing video or rights metadata."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise DiscoveryBlocked("CLIVOX_DISCOVERY_DENIED_" + reason)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def utc_timestamp(dt: datetime) -> str:
    require(dt.tzinfo is not None and dt.utcoffset() is not None, "NAIVE_DATETIME")
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def canonical_ids(value: str) -> list[str]:
    require(type(value) is str and len(value) <= 600, "INVALID_INPUT")
    ids = [x.strip() for x in value.split(",") if x.strip()]
    require(1 <= len(ids) <= MAX_VIDEO_IDS, "VIDEO_IDS_LIMIT")
    require(all(VIDEO_ID.fullmatch(x) is not None for x in ids), "INVALID_VIDEO_ID")
    return list(dict.fromkeys(ids))


def api_read(endpoint: str, params: dict[str, str], key: str, *, opener=urlopen) -> dict:
    """Fixed-host API metadata GET only, one request and bounded response."""
    require(endpoint in {"videos", "search"}, "UNSUPPORTED_API_OPERATION")
    require(type(key) is str and len(key) >= 12 and len(key) < 300, "MISSING_METADATA_KEY")
    require(set(params) <= {
        "part", "id", "q", "type", "maxResults", "order", "publishedAfter"
    }, "UNEXPECTED_API_PARAMETER")
    # Never print request URL or exception; URL includes API key.
    url = API_ORIGIN + endpoint + "?" + urlencode({**params, "key": key})
    try:
        with opener(url, timeout=15) as res:
            content = res.read(MAX_API_RESPONSE + 1)
        require(len(content) <= MAX_API_RESPONSE, "RESPONSE_TOO_LARGE")
        data = json.loads(content)
        require(type(data) is dict and type(data.get("items")) is list, "INVALID_API_RESULT")
        require(len(data["items"]) <= 50, "TOO_MANY_API_ITEMS")
        return data
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError):
        # Do not leak key through HTTP errors, tracebacks or logs.
        raise DiscoveryBlocked("CLIVOX_DISCOVERY_DENIED_METADATA_API_UNAVAILABLE") from None


def collect_public_videos(
    *, mode: str, category: str, ids: str, query: str, key: str,
    now: datetime, opener=urlopen,
) -> list[dict]:
    require(category in CATEGORIES, "INVALID_CATEGORY")
    require(mode in ("ids", "query"), "UNSUPPORTED_MODE")
    require(now.tzinfo is not None, "NAIVE_NOW")
    if mode == "ids":
        selected = canonical_ids(ids)
        require(not query.strip(), "CONFLICTING_QUERY")
    else:
        require(not ids.strip(), "CONFLICTING_IDS")
        require(type(query) is str and 3 <= len(query.strip()) <= 90, "INVALID_QUERY")
        # Exactly one search page, recent window and at most ten candidate IDs.
        since = utc_timestamp(now - timedelta(days=14))
        result = api_read("search", {
            "part": "snippet", "q": query.strip(), "type": "video",
            "maxResults": str(MAX_SEARCH_RESULTS), "order": "viewCount",
            "publishedAfter": since,
        }, key, opener=opener)
        raw_ids = [
            item.get("id", {}).get("videoId")
            for item in result["items"] if type(item) is dict
        ]
        selected = list(dict.fromkeys(
            video_id for video_id in raw_ids
            if type(video_id) is str and VIDEO_ID.fullmatch(video_id)
        ))
        if not selected:
            return []
    result = api_read("videos", {
        "part": "snippet,statistics,contentDetails", "id": ",".join(selected)
    }, key, opener=opener)
    valid_ids = set(selected)
    return [
        item for item in result["items"]
        if type(item) is dict and item.get("id") in valid_ids
    ]


def parse_datetime(value: object) -> datetime:
    require(type(value) is str and value.endswith("Z") and len(value) < 36, "BAD_PUBLISHED_DATE")
    try:
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
        require(dt.tzinfo is not None, "BAD_PUBLISHED_DATE")
        return dt
    except (TypeError, ValueError):
        raise DiscoveryBlocked("CLIVOX_DISCOVERY_DENIED_BAD_PUBLISHED_DATE") from None


def public_count(stats: dict, key: str) -> int | None:
    value = stats.get(key)
    if type(value) is not str or not value.isdecimal() or len(value) > 20:
        return None
    count = int(value)
    return count if count >= 0 else None


def build_report(
    items: list[dict], *, category: str, mode: str, query: str,
    now: datetime, fixture: bool,
) -> dict:
    require(category in CATEGORIES, "INVALID_CATEGORY")
    require(mode in {"ids", "query", "fixture"}, "INVALID_REPORT_MODE")
    require(now.tzinfo is not None and now.utcoffset() is not None, "NAIVE_DATETIME")
    require(type(items) is list and len(items) <= 50, "INVALID_ITEMS")
    candidates: list[dict] = []
    seen: set[str] = set()
    for item in items:
        if type(item) is not dict:
            continue
        video_id = item.get("id")
        snippet, statistics, content = (
            item.get("snippet"), item.get("statistics"), item.get("contentDetails")
        )
        if not (type(video_id) is str and VIDEO_ID.fullmatch(video_id)
                and type(snippet) is dict and type(statistics) is dict
                and type(content) is dict):
            continue
        channel_id = snippet.get("channelId")
        if not (type(channel_id) is str and CHANNEL_ID.fullmatch(channel_id)):
            continue
        if video_id in seen:
            continue
        seen.add(video_id)
        published = parse_datetime(snippet.get("publishedAt"))
        # Future-dated source metadata must never be taken as a real video.
        if published > now:
            continue
        title = html.unescape(str(snippet.get("title", ""))).strip()[:160]
        if not title:
            continue
        view_count = public_count(statistics, "viewCount")
        like_count = public_count(statistics, "likeCount")
        comment_count = public_count(statistics, "commentCount")
        candidates.append({
            "source_video_id": video_id,
            "source_channel_id": channel_id,
            "source_url": f"https://www.youtube.com/watch?v={video_id}",
            "source_title": title,
            "source_channel_title": html.unescape(str(snippet.get("channelTitle", ""))).strip()[:100],
            "source_published_utc": utc_timestamp(published),
            # Preserve original YouTube ISO-8601 value; no calculated
            # duration/rate/view velocity or API-data-derived metric.
            "source_duration_iso8601": content.get("duration") if (
                type(content.get("duration")) is str
                and len(content["duration"]) <= 50
                and content["duration"].startswith("P")
            ) else None,
            "public_stats": {
                "views": view_count, "likes": like_count, "comments": comment_count,
            },
            "permission_state": "UNVERIFIED",
            "rights_holder_identity_verified": False,
            "clivox_commercial_clipping_rights_verified": False,
            "underlying_game_music_guest_rights_cleared": False,
            "source_media_download_allowed": False,
            "segment_selected": False,
            "quote_verified": False,
            "ready_to_publish": False,
            "youtube_upload_authorized": False,
            "sourcing_status": "RESEARCH_ONLY_PUBLIC_METADATA",
        })
    # Stable lexical ID ordering, not comparative YouTube analytics.
    candidates.sort(key=lambda c: c["source_video_id"])
    report = {
        "schema_version": 1,
        "channel_id": TARGET_CHANNEL,
        "channel_handle": "@ClivoxPulse",
        "stage": "A1_DISCOVERY_PUBLIC_METADATA_ONLY",
        "mode": mode,
        "category": category,
        "query": query.strip()[:90] if mode == "query" else None,
        "retrieved_at_utc": utc_timestamp(now),
        "non_authorized_api_data_expires_at_utc": utc_timestamp(
            now + timedelta(days=NON_AUTHORIZED_API_DATA_RETENTION_DAYS)
        ),
        "non_authorized_api_data_retention_days": NON_AUTHORIZED_API_DATA_RETENTION_DAYS,
        "disallowed_api_data_derived_scores_generated": False,
        "cross_owner_statistics_aggregated": False,
        "is_synthetic_fixture": fixture,
        "source_of_numbers": "synthetic_test_fixture" if fixture else "youtube_data_api_v3_public_statistics",
        "all_candidates_permission_unverified": True,
        "release_or_media_acquisition_allowed": False,
        "youtube_api_write_calls": 0,
        "upstream_clip_rights_human_review_required": True,
        "method": "bounded official source metadata, ID-sorted; no calculated engagement or popularity metrics",
        "explanation": "Official statistics are displayed without new ratios, rankings or heatmaps. Public video data does not identify most-replayed timestamps, grant footage rights, predict Shorts performance or authorize downloading/publishing.",
        "candidates": candidates,
    }
    require(len(json.dumps(report).encode("utf-8")) <= MAX_REPORT_BYTES, "REPORT_TOO_LARGE")
    return report


def mock_fixture() -> list[dict]:
    """Synthetic metadata for exercising the cloud workflow; never claim live views."""
    return [
        {"id": "AbCdEf12345",
         "snippet": {"channelId": "UC" + "a" * 22, "title": "Synthetic gaming clutch highlight",
                     "channelTitle": "SYNTHETIC TEST CHANNEL", "publishedAt": "2026-11-10T10:00:00Z"},
         "statistics": {"viewCount": "12500", "likeCount": "700", "commentCount": "65"},
         "contentDetails": {"duration": "PT21M15S"}},
        {"id": "GhIjKl67890",
         "snippet": {"channelId": "UC" + "b" * 22, "title": "Synthetic funny livestream reaction",
                     "channelTitle": "SYNTHETIC TEST CHANNEL", "publishedAt": "2026-11-11T11:30:00Z"},
         "statistics": {"viewCount": "2500", "likeCount": "90", "commentCount": "14"},
         "contentDetails": {"duration": "PT1H02M04S"}},
    ]


def run_cli() -> None:
    parser = argparse.ArgumentParser(description="Clivox A1 research-only public YouTube metadata discovery")
    parser.add_argument("--mode", choices=("fixture", "ids", "query"), required=True)
    parser.add_argument("--category", choices=tuple(CATEGORIES), required=True)
    parser.add_argument("--ids", default="")
    parser.add_argument("--query", default="")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        now = now_utc()
        if args.mode == "fixture":
            require(not args.ids.strip() and not args.query.strip(), "FIXTURE_MUST_BE_ISOLATED")
            # Fix example dates so CI results remain stable even if historical.
            items = mock_fixture()
        else:
            key = os.environ.get("CLIVOX_YOUTUBE_METADATA_API_KEY", "")
            require(bool(key), "MISSING_PUBLIC_METADATA_API_KEY")
            items = collect_public_videos(
                mode=args.mode, category=args.category, ids=args.ids,
                query=args.query, key=key, now=now,
            )
        report = build_report(
            items, category=args.category, mode=args.mode, query=args.query,
            now=now, fixture=(args.mode == "fixture"),
        )
        # Never write a report into tracked public source or a hidden secret directory.
        require(args.out.suffix.lower() == ".json", "REPORT_MUST_BE_JSON")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("CLIVOX_A1_RESEARCH_ONLY candidates=" + str(len(report["candidates"]))
              + " mode=" + args.mode + " rights=UNVERIFIED videos_downloaded=0 youtube_writes=0")
    except DiscoveryBlocked as exc:
        raise SystemExit(str(exc)) from None


if __name__ == "__main__":
    run_cli()
