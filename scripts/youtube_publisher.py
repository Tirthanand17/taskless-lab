#!/usr/bin/env python3
"""FlowMinute YouTube publisher. Safe by default; no writes without explicit CLI consent.

Google API imports are intentionally lazy so offline validation/tests need no Google account.
This is not a web scraper and never operates on the browser's Studio session.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any

UTC = dt.timezone.utc
READ_SCOPE = "https://www.googleapis.com/auth/youtube.readonly"
WRITE_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
CHANNEL_ID = re.compile(r"^UC[A-Za-z0-9_-]{22}$")
SAFE_EPISODE = re.compile(r"^[a-z][a-z0-9_-]{2,79}$")
DEFAULT_LEDGER = Path.home() / ".flowminute-private" / "youtube-ledger.json"


class PublisherError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PublisherError(message)


def resolve_existing(path: str, *, suffixes: tuple[str, ...] = ()) -> Path:
    p = Path(path).expanduser().resolve()
    require(p.is_file(), f"Required file not found: {p}")
    if suffixes:
        require(p.suffix.lower() in suffixes, f"Unexpected file extension: {p.name}")
    return p


def parse_utc(value: str) -> dt.datetime:
    require(isinstance(value, str), "publish_at must be a string")
    require(bool(re.search(r"(Z|[+-]\d\d:\d\d)$", value)), "publish_at requires explicit timezone offset")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PublisherError(f"Invalid publish_at: {value}") from exc
    require(parsed.tzinfo is not None, "publish_at cannot be naive")
    return parsed.astimezone(UTC)


def as_rfc3339(value: dt.datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PublisherError(f"Invalid or inaccessible JSON: {path}") from exc
    require(isinstance(data, dict), "Expected JSON object")
    return data


def validate_srt_file(path: Path) -> int:
    """Validate timed, nonoverlapping SRT cues; this does not replace an audio review."""
    import re
    content = path.read_text(encoding="utf-8-sig").strip()
    require(bool(content), "Caption SRT cannot be empty")
    cues = re.split(r"\n\s*\n", content.replace("\r\n", "\n"))
    timestamp = re.compile(r"^(\d\d):(\d\d):(\d\d),(\d{3})$")
    previous_end = 0

    def milliseconds(value: str) -> int:
        match = timestamp.fullmatch(value)
        require(match is not None, "SRT requires HH:MM:SS,mmm time codes")
        h, m, sec, ms = map(int, match.groups())
        require(m < 60 and sec < 60, "Invalid SRT minutes or seconds")
        return ((h * 60 + m) * 60 + sec) * 1000 + ms

    for index, block in enumerate(cues, start=1):
        lines = block.split("\n")
        require(len(lines) >= 3, "SRT cue requires index, timeline and subtitle text")
        require(lines[0].strip() == str(index), "SRT cue numbering must start at one and be sequential")
        times = lines[1].strip().split(" --> ")
        require(len(times) == 2, "Invalid SRT cue timestamp separator")
        start, end = milliseconds(times[0]), milliseconds(times[1])
        require(start >= previous_end and end > start, "SRT cues overlap or have invalid durations")
        require(any(t.strip() for t in lines[2:]), "SRT cue cannot have empty text")
        previous_end = end
    return len(cues)


def validate_manifest(path: Path, *, now: dt.datetime | None = None) -> dict[str, Any]:
    doc = read_json(path)
    base = path.parent
    episode_id = doc.get("episode_id")
    require(isinstance(episode_id, str) and SAFE_EPISODE.fullmatch(episode_id) is not None,
            "Invalid episode_id: use lowercase letters, numbers, '_' or '-'")
    expected_channel = doc.get("expected_channel_id")
    require(isinstance(expected_channel, str) and CHANNEL_ID.fullmatch(expected_channel) is not None,
            "expected_channel_id must be a real-looking UC... channel ID")
    receipt = Path(__file__).resolve().parents[1] / "state" / "scheduled" / (episode_id + ".json")
    require(not receipt.exists(),
            f"Episode already scheduled in the channel release receipts: {receipt}. Do NOT duplicate-upload.")
    require(doc.get("qa_approved") is True, "qa_approved must be explicitly true")
    require(doc.get("made_for_kids") is False or doc.get("made_for_kids") is True,
            "made_for_kids must be explicitly true/false, not omitted")
    require(doc.get("synthetic_media") is False or doc.get("synthetic_media") is True,
            "synthetic_media requires explicit true/false after editorial review")
    require(doc.get("captions_reviewed") in (True, False, None),
            "captions_reviewed must be Boolean")
    schedule = parse_utc(doc.get("publish_at"))
    clock = now or dt.datetime.now(UTC)
    require(clock.tzinfo is not None and schedule > clock.astimezone(UTC) + dt.timedelta(minutes=30),
            "publish_at must be over 30 minutes in the future; past dates can publish immediately")
    ep = resolve_existing(str(base / str(doc.get("episode_path", ""))), suffixes=(".json",))
    metadata = read_json(ep)
    require(metadata.get("id") == episode_id, "Episode metadata ID differs from release manifest")
    title, desc = metadata.get("title"), metadata.get("description")
    require(isinstance(title, str) and 1 <= len(title) <= 100, "Video title must be 1-100 characters")
    require(isinstance(desc, str) and len(desc.encode("utf-8")) <= 5000,
            "Description exceeds YouTube's 5,000-byte limit")
    require("<" not in title and ">" not in title and "<" not in desc and ">" not in desc,
            "Video title and description cannot contain angle brackets")
    require(metadata.get("type") in ("short", "long"), "Episode type must be short or long")
    video = resolve_existing(str(base / str(doc.get("video_path", ""))), suffixes=(".mp4",))
    require(video.stat().st_size > 0, "Empty video")
    approved_hash = doc.get("video_sha256")
    require(isinstance(approved_hash, str) and re.fullmatch(r"[a-f0-9]{64}", approved_hash),
            "video_sha256 approval hash is required")
    computed_hash = file_sha256(video)
    require(computed_hash == approved_hash, "Video file differs from QA-approved SHA-256")
    image = None
    if doc.get("thumbnail_path"):
        image = resolve_existing(str(base / doc["thumbnail_path"]), suffixes=(".jpg", ".jpeg", ".png"))
        require(image.stat().st_size <= 2 * 1024 * 1024, "Thumbnail must not exceed 2 MiB")
        require(doc.get("thumbnail_sha256") == file_sha256(image),
                "Thumbnail differs from QA-approved thumbnail_sha256")
    caption = None
    if doc.get("caption_path"):
        require(doc.get("captions_reviewed") is True,
                "Caption upload blocked until reviewed against exact narration")
        caption = resolve_existing(str(base / doc["caption_path"]), suffixes=(".srt",))
        require(doc.get("caption_sha256") == file_sha256(caption),
                "Caption file differs from approved caption_sha256")
        validate_srt_file(caption)
    return {
        "episode_id": episode_id, "expected_channel_id": expected_channel,
        "publish_at": as_rfc3339(schedule), "video_path": video, "video_sha256": computed_hash,
        "episode_path": ep, "title": title, "description": desc, "type": metadata["type"],
        "tags": list(metadata.get("tags", [])), "thumbnail_path": image, "caption_path": caption,
        "made_for_kids": doc["made_for_kids"], "synthetic_media": doc["synthetic_media"],
        "category_id": str(doc.get("category_id", "28")),
        "qa_approved": True,
    }


def printable_plan(plan: dict[str, Any]) -> dict[str, Any]:
    return {k: str(v) if isinstance(v, Path) else v for k, v in plan.items()}


def write_json_secure(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".pending-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(data, out, indent=2, sort_keys=True)
            out.write("\n")
            out.flush()
            os.fsync(out.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextlib.contextmanager
def exclusive_ledger(ledger_path: Path):
    """Lock is intentionally NOT automatically broken; operator handles stale locks."""
    lock_path = ledger_path.with_suffix(ledger_path.suffix + ".lock")
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise PublisherError(f"Publisher busy or previous run interrupted. Inspect lock manually: {lock_path}") from exc
    try:
        with os.fdopen(fd, "w") as out:
            out.write(f"pid={os.getpid()}\n")
        yield
    finally:
        lock_path.unlink(missing_ok=True)


def get_ledger(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": 1, "episodes": {}}
    data = read_json(path)
    require(data.get("schema_version") == 1 and isinstance(data.get("episodes"), dict),
            "Unrecognized ledger format")
    return data


def create_upload_reservation(ledger: dict[str, Any], plan: dict[str, Any]) -> None:
    episode_id = plan["episode_id"]
    require(episode_id not in ledger["episodes"],
            f"{episode_id} already has a reservation or receipt. Do not duplicate-upload; reconcile manually.")
    for other_id, existing in ledger["episodes"].items():
        require(existing.get("video_sha256") != plan["video_sha256"],
                f"Video content already attempted under {other_id}. Do not upload duplicate media.")
    ledger["episodes"][episode_id] = {
        "state": "uploading_unresolved", "video_id": None, "channel_id": plan["expected_channel_id"],
        "video_sha256": plan["video_sha256"], "publish_at": plan["publish_at"],
        "title": plan["title"], "note": "If upload times out, NEVER blindly retry; reconcile in Studio."
    }


def require_matching_record(ledger: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    record = ledger["episodes"].get(plan["episode_id"])
    require(isinstance(record, dict), "No ledger record. First upload privately or reconcile externally.")
    require(record.get("video_sha256") == plan["video_sha256"], "Media checksum changed")
    require(record.get("title") == plan["title"], "Episode title changed after the upload reservation")
    require(record.get("channel_id") == plan["expected_channel_id"], "Wrong channel")
    require(record.get("publish_at") == plan["publish_at"], "Schedule changed: manual review required")
    return record


def credentials(token_file: Path, *, required_scope: str):
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except ImportError as exc:
        raise PublisherError("Install dependencies: pip install -r scripts/youtube_api_requirements.txt") from exc
    resolve_existing(str(token_file))
    creds = Credentials.from_authorized_user_file(str(token_file))
    have = set(creds.scopes or [])
    require(required_scope in have or WRITE_SCOPE in have,
            "This OAuth credential lacks the required scope. Authorize using the correct --mode.")
    if not creds.valid:
        require(creds.refresh_token is not None, "No refresh token; re-authorize locally")
        creds.refresh(Request())
        write_json_secure(token_file, json.loads(creds.to_json()))
    return creds


def credential_health(token_file: Path, *, expected_scope: str) -> dict[str, Any]:
    """Inspect local OAuth metadata without printing or refreshing secret tokens."""
    data = read_json(resolve_existing(str(token_file)))
    scopes = set(data.get("scopes", []))
    require(expected_scope in scopes or (expected_scope == READ_SCOPE and WRITE_SCOPE in scopes),
            "OAuth token lacks required scope")
    expiry = data.get("expiry")
    exp = None
    if expiry:
        try:
            exp = parse_utc(expiry)
        except (ValueError, TypeError) as exc:
            raise PublisherError("Invalid local OAuth access-token expiry") from exc
    now = dt.datetime.now(UTC)
    return {
        "token_file_present": True,
        "read_scope": READ_SCOPE in scopes or WRITE_SCOPE in scopes,
        "publish_scope": WRITE_SCOPE in scopes,
        "refresh_token_present": bool(data.get("refresh_token")),
        "access_token_expired": (now >= exp) if exp is not None else None,
        "access_token_expiry_utc": as_rfc3339(exp) if exp is not None else None,
        "refresh_token_expiry_known": False,
        "note": "Access-token expiry does not establish refresh-token lifetime. Testing-mode "
                "OAuth can expire after approximately seven days; run a safe doctor check "
                "before each publishing session and stop on failure.",
    }


def youtube_client(token_file: Path, *, writable: bool):
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise PublisherError("Install dependencies: pip install -r scripts/youtube_api_requirements.txt") from exc
    return build("youtube", "v3",
                 credentials=credentials(token_file, required_scope=WRITE_SCOPE if writable else READ_SCOPE),
                 cache_discovery=False)


def authorize(secrets_file: Path, token_file: Path, mode: str) -> None:
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise PublisherError("Install dependencies: pip install -r scripts/youtube_api_requirements.txt") from exc
    require(not token_file.exists(), f"Token file exists: {token_file}. Back up and manually remove to reauthorize.")
    secrets = read_json(resolve_existing(str(secrets_file)))
    require("installed" in secrets, "Create a Google OAuth Desktop client, not a web or service account")
    scope = [READ_SCOPE if mode == "read" else WRITE_SCOPE]
    flow = InstalledAppFlow.from_client_secrets_file(str(secrets_file), scopes=scope)
    creds = flow.run_local_server(host="localhost", port=0, open_browser=True,
                                  access_type="offline", prompt="consent")
    require(creds.refresh_token is not None, "Offline refresh token not returned. Check OAuth configuration.")
    write_json_secure(token_file, json.loads(creds.to_json()))
    print("OAuth connected. Token stored locally and ignored by Git. Next: doctor.")


def owned_channel_id(api) -> str:
    response = api.channels().list(part="id,snippet", mine=True, maxResults=50).execute()
    ids = [x.get("id") for x in response.get("items", []) if x.get("id")]
    require(len(ids) == 1, f"Expected one authorized channel, got {len(ids)}. Switch account or specify a different OAuth identity.")
    return ids[0]


def guard_channel(api, expected: str) -> None:
    actual = owned_channel_id(api)
    require(actual == expected, f"Refusing operation on channel {actual}; expected {expected}")
    print(f"Authenticated channel verified: {actual}")


def video_info(api, video_id: str) -> dict[str, Any]:
    require(bool(VIDEO_ID.fullmatch(video_id)), "Invalid YouTube video ID")
    r = api.videos().list(part="status,snippet,processingDetails", id=video_id).execute()
    items = r.get("items", [])
    require(len(items) == 1, f"Video not found/accessible: {video_id}")
    return items[0]


def check_processing_succeeded(video: dict[str, Any]) -> None:
    """Require actual successful processing before an automatic schedule."""
    status = video.get("status", {})
    processing = video.get("processingDetails", {})
    require(status.get("uploadStatus") == "processed",
            "Video upload has not finished processing; leave private")
    require(processing.get("processingStatus") == "succeeded",
            "Video processing has not succeeded; leave private")


def ensure_future_schedule(publish_at: str, now: dt.datetime | None = None) -> None:
    target = parse_utc(publish_at)
    current = (now or dt.datetime.now(UTC)).astimezone(UTC)
    require(target > current + dt.timedelta(minutes=30),
            "Schedule must remain at least 30 minutes in the future")


def verify_private(video: dict[str, Any], expected_title: str) -> None:
    require(video.get("status", {}).get("privacyStatus") == "private",
            "Video is not private; refusing to schedule")
    require(video.get("snippet", {}).get("title") == expected_title,
            "Remote title does not match manifest; check identity")
    require(not video.get("status", {}).get("publishAt"), "Video already has a schedule")


def preserved_status(status: dict[str, Any], publish_at: str) -> dict[str, Any]:
    """Never replace status without preserving user-settable fields returned by videos.list."""
    allowed = ("embeddable", "license", "publicStatsViewable",
               "selfDeclaredMadeForKids", "containsSyntheticMedia")
    result = {k: status[k] for k in allowed if k in status}
    result.update({"privacyStatus": "private", "publishAt": publish_at})
    return result


def upload_private(api, plan: dict[str, Any], ledger_path: Path) -> None:
    try:
        from googleapiclient.http import MediaFileUpload
    except ImportError as exc:
        raise PublisherError("Install dependencies first") from exc
    with exclusive_ledger(ledger_path):
        ledger = get_ledger(ledger_path)
        create_upload_reservation(ledger, plan)
        write_json_secure(ledger_path, ledger)
    media = MediaFileUpload(str(plan["video_path"]), mimetype="video/mp4",
                            resumable=True, chunksize=8 * 1024 * 1024)
    body = {
        "snippet": {
            "title": plan["title"], "description": plan["description"],
            "categoryId": plan["category_id"], "tags": plan["tags"]
        },
        "status": {
            "privacyStatus": "private",
            "selfDeclaredMadeForKids": plan["made_for_kids"],
            "containsSyntheticMedia": plan["synthetic_media"],
        }
    }
    try:
        request = api.videos().insert(part="snippet,status", body=body, media_body=media)
        result = None
        while result is None:
            progress, result = request.next_chunk()
            if progress is not None:
                print(f"Resumable upload progress: {progress.progress() * 100:.1f}%")
        video_id = result.get("id")
        require(isinstance(video_id, str) and VIDEO_ID.fullmatch(video_id) is not None,
                "Upload response missing video ID. Reconcile manually.")
        remote = video_info(api, video_id)
        verify_private(remote, plan["title"])
    except Exception as exc:
        print("Upload may or may not have succeeded. Reservation retained; DO NOT RETRY automatically.",
              file=sys.stderr)
        raise PublisherError(f"Upload unresolved: {type(exc).__name__}: {exc}") from exc
    with exclusive_ledger(ledger_path):
        ledger = get_ledger(ledger_path)
        record = require_matching_record(ledger, plan)
        require(record["state"] == "uploading_unresolved", "Unexpected upload state")
        record.update({"state": "uploaded_private", "video_id": video_id})
        write_json_secure(ledger_path, ledger)
    print(f"Private upload VERIFIED: https://youtu.be/{video_id}")
    print("Schedule is NOT set. Separate confirm-schedule step required.")


def schedule_private(api, plan: dict[str, Any], ledger_path: Path) -> None:
    # A private connectivity test must NEVER turn into scheduled public content.
    require(not plan["episode_id"].startswith("api_private_test_"),
            "Private API pilot videos cannot be scheduled or published by this tool")
    ensure_future_schedule(plan["publish_at"])
    with exclusive_ledger(ledger_path):
        ledger = get_ledger(ledger_path)
        record = require_matching_record(ledger, plan)
        require(record["state"] == "uploaded_private",
                f"Cannot schedule from state {record['state']}; no retry after ambiguous outcome")
        video_id = record["video_id"]
        require(isinstance(video_id, str) and VIDEO_ID.fullmatch(video_id) is not None,
                "No valid video ID")
        remote = video_info(api, video_id)
        verify_private(remote, plan["title"])
        check_processing_succeeded(remote)
        require(remote.get("snippet", {}).get("channelId") == plan["expected_channel_id"],
                "Remote video belongs to a different channel")
        record["state"] = "scheduling_unresolved"
        write_json_secure(ledger_path, ledger)
    try:
        ensure_future_schedule(plan["publish_at"])
        new_status = preserved_status(remote.get("status", {}), plan["publish_at"])
        api.videos().update(part="status", body={"id": video_id, "status": new_status}).execute()
        checked = video_info(api, video_id)
        target = parse_utc(plan["publish_at"])
        actual = parse_utc(checked.get("status", {}).get("publishAt"))
        require(abs((target - actual).total_seconds()) <= 1,
                "YouTube did not confirm requested publishAt")
        require(checked.get("status", {}).get("privacyStatus") == "private",
                "YouTube did not confirm private-until-publication")
    except Exception as exc:
        raise PublisherError(f"Schedule unresolved; inspect Studio manually before retry: {exc}") from exc
    with exclusive_ledger(ledger_path):
        ledger = get_ledger(ledger_path)
        record = require_matching_record(ledger, plan)
        require(record["state"] == "scheduling_unresolved", "Unexpected schedule state")
        record.update({"state": "scheduled_verified", "confirmed_publish_at": as_rfc3339(actual)})
        write_json_secure(ledger_path, ledger)
    print(f"Schedule VERIFIED: {video_id} on {as_rfc3339(actual)} (UTC)")




def decorate_assets(api, plan: dict[str, Any], ledger_path: Path) -> None:
    """Explicit second stage for approved thumbnails and accurate, human-reviewed SRTs.

    Upload only for this publisher's ledger-owned videos. If an API call is
    ambiguous, leave its reservation unresolved; never retry automatically.
    """
    from googleapiclient.http import MediaFileUpload
    for kind, media_path in (("thumbnail", plan["thumbnail_path"]), ("caption", plan["caption_path"])):
        if not media_path:
            continue
        with exclusive_ledger(ledger_path):
            ledger = get_ledger(ledger_path)
            record = require_matching_record(ledger, plan)
            require(record["state"] in ("uploaded_private", "scheduled_verified"),
                    f"Unexpected episode state: {record['state']}")
            video_id = record["video_id"]
            require(bool(VIDEO_ID.fullmatch(video_id or "")), "Missing upload receipt")
            asset_states = record.setdefault("assets", {})
            require(kind not in asset_states,
                    f"{kind} was attempted before ({asset_states[kind]}). Reconcile manually; no blind retry.")
            remote = video_info(api, video_id)
            require(remote.get("snippet", {}).get("channelId") == plan["expected_channel_id"],
                    "Video channel changed")
            require(remote.get("snippet", {}).get("title") == plan["title"],
                    "Video title changed")
            require(remote.get("status", {}).get("privacyStatus") == "private",
                    "Video is not private; no automatic asset modification")
            asset_states[kind] = "unresolved"
            write_json_secure(ledger_path, ledger)
        try:
            if kind == "thumbnail":
                mime = "image/png" if media_path.suffix.lower() == ".png" else "image/jpeg"
                request = api.thumbnails().set(
                    videoId=video_id, media_body=MediaFileUpload(str(media_path), mimetype=mime))
            else:
                request = api.captions().insert(
                    part="snippet",
                    body={"snippet": {
                        "videoId": video_id, "language": "en", "name": "English — reviewed",
                        "isDraft": False,
                    }},
                    media_body=MediaFileUpload(str(media_path), mimetype="application/octet-stream"))
            response = request.execute()
            require(isinstance(response, dict), f"{kind} API did not return confirmation")
        except Exception as exc:
            raise PublisherError(
                f"{kind} operation uncertain. Review it in Studio before retry: {exc}") from exc
        with exclusive_ledger(ledger_path):
            ledger = get_ledger(ledger_path)
            record = require_matching_record(ledger, plan)
            require(record["assets"].get(kind) == "unresolved", "Unexpected asset state")
            record["assets"][kind] = "confirmed"
            write_json_secure(ledger_path, ledger)
        print(f"{kind} upload confirmed by API for {video_id}")


def inspect_release(api, plan: dict[str, Any], ledger_path: Path) -> dict[str, Any]:
    """Read-only comparison of local receipt against official remote video state."""
    guard_channel(api, plan["expected_channel_id"])
    ledger = get_ledger(ledger_path)
    record = require_matching_record(ledger, plan)
    vid = record.get("video_id")
    require(isinstance(vid, str) and VIDEO_ID.fullmatch(vid) is not None,
            "No verified video ID in ledger; manual reconciliation required")
    remote = video_info(api, vid)
    require(remote.get("snippet", {}).get("channelId") == plan["expected_channel_id"],
            "Remote video ownership differs from the manifest")
    require(remote.get("snippet", {}).get("title") == plan["title"],
            "Remote video title differs from QA-approved metadata")
    remote_privacy = remote.get("status", {}).get("privacyStatus")
    remote_schedule = remote.get("status", {}).get("publishAt")
    if record["state"] in ("uploaded_private", "uploading_unresolved"):
        require(remote_privacy == "private" and not remote_schedule,
                "A supposedly private unscheduled release is scheduled or not private")
    if record["state"] == "scheduled_verified":
        require(remote_privacy == "private", "Scheduled video is no longer private")
        require(remote_schedule and abs((parse_utc(remote_schedule) -
                                         parse_utc(record["publish_at"])).total_seconds()) <= 1,
                "Scheduled time does not match the approved release")
    return {
        "episode_id": plan["episode_id"], "video_id": vid,
        "ledger_state": record["state"], "remote_privacy": remote_privacy,
        "remote_publish_at": remote_schedule,
        "remote_upload_status": remote.get("status", {}).get("uploadStatus"),
        "remote_processing": remote.get("processingDetails", {}).get("processingStatus"),
        "recorded_assets": record.get("assets", {}),
        "safe_for_publication": record["state"] == "scheduled_verified" and
            remote_privacy == "private" and remote_schedule is not None,
    }


def verify_existing(api, video_id: str, expected_channel_id: str) -> None:
    guard_channel(api, expected_channel_id)
    video = video_info(api, video_id)
    require(video.get("snippet", {}).get("channelId") == expected_channel_id, "Video channel mismatch")
    print(json.dumps({
        "video_id": video_id, "title": video["snippet"].get("title"),
        "privacy": video.get("status", {}).get("privacyStatus"),
        "publish_at": video.get("status", {}).get("publishAt"),
        "channel_id": expected_channel_id
    }, indent=2))


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fail-closed YouTube publisher; prepare is offline.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    prep = sub.add_parser("prepare", help="Validate manifest/video against QA hash; NO API writes")
    prep.add_argument("manifest", type=Path)
    auth = sub.add_parser("authorize", help="One-time local browser OAuth: READ or PUBLISH")
    auth.add_argument("--client-secret", type=Path, required=True)
    auth.add_argument("--token-file", type=Path, required=True)
    auth.add_argument("--mode", choices=["read", "publish"], default="read")
    health = sub.add_parser("auth-health", help="Offline local OAuth metadata check (no secrets or network)")
    health.add_argument("--token-file", type=Path, required=True)
    health.add_argument("--mode", choices=["read", "publish"], default="publish")
    doctor = sub.add_parser("doctor", help="Read-only confirmation of OAuth channel")
    doctor.add_argument("--token-file", type=Path, required=True)
    doctor.add_argument("--expected-channel-id", required=True)
    up = sub.add_parser("upload", help="Explicitly upload a reviewed video as PRIVATE only")
    up.add_argument("manifest", type=Path)
    up.add_argument("--token-file", type=Path, required=True)
    up.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    up.add_argument("--confirm-private-upload", action="store_true")
    sch = sub.add_parser("schedule", help="Explicitly schedule a verified PRIVATE upload")
    sch.add_argument("manifest", type=Path)
    sch.add_argument("--token-file", type=Path, required=True)
    sch.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    sch.add_argument("--confirm-schedule", action="store_true")
    dec = sub.add_parser("assets", help="Upload QA-approved thumbnail/reviewed captions for ledger-owned video")
    dec.add_argument("manifest", type=Path)
    dec.add_argument("--token-file", type=Path, required=True)
    dec.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    dec.add_argument("--confirm-assets", action="store_true")
    ins = sub.add_parser("inspect", help="Read-only crosscheck of local ledger and remote YouTube video")
    ins.add_argument("manifest", type=Path)
    ins.add_argument("--token-file", type=Path, required=True)
    ins.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    chk = sub.add_parser("verify", help="Read remote metadata with no writes")
    chk.add_argument("--token-file", type=Path, required=True)
    chk.add_argument("--expected-channel-id", required=True)
    chk.add_argument("--video-id", required=True)
    args = parser.parse_args(argv)
    try:
        if args.cmd == "authorize":
            authorize(args.client_secret, args.token_file, args.mode)
        elif args.cmd == "prepare":
            print(json.dumps(printable_plan(validate_manifest(args.manifest)), indent=2))
            print("SAFE DRY RUN: no API call; no upload; no schedule.")
        elif args.cmd == "auth-health":
            required = READ_SCOPE if args.mode == "read" else WRITE_SCOPE
            print(json.dumps(credential_health(args.token_file, expected_scope=required), indent=2))
        elif args.cmd == "doctor":
            guard_channel(youtube_client(args.token_file, writable=False), args.expected_channel_id)
        elif args.cmd == "inspect":
            plan = validate_manifest(args.manifest)
            api = youtube_client(args.token_file, writable=False)
            print(json.dumps(inspect_release(api, plan, args.ledger), indent=2))
        elif args.cmd == "verify":
            verify_existing(youtube_client(args.token_file, writable=False),
                            args.video_id, args.expected_channel_id)
        elif args.cmd in ("upload", "schedule", "assets"):
            confirmation = (args.confirm_private_upload if args.cmd == "upload"
                            else args.confirm_schedule if args.cmd == "schedule"
                            else args.confirm_assets)
            require(confirmation, "Write blocked: explicit --confirm-private-upload, --confirm-schedule or --confirm-assets required")
            plan = validate_manifest(args.manifest)
            api = youtube_client(args.token_file, writable=True)
            guard_channel(api, plan["expected_channel_id"])
            if args.cmd == "upload":
                upload_private(api, plan, args.ledger)
            else:
                if args.cmd == "schedule":
                    schedule_private(api, plan, args.ledger)
                else:
                    decorate_assets(api, plan, args.ledger)
    except PublisherError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
