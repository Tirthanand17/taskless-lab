"""Phase 3R3: TWO complete native-HD 42-second original SILENT Shorts.

Deterministically render each one-second script window as a bounded 24-frame
1080x1920/24fps H264 MP4, verify its frames and lack of audio, then stream
copy concatenate and fully decode the entire resulting 42-second video.

This is a disposable, not-licensed, NOT PUBLISHABLE engineering proof. It
never creates a narrator, claims human approval, stores a cloud artifact,
downloads anything, uses private account tokens or publishes to YouTube.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import time
from tempfile import TemporaryDirectory

from .agent_org import WorkflowError
from .phase3_csv_visual_preview import english_script_rows, render_visual_preview
from .phase3_hindi_visual_preview import _authored_profile, render_hindi_visual_preview

ENGLISH="csv_tutorial_short_en"
HINDI="csv_tutorial_short_hi"
EPISODES=(ENGLISH,HINDI)
DURATION_SECONDS=42
FPS=24
WIDTH=1080
HEIGHT=1920
ONE_SECOND_FRAME_COUNT=24
TOTAL_FRAMES=DURATION_SECONDS*FPS
MAX_PART_BYTES=20_000_000
MAX_FINAL_BYTES=95_000_000
MAX_ELAPSED_SECONDS=360


@dataclass(frozen=True)
class HDShortPart:
    number:int
    offset_seconds:int
    duration_seconds:int=1
    frame_count:int=ONE_SECOND_FRAME_COUNT


def hd_short_plan(episode_id:str)->tuple[HDShortPart,...]:
    if episode_id not in EPISODES:
        raise WorkflowError("Only the two actual authored CSV Shorts are allowed")
    if episode_id==ENGLISH and len(english_script_rows())!=4:
        raise WorkflowError("Original English Short changed; stop HD render")
    if episode_id==HINDI:
        kind,length,beats,subtitles=_authored_profile(HINDI)
        if kind!="short" or length!=DURATION_SECONDS or len(beats)!=4:
            raise WorkflowError("Original Hindi Short changed; stop HD render")
    plan=tuple(HDShortPart(i+1,i) for i in range(DURATION_SECONDS))
    if (sum(p.frame_count for p in plan)!=TOTAL_FRAMES
            or plan[-1].offset_seconds+plan[-1].duration_seconds!=DURATION_SECONDS):
        raise WorkflowError("Full native-HD Short timeline invalid")
    return plan


def _check_h264_silent(path:Path, *, expected_frames:int)->None:
    if (not path.is_file() or path.is_symlink()
            or not 2048 <= path.stat().st_size <=
            (MAX_FINAL_BYTES if expected_frames==TOTAL_FRAMES else MAX_PART_BYTES)):
        raise WorkflowError("Expected bounded video-only MP4 missing")
    try:
        probe=subprocess.run(
            ["ffprobe","-v","error","-show_entries",
             "format=duration:stream=codec_type,codec_name,width,height,nb_frames",
             "-of","json",str(path)],
            stdin=subprocess.DEVNULL,capture_output=True,text=True,
            check=True,timeout=25)
        if len(probe.stdout)>20000:
            raise WorkflowError("Unexpected excessive FFprobe metadata")
        data=json.loads(probe.stdout)
        streams=data["streams"]
        if len(streams)!=1 or streams[0].get("codec_type")!="video":
            raise WorkflowError("Exactly one video stream; no audio allowed")
        video=streams[0]
        if (video.get("codec_name")!="h264"
                or int(video["width"])!=WIDTH
                or int(video["height"])!=HEIGHT
                or int(video["nb_frames"])!=expected_frames
                or abs(float(data["format"]["duration"])-expected_frames/FPS)>0.15):
            raise WorkflowError("Incorrect full-HD video stream, length or frame count")
    except (OSError,subprocess.CalledProcessError,subprocess.TimeoutExpired,
            ValueError,KeyError,TypeError) as exc:
        raise WorkflowError("FFprobe native-HD video validation failed") from exc


def render_full_hd_short(episode_id:str,output_path:Path)->dict:
    """Render one whole 42-second HD Short; always silent/unapproved.

    The caller must select a fresh path in an existing disposable directory.
    Only standard installed Pillow/system fonts/FFmpeg are used.
    """
    plan=hd_short_plan(episode_id)
    output=Path(output_path)
    if (output.suffix.lower()!=".mp4" or output.exists() or output.is_symlink()
            or not output.parent.is_dir() or output.parent.is_symlink()):
        raise WorkflowError("New full-HD output inside existing ordinary folder required")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise WorkflowError("Existing FFmpeg/FFprobe required, no auto-download")
    if shutil.disk_usage(output.parent).free < 1_000_000_000:
        raise WorkflowError("Insufficient scratch space; do not risk partial render")
    clock=time.perf_counter()
    try:
        with TemporaryDirectory(prefix="flowminute-hd-short-parts-",dir=output.parent) as tmp:
            scratch=Path(tmp)
            items=[]
            for part in plan:
                if time.perf_counter()-clock>MAX_ELAPSED_SECONDS:
                    raise WorkflowError("Full-HD Short exceeded bounded render time")
                name=f"segment_{part.number:02}.mp4"
                segment=scratch/name
                if episode_id==ENGLISH:
                    render_visual_preview(
                        segment,duration_s=1,fps=FPS,width=WIDTH,
                        start_s=part.offset_seconds)
                else:
                    render_hindi_visual_preview(
                        HINDI,segment,duration_s=1,fps=FPS,width=WIDTH,
                        start_s=part.offset_seconds)
                _check_h264_silent(segment,expected_frames=ONE_SECOND_FRAME_COUNT)
                items.append(name)
            playlist=scratch/"scenes.ffconcat"
            playlist.write_text("ffconcat version 1.0\n"+"".join(
                f"file '{name}'\n" for name in items),encoding="utf-8")
            process=subprocess.run(
                ["ffmpeg","-nostdin","-v","error","-xerror","-n",
                 "-safe","1","-f","concat","-i",str(playlist),
                 "-map","0:v:0","-an","-c:v","copy",
                 "-movflags","+faststart",str(output)],
                stdin=subprocess.DEVNULL,capture_output=True,timeout=90)
            if process.returncode:
                raise WorkflowError("Native-HD Short scene concatenation failed")
            _check_h264_silent(output,expected_frames=TOTAL_FRAMES)
            dec=subprocess.run(
                ["ffmpeg","-nostdin","-v","error","-xerror","-i",str(output),
                 "-f","null","-"],
                stdin=subprocess.DEVNULL,capture_output=True,timeout=120)
            if dec.returncode:
                raise WorkflowError("Complete native-HD Short failed full decode")
            digest=sha256()
            with output.open("rb") as media:
                for block in iter(lambda:media.read(1_048_576),b""):
                    digest.update(block)
            return {
                "status":"REAL_FULL_HD_42S_SILENT_SHORT_NOT_PUBLISHABLE",
                "episode_id":episode_id,
                "width":WIDTH,"height":HEIGHT,
                "duration_seconds":DURATION_SECONDS,
                "fps":FPS,"frame_count":TOTAL_FRAMES,
                "scene_chunks":len(items),
                "sha256":digest.hexdigest(),
                "size_bytes":output.stat().st_size,
                "render_wall_seconds":round(time.perf_counter()-clock,3),
                "fully_decoded":True,
                "has_spoken_voice":False,
                "has_any_audio":False,
                "two_licensed_distinct_narrators_verified":False,
                "actual_subtitle_speech_alignment_verified":False,
                "independent_script_facts_verified":False,
                "high_end_cinematic_quality_approved":False,
                "ready_for_upload":False,
                "youtube_publish_authorized":False,
                "network_calls":0,
                "external_service_connected":False,
                "publishing_authorized":False,
            }
    except (OSError,subprocess.TimeoutExpired,WorkflowError):
        output.unlink(missing_ok=True)
        raise


def main()->int:
    import argparse
    parser=argparse.ArgumentParser(description="Never-publish native HD Short technical proof")
    parser.add_argument("--episode",choices=EPISODES,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(render_full_hd_short(args.episode,args.output),
                     sort_keys=True,separators=(",",":")))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
