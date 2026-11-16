"""Branch 1 independent real-pixel motion/readability screening.

Read-only analysis of the EXACT already-rendered, unapproved first-party
Short. Masks captions/header and measures change in application-screen pixels.
Cannot establish viewer satisfaction, app correctness, owner approval or upload.
No credentials, network, source-media downloads or YouTube calls.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import subprocess

FORMAT="FLOWMINUTE_B1_EXACT_VISUAL_MOTION_SCREEN_V1"
PREVIEW_STATUS="B1_REAL_APP_NARRATED_VIDEO_REQUIRES_HUMAN_REVIEW_NO_YOUTUBE"
HEX64=re.compile(r"[0-9a-f]{64}\Z")
MIN_BYTES=250_000
MAX_BYTES=240_000_000
MAX_SECONDS=64
W,H=80,100
FPS=2
FRAME_BYTES=W*H
# The central ROI excludes upper chapter headers and lower captions.
CROP="crop=860:1100:110:175,scale=80:100:flags=fast_bilinear,fps=2,format=gray"
# Internal review heuristics, not an official YouTube threshold.
NEAR_STILL_DELTA=0.75
MAX_STATIC_SECONDS=3.0
MAX_STATIC_SHARE=.45
MIN_VISUAL_CONTRAST=9.0

class ScreenAuditRefused(ValueError):
    """Untrusted or unreviewable media."""

def need(ok,why):
    if not ok:
        raise ScreenAuditRefused(why)

def sh(path:Path):
    need(path.is_file() and not path.is_symlink(),"NONREGULAR_MEDIA")
    h=hashlib.sha256()
    with path.open("rb") as fp:
        for block in iter(lambda:fp.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def inspect_receipt(receipt:Path,media:Path)->dict:
    need(receipt.is_file() and not receipt.is_symlink()
         and receipt.stat().st_size<12000,"UNSAFE_NARRATED_RECEIPT")
    need(media.is_file() and not media.is_symlink()
         and MIN_BYTES<=media.stat().st_size<=MAX_BYTES,
         "UNSAFE_OR_MISSING_EXACT_RENDER")
    r=json.loads(receipt.read_text("utf8"))
    need(type(r) is dict
         and r.get("schema")=="FLOWMINUTE_B1_NARRATED_REAL_APP_V1"
         and r.get("status")==PREVIEW_STATUS
         and r.get("app") in ("calc","chrome")
         and r.get("real_recording_pixel_source") is True
         and r.get("postencoded_audio_verified") is True
         and r.get("owner_final_watch") is False
         and r.get("release_signed") is False
         and type(r.get("youtube_uploads")) is int
         and r["youtube_uploads"]==0
         and type(r.get("youtube_schedules")) is int
         and r["youtube_schedules"]==0
         and type(r.get("narrated_mp4_sha256")) is str
         and HEX64.fullmatch(r["narrated_mp4_sha256"])
         and type(r.get("narrated_mp4_bytes")) is int
         and r["narrated_mp4_bytes"]==media.stat().st_size
         and sh(media)==r["narrated_mp4_sha256"],
         "RECEIPT_MEDIA_OR_RIGHTS_BINDING_FAILED")
    return r

def _run(cmd, *, timeout=120, text=True):
    try:
        result=subprocess.run(cmd,capture_output=True,text=text,
                              timeout=timeout,check=False)
    except (OSError,subprocess.TimeoutExpired):
        raise ScreenAuditRefused("LOCAL_MEDIA_TOOL_MISSING_OR_TIMED_OUT") from None
    need(result.returncode==0,"FFMPEG_READ_ONLY_ANALYSIS_FAILED")
    return result.stdout

def check_streams(media:Path)->float:
    metadata=json.loads(_run([
        "ffprobe","-v","error","-show_entries",
        "stream=codec_type,codec_name,width,height:format=duration",
        "-of","json",str(media)],timeout=25))
    tracks=metadata.get("streams",[])
    vid=[t for t in tracks if t.get("codec_type")=="video"]
    aud=[t for t in tracks if t.get("codec_type")=="audio"]
    need(len(vid)==1 and len(aud)==1 and
         vid[0].get("codec_name")=="h264" and
         aud[0].get("codec_name")=="aac" and
         vid[0].get("width")==1080 and vid[0].get("height")==1920,
         "WRONG_NARRATED_SHORT_MEDIA_STREAMS")
    length=float(metadata["format"]["duration"])
    need(math.isfinite(length) and 20<=length<=MAX_SECONDS,
         "MEDIA_TOO_SHORT_OR_LONG")
    return length

def plane_score(planes:list[bytes], duration:float)->dict:
    """Measure actual visible application ROI, ignoring narration/caption pixels."""
    need(type(planes) is list and 30<=len(planes)<=MAX_SECONDS*FPS+3
         and all(type(x) is bytes and len(x)==FRAME_BYTES for x in planes)
         and type(duration) in (float,int)
         and math.isfinite(duration) and 20<=duration<=MAX_SECONDS,
         "TRUNCATED_OR_MALFORMED_PIXEL_SERIES")
    contrast=[statistics.pstdev(frame) for frame in planes]
    mean_contrast=statistics.median(contrast)
    deltas=[]
    for previous,current in zip(planes,planes[1:]):
        # Exact grayscale pixel-change averages mask static cloned frames.
        deltas.append(sum(abs(a-b) for a,b in zip(previous,current))/FRAME_BYTES)
    stationary=[value<=NEAR_STILL_DELTA for value in deltas]
    longest=0
    current=0
    for frozen in stationary:
        current=current+1 if frozen else 0
        longest=max(longest,current)
    static_share=sum(stationary)/len(stationary)
    first_3s_has_motion=any(x>NEAR_STILL_DELTA for x in deltas[:6])
    no_app_visual=mean_contrast<MIN_VISUAL_CONTRAST
    long_pause=longest/FPS>MAX_STATIC_SECONDS
    excessive_static=static_share>MAX_STATIC_SHARE
    return {
        "frames_sampled":len(planes),"fps":FPS,
        "center_application_roi":"x110-970_y175-1275_ignores_chapter_and_caption_bands",
        "median_grayscale_contrast":round(mean_contrast,2),
        "mean_interframe_change":round(statistics.mean(deltas),3),
        "static_frame_pair_share":round(static_share,3),
        "longest_near_frozen_seconds":round(longest/FPS,2),
        "first_three_seconds_show_visible_change":first_3s_has_motion,
        "high_risk_static_pacing":bool(long_pause or excessive_static or
                                       no_app_visual or not first_3s_has_motion),
        "reasons":(
            (["POSSIBLE_BLANK_OR_LOW_CONTRAST_APPLICATION"] if no_app_visual else [])+
            (["LONG_FROZEN_APPLICATION_PIXELS"] if long_pause else [])+
            (["EXCESSIVE_STATIC_PIXEL_COVERAGE"] if excessive_static else [])+
            (["NO_CHANGE_IN_FIRST_THREE_SECONDS"] if not first_3s_has_motion else [])
        ),
    }

def audit(media:Path,receipt:Path)->dict:
    metadata=inspect_receipt(receipt,media)
    length=check_streams(media)
    need(abs(length-float(metadata["duration_seconds"]))<.6,
         "SIGNED_DURATION_DOES_NOT_MATCH_ENCODED_VIDEO")
    raw=_run(["ffmpeg","-nostdin","-v","error",
              "-i",str(media),"-map","0:v:0","-an",
              "-vf",CROP,"-pix_fmt","gray","-f","rawvideo","pipe:1"],
             timeout=180,text=False)
    need(len(raw)%FRAME_BYTES==0 and
         30<=len(raw)//FRAME_BYTES<=MAX_SECONDS*FPS+3,
         "DECODED_VISUAL_SAMPLES_INVALID")
    samples=[raw[i:i+FRAME_BYTES] for i in range(0,len(raw),FRAME_BYTES)]
    score=plane_score(samples,length)
    return {
        "schema":FORMAT,
        "status":("CREATIVE_REWORK_REQUIRED_DO_NOT_RELEASE"
                  if score["high_risk_static_pacing"] else
                  "MOTION_SCREEN_PASS_STILL_HUMAN_REVIEW_REQUIRED"),
        "app":metadata["app"],
        "video_sha256":metadata["narrated_mp4_sha256"],
        "duration_seconds":round(length,3),
        "visual_screening":score,
        "interpretation":(
            "Pixel motion alone cannot prove a good hook, readability, "
            "legitimate rights or viewer satisfaction. A human MUST watch "
            "the exact final video in full and compare to its narrated claims."
        ),
        "owner_review_complete":False,
        "publish_or_schedule_authorized":False,
        "youtube_uploads":0,"youtube_schedules":0,
    }

def export_frames(media:Path,duration:float,folder:Path):
    """Extract contact key frames from actual MP4. No mock screenshots."""
    need(folder.is_dir() and 20<=duration<=64,"UNSAFE_STORYBOARD_OUTPUT")
    seconds=(0.6,2.6,6.0,round(duration*.45,2),
             round(duration*.72,2),round(duration-2,2))
    for i,s in enumerate(seconds):
        target=folder/f"REAL_MOBILE_REVIEW_{i+1:02}.png"
        _run(["ffmpeg","-nostdin","-v","error","-ss",str(s),
              "-i",str(media),"-frames:v","1","-vf",
              "scale=324:576:flags=bicubic","-y",str(target)],
             timeout=30)
        need(target.is_file() and 2000<target.stat().st_size<5_000_000,
             "MISSING_ACTUAL_MOBILE_FRAME")
    return seconds

def main():
    parser=argparse.ArgumentParser(description="Offline, no-upload visual check")
    parser.add_argument("--mp4",type=Path,required=True)
    parser.add_argument("--receipt",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    need(not args.out.exists(),"REFUSE_OVERWRITE_VISUAL_REPORT")
    args.out.mkdir(mode=0o700,parents=True)
    result=audit(args.mp4,args.receipt)
    export_frames(args.mp4,result["duration_seconds"],args.out)
    (args.out/"REAL_VISUAL_CREATIVE_REVIEW.json").write_text(
        json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
