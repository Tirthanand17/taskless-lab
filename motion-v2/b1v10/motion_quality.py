"""Review-only media QA. Thresholds are screening heuristics, not creative approval."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import re

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent
def require(condition,message):
    if not condition: raise ValueError(message)
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()
def sharpness(gray):
    return float(cv2.Laplacian(gray,cv2.CV_64F).var())
def validate_asset(path,record):
    require(record.get("sha256")==sha(path),"asset hash mismatch")
    require(record.get("origin") in ("original","licensed"),"unknown asset origin")
    require(isinstance(record.get("rights_evidence"),str) and record["rights_evidence"].strip(),"missing rights evidence")
    require(record.get("review_only") is True,"no asset release authority")
    with Image.open(path) as im:
        require(im.format in ("PNG","JPEG","WEBP"),"unsupported raster format")
        w,h=im.size
        need=record["display_pixels"]
        require(type(need) is list and len(need)==2 and all(type(n) is int and n>0 for n in need),"bad display dimensions")
        require(w>=need[0] and h>=need[1],"raster upscaling required")
        gray=np.array(im.convert("L"))
    s=sharpness(gray)
    require(s>=25,"low edge-detail review hold")
    return {"dimensions":[w,h],"laplacian_variance":round(s,3),"rights_metadata_present":True,"legal_approval":False}
def motion_stats(frames,fps=30):
    require(len(frames)>=2,"insufficient samples")
    # Frame-wise ROI change; constant backgrounds, captions and brand marks are excluded.
    deltas=[float(np.mean(cv2.absdiff(a,b))) for a,b in zip(frames,frames[1:])]
    longest=run=0
    for d in deltas:
        run=run+1 if d<.06 else 0
        longest=max(longest,run)
    # Compare against previous lags: exact/near-exact recurring ROI can indicate a loop.
    repeats=[]
    for lag in (12,15,20,30):
        if len(frames)<2*lag: continue
        frac=sum(float(np.mean(cv2.absdiff(a,b)))<.10 for a,b in zip(frames[:-lag],frames[lag:]))/(len(frames)-lag)
        repeats.append({"lag_frames":lag,"near_repeat_fraction":round(frac,4)})
    peak=max((x["near_repeat_fraction"] for x in repeats),default=0)
    return {"frames":len(frames),"mean_delta":round(float(np.mean(deltas)),4),
            "max_near_static_seconds":round(longest/fps,3),"loop_candidates":repeats,
            "freeze_review_hold":longest>=fps*.75,"repeat_review_hold":peak>=.8}
def review(path,ffmpeg,out):
    c=cv2.VideoCapture(str(path))
    require(c.isOpened(),"cannot decode")
    try:
        w,h=int(c.get(cv2.CAP_PROP_FRAME_WIDTH)),int(c.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps=c.get(cv2.CAP_PROP_FPS)
        require((w,h)==(1080,1920) and abs(fps-30)<.01,"wrong native canvas/fps")
        frames=[]; samples=[]; edge=[]
        while True:
            ok,frame=c.read()
            if not ok: break
            require(frame.shape[:2]==(h,w),"wrong frame shape")
            i=len(frames)
            roi=cv2.cvtColor(frame[440:1046,72:896],cv2.COLOR_BGR2GRAY)
            frames.append(cv2.resize(roi,(240,176),interpolation=cv2.INTER_AREA))
            if i in (0,30,60,89):
                edge.append(round(sharpness(roi),3))
                samples.append(Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)).resize((270,480),Image.Resampling.LANCZOS))
        require(len(frames)==90,"wrong decoded frame count")
    finally:
        c.release()
    subprocess.run([ffmpeg,"-nostdin","-v","error","-xerror","-i",str(path),"-map","0:v:0","-f","null","-"],check=True)
    stats=motion_stats(frames)
    require(not stats["freeze_review_hold"],"freeze screening hold")
    require(not stats["repeat_review_hold"],"repeat screening hold")
    sheet=Image.new("RGB",(1080,505),"#09131F")
    draw=ImageDraw.Draw(sheet)
    for n,img in enumerate(samples):
        sheet.paste(img,(n*270,25))
        draw.text((n*270+8,5),f"Frame {(0,30,60,89)[n]}",fill="white")
    sheet.save(out/"motion-contact.jpg",quality=94)
    sources=["motion-primitives.tsx","motion-benchmark.tsx","render_motion_review.cjs","motion_quality.py","test_motion_quality.py","EDITORIAL_REVIEW_QA.json","design.json","visual-system.tsx"]
    report={"version":"0.4.0","resolution":[w,h],"fps":fps,"decoded_frames":len(frames),"duration_seconds":len(frames)/fps,
            "mp4_sha256":sha(path),"contact_sha256":sha(out/"motion-contact.jpg"),
            "source_sha256":{s:hashlib.sha256((ROOT/s).read_bytes().replace(b"\r\n",b"\n")).hexdigest() for s in sources},"source_hash_mode":"LF-normalized text","source_raw_sha256":{s:sha(ROOT/s) for s in sources},"decode_pass":True,"hero_roi": [72,440,824,606],
            "motion":stats,"roi_edge_variance_samples":edge,
            "asset_mode":"original code-drawn SVG and CSS, no external raster assets in benchmark",
            "rights_review_approved":False,"human_full_playback_approved":False,"release_authorized":False}
    (out/"MOTION_REVIEW_QA.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("review",type=Path);p.add_argument("--ffmpeg",required=True)
    a=p.parse_args();review(a.review/"motion-v040.mp4",a.ffmpeg,a.review)
if __name__=="__main__":main()
