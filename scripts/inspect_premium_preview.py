"""Inspect FlowMinute ten-second technical previews without publishing.

Uses ffprobe / ffmpeg for actual decode and sampled motion checks. Source is
operator-identified; still-image frame difference alone never proves true 3D.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from autopilot.premium_preview_qa import MediaFacts, MotionFacts, validate_preview


def run(command: list[str], *, timeout: int = 60) -> bytes:
    return subprocess.run(command, capture_output=True, check=True, timeout=timeout).stdout


def inspect(video: Path, source: Path) -> dict:
    if not video.is_file() or video.suffix.lower() != ".mp4" or video.stat().st_size > 75_000_000:
        raise ValueError("Missing or oversized MP4")
    if not source.is_file() or source.suffix.lower() != ".py":
        raise ValueError("A Python renderer source is required")
    meta = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                           "-of", "json", str(video)]))
    video_stream = next((x for x in meta["streams"] if x.get("codec_type") == "video"), None)
    audio_stream = next((x for x in meta["streams"] if x.get("codec_type") == "audio"), None)
    if not video_stream:
        raise ValueError("Video stream absent")
    fps_numerator, fps_denominator = map(int, video_stream["r_frame_rate"].split("/"))
    fps = fps_numerator / fps_denominator
    run(["ffmpeg", "-v", "error", "-i", str(video), "-f", "null", "-"])
    frames_blob = run(["ffmpeg", "-v", "error", "-i", str(video),
                       "-vf", "fps=1,scale=64:36:flags=fast_bilinear,format=gray",
                       "-an", "-f", "rawvideo", "-pix_fmt", "gray", "-"])
    frame_size = 64 * 36
    frames = [frames_blob[offset:offset + frame_size]
              for offset in range(0, len(frames_blob), frame_size)]
    if len(frames) < 10 or any(len(x) != frame_size for x in frames):
        raise ValueError("Incomplete sampled video frames")
    samples = [frames[i] for i in (0, 3, 6, 9)]
    motion = tuple(sum(abs(a - b) for a, b in zip(x, y)) / frame_size
                   for x, y in zip(samples, samples[1:]))
    media = MediaFacts(
        duration_seconds=float(meta["format"]["duration"]),
        width=int(video_stream["width"]), height=int(video_stream["height"]),
        fps=fps, frames=int(video_stream["nb_frames"]),
        video_codec=video_stream["codec_name"],
        audio_codec=audio_stream["codec_name"] if audio_stream else "none",
        fully_decoded=True,
    )
    record = validate_preview(media, MotionFacts(motion, "real_3d_geometry", str(source)))
    record.update({
        "media_sha256": hashlib.sha256(video.read_bytes()).hexdigest(),
        "renderer_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "frame_size": [media.width, media.height],
        "fps": fps, "frames": media.frames,
        "audio_codec": media.audio_codec,
        "sampled_mae": list(motion),
        "motion_provenance": "Renderer path supplied by operator; video pixels do not prove real 3D",
        "full_ffmpeg_decode": "PASS",
        "video_file_bytes": video.stat().st_size,
    })
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--renderer-source", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = inspect(args.video, args.renderer_source)
    if args.output:
        if not args.output.parent.is_dir():
            raise ValueError("Output parent must exist")
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
