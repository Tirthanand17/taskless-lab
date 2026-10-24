"""FlowMinute FFmpeg episode draft assembler.

Real video/audio inputs only. No Flow credentials, API calls, uploads or billing.
Never approves rights, factual content, natural voices or YouTube publishing.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import math
import re
import subprocess

TARGETS = {
    "fm_20261024_short_en": (48000, 720, 1280),
    "fm_20261024_short_hi": (48000, 720, 1280),
    "fm_20261024_long_hi": (300000, 1280, 720),
}
# Creator-rejected 48s cut is NEVER an acceptable source for cinematic V2.
CINEMATIC_V2_ID = "cinematic_v2_32s"
CINEMATIC_V2_SHOTS = ("asha_jay_opening", "cinematic_02", "cinematic_03", "cinematic_04")
APPROVED_REEXPORTED_OPENING_SHA256 = "536652db768052c69e640d0bcd5c950cafcfcee37cc062286dcef2e2d4938517"
REJECTED_48S_SHA256 = "7bd6319297fba469709467ac3416fd32be1a5efa9f25ee1d2c8c1dd016050fb9"
VIDEO_SAFE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,120}\.mp4")
HEX = re.compile(r"[0-9a-f]{64}")
MAX_BYTES = 1_073_741_824


class AssemblyError(ValueError):
    pass


def _require(ok: bool, why: str):
    if not ok:
        raise AssemblyError(why)


def _cmd(args: list[str], timeout: int = 180) -> str:
    try:
        result = subprocess.run(args, capture_output=True, text=True,
                                timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as ex:
        raise AssemblyError("FFmpeg operation unavailable") from ex
    if result.returncode:
        raise AssemblyError("FFmpeg operation failed: " + (result.stderr or "")[-700:])
    return result.stdout


def _probe(file: Path) -> tuple[dict, dict, float]:
    try:
        body = json.loads(_cmd([
            "ffprobe", "-v", "error", "-show_entries",
            "stream=codec_type,codec_name,width,height,r_frame_rate:"
            "format=duration,format_name", "-of", "json", str(file)]))
        video = [x for x in body["streams"] if x.get("codec_type") == "video"]
        audio = [x for x in body["streams"] if x.get("codec_type") == "audio"]
        _require(len(video) == 1 and len(audio) == 1,
                 "Every source needs exactly one video stream and one audio stream")
        seconds = float(body["format"]["duration"])
        _require(math.isfinite(seconds) and 0 < seconds <= 3600, "Bad source duration")
        return video[0], audio[0], seconds
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as ex:
        raise AssemblyError("Invalid media metadata") from ex


def _file_check(path: Path, digest: str) -> tuple[dict, float]:
    _require(path.is_file() and not path.is_symlink()
             and VIDEO_SAFE.fullmatch(path.name) is not None,
             "Missing, symlinked or unsafe source MP4")
    _require(100 <= path.stat().st_size <= MAX_BYTES, "Unsafe source size")
    _require(isinstance(digest, str) and HEX.fullmatch(digest) is not None,
             "Source file SHA256 must be pinned")
    hash_value = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hash_value.update(block)
    _require(hash_value.hexdigest() == digest, "Source media checksum changed")
    video, _, duration = _probe(path)
    return video, duration


def check_cinematic_v2_contract(manifest: dict) -> int:
    """Review-only structural gate; a plan or pretty storyboard is not video footage.

    Returns intended duration, but grants NO rights, creative QA, or publication.
    """
    if manifest.get("creative_revision") is None:
        return 0
    _require(manifest["creative_revision"] == CINEMATIC_V2_ID,
             "Unknown creative revision")
    _require(manifest.get("episode_id") == "fm_20261024_short_en",
             "Only the approved English Short has a 32s cinematic revision")
    segments = manifest.get("segments")
    _require(isinstance(segments,list) and len(segments) == 4,
             "Cinematic 32s video needs exactly four real video clips")
    ids = tuple(x.get("id") if isinstance(x,dict) else None for x in segments)
    _require(ids == CINEMATIC_V2_SHOTS,
             "Wrong 32s order; missing 3D scenes or opening footage")
    _require(all(x.get("duration_ms") == 8000 and x.get("source_start_ms") == 0
                 for x in segments),
             "Cinematic revision requires exactly four contiguous eight-second scenes")
    _require(segments[0].get("sha256") == APPROVED_REEXPORTED_OPENING_SHA256,
             "Opening must be the exact approved 8s reference MP4")
    sha = [x.get("sha256") for x in segments]
    _require(all(isinstance(x,str) and HEX.fullmatch(x) for x in sha),
             "Every real 3D scene must carry its own pinned MP4 digest")
    _require(len(set(sha)) == 4 and REJECTED_48S_SHA256 not in sha,
             "Duplicate footage or owner-rejected flat video is prohibited")
    _require(len({x.get("path") for x in segments}) == 4,
             "Four unique real scene files required; no repeated filler")
    return 32000


def validate_manifest(manifest: dict, *, test_mode: bool = False) -> dict:
    _require(isinstance(manifest, dict) and manifest.get("schema_version") == 1,
             "Invalid assembly schema")
    eid = manifest.get("episode_id")
    _require(eid in TARGETS, "Unsupported episode ID")
    planned, width, height = TARGETS[eid]
    cinematic_duration = check_cinematic_v2_contract(manifest)
    if cinematic_duration:
        _require(not test_mode, "Cinematic V2 refuses synthetic partial test assembly")
        planned = cinematic_duration
    segments = manifest.get("segments")
    _require(isinstance(segments, list) and 1 <= len(segments) <= 60,
             "Need actual video segments")
    seen = set()
    total = 0
    validated = []
    for segment in segments:
        _require(isinstance(segment, dict), "Invalid scene segment")
        name = segment.get("id")
        _require(isinstance(name, str) and re.fullmatch("[a-z0-9_]{3,40}", name)
                 and name not in seen, "Invalid/duplicated segment ID")
        seen.add(name)
        file_path = segment.get("path")
        _require(isinstance(file_path, str) and file_path, "Missing file path")
        file = Path(file_path)
        video, source_seconds = _file_check(file, segment.get("sha256"))
        start = segment.get("source_start_ms")
        duration = segment.get("duration_ms")
        _require(type(start) is int and type(duration) is int
                 and start >= 0 and duration >= 500,
                 "Missing accurate source timing")
        _require(start / 1000 + duration / 1000 <= source_seconds + .08,
                 "Trim exceeds actual source media")
        src_width, src_height = int(video["width"]), int(video["height"])
        _require(src_width >= 240 and src_height >= 240,
                 "Source clip too small for editorial edit")
        actual = src_width / src_height
        expected = width / height
        _require(abs(actual - expected) < .03, "Scene aspect ratio differs from episode")
        total += duration
        _require(total <= planned, "Episode is longer than its storyboard target")
        validated.append({"name": name, "file": file,
                          "start": start / 1000, "duration": duration / 1000,
                          "source_width": src_width, "source_height": src_height})
    complete = total == planned
    if not test_mode:
        _require(complete, "Incomplete timeline: refusing to pad with silent or fake footage")
    else:
        _require(total <= planned, "Test duration exceeds episode target")
    return {"episode_id": eid, "planned_ms": planned, "assembled_ms": total,
            "missing_ms": planned - total, "full_duration": complete,
            "output_width": width, "output_height": height, "segments": validated,
            "status": "FULL_DURATION_DRAFT_ONLY" if complete else "PARTIAL_TEST_DRAFT_ONLY",
            "release_authorized": False, "youtube_scheduled": False}


def assemble(manifest: dict, output: str | Path, *, test_mode: bool = False) -> dict:
    info = validate_manifest(manifest, test_mode=test_mode)
    destination = Path(output)
    _require(destination.parent.is_dir() and not destination.parent.is_symlink()
             and destination.suffix.lower() == ".mp4" and
             VIDEO_SAFE.fullmatch(destination.name) is not None
             and not destination.exists() and not destination.is_symlink(),
             "Output must be a new MP4 inside an existing real directory")
    width, height = info["output_width"], info["output_height"]
    with TemporaryDirectory(prefix="flowminute-compose-", dir=destination.parent) as folder:
        stage = Path(folder)
        all_files = []
        for i, segment in enumerate(info["segments"]):
            dest = stage / ("part_%03d.mp4" % i)
            vf = (
                "fps=30,scale=%d:%d:force_original_aspect_ratio=decrease,"
                "pad=%d:%d:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p"
                % (width, height, width, height)
            )
            _cmd(["ffmpeg","-hide_banner","-nostdin","-loglevel","error",
                  "-ss",str(segment["start"]),"-i",str(segment["file"]),
                  "-t",str(segment["duration"]),
                  "-vf",vf,"-af","aresample=async=1:first_pts=0,apad",
                  "-c:v","libx264","-preset","veryfast","-crf","24",
                  "-pix_fmt","yuv420p","-r","30",
                  "-c:a","aac","-ar","48000","-ac","2",
                  "-movflags","+faststart","-y",str(dest)])
            all_files.append(dest)
        concat = stage / "concat.txt"
        # No interpolated path from user input is added to the FFmpeg concat list.
        concat.write_text("".join("file 'part_%03d.mp4'\n" % i
                                  for i in range(len(all_files))), encoding="utf-8")
        draft = stage / "assembled.mp4"
        _cmd(["ffmpeg","-hide_banner","-nostdin","-loglevel","error",
              "-f","concat","-safe","1","-i",str(concat),
              "-c","copy","-movflags","+faststart","-y",str(draft)])
        video, audio, seconds = _probe(draft)
        _require((int(video["width"]), int(video["height"])) == (width, height),
                 "Result has wrong dimensions")
        _require(video.get("codec_name") == "h264" and audio.get("codec_name") == "aac",
                 "Result lacks H264/AAC")
        _require(abs(seconds - info["assembled_ms"] / 1000) < .35,
                 "Result length drifted from scene timeline")
        _cmd(["ffmpeg","-hide_banner","-nostdin","-loglevel","error",
              "-xerror","-i",str(draft),"-f","null","-"],timeout=180)
        # Success is atomic: no partial output left if any step above fails.
        draft.replace(destination)
    digest = sha256()
    with destination.open("rb") as fh:
        for piece in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(piece)
    return {"episode_id": info["episode_id"],
            "status": info["status"],
            "output_file_name": destination.name,
            "output_sha256": digest.hexdigest(),
            "verified_duration_seconds": round(seconds, 3),
            "dimensions": [width,height],
            "segments": len(info["segments"]),
            "missing_seconds": info["missing_ms"] / 1000,
            "audio_present_not_voice_verified": True,
            "natural_voice_verified": False,
            "factual_review_verified": False,
            "visual_art_qa_verified": False,
            "rights_verified": False,
            "publishing_authorized": False,
            "youtube_scheduled": False}
