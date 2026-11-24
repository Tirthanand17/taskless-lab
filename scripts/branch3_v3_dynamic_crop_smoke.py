"""Generated moving-object detection, crop path compilation and decoded QA.

Uses original test shapes only. Does not pretend a shape is a human face or
speaker. The generic crop expression is bound to validated keyframes.
"""
from __future__ import annotations

import json
from pathlib import Path
import tempfile

from scripts.branch3_v3_subject_crop_plan import crop_plan
from scripts.branch3_v3_vertical_render_smoke import run, need
from scripts.branch3_v2_p5_synthetic_moment_proposals import _probe_closed

W,H,FPS,SECONDS=640,360,24,4


def expression(points, axis):
    """Linear interpolation with even pixel alignment, hold final keyframe."""
    need(bool(points) and axis in ("x","y"),"KEYFRAMES")
    tail=str(points[-1][axis])
    for p,q in reversed(list(zip(points,points[1:]))):
        a,b=p["time_ms"]/1000,q["time_ms"]/1000
        need(b>a,"KEYFRAME_ORDER")
        tail=f"if(lt(t,{b:g}),{p[axis]}+({q[axis]}-{p[axis]})*(t-{a:g})/{b-a:g},{tail})"
    return f"2*floor(({tail})/2)"


def detect_fixture_box(frame):
    """Threshold the known white test shape; never treat as face confidence."""
    points=[(i%W,i//W) for i,p in enumerate(frame) if p>200]
    if not points:
        return []
    xs,ys=zip(*points)
    return [[min(xs),min(ys),max(xs)-min(xs)+1,max(ys)-min(ys)+1,1000]]


def smoke():
    _probe_closed()
    with tempfile.TemporaryDirectory(prefix="clivox-v3-tracking-") as root:
        folder=Path(root)
        with (folder/"frames.gray").open("wb") as f:
            for i in range(FPS*SECONDS):
                x=80+3*i
                frame=bytearray([24])*(W*H)
                for y in range(130,230):
                    frame[y*W+x:y*W+x+64]=bytes([235])*64
                f.write(frame)
        run(["ffmpeg","-v","error","-nostdin","-f","rawvideo","-pixel_format","gray",
             "-video_size",f"{W}x{H}","-framerate",str(FPS),"-i","frames.gray",
             "-c:v","libx264","-threads:v","1","-pix_fmt","yuv420p","source.mp4"],folder)
        raw=run(["ffmpeg","-v","error","-i","source.mp4","-vf","fps=2,format=gray",
                 "-f","rawvideo","pipe:1"],folder,W*H*8)
        need(len(raw)==W*H*8,"FRAME_COUNT")
        samples=[{"time_ms":i*500,"boxes":detect_fixture_box(raw[i*W*H:(i+1)*W*H])}
                 for i in range(8)]
        plan=crop_plan(W,H,SECONDS*1000,[{"start_ms":0,"end_ms":SECONDS*1000,"samples":samples}])
        shot=plan["shots"][0]
        need(shot["mode"]=="tracked_crop","TRACKED_PLAN")
        cw,ch=shot["crop_size"]
        x,y=(expression(shot["keyframes"],k) for k in ("x","y"))
        filt=f"crop={cw}:{ch}:x='{x}':y='{y}',scale=1080:1920,setsar=1"
        run(["ffmpeg","-v","error","-nostdin","-i","source.mp4","-vf",filt,
             "-c:v","libx264","-threads:v","2","-preset","ultrafast","-pix_fmt","yuv420p",
             "tracked.mp4"],folder)
        pixels=run(["ffmpeg","-v","error","-i","tracked.mp4","-vf","fps=2,scale=108:192,format=gray",
                    "-f","rawvideo","pipe:1"],folder,108*192*8)
        need(len(pixels)==108*192*8,"CROP_FRAMES")
        # Decode all sampled output frames and ensure the full bright object
        # remains within the safe central area. No claim between samples.
        for i in range(8):
            frame=pixels[i*108*192:(i+1)*108*192]
            points=[(j%108,j//108) for j,v in enumerate(frame) if v>200]
            need(len(points)>900,"SUBJECT_PIXEL_AREA")
            xs,ys=zip(*points)
            need(min(xs)>=4 and max(xs)<=103 and min(ys)>=4 and max(ys)<=187,"SUBJECT_VISIBILITY")
        _probe_closed()
        return {"generated_only":True,"samples_verified":8,"dynamic_crop_rendered":True,
                "real_face_tracking_verified":False,"speaker_tracking_verified":False,
                "production_ready":False,"youtube_upload_authorized":False}


if __name__=="__main__":
    print(json.dumps(smoke(),sort_keys=True))
