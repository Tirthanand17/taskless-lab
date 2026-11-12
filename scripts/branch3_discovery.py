"""Clivox A1: bounded, public-metadata-only YouTube discovery and source ranking.

No video, captions, transcription, audio, creator credentials, publishing OAuth, or
third-party source download. This module never creates an approved-rights record.
Public engagement is NOT evidence of clipping rights or future Shorts performance.
Standard library only, suitable for GitHub-hosted Actions.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import html
import json
import math
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
DURATION = re.compile(
    r"P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?"
    r"(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?\Z"
)
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


def parse_duration(value: object) -> int | None:
    if type(value) is not str:
        return None
    match = DURATION.fullmatch(value)
    if not match:
        return None
    parts = {k: int(v or 0) for k, v in match.groupdict().items()}
    seconds = (parts["days"] * 86400 + parts["hours"] * 3600
               + parts["minutes"] * 60 + parts["seconds"])
    return seconds if seconds > 0 else None


def public_count(stats: dict, key: str) -> int | None:
    value = stats.get(key)
    if type(value) is not str or not value.isdecimal() or len(value) > 20:
        return None
    count = int(value)
    return count if count >= 0 else None


def source_score(
    *, title: str, category: str, age_hours: float,
    views: int | None, likes: int | None, comments: int | None,
) -> tuple[int, dict]:
    """Research heuristic, not a prediction or segment-quality evaluation."""
    require(category in CATEGORIES and age_hours >= 0, "INVALID_SCORE_SOURCE")
    # Recency, early viewing velocity and engagement. Public likes can be hidden.
    view_velocity = (views / max(age_hours, 12)) if views is not None else None
    velocity_component = min(1., math.log10(1 + view_velocity) / 5) if view_velocity is not None else 0.
    engagement_ratio = None
    if views and views > 0 and likes is not None and comments is not None:
        engagement_ratio = min(1., (likes + comments * 3) / views)
    engagement_component = min(1., engagement_ratio / .10) if engagement_ratio is not None else 0.
    recency_component = max(0., 1 - age_hours / (30 * 24))
    terms = CATEGORIES[category]
    title_lower = title.lower()
    overlap = sum(bool(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", title_lower)) for term in terms)
    relevance_component = min(1., overlap / 2)
    # Only 20% topic-match: avoid ranking solely by clickbait titles.
    value = round(100 * (
        .40 * velocity_component + .22 * engagement_component
        + .18 * recency_component + .20 * relevance_component
    ))
    components = {
        "views_per_hour": round(view_velocity, 2) if view_velocity is not None else None,
        "observed_engagement_ratio": round(engagement_ratio, 5) if engagement_ratio is not None else None,
        "source_title_keyword_matches": overlap,
        "velocity_component": round(velocity_component, 4),
        "engagement_component": round(engagement_component, 4),
        "recency_component": round(recency_component, 4),
        "relevance_component": round(relevance_component, 4),
    }
    return max(0, min(100, value)), components


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
        # Ignore impossible future-dated entries; no guessing about a source.
        age = (now - published).total_seconds() / 3600.
        if age < 0:
            continue
        title = html.unescape(str(snippet.get("title", ""))).strip()[:160]
        if not title:
            continue
        view_count = public_count(statistics, "viewCount")
        like_count = public_count(statistics, "likeCount")
        comment_count = public_count(statistics, "commentCount")
        score, details = source_score(
            title=title, category=category, age_hours=age,
            views=view_count, likes=like_count, comments=comment_count,
        )
        candidates.append({
            "source_video_id": video_id,
            "source_channel_id": channel_id,
            "source_url": f"https://www.youtube.com/watch?v={video_id}",
            "source_title": title,
            "source_channel_title": html.unescape(str(snippet.get("channelTitle", ""))).strip()[:100],
            "source_published_utc": utc_timestamp(published),
            "source_age_hours": round(age, 2),
            "source_duration_seconds": parse_duration(content.get("duration")),
            "public_stats": {
                "views": view_count, "likes": like_count, "comments": comment_count,
            },
            "research_priority_score_0_to_100": score,
            "score_components": details,
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
    candidates.sort(key=lambda c: (-c["research_priority_score_0_to_100"], c["source_video_id"]))
    report = {
        "schema_version": 1,
        "channel_id": TARGET_CHANNEL,
        "channel_handle": "@ClivoxPulse",
        "stage": "A1_DISCOVERY_PUBLIC_METADATA_ONLY",
        "mode": mode,
        "category": category,
        "query": query.strip()[:90] if mode == "query" else None,
        "retrieved_at_utc": utc_timestamp(now),
        "is_synthetic_fixture": fixture,
        "source_of_numbers": "synthetic_test_fixture" if fixture else "youtube_data_api_v3_public_statistics",
        "all_candidates_permission_unverified": True,
        "release_or_media_acquisition_allowed": False,
        "youtube_api_write_calls": 0,
        "upstream_clip_rights_human_review_required": True,
        "method": "bounded source-video metadata, not segment virality prediction",
        "explanation": "A score prioritizes full videos for human review. It does not identify an exact clip, grant rights, certify accuracy, predict a viral Short, or authorize downloading/publishing.",
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
