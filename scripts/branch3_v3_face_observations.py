"""Optional local OpenCV single-face observation baseline.

A face detection is neither identity nor active-speaker evidence. Keep all
detected faces (including ambiguity); never choose largest as a speaker.
Caller is responsible for approved media access. No network or public CLI.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import math
import subprocess

from scripts.branch3_v3_subject_crop_plan import crop_plan


def need(ok,code):
    if not ok:
        raise ValueError("CLIVOX_V3_FACE_"+code)


def observed_boxes(gray, classifier, width, height):
    """Convert qualified detector regions, not calibrated probabilities."""
    h,w=gray.shape
    found=classifier.detectMultiScale(gray,scaleFactor=1.1,minNeighbors=6,minSize=(24,24))
    result=[]
    for x,y,bw,bh in found:
        left=int(x)*width//w
        top=int(y)*height//h
        right=math.ceil((int(x)+int(bw))*width/w)
        bottom=math.ceil((int(y)+int(bh))*height/h)
        need(0<=left<right<=width and 0<=top<bottom<=height,"BOUNDS")
        result.append([left,top,right-left,bottom-top,650])
    # The value 650 is a nominal qualified-observation marker to satisfy
    # crop_plan's contract, not a probability or measured detector confidence.
    return result if len(result)<=8 else []


def observe_local_clip(path, width, height, start_ms, end_ms, cut_times_ms=()):
    """Optional CPU-only detector for an already approved normalized proxy."""
    import cv2
    import numpy as np
    need(isinstance(path,Path) and path.is_absolute() and path.is_file()
         and not path.is_symlink() and path.resolve()==path and path.suffix.lower()==".mp4","FILE")
    need(type(width) is int and type(height) is int and 16<=width<=3840
         and 16<=height<=2160 and width%2==height%2==0,"DIMENSIONS")
    need(type(start_ms) is int and type(end_ms) is int and
         0<=start_ms<end_ms<=7200000 and end_ms-start_ms<=55000,"TIME")
    # Round observations to the planner grid; non-grid clips fall back rather
    # than approximate scene boundaries across an unsupported timebase.
    duration=end_ms-start_ms
    cuts=list(cut_times_ms)
    need(all(type(x) is int and 0<x<duration and x%500==0 for x in cuts)
         and cuts==sorted(set(cuts)) and duration%500==0,"NORMALIZED_GRID")
    cascade=Path(cv2.data.haarcascades)/"haarcascade_frontalface_default.xml"
    need(cascade.is_file(),"CASCADE")
    classifier=cv2.CascadeClassifier(str(cascade))
    need(not classifier.empty(),"CASCADE_LOAD")
    # Aspect-preserving bounded analysis frame.
    w=min(width,480)
    h=max(2,round(height*w/width))
    if h>480:
        h=480;w=max(2,round(width*h/height))
    n=duration//500
    result=subprocess.run(["ffmpeg","-v","error","-nostdin","-protocol_whitelist","file",
                           "-ss",str(start_ms/1000),"-i",str(path),"-t",str(duration/1000),
                           "-map","0:v:0","-an","-vf",f"fps=2,scale={w}:{h},format=gray",
                           "-f","rawvideo","pipe:1"],
                          capture_output=True,stdin=subprocess.DEVNULL,check=True,timeout=90)
    need(len(result.stdout)==n*w*h,"FRAME_COUNT")
    frames=np.frombuffer(result.stdout,dtype=np.uint8).reshape(n,h,w)
    samples=[{"time_ms":i*500,"boxes":observed_boxes(frame,classifier,width,height)}
             for i,frame in enumerate(frames)]
    edges=[0,*cuts,duration]
    shots=[{"start_ms":a,"end_ms":b,"samples":[s for s in samples if a<=s["time_ms"]<b]}
           for a,b in zip(edges,edges[1:])]
    plan=crop_plan(width,height,duration,shots)
    return {"stage":"UNVERIFIED_OPENCV_FACE_OBSERVATIONS","opencv_version":cv2.__version__,
            "cascade_sha256":hashlib.sha256(cascade.read_bytes()).hexdigest(),
            "sample_count":n,"samples_with_face":sum(bool(s["boxes"]) for s in samples),
            "plan":plan,"active_speaker_verified":False,"render_authorized":False,
            "youtube_upload_authorized":False}


def generated_negative_smoke():
    """Actual classifier on non-face generated shapes. No positive face benchmark."""
    import tempfile
    from scripts.branch3_v3_generated_media_smoke import fixture
    from scripts.branch3_v2_p5_synthetic_moment_proposals import _probe_closed
    _probe_closed()
    with tempfile.TemporaryDirectory(prefix="clivox-v3-face-negative-") as root:
        source=fixture(Path(root)).resolve()
        result=observe_local_clip(source,160,90,0,4000)
        need(result["samples_with_face"]==0 and result["plan"]["shots"][0]["mode"]=="fit",
             "NEGATIVE_FALLBACK")
        return result
