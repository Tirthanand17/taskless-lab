"""Phase 3R3: native-HD entire 432s Hindi tutorial -- silent QA, NEVER release.

Exactly 432 verified 1-second / 24-frame original 1920x1080 segments
are generated using the existing MAX_HIRES_FRAMES=36 Hindi renderer.
Each segment is H264 video ONLY. Validate all, concatenate without
reencoding, ffprobe total 10368 frames / 432 s and fully decode.

No model, narrator, speech, publisher, OAuth, service, persistent cloud
storage or paid infrastructure. This is a bounded, ephemeral engineering test.
"""
from __future__ import annotations

from hashlib import sha256
import json
import math
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
from time import monotonic

from .agent_org import WorkflowError
from .phase3_hindi_visual_preview import (
    _authored_profile,render_hindi_visual_preview,MAX_HIRES_FRAMES,
)

EPISODE="csv_tutorial_long_hi"
DURATION_SECONDS=432
FPS=24
WIDTH=1920
HEIGHT=1080
SEGMENT_FRAMES=24
SEGMENT_SECONDS=1
TOTAL_FRAMES=DURATION_SECONDS*FPS
MAX_RENDER_WALL_SECONDS=780
MAX_FINAL_BYTES=120_000_000
MAX_SINGLE_BYTES=3_000_000
MIN_DISK_FREE_BYTES=800_000_000


def plan_native_hd_long() -> tuple[int,...]:
    """A fixed, gapless original-script frame map; no arbitrary remote input."""
    kind, length, beats, cues=_authored_profile(EPISODE)
    if kind!="long" or length!=DURATION_SECONDS or len(beats)!=24:
        raise WorkflowError("Authored 7m12s long-form script changed")
    if MAX_HIRES_FRAMES < SEGMENT_FRAMES:
        raise WorkflowError("HD segment exceeds renderer's per-call safety cap")
    if (beats[0][0]!=0 or beats[-1][1]!=DURATION_SECONDS*1000
            or any(left[1]!=right[0] for left,right in zip(beats,beats[1:]))):
        raise WorkflowError("Gaps or overlaps in authored long scenes")
    seconds=tuple(range(DURATION_SECONDS))
    if len(seconds)*SEGMENT_FRAMES!=TOTAL_FRAMES:
        raise WorkflowError("Native-HD long video frame plan invalid")
    return seconds


def _probe_exact_video(path:Path, *, frames:int, max_bytes:int)->None:
    if (not path.is_file() or path.is_symlink()
            or not 2048<=path.stat().st_size<=max_bytes):
        raise WorkflowError("No bounded H264 MP4 at expected path")
    try:
        p=subprocess.run(
            ["ffprobe","-v","error","-show_entries",
             "stream=codec_type,codec_name,width,height,nb_frames:format=duration",
             "-of","json",str(path)],stdin=subprocess.DEVNULL,
            capture_output=True,text=True,check=True,timeout=25)
        if len(p.stdout)>16_000:
            raise WorkflowError("Unexpected oversized media metadata")
        data=json.loads(p.stdout)
        stream=data["streams"]
        if len(stream)!=1 or stream[0].get("codec_type")!="video":
            raise WorkflowError("Native HD QA requires a single silent video stream")
        codec=stream[0]
        if (codec.get("codec_name")!="h264"
                or int(codec["width"])!=WIDTH
                or int(codec["height"])!=HEIGHT
                or int(codec["nb_frames"])!=frames
                or not math.isfinite(float(data["format"]["duration"]))
                or abs(float(data["format"]["duration"])-frames/FPS)>0.12):
            raise WorkflowError("Incorrect H264 video geometry, codec, duration or frame count")
    except (OSError,ValueError,KeyError,TypeError,subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as err:
        raise WorkflowError("Failed to parse or validate original HD media") from err


def render_native_hd_long(target:Path)->dict:
    """Build a complete silent 432s movie with capped per-call HD rendering.

    Output is discarded by the caller's CI workflow; never a licensed or
    publishable artifact. Requires an already-existing local scratch folder.
    """
    parts=plan_native_hd_long()
    output=Path(target)
    if (output.suffix.lower()!=".mp4" or output.exists() or output.is_symlink()
            or not output.parent.is_dir() or output.parent.is_symlink()
            or not shutil.which("ffmpeg") or not shutil.which("ffprobe")
            or shutil.disk_usage(output.parent).free<MIN_DISK_FREE_BYTES):
        raise WorkflowError("Fresh local MP4, disk and installed FFmpeg required")
    began=monotonic()
    max_subpart=0
    try:
        with TemporaryDirectory(prefix="fm-long-1080p-silent-",dir=output.parent) as temp:
            folder=Path(temp)
            playlist_lines=["ffconcat version 1.0"]
            # 1s 24-frame parts are run serially. Fixed local basenames;
            # ffconcat safe=1 cannot load external or URL sources.
            for second in parts:
                if monotonic()-began>MAX_RENDER_WALL_SECONDS:
                    raise WorkflowError("Full native-HD long exceeded strict time budget")
                name=f"scene_{second:03d}.mp4"
                part=folder/name
                receipt=render_hindi_visual_preview(
                    EPISODE,part,duration_s=SEGMENT_SECONDS,
                    fps=FPS,width=WIDTH,start_s=second)
                if (receipt["audio_track_present"] or receipt["publishing_authorized"]):
                    raise WorkflowError("Untrusted Hindi renderer reported unexpected production state")
                _probe_exact_video(part,frames=SEGMENT_FRAMES,max_bytes=MAX_SINGLE_BYTES)
                max_subpart=max(max_subpart,part.stat().st_size)
                playlist_lines.append(f"file '{name}'")
            playlist=folder/"sequence.ffconcat"
            playlist.write_text("\n".join(playlist_lines)+"\n",encoding="utf-8")
            copied=subprocess.run(
                ["ffmpeg","-nostdin","-v","error","-xerror","-n",
                 "-safe","1","-f","concat","-i",str(playlist),
                 "-map","0:v:0","-an","-c:v","copy","-movflags",
                 "+faststart",str(output)],
                stdin=subprocess.DEVNULL,capture_output=True,timeout=110)
            if copied.returncode:
                raise WorkflowError("Native HD long concat failed")
            _probe_exact_video(output,frames=TOTAL_FRAMES,max_bytes=MAX_FINAL_BYTES)
            decoded=subprocess.run(
                ["ffmpeg","-nostdin","-v","error","-xerror","-i",
                 str(output),"-f","null","-"],
                stdin=subprocess.DEVNULL,capture_output=True,timeout=150)
            if decoded.returncode:
                raise WorkflowError("Full HD 432s H264 video did not decode")
            if monotonic()-began>MAX_RENDER_WALL_SECONDS:
                raise WorkflowError("Full HD complete render exceeded total time cap")
            h=sha256()
            with output.open("rb") as stream:
                for block in iter(lambda:stream.read(1024*1024),b""):
                    h.update(block)
            return {
                "status":"REAL_NATIVE_HD_432S_HINDI_SILENT_FULL_DECODE_NO_RELEASE",
                "episode_id":EPISODE,
                "duration_seconds":DURATION_SECONDS,
                "fps":FPS,
                "width":WIDTH,"height":HEIGHT,
                "total_frames":TOTAL_FRAMES,
                "verified_one_second_segments":len(parts),
                "max_single_segment_bytes":max_subpart,
                "mp4_size_bytes":output.stat().st_size,
                "mp4_sha256":h.hexdigest(),
                "render_wall_seconds":round(monotonic()-began,2),
                "fully_decoded":True,
                "separate_temp_chunks_removed":True,
                "actual_human_voice_present":False,
                "two_voices_verified":False,
                "voice_rights_verified":False,
                "speech_caption_alignment_verified":False,
                "factual_editorial_approval_verified":False,
                "premium_cinematic_quality_verified":False,
                "licensed_media_release_ready":False,
                "youtube_upload_authorized":False,
                "publishing_authorized":False,
                "network_calls":0,
            }
    except (OSError,subprocess.TimeoutExpired,WorkflowError):
        output.unlink(missing_ok=True)
        raise


def main()->int:
    import argparse
    parser=argparse.ArgumentParser(description="432s silent native 1080p smoke, NEVER publish")
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(render_native_hd_long(args.output),sort_keys=True,
                     separators=(",",":")))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
