"""CLIVOX V2 P5: source-free acoustic/scene candidate *engineering fixture*.

This is NOT a creator-source processor or a viral predictor. Before reading
anything, validate real P4/A3 CLOSED rights and storage controls. Only accept
a tiny, locally generated synthetic MP4 already validated by P4. Extract
short-lived PCM and small luma frames to find bounded event windows. Never
fetch from a URL, infer a voice/quote, contact anyone, write media, or publish.
"""
from __future__ import annotations

import argparse
from array import array
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys

from scripts.branch3_v2_p4_synthetic_handoff_preflight import (
    MAX_FIXTURE_BYTES, P4Denied, SAFE_NAME, SHA256,
    actual_closed_boundary, inspect_synthetic_fixture,
)

CHANNEL = "UCfPEvy0SefE_5nNlYlY_CyQ"
FRAME_WIDTH = 16
FRAME_HEIGHT = 9
FRAME_RATE = 2
FRAME_BYTES = FRAME_WIDTH * FRAME_HEIGHT
SAMPLE_RATE = 8000
HOP_MS = 500
AUDIO_SAMPLES_PER_HOP = SAMPLE_RATE * HOP_MS // 1000
MAX_SECONDS = 10
MAX_FRAMES = (MAX_SECONDS + 1) * FRAME_RATE
MAX_AUDIO_BYTES = (MAX_SECONDS + 1) * SAMPLE_RATE * 2
MAX_CANDIDATES = 8
MAX_PROPOSAL_MS = 10_000


class P5Denied(ValueError):
    """Proposals cannot be created outside synthetic, closed-rights mode."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise P5Denied("CLIVOX_V2_P5_DENIED_" + code)


def _probe_closed() -> dict:
    """No creator license/vault; a passing code test must not simulate one."""
    try:
        upstream = actual_closed_boundary()
    except (P4Denied, ValueError, KeyError, TypeError):
        raise P5Denied("CLIVOX_V2_P5_DENIED_A3_P4_POLICY") from None
    require(upstream["p4_milestone_complete"] is False
            and upstream["creator_media_fetch_enabled"] is False
            and upstream["creator_media_write_enabled"] is False
            and upstream["youtube_upload_enabled"] is False
            and upstream["youtube_publish_enabled"] is False
            and upstream["rights_grants_verified"] == 0,
            "P4_MUST_BE_CLOSED")
    return upstream


def safe_process(cmd: list[str], *, runner=subprocess.run,
                 max_output_bytes: int) -> bytes:
    """Read only bounded binary output of a fixed FFmpeg invocation."""
    require(type(cmd) is list and len(cmd) <= 30
            and cmd[0] == "ffmpeg"
            and "--" not in cmd, "FIXED_FFMPEG")
    try:
        result = runner(cmd, capture_output=True, timeout=25, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise P5Denied("CLIVOX_V2_P5_DENIED_FFMPEG_UNAVAILABLE") from None
    require(result.returncode == 0 and type(result.stdout) is bytes
            and 0 < len(result.stdout) <= max_output_bytes,
            "INVALID_FFMPEG_OUTPUT")
    return result.stdout


def audio_rms_windows(pcm: bytes) -> list[int]:
    """Window-local acoustic energy only; NOT VAD/ASR or emotion inference."""
    require(type(pcm) is bytes and len(pcm) % 2 == 0
            and 2 * AUDIO_SAMPLES_PER_HOP <= len(pcm) <= MAX_AUDIO_BYTES,
            "PCM_SIZE")
    samples = array("h")
    samples.frombytes(pcm)
    if sys.byteorder != "little":
        samples.byteswap()
    rms = []
    for start in range(0, len(samples), AUDIO_SAMPLES_PER_HOP):
        window = samples[start:start + AUDIO_SAMPLES_PER_HOP]
        if len(window) < AUDIO_SAMPLES_PER_HOP // 2:
            break
        rms.append(int((sum(int(x) * int(x) for x in window)
                        / len(window)) ** .5))
    require(1 <= len(rms) <= 2 * (MAX_SECONDS + 1), "PCM_WINDOW_COUNT")
    return rms


def detect_scene_events(raw_gray: bytes) -> list[int]:
    """Pixel change proposals; no person recognition or copyrighted frames saved."""
    require(type(raw_gray) is bytes
            and len(raw_gray) % FRAME_BYTES == 0
            and 2 <= len(raw_gray) // FRAME_BYTES <= MAX_FRAMES,
            "GRAY_FRAME_COUNT")
    frames = [raw_gray[i:i + FRAME_BYTES]
              for i in range(0, len(raw_gray), FRAME_BYTES)]
    events = []
    for index in range(1, len(frames)):
        delta = sum(abs(a - b) for a, b in
                    zip(frames[index - 1], frames[index])) // FRAME_BYTES
        if delta >= 45:
            events.append(index * 1000 // FRAME_RATE)
    return events


def event_windows(*, acoustic_rms: list[int], scene_events_ms: list[int],
                  duration_ms: int) -> list[dict]:
    """Candidate timecodes, no purported popularity, caption or speech text."""
    require(type(duration_ms) is int and 1000 <= duration_ms <= MAX_PROPOSAL_MS,
            "DURATION")
    require(type(acoustic_rms) is list
            and 2 <= len(acoustic_rms) <= 22
            and all(type(x) is int and 0 <= x <= 32768 for x in acoustic_rms),
            "INVALID_ACOUSTIC_OBSERVATIONS")
    require(type(scene_events_ms) is list and len(scene_events_ms) <= 22
            and all(type(x) is int and 0 <= x < duration_ms
                    for x in scene_events_ms)
            and scene_events_ms == sorted(set(scene_events_ms)),
            "INVALID_SCENE_EVENTS")
    median = statistics.median(acoustic_rms)
    # Only source-independent, local relative changes, not an emotion or
    # viral-probability score. Constant loud speech/music does not trigger.
    acoustic_events = [
        i * HOP_MS for i, rms in enumerate(acoustic_rms)
        if i > 0 and i * HOP_MS < duration_ms
        and rms >= 600 and rms > median * 1.8
        and rms > acoustic_rms[i - 1] * 1.7
    ]
    observations = [(t, "ACOUSTIC_RMS_RISE") for t in acoustic_events]
    observations += [(t, "VIDEO_LUMA_CUT") for t in scene_events_ms]
    observations.sort(key=lambda x: (x[0], x[1]))
    windows: list[dict] = []
    for when, kind in observations:
        start, end = max(0, when - 800), min(duration_ms, when + 1200)
        if end - start < 300:
            continue
        if windows and start <= windows[-1]["end_ms"]:
            windows[-1]["end_ms"] = max(windows[-1]["end_ms"], end)
            windows[-1]["evidence_kinds"] = sorted(
                set(windows[-1]["evidence_kinds"]) | {kind}
            )
        else:
            windows.append({"start_ms": start, "end_ms": end,
                            "evidence_kinds": [kind]})
    # Do not report truncated (partial) windows if > MAX_CANDIDATES:
    # hold for human editor rather than falsely asserting top-K precision.
    windows = windows[:MAX_CANDIDATES]
    for i, window in enumerate(windows, start=1):
        window["proposal_id"] = f"synthetic_{i:02d}"
        window["machine_transcript"] = None
        window["transcript_verified"] = False
        window["creator_rights_verified"] = False
        window["ready_for_editorial_use"] = False
        window["human_context_review_required"] = True
    return windows


def scan_synthetic_moments(*, scratch: Path, basename: str,
                           expected_sha256: str, expected_bytes: int,
                           runner=subprocess.run) -> dict:
    """Actual signal extraction, limited to verified synthetic test fixture."""
    _probe_closed()  # FIRST; cannot process actual source in public CI.
    require(isinstance(scratch, Path) and scratch.is_dir()
            and not scratch.is_symlink()
            and type(basename) is str and SAFE_NAME.fullmatch(basename) is not None,
            "SYNTHETIC_FILE_ARGUMENTS")
    require(type(expected_sha256) is str
            and SHA256.fullmatch(expected_sha256) is not None
            and type(expected_bytes) is int
            and 32 <= expected_bytes <= MAX_FIXTURE_BYTES,
            "EXPECTED_SYNTHETIC_FILE_DIGEST")
    try:
        p4 = inspect_synthetic_fixture(
            scratch=scratch, basename=basename,
            expected_sha256=expected_sha256, expected_bytes=expected_bytes,
            runner=runner,
        )
    except (P4Denied, OSError, ValueError, KeyError, TypeError):
        raise P5Denied("CLIVOX_V2_P5_DENIED_P4_FIXTURE") from None
    require(p4["synthetic_fixture_decoded"] is True
            and p4["rights_grants_verified"] == 0
            and p4["youtube_upload_enabled"] is False, "P4_INTEGRITY")
    file = scratch.resolve(strict=True) / basename
    command = ["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error",
               "-protocol_whitelist", "file", "-i", str(file)]
    pcm = safe_process(command + [
        "-map", "0:a:0", "-vn", "-ac", "1", "-ar", str(SAMPLE_RATE),
        "-f", "s16le", "pipe:1",
    ], runner=runner, max_output_bytes=MAX_AUDIO_BYTES)
    gray = safe_process(command + [
        "-map", "0:v:0", "-an", "-vf",
        f"fps={FRAME_RATE},scale={FRAME_WIDTH}:{FRAME_HEIGHT},format=gray",
        "-f", "rawvideo", "pipe:1",
    ], runner=runner, max_output_bytes=MAX_FRAMES * FRAME_BYTES)
    # Check integrity a second time after the independent decoders ran.
    hasher = hashlib.sha256()
    try:
        with file.open("rb") as stream:
            while chunk := stream.read(65536):
                hasher.update(chunk)
    except OSError:
        raise P5Denied("CLIVOX_V2_P5_DENIED_SOURCE_CHANGED") from None
    require(hasher.hexdigest() == expected_sha256
            and file.stat().st_size == expected_bytes,
            "SOURCE_CHANGED")
    duration_ms = min(MAX_PROPOSAL_MS,
                      len(pcm) // 2 * 1000 // SAMPLE_RATE)
    require(1000 <= duration_ms <= 10000
            and 1 <= len(gray) // FRAME_BYTES <= MAX_FRAMES,
            "TIMEBASE")
    windows = event_windows(
        acoustic_rms=audio_rms_windows(pcm),
        scene_events_ms=detect_scene_events(gray),
        duration_ms=duration_ms,
    )
    _probe_closed()  # Re-check after extraction, never release on changed state.
    return {
        "stage": "CLIVOX_V2_P5_SYNTHETIC_SIGNAL_CANDIDATES_ONLY",
        "channel_id": CHANNEL,
        "synthetic_original_fixture_only": True,
        "actual_creator_source_count": 0,
        "real_creator_license_count": 0,
        "third_party_video_downloads": 0,
        "outreach_messages_sent": 0,
        "youtube_api_calls": 0,
        "youtube_uploads": 0,
        "p5_real_licensed_pipeline_complete": False,
        "p5_real_editor_label_evaluation_complete": False,
        "ASR_or_VAD_performed": False,
        "speech_or_quotes_inferred": False,
        "youtube_replay_heatmap_inferred": False,
        "estimated_viral_performance": None,
        "human_source_context_required": True,
        "synthetic_technical_candidate_count": len(windows),
        "synthetic_candidate_windows": windows,
        "status": "PRIVATE_LICENSING_REQUIRED_NO_REAL_CLIP_RELEASE",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("closed", "synthetic"), default="closed")
    parser.add_argument("--scratch", type=Path)
    parser.add_argument("--fixture-file")
    parser.add_argument("--sha256")
    parser.add_argument("--bytes", type=int)
    args = parser.parse_args()
    try:
        closed = _probe_closed()
        if args.mode == "closed":
            require(all(x is None for x in (
                args.scratch, args.fixture_file, args.sha256, args.bytes)),
                "CLOSED_ARGUMENTS")
            result = {
                "stage": "CLIVOX_V2_P5_CLOSED_BEFORE_MEDIA",
                "channel_id": CHANNEL, "rights_grants_verified": 0,
                "p5_real_licensed_pipeline_complete": False,
                "youtube_uploads": 0, "candidate_count": 0,
                "status": closed["status"],
            }
        else:
            require(all(x is not None for x in (
                args.scratch, args.fixture_file, args.sha256, args.bytes)),
                "SYNTHETIC_ARGS_REQUIRED")
            result = scan_synthetic_moments(
                scratch=args.scratch, basename=args.fixture_file,
                expected_sha256=args.sha256, expected_bytes=args.bytes)
        print(json.dumps(result, sort_keys=True))
    except (P4Denied, P5Denied, OSError, ValueError, KeyError, TypeError):
        raise SystemExit("CLIVOX_V2_P5_BLOCKED_NO_CREATOR_INGEST_NO_RELEASE") from None


if __name__ == "__main__":
    main()
