"""Phase 3R4: actual visual-signal sampling of ORIGINAL silent CSV videos.

This is NOT semantic/human visual review. Verify real video pixels across
the full authored timeline; catch blank, frozen, or almost unchanging visual
scenes that mere codec/duration QA cannot detect. Never mark media publishable.

No network, voice provider, accounts, large stored artifacts, or media output.
Only reads a preexisting local MP4 using installed FFmpeg/FFprobe, with strict
bounded 160x90 or 90x160 RGB frame reads and <=26 fixed sample moments.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import math
import subprocess

from .agent_org import WorkflowError

EPISODES = {
    "csv_tutorial_short_en": (42,1080,1920,24,1008),
    "csv_tutorial_short_hi": (42,1080,1920,24,1008),
    "csv_tutorial_long_hi": (432,1920,1080,24,10368),
}
MAX_MEDIA_BYTES=150_000_000
MAX_PROBE_CHARS=16_384
MAX_THUMB_BYTES=160*160*3


def _sample_times(episode_id: str) -> tuple[float,...]:
    if episode_id not in EPISODES:
        raise WorkflowError("Unrecognized or unreviewed original video")
    if episode_id=="csv_tutorial_long_hi":
        # All 24 authored 18-second long beats, plus edge checks.
        return (0.5,)+(tuple(i*18+9.0 for i in range(24)))+(431.5,)
    return (0.5,10.5,20.5,30.5,41.5)


def _probe(path:Path) -> tuple[int,int,int,float,float]:
    try:
        p=subprocess.run(
            ["ffprobe","-v","error","-show_entries",
             "stream=codec_type,codec_name,width,height,nb_frames,avg_frame_rate:"
             "format=duration","-of","json",str(path)],
            input=None,capture_output=True,text=True,timeout=20,check=True)
        if len(p.stdout)>MAX_PROBE_CHARS:
            raise WorkflowError("Excessive FFprobe output")
        obj=json.loads(p.stdout)
        streams=obj["streams"]
        if len(streams)!=1 or streams[0].get("codec_type")!="video":
            raise WorkflowError("Visual audit only accepts one silent video stream")
        v=streams[0]
        if v.get("codec_name")!="h264":
            raise WorkflowError("Visual audit requires original H.264")
        w,h,frames=(int(v[k]) for k in ("width","height","nb_frames"))
        rate=v["avg_frame_rate"].split("/")
        fps=float(rate[0])/float(rate[1]) if len(rate)==2 else float(rate[0])
        return w,h,frames,fps,float(obj["format"]["duration"])
    except (OSError,TypeError,ValueError,KeyError,ZeroDivisionError,
            subprocess.TimeoutExpired,subprocess.CalledProcessError) as exc:
        raise WorkflowError("Actual video cannot be probed") from exc


def _thumb(path:Path,second:float, *,width:int,height:int) -> bytes:
    if not isinstance(second,(int,float)) or not math.isfinite(second) or second<0:
        raise WorkflowError("Invalid authored visual sample time")
    # Strong bounds: rawvideo RGB thumbnail, fixed dimensions and one frame.
    cmd=[
        "ffmpeg","-nostdin","-v","error","-xerror",
        "-ss",f"{second:.3f}","-i",str(path),
        "-frames:v","1","-vf",f"scale={width}:{height}:flags=bilinear",
        "-f","rawvideo","-pix_fmt","rgb24","pipe:1",
    ]
    try:
        p=subprocess.run(cmd,stdin=subprocess.DEVNULL,capture_output=True,
                         check=True,timeout=30)
        expected=width*height*3
        if len(p.stdout)!=expected or len(p.stdout)>MAX_THUMB_BYTES:
            raise WorkflowError("Missing or invalid bounded visual sample")
        return p.stdout
    except (OSError,subprocess.CalledProcessError,subprocess.TimeoutExpired) as exc:
        raise WorkflowError("Could not decode one authored scene frame") from exc


def analyze_rgb_samples(samples:tuple[bytes,...], *,
                        width:int,height:int) -> dict:
    """Evaluate bounded actual RGB frames. A PASS is signal-only, not content."""
    if (type(width)is not int or type(height)is not int or
            width<=0 or height<=0 or width*height>160*160 or
            not isinstance(samples,tuple) or not 2<=len(samples)<=26):
        raise WorkflowError("Invalid sample geometry or collection")
    expected=width*height*3
    if any(not isinstance(s,bytes) or len(s)!=expected for s in samples):
        raise WorkflowError("Raw RGB sample length or type wrong")
    levels=[]
    flat=[]
    dark=[]
    hashes=[]
    for frame in samples:
        hashes.append(sha256(frame).hexdigest())
        # Fast bounded calculations, no unbounded image libraries or
        # external model/VLM API calls. Quantities are pixel statistics.
        n=len(frame)//3
        l=[(frame[i]+frame[i+1]+frame[i+2])/3
           for i in range(0,len(frame),3)]
        mean=sum(l)/n
        contrast=math.sqrt(sum((x-mean)**2 for x in l)/n)
        nearblack=sum(1 for x in l if x<9)/n
        levels.append(round(mean,2))
        flat.append(round(contrast,2))
        dark.append(round(nearblack,5))
    adjacent=[]
    for prev,current in zip(samples,samples[1:]):
        mean_abs=sum(abs(a-b) for a,b in zip(prev,current))/len(prev)
        adjacent.append(round(mean_abs,3))
    issues=[]
    if any(x>=0.995 for x in dark):
        issues.append("BLANK_BLACK_SCENE_SAMPLE")
    if any(x<5 for x in flat):
        issues.append("VERY_LOW_CONTRAST_SCENE_SAMPLE")
    if len(set(hashes))<len(samples):
        issues.append("DUPLICATE_EXACT_SCENE_SAMPLES")
    if any(x<1.0 for x in adjacent):
        issues.append("NEAR_STATIC_ACROSS_ADJACENT_SAMPLED_SCENES")
    return {
        "status":("VISUAL_SIGNAL_QA_PASS_UNPUBLISHABLE"
                  if not issues else "VISUAL_SIGNAL_QA_REVIEW_REQUIRED"),
        "issues":issues,
        "sample_count":len(samples),
        "mean_luminance":levels,
        "contrast_stddev":flat,
        "nearblack_fraction":dark,
        "adjacent_mean_absolute_rgb_change":adjacent,
        "sample_sha256":hashes,
        "human_visual_review_observed":False,
        "actual_caption_legibility_verified":False,
        "factual_csv_explanation_verified":False,
        "voice_or_sound_verified":False,
        "commercial_media_rights_verified":False,
        "real_photo_or_3d_quality_verified":False,
        "youtube_publishing_authorized":False,
    }


def inspect_authored_visual_signal(*,episode_id:str, path:Path)->dict:
    """Probe entire HD video, seek fixed scene representative frames.

    Each result is technical/review-only. Never a media release approval.
    """
    if episode_id not in EPISODES:
        raise WorkflowError("Unknown original episode")
    p=Path(path)
    if (p.is_symlink() or not p.is_file() or p.suffix!=".mp4"
            or not 2048<=p.stat().st_size<=MAX_MEDIA_BYTES):
        raise WorkflowError("Bounded existing ordinary original MP4 required")
    duration,w,h,fps,frames=EPISODES[episode_id]
    pw,ph,pn,pr,pt=_probe(p)
    if ((pw,ph,pn)!=(w,h,frames) or abs(pr-fps)>0.01
            or abs(pt-duration)>0.12):
        raise WorkflowError("Video metadata does not match authored native HD episode")
    scale=(90,160) if w<h else (160,90)
    frame_data=tuple(_thumb(p,second,width=scale[0],height=scale[1])
                     for second in _sample_times(episode_id))
    analyzed=analyze_rgb_samples(frame_data,width=scale[0],height=scale[1])
    return {
        "episode_id":episode_id,
        "actual_frame_samples_decoded":True,
        "sample_timestamps_s":_sample_times(episode_id),
        "verified_full_video_metadata":True,
        "status":analyzed["status"],
        "issues":analyzed["issues"],
        "visual_signal":analyzed,
        "full_video_semantics_approved":False,
        "speech_approved":False,
        "third_party_rights_approved":False,
        "publishing_authorized":False,
        "network_calls":0,
    }
