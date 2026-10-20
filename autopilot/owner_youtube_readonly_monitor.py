"""Read-only, owner-authorized three-slot YouTube release verification.

No upload, scheduling mutation, OAuth refresh, token persistence, or secret logging.
A verified account/channel and one video snapshot per lane are prerequisites.
Never interpret repository plans or self-declared receipts as live YouTube proof.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
import argparse
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener
from zoneinfo import ZoneInfo

CHANNEL = "UCCcL9Q_jqVq6LJmnYUSAFZA"
API = "https://www.googleapis.com/youtube/v3"
SLOTS = {"short_morning": (11, 0), "long": (16, 0), "short_evening": (20, 30)}
VIDEO_RE = re.compile(r"[A-Za-z0-9_-]{11}\Z")
UTC = timezone.utc


class ReleaseAuditError(ValueError):
    """Safe, non-secret rejection of unverifiable scheduling evidence."""


def _expected(day: str, slot: str) -> str:
    try:
        parsed = date.fromisoformat(day)
    except (TypeError, ValueError) as exc:
        raise ReleaseAuditError("INVALID_RELEASE_DAY") from exc
    if parsed.isoformat() != day or slot not in SLOTS:
        raise ReleaseAuditError("INVALID_DAY_OR_SLOT")
    local = datetime.combine(parsed, time(*SLOTS[slot]), tzinfo=ZoneInfo("Asia/Kolkata"))
    return local.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _utc_instant(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if result.tzinfo is None or result.utcoffset() != timedelta(0):
        return None
    return result


def _entry_format(entry: Any) -> bool:
    if not isinstance(entry, dict) or set(entry) != {"video_id", "title"}:
        return False
    vid, title = entry["video_id"], entry["title"]
    return (vid is None or (isinstance(vid, str) and bool(VIDEO_RE.fullmatch(vid)))) and (
        isinstance(title, str) and 1 <= len(title.strip()) <= 100
    )


class OwnerYouTubeReader:
    """Use a short-lived access token passed at runtime by an approved secret store."""

    def __init__(self, access_token: str) -> None:
        if not isinstance(access_token, str) or not 16 <= len(access_token) <= 8192:
            raise ReleaseAuditError("OWNER_OAUTH_ACCESS_NOT_AVAILABLE")
        if any(ch.isspace() for ch in access_token):
            raise ReleaseAuditError("INVALID_OAUTH_ACCESS_TOKEN")
        self.__token = access_token

    def _get(self, path: str, params: Mapping[str, str]) -> dict:
        if path not in ("channels", "videos"):
            raise ReleaseAuditError("ENDPOINT_NOT_ALLOWED")
        url = API + "/" + path + "?" + urlencode(params)
        request = Request(url, headers={
            "Authorization": "Bearer " + self.__token,
            "Accept": "application/json",
            "User-Agent": "FlowMinuteOwnerReadOnly/1",
        })

        class RefuseRedirect(HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                raise ReleaseAuditError("REDIRECT_REFUSED")

        try:
            with build_opener(RefuseRedirect()).open(request, timeout=12) as response:
                if response.geturl() != url:
                    raise ReleaseAuditError("RESPONSE_URL_MISMATCH")
                raw = response.read(1024 * 1024 + 1)
            if len(raw) > 1024 * 1024:
                raise ReleaseAuditError("API_RESPONSE_TOO_LARGE")
            payload = json.loads(raw)
        except Exception:
            # Never forward API response, requested headers, or token in exceptions.
            raise ReleaseAuditError("OWNER_YOUTUBE_READ_FAILED") from None
        if not isinstance(payload, dict):
            raise ReleaseAuditError("MALFORMED_API_JSON")
        return payload

    def verify_channel(self) -> bool:
        response = self._get("channels", {"part": "id", "mine": "true", "maxResults": "50"})
        items = response.get("items")
        if not isinstance(items, list) or len(items) == 0 or any(not isinstance(x, dict) for x in items):
            return False
        # Only the specific Brand channel is an acceptable owner identity.
        return CHANNEL in {x.get("id") for x in items}

    def video(self, video_id: str) -> dict:
        if not isinstance(video_id, str) or not VIDEO_RE.fullmatch(video_id):
            raise ReleaseAuditError("INVALID_VIDEO_ID")
        data = self._get("videos", {"part": "snippet,status,processingDetails", "id": video_id})
        items = data.get("items")
        if not isinstance(items, list) or len(items) != 1 or not isinstance(items[0], dict):
            raise ReleaseAuditError("VIDEO_NOT_RETURNED")
        item = items[0]
        if item.get("id") != video_id:
            raise ReleaseAuditError("REMOTE_VIDEO_ID_MISMATCH")
        return item


def audit_day(*, day: str, planned: Mapping[str, Any], reader: OwnerYouTubeReader,
              now: datetime | None = None) -> dict:
    """Return evidence-labelled status; no automatic follow-up actions.

    All three slots are required in the input, but video_id=None represents an
    unproduced/not-uploaded lane. Such lanes do not trigger a YouTube call.
    """
    if not isinstance(planned, Mapping) or set(planned) != set(SLOTS):
        raise ReleaseAuditError("REQUIRE_EXACT_THREE_RELEASE_SLOTS")
    expected = {slot: _expected(day, slot) for slot in SLOTS}
    for slot in SLOTS:
        if not _entry_format(planned[slot]):
            raise ReleaseAuditError("MALFORMED_SLOT_INPUT")
    ids = [planned[slot]["video_id"] for slot in SLOTS if planned[slot]["video_id"]]
    if len(ids) != len(set(ids)):
        raise ReleaseAuditError("DUPLICATE_REMOTE_VIDEO_ID")
    if not isinstance(reader, OwnerYouTubeReader):
        raise ReleaseAuditError("AUTHORIZED_READER_REQUIRED")
    instant = now if now is not None else datetime.now(UTC)
    if not isinstance(instant, datetime) or instant.tzinfo is None or instant.utcoffset() is None:
        raise ReleaseAuditError("AWARE_CLOCK_REQUIRED")
    instant = instant.astimezone(UTC)

    try:
        owner_verified = reader.verify_channel() is True
    except Exception:
        owner_verified = False
    statuses = []
    for slot in SLOTS:
        entry = planned[slot]
        video_id = entry["video_id"]
        at = expected[slot]
        result = {"slot": slot, "publish_at_utc": at, "video_id": video_id,
                  "status": "HOLD_UNVERIFIED", "reason": "OWNER_ACCOUNT_NOT_VERIFIED"}
        if not owner_verified:
            pass
        elif video_id is None:
            result.update(status="MISSING_VIDEO", reason="NO_REMOTE_VIDEO_ID")
        else:
            try:
                remote = reader.video(video_id)
                snippet = remote.get("snippet")
                state = remote.get("status")
                processing = remote.get("processingDetails")
                if not isinstance(snippet, dict) or not isinstance(state, dict) or not isinstance(processing, dict):
                    raise ReleaseAuditError("REMOTE_SHAPE_INVALID")
                if snippet.get("channelId") != CHANNEL or snippet.get("title") != entry["title"]:
                    raise ReleaseAuditError("CHANNEL_OR_TITLE_MISMATCH")
                if state.get("uploadStatus") != "processed" or processing.get("processingStatus") != "succeeded":
                    raise ReleaseAuditError("REMOTE_PROCESSING_INCOMPLETE")
                scheduled = _utc_instant(state.get("publishAt"))
                due = _utc_instant(at)
                if (state.get("privacyStatus") == "private" and scheduled == due and instant < due):
                    result.update(status="SCHEDULED_VERIFIED", reason="OWNER_API_EXACT_SCHEDULE")
                elif state.get("privacyStatus") == "public" and instant >= due:
                    result.update(status="PUBLIC_STATUS_ONLY", reason="ANONYMOUS_PLAYABILITY_NOT_VERIFIED")
                else:
                    result.update(status="HOLD_UNVERIFIED", reason="REMOTE_STATUS_OR_TIME_MISMATCH")
            except Exception:
                # Never include dynamic exceptions; they can embed OAuth headers.
                result.update(status="HOLD_UNVERIFIED", reason="REMOTE_STATUS_UNVERIFIED")
        statuses.append(result)
    scheduled_count = sum(x["status"] == "SCHEDULED_VERIFIED" for x in statuses)
    public_status_count = sum(x["status"] == "PUBLIC_STATUS_ONLY" for x in statuses)
    return {
        "date_local": day,
        "channel_id": CHANNEL,
        "account_verified": owner_verified,
        "source": "authenticated_youtube_owner_read_only" if owner_verified else "unverified",
        "verified_scheduled_count": scheduled_count,
        "verified_public_status_count": public_status_count,
        "verified_platform_state_count": scheduled_count + public_status_count,
        "slots_total": 3,
        "lanes": statuses,
        "publishing_authorized": False,
        "uploads_attempted": 0,
        "schedules_written": 0,
        "anonymous_playability_verified": False,
        "cloud_autopilot_ready": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only authorized FlowMinute YouTube release audit")
    parser.add_argument("--date", required=True)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        entries = json.loads(args.manifest.read_text(encoding="utf-8"))
        token = os.environ.get("FLOWMINUTE_YOUTUBE_ACCESS_TOKEN", "")
        report = audit_day(day=args.date, planned=entries, reader=OwnerYouTubeReader(token))
        print(json.dumps(report, indent=2))
        return 0 if report["verified_platform_state_count"] == 3 else 2
    except (ReleaseAuditError, ValueError, OSError, TypeError):
        print(json.dumps({"status": "HOLD_UNVERIFIED", "publishing_authorized": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
