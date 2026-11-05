"""Actual full-duration H264+AAC smoke with SYNTHETIC TONE, never narration.

No content production, model/provider/account, subtitles, cloud persistence,
speech/language/rights assertion, Google OAuth, YouTube or network access.
Used only on three preexisting ORIGINAL silent authored HD videos on disposable
standard runners; all generated WAV/MP4 bytes vanish even on failure.
"""
from __future__ import annotations

from array import array
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import math
import shutil
import subprocess
import sys

from .agent_org import WorkflowError
from .phase3_visual_signal_audit import EPISODES
from .phase3_full_ephemeral_audio_batch import _probe_exact_muxed
from .phase3_voice_subtitle_handoff import inspect_external_voice_wav

MAX_ORIGINAL_BYTES = 150_000_000
MAX_PROBE_CHARS = 20_000
MIN_SCRATCH_FREE = 600_000_000


def _probe_exact_silent_original(path: Path, episode: str) -> None:
    if episode not in EPISODES:
        raise WorkflowError("Unknown original authored episode")
    if (not isinstance(path, Path) or path.is_symlink()
            or not path.is_file() or path.suffix.lower() != ".mp4"
            or not 2048 <= path.stat().st_size <= MAX_ORIGINAL_BYTES):
        raise WorkflowError("Expected actual bounded ordinary original MP4")
    try:
        process = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "stream=codec_type,codec_name,width,height,nb_frames,avg_frame_rate:"
             "format=duration", "-of", "json", str(path)],
            stdin=subprocess.DEVNULL, capture_output=True, text=True,
            check=True, timeout=25,
        )
        if len(process.stdout) > MAX_PROBE_CHARS:
            raise WorkflowError("Original MP4 probe oversized")
        data = json.loads(process.stdout)
        streams = data["streams"]
        if len(streams) != 1 or streams[0].get("codec_type") != "video":
            raise WorkflowError("Original MP4 must have exactly one silent video stream")
        expected_duration, w, h, fps, frames = EPISODES[episode]
        v = streams[0]
        parts = v["avg_frame_rate"].split("/")
        rate = float(parts[0])/float(parts[1]) if len(parts)==2 else float(parts[0])
        measured = float(data["format"]["duration"])
        if (v.get("codec_name") != "h264"
                or (int(v["width"]), int(v["height"])) != (w,h)
                or int(v["nb_frames"]) != frames
                or not math.isfinite(rate) or abs(rate-fps) > .015
                or not math.isfinite(measured)
                or abs(measured-expected_duration) > .12):
            raise WorkflowError("Original silent HD episode is not exact duration/format")
    except (OSError, TypeError, KeyError, ValueError, ZeroDivisionError,
            subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise WorkflowError("Original silent HD episode probe failed") from exc


def _run_checked(args: list[str], *, timeout: int) -> bytes:
    try:
        result = subprocess.run(args, stdin=subprocess.DEVNULL,
                                capture_output=True, check=False, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise WorkflowError("Bounded local media subprocess failed") from exc
    if result.returncode != 0:
        raise WorkflowError("Local FFmpeg media processing failed")
    return result.stdout


def _probe_real_audio_energy(mp4: Path) -> float:
    """Decode limited AAC samples; valid MP4 metadata alone can hide silence."""
    raw = _run_checked([
        "ffmpeg", "-nostdin", "-v", "error", "-xerror",
        "-ss", "0.10", "-i", str(mp4), "-map", "0:a:0", "-vn",
        "-t", "0.50", "-c:a", "pcm_s16le", "-ac", "1",
        "-ar", "16000", "-f", "s16le", "pipe:1",
    ], timeout=30)
    if not 8000 <= len(raw) <= 20000 or len(raw) % 2:
        raise WorkflowError("Real decoded AAC audio sample absent or malformed")
    values = array("h")
    values.frombytes(raw)
    if sys.byteorder != "little":
        values.byteswap()
    rms = math.sqrt(sum(v*v for v in values)/len(values))/32768.0
    if not .002 < rms < .7:
        raise WorkflowError("Decoded real AAC audio energy insufficient")
    return round(rms, 5)


def run_full_synthetic_tone_smoke(*, episode_id: str,
                                  silent_mp4: Path,
                                  scratch_dir: Path) -> dict:
    """Full duration actual FFmpeg smoke; self-deleting untrusted test material.

    This bypasses intentionally the real-voice admission gate ONLY for an
    explicitly named SYNTHETIC TONE smoke, never a production media adapter.
    Must not be used to create retained/video-uploadable content.
    """
    if (episode_id not in EPISODES
            or not isinstance(scratch_dir, Path) or scratch_dir.is_symlink()
            or not scratch_dir.is_dir()
            or shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None):
        raise WorkflowError("Approved existing episode, scratch and FFmpeg required")
    if (scratch_dir.resolve() == silent_mp4.resolve()
            or shutil.disk_usage(scratch_dir).free < MIN_SCRATCH_FREE):
        raise WorkflowError("Insufficient or invalid scratch space")
    _probe_exact_silent_original(silent_mp4, episode_id)
    expected_seconds, w, h, fps, frames = EPISODES[episode_id]
    frequency = {
        "csv_tutorial_short_en": 330,
        "csv_tutorial_short_hi": 220,
        "csv_tutorial_long_hi": 275,
    }[episode_id]
    with TemporaryDirectory(prefix="flowminute-synthetic-tone-only-", dir=scratch_dir) as temp:
        folder = Path(temp)
        wav = folder/"THIS_IS_NOT_SPEECH.wav"
        output = folder/"DO_NOT_PUBLISH.mp4"
        _run_checked([
            "ffmpeg", "-nostdin", "-v", "error", "-xerror", "-n",
            "-f", "lavfi",
            "-i", f"sine=frequency={frequency}:sample_rate=16000:duration={expected_seconds}",
            "-ac", "1", "-c:a", "pcm_s16le", str(wav),
        ], timeout=50)
        narrator = {
            "csv_tutorial_short_en": ("narrator_english_b", "en"),
            "csv_tutorial_short_hi": ("narrator_hindi_a", "hi"),
            "csv_tutorial_long_hi": ("narrator_hindi_long_c", "hi"),
        }[episode_id]
        audio = inspect_external_voice_wav(
            wav, episode_id=episode_id, expected_seconds=expected_seconds,
            declared_narrator_id=narrator[0], declared_language=narrator[1],
        )
        if (audio.get("real_speech_verified") is not False
                or audio.get("license_rights_verified") is not False
                or abs(audio["duration_seconds"]-expected_seconds)>.01):
            raise WorkflowError("Synthetic audio inspector must never attest to speech")
        _run_checked([
            "ffmpeg", "-nostdin", "-v", "error", "-xerror", "-n",
            "-i", str(silent_mp4), "-i", str(wav),
            "-map", "0:v:0", "-map", "1:a:0", "-sn", "-dn",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
            "-ar", "48000", "-ac", "2",
            "-t", str(expected_seconds), "-movflags", "+faststart",
            "-metadata", "comment=SYNTHETIC_TONE_ONLY_NEVER_PUBLISH",
            str(output),
        ], timeout=110 if expected_seconds<=60 else 300)
        quality = _probe_exact_muxed(output, episode_id)
        if quality["video_frames"] != frames or quality["video_width"] != w or quality["video_height"] != h:
            raise WorkflowError("Output changed actual original frame plan")
        _run_checked([
            "ffmpeg", "-nostdin", "-v", "error", "-xerror",
            "-i", str(output), "-f", "null", "-",
        ], timeout=130 if expected_seconds<=60 else 360)
        rms = _probe_real_audio_energy(output)
        hsh=sha256()
        with output.open("rb") as stream:
            for piece in iter(lambda:stream.read(1048576),b""):
                hsh.update(piece)
        # This metadata is an UNSIGNED local engineering observation only.
        summary = {
            "status": "REAL_FULL_DURATION_SYNTHETIC_TONE_AAC_QA_NOT_A_VOICE",
            "episode_id": episode_id,
            "source_original_is_silent": True,
            "synthetic_tone_hz": frequency,
            "output_h264_aac_fully_decoded": True,
            "output_sha256": hsh.hexdigest(),
            "output_size_bytes": output.stat().st_size,
            "measured_audio_rms": rms,
            **quality,
            "contains_genuine_natural_speech": False,
            "narrator_identity_or_language_verified": False,
            "caption_alignment_verified": False,
            "factual_creative_or_legal_rights_verified": False,
            "commercial_release_ready": False,
            "ready_for_mux_or_upload": False,
            "youtube_upload_or_scheduling_authorized": False,
            "publishing_authorized": False,
            "new_service_or_provider_used": False,
            "network_calls": 0,
        }
    # At return TemporaryDirectory has deleted WAV, output MP4 and staging dir.
    summary["temp_media_removed_before_return"] = True
    return summary


def main() -> None:
    import argparse
    parser=argparse.ArgumentParser(description="Full original HD synthetic tone QA; not real speech")
    parser.add_argument("--episode", choices=sorted(EPISODES), required=True)
    parser.add_argument("--silent-mp4", type=Path, required=True)
    parser.add_argument("--scratch-dir", type=Path, required=True)
    args=parser.parse_args()
    report=run_full_synthetic_tone_smoke(
        episode_id=args.episode,silent_mp4=args.silent_mp4,
        scratch_dir=args.scratch_dir,
    )
    if (report["publishing_authorized"] or not report["temp_media_removed_before_return"]):
        raise WorkflowError("Unsafe synthetic tone QA status")
    print("REAL_FULL_DURATION_SYNTHETIC_TONE_AUDIO_QA_PASSED "
          +json.dumps(report,sort_keys=True))


if __name__ == "__main__":
    main()
