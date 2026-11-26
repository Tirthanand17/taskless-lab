"""RC3: use actual recorded Git console excerpts in long pilot; preserve audio exactly."""
import argparse,hashlib,json,subprocess
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from narration_review import pcm,energy
from sound_mix import measure
D=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def need(ok,msg):
    if not ok:raise ValueError(msg)
# (page, first output frame, end exclusive); retain original diagrams outside these excerpts.
EXCERPTS=[(0,0,90),(1,932,1052),(2,1291,1411),(3,1626,1746),
          (4,1887,1976),(5,2065,2155),(6,2155,2305),(7,3200,3320)]
def main():
    p=argparse.ArgumentParser();p.add_argument("--capture",type=Path,required=True);p.add_argument("--pilot",type=Path,required=True);p.add_argument("--out",type=Path,required=True);p.add_argument("--ffmpeg",required=True);p.add_argument("--verify-existing",action="store_true");a=p.parse_args()
    c=read(a.capture/"GIT_CAPTURE_QA.json");prior=read(D/"LONG_PILOT_QA.json")
    video=a.capture/"ACTUAL_GIT_CONSOLE.mp4"
    need(sha(video)==c["capture_sha256"] and sha(a.pilot)==prior["mp4_sha256"],"input hash mismatch")
    need(c["original_git_evidence_sha256"]==prior["actual_git_evidence_sha256"],"Git evidence mismatch")
    need(c["release_authorized"] is False and c["decoded_frames"]==192 and c["dimensions"]==[870,494],"unexpected capture")
    total=prior["frames"]
    need(all(0<=lo<hi<=total for _,lo,hi in EXCERPTS) and all(x[2]<=y[1] for x,y in zip(EXCERPTS,EXCERPTS[1:])),"bad timeline")
    if not a.verify_existing:a.out.mkdir(parents=True,exist_ok=False)
    filters=["[1:v]split=8"+"".join(f"[c{i}]" for i in range(8))]
    for i,(page,start,end) in enumerate(EXCERPTS):
        next_start=EXCERPTS[i+1][1] if i<7 else total
        count=next_start-start
        filters.append(f"[c{i}]trim=start_frame={page*24}:end_frame={(page+1)*24},setpts=PTS-STARTPTS,fps=30,tpad=stop_mode=clone:stop_duration={count/30:.6f},trim=end_frame={count},setpts=N/(30*TB)[v{i}]")
    filters.append("".join(f"[v{i}]" for i in range(8))+"concat=n=8:v=1:a=0,fps=30,setpts=N/(30*TB)[cap]")
    enabled="+".join(f"between(n,{start},{end-1})" for _,start,end in EXCERPTS)
    filters.append(f"[0:v]drawbox=x=96:y=294:w=1000:h=510:color=0x132536:t=fill:enable='{enabled}'[base]")
    filters.append(f"[base][cap]overlay=160:302:shortest=0:eof_action=repeat:enable='{enabled}'[out]")
    def ff(args):subprocess.run([a.ffmpeg,"-nostdin","-v","error","-y",*map(str,args)],check=True)
    silent=a.out/"silent.mp4";final=a.out/"B1V10_GIT_BISECT_REAL_PROOF_REVIEW.mp4"
    if not a.verify_existing:
        print("Encoding native-HD long video with eight real excerpts",flush=True)
        ff(["-i",a.pilot,"-i",video,"-filter_complex_threads","1","-filter_complex",";".join(filters),"-map","[out]","-an","-frames:v",total,"-c:v","libx264","-preset","ultrafast","-crf","18","-threads","2","-pix_fmt","yuv420p",silent])
        ff(["-i",silent,"-i",a.pilot,"-map","0:v:0","-map","1:a:0","-c","copy","-movflags","+faststart",final])
    print("Full A/V decode and PCM comparison",flush=True)
    ff(["-xerror","-i",final,"-map","0:v:0","-map","0:a:0","-f","null","-"])
    for name,path in [("original",a.pilot),("new",final)]:
        ff(["-i",path,"-map","0:a:0","-ar","48000","-ac","1","-c:a","pcm_s16le",a.out/(name+".wav")])
    x=pcm(a.out/"new.wav");need(len(x)==prior["audio_samples"] and np.array_equal(x,pcm(a.out/"original.wav")),"audio changed")
    cap=cv2.VideoCapture(str(video)); refs={}
    for page,start,end in EXCERPTS:
        cap.set(cv2.CAP_PROP_POS_FRAMES,page*24+12);ok,f=cap.read();need(ok,"source frame missing")
        refs[page]=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY)
    cap.release()
    samples={start+30:page for page,start,end in EXCERPTS}
    samples[550]=None;samples[2700]=None
    cap=cv2.VideoCapture(str(final));w,h=int(cap.get(3)),int(cap.get(4));fps=cap.get(5);i=0;observed=[];stills=[]
    while True:
        ok,f=cap.read()
        if not ok:break
        if i in samples:
            page=samples[i]
            if page is not None:
                roi=cv2.cvtColor(f[302:796,160:1030],cv2.COLOR_BGR2GRAY)
                delta=float(np.mean(cv2.absdiff(roi,refs[page])))
                need(delta<8,"overlay page mismatch "+str(page)+" delta "+str(delta))
                distances={k:float(np.mean(cv2.absdiff(roi,v))) for k,v in refs.items()}
                need(min(distances,key=distances.get)==page,"wrong console page nearest match")
                observed.append({"page":page,"frame":i,"mean_gray_error":round(delta,4),"next_best_error":round(min(v for k,v in distances.items() if k!=page),4)})
            stills.append((i,Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).resize((480,270),Image.Resampling.LANCZOS)))
        i+=1
    cap.release();need((w,h)==(1920,1080) and abs(fps-30)<.01 and i==total and len(observed)==8,"video clock or capture count mismatch")
    sheet=Image.new("RGB",(1440,4*296),"#09131F");draw=ImageDraw.Draw(sheet)
    for j,(k,img) in enumerate(stills):
        xx=j%3*480;yy=j//3*296;sheet.paste(img,(xx,yy+26));draw.text((xx+8,yy+4),f"Frame {k}",fill="white")
    sheet.save(a.out/"real-git-contact.jpg",quality=94)
    report={"version":"1.0.0-rc3","resolution":[w,h],"fps":fps,"frames":i,"duration_seconds":i/fps,"audio_samples":len(x),
            "pcm_identical_to_prior_pilot":True,"audio_energy":energy(x),"encoded_loudness":measure(a.ffmpeg,final),
            "capture_sha256":sha(video),"prior_mp4_sha256":sha(a.pilot),"mp4_sha256":sha(final),"capture_dimensions":c["dimensions"],
            "embedded_dimensions":[870,494],"excerpts":[{"page":p,"start_frame":s,"end_frame":e} for p,s,e in EXCERPTS],
            "excerpt_seconds":sum(e-s for _,s,e in EXCERPTS)/30,"observed_overlay_matches":observed,"full_decode_pass":True,
            "contact_sha256":sha(a.out/"real-git-contact.jpg"),"legacy_capture_validator_pass":False,"creative_policy_full_pass":False,
            "human_playback_approved":False,"release_authorized":False}
    (a.out/"REAL_PROOF_LONG_QA.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");print(json.dumps(report,indent=2))
if __name__=="__main__":main()
