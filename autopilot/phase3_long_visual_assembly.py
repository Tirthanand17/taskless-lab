"""Phase 3R3: full 7m12s Hindi CSV *silent* video from bounded scene clips.

Uses ONLY existing authored Hindi long scenes and an existing local FFmpeg.
Each short-lived scene MP4 is rendered separately, validated, then stream-copy
concatenated. Intermediate scenes are discarded. No accounts/network,
external media, voices, uploads, tokens, billing or publication rights.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
from typing import Sequence

from .agent_org import WorkflowError
from .phase3_hindi_visual_preview import (
    _authored_profile, render_hindi_visual_preview,
)

EPISODE = "csv_tutorial_long_hi"
DURATION_S = 432
SCENE_COUNT = 24
MAX_SCENE_SECONDS = 24
MAX_OUTPUT_BYTES = 90_000_000
_ALLOWED_FPS = (8, 12)
_ALLOWED_WIDTH = (640, 960)


@dataclass(frozen=True)
class RenderPart:
    number: int
    offset_s: int
    duration_s: int
    start_frame: int
    frame_count: int


def plan_full_long_render(*, fps: int = 8) -> tuple[RenderPart, ...]:
    """Bind each bounded render part to an existing original authored scene."""
    if type(fps) is not int or fps not in _ALLOWED_FPS:
        raise WorkflowError("Only bounded deterministic long-video rates permitted")
    kind, seconds, beats, subtitles = _authored_profile(EPISODE)
    if kind != "long" or seconds != DURATION_S or len(beats) != SCENE_COUNT:
        raise WorkflowError("Changed authored long-video storyboard requires review")
    result = []
    previous = 0
    for i, (start, end, _spoken, _visual) in enumerate(beats):
        if (start != previous or end <= start
                or start % 1000 or end % 1000
                or (end-start) // 1000 > MAX_SCENE_SECONDS):
            raise WorkflowError("Long-scene timing changed or exceeds render cap")
        start_s = start // 1000
        duration_s = (end-start) // 1000
        result.append(RenderPart(
            number=i+1, offset_s=start_s,
            duration_s=duration_s,
            start_frame=start_s*fps,
            frame_count=duration_s*fps,
        ))
        previous=end
    if previous != DURATION_S*1000:
        raise WorkflowError("Long script did not cover exactly 432 seconds")
    if sum(x.frame_count for x in result) != DURATION_S*fps:
        raise WorkflowError("Calculated long-video frame count inconsistent")
    return tuple(result)


def _probe(path: Path) -> dict:
    try:
        p = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration:stream=codec_type,codec_name,width,height,nb_frames",
             "-of", "json", str(path)],
            stdin=subprocess.DEVNULL, capture_output=True, text=True,
            check=True, timeout=25,
        )
        if len(p.stdout) > 10_000:
            raise WorkflowError("Bounded media metadata exceeded limit")
        result=json.loads(p.stdout)
        if not isinstance(result, dict):
            raise WorkflowError("Media probe was not a dictionary")
        return result
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired,
            ValueError, KeyError) as exc:
        raise WorkflowError("Unable to inspect rendered silent media") from exc


def _validate_video(path: Path, *, fps: int, width: int,
                    frames: int) -> dict:
    info = _probe(path)
    streams = info.get("streams", [])
    if len(streams) != 1 or streams[0].get("codec_type") != "video":
        raise WorkflowError("Only one silent H264 video track allowed")
    vid = streams[0]
    try:
        ok = (vid.get("codec_name") == "h264"
              and int(vid["width"]) == width
              and int(vid["height"]) == width*9//16
              and int(vid["nb_frames"]) == frames
              and abs(float(info["format"]["duration"])-frames/fps) < 0.15)
    except (ValueError, TypeError, KeyError) as exc:
        raise WorkflowError("Video metadata absent or malformed") from exc
    if not ok:
        raise WorkflowError("Visual-only frame count, size or duration mismatch")
    return info


def render_complete_long_visual(
    target: Path, *, fps: int = 8, width: int = 640
) -> dict:
    """Produce one actual 432s 16:9 H264 MP4, NO AUDIO, NOT PUBLISHABLE.

    Temp part files live only inside a private temporary directory adjacent to
    the target, so loss of a segment never yields a claimed final deliverable.
    No file overwrites or auto-created artifact stores.
    """
    if type(fps) is not int or fps not in _ALLOWED_FPS or width not in _ALLOWED_WIDTH:
        raise WorkflowError("Only bounded low-resolution visual proof is supported")
    output = Path(target)
    if (output.suffix != ".mp4" or output.exists() or output.is_symlink()
            or not output.parent.is_dir() or output.parent.is_symlink()):
        raise WorkflowError("Fresh MP4 file within existing ordinary directory required")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise WorkflowError("Existing FFmpeg and FFprobe required")
    plan = plan_full_long_render(fps=fps)
    hashes = []
    try:
        with TemporaryDirectory(prefix="fm-hindi-long-silent-", dir=output.parent) as temp:
            folder=Path(temp)
            names=[]
            for part in plan:
                filename=f"part_{part.number:02d}.mp4"
                part_path=folder/filename
                render_hindi_visual_preview(
                    EPISODE, part_path,
                    duration_s=part.duration_s,
                    start_s=part.offset_s,
                    fps=fps, width=width,
                )
                _validate_video(part_path, fps=fps, width=width,
                                frames=part.frame_count)
                if not 2048 <= part_path.stat().st_size <= MAX_OUTPUT_BYTES:
                    raise WorkflowError("Unexpected clip size")
                clip_hash=sha256(part_path.read_bytes()).hexdigest()
                hashes.append(clip_hash)
                names.append(filename)

            # All filenames are generated ourselves; -safe 1 and relative
            # names prevent loading arbitrary external media via playlist.
            playlist=folder/"parts.ffconcat"
            playlist.write_text(
                "ffconcat version 1.0\n" +
                "".join(f"file '{name}'\n" for name in names),
                encoding="utf-8",
            )
            proc=subprocess.run(
                ["ffmpeg","-nostdin","-v","error","-xerror","-n",
                 "-safe","1","-f","concat","-i",str(playlist),
                 "-map","0:v:0","-an","-c:v","copy",
                 "-movflags","+faststart",str(output)],
                stdin=subprocess.DEVNULL,capture_output=True,
                timeout=150,
            )
            if proc.returncode != 0:
                raise WorkflowError("Failed to concatenate scene clips")
            if (not output.is_file()
                    or not 2048 <= output.stat().st_size <= MAX_OUTPUT_BYTES):
                raise WorkflowError("Full long silent MP4 missing or unexpectedly sized")
            _validate_video(
                output, fps=fps, width=width, frames=DURATION_S*fps)
            probe_decode=subprocess.run(
                ["ffmpeg","-nostdin","-v","error","-xerror",
                 "-i",str(output),"-f","null","-"],
                stdin=subprocess.DEVNULL,capture_output=True,timeout=150,
            )
            if probe_decode.returncode:
                raise WorkflowError("Complete long MP4 did not decode")
            overall=sha256()
            with output.open("rb") as file:
                for block in iter(lambda: file.read(1_048_576),b""):
                    overall.update(block)
            return {
                "status": "FULL_432S_LONG_ORIGINAL_VISUAL_MP4_ONLY_NOT_PUBLISHABLE",
                "episode_id": EPISODE,
                "width": width, "height": width*9//16,
                "duration_seconds": DURATION_S, "frames": DURATION_S*fps,
                "fps": fps, "parts_rendered": len(plan),
                "parts_were_bounded": True,
                "all_parts_reconciled": True,
                "sha256": overall.hexdigest(),
                "part_hash_count": len(hashes),
                "intermediate_parts_discarded": True,
                "has_narration_or_music": False,
                "licensed_voice_verified": False,
                "caption_speech_sync_verified": False,
                "independent_factual_approval_verified": False,
                "high_resolution_production_quality_verified": False,
                "youtube_upload_authorized": False,
                "publishing_authorized": False,
                "network_calls": 0,
            }
    except (OSError, subprocess.TimeoutExpired, WorkflowError):
        output.unlink(missing_ok=True)
        raise


def main(argv: Sequence[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Original Hindi full silent visual QA")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fps", type=int, default=8)
    parser.add_argument("--width", type=int, default=640)
    opts = parser.parse_args(argv)
    print(json.dumps(render_complete_long_visual(
        opts.output,fps=opts.fps,width=opts.width),
        sort_keys=True,separators=(",",":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
