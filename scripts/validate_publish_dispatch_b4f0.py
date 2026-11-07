"""B4f0: validate manual GitHub workflow_dispatch inputs without shell interpolation.

No network, account access, media or publisher behavior. This module is for
the pre-existing *manual* artifact publish workflow, which remains disabled
unless the owner enables the protected environment/release variables.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import re
import sys


class DispatchInputRejected(ValueError):
    """Fail closed before downloading any artifact or loading YouTube OAuth."""


ALLOWED_KEYS = (
    "FM_SOURCE_RUN_ID", "FM_ARTIFACT_NAME", "FM_VIDEO_FILE",
    "FM_CAPTIONS_FILE", "FM_THUMBNAIL_FILE", "FM_EPISODE",
    "FM_RECEIPT", "FM_PUBLISH_AT_UTC", "FM_VIDEO_SHA256",
    "FM_APPROVAL_MANIFEST", "FM_PRIVACY",
)
BASENAME = re.compile(r"[a-zA-Z0-9_-][a-zA-Z0-9._-]{0,119}\Z")
RUN_ID = re.compile(r"[1-9][0-9]{0,19}\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
Z_TIME = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\Z")
EPISODE = re.compile(r"content/episodes/[A-Za-z0-9_-]{1,100}\.json\Z")
APPROVAL = re.compile(r"state/approvals/[A-Za-z0-9_-]{1,100}\.json\Z")
RECEIPT = re.compile(r"state/published/[A-Za-z0-9_-]{1,100}\.json\Z")


def _need(predicate: bool, reason: str) -> None:
    if not predicate:
        raise DispatchInputRejected(reason)


def _filename(value: object, suffix: str) -> None:
    _need(type(value) is str and BASENAME.fullmatch(value) is not None
          and value.endswith(suffix) and ".." not in value
          and "/" not in value and "\\" not in value,
          "Unsafe artifact media filename")


def validate_dispatch(env: dict, *, now: datetime | None = None) -> dict:
    _need(type(env) is dict, "Missing dispatch environment")
    _need(all(type(env.get(key)) is str for key in ALLOWED_KEYS),
          "Missing required dispatch input")
    values = {k: env[k] for k in ALLOWED_KEYS}
    _need(RUN_ID.fullmatch(values["FM_SOURCE_RUN_ID"]) is not None,
          "Source workflow run ID must be numeric")
    _filename(values["FM_ARTIFACT_NAME"], "")
    _filename(values["FM_VIDEO_FILE"], ".mp4")
    _filename(values["FM_CAPTIONS_FILE"], ".srt")
    _need(any(values["FM_THUMBNAIL_FILE"].endswith(s)
              for s in (".png", ".jpg", ".jpeg")),
          "Thumbnail must be an image")
    _need(BASENAME.fullmatch(values["FM_THUMBNAIL_FILE"]) is not None
          and ".." not in values["FM_THUMBNAIL_FILE"],
          "Invalid thumbnail filename")
    _need(len(set((values["FM_VIDEO_FILE"], values["FM_CAPTIONS_FILE"],
                   values["FM_THUMBNAIL_FILE"]))) == 3,
          "Duplicate media filenames")
    _need(EPISODE.fullmatch(values["FM_EPISODE"]) is not None,
          "Episode must be a canonical content metadata JSON")
    _need(APPROVAL.fullmatch(values["FM_APPROVAL_MANIFEST"]) is not None,
          "Approval must be a canonical repo-relative JSON")
    _need(RECEIPT.fullmatch(values["FM_RECEIPT"]) is not None,
          "Receipt must be a canonical repo-relative JSON")
    _need(DIGEST.fullmatch(values["FM_VIDEO_SHA256"]) is not None,
          "Exact lowercase SHA-256 required")
    _need(values["FM_PRIVACY"] == "private",
          "Public/unlisted upload not permitted")
    timestamp = values["FM_PUBLISH_AT_UTC"]
    _need(Z_TIME.fullmatch(timestamp) is not None,
          "Expected UTC whole-second timestamp")
    try:
        target = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc)
    except ValueError as exc:
        raise DispatchInputRejected("Impossible scheduled date") from exc
    clock = datetime.now(timezone.utc) if now is None else now
    _need(isinstance(clock, datetime) and clock.tzinfo is not None
          and clock.utcoffset() is not None,
          "Trusted aware UTC time required")
    _need(target > clock.astimezone(timezone.utc) + timedelta(minutes=15),
          "Not safely in future: refuse scheduled upload")
    return {
        "status": "B4F0_DISPATCH_PARAMETERS_STRUCTURALLY_VALID_ONLY",
        "remote_artifact_verified": False,
        "real_owner_or_media_approved": False,
        "youtube_insert_authorized_by_this_check": False,
    }


def validate_source_run(source: dict) -> dict:
    """Validate trusted GitHub CLI readback, never accept dispatch arguments as proof."""
    _need(type(source) is dict, "GitHub run readback must be an object")
    _need(source.get("headBranch") == "main"
          and source.get("conclusion") == "success"
          and source.get("event") in ("push", "schedule", "workflow_dispatch"),
          "Source run is not a successful trusted main run")
    head = source.get("headSha")
    _need(type(head) is str and DIGEST.fullmatch(head) is None
          and re.fullmatch(r"[0-9a-f]{40}\Z", head) is not None,
          "Invalid source commit SHA")
    return {
        "status": "B4F0_SUCCESSFUL_MAIN_SOURCE_RUN_METADATA_ONLY",
        "media_rights_or_owner_approved": False,
        "youtube_insert_authorized": False,
    }


def validate_downloaded_media(root: Path, env: dict) -> dict:
    validate_dispatch(env)
    _need(not root.is_symlink() and root.is_dir(), "Unexpected artifact root")
    for key in ("FM_VIDEO_FILE", "FM_CAPTIONS_FILE", "FM_THUMBNAIL_FILE"):
        path = root / env[key]
        _need(not path.is_symlink() and path.is_file() and
              100 <= path.stat().st_size <= 4_000_000_000,
              "Missing, linked, empty or excessively large artifact file")
    return {"status": "B4F0_LOCAL_ARTIFACT_FILES_PRESENT_NOT_APPROVED",
            "hash_and_rights_verified": False,
            "youtube_insert_authorized": False}


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("dispatch", "source", "files"):
        raise SystemExit("Use dispatch | source | files (no publication)")
    try:
        if sys.argv[1] == "dispatch":
            result = validate_dispatch(os.environ)
        elif sys.argv[1] == "source":
            result = validate_source_run(json.load(sys.stdin))
        else:
            result = validate_downloaded_media(Path("incoming"), os.environ)
    except (DispatchInputRejected, OSError, ValueError) as exc:
        # Never log raw input values in failures (could contain payloads/tokens).
        raise SystemExit("Manual publishing preflight denied") from None
    print(json.dumps(result, sort_keys=True))
