"""Offline, fail-closed inspection of a downloaded Google Flow clip.

Not a Flow API, credential client, or YouTube uploader. A media pass does NOT
certify identity, rights, subtitles, creative quality, or publication approval.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json
import math
import re
import subprocess
from .flow_cinematic_handoff import build_plan, FlowHandoffError

MAX_BYTES = 250_000_000
SAFE_MP4 = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,120}\.mp4")


@dataclass(frozen=True)
class ClipEvidence:
    episode_id: str
    clip_id: str
    status: str
    file_name: str | None
    media_sha256: str | None
    duration_seconds: float | None
    width: int | None
    height: int | None
    fps: float | None
    video_codec: str | None
    audio_codec: str | None
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    declared_source: str
    technical_candidate: bool = False
    source_independently_verified: bool = False
    character_consistency_verified: bool = False
    natural_voice_verified: bool = False
    asset_rights_verified: bool = False
    spoken_claims_reviewed: bool = False
    subtitle_alignment_verified: bool = False
    release_authorized: bool = False
    youtube_uploaded: bool = False
    youtube_scheduled: bool = False


def _blocked(ep, clip, origin, error):
    return ClipEvidence(ep, clip, "BLOCKED_TECHNICAL_INTAKE",
                        None, None, None, None, None, None, None, None,
                        (error,), (), origin)


def inspect_flow_clip(media_path: str | Path, package: dict, *,
                      episode_id: str, clip_id: str,
                      mode: str = "pilot",
                      source: str = "google_flow_download") -> ClipEvidence:
    if source not in ("google_flow_download", "user_supplied_file"):
        raise FlowHandoffError("Unrecognized source declaration")
    plan = build_plan(package, mode=mode)
    selected = [s for s in plan["clips"]
                if s["episode_id"] == episode_id and s["clip_id"] == clip_id]
    if len(selected) != 1:
        raise FlowHandoffError("Clip is not part of chosen plan")
    path = Path(media_path)
    if not SAFE_MP4.fullmatch(path.name) or path.is_symlink() or not path.is_file():
        return _blocked(episode_id, clip_id, source, "UNSAFE_OR_MISSING_MP4")
    if not 100 <= path.stat().st_size <= MAX_BYTES:
        return _blocked(episode_id, clip_id, source, "MEDIA_SIZE_OUT_OF_BOUNDS")
    try:
        probe = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries",
            "stream=codec_type,codec_name,width,height,r_frame_rate:"
            "format=duration,format_name", "-of", "json", str(path)],
            capture_output=True, text=True, timeout=60, check=False)
        if probe.returncode:
            return _blocked(episode_id, clip_id, source, "FFPROBE_FAILED")
        payload = json.loads(probe.stdout)
        videos = [s for s in payload.get("streams", []) if s.get("codec_type") == "video"]
        audios = [s for s in payload.get("streams", []) if s.get("codec_type") == "audio"]
        if len(videos) != 1 or len(audios) > 1:
            return _blocked(episode_id, clip_id, source, "INVALID_STREAM_LAYOUT")
        video = videos[0]
        width, height = int(video["width"]), int(video["height"])
        duration = float(payload["format"]["duration"])
        fps = float(Fraction(video["r_frame_rate"]))
        video_codec = video.get("codec_name")
        audio_codec = audios[0].get("codec_name") if audios else None
        errors = []
        warnings = ["DECLARED_SOURCE_NOT_INDEPENDENTLY_VERIFIED",
                    "VISUAL_AUDIO_FACTS_AND_RIGHTS_REVIEW_REQUIRED"]
        expected_ratio = 9 / 16 if selected[0]["target_orientation"] == "9:16" else 16 / 9
        if not 360 <= min(width,height) <= 2160 or max(width,height) > 4096:
            errors.append("DIMENSIONS_OUT_OF_BOUNDS")
        if not math.isfinite(width / height) or abs(width / height - expected_ratio) > .025:
            errors.append("WRONG_ASPECT_RATIO")
        if not math.isfinite(duration) or not 8 <= duration <= 10.5:
            errors.append("INVALID_CLIP_DURATION")
        elif abs(duration - selected[0]["expected_seconds"]) > .5:
            warnings.append("TRIM_OR_PADDING_REQUIRED")
        if not math.isfinite(fps) or not 18 <= fps <= 60:
            errors.append("INVALID_FPS")
        if video_codec not in ("h264", "hevc", "av1", "vp9"):
            errors.append("UNSUPPORTED_CODEC")
        if "mp4" not in payload["format"].get("format_name", "").split(","):
            errors.append("NOT_MP4")
        if audio_codec is None:
            warnings.append("NARRATION_AUDIO_MISSING")
        elif audio_codec not in ("aac", "opus", "mp3"):
            warnings.append("AUDIO_TRANSCODE_REQUIRED")
        decode = subprocess.run([
            "ffmpeg", "-hide_banner", "-nostdin", "-v", "error",
            "-xerror", "-i", str(path), "-f", "null", "-"],
            capture_output=True, text=True, timeout=120, check=False)
        if decode.returncode:
            errors.append("FULL_DECODE_FAILED")
        digest = sha256()
        with path.open("rb") as file:
            for data in iter(lambda: file.read(1024*1024), b""):
                digest.update(data)
        return ClipEvidence(
            episode_id, clip_id,
            "PASS_MEDIA_INTAKE_PENDING_INDEPENDENT_QA" if not errors else "BLOCKED_TECHNICAL_INTAKE",
            path.name, digest.hexdigest(), round(duration,3), width, height,
            round(fps,3), video_codec, audio_codec, tuple(sorted(set(errors))),
            tuple(sorted(set(warnings))), source, technical_candidate=not errors)
    except (OSError, ValueError, KeyError, TypeError, ZeroDivisionError,
            subprocess.TimeoutExpired, json.JSONDecodeError):
        return _blocked(episode_id, clip_id, source, "MEDIA_INSPECTION_UNAVAILABLE")


def redacted_json(result: ClipEvidence) -> dict:
    """Serializes evidence without including private local filesystem paths."""
    return asdict(result)
