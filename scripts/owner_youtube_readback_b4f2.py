"""B4f2 owner-authenticated read-only channel and processed video proof.

Stops wrong OAuth channel uploads. Later refuses to mark schedule verified
until private status, finished processing, thumbnail and caption-track readback.
This module has no OAuth, database or insert; tests use fake injected clients.
"""
from __future__ import annotations
import re
from datetime import datetime, timezone

CHANNEL_ID=re.compile(r"UC[A-Za-z0-9_-]{22}\Z")
VIDEO_ID=re.compile(r"[A-Za-z0-9_-]{11}\Z")


class OwnerYouTubeReadbackRefused(ValueError):
    """Wrong or ambiguous owner channel, or incomplete readback."""


def _require(ok: bool, reason: str) -> None:
    if not ok:
        raise OwnerYouTubeReadbackRefused(reason)


def _same_utc_instant(actual: object, pinned_utc: str) -> bool:
    """Compare API RFC3339 offset/precision to strict owner-pinned UTC-Z."""
    if type(actual) is not str or type(pinned_utc) is not str:
        return False
    try:
        actual_time=datetime.fromisoformat(actual.replace("Z","+00:00"))
        expected_time=datetime.fromisoformat(pinned_utc.replace("Z","+00:00"))
    except ValueError:
        return False
    return (actual_time.tzinfo is not None and
            expected_time.tzinfo is not None and
            actual_time.astimezone(timezone.utc) ==
            expected_time.astimezone(timezone.utc))


def verify_authenticated_owner_channel(youtube: object, expected_channel_id: str) -> dict:
    """READ-ONLY channels.list(mine=true,part=id) BEFORE any upload."""
    _require(isinstance(expected_channel_id,str) and
             CHANNEL_ID.fullmatch(expected_channel_id) is not None,
             "Malformed target channel ID: no upload")
    try:
        response=youtube.channels().list(part="id",mine=True,maxResults=2).execute()
    except Exception:
        raise OwnerYouTubeReadbackRefused(
            "Owner-authenticated channels.list unavailable; stop before insert"
        ) from None
    _require(type(response) is dict, "Malformed owner channel response")
    entries=response.get("items")
    _require(type(entries) is list and len(entries)==1 and
             type(entries[0]) is dict and
             entries[0].get("id")==expected_channel_id and
             not response.get("nextPageToken"),
             "OAuth channel is not exactly the intended owner channel")
    page=response.get("pageInfo")
    if page is not None:
        _require(type(page) is dict and
                 type(page.get("totalResults")) is int and
                 page["totalResults"]==1,
                 "Ambiguous authenticated channel result count")
    return {
        "status":"B4F2_EXACT_OWNER_OAUTH_CHANNEL_READBACK_ONLY",
        "authenticated_channel_id":expected_channel_id,
        "read_only_query_count":1,
        "videos_insert_executed_by_this_function":False,
        "independent_video_rights_or_facts_approved":False,
        "youtube_release_authorized_by_this_function":False,
    }


def verify_processed_private_schedule_and_caption(
    youtube: object, *,
    video_id: str, expected_channel_id: str, expected_publish_at: str,
    expected_title: str, expected_description: str,
    expected_language: str, expected_caption_id: str,
    expected_synthetic_disclosure: bool, expected_made_for_kids: bool,
) -> dict:
    """Verify specific uploaded caption ID and processed private YouTube video.

    Video+caption metadata is NOT independent proof of original MP4/SRT bytes,
    or factual accuracy, media rights, actual owner human watch or publication.
    """
    _require(type(video_id) is str and VIDEO_ID.fullmatch(video_id) is not None,
             "Invalid reported remote video ID")
    _require(type(expected_channel_id) is str and
             CHANNEL_ID.fullmatch(expected_channel_id) is not None,
             "Invalid intended channel ID")
    _require(type(expected_caption_id) is str and
             1 <= len(expected_caption_id) <= 128 and
             re.fullmatch(r"[A-Za-z0-9_.-]+",expected_caption_id) is not None,
             "Missing uploaded caption-track identity")
    _require(expected_language in ("en","hi") and
             type(expected_synthetic_disclosure) is bool and
             type(expected_made_for_kids) is bool,
             "Explicit locale and AI/audience declarations mandatory")
    _require(type(expected_title) is str and expected_title.strip() != "" and
             type(expected_description) is str and
             expected_description.strip() != "" and
             type(expected_publish_at) is str and
             re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ",
                          expected_publish_at) is not None,
             "Expected metadata must be locked")
    try:
        video_response=youtube.videos().list(
            part="snippet,status,processingDetails,contentDetails",id=video_id
        ).execute()
        cap_response=youtube.captions().list(
            part="snippet",videoId=video_id
        ).execute()
    except Exception:
        raise OwnerYouTubeReadbackRefused(
            "Owner media readback failed; keep pending receipt and do not reinsert"
        ) from None
    _require(type(video_response) is dict and
             type(video_response.get("items")) is list and
             len(video_response["items"])==1 and
             type(video_response["items"][0]) is dict,
             "Expected exactly one private owner video response")
    video=video_response["items"][0]
    snippet, status, processing, content=(
        video.get("snippet"),video.get("status"),
        video.get("processingDetails"),video.get("contentDetails")
    )
    _require(all(type(x) is dict for x in (
        snippet,status,processing,content)),
        "Video status/processing/thumbnail metadata incomplete")
    _require(
        video.get("id")==video_id and
        snippet.get("channelId")==expected_channel_id and
        snippet.get("title")==expected_title and
        snippet.get("description")==expected_description and
        status.get("privacyStatus")=="private" and
        _same_utc_instant(status.get("publishAt"),expected_publish_at) and
        status.get("uploadStatus")=="processed" and
        processing.get("processingStatus")=="succeeded" and
        content.get("hasCustomThumbnail") is True and
        status.get("selfDeclaredMadeForKids") is expected_made_for_kids and
        status.get("containsSyntheticMedia") is expected_synthetic_disclosure,
        "Owner remote video not processed, exact private, scheduled or complete"
    )
    _require(type(cap_response) is dict and
             type(cap_response.get("items")) is list,
             "No authenticated caption tracks")
    caps=[cap for cap in cap_response["items"]
          if type(cap) is dict and cap.get("id")==expected_caption_id]
    _require(len(caps)==1 and type(caps[0].get("snippet")) is dict,
             "Uploaded caption ID not found exactly once")
    c=caps[0]["snippet"]
    _require(c.get("videoId")==video_id and
             c.get("language")==expected_language and
             c.get("status")=="serving" and
             c.get("isDraft") is False,
             "Requested caption track is not the serving uploaded version")
    return {
        "status":"B4F2_EXACT_PRIVATE_PROCESSED_REMOTE_MEDIA_AND_CAPTION_READBACK",
        "video_id":video_id,
        "channel_id":expected_channel_id,
        "scheduled_publish_at_utc":expected_publish_at,
        "caption_track_id":expected_caption_id,
        "authenticated_video_and_caption_api_readback":True,
        "actual_caption_text_independently_downloaded":False,
        "actual_video_mp4_sha256_independently_read_from_youtube":False,
        "independent_facts_rights_and_human_watch_verified":False,
        "actually_publicly_published":False,
        "youtube_release_authorized_by_this_function":False,
    }
