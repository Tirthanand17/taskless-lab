"""B1q6: strict owner-OAuth, READ-ONLY YouTube Nov 05-11 schedule inventory.

This module takes an injected YouTube API client, never credentials. It only
invokes channels.list, playlistItems.list and videos.list. All output is
REDACTED (no private titles, YouTube IDs, OAuth, descriptions or video links).
A historical GitHub receipt is not a current API confirmation. No upload,
edit, deletion, replacement or owner editorial approval is implemented.

CI fake clients are NOT real YouTube authentication evidence. The protected
runtime must connect the actual owner's OAuth independently.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import re

from autopilot.branch1_nov_repair_inventory import (
    CHANNEL, START, END, IST, SLOTS, build_nov_repair_inventory,
)

VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
PLAYLIST_ID = re.compile(r"^[A-Za-z0-9_-]{16,80}$")
RELEASE_STATUS = "OWNER_READONLY_NOV05_11_COMPLETE_SCAN_NO_YOUTUBE_MUTATION"
MAX_PAGES = 30
BATCH = 50


class ReadonlyScheduleRejected(ValueError):
    """Remote state is indeterminate: don't schedule anything."""


def _external(fn, label: str) -> dict:
    # Do not chain exceptions: HTTP/OAuth messages sometimes contain tokens.
    try:
        response = fn()
    except Exception:
        raise ReadonlyScheduleRejected(label) from None
    if type(response) is not dict:
        raise ReadonlyScheduleRejected("YouTube returned invalid read-only data")
    return response


def _instant(value: str) -> datetime:
    if type(value) is not str or len(value) > 70:
        raise ReadonlyScheduleRejected("Malformed private publishAt")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ReadonlyScheduleRejected("Malformed private publishAt") from None
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ReadonlyScheduleRejected("Private publishAt must be timezone-aware")
    return dt.astimezone(timezone.utc)


def _verified_upload_ids(youtube, uploads_id: str) -> set[str]:
    ids: set[str] = set()
    seen_tokens: set[str] = set()
    next_page = ""
    for _ in range(MAX_PAGES):
        kwargs = {"part": "contentDetails", "playlistId": uploads_id,
                  "maxResults": BATCH}
        if next_page:
            kwargs["pageToken"] = next_page
        response = _external(lambda: youtube.playlistItems().list(
            **kwargs).execute(), "YouTube uploads playlist read unavailable")
        items = response.get("items")
        if type(items) is not list or len(items) > BATCH:
            raise ReadonlyScheduleRejected("Uploads list incomplete or malformed")
        for item in items:
            if type(item) is not dict or type(item.get("contentDetails")) is not dict:
                raise ReadonlyScheduleRejected("Malformed owner uploaded video")
            video_id = item["contentDetails"].get("videoId")
            if type(video_id) is not str or not VIDEO_ID.fullmatch(video_id):
                raise ReadonlyScheduleRejected("Invalid owner uploaded video ID")
            if video_id in ids:
                raise ReadonlyScheduleRejected("Repeated owner uploads video ID")
            ids.add(video_id)
        token = response.get("nextPageToken")
        if token in (None, ""):
            return ids
        if type(token) is not str or len(token) > 400 or token in seen_tokens:
            raise ReadonlyScheduleRejected("Repeated/untrusted uploads page token")
        seen_tokens.add(token)
        next_page = token
    raise ReadonlyScheduleRejected("Owner uploads pagination not exhausted; no coverage claim")


def _video_states(youtube, ids: set[str], *, uploads: set[str]) -> dict:
    states = {}
    ordered = sorted(ids)
    for first in range(0, len(ordered), BATCH):
        subset = ordered[first:first+BATCH]
        response = _external(lambda: youtube.videos().list(
            part="id,snippet,status", id=",".join(subset)
            ).execute(), "Owner videos.list status read unavailable")
        items = response.get("items")
        if type(items) is not list or len(items) > BATCH:
            raise ReadonlyScheduleRejected("Owner video statuses malformed or incomplete")
        for item in items:
            if type(item) is not dict:
                raise ReadonlyScheduleRejected("Malformed owner video response")
            video_id, status, snippet = (item.get("id"), item.get("status"),
                                         item.get("snippet"))
            if (type(video_id) is not str or video_id not in subset
                or video_id in states or type(status) is not dict
                or type(snippet) is not dict
                or snippet.get("channelId") != CHANNEL):
                raise ReadonlyScheduleRejected("Channel mismatch or repeated remote video")
            privacy = status.get("privacyStatus")
            if privacy not in ("private", "public", "unlisted"):
                raise ReadonlyScheduleRejected("Unrecognized current video privacy")
            publish_at = status.get("publishAt")
            if publish_at is not None and type(publish_at) is not str:
                raise ReadonlyScheduleRejected("Invalid remote publishAt type")
            # Do not trust publishAt on public or unlisted videos as a
            # currently pending schedule. Keep it only when still private.
            states[video_id] = {
                "privacy": privacy,
                "publish_at": (_instant(publish_at) if publish_at else None),
            }
    if not uploads.issubset(states):
        raise ReadonlyScheduleRejected("Owner uploads scan includes unresolved video IDs")
    return states


def read_owner_nov_schedule(youtube, *, root, checked_at_utc: datetime) -> dict:
    """Return sanitized slot occupancy only, never release instructions.

    The caller must inject an owner-authorized YouTube Data API client. The
    report should be stored in a protected runner, not an open PR artifact.
    """
    if (not isinstance(checked_at_utc, datetime)
        or checked_at_utc.tzinfo is None
        or checked_at_utc.utcoffset() is None):
        raise ReadonlyScheduleRejected("Authenticated readback requires a real UTC clock")
    checked_at = checked_at_utc.astimezone(timezone.utc)
    inventory = build_nov_repair_inventory(root)
    source_slots = inventory["slots"]
    if len(source_slots) != 21 or inventory["historical_repo_receipt_count"] != 4:
        raise ReadonlyScheduleRejected("GitHub historical schedule has changed; manual re-audit")
    response = _external(lambda: youtube.channels().list(
        part="id,contentDetails", mine=True, maxResults=50).execute(),
        "Owner channels.list OAuth read unavailable")
    channels = response.get("items")
    if type(channels) is not list or len(channels) != 1:
        raise ReadonlyScheduleRejected("Owner authenticated channel is ambiguous")
    channel = channels[0]
    if (type(channel) is not dict or channel.get("id") != CHANNEL
        or type(channel.get("contentDetails")) is not dict
        or type(channel["contentDetails"].get("relatedPlaylists")) is not dict):
        raise ReadonlyScheduleRejected("Authenticated owner channel is not FlowMinute Lab")
    uploads_id = channel["contentDetails"]["relatedPlaylists"].get("uploads")
    if type(uploads_id) is not str or not PLAYLIST_ID.fullmatch(uploads_id):
        raise ReadonlyScheduleRejected("Owned channel uploads playlist missing")

    uploads = _verified_upload_ids(youtube, uploads_id)
    prior_by_slot = {}
    for entry in source_slots:
        historical = entry.get("historical")
        if historical is not None:
            video_id = historical.get("original_youtube_video_id")
            if type(video_id) is not str or not VIDEO_ID.fullmatch(video_id):
                raise ReadonlyScheduleRejected("Invalid GitHub original video ID")
            prior_by_slot[(entry["date_ist"],entry["local_clock_ist"])] = video_id
    states = _video_states(youtube, uploads | set(prior_by_slot.values()), uploads=uploads)

    occupied: dict[tuple[str,str], list[str]] = {}
    offslot = 0
    for video_id in uploads | set(prior_by_slot.values()):
        info = states.get(video_id)
        if not info or info["privacy"] != "private" or not info["publish_at"]:
            continue
        local = info["publish_at"].astimezone(IST)
        if not START <= local.date() <= END:
            continue
        date_key, clock = local.date().isoformat(), local.strftime("%H:%M")
        if clock not in {slot[2] for slot in SLOTS}:
            offslot += 1
            continue
        occupied.setdefault((date_key,clock),[]).append(video_id)

    rows=[]
    conflicts=0
    scheduled=0
    historical_confirmed=0
    for slot in source_slots:
        key=(slot["date_ist"],slot["local_clock_ist"])
        ids=occupied.get(key,[])
        previous_id=prior_by_slot.get(key)
        old=states.get(previous_id) if previous_id else None
        if len(ids)>1:
            conflicts+=1
            slot_state="MULTIPLE_PRIVATE_VIDEOS_AT_ONE_SLOT_STOP"
        elif len(ids)==1:
            scheduled+=1
            slot_state="ONE_PRIVATE_SCHEDULE_IN_OWNER_UPLOADS"
        else:
            slot_state="NO_MATCH_IN_COMPLETE_OWNER_UPLOADS_SCAN"
        matches=bool(previous_id and previous_id in ids)
        historical_confirmed+=int(matches)
        historical_state=(
            "NO_HISTORICAL_RECEIPT" if not previous_id else
            "HISTORICAL_ID_NOT_RETURNED_BY_OWNER" if not old else
            "HISTORICAL_ID_STILL_SCHEDULED_SAME_SLOT" if matches else
            "HISTORICAL_ID_NOW_PUBLIC" if old["privacy"]=="public" else
            "HISTORICAL_ID_NOW_UNLISTED" if old["privacy"]=="unlisted" else
            "HISTORICAL_ID_PRIVATE_DIFFERENT_OR_NO_SCHEDULE"
        )
        due=_instant(slot["utc_publish_at"])
        rows.append({
            "date_ist":slot["date_ist"],
            "slot":slot["slot"],
            "kind":slot["kind"],
            "time_ist":slot["local_clock_ist"],
            "slot_time_already_passed":due <= checked_at,
            "owner_private_scheduled_count":len(ids),
            "slot_status":slot_state,
            "historical_status":historical_state,
            "replacement_eligible_without_human_release_approval":False,
            "existing_remote_media_changed":False,
        })

    return {
        "status":RELEASE_STATUS,
        "channel_owned_by_authenticated_oauth":True,
        "owner_uploads_pagination_exhausted":True,
        "checked_at_utc":checked_at.isoformat(timespec="seconds").replace("+00:00","Z"),
        "original_git_receipts_count":len(prior_by_slot),
        "slots_checked":len(rows),
        "private_scheduled_slots_found":scheduled,
        "historical_ids_same_private_schedule_count":historical_confirmed,
        "slot_conflicts":conflicts,
        "private_schedule_outside_standard_time_count":offslot,
        "current_youtube_uploads_scanned":len(uploads),
        "owner_approval_for_exact_new_video":False,
        "video_uploaded_or_edited_or_deleted":False,
        "safe_to_change_any_scheduled_video":False,
        "only_readonly_channels_playlistitems_videos_list_called":True,
        "slots":rows,
    }
