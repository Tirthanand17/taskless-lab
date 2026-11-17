"""Fail-closed fence against re-uploading videos already seen in owner Studio.

Runs BEFORE OAuth and before downloading render artifacts in the manual
publisher workflow. A local ledger is NOT an OAuth token or evidence of
audience growth. This prevents accidentally re-sending the same video when
the historical release JSON still says youtube_uploaded=false.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

CHANNEL = "UCCcL9Q_jqVq6LJmnYUSAFZA"
REGISTRY = Path("state/known_youtube_uploads.json")
SCHEMA = "FLOWMINUTE_OWNER_STUDIO_KNOWN_UPLOADS_V1"
KNOWN_EPISODE = "fm_real_python_csv_three_bugs_long_en"
KNOWN_SHA = "1a20dedf886f3228445ed718e1f2e93a7e38cd74abf8aeb211540e32b6683f42"
KNOWN_VIDEO_ID = "ZanfCnmTegA"
HEX = re.compile(r"[0-9a-f]{64}\Z")
EPISODE = re.compile(r"content/episodes/[A-Za-z0-9_-]{1,100}\.json\Z")
YT_ID = re.compile(r"[A-Za-z0-9_-]{11}\Z")
UTC = re.compile(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z")

class KnownUploadRejected(ValueError):
    """Do not proceed to another YouTube videos.insert."""

def need(condition: bool, reason: str) -> None:
    if not condition:
        raise KnownUploadRejected(reason)

def load_known_uploads(root: Path) -> list[dict]:
    file = root / REGISTRY
    need(file.is_file() and not file.is_symlink()
         and 0 < file.stat().st_size <= 100_000,
         "KNOWN_UPLOAD_LEDGER_MISSING_OR_UNSAFE")
    try:
        blob = json.loads(file.read_text(encoding="utf8"))
    except (OSError, UnicodeError, ValueError):
        raise KnownUploadRejected("KNOWN_UPLOAD_LEDGER_NOT_VALID_JSON") from None
    need(type(blob) is dict and blob.get("schema") == SCHEMA
         and blob.get("channel_id") == CHANNEL
         and type(blob.get("records")) is list and blob["records"]
         and len(blob["records"]) <= 500,
         "INVALID_OWNER_UPLOAD_LEDGER_SCHEMA")
    records = blob["records"]
    ids, episodes, digests = set(), set(), set()
    for record in records:
        need(type(record) is dict and set(record) == {
            "episode_id", "episode_path", "video_sha256",
            "youtube_video_id", "scheduled_publish_at_utc",
            "status_at_verification", "verified_source", "verified_date",
        }, "INVALID_KNOWN_UPLOADED_ITEM")
        episode, ep_path = record["episode_id"], record["episode_path"]
        digest, video_id = record["video_sha256"], record["youtube_video_id"]
        need(type(episode) is str and type(ep_path) is str
             and EPISODE.fullmatch(ep_path) is not None
             and episode == Path(ep_path).stem
             and type(digest) is str and HEX.fullmatch(digest) is not None
             and type(video_id) is str and YT_ID.fullmatch(video_id) is not None
             and type(record["scheduled_publish_at_utc"]) is str
             and UTC.fullmatch(record["scheduled_publish_at_utc"]) is not None
             and record["status_at_verification"] in ("scheduled", "public")
             and record["verified_source"] ==
                 "owner_youtube_studio_confirmation_and_independent_content_readback"
             and type(record["verified_date"]) is str
             and re.fullmatch(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}",
                              record["verified_date"]) is not None,
             "UNVERIFIED_KNOWN_UPLOAD_RECORD")
        need(episode not in episodes and digest not in digests and video_id not in ids,
             "DUPLICATE_KNOWN_UPLOAD_RECORD")
        episodes.add(episode); digests.add(digest); ids.add(video_id)
    # No future editable ledger may omit or silently alter the one video that
    # was observed in actual Studio after a live upload.
    need(any(r["episode_id"] == KNOWN_EPISODE
             and r["video_sha256"] == KNOWN_SHA
             and r["youtube_video_id"] == KNOWN_VIDEO_ID for r in records),
         "MISSING_INDEPENDENTLY_VERIFIED_NOV19_VIDEO")
    return records

def refuse_if_already_uploaded(*, root: Path, episode_path: str,
                               mp4_sha256: str | None,
                               channel_id: str | None = None) -> dict:
    # Check before access tokens, artifact copies, signatures, or any write.
    need(type(episode_path) is str and EPISODE.fullmatch(episode_path) is not None,
         "INVALID_EPISODE_FOR_DUPLICATE_CHECK")
    need(type(mp4_sha256) is str and HEX.fullmatch(mp4_sha256) is not None,
         "EXACT_MEDIA_SHA_REQUIRED_FOR_DUPLICATE_CHECK")
    need(channel_id == CHANNEL, "WRONG_CHANNEL_FOR_DUPLICATE_CHECK")
    records = load_known_uploads(root)
    for record in records:
        if (record["episode_path"] == episode_path
                or record["video_sha256"] == mp4_sha256):
            raise KnownUploadRejected(
                "ALREADY_UPLOADED_IN_OWNER_YOUTUBE_STUDIO_STOP_NO_RETRY"
            )
    return {"status": "NOT_IN_KNOWN_OWNER_STUDIO_UPLOAD_LEDGER",
            "owner_rights_or_cryptographic_release_approved": False,
            "live_youtube_duplicate_scan_completed": False,
            "youtube_uploads": 0, "youtube_schedules": 0}

def main() -> None:
    ap = argparse.ArgumentParser(description="Fail closed on known YouTube uploads; never upload.")
    ap.add_argument("--episode", required=True)
    ap.add_argument("--sha256", required=True)
    ap.add_argument("--channel-id", required=True)
    args = ap.parse_args()
    try:
        result = refuse_if_already_uploaded(
            root=Path(__file__).resolve().parents[1],
            episode_path=args.episode,
            mp4_sha256=args.sha256,
            channel_id=args.channel_id,
        )
    except (KnownUploadRejected, OSError, ValueError):
        raise SystemExit("Known owner-Studio upload or invalid ledger: refuse upload") from None
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
