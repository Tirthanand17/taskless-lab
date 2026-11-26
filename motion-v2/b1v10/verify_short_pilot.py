"""Verify the complete B1v10 SHA-256 pilot against its locked narration and mix."""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
from narration_review import pcm, energy
from motion_quality import motion_stats
from sound_mix import measure
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,msg):
    if not ok:raise ValueError(msg)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory",type=Path);p.add_argument("--mix",type=Path,required=True);p.add_argument("--ffmpeg",required=True)
    a=p.parse_args();d=a.directory
    n=json.loads((ROOT/"NARRATION_REVIEW_QA.json").read_text(encoding="utf-8"))
    m=json.loads((ROOT/"SOUND_MIX_QA.json").read_text(encoding="utf-8"))
    c=json.loads((ROOT/"CAPTION_CORRECTION_QA.json").read_text(encoding="utf-8"))
    need(sha(a.mix)==m["artifacts_sha256"]["mix.m4a"],"mix changed")
    need(sha(ROOT/"word_captions_review.json")==c["corrected_word_captions_sha256"],"captions changed")
    silent=d/"silent.mp4";final=d/"B1V10_SHA256_SHORT_REVIEW.mp4"
    subprocess.run([a.ffmpeg,"-nostdin","-v","error","-y","-i",str(silent),"-i",str(a.mix),"-map","0:v:0","-map","1:a:0","-c","copy","-movflags","+faststart",str(final)],check=True)
    subprocess.run([a.ffmpeg,"-nostdin","-v","error","-xerror","-i",str(final),"-map","0:v:0","-map","0:a:0","-f","null","-"],check=True)
    decoded=d/"final-audio.wav"
    subprocess.run([a.ffmpeg,"-nostdin","-v","error","-y","-i",str(final),"-map","0:a:0","-ar","48000","-ac","1","-c:a","pcm_s16le",str(decoded)],check=True)
    x=pcm(decoded)
    need(len(x)==n["samples"],"audio clock changed")
    reference=d/"reference-audio.wav"
    subprocess.run([a.ffmpeg,"-nostdin","-v","error","-y","-i",str(a.mix),"-map","0:a:0","-ar","48000","-ac","1","-c:a","pcm_s16le",str(reference)],check=True)
    need(np.array_equal(x,pcm(reference)),"decoded PCM differs from reviewed mix")
    cap=cv2.VideoCapture(str(final))
    need(cap.isOpened(),"cannot decode video")
    w,h=int(cap.get(3)),int(cap.get(4));fps=cap.get(5)
    need((w,h)==(1080,1920) and abs(fps-30)<.01,"native resolution/fps")
    samples=sorted(set([0,24,60,71,155,156,180,213,214,230,232,300,353,354,382,383,416,417,500,580]))
    # Store hero ROI only, at 240px wide, to avoid RAM overhead on laptop.
    rois=[]; stills={};i=0
    while True:
        ok,frame=cap.read()
        if not ok:break
        roi=frame[440:1046,72:896]
        rois.append(cv2.resize(cv2.cvtColor(roi,cv2.COLOR_BGR2GRAY),(240,176),interpolation=cv2.INTER_AREA))
        if i in samples:
            stills[i]=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
        i+=1
    cap.release()
    need(i==n["frames_at_30fps"],"incorrect decoded frame count")
    need(set(stills)==set(samples),"missing inspection frames")
    # The 3-second benchmark's threshold is a review signal, not an automatic
    # creative pass/fail for full scenes with intentional reading holds.
    stats=[]
    for scene in n["scene_timeline"]:
        r=motion_stats(rois[scene["start_frame"]:scene["end_frame"]])
        stats.append({"scene":scene["id"],**r})
    sheet=Image.new("RGB",(5*216,4*408),"#09131f");draw=ImageDraw.Draw(sheet)
    for j,k in enumerate(samples):
        im=stills[k].resize((216,384),Image.Resampling.LANCZOS);x0=j%5*216;y0=j//5*408
        sheet.paste(im,(x0,y0+24));draw.text((x0+6,y0+5),f"Frame {k} / {k/30:.2f}s",fill="white")
    sheet.save(d/"short-contact.jpg",quality=94)
    events=[]
    for e in m["events"]:
        f=e["frame"]; before=rois[f-1];after=rois[f]
        delta=float(np.mean(cv2.absdiff(before,after)))
        # Visual change at the intended frame is directly observed; it is not
        # a human perception or audio latency measurement.
        events.append({**e,"hero_frame_delta":round(delta,4)})
    report={"version":"0.7.0","resolution":[w,h],"fps":fps,"decoded_frames":i,
        "duration_seconds":i/fps,"audio_samples":len(pcm(decoded)),"audio_identical_to_mix_decode":True,
        "full_av_decode_pass":True,"loudness":measure(a.ffmpeg,final),"audio_energy":energy(pcm(decoded)),
        "scene_motion":stats,"planned_event_frame_observations":events,
        "contact_frames":samples,"contact_sha256":sha(d/"short-contact.jpg"),"mp4_sha256":sha(final),
        "source_sha256":{k:sha(ROOT/k) for k in ("short-pilot.tsx","render_short_pilot.cjs","verify_short_pilot.py","SOUND_MIX_QA.json","NARRATION_REVIEW_QA.json","word_captions_review.json")},
        "owner_full_video_approved":False,"human_mix_listening_approved":False,"release_authorized":False}
    (d/"SHORT_PILOT_QA.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()
