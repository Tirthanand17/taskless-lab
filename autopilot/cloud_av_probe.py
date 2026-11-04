"""FlowMinute Branch 2 cloud-only *technical feasibility probe*, NEVER a video producer.

Runs only on a disposable GitHub public hosted runner. Generates actual Kokoro
speech for three DIFFERENT narration prompts, renders three disposable 4-second
H.264/AAC technical clips, full-decodes, and reports SHA/duration/time/bytes.
These clips are not real educational videos and MUST NOT be uploaded anywhere.

Kokoro weights must be downloaded from one fixed upstream GitHub release and
verified byte-for-byte against official release-asset SHA256 before model load.
No connection to YouTube, Nirala, paid APIs, GitHub artifacts or private storage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Any

RELEASE_TAG = "model-files-v1.1"
UPSTREAM_REPO = "thewh1teagle/kokoro-onnx"
MODEL_NAME = "kokoro-v1.0.int8.onnx"
MODEL_SHA256 = "ae315a79b623f244700e4afb9246c46a26066782e049ba174bf3ba433970ee9c"
VOICES_NAME = "voices-v1.0.bin"
VOICES_SHA256 = "bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d"
MODEL_MAX_BYTES = 125_000_000
VOICES_MAX_BYTES = 35_000_000
FRAME_RATE = 24
CLIP_SECONDS = 4.0
SLOTS = (
    ("short_am", "short", "af_heart",
     "Sample one. Keep a backup before changing your spreadsheet settings. Compare the original data and the imported results."),
    ("long", "long", "am_michael",
     "Sample two. Start with a small test file and inspect each step. Compare the source with the result, and confirm that each number is correct."),
    ("short_pm", "short", "bf_emma",
     "Sample three. A secure website connection does not establish that its owner is trustworthy. Confirm the destination yourself."),
)


class ProbeError(ValueError):
    """A missing checksum, unsupported format or defective clip stops the test."""


def sha256_stream(path: Path, *, max_bytes: int) -> tuple[str, int]:
    """Hash bytes in bounded memory and fail if source exceeds its cap."""
    total = 0
    h = hashlib.sha256()
    with path.open("rb") as reader:
        for chunk in iter(lambda: reader.read(1 << 20), b""):
            total += len(chunk)
            if total > max_bytes:
                raise ProbeError("Model asset exceeds pinned size cap")
            h.update(chunk)
    return h.hexdigest(), total


def verify_pinned_assets(model: Path, voices: Path) -> dict[str, Any]:
    if model.name != MODEL_NAME or voices.name != VOICES_NAME:
        raise ProbeError("Unexpected model or voice filename")
    if model.is_symlink() or voices.is_symlink():
        raise ProbeError("Weights must be regular non-symlink files")
    try:
        model_sha, model_size = sha256_stream(model, max_bytes=MODEL_MAX_BYTES)
        voice_sha, voice_size = sha256_stream(voices, max_bytes=VOICES_MAX_BYTES)
    except OSError as exc:
        raise ProbeError("Required upstream model/voice file absent") from exc
    if model_sha != MODEL_SHA256 or voice_sha != VOICES_SHA256:
        raise ProbeError("Upstream Kokoro release SHA256 mismatch")
    return {
        "upstream": UPSTREAM_REPO,
        "release_tag": RELEASE_TAG,
        "model_sha256": model_sha,
        "model_bytes": model_size,
        "voice_pack_sha256": voice_sha,
        "voice_pack_bytes": voice_size,
        "asset_integrity_passed": True,
    }


def execute(command: list[str], *, timeout_s: int = 120) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(command, check=True, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True, timeout=timeout_s)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
            FileNotFoundError) as exc:
        raise ProbeError("Media tool failed: " + type(exc).__name__) from exc


def check_media(path: Path, kind: str) -> dict:
    if kind not in ("long", "short") or not path.is_file():
        raise ProbeError("Unsupported format or missing clip")
    meta = json.loads(execute([
        "ffprobe", "-v", "error", "-show_format", "-show_streams",
        "-of", "json", str(path),
    ]).stdout)
    streams = meta.get("streams", [])
    video = [x for x in streams if x.get("codec_type") == "video"]
    audio = [x for x in streams if x.get("codec_type") == "audio"]
    if len(video) != 1 or len(audio) != 1:
        raise ProbeError("Missing or additional audio/video streams")
    expected = (1920, 1080) if kind == "long" else (1080, 1920)
    v, a = video[0], audio[0]
    if (v.get("width"), v.get("height")) != expected:
        raise ProbeError("Incorrect long/short dimensions")
    if v.get("codec_name") != "h264" or a.get("codec_name") != "aac":
        raise ProbeError("Only H264/AAC technical samples accepted")
    if v.get("pix_fmt") != "yuv420p":
        raise ProbeError("Invalid chroma pixel format")
    duration = float(meta.get("format", {}).get("duration", 0))
    if not 3.3 <= duration <= 4.2:
        raise ProbeError("Truncated or overly long sample")
    execute(["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error",
             "-xerror", "-i", str(path), "-f", "null", "-"], timeout_s=90)
    digest, size = sha256_stream(path, max_bytes=30_000_000)
    return {
        "sha256": digest,
        "bytes": size,
        "duration_seconds": round(duration, 3),
        "width": expected[0],
        "height": expected[1],
        "video_codec": "h264",
        "audio_codec": "aac",
        "full_decode_passed": True,
        "viewer_or_rights_review_performed": False,
        "video_ready_to_publish": False,
    }


def render_probe(wav: Path, output: Path, kind: str, slot: str) -> None:
    if kind not in ("short", "long") or slot not in {s[0] for s in SLOTS}:
        raise ProbeError("Invalid probe clip slot")
    dims = (1920, 1080) if kind == "long" else (1080, 1920)
    w, h = dims
    label = {"short_am": "SHORT A", "long": "LONG", "short_pm": "SHORT B"}[slot]
    fontsize = 68 if kind == "long" else 74
    vf = (
        "drawgrid=w=120:h=120:t=2:c=white@0.08,"
        "drawbox=x=80:y=140:w=iw-160:h=380:color=0x1B3C67@0.9:t=fill,"
        f"drawtext=text='FLOWMINUTE CLOUD TEST':fontcolor=white:fontsize={fontsize}:"
        "x=(w-text_w)/2:y=195,"
        f"drawtext=text='{label}  /  NO PUBLISH':fontcolor=0xBEE3F8:"
        "fontsize=47:x=(w-text_w)/2:y=330,"
        "fade=t=in:st=0:d=0.4,fade=t=out:st=3.3:d=0.7"
    )
    execute([
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", f"color=c=0x101A2D:s={w}x{h}:r={FRAME_RATE}:d={CLIP_SECONDS}",
        "-i", str(wav), "-map", "0:v:0", "-map", "1:a:0",
        "-vf", vf,
        "-af", "loudnorm=I=-16:LRA=9:TP=-2.0",
        "-t", str(CLIP_SECONDS), "-r", str(FRAME_RATE),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "112k",
        "-threads", "2", "-movflags", "+faststart",
        "-y", str(output),
    ], timeout_s=180)


def benchmark(model: Path, voices: Path, out_dir: Path) -> dict:
    """Run inference and actual full video decode; delete outputs in workflow."""
    if out_dir.is_symlink():
        raise ProbeError("Output directory cannot be a symlink")
    if out_dir.exists() and any(out_dir.iterdir()):
        raise ProbeError("Refuse overwriting an existing output directory")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise ProbeError("GitHub runner FFmpeg/ffprobe not installed")
    assets = verify_pinned_assets(model, voices)
    from kokoro_onnx import Kokoro  # installed only in the optional cloud benchmark
    import soundfile as sf
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    voice_model = Kokoro(str(model), str(voices))
    results = []
    try:
        for slot, kind, voice_name, narration in SLOTS:
            t0 = time.monotonic()
            samples, sample_rate = voice_model.create(narration, voice=voice_name,
                                                       speed=1.12, lang="en-us")
            if sample_rate < 16000 or len(samples) < sample_rate * 3:
                raise ProbeError("Synthesized speech is missing/too short")
            wav = out_dir / f"{slot}.wav"
            sf.write(str(wav), samples, sample_rate, subtype="PCM_16")
            tts_elapsed = time.monotonic() - t0
            target = out_dir / f"{slot}.mp4"
            render_probe(wav, target, kind, slot)
            qa = check_media(target, kind)
            results.append({
                "slot": slot, "kind": kind, "voice": voice_name,
                "speech_generated": True, "speech_sample_rate": sample_rate,
                "narration_characters": len(narration),
                "tts_elapsed_seconds": round(tts_elapsed, 2),
                "total_elapsed_seconds": round(time.monotonic() - t0, 2),
                **qa,
            })
    finally:
        close = getattr(getattr(voice_model, "voices", None), "close", None)
        if callable(close):
            close()
    if len(results) != 3 or len({x["sha256"] for x in results}) != 3:
        raise ProbeError("All three slot clips must be distinct and fully decoded")
    return {
        "schema_version": 1,
        "probe_kind": "REAL_CLOUD_KOKORO_TTS_AND_FFMPEG_TECHNICAL_SMOKE_ONLY",
        "runner": "github-hosted-ubuntu",
        "tested_media_sourced_from_user_laptop": False,
        "original_upstream_license": "Apache-2.0; owner must verify notices and dependencies",
        **assets,
        "total_probe_elapsed_seconds": round(time.monotonic() - started, 2),
        "test_slots": results,
        "real_short_or_long_video_production_proven": False,
        "episode_scripts_fact_verified": False,
        "full_narration_quality_human_reviewed": False,
        "cloud_storage_connected": False,
        "youtube_upload_enabled": False,
        "youtube_schedule_enabled": False,
        "billed_model_calls": 0,
        "publication_authorized": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Real cloud TTS/FFmpeg smoke; outputs are never released")
    ap.add_argument("--model", type=Path, required=True)
    ap.add_argument("--voices", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    report = benchmark(args.model, args.voices, args.output_dir)
    p = args.output_dir / "technical_probe_report.json"
    p.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
    print(json.dumps({
        "status": report["probe_kind"],
        "slots": len(report["test_slots"]),
        "tts_samples": [x["tts_elapsed_seconds"] for x in report["test_slots"]],
        "full_media_decode": [x["full_decode_passed"] for x in report["test_slots"]],
        "model_sha_verified": report["asset_integrity_passed"],
        "total_seconds": report["total_probe_elapsed_seconds"],
        "youtube_upload_enabled": False,
    }))


if __name__ == "__main__":
    main()
