"""V3 generated-media smoke: real FFmpeg decode -> local signal -> candidate plan.

No external input paths, URLs, production ingest, credentials, or release.
Frame difference is a cheap motion proxy, not optical flow or semantic AI.
"""
from __future__ import annotations

import array
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from scripts.branch3_v3_multimodal_candidates import (
    CHANNEL, INPUT_STATE, baseline, propose,
)
from scripts.branch3_v2_p5_synthetic_moment_proposals import _probe_closed

WIDTH, HEIGHT, FPS = 160, 90, 2
FRAME_BYTES = WIDTH * HEIGHT
RATE, SECONDS = 8000, 80
N = SECONDS * FPS
AUDIO_HOP = RATE // FPS


def command(args, output_limit=0):
    result = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True,
                            timeout=90, check=True)
    if len(result.stdout) > output_limit:
        raise ValueError("unexpected output size")
    return result.stdout


def fixture(folder):
    """Produce original black/gray synthetic scene and tone, no source input."""
    raw = folder / "original.gray"
    pcm = folder / "original.pcm"
    source = folder / "generated.mp4"
    with raw.open("wb") as f:
        for i in range(N):
            level = 24 if i < 140 else 160
            frame = bytearray([level]) * FRAME_BYTES
            x = 10 if i < 110 else 90
            if i < 140:
                for y in range(20, 60):
                    frame[y * WIDTH + x:y * WIDTH + x + 40] = bytes([220]) * 40
            f.write(frame)
    with pcm.open("wb") as f:
        for i in range(N):
            amplitude = 10000 if i == 30 else 0
            chunk = array.array("h", (round(amplitude * math.sin(2 * math.pi * 440 * k / RATE))
                                      for k in range(AUDIO_HOP)))
            if sys.byteorder != "little":
                chunk.byteswap()
            f.write(chunk.tobytes())
    command(["ffmpeg", "-hide_banner", "-nostdin", "-v", "error",
             "-f", "rawvideo", "-pixel_format", "gray", "-video_size", f"{WIDTH}x{HEIGHT}",
             "-framerate", str(FPS), "-i", str(raw), "-f", "s16le",
             "-ar", str(RATE), "-ac", "1", "-i", str(pcm), "-t", str(SECONDS),
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-threads:v", "1",
             "-c:a", "aac", str(source)])
    return source


def measure_generated(source):
    """Internal generated fixture path only. Not a public ingest interface."""
    prefix = ["ffmpeg", "-hide_banner", "-nostdin", "-v", "error",
              "-protocol_whitelist", "file", "-i", str(source), "-t", str(SECONDS)]
    raw = command(prefix + ["-map", "0:v:0", "-an", "-vf",
                            f"fps={FPS},scale={WIDTH}:{HEIGHT},format=gray",
                            "-f", "rawvideo", "pipe:1"], N * FRAME_BYTES)
    audio = command(prefix + ["-map", "0:a:0", "-vn", "-ac", "1",
                              "-ar", str(RATE), "-f", "s16le", "pipe:1"],
                    RATE * SECONDS * 2)
    if len(raw) != N * FRAME_BYTES or len(audio) != RATE * SECONDS * 2:
        raise ValueError("generated fixture timebase mismatch")
    pcm = array.array("h")
    pcm.frombytes(audio)
    if sys.byteorder != "little":
        pcm.byteswap()
    rms = [round(math.sqrt(sum(v*v for v in pcm[i:i+AUDIO_HOP]) / AUDIO_HOP))
           for i in range(0, len(pcm), AUDIO_HOP)]
    motion, cuts = [0], []
    for i in range(1, N):
        prev, cur = raw[(i-1)*FRAME_BYTES:i*FRAME_BYTES], raw[i*FRAME_BYTES:(i+1)*FRAME_BYTES]
        delta = sum(abs(a-b) for a, b in zip(prev, cur)) / FRAME_BYTES
        if delta >= 45:
            cuts.append(i * 500)
            motion.append(0)
        else:
            motion.append(round(delta * 10000 / 255))
    return {"schema_version": 1, "channel_id": CHANNEL, "state": INPUT_STATE,
            "profile": "gaming", "duration_ms": SECONDS * 1000, "step_ms": 500,
            "audio_rms": rms, "motion": motion, "scene_cuts_ms": cuts,
            "semantic_events_ms": None, "editor_marks_ms": None}


def smoke():
    _probe_closed()
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("FFmpeg and FFprobe are required")
    with tempfile.TemporaryDirectory(prefix="clivox-v3-generated-") as temp:
        source = fixture(Path(temp))
        doc = measure_generated(source)
        old, new = baseline(doc), propose(doc)
        assert old is not None
        if not (old["candidate_count"] == 1 and len(new["candidates"]) == 2
                and new["event_counts"]["audio"] >= 1
                and new["event_counts"]["motion"] == 1
                and doc["scene_cuts_ms"] == [70000]
                and any(c["anchor_ms"] == 55000 for c in new["candidates"])
                and new["youtube_upload_authorized"] is False):
            raise ValueError("generated media regression")
        _probe_closed()
        return {"generated_fixture_only": True, "decoded_seconds": SECONDS,
                "baseline_candidates": old["candidate_count"],
                "multimodal_candidates": len(new["candidates"]),
                "scene_cuts_ms": doc["scene_cuts_ms"],
                "motion_method": "sampled grayscale frame difference",
                "asr_performed": False, "production_ready": False,
                "youtube_upload_authorized": False}


if __name__ == "__main__":
    print(json.dumps(smoke(), sort_keys=True))
