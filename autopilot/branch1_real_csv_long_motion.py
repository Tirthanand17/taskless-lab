"""Independent real-terminal source pixel audit for landscape long-form.

Not the portrait Shorts threshold: this inspects the genuine 1600x900 X11
recording, excluding subtitles and title bands altogether. No fake motion
or signal that editorial quality / audience retention has been proven.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from autopilot.branch1_real_csv_long import (
    SOURCE,FINAL,RECEIPT,STATUS,LongPilotRefused,need,
)

THRESHOLD_MEAN_DELTA=.18   # 0..255 grayscale, physical real xterm ROI
MAX_STATIC_PAIR_SHARE=.68  # internal engineering screen; not a YT rule
MAX_FROZEN_SECONDS=12.0
REVIEW="LONG_SOURCE_PIXEL_SCREEN_REVIEW_ONLY.json"

def decode_gray(source,frequency,seconds):
    import numpy as np
    cmd=["ffmpeg","-nostdin","-v","error","-i",str(source),
         "-vf",f"fps={frequency},scale=320:180,format=gray",
         "-t",str(seconds),"-f","rawvideo","-"]
    try:
        p=subprocess.run(cmd,capture_output=True,timeout=240)
    except (OSError,subprocess.TimeoutExpired):
        raise LongPilotRefused("REAL_LONG_SOURCE_FRAME_DECODE_FAILED") from None
    need(p.returncode==0 and len(p.stdout)>320*180,
         "INVALID_EXECUTED_LONG_SOURCE_VIDEO_FRAMES")
    size=320*180
    need(len(p.stdout)%size==0,"INVALID_GRAYSCALE_FRAME_BLOCK")
    a=np.frombuffer(p.stdout,dtype=np.uint8).reshape(-1,180,320)
    # XTerm's live editable data area; exclude borders and fake title/caption.
    return a[:,15:160,15:285].astype(np.int16)

def deltas(source,duration):
    import numpy as np
    frames=decode_gray(source,"1/3",duration)
    need(len(frames)>=36,"TOO_FEW_REAL_LONG_FRAMES")
    diff=np.abs(np.diff(frames,axis=0)).mean(axis=(1,2))
    first=decode_gray(source,"1",4.0)
    early=np.abs(np.diff(first,axis=0)).mean(axis=(1,2))
    return diff,early,len(frames)

def audit(folder):
    import numpy as np
    need(folder.is_dir() and not folder.is_symlink(),"UNSAFE_MEDIA_FOLDER")
    receipt_path=folder/RECEIPT
    source=folder/SOURCE
    final=folder/FINAL
    need(receipt_path.is_file() and source.is_file() and final.is_file()
         and not any(p.is_symlink() for p in (receipt_path,source,final))
         and receipt_path.stat().st_size<=6500,
         "MISSING_REAL_LONG_MEDIA_OR_RECEIPT")
    data=json.loads(receipt_path.read_text("utf8"))
    need(data["status"]==STATUS
         and data["schema"]=="FLOWMINUTE_B1_EXECUTED_PYTHON_LONG_V1"
         and data["source_sha256"]==sha256(source.read_bytes()).hexdigest()
         and data["final_sha256"]==sha256(final.read_bytes()).hexdigest()
         and data["true_software_execution"] is True
         and data["fictional_data_only"] is True
         and data["owner_watched"] is False
         and data["publishing_authorized"] is False
         and data["youtube_uploads"]==0
         and data["youtube_schedules"]==0,
         "UNTRUSTED_SOURCE_OR_OWNER_APPROVAL_FORGED")
    duration=float(data["duration_seconds"])
    need(110<=duration<=300,"LONGFORM_DURATION_NOT_AUTHENTIC")
    diff,early,count=deltas(source,duration)
    still=diff<THRESHOLD_MEAN_DELTA
    share=float(np.mean(still))
    longest=0;current=0
    for fixed in still:
        if fixed:
            current+=1
            longest=max(longest,current)
        else:
            current=0
    freeze=longest*3.0
    first_motion=bool(np.any(early>THRESHOLD_MEAN_DELTA))
    risky=(share>MAX_STATIC_PAIR_SHARE
           or freeze>MAX_FROZEN_SECONDS or not first_motion)
    summary={
        "schema":"FLOWMINUTE_B1_LONG_REAL_SOURCE_PIXEL_V1",
        "status":("REJECT_LONG_STATIC_SOURCE" if risky
                  else "PASS_LONG_SOURCE_MOTION_HUMAN_REVIEW_REQUIRED"),
        "source_sha256":data["source_sha256"],
        "final_sha256":data["final_sha256"],
        "source_region":"genuine Python XTerm x15-285_y15-160 downscaled",
        "samples":count,
        "near_static_pair_share":round(share,3),
        "longest_frozen_seconds":round(freeze,1),
        "real_first_three_second_change":first_motion,
        "static_screen_risk":risky,
        "owner_creative_approval":False,
        "youtube_uploads":0,"youtube_schedules":0,
    }
    (folder/REVIEW).write_text(json.dumps(summary,sort_keys=True,indent=2)+"\n","utf8")
    # Real frames only, from the exact final MP4; 16:9 review contact points.
    for idx,t in enumerate((0.5,15.,45.,75.,105.,135.)):
        if t>=duration:break
        target=folder/f"REAL_LONG_FRAME_{idx:02}.png"
        p=subprocess.run(["ffmpeg","-nostdin","-v","error",
            "-ss",str(t),"-i",str(final),"-frames:v","1",
            "-vf","scale=640:360","-y",str(target)],
            capture_output=True,timeout=60)
        need(p.returncode==0 and target.is_file()
             and target.stat().st_size>3000,
             "EXACT_LONG_FRAME_NOT_DECODABLE")
    need(not risky,"REAL_LONG_SOURCE_STATIC_PACING_REFUSED")
    return summary

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    print(json.dumps(audit(p.parse_args().out),sort_keys=True))

if __name__=="__main__":
    main()
