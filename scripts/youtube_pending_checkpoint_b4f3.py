"""B4f3 crash-safe local caption ID checkpoint for an EXISTING uploaded video.

Called only after captions.insert returns an ID. This does not contact YouTube,
does not create another upload, and must preserve a preexisting pending receipt
when the crash state is ambiguous.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re

VIDEO=re.compile(r"[A-Za-z0-9_-]{11}\Z")
CAPTION=re.compile(r"[A-Za-z0-9_.-]{1,128}\Z")


class PendingCheckpointRefused(ValueError):
    """Stop; do not remove a possibly sent upload checkpoint."""


def save_existing_caption_identity(path: Path, *, video_id: str, caption_id: str) -> None:
    if (type(path) is not Path
        or not path.name.endswith(".json.pending.json")
        or not path.parent.is_dir() or path.parent.is_symlink()
        or path.is_symlink() or not path.is_file()
        or not 20 <= path.stat().st_size <= 16000
        or type(video_id) is not str or VIDEO.fullmatch(video_id) is None
        or type(caption_id) is not str or CAPTION.fullmatch(caption_id) is None):
        raise PendingCheckpointRefused("Invalid already-uploaded caption checkpoint")
    try:
        existing=json.loads(path.read_text(encoding="utf8"))
    except (UnicodeError,json.JSONDecodeError):
        raise PendingCheckpointRefused("Unreadable existing upload marker") from None
    if (type(existing) is not dict
        or existing.get("state")!="UPLOAD_EXISTS_SCHEDULE_NOT_YET_VERIFIED"
        or existing.get("youtube_schedule_verified") is not False
        or existing.get("video_id")!=video_id
        or "caption_track_id" in existing):
        raise PendingCheckpointRefused("No unique unverified original upload checkpoint")
    existing["caption_track_id"]=caption_id
    temp=path.with_name(path.name+".tmp")
    try:
        fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,"w",encoding="utf8") as stream:
            stream.write(json.dumps(existing,sort_keys=True,indent=2)+"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp,path)
        if os.name=="posix":
            folder=os.open(path.parent,os.O_RDONLY)
            try:
                os.fsync(folder)
            finally:
                os.close(folder)
    except (OSError,ValueError):
        # Never clear old marker: it is the only evidence of a possibly sent
        # remote video. An orphan temp file also blocks an unsafe blind retry.
        raise PendingCheckpointRefused(
            "Caption checkpoint write uncertain; no new upload"
        ) from None
