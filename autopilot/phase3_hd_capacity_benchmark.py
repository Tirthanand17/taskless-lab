"""FlowMinute 3R3: bounded native-HD capacity measurement on public CI.

Runs exactly three ORIGINAL 1-second 24fps silent scenes at 1080x1920 or
1920x1080, chosen from the actual authored CSV scripts. Measures end-to-end
wall time, runner memory high-water and H264 output size; verifies actual video
frame counts/decoding; deletes no files outside the supplied existing folder.

Never extrapolate one second into a factual assertion that 42/432 second
full-HD production is sustainable. Does not create voice/music, use paid
services, fetch a model, open accounts, store artifacts or authorize publishing.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
import resource
import shutil
import subprocess
import time

from .agent_org import WorkflowError
from .phase3_csv_visual_preview import render_visual_preview
from .phase3_hindi_visual_preview import render_hindi_visual_preview


@dataclass(frozen=True)
class HDCase:
    episode_id: str
    source_duration_s: int
    width: int
    height: int
    offset_s: int
    output_basename: str


CASES = (
    HDCase("csv_tutorial_short_en", 42, 1080, 1920, 22,
           "hd-capacity-English-Short-visual-only.mp4"),
    HDCase("csv_tutorial_short_hi", 42, 1080, 1920, 31,
           "hd-capacity-Hindi-Short-visual-only.mp4"),
    HDCase("csv_tutorial_long_hi", 432, 1920, 1080, 254,
           "hd-capacity-Hindi-long-visual-only.mp4"),
)
FPS=24
SAMPLE_DURATION_S=1
MAX_OUTPUT_BYTES=25_000_000
MAX_BENCHMARK_SECONDS=160
MAX_MEDIA_PROBE_TEXT=20000


def analyze_hd_samples(samples: list[dict]) -> dict:
    """Deterministic arithmetic only; NO production feasibility attestation."""
    if not isinstance(samples,list) or len(samples)!=len(CASES):
        raise WorkflowError("Exactly three bounded HD measurements required")
    provided={s.get("episode_id"):s for s in samples
              if isinstance(s,dict)}
    if set(provided)!={x.episode_id for x in CASES} or len(provided)!=len(samples):
        raise WorkflowError("Unknown, duplicated or missing HD episodes")
    measured=[]
    linear_runtime_s=0.0
    linear_storage_bytes=0.0
    for spec in CASES:
        rec=provided[spec.episode_id]
        try:
            secs=rec["render_wall_seconds"]
            byte_count=rec["output_bytes"]
            count=rec["frame_count"]
            width=rec["width"]
            height=rec["height"]
            no_audio=rec["audio_stream_count"]==0
        except KeyError as exc:
            raise WorkflowError("Incomplete HD render measurement") from exc
        if (type(secs) not in (float,int) or not math.isfinite(secs)
                or not 0<secs<=MAX_BENCHMARK_SECONDS
                or type(byte_count) is not int or not 2048<=byte_count<=MAX_OUTPUT_BYTES
                or type(count) is not int or count!=FPS
                or type(width) is not int or width!=spec.width
                or type(height) is not int or height!=spec.height
                or not no_audio):
            raise WorkflowError("Invalid bounded full-HD video measurement")
        linear_runtime_s+=secs*spec.source_duration_s
        linear_storage_bytes+=byte_count*spec.source_duration_s
        measured.append({
            "episode_id":spec.episode_id,
            "format":f"{spec.width}x{spec.height}",
            "source_duration_seconds":spec.source_duration_s,
            "sample_offset_seconds":spec.offset_s,
            "sample_frames":count,
            "render_wall_seconds":round(secs,3),
            "effective_render_fps":round(FPS/secs,2),
            "output_sample_bytes":byte_count,
            "sample_size_kib":round(byte_count/1024,1),
        })
    return {
        "status":"HD_SAMPLE_MEASURED_FULL_LENGTH_CAPACITY_NOT_PROVEN",
        "sample_count":len(measured),
        "samples":measured,
        # Compression scene variance, disk, codec, CPU contention, font
        # shaping and fresh CI runner variance make these extrapolations
        # UNRELIABLE. They are not go/no-go measurements.
        "naive_linear_render_seconds_UNVALIDATED":round(linear_runtime_s,1),
        "naive_linear_media_megabytes_UNVALIDATED":round(
            linear_storage_bytes/1_000_000,1),
        "warning":"1 second snapshots cannot prove full 42s or 432s HD capacity, costs or video quality",
        "full_hd_daily_batch_capacity_verified":False,
        "sustained_zero_cost_verified":False,
        "voice_naturalness_verified":False,
        "speech_subtitle_sync_verified":False,
        "high_quality_3d_verified":False,
        "youtube_upload_authorized":False,
        "publishing_authorized":False,
        "network_calls":0,
        "new_paid_service_connected":False,
    }


def _inspect_video(path:Path, *, case:HDCase)->dict:
    cmd=["ffprobe","-v","error","-show_entries",
         "stream=codec_type,codec_name,width,height,nb_frames:format=duration",
         "-of","json",str(path)]
    try:
        probe=subprocess.run(cmd,stdin=subprocess.DEVNULL,
                             capture_output=True,text=True,check=True,timeout=25)
        if len(probe.stdout)>MAX_MEDIA_PROBE_TEXT:
            raise WorkflowError("Excessive metadata returned from FFprobe")
        data=json.loads(probe.stdout)
        streams=data["streams"]
        vid=[s for s in streams if s.get("codec_type")=="video"]
        aud=[s for s in streams if s.get("codec_type")=="audio"]
        duration=float(data["format"]["duration"])
        if (len(streams)!=1 or len(vid)!=1 or aud
                or vid[0].get("codec_name")!="h264"
                or int(vid[0]["width"])!=case.width
                or int(vid[0]["height"])!=case.height
                or int(vid[0]["nb_frames"])!=FPS
                or abs(duration-SAMPLE_DURATION_S)>0.15):
            raise WorkflowError("HD proof codec, frames, duration or audio invalid")
        decoded=subprocess.run(
            ["ffmpeg","-nostdin","-v","error","-xerror","-i",str(path),
             "-f","null","-"],
            stdin=subprocess.DEVNULL,capture_output=True,timeout=60)
        if decoded.returncode:
            raise WorkflowError("Original H264 HD scene failed full decode")
    except (ValueError,KeyError,TypeError,OSError,subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as exc:
        raise WorkflowError("HD technical video QA failed") from exc
    return {
        "episode_id":case.episode_id,
        "frame_count":int(vid[0]["nb_frames"]),
        "width":case.width,"height":case.height,
        "audio_stream_count":len(aud),
        "duration_seconds":duration,
    }


def run_hd_capacity_benchmark(folder:Path)->dict:
    """The ONLY runner entry point. No background or external execution."""
    destination=Path(folder)
    if (not destination.is_dir() or destination.is_symlink()
            or not shutil.which("ffmpeg") or not shutil.which("ffprobe")):
        raise WorkflowError("Pre-existing ordinary scratch folder and FFmpeg required")
    outputs=[destination/c.output_basename for c in CASES]
    if any(p.exists() or p.is_symlink() for p in outputs):
        raise WorkflowError("Refuse to overwrite any measured video or symlink")
    samples=[]
    try:
        for case,path in zip(CASES,outputs):
            start=time.perf_counter()
            if case.episode_id=="csv_tutorial_short_en":
                render_visual_preview(path,duration_s=SAMPLE_DURATION_S,
                                      fps=FPS,width=case.width,start_s=case.offset_s)
            else:
                render_hindi_visual_preview(
                    case.episode_id,path,duration_s=SAMPLE_DURATION_S,
                    fps=FPS,width=case.width,start_s=case.offset_s)
            elapsed=time.perf_counter()-start
            size=path.stat().st_size
            if not 2048<=size<=MAX_OUTPUT_BYTES:
                raise WorkflowError("Unexpected oversized or missing output")
            probe=_inspect_video(path,case=case)
            probe.update({
                "render_wall_seconds":elapsed,
                "output_bytes":size,
            })
            samples.append(probe)
        analysis=analyze_hd_samples(samples)
        # Resource maxrss is a process high water, not a sum nor a precise
        # per-scene live RAM profile. Report parent and child separately.
        analysis["runner_python_peak_rss_mib_upper_observed"]=round(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,1)
        analysis["runner_child_peak_rss_mib_upper_observed"]=round(
            resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss/1024,1)
        analysis["memory_note"]="Parent and child process high-water marks, not simultaneous system RAM total"
        analysis["all_three_real_h264_hd_scenes_decoded"]=True
        analysis["media_durable_storage_created"]=False
        return analysis
    finally:
        for f in outputs:
            f.unlink(missing_ok=True)


def main() -> int:
    import argparse
    p=argparse.ArgumentParser(description="Bounded three-video HD render measurement")
    p.add_argument("--existing-scratch-dir",required=True,type=Path)
    args=p.parse_args()
    result=run_hd_capacity_benchmark(args.existing_scratch_dir)
    print(json.dumps(result,sort_keys=True,separators=(",",":")))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
