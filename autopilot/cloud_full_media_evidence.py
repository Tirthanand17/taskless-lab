"""Offline, read-only FULL-DURATION H.264/AAC evidence intake.

Produces technical, SHA-256-bound observations from an EXISTING file only.
FFprobe counts every video frame and FFmpeg decodes all video AND audio.
No recording, media generation, network, tokens, rights verification, or
upload; no data or secrets are copied to a public artifact.

Timing and peak-RAM are still operator-asserted, and codec conformance never
establishes narration naturalness, captions, consent, or legal media rights.
Nothing in this module can make production publishing eligible.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json
import math
import stat
import subprocess

from .agent_org import WorkflowError
from .cloud_capacity_admission import (
    FPS,LANES,FullLengthTrial,ZeroRupeeCapacity,evaluate_capacity,
)

MAX_PROBE_CHARS=16_384
MAX_DECODE_OUTPUT_CHARS=8192
MAX_SHORT_BYTES=600_000_000
MAX_LONG_BYTES=4_000_000_000
MAX_INPUT_FRAME_DURATION_SLACK_S=0.40
MAX_RENDER_WALL_SECONDS=86_400
MAX_PEAK_MIB=65_536
SPEC={x.lane:x for x in LANES}


@dataclass(frozen=True)
class TechnicalFullHDObservation:
    lane:str
    video_sha256:str
    video_bytes:int
    frames_decoded_or_counted:int
    width:int
    height:int
    container_duration_s:float
    video_codec:str
    audio_codec:str
    whole_media_ffmpeg_decode_passed:bool
    render_wall_seconds_claimed:float
    peak_memory_mib_claimed:int
    observed_at:datetime
    original_file_unchanged_after_inspection:bool
    signed_by_independent_reviewer:bool=False
    natural_narration_verified:bool=False
    speech_caption_alignment_verified:bool=False
    third_party_license_authenticated:bool=False
    publishing_authorized:bool=False


def _sha_file(path:Path,*,limit:int)->tuple[str,int,int,int]:
    try:
        info=path.lstat()
    except OSError as exc:
        raise WorkflowError("Media source missing or unreadable") from exc
    if (not stat.S_ISREG(info.st_mode) or path.is_symlink()
            or info.st_size<2048 or info.st_size>limit):
        raise WorkflowError("Only bounded ordinary full-length files are accepted")
    h=sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda:handle.read(1024*1024),b""):
                h.update(chunk)
        after=path.lstat()
    except OSError as exc:
        raise WorkflowError("Media bytes became unavailable") from exc
    if ((info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns)
            !=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)):
        raise WorkflowError("Media file changed during hashing")
    return h.hexdigest(),info.st_size,info.st_dev,info.st_ino


def _run_bounded(argv:list[str],*,seconds:int):
    try:
        result=subprocess.run(
            argv,stdin=subprocess.DEVNULL,capture_output=True,
            text=True,timeout=seconds,check=False,
        )
    except (OSError,subprocess.TimeoutExpired,UnicodeError) as exc:
        raise WorkflowError("Local media inspection failed or timed out") from exc
    if (result.returncode!=0
            or len(result.stdout)>MAX_PROBE_CHARS
            or len(result.stderr)>MAX_DECODE_OUTPUT_CHARS):
        raise WorkflowError("Media inspector failed or produced oversized output")
    return result


def _extract_streams(payload:str,*,lane:str)->tuple[int,float]:
    spec=SPEC[lane]
    try:
        object_=json.loads(payload)
        if not isinstance(object_,dict):
            raise ValueError("Not a JSON object")
        streams=object_["streams"]
        if not isinstance(streams,list) or len(streams)!=2:
            raise ValueError("Expected one audio plus one video stream")
        video=[x for x in streams if isinstance(x,dict)
               and x.get("codec_type")=="video"]
        audio=[x for x in streams if isinstance(x,dict)
               and x.get("codec_type")=="audio"]
        if len(video)!=1 or len(audio)!=1:
            raise ValueError("Missing or duplicated audio/video")
        v,a=video[0],audio[0]
        frames=int(v["nb_read_frames"])
        width=int(v["width"])
        height=int(v["height"])
        rate=Fraction(v["avg_frame_rate"])
        nominal_rate=Fraction(v["r_frame_rate"])
        container_seconds=float(object_["format"]["duration"])
        if (v.get("codec_name")!="h264" or a.get("codec_name")!="aac"
                or width!=spec.width or height!=spec.height
                or rate!=FPS or nominal_rate!=FPS
                or frames!=spec.duration_s*FPS
                or not math.isfinite(container_seconds)
                or abs(container_seconds-spec.duration_s)
                    >MAX_INPUT_FRAME_DURATION_SLACK_S):
            raise ValueError("Not an exact native-HD whole-length H264/AAC video")
    except (KeyError,ValueError,TypeError,OverflowError,ZeroDivisionError) as exc:
        raise WorkflowError("Full-length stream/frame evidence invalid") from exc
    return frames,container_seconds


def inspect_full_length_media(lane:str,existing_video:Path, *,
                              claimed_render_seconds:float,
                              claimed_peak_ram_mib:int,
                              measured_at:datetime)->TechnicalFullHDObservation:
    """Observe an existing FULL native-HD asset; never write a new one."""
    if not isinstance(lane,str) or lane not in SPEC:
        raise WorkflowError("Unknown full-HD production lane")
    if (type(claimed_render_seconds) not in (float,int)
            or not math.isfinite(claimed_render_seconds)
            or not 0<claimed_render_seconds<=MAX_RENDER_WALL_SECONDS
            or type(claimed_peak_ram_mib) is not int
            or not 0<claimed_peak_ram_mib<=MAX_PEAK_MIB
            or not isinstance(measured_at,datetime)
            or measured_at.tzinfo is None
            or measured_at.utcoffset() is None):
        raise WorkflowError("Missing bounded operator resource measurements")
    file=Path(existing_video)
    if not file.is_absolute():
        raise WorkflowError("Full-media inspector requires existing absolute file")
    limit=(MAX_SHORT_BYTES if lane.startswith("short_") else MAX_LONG_BYTES)
    digest,bytes_before,dev,inode=_sha_file(file,limit=limit)
    probe=_run_bounded([
        "ffprobe","-v","error","-count_frames",
        "-show_entries",
        "stream=codec_type,codec_name,width,height,avg_frame_rate,r_frame_rate,nb_read_frames:format=duration",
        "-of","json","-i",str(file),
    ],seconds=70)
    frames,duration=_extract_streams(probe.stdout,lane=lane)
    # Decode every stream rather than relying exclusively on container
    # metadata; any decoding failure vetoes this technical observation.
    decode=_run_bounded([
        "ffmpeg","-nostdin","-v","error","-xerror",
        "-i",str(file),"-map","0:v:0","-map","0:a:0",
        "-f","null","-",
    ],seconds=240 if lane.startswith("short_") else 900)
    if decode.stderr.strip():
        raise WorkflowError("Full A/V decode emitted errors")
    again,count,newdev,newinode=_sha_file(file,limit=limit)
    if (again!=digest or count!=bytes_before or newdev!=dev
            or newinode!=inode):
        raise WorkflowError("Media mutated or was swapped during inspection")
    spec=SPEC[lane]
    return TechnicalFullHDObservation(
        lane=lane,video_sha256=digest,video_bytes=bytes_before,
        frames_decoded_or_counted=frames,width=spec.width,height=spec.height,
        container_duration_s=duration,video_codec="h264",audio_codec="aac",
        whole_media_ffmpeg_decode_passed=True,
        render_wall_seconds_claimed=claimed_render_seconds,
        peak_memory_mib_claimed=claimed_peak_ram_mib,
        observed_at=measured_at,
        original_file_unchanged_after_inspection=True,
    )


def evaluate_observed_media_capacity(
    observations:tuple[TechnicalFullHDObservation,...],
    capacity:ZeroRupeeCapacity|None,*,now:datetime)->dict:
    """Bind observed hashes to draft capacity, but keep all editorial vetoes."""
    if not isinstance(observations,tuple) or len(observations)>len(LANES):
        raise WorkflowError("Bounded immutable technical observations required")
    seen=set()
    trials=[]
    checksums={}
    for obs in observations:
        if not isinstance(obs,TechnicalFullHDObservation):
            raise WorkflowError("Typed video technical observation required")
        if obs.lane not in SPEC or obs.lane in seen:
            raise WorkflowError("Unknown/duplicated observed media lane")
        seen.add(obs.lane)
        spec=SPEC[obs.lane]
        if (not isinstance(obs.video_sha256,str)
                or len(obs.video_sha256)!=64
                or any(x not in "0123456789abcdef" for x in obs.video_sha256)
                or type(obs.video_bytes) is not int
                or obs.video_bytes<2048
                or obs.frames_decoded_or_counted!=spec.duration_s*FPS
                or (obs.width,obs.height)!=(spec.width,spec.height)
                or obs.whole_media_ffmpeg_decode_passed is not True
                or obs.original_file_unchanged_after_inspection is not True
                or obs.publishing_authorized is not False
                or obs.natural_narration_verified is not False
                or obs.speech_caption_alignment_verified is not False
                or obs.third_party_license_authenticated is not False
                or obs.signed_by_independent_reviewer is not False):
            raise WorkflowError("Invalid or falsely approved technical evidence")
        checksums[obs.lane]=obs.video_sha256
        trials.append(FullLengthTrial(
            lane=obs.lane,duration_s=spec.duration_s,
            frames=obs.frames_decoded_or_counted,
            width=obs.width,height=obs.height,
            wall_seconds=obs.render_wall_seconds_claimed,
            final_bytes=obs.video_bytes,
            peak_memory_mib=obs.peak_memory_mib_claimed,
            video_codec=obs.video_codec,audio_codec=obs.audio_codec,
            full_decode_passed=True,
            narration_and_caption_qa_passed=False,
            rights_review_passed=False,
            measured_at=obs.observed_at,
        ))
    report=evaluate_capacity(tuple(trials),capacity,now=now)
    return {
        **report,
        "technical_video_sha256_by_lane":checksums,
        "technical_evidence_read_only":True,
        "operator_render_time_and_ram_not_independently_attested":True,
        "audio_language_or_voice_identity_verified":False,
        "independent_license_review_verified":False,
        "signed_media_editorial_reviews_present":False,
        "full_hd_publishing_capacity_verified":False,
        "youtube_upload_authorized":False,
        "publishing_authorized":False,
    }
