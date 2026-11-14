"""CLIVOX P4: offline inspection primitive for a creator-delivered local master.

Technical validation ONLY. It does NOT authenticate a creator, commercial
license, vault ACL, grant/revocation, editorial approval, or YouTube upload.
No network, files copied, source downloader, writes, media render, or signing.
Invoke only inside an independently approved isolated PRIVATE runtime.
Public CI exercises this primitive exclusively with self-generated media.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess

from scripts.branch3_v2_p4_synthetic_handoff_preflight import CHANNEL, ROOT

NAME = re.compile(r"master_[a-z0-9_-]{4,48}\.mp4\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
MAX_MASTER_BYTES = 3 * 1024 ** 3
MAX_PROBE_BYTES = 64_000
HOLD = "TECHNICAL_LOCAL_MASTER_QA_ONLY_NOT_LICENSED_OR_AUTHORIZED"


class MasterDenied(ValueError):
    """No file identity, media shape or rights assertion may fail open."""


def need(condition: bool, reason: str) -> None:
    if not condition:
        raise MasterDenied("CLIVOX_P4_MASTER_DENIED_" + reason)


def _checked_target(scratch: Path, basename: str) -> Path:
    need(isinstance(scratch, Path) and type(basename) is str
         and NAME.fullmatch(basename) is not None, "INPUT_SHAPE")
    need(scratch.is_absolute() and scratch.is_dir()
         and not scratch.is_symlink(), "PRIVATE_SCRATCH")
    real = scratch.resolve(strict=True)
    need(scratch == real and ROOT.resolve() not in real.parents
         and ROOT.resolve() != real, "NOT_PUBLIC_REPO_OR_LINKED_PATH")
    need(real.stat().st_mode & 0o077 == 0, "SCRATCH_MUST_BE_OWNER_ONLY")
    target = real / basename
    need(target.is_file() and not target.is_symlink()
         and target.resolve(strict=True).parent == real,
         "SOURCE_IS_LOCAL_REGULAR")
    return target


def _hash_file(target: Path, expected_bytes: int) -> str:
    need(hasattr(os, "O_NOFOLLOW"), "NOFOLLOW_PLATFORM_REQUIRED")
    fd = os.open(target, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
             and before.st_size == expected_bytes, "INODE_OR_LENGTH")
        digest = hashlib.sha256()
        first = b""
        with os.fdopen(fd, "rb", closefd=False) as source:
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                if not first:
                    first = chunk[:12]
                digest.update(chunk)
        after = os.fstat(fd)
        need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
             == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
             "FILE_CHANGED_DURING_HASH")
        need(len(first) == 12 and first[4:8] == b"ftyp",
             "NOT_MP4_MAGIC")
        return digest.hexdigest()
    finally:
        os.close(fd)


def validate_master_probe(doc: object, expected_bytes: int) -> dict:
    """MP4 H264/AAC, one audio/video stream, bounded 10 s–2 h offline source."""
    need(type(doc) is dict and type(doc.get("streams")) is list
         and type(doc.get("format")) is dict, "PROBE_OBJECT")
    streams = doc["streams"]
    need(len(streams) == 2 and all(type(s) is dict for s in streams),
         "EXACT_TWO_STREAMS")
    video = [s for s in streams if s.get("codec_type") == "video"]
    audio = [s for s in streams if s.get("codec_type") == "audio"]
    need(len(video) == len(audio) == 1, "EXACT_VIDEO_AND_AUDIO")
    v, a = video[0], audio[0]
    need(v.get("codec_name") == "h264" and v.get("pix_fmt") == "yuv420p"
         and type(v.get("width")) is int and 320 <= v["width"] <= 3840
         and type(v.get("height")) is int and 240 <= v["height"] <= 2160,
         "VIDEO_PROFILE")
    need(a.get("codec_name") == "aac" and str(a.get("sample_rate")) in
         ("44100", "48000") and type(a.get("channels")) is int
         and a["channels"] in (1, 2), "AUDIO_PROFILE")
    try:
        fps = Fraction(v["avg_frame_rate"])
        duration = float(doc["format"]["duration"])
        size = int(doc["format"]["size"])
    except (ValueError, ZeroDivisionError, OverflowError, TypeError, KeyError):
        raise MasterDenied("CLIVOX_P4_MASTER_DENIED_INVALID_PROBE") from None
    need(math.isfinite(duration) and 10 <= duration <= 7200
         and 15 <= fps <= 120 and size == expected_bytes,
         "DURATION_RATE_OR_SIZE")
    name = doc["format"].get("format_name")
    need(type(name) is str and "mp4" in name.split(","),
         "MP4_CONTAINER")
    return {
        "duration_seconds": round(duration, 3),
        "frame_rate": float(fps),
        "width": v["width"],
        "height": v["height"],
    }


def inspect_local_master(*, scratch: Path, basename: str,
                         expected_sha256: str, expected_bytes: int,
                         runner=subprocess.run) -> dict:
    """Read-only byte and ffprobe check. Caller digest is NOT trusted rights.

    Do not use this result as an authenticated P3 license or P4 acceptance.
    The adapter never authorizes any transform or download even on success.
    """
    need(type(expected_sha256) is str and SHA.fullmatch(expected_sha256)
         is not None, "EXPECTED_DIGEST")
    need(type(expected_bytes) is int
         and 128 <= expected_bytes <= MAX_MASTER_BYTES, "EXPECTED_BYTES")
    target = _checked_target(scratch, basename)
    before = target.stat()
    need(before.st_size == expected_bytes, "FILE_SIZE")
    need(_hash_file(target, expected_bytes) == expected_sha256,
         "SHA256_MISMATCH")
    command = [
        "ffprobe", "-v", "error", "-protocol_whitelist", "file",
        "-show_streams", "-show_format", "-of", "json", str(target),
    ]
    try:
        result = runner(command, check=False, capture_output=True,
                        text=True, timeout=45)
    except (subprocess.TimeoutExpired, OSError):
        raise MasterDenied("CLIVOX_P4_MASTER_DENIED_PROBE_FAILED") from None
    need(result.returncode == 0 and type(result.stdout) is str
         and 0 < len(result.stdout) <= MAX_PROBE_BYTES,
         "PROBE_FAILED_OR_TOO_LARGE")
    try:
        probe = json.loads(result.stdout)
    except (ValueError, TypeError):
        raise MasterDenied("CLIVOX_P4_MASTER_DENIED_PROBE_JSON") from None
    media = validate_master_probe(probe, expected_bytes)
    after = target.stat()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
         == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
         "FILE_CHANGED_DURING_PROBE")
    need(_hash_file(target, expected_bytes) == expected_sha256,
         "SHA256_CHANGED_AFTER_PROBE")
    return {
        "stage": "CLIVOX_V2_P4_LOCAL_MASTER_TECHNICAL_INSPECTION",
        "channel_id": CHANNEL,
        "private_runtime_requirement": "OWNER_APPROVED_ISOLATED_RUNTIME_NOT_PUBLIC_CI",
        "technical_hash_and_probe_passed": True,
        "technical_media": media,
        "full_decode_and_editorial_review_passed": False,
        "creator_identity_authenticated": False,
        "creator_commercial_license_authenticated": False,
        "underlying_music_game_guest_rights_authenticated": False,
        "vault_access_rights_authenticated": False,
        "revocations_rechecked": False,
        "source_ingest_authorized": False,
        "clip_edit_authorized": False,
        "youtube_upload_authorized": False,
        "youtube_publish_authorized": False,
        "p4_real_milestone_complete": False,
        "status": HOLD,
    }


def production_media_ingest(*_args, **_kwargs) -> None:
    raise MasterDenied("CLIVOX_P4_MASTER_DENIED_NO_AUTHORIZED_INGEST")


if __name__ == "__main__":
    raise SystemExit("CLIVOX_P4_MASTER_NO_PUBLIC_CLI_PRIVATE_RUNTIME_REQUIRED")
