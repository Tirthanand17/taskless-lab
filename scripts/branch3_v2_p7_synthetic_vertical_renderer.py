"""CLIVOX V2 P7: generate a six-second original, synthetic-only 9:16 QA video.

No third-party media input is ever accepted: FFmpeg receives ONLY fixed lavfi
color/silence/sine generators, with fixed P6-validated original caption text.
The written P6 packet is NOT legal approval. Public CI keeps MP4 in an
ephemeral runner and NEVER uploads video, contracts, thumbnails, or API keys.
"""
from __future__ import annotations

import argparse
from array import array
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys

from scripts.branch3_v2_p5_synthetic_moment_proposals import (
    CHANNEL, P5Denied, _probe_closed,
)
from scripts.branch3_v2_p6_synthetic_storyboard import (
    P6Denied, validate_storyboard,
)
from scripts.branch3_v2_p4_synthetic_handoff_preflight import (
    P4Denied, MAX_FIXTURE_BYTES, inspect_synthetic_fixture,
)

FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
INPUT_NAME = "synthetic-edl-draft-only.json"
OUTPUT_NAME = "synthetic_clivox_short.mp4"
DURATION_SEC = 6
WIDTH, HEIGHT, FPS = 270, 480, 24
OUTPUT_STAGE = "CLIVOX_V2_P7_ORIGINAL_SYNTHETIC_VERTICAL_RENDER_QA_ONLY"
MAX_EDL_BYTES = 32_768
MAX_PROBE_BYTES = 40000


class P7Denied(ValueError):
    """Fail closed on non-synthetic rendering, media QA or released-state claims."""


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise P7Denied("CLIVOX_V2_P7_DENIED_" + reason)


def read_synthetic_edl(scratch: Path, filename: str = INPUT_NAME) -> dict:
    _probe_closed()
    require(isinstance(scratch, Path) and scratch.is_dir()
            and not scratch.is_symlink() and filename == INPUT_NAME,
            "ONLY_LOCAL_SYNTHETIC_EDL")
    base = scratch.resolve(strict=True)
    target = base / INPUT_NAME
    require(target.is_file() and not target.is_symlink()
            and target.resolve(strict=True).parent == base
            and 0 < target.stat().st_size <= MAX_EDL_BYTES,
            "EDL_FILE_SAFETY")
    try:
        packet = json.loads(target.read_text(encoding="utf-8"))
    except (ValueError, OSError, UnicodeError):
        raise P7Denied("CLIVOX_V2_P7_DENIED_BAD_EDL_JSON") from None
    try:
        validate_storyboard(packet)
    except (P6Denied, P5Denied, TypeError, KeyError, ValueError):
        raise P7Denied("CLIVOX_V2_P7_DENIED_P6_STORYBOARD") from None
    return packet


def _filters(edl: dict) -> str:
    validate_storyboard(edl)  # exact caption words and fixed timecodes
    captions = []
    for shot in edl["draft_shots"]:
        start = shot["target_start_ms"] / 1000
        end = shot["target_end_ms"] / 1000
        phrase = shot["original_clivox_overlay"]
        require(bool(re.fullmatch(r"[A-Za-z .]+", phrase)) and
                len(phrase) <= 50, "SAFE_FIXED_CAPTION")
        # Short synthetic caption cards must fit the 270px vertical preview.
        font_size = 12 if len(phrase) > 25 else 17
        captions.append(
            "drawtext=fontfile=" + str(FONT) + ":text='" + phrase + "'"
            + f":fontcolor=white:fontsize={font_size}:box=1:boxcolor=black@0.75"
            + ":boxborderw=7:x=(w-text_w)/2:y=(h-text_h)*0.68"
            + f":enable='gte(t,{start:g})*lt(t,{end:g})'"
        )
    return (
        "[0:v][1:v][2:v]concat=n=3:v=1:a=0[base];"
        + "[base]" + ",".join(captions) + "[v];"
        + "[3:a][4:a][5:a]concat=n=3:v=0:a=1[a]"
    )


def render_command(edl: dict, *, target: Path) -> list[str]:
    """Only lavfi inputs; no -i file, arbitrary network, script, URL or voice."""
    _probe_closed()
    require(isinstance(target, Path) and target.name == OUTPUT_NAME
            and not target.is_symlink(), "OUTPUT_TARGET")
    require(FONT.is_file() and not FONT.is_symlink(), "SYSTEM_FONT_MISSING")
    filters = _filters(edl)
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error",
           "-nostdin", "-n"]
    for color, seconds in (("black", 2), ("white", 1), ("black", 3)):
        cmd += ["-f", "lavfi", "-i",
                f"color=c={color}:s={WIDTH}x{HEIGHT}:r={FPS}:d={seconds}"]
    for sound, seconds in (("anullsrc", 2), ("sine", 1), ("anullsrc", 3)):
        if sound == "sine":
            desc = "sine=frequency=440:sample_rate=48000:duration=1"
        else:
            desc = f"anullsrc=r=48000:cl=mono:d={seconds}"
        cmd += ["-f", "lavfi", "-i", desc]
    cmd += ["-filter_complex", filters, "-map", "[v]", "-map", "[a]",
            "-t", str(DURATION_SEC), "-r", str(FPS),
            "-c:v", "libx264", "-threads:v", "1",
            "-preset", "ultrafast", "-crf", "23", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-ar", "48000", "-ac", "1",
            "-movflags", "+faststart", "-f", "mp4", str(target)]
    # Every input is one of the six fixed lavfi generators. No media file
    # or URL is ever accepted as a source.
    positions = [i for i, x in enumerate(cmd) if x == "-i"]
    require(len(positions) == 6 and all(cmd[i - 2:i] == ["-f", "lavfi"]
                                      for i in positions),
            "GENERATED_INPUTS_ONLY")
    return cmd


def _run_binary(cmd: list[str], *, runner=subprocess.run,
                max_bytes: int) -> bytes:
    try:
        p = runner(cmd, capture_output=True, timeout=25, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise P7Denied("CLIVOX_V2_P7_DENIED_MEDIA_TOOL_TIMEOUT") from None
    require(p.returncode == 0 and type(p.stdout) is bytes
            and len(p.stdout) <= max_bytes, "MEDIA_COMMAND_FAILED")
    return p.stdout


def verify_output_probe(info: object, *, actual_bytes: int) -> None:
    """Independent output container, stream, timebase and sync checks."""
    require(type(info) is dict and type(info.get("streams")) is list
            and type(info.get("format")) is dict, "PROBE_SCHEMA")
    streams = info["streams"]
    require(len(streams) == 2 and all(type(x) is dict for x in streams),
            "ONLY_AV")
    video = [x for x in streams if x.get("codec_type") == "video"]
    audio = [x for x in streams if x.get("codec_type") == "audio"]
    require(len(video) == 1 and len(audio) == 1, "BOTH_STREAMS")
    v, a = video[0], audio[0]
    require(v.get("codec_name") == "h264"
            and v.get("pix_fmt") == "yuv420p"
            and type(v.get("width")) is int and v["width"] == WIDTH
            and type(v.get("height")) is int and v["height"] == HEIGHT
            and v.get("avg_frame_rate") == f"{FPS}/1"
            and str(v.get("nb_frames")) == str(FPS * DURATION_SEC),
            "VERTICAL_VIDEO")
    require(a.get("codec_name") == "aac"
            and str(a.get("sample_rate")) == "48000"
            and type(a.get("channels")) is int and a["channels"] == 1,
            "AUDIO_FORMAT")
    fmt = info["format"]
    require(type(fmt.get("format_name")) is str
            and "mp4" in fmt["format_name"].split(","),
            "CONTAINER")
    try:
        duration = float(fmt["duration"])
        encoded_bytes = int(fmt["size"])
        v_start = float(v["start_time"])
        a_start = float(a["start_time"])
        v_dur = float(v["duration"])
        a_dur = float(a["duration"])
    except (KeyError, TypeError, ValueError, OverflowError):
        raise P7Denied("CLIVOX_V2_P7_DENIED_BAD_PROBE_TIME") from None
    require(5.9 <= duration <= 6.2
            and 5.9 <= v_dur <= 6.2 and 5.9 <= a_dur <= 6.2
            and abs(v_start - a_start) <= 0.10
            and abs(v_dur - a_dur) <= 0.10
            and abs(v_start) <= 0.10 and abs(a_start) <= 0.10,
            "AV_SYNC_OR_DURATION")
    require(type(actual_bytes) is int and 128 <= actual_bytes <= MAX_FIXTURE_BYTES
            and encoded_bytes == actual_bytes, "OUTPUT_BYTES")


def _frame_patch(file: Path, second: float, *, runner=subprocess.run,
                 overlay: bool) -> bytes:
    if overlay:
        crop = "crop=200:44:35:315,format=gray"
        expected = 200 * 44
    else:
        crop = "crop=8:8:0:0,format=gray"
        expected = 64
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
        "-protocol_whitelist", "file", "-ss", str(second), "-i", str(file),
        "-vf", crop, "-frames:v", "1", "-f", "rawvideo", "pipe:1",
    ]
    result = _run_binary(cmd, runner=runner, max_bytes=expected)
    require(len(result) == expected, "PIXEL_PATCH_SIZE")
    return result


def _audio_rms(file: Path, second: float, *, runner=subprocess.run) -> float:
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
        "-protocol_whitelist", "file", "-ss", str(second), "-i", str(file),
        "-vn", "-t", "0.25", "-ac", "1", "-ar", "8000",
        "-f", "s16le", "pipe:1",
    ]
    pcm = _run_binary(cmd, runner=runner, max_bytes=5000)
    require(len(pcm) >= 1000 and len(pcm) % 2 == 0,
            "AUDIO_SAMPLE_LENGTH")
    samples = array("h")
    samples.frombytes(pcm)
    if sys.byteorder != "little":
        samples.byteswap()
    return (sum(int(s) * int(s) for s in samples) / len(samples)) ** 0.5


def check_original_signal_and_captions(file: Path, *, runner=subprocess.run) -> None:
    """Check actual original scene turns, visible overlay and tone versus silence."""
    dark1 = _frame_patch(file, 1.0, runner=runner, overlay=False)
    light = _frame_patch(file, 2.5, runner=runner, overlay=False)
    dark2 = _frame_patch(file, 4.5, runner=runner, overlay=False)
    require(statistics.mean(dark1) < 45
            and statistics.mean(light) > 205
            and statistics.mean(dark2) < 45, "SCENE_TIMING")
    for second in (1.0, 2.5, 4.5):
        image = _frame_patch(file, second, runner=runner, overlay=True)
        require(max(image) - min(image) >= 85, "ORIGINAL_CAPTION_VISIBILITY")
    silence_a = _audio_rms(file, 1.0, runner=runner)
    tone = _audio_rms(file, 2.5, runner=runner)
    silence_b = _audio_rms(file, 4.5, runner=runner)
    require(tone > 200 and silence_a < tone * 0.10
            and silence_b < tone * 0.10, "AUDIO_CUE_SYNC")


def render_synthetic_video(*, scratch: Path, edl_file: str = INPUT_NAME,
                           runner=subprocess.run) -> dict:
    """Generate exactly one tiny original-only MP4; return no path or digest."""
    _probe_closed()
    edl = read_synthetic_edl(scratch, edl_file)
    base = scratch.resolve(strict=True)
    target = base / OUTPUT_NAME
    require(not target.exists() and not target.is_symlink(),
            "OUTPUT_MUST_NOT_EXIST")
    cmd = render_command(edl, target=target)
    try:
        job = runner(cmd, capture_output=True, timeout=40, check=False)
    except (subprocess.TimeoutExpired, OSError):
        raise P7Denied("CLIVOX_V2_P7_DENIED_RENDER_TIMEOUT") from None
    require(job.returncode == 0, "RENDER_FAILED")
    require(target.is_file() and not target.is_symlink()
            and target.resolve(strict=True).parent == base,
            "NEW_SYNTHETIC_MP4_REQUIRED")
    size = target.stat().st_size
    require(128 <= size <= MAX_FIXTURE_BYTES, "OUTPUT_BOUNDED")
    digest = hashlib.sha256()
    with target.open("rb") as src:
        while block := src.read(65536):
            digest.update(block)
    # P4 checks original-source quarantine, exact digest, codec and full decode.
    try:
        checked = inspect_synthetic_fixture(
            scratch=scratch, basename=OUTPUT_NAME,
            expected_sha256=digest.hexdigest(), expected_bytes=size,
            runner=runner,
        )
    except (P4Denied, OSError, TypeError, KeyError, ValueError):
        raise P7Denied("CLIVOX_V2_P7_DENIED_P4_CODEC_INTEGRITY") from None
    require(checked["synthetic_fixture_decoded"] is True
            and checked["rights_grants_verified"] == 0
            and checked["youtube_upload_enabled"] is False, "NO_RELEASE")
    try:
        probe = runner([
            "ffprobe", "-v", "error", "-protocol_whitelist", "file",
            "-show_format", "-show_streams", "-of", "json", str(target),
        ], capture_output=True, text=True, timeout=20, check=False)
    except (subprocess.TimeoutExpired, OSError):
        raise P7Denied("CLIVOX_V2_P7_DENIED_PROBE_TOOL") from None
    require(probe.returncode == 0 and type(probe.stdout) is str
            and len(probe.stdout) <= MAX_PROBE_BYTES, "PROBE_RESPONSE")
    try:
        detail = json.loads(probe.stdout)
    except (TypeError, ValueError):
        raise P7Denied("CLIVOX_V2_P7_DENIED_PROBE_JSON") from None
    verify_output_probe(detail, actual_bytes=size)
    check_original_signal_and_captions(target, runner=runner)
    _probe_closed()
    return {
        "stage": OUTPUT_STAGE, "channel_id": CHANNEL,
        "synthetic_original_lavfi_only": True,
        "source_creator_media_count": 0,
        "real_creator_licenses_verified": 0,
        "original_synthetic_mp4_rendered_in_ephemeral_scratch": True,
        "synthetic_h264_aac_decode_validated": True,
        "synthetic_portrait_9_16_validated": True,
        "synthetic_original_caption_pixels_validated": True,
        "synthetic_audio_cue_and_scene_sync_validated": True,
        "preview_width": WIDTH, "preview_height": HEIGHT,
        "duration_ms": DURATION_SEC * 1000,
        "real_1080x1920_output_validated": False,
        "real_creator_source_processing_allowed": False,
        "real_editorial_context_verified": False,
        "owner_exact_final_media_approved": False,
        "youtube_uploads": 0, "youtube_publish_authorized": False,
        "p7_real_licensed_compositor_milestone_complete": False,
        "status": "SYNTHETIC_RENDER_QA_ONLY_NO_CREATOR_LICENSE_NO_RELEASE",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("closed", "synthetic"), default="closed")
    parser.add_argument("--scratch", type=Path)
    parser.add_argument("--edl-file")
    args = parser.parse_args()
    try:
        _probe_closed()
        if args.mode == "closed":
            require(args.scratch is None and args.edl_file is None,
                    "CLOSED_ARGS")
            report = {
                "stage": "CLIVOX_V2_P7_CLOSED_BEFORE_REAL_RENDER",
                "channel_id": CHANNEL, "real_creator_licenses_verified": 0,
                "youtube_uploads": 0, "youtube_publish_authorized": False,
                "p7_real_licensed_compositor_milestone_complete": False,
            }
        else:
            require(args.scratch is not None and args.edl_file is not None,
                    "ONLY_EPHEMERAL_SYNTHETIC_EDL")
            report = render_synthetic_video(
                scratch=args.scratch, edl_file=args.edl_file)
        print(json.dumps(report, sort_keys=True))
    except (P7Denied, P4Denied, P5Denied, P6Denied, OSError, ValueError,
            KeyError, TypeError, UnicodeError):
        raise SystemExit(
            "CLIVOX_V2_P7_BLOCKED_NO_CREATOR_MEDIA_NO_YOUTUBE_UPLOAD"
        ) from None


if __name__ == "__main__":
    main()
