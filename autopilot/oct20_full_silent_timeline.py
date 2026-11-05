"""Seven-scene full-duration ORIGINAL October-20 silent editor preview.

Unlike the earlier 9-second kinetic snippets, this connects EVERY original
7-scene English/Hindi script timestamp to one original vector-like storyboard
keyframe and FFmpeg camera motion. May render a full 42/44 second video-only
H.264 MP4 ONLY into a caller-chosen, empty, disposable output directory.

This is a preview composition, never a publishable video: no spoken language,
no licensed human voice, no independent transcription/SRT, no 3D scene mesh,
no copyrights assertion, no YouTube account, no OAuth, no services or uploads.
No media render in public CI beyond one-second *offline* QA.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import shutil
import subprocess
import time

from .agent_org import WorkflowError
from .oct20_silent_concept_preview import (
    HEADLINES,load_preview_plan,preview_spec,render_storyboard_keyframe,
)

FPS=24
WIDTH=432
HEIGHT=768
MAX_OUTPUT_BYTES=100_000_000
_MAX_SCENE_COUNT=7
_ALLOWED={
    "fm_20261020_short_en":(42,"en"),
    "fm_20261020_short_hi":(44,"hi"),
}


def _deny():
    raise WorkflowError("Offline original seven-scene silent review refused")


@dataclass(frozen=True)
class SceneCut:
    scene_index:int
    start_frame:int
    end_frame:int
    start_second:int
    end_second:int


def full_silent_scene_plan(episode_id:str)->tuple[SceneCut,...]:
    """Bind only the original Oct20 script's true 7 scene boundaries."""
    if type(episode_id) is not str or episode_id not in _ALLOWED:
        _deny()
    source=load_preview_plan()
    spec=preview_spec(source,episode_id)
    duration,lang=_ALLOWED[episode_id]
    if (spec.duration_seconds!=duration or spec.language!=lang
            or spec.scenes!=_MAX_SCENE_COUNT
            or len(HEADLINES.get(episode_id,()))!=_MAX_SCENE_COUNT):
        _deny()
    target=next(x for x in source["episodes"]
                if x["episode_id"]==episode_id)
    result=[]
    for i,chapter in enumerate(target["segments"]):
        start=chapter["start_second"]
        end=chapter["end_second"]
        if (type(start) is not int or type(end) is not int
                or not 0<=start<end<=duration
                or (result and result[-1].end_second!=start)
                or (not result and start!=0)):
            _deny()
        result.append(SceneCut(i,start*FPS,end*FPS,start,end))
    if (len(result)!=_MAX_SCENE_COUNT or
            result[-1].end_frame!=duration*FPS):
        _deny()
    return tuple(result)


def _checked_ffmpeg(command:list[str],limit_seconds:int)->None:
    try:
        run=subprocess.run(command,stdin=subprocess.DEVNULL,
                           capture_output=True,check=False,
                           timeout=limit_seconds)
    except (OSError,subprocess.TimeoutExpired):
        _deny()
    if run.returncode!=0:
        # Do not echo arbitrary media filesystem paths or codec error text.
        _deny()


def _probe(path:Path,expected_frames:int)->None:
    try:
        run=subprocess.run([
            "ffprobe","-v","error",
            "-show_entries",
            "format=duration:stream=codec_type,codec_name,width,height,nb_frames,avg_frame_rate",
            "-of","json",str(path),
        ],stdin=subprocess.DEVNULL,capture_output=True,check=True,
          timeout=18)
        if len(run.stdout)>12000:
            _deny()
        data=json.loads(run.stdout)
        streams=data["streams"]
        v=streams[0]
        if (len(streams)!=1 or v.get("codec_type")!="video"
                or v.get("codec_name")!="h264"
                or (int(v["width"]),int(v["height"]))!=(WIDTH,HEIGHT)
                or int(v["nb_frames"])!=expected_frames
                or v.get("avg_frame_rate") not in ("24/1","24")
                or abs(float(data["format"]["duration"])-
                       expected_frames/FPS)>.12):
            _deny()
    except (OSError,ValueError,TypeError,KeyError,
            subprocess.CalledProcessError,subprocess.TimeoutExpired):
        _deny()


def render_silent_scene_timeline(
    *,episode_id:str,output_path:Path,
    test_only_first_scene_seconds:int|None=None,
)->dict:
    """Real FFmpeg camera motion across 7 scenes, or 1s QA smoke.

    Outputs are NOT audio-complete or uploadable; do not mark them READY.
    """
    scenes=full_silent_scene_plan(episode_id)
    if (not isinstance(output_path,Path)
            or output_path.suffix.lower()!=".mp4"
            or output_path.exists() or output_path.is_symlink()
            or not output_path.parent.is_dir()
            or output_path.parent.is_symlink()
            or shutil.which("ffmpeg") is None
            or shutil.which("ffprobe") is None
            or (test_only_first_scene_seconds is not None
                and (type(test_only_first_scene_seconds) is not int
                     or test_only_first_scene_seconds!=1))
            or shutil.disk_usage(output_path.parent).free<500_000_000):
        _deny()
    source=load_preview_plan()
    selected=scenes if test_only_first_scene_seconds is None else scenes[:1]
    total_frames=0
    started=time.monotonic()
    try:
        with TemporaryDirectory(
            prefix="fm-oct20-seven-cut-preview-",dir=output_path.parent
        ) as temp:
            root=Path(temp)
            segments=[]
            for scene in selected:
                if time.monotonic()-started>180:
                    _deny()
                png=root/f"scene_{scene.scene_index:02}.png"
                segment=root/f"segment_{scene.scene_index:02}.mp4"
                render_storyboard_keyframe(
                    plan=source,episode_id=episode_id,
                    scene_number=scene.scene_index,output_path=png,
                    width=WIDTH,height=HEIGHT,
                )
                frame_count=(FPS if test_only_first_scene_seconds is not None
                             else scene.end_frame-scene.start_frame)
                # Zoom from an original drawn frame, plus camera movement.
                # Every scene independently maps to authored script duration.
                motion=(
                    "zoompan="
                    "z='min(zoom+0.00035,1.13)':"
                    "x='iw/2-(iw/zoom/2)+7*sin(on/18)':"
                    "y='ih/2-(ih/zoom/2)+7*cos(on/22)':"
                    "d=1:s=432x768:fps=24,"
                    "format=yuv420p"
                )
                _checked_ffmpeg([
                    "ffmpeg","-nostdin","-hide_banner","-v","error","-xerror","-n",
                    "-loop","1","-framerate",str(FPS),"-i",str(png),
                    "-frames:v",str(frame_count),
                    "-vf",motion,"-an","-c:v","libx264",
                    "-pix_fmt","yuv420p","-preset","veryfast",
                    "-crf","24",str(segment),
                ],limit_seconds=100 if frame_count>120 else 40)
                _probe(segment,frame_count)
                segments.append(segment.name)
                total_frames+=frame_count
            playlist=root/"timeline.ffconcat"
            playlist.write_text("ffconcat version 1.0\n"+"".join(
                f"file '{x}'\n" for x in segments),encoding="utf-8")
            _checked_ffmpeg([
                "ffmpeg","-nostdin","-hide_banner","-v","error","-xerror","-n",
                "-safe","1","-f","concat","-i",str(playlist),
                "-an","-c","copy","-movflags","+faststart",
                str(output_path),
            ],limit_seconds=50)
            _probe(output_path,total_frames)
            if (not output_path.is_file()
                    or not 2048<=output_path.stat().st_size<=MAX_OUTPUT_BYTES):
                _deny()
    except BaseException:
        # Do not leave a partially completed preview that could be mistaken
        # for a full-duration item; never overwrite a pre-existing file.
        if output_path.is_file():
            output_path.unlink(missing_ok=True)
        raise
    return {
        "status":"FULL_SCRIPT_SCENE_VISUAL_PREVIEW_SILENT_UNRELEASED",
        "episode_id":episode_id,
        "script_duration_seconds":scenes[-1].end_second,
        "rendered_duration_seconds":total_frames//FPS,
        "exact_script_scene_boundaries_used":True,
        "script_scene_count":len(scenes),
        "rendered_scene_count":len(selected),
        "video_codec":"h264",
        "video_width":WIDTH,
        "video_height":HEIGHT,
        "video_fps":FPS,
        "frame_count":total_frames,
        "audio_track_count":0,
        "entire_silent_visual_timeline_rendered":
            test_only_first_scene_seconds is None,
        "real_cinematic_3d_confirmed":False,
        "spoken_language_verified":False,
        "licensed_narrator_verified":False,
        "speech_to_srt_alignment_verified":False,
        "production_video_ready":False,
        "youtube_upload_authorized":False,
        "youtube_publish_authorized":False,
        "external_network_calls":0,
        "monthly_recurring_infrastructure_inr":0,
    }
