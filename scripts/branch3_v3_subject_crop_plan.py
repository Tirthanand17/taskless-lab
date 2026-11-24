"""Pure shot-aware subject crop planning from unverified box observations.

No detector, recognition, media I/O, credentials or release. Fall back to
contain when observation coverage, ambiguity or subject visibility is unsafe.
"""
from __future__ import annotations

import math


def need(ok, reason):
    if not ok:
        raise ValueError("CLIVOX_V3_CROP_" + reason)


def crop_plan(width, height, duration_ms, shots):
    need(type(width) is int and type(height) is int and
         16<=width<=7680 and 16<=height<=4320 and width%2==height%2==0,"SIZE")
    need(type(duration_ms) is int and 0<duration_ms<=180000,"DURATION")
    need(type(shots) is list and 0<len(shots)<=180,"SHOTS")
    expected=0
    result=[]
    # Largest even exact 9:16 crop that fits both dimensions.
    unit=min(width//9,height//16)//2*2
    cw,ch=9*unit,16*unit
    need(unit>=2,"CROP_SIZE")
    for shot in shots:
        need(type(shot) is dict and set(shot)=={"start_ms","end_ms","samples"},"SHOT_FIELDS")
        a,b,samples=shot["start_ms"],shot["end_ms"],shot["samples"]
        need(type(a) is int and type(b) is int and expected==a<b<=duration_ms,"SHOT_TIMING")
        need(type(samples) is list and len(samples)<=1000,"SAMPLES")
        expected=b
        prev=a-1
        frames=[]
        for sample in samples:
            need(type(sample) is dict and set(sample)=={"time_ms","boxes"},"SAMPLE")
            t,boxes=sample["time_ms"],sample["boxes"]
            need(type(t) is int and prev<t<b and t>=a,"SAMPLE_TIME")
            need(type(boxes) is list and len(boxes)<=8,"BOXES")
            prev=t
            valid=[]
            for box in boxes:
                need(type(box) is list and len(box)==5 and all(type(v) is int for v in box),"BOX")
                x,y,w,h,confidence=box
                need(x>=0 and y>=0 and w>0 and h>0 and x+w<=width and y+h<=height
                     and 0<=confidence<=1000,"BOX_BOUNDS")
                if confidence>=650:
                    valid.append((x,y,w,h))
            frames.append((t,valid))
        reason=None
        if not frames or frames[0][0]!=a or b-frames[-1][0]>500 or any(
                t2-t1>500 for (t1,_),(t2,_) in zip(frames,frames[1:])):
            reason="INSUFFICIENT_COVERAGE"
        elif any(len(v)!=1 for _,v in frames):
            reason="MISSING_OR_AMBIGUOUS_SUBJECT"
        points=[]
        if reason is None:
            for t,boxes in frames:
                x,y,w,h=boxes[0]
                # Keep margin on both sides where source boundaries permit.
                margin_x=max(2,cw//20)
                margin_y=max(2,ch//20)
                left=max(0,x-margin_x); right=min(width,x+w+margin_x)
                top=max(0,y-margin_y); bottom=min(height,y+h+margin_y)
                lo_x=max(0,right-cw); hi_x=min(width-cw,left)
                lo_y=max(0,bottom-ch); hi_y=min(height-ch,top)
                lo_x=(lo_x+1)//2*2; lo_y=(lo_y+1)//2*2
                hi_x=hi_x//2*2; hi_y=hi_y//2*2
                if lo_x>hi_x or lo_y>hi_y:
                    reason="SUBJECT_TOO_LARGE"
                    break
                ideal_x=(x+w//2-cw//2)//2*2
                ideal_y=(y+h//2-ch//2)//2*2
                if points:
                    p=points[-1]
                    dt=t-p["time_ms"]
                    # Avoid jitter and cap motion to half the crop dimension per second.
                    dx=max(2,(cw*dt//2000)//2*2)
                    dy=max(2,(ch*dt//2000)//2*2)
                    lo_x=max(lo_x,p["x"]-dx); hi_x=min(hi_x,p["x"]+dx)
                    lo_y=max(lo_y,p["y"]-dy); hi_y=min(hi_y,p["y"]+dy)
                    if lo_x>hi_x or lo_y>hi_y:
                        reason="UNSAFE_FAST_MOTION"
                        break
                    if abs(ideal_x-p["x"])<cw//20: ideal_x=p["x"]
                    if abs(ideal_y-p["y"])<ch//20: ideal_y=p["y"]
                points.append({"time_ms":t,"x":min(hi_x,max(lo_x,ideal_x)),
                               "y":min(hi_y,max(lo_y,ideal_y))})
        item={"start_ms":a,"end_ms":b,"mode":"fit" if reason else "tracked_crop",
              "fallback_reason":reason,"crop_size":None if reason else [cw,ch],
              "keyframes":[] if reason else points,
              "operator_review_required":True}
        result.append(item)
    need(expected==duration_ms,"COMPLETE_TIMELINE")
    return {"stage":"UNVERIFIED_SUBJECT_OBSERVATION_CROP_PLAN","output":[1080,1920],
            "shots":result,"interpolation_verified":False,"speaker_verified":False,
            "render_authorized":False,"youtube_upload_authorized":False}
