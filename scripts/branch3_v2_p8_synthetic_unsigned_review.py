"""CLIVOX V2 P8: exact synthetic MP4 review packet, UNSIGNED and unpublishable.

Never processes a creator-source file. Reads only the prior generated P7 MP4
inside an ephemeral runner, revalidates exact bytes and closed A3/P4/A6 state,
then writes a review request with EVERY approval check false. This module
does NOT generate keys, verify human identity, sign, upload or release media.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

from scripts.branch3_v2_p5_synthetic_moment_proposals import (
    CHANNEL, P5Denied, _probe_closed,
)
from scripts.branch3_v2_p6_synthetic_storyboard import (
    P6Denied, validate_storyboard,
)
from scripts.branch3_v2_p7_synthetic_vertical_renderer import (
    P7Denied, OUTPUT_NAME, WIDTH, HEIGHT, FPS, verify_output_probe,
    check_original_signal_and_captions,
)
from scripts.branch3_v2_p4_synthetic_handoff_preflight import (
    MAX_FIXTURE_BYTES, P4Denied, inspect_synthetic_fixture,
)
from scripts.branch3_a6_signed_release import (
    FIXTURE as A6_FIXTURE, POLICY as A6_POLICY,
    ReleaseBlocked, validate_quarantine_manifest, production_release,
)

EDL_FILE = "synthetic-edl-draft-only.json"
QA_FILE = "synthetic-render-qa-only.json"
REVIEW_FILE = "owner-review-UNSIGNED-synthetic.json"
MAX_JSON_BYTES = 32768
DOMAIN = "CLIVOX-V2-P8-EXACT-SYNTHETIC-UNSIGNED-REVIEW-V1"
SHA = re.compile(r"[0-9a-f]{64}\Z")
CHECKS = (
    "actual_finished_video_watched_by_owner",
    "actual_source_speaker_voice_and_quotes_verified",
    "original_clivox_commentary_context_human_reviewed",
    "creator_commercial_license_authentically_verified",
    "publisher_game_guest_and_music_rights_cleared",
    "current_revocations_independently_rechecked",
    "captions_audio_and_crop_final_human_reviewed",
    "owner_signing_identity_enrolled_outside_public_ci",
)
QA_TRUE = (
    "synthetic_original_lavfi_only",
    "original_synthetic_mp4_rendered_in_ephemeral_scratch",
    "synthetic_h264_aac_decode_validated",
    "synthetic_portrait_9_16_validated",
    "synthetic_original_caption_pixels_validated",
    "synthetic_audio_cue_and_scene_sync_validated",
)
QA_FALSE = (
    "real_1080x1920_output_validated",
    "real_creator_source_processing_allowed",
    "real_editorial_context_verified",
    "owner_exact_final_media_approved",
    "youtube_publish_authorized",
    "p7_real_licensed_compositor_milestone_complete",
)
QA_FIELDS = frozenset({
    "stage", "channel_id", *QA_TRUE, *QA_FALSE,
    "source_creator_media_count", "real_creator_licenses_verified",
    "preview_width", "preview_height", "duration_ms", "youtube_uploads",
    "status",
})
PACKET_FIELDS = frozenset({
    "schema_version", "domain", "channel_id", "review_state",
    "source_scope", "exact_synthetic_video_sha256", "exact_video_bytes",
    "exact_p6_storyboard_sha256", "exact_p7_qa_report_sha256",
    "source_rights_evidence_sha256", "real_creator_licenses",
    "review_checks", "human_owner_identity_verified",
    "owner_public_key_independently_enrolled",
    "owner_review_completed_at_utc", "detached_signature_base64",
    "owner_release_signed", "requested_youtube_privacy",
    "publish_at_utc", "youtube_upload_authorized",
    "youtube_publish_authorized", "technical_preview_not_production_master",
    "real_rights_freshness_verified",
})


class P8Denied(ValueError):
    """Missing rights and real owner review remain permanently closed here."""


def require(value: bool, reason: str) -> None:
    if not value:
        raise P8Denied("CLIVOX_V2_P8_DENIED_" + reason)


def canonical(obj: object) -> bytes:
    require(type(obj) is dict, "CANONICAL_JSON_OBJECT")
    try:
        return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, allow_nan=False).encode("utf-8")
    except (ValueError, TypeError, OverflowError):
        raise P8Denied("CLIVOX_V2_P8_DENIED_CANONICAL_JSON") from None


def closed_release_boundary() -> None:
    """Reuse actual A6 release quarantine instead of inventing a second signer."""
    _probe_closed()
    try:
        m = json.loads(A6_FIXTURE.read_text(encoding="utf-8"))
        p = json.loads(A6_POLICY.read_text(encoding="utf-8"))
        released = validate_quarantine_manifest(m, p)
    except (OSError, ValueError, KeyError, TypeError, ReleaseBlocked):
        raise P8Denied("CLIVOX_V2_P8_DENIED_A6_RELEASE_POLICY") from None
    require(released["owner_public_key_enrolled"] is False
            and released["signed_licensed_assets"] == 0
            and released["video_upload_authorized"] is False
            and released["youtube_publish_authorized"] is False,
            "A6_MUST_REMAIN_CLOSED")


def _read_ephemeral(root: Path, name: str) -> dict:
    require(isinstance(root, Path) and root.is_dir()
            and not root.is_symlink()
            and name in (EDL_FILE, QA_FILE), "LOCAL_JSON_ONLY")
    base = root.resolve(strict=True)
    target = base / name
    require(target.is_file() and not target.is_symlink()
            and target.resolve(strict=True).parent == base
            and 0 < target.stat().st_size <= MAX_JSON_BYTES,
            "JSON_PATH_OR_SIZE")
    try:
        x = json.loads(target.read_text(encoding="utf-8"))
    except (ValueError, OSError, UnicodeError):
        raise P8Denied("CLIVOX_V2_P8_DENIED_JSON_FORMAT") from None
    require(type(x) is dict, "JSON_OBJECT")
    return x


def validate_p7_technical_report(report: object) -> dict:
    closed_release_boundary()
    require(type(report) is dict and set(report) == QA_FIELDS,
            "P7_REPORT_EXACT_SCHEMA")
    require(report["stage"] ==
            "CLIVOX_V2_P7_ORIGINAL_SYNTHETIC_VERTICAL_RENDER_QA_ONLY"
            and report["channel_id"] == CHANNEL
            and report["status"] ==
            "SYNTHETIC_RENDER_QA_ONLY_NO_CREATOR_LICENSE_NO_RELEASE",
            "P7_REPORT_IDENTITY")
    require(all(report[name] is True for name in QA_TRUE)
            and all(report[name] is False for name in QA_FALSE),
            "P7_QA_FLAGS")
    for name in ("source_creator_media_count", "real_creator_licenses_verified",
                 "youtube_uploads"):
        require(type(report[name]) is int and report[name] == 0,
                "P7_FORGED_" + name.upper())
    require(type(report["preview_width"]) is int
            and report["preview_width"] == WIDTH
            and type(report["preview_height"]) is int
            and report["preview_height"] == HEIGHT
            and type(report["duration_ms"]) is int
            and report["duration_ms"] == 6000,
            "P7_PREVIEW_ONLY")
    return report


def _hash_exact_synthetic_mp4(scratch: Path) -> tuple[str, int]:
    require(isinstance(scratch, Path) and scratch.is_dir()
            and not scratch.is_symlink(), "MEDIA_SCRATCH")
    base = scratch.resolve(strict=True)
    target = base / OUTPUT_NAME
    require(target.is_file() and not target.is_symlink()
            and target.resolve(strict=True).parent == base,
            "ONLY_FIXED_RENDER_FILE")
    before = target.stat()
    require(stat.S_ISREG(before.st_mode)
            and 128 <= before.st_size <= MAX_FIXTURE_BYTES,
            "BOUNDED_MP4_SIZE")
    require(hasattr(os, "O_NOFOLLOW"), "NOFOLLOW_REQUIRED")
    fd = os.open(target, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        seen = os.fstat(fd)
        require((seen.st_dev, seen.st_ino, seen.st_size) ==
                (before.st_dev, before.st_ino, before.st_size),
                "MP4_CHANGED_BEFORE_READ")
        hasher = hashlib.sha256()
        with os.fdopen(fd, "rb", closefd=False) as stream:
            while chunk := stream.read(65536):
                hasher.update(chunk)
    finally:
        os.close(fd)
    after = target.stat()
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
            == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
            "MP4_CHANGED_DURING_READ")
    return hasher.hexdigest(), before.st_size


def make_unsigned_packet(*, video_sha: str, video_bytes: int,
                         edl: dict, p7_report: dict) -> dict:
    closed_release_boundary()
    require(type(video_sha) is str and SHA.fullmatch(video_sha) is not None
            and type(video_bytes) is int
            and 128 <= video_bytes <= MAX_FIXTURE_BYTES,
            "EXACT_RENDER_DIGEST")
    try:
        validate_storyboard(edl)
    except (P6Denied, P5Denied, ValueError, TypeError, KeyError):
        raise P8Denied("CLIVOX_V2_P8_DENIED_P6_STORYBOARD") from None
    validate_p7_technical_report(p7_report)
    packet = {
        "schema_version": 1, "domain": DOMAIN, "channel_id": CHANNEL,
        "review_state": "UNSIGNED_QUARANTINED_TEST_ONLY",
        "source_scope": "SELF_GENERATED_LAVFI_ONLY_NO_CREATOR_FOOTAGE",
        "exact_synthetic_video_sha256": video_sha,
        "exact_video_bytes": video_bytes,
        "exact_p6_storyboard_sha256": hashlib.sha256(canonical(edl)).hexdigest(),
        "exact_p7_qa_report_sha256": hashlib.sha256(canonical(p7_report)).hexdigest(),
        "source_rights_evidence_sha256": None,
        "real_creator_licenses": 0,
        "review_checks": {key: False for key in CHECKS},
        "human_owner_identity_verified": False,
        "owner_public_key_independently_enrolled": False,
        "owner_review_completed_at_utc": None,
        "detached_signature_base64": None,
        "owner_release_signed": False,
        "requested_youtube_privacy": "private",
        "publish_at_utc": None,
        "youtube_upload_authorized": False,
        "youtube_publish_authorized": False,
        "technical_preview_not_production_master": True,
        "real_rights_freshness_verified": False,
    }
    return validate_unsigned_packet(packet, video_sha=video_sha,
                                    video_bytes=video_bytes, edl=edl,
                                    p7_report=p7_report)


def validate_unsigned_packet(packet: object, *, video_sha: str,
                             video_bytes: int, edl: dict,
                             p7_report: dict) -> dict:
    closed_release_boundary()
    require(type(packet) is dict and set(packet) == PACKET_FIELDS,
            "EXACT_REVIEW_PACKET_FIELDS")
    require(type(packet["schema_version"]) is int
            and packet["schema_version"] == 1
            and packet["domain"] == DOMAIN
            and packet["channel_id"] == CHANNEL
            and packet["review_state"] == "UNSIGNED_QUARANTINED_TEST_ONLY"
            and packet["source_scope"] ==
            "SELF_GENERATED_LAVFI_ONLY_NO_CREATOR_FOOTAGE",
            "PACKET_IDENTITY")
    require(type(video_sha) is str and SHA.fullmatch(video_sha) is not None
            and type(packet["exact_synthetic_video_sha256"]) is str
            and packet["exact_synthetic_video_sha256"] == video_sha
            and type(video_bytes) is int
            and type(packet["exact_video_bytes"]) is int
            and packet["exact_video_bytes"] == video_bytes
            and 128 <= video_bytes <= MAX_FIXTURE_BYTES,
            "EXACT_MP4_BINDING")
    try:
        validate_storyboard(edl)
    except (P6Denied, P5Denied, ValueError, TypeError, KeyError):
        raise P8Denied("CLIVOX_V2_P8_DENIED_P6_REVIEW") from None
    validate_p7_technical_report(p7_report)
    require(packet["exact_p6_storyboard_sha256"] ==
            hashlib.sha256(canonical(edl)).hexdigest()
            and packet["exact_p7_qa_report_sha256"] ==
            hashlib.sha256(canonical(p7_report)).hexdigest(),
            "EXACT_PLAN_AND_QA_BINDING")
    require(packet["source_rights_evidence_sha256"] is None
            and type(packet["real_creator_licenses"]) is int
            and packet["real_creator_licenses"] == 0,
            "NO_REAL_RIGHTS")
    require(type(packet["review_checks"]) is dict
            and set(packet["review_checks"]) == set(CHECKS)
            and all(packet["review_checks"][k] is False for k in CHECKS),
            "HUMAN_CHECKS_MUST_BE_UNCHECKED")
    for name in ("human_owner_identity_verified",
                 "owner_public_key_independently_enrolled",
                 "owner_release_signed", "youtube_upload_authorized",
                 "youtube_publish_authorized", "real_rights_freshness_verified"):
        require(packet[name] is False, "FORGED_" + name.upper())
    require(packet["owner_review_completed_at_utc"] is None
            and packet["detached_signature_base64"] is None
            and packet["publish_at_utc"] is None
            and packet["requested_youtube_privacy"] == "private"
            and packet["technical_preview_not_production_master"] is True,
            "NO_FINAL_RELEASE_OR_SCHEDULE")
    return packet


def inspect_and_prepare_unsigned(*, scratch: Path,
                                 runner=subprocess.run) -> dict:
    """Re-check exact generated MP4 then create a not-signed review packet."""
    closed_release_boundary()
    edl = _read_ephemeral(scratch, EDL_FILE)
    report = _read_ephemeral(scratch, QA_FILE)
    digest, count = _hash_exact_synthetic_mp4(scratch)
    packet = make_unsigned_packet(
        video_sha=digest, video_bytes=count, edl=edl, p7_report=report)
    try:
        qc = inspect_synthetic_fixture(
            scratch=scratch, basename=OUTPUT_NAME,
            expected_sha256=digest, expected_bytes=count, runner=runner,
        )
    except (P4Denied, OSError, TypeError, KeyError, ValueError):
        raise P8Denied("CLIVOX_V2_P8_DENIED_P4_REVALIDATION") from None
    require(qc["synthetic_fixture_decoded"] is True
            and qc["rights_grants_verified"] == 0
            and qc["youtube_publish_enabled"] is False,
            "NO_SOURCE_OR_RELEASE")
    target = scratch.resolve(strict=True) / OUTPUT_NAME
    try:
        probe = runner([
            "ffprobe", "-v", "error", "-protocol_whitelist", "file",
            "-show_format", "-show_streams", "-of", "json", str(target),
        ], capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise P8Denied("CLIVOX_V2_P8_DENIED_FFPROBE_FAILURE") from None
    require(probe.returncode == 0 and type(probe.stdout) is str
            and len(probe.stdout) <= 40000, "PROBE_RESULT")
    try:
        verify_output_probe(json.loads(probe.stdout), actual_bytes=count)
    except (P7Denied, TypeError, KeyError, ValueError):
        raise P8Denied("CLIVOX_V2_P8_DENIED_P7_FRAME_AUDIO_PROBE") from None
    try:
        check_original_signal_and_captions(target, runner=runner)
    except (P7Denied, OSError, ValueError):
        raise P8Denied("CLIVOX_V2_P8_DENIED_REVIEW_MEDIA_CONTENT_QA") from None
    require(_hash_exact_synthetic_mp4(scratch) == (digest, count),
            "MEDIA_CHANGED_AFTER_QA")
    validate_unsigned_packet(packet, video_sha=digest, video_bytes=count,
                             edl=edl, p7_report=report)
    closed_release_boundary()
    out = scratch.resolve(strict=True) / REVIEW_FILE
    require(not out.exists() and not out.is_symlink(), "DO_NOT_OVERWRITE")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    try:
        fd = os.open(out, flags, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(packet, stream, sort_keys=True, indent=2)
            stream.write("\n")
    except OSError:
        raise P8Denied("CLIVOX_V2_P8_DENIED_REVIEW_PACKET_WRITE") from None
    return {
        "stage": "CLIVOX_V2_P8_SYNTHETIC_EXACT_MEDIA_UNSIGNED_REVIEW_QA",
        "channel_id": CHANNEL,
        "synthetic_exact_video_bytes_hashed": True,
        "synthetic_exact_p6_edl_and_p7_qa_hash_bound": True,
        "synthetic_media_redecoded_and_audio_visual_rechecked": True,
        "unsigned_quarantined_review_packet_created_in_runner": True,
        "review_checks_default_false": True,
        "real_rights_grants": 0, "real_creator_media": 0,
        "real_trusted_owner_key_enrolled": False,
        "authentic_owner_review_verified": False,
        "actual_owner_detached_signature_present": False,
        "real_rights_revocation_freshness_verified": False,
        "youtube_uploads": 0, "youtube_publish_authorized": False,
        "p8_real_owner_release_milestone_complete": False,
        "status": "P8_SYNTHETIC_UNSIGNED_EVIDENCE_ONLY_NO_REAL_RELEASE",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("closed", "synthetic"),
                        default="closed")
    parser.add_argument("--scratch", type=Path)
    args = parser.parse_args()
    try:
        closed_release_boundary()
        if args.mode == "closed":
            require(args.scratch is None, "CLOSED_INPUT")
            result = {
                "stage": "CLIVOX_V2_P8_OWNER_REVIEW_CLOSED",
                "channel_id": CHANNEL,
                "real_rights_grants": 0,
                "real_trusted_owner_key_enrolled": False,
                "authentic_owner_review_verified": False,
                "youtube_uploads": 0,
            }
        else:
            require(args.scratch is not None, "EPHEMERAL_SCRATCH_REQUIRED")
            result = inspect_and_prepare_unsigned(scratch=args.scratch)
        print(json.dumps(result, sort_keys=True))
    except (P8Denied, P7Denied, P6Denied, P5Denied, P4Denied,
            ReleaseBlocked, OSError, TypeError, ValueError,
            KeyError, UnicodeError):
        raise SystemExit(
            "CLIVOX_V2_P8_BLOCKED_NO_REAL_OWNER_SIGNATURE_OR_SOURCE_GRANTS"
        ) from None


if __name__ == "__main__":
    main()
