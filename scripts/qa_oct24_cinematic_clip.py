"""Independent, local cinematic clip inspection (not a provider or YouTube client).

Inspects real MP4 bytes before FlowMinute accepts an 8s shot. Decoding, black/
freeze tests cannot establish quality, likeness, license, or provenance.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import argparse
import json
import re
import subprocess

LABELS={"asha_jay_opening","cinematic_02","cinematic_03","cinematic_04"}
SAFE_NAME=re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,120}\.mp4")
FREEZE_START=re.compile(r"freeze_start:\s*([0-9.]+)")
FREEZE_END=re.compile(r"freeze_end:\s*([0-9.]+)")
CODECS={"h264","hevc","av1","vp9"}


def command(args, timeout=130):
    return subprocess.run(args,capture_output=True,text=True,timeout=timeout,check=False)


def freeze_periods(stderr, duration):
    starts=[float(x) for x in FREEZE_START.findall(stderr)]
    ends=[float(x) for x in FREEZE_END.findall(stderr)]
    return [(a, ends[i] if i<len(ends) else duration)
            for i,a in enumerate(starts)]


def inspect(path: Path, label: str) -> dict:
    if label not in LABELS:
        raise ValueError("Unknown cinematic shot label")
    result={
        "scene_id":label,"file_name":path.name,
        "status":"BLOCKED","issues":[],
        "real_premium_3d_human_approved":False,
        "characters_match_opening_human_approved":False,
        "motion_and_props_human_approved":False,
        "rights_verified":False,
        "source_authenticated":False,
        "ready_to_publish":False,"youtube_scheduled":False,
    }
    errors=result["issues"]
    if path.is_symlink() or not path.is_file() or not SAFE_NAME.fullmatch(path.name):
        errors.append("MISSING_OR_UNSAFE_MP4")
        return result
    size=path.stat().st_size
    if not 100_000<=size<=250_000_000:
        errors.append("MEDIA_SIZE_NOT_VALID")
        return result
    digest=sha256()
    with path.open("rb") as fh:
        for part in iter(lambda:fh.read(1024*1024),b""):
            digest.update(part)
    result.update(sha256=digest.hexdigest(),size_bytes=size)
    p=command(["ffprobe","-v","error","-show_entries",
       "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
       "-of","json",str(path)])
    if p.returncode:
        errors.append("FFPROBE_FAILED")
        return result
    try:
        meta=json.loads(p.stdout)
        vids=[x for x in meta["streams"] if x.get("codec_type")=="video"]
        auds=[x for x in meta["streams"] if x.get("codec_type")=="audio"]
        assert len(vids)==1 and len(auds)<=1
        v=vids[0]
        width,height=int(v["width"]),int(v["height"])
        a,b=map(int,v["r_frame_rate"].split("/"))
        fps=a/b
        duration=float(meta["format"]["duration"])
    except (ValueError,ZeroDivisionError,KeyError,TypeError,AssertionError):
        errors.append("INVALID_VIDEO_METADATA")
        return result
    result.update(duration_seconds=round(duration,3),resolution=[width,height],
                  fps=round(fps,2),video_codec=v["codec_name"],
                  contains_audio=bool(auds))
    if not 7.65<=duration<=8.55:
        errors.append("NOT_AN_EIGHT_SECOND_SHOT")
    if min(width,height)<540 or abs(width/height-9/16)>.025:
        errors.append("NOT_VERTICAL_9_16")
    if not 23<=fps<=60:
        errors.append("UNUSABLE_FRAME_RATE")
    if v["codec_name"] not in CODECS:
        errors.append("UNUSABLE_CODEC")
    decode=command(["ffmpeg","-hide_banner","-nostdin","-v","error","-xerror",
                    "-i",str(path),"-f","null","-"])
    if decode.returncode:
        errors.append("FULL_VIDEO_OR_AUDIO_DECODE_FAILED")
    freeze=command(["ffmpeg","-hide_banner","-nostdin","-i",str(path),
                    "-vf","freezedetect=n=-55dB:d=0.75","-an","-f","null","-"])
    if freeze.returncode:
        errors.append("FROZEN_FRAME_INSPECTION_FAILED")
    else:
        spans=freeze_periods(freeze.stderr,duration)
        result["freeze_intervals"]=[[round(a,3),round(b,3)] for a,b in spans]
        if any(b-a>=1.1 for a,b in spans):
            errors.append("VISUAL_STATIC_OVER_1_1_SECONDS")
    if not errors:
        result["status"]="TECHNICAL_PASS_AWAITING_HUMAN_CINEMATIC_REVIEW"
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--file",type=Path,required=True)
    p.add_argument("--scene",required=True,choices=sorted(LABELS))
    p.add_argument("--report",type=Path,required=True)
    args=p.parse_args()
    if args.report.exists() or not args.report.parent.is_dir():
        raise SystemExit("Report must be a new path in an existing directory")
    result=inspect(args.file,args.scene)
    args.report.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    if result["issues"]:
        raise SystemExit(2)


if __name__=="__main__":
    main()
