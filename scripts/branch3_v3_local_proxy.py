"""Bounded local measurement adapter for normalized, private MP4 proxies.

This is a compute primitive, not a source acquisition or rights authorization.
Caller must supply independently approved private input in production; only
self-generated inputs are exercised by public CI. No external CLI or URL input.
Reject unsupported timelines instead of silently inventing samples.
"""
from __future__ import annotations

import array
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from fractions import Fraction

from scripts.branch3_v3_multimodal_candidates import CHANNEL, INPUT_STATE, PROFILES, validate

W,H,FPS,RATE=160,90,2,8000
FRAME_BYTES=W*H
BIN_MS=500
HOP=RATE//FPS
CHUNK_BINS=120
MAX_BYTES=3*1024**3


def need(ok,code):
    if not ok:
        raise ValueError("CLIVOX_V3_PROXY_"+code)


def invoke(args, limit, timeout=90):
    result=subprocess.run(args,stdin=subprocess.DEVNULL,capture_output=True,check=True,timeout=timeout)
    need(len(result.stdout)<=limit,"OUTPUT_BOUND")
    return result.stdout


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f,"sha256").hexdigest()


def measure_local_proxy(path, profile):
    """Read normalized zero-origin, one-video/one-audio MP4; no network or writes."""
    need(isinstance(path,Path) and path.is_absolute() and path.is_file()
         and not path.is_symlink() and path.resolve()==path
         and path.suffix.lower()==".mp4" and 128<=path.stat().st_size<=MAX_BYTES,"LOCAL_PROXY")
    need(type(profile) is str and profile in PROFILES,"PROFILE")
    before=sha(path)
    detail=json.loads(invoke(["ffprobe","-v","error","-protocol_whitelist","file",
                              "-show_streams","-show_format","-of","json",str(path)],64000))
    streams=detail["streams"]
    need(len(streams)==2,"EXACT_AV")
    v=next((s for s in streams if s["codec_type"]=="video"),None)
    a=next((s for s in streams if s["codec_type"]=="audio"),None)
    need(v is not None and a is not None and v["codec_name"]=="h264"
         and a["codec_name"]=="aac" and v.get("pix_fmt")=="yuv420p"
         and 16<=v["width"]<=3840 and 16<=v["height"]<=2160,"CODECS")
    try:
        vd,ad=float(v["duration"]),float(a["duration"])
        rate=Fraction(v["avg_frame_rate"])
        size=int(detail["format"]["size"])
        duration=float(detail["format"]["duration"])
        starts=[float(s["start_time"]) for s in (v,a)]
    except (KeyError,ValueError,TypeError,ZeroDivisionError,OverflowError):
        raise ValueError("CLIVOX_V3_PROXY_TIMEBASE") from None
    need(all(math.isfinite(x) for x in [vd,ad,duration,*starts]) and
         all(abs(x)<.025 for x in starts) and abs(vd-ad)<=.05
         and abs(duration-vd)<=.05 and 20<=duration<=7200 and 2<=rate<=120
         and size==path.stat().st_size,"NORMALIZED_TIMELINE_REQUIRED")
    # Only full 500ms bins are supported; reject a partial tail in this
    # initial adapter rather than fabricate data or silently drop duration.
    bins=round(duration*2)
    need(abs(duration-bins/2)<=.025,"NORMALIZE_PARTIAL_BIN_FIRST")
    rms,motion,cuts=[],[],[]
    previous=None
    for offset in range(0,bins,CHUNK_BINS):
        n=min(CHUNK_BINS,bins-offset)
        prefix=["ffmpeg","-v","error","-nostdin","-protocol_whitelist","file",
                "-ss",str(offset/2),"-i",str(path),"-t",str(n/2)]
        gray=invoke(prefix+["-map","0:v:0","-an","-vf",
                             f"fps=2,scale={W}:{H},format=gray",
                             "-f","rawvideo","pipe:1"],n*FRAME_BYTES)
        pcm=invoke(prefix+["-map","0:a:0","-vn","-ac","1","-ar",str(RATE),
                            "-f","s16le","pipe:1"],n*HOP*2)
        need(len(gray)==n*FRAME_BYTES and len(pcm)==n*HOP*2,"DECODE_TIMEBASE")
        samples=array.array("h");samples.frombytes(pcm)
        if sys.byteorder!="little":samples.byteswap()
        for i in range(n):
            chunk=samples[i*HOP:(i+1)*HOP]
            rms.append(min(32767,round(math.sqrt(sum(s*s for s in chunk)/HOP))))
            frame=gray[i*FRAME_BYTES:(i+1)*FRAME_BYTES]
            if previous is None:
                motion.append(0)
            else:
                delta=sum(abs(x-y) for x,y in zip(previous,frame))/FRAME_BYTES
                if delta>=45:
                    cuts.append((offset+i)*BIN_MS)
                    motion.append(0)
                else:
                    motion.append(round(delta*10000/255))
            previous=frame
    need(sha(path)==before,"INPUT_CHANGED")
    doc={"schema_version":1,"channel_id":CHANNEL,"state":INPUT_STATE,
         "profile":profile,"duration_ms":bins*BIN_MS,"step_ms":BIN_MS,
         "audio_rms":rms,"motion":motion,"scene_cuts_ms":cuts,
         "semantic_events_ms":None,"editor_marks_ms":None}
    validate(doc)
    return doc
