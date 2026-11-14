"""CLIVOX V2 P4: quarantined, source-free technical media inspection.

This module CANNOT grant rights, fetch a URL, create a private vault, write
media, or publish to YouTube. The public CI path accepts only a small
synthetic local test file in a caller-provided scratch directory.
A green media inspection is NOT creator permission or a P4 milestone pass.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

from scripts.branch3_media_storage_preflight import (
    CHANNEL_STATE, CREATOR_PERMS, MANIFEST, POLICY, read_json, validate_policy,
)

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "branch3/clipping_v2/architecture-status.json"
CHANNEL = "UCfPEvy0SefE_5nNlYlY_CyQ"
MAX_FIXTURE_BYTES = 8 * 1024 * 1024
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
SAFE_NAME = re.compile(r"[a-z][a-z0-9_-]{0,48}\.mp4\Z")


class P4Denied(ValueError):
    """Private-source work remains blocked by legal/owner approval."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise P4Denied("CLIVOX_V2_P4_DENIED_" + code)


def closed_boundary(*, storage_policy: dict, manifest: dict,
                    creator_registry: dict, channel_state: dict,
                    v2_status: dict) -> dict:
    """Validate the real existing A3 and V2 CLOSED contracts, not a new grant."""
    try:
        preflight = validate_policy(storage_policy, manifest, creator_registry,
                                    channel_state)
    except (ValueError, KeyError, TypeError) as exc:
        raise P4Denied("CLIVOX_V2_P4_DENIED_UPSTREAM_A3_CLOSED_POLICY") from None
    require(preflight["source_download_authorized"] is False
            and preflight["youtube_publish_authorized"] is False,
            "STORAGE_NOT_CLOSED")
    require(type(v2_status) is dict
            and v2_status.get("schema_version") == 1
            and v2_status.get("project") == "CLIVOX_VIRAL_CLIPPING_V2"
            and v2_status.get("channel_id") == CHANNEL
            and v2_status.get("public_repo") == "Tirthanand17/taskless-lab",
            "V2_IDENTITY")
    require(type(v2_status.get("confirmed_creator_commercial_grants")) is int
            and v2_status["confirmed_creator_commercial_grants"] == 0,
            "NO_ACTUAL_CREATOR_GRANTS")
    require(type(v2_status.get("confirmed_rights_cleared_source_files")) is int
            and v2_status["confirmed_rights_cleared_source_files"] == 0,
            "NO_AUTHORIZED_SOURCE_FILES")
    for field in (
        "private_licensed_media_storage_ready",
        "owner_commercial_reuse_authorization_verified",
        "clivox_live_uploads_enabled", "youtube_media_download_enabled",
        "creator_outreach_sent", "clivox_channel_oauth_write_enabled",
    ):
        require(v2_status.get(field) is False, "PREMATURE_" + field.upper())
    require(v2_status.get("roadmap_confirmed_completed_phases") == 2
            and v2_status.get("p3_real_source_clip_licenses_attained") == 0,
            "FORGED_ROADMAP_OR_RIGHTS")
    return {
        "stage": "CLIVOX_V2_P4_SYNTHETIC_MEDIA_HANDOFF_QUARANTINE",
        "channel_id": CHANNEL,
        "rights_grants_verified": 0,
        "real_media_delivered": 0,
        "private_vault_activated": False,
        "creator_media_fetch_enabled": False,
        "creator_media_write_enabled": False,
        "youtube_upload_enabled": False,
        "youtube_publish_enabled": False,
        "p4_milestone_complete": False,
        "synthetic_fixture_integrity_checked": False,
        "synthetic_fixture_codec_checked": False,
        "synthetic_fixture_decoded": False,
        "status": "BLOCKED_NO_PRIVATE_VAULT_OR_REAL_COMMERCIAL_SOURCE_GRANTS",
    }


def actual_closed_boundary() -> dict:
    return closed_boundary(
        storage_policy=read_json(POLICY), manifest=read_json(MANIFEST),
        creator_registry=read_json(CREATOR_PERMS),
        channel_state=read_json(CHANNEL_STATE),
        v2_status=read_json(STATUS),
    )


def check_probe(doc: object, actual_size: int) -> None:
    """Verify a bounded synthetic H.264/AAC MP4; never infer legal rights."""
    require(type(doc) is dict and
            type(doc.get("streams")) is list and
            type(doc.get("format")) is dict, "PROBE_SCHEMA")
    streams = doc["streams"]
    require(len(streams) == 2 and all(type(s) is dict for s in streams),
            "TWO_AV_STREAMS_REQUIRED")
    videos = [s for s in streams if s.get("codec_type") == "video"]
    audios = [s for s in streams if s.get("codec_type") == "audio"]
    require(len(videos) == 1 and len(audios) == 1, "VIDEO_AND_AUDIO_REQUIRED")
    video, audio = videos[0], audios[0]
    require(video.get("codec_name") == "h264"
            and video.get("pix_fmt") == "yuv420p"
            and type(video.get("width")) is int
            and type(video.get("height")) is int
            and 64 <= video["width"] <= 1920
            and 64 <= video["height"] <= 1920,
            "VIDEO_CODEC_OR_DIMENSIONS")
    require(audio.get("codec_name") == "aac"
            and str(audio.get("sample_rate")) in ("44100", "48000")
            and type(audio.get("channels")) is int
            and audio["channels"] in (1, 2), "AUDIO_CODEC")
    fmt = doc["format"]
    require(type(fmt.get("format_name")) is str
            and "mp4" in fmt["format_name"].split(","), "MP4_CONTAINER")
    try:
        duration = float(fmt["duration"])
        declared_size = int(fmt["size"])
    except (ValueError, TypeError, KeyError, OverflowError):
        raise P4Denied("CLIVOX_V2_P4_DENIED_INVALID_PROBE_VALUES") from None
    require(0.1 <= duration <= 10.0 and declared_size == actual_size,
            "FIXTURE_DURATION_OR_SIZE")


def inspect_synthetic_fixture(
    *, scratch: Path, basename: str, expected_sha256: str,
    expected_bytes: int, runner=subprocess.run,
) -> dict:
    """Only read an existing tiny local test MP4; make no copies or uploads."""
    require(type(basename) is str and SAFE_NAME.fullmatch(basename) is not None,
            "SAFE_FIXTURE_BASENAME")
    require(type(expected_sha256) is str
            and SHA256.fullmatch(expected_sha256) is not None,
            "EXPECTED_SHA256")
    require(type(expected_bytes) is int
            and 32 <= expected_bytes <= MAX_FIXTURE_BYTES,
            "EXPECTED_SIZE")
    require(isinstance(scratch, Path) and not scratch.is_symlink()
            and scratch.is_dir(), "SCRATCH_DIRECTORY")
    root = scratch.resolve(strict=True)
    target = root / basename
    require(not target.is_symlink() and target.is_file()
            and target.resolve(strict=True).parent == root,
            "NO_LINKS_OR_TRAVERSAL")
    before = target.stat()
    require(stat.S_ISREG(before.st_mode) and before.st_size == expected_bytes,
            "ACTUAL_SIZE")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    require(hasattr(os, "O_NOFOLLOW"), "NOFOLLOW_REQUIRED")
    fd = os.open(target, flags)
    try:
        opened = os.fstat(fd)
        require(stat.S_ISREG(opened.st_mode) and
                opened.st_dev == before.st_dev and
                opened.st_ino == before.st_ino and
                opened.st_size == expected_bytes, "FILE_CHANGED_BEFORE_READ")
        hashed = hashlib.sha256()
        prefix = b""
        with os.fdopen(fd, "rb", closefd=False) as stream:
            while True:
                chunk = stream.read(65536)
                if not chunk:
                    break
                if not prefix:
                    prefix = chunk[:12]
                hashed.update(chunk)
        require(len(prefix) == 12 and prefix[4:8] == b"ftyp",
                "NOT_MP4_HEADER")
        require(hashed.hexdigest() == expected_sha256, "SOURCE_SHA_MISMATCH")
    finally:
        os.close(fd)
    commands = (
        ["ffprobe", "-v", "error", "-protocol_whitelist", "file",
         "-show_format", "-show_streams", "-of", "json", str(target)],
        ["ffmpeg", "-nostdin", "-v", "error", "-xerror",
         "-protocol_whitelist", "file", "-i", str(target),
         "-map", "0:v:0", "-map", "0:a:0",
         "-f", "null", "-"],
    )
    for idx, command in enumerate(commands):
        try:
            proc = runner(command, capture_output=True, text=True,
                          timeout=20, check=False)
        except (OSError, subprocess.TimeoutExpired):
            raise P4Denied("CLIVOX_V2_P4_DENIED_MEDIA_TOOL_FAILED") from None
        require(proc.returncode == 0, "MEDIA_PROBE_OR_DECODE_FAILED")
        if idx == 0:
            require(type(proc.stdout) is str and len(proc.stdout) <= 40000,
                    "PROBE_OUTPUT_BOUND")
            try:
                doc = json.loads(proc.stdout)
            except (ValueError, TypeError):
                raise P4Denied("CLIVOX_V2_P4_DENIED_BAD_PROBE_JSON") from None
            check_probe(doc, expected_bytes)
    after = target.stat()
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
            == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
            "FILE_CHANGED_DURING_PROBE")
    report = actual_closed_boundary()
    report.update(
        synthetic_fixture_integrity_checked=True,
        synthetic_fixture_codec_checked=True,
        synthetic_fixture_decoded=True,
        status="SYNTHETIC_SAMPLE_TECHNICAL_QA_ONLY_REAL_SOURCE_STILL_BLOCKED",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("closed", "synthetic-sample"),
                        default="closed")
    parser.add_argument("--scratch", type=Path)
    parser.add_argument("--fixture-file")
    parser.add_argument("--sha256")
    parser.add_argument("--bytes", type=int)
    args = parser.parse_args()
    try:
        closed = actual_closed_boundary()
        if args.mode == "closed":
            require(all(v is None for v in (
                args.scratch, args.fixture_file, args.sha256, args.bytes)),
                "CLOSED_MODE_HAS_MEDIA_ARGS")
            result = closed
        else:
            require(all(v is not None for v in (
                args.scratch, args.fixture_file, args.sha256, args.bytes)),
                "FIXTURE_ARGS_REQUIRED")
            result = inspect_synthetic_fixture(
                scratch=args.scratch, basename=args.fixture_file,
                expected_sha256=args.sha256, expected_bytes=args.bytes)
        print(json.dumps(result, sort_keys=True))
    except (P4Denied, OSError, ValueError, KeyError, TypeError):
        raise SystemExit("CLIVOX_V2_P4_BLOCKED_NO_INGEST_NO_RELEASE") from None


if __name__ == "__main__":
    main()
