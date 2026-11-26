"""RC2: insert actual console recording into existing narrated Short, review only."""
import argparse,hashlib,json,subprocess
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from narration_review import pcm,energy
from sound_mix import measure
D=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,msg):
    if not ok:raise ValueError(msg)
def main():
    p=argparse.ArgumentParser();p.add_argument("--capture",type=Path,required=True);p.add_argument("--pilot",type=Path,required=True);p.add_argument("--out",type=Path,required=True);p.add_argument("--ffmpeg",required=True);a=p.parse_args()
    c=read(a.capture/"CAPTURE_QA.json");s=read(D/"SHORT_PILOT_QA.json");n=read(D/"NARRATION_REVIEW_QA.json")
    source=a.capture/"ACTUAL_SHA256_CONSOLE.mp4"
    need(sha(source)==c["capture_sha256"] and sha(a.pilot)==s["mp4_sha256"],"source hash mismatch")
    need(c["capture_method"]=="windows_classic_console_window_only_live" and c["release_authorized"] is False,"invalid capture provenance")
    need(c["dimensions"][0]>=720 and c["dimensions"][1]>=570,"insufficient native capture")
    cap=cv2.VideoCapture(str(source));changes=[];last=None;i=0
    while True:
        ok,f=cap.read()
        if not ok:break
        g=cv2.resize(cv2.cvtColor(f,cv2.COLOR_BGR2GRAY),(160,120))
        if last is not None and float(np.mean(cv2.absdiff(g,last)))>.8:changes.append(i)
        last=g;i+=1
    cap.release()
    need(i==120 and len(changes)==3,"unexpected capture state sequence")
    # Map observed live state changes to the original audio-derived scene boundaries.
    cuts=[0,*changes,120]
    dest=[0,*[x["start_frame"] for x in n["scene_timeline"][1:]],581]
    a.out.mkdir(parents=True,exist_ok=False);final=a.out/"B1V10_SHA256_REAL_PROOF_REVIEW.mp4"
    filters=["[1:v]split=4"+"".join(f"[c{i}]" for i in range(4))]
    for i in range(4):
        count=dest[i+1]-dest[i];length=cuts[i+1]-cuts[i]
        # Map exact captured samples to constant-rate output with an explicit terminal hold.
        factor=count/30/(length/12)
        filters.append(f"[c{i}]trim=start_frame={cuts[i]}:end_frame={cuts[i+1]},setpts=(PTS-STARTPTS)*{factor:.12f},fps=30,tpad=stop_mode=clone:stop_duration=1,trim=end_frame={count},setpts=PTS-STARTPTS[v{i}]")
    filters.append("".join(f"[v{i}]" for i in range(4))+"concat=n=4:v=1:a=0,scale=720:572:flags=lanczos,setsar=1[capture]")
    # Keep existing typography, captions and proof panel. No capture upscaling.
    filters.append("[0:v]drawbox=x=72:y=440:w=824:h=606:color=0x132536:t=fill[base];[base][capture]overlay=124:457:shortest=0:eof_action=repeat[out]")
    def ff(args):subprocess.run([a.ffmpeg,"-nostdin","-v","error",*map(str,args)],check=True)
    ff(["-i",a.pilot,"-i",source,"-filter_complex_threads","1","-filter_complex",";".join(filters),"-map","[out]","-an","-frames:v","581","-c:v","libx264","-preset","fast","-crf","18","-threads","2","-pix_fmt","yuv420p","-movflags","+faststart",a.out/"silent.mp4"])
    ff(["-i",a.out/"silent.mp4","-i",a.pilot,"-map","0:v:0","-map","1:a:0","-c","copy","-movflags","+faststart",final])
    ff(["-xerror","-i",final,"-map","0:v:0","-map","0:a:0","-f","null","-"])
    for label,path in [("reference",a.pilot),("new",final)]:
        ff(["-i",path,"-map","0:a:0","-ar","48000","-ac","1","-c:a","pcm_s16le",a.out/(label+".wav")])
    x=pcm(a.out/"new.wav");ref=pcm(a.out/"reference.wav")
    need(len(x)==929600 and np.array_equal(x,ref),"audio changed")
    cap=cv2.VideoCapture(str(final));w,h=int(cap.get(3)),int(cap.get(4));fps=cap.get(5);i=0;images=[]
    samples=[0,60,71,155,232,300,383,500]
    while True:
        ok,f=cap.read()
        if not ok:break
        if i in samples:images.append((i,Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).resize((270,480),Image.Resampling.LANCZOS)))
        i+=1
    cap.release();need((w,h)==(1080,1920) and abs(fps-30)<.01 and i==581,"output video mismatch")
    sheet=Image.new("RGB",(1080,1010),"#09131F");draw=ImageDraw.Draw(sheet)
    for j,(k,im) in enumerate(images):
        xx=j%4*270;yy=j//4*505;sheet.paste(im,(xx,yy+25));draw.text((xx+6,yy+5),f"Frame {k}",fill="white")
    sheet.save(a.out/"real-proof-contact.jpg",quality=94)
    r={"version":"1.0.0-rc2","resolution":[w,h],"fps":fps,"frames":i,"duration_seconds":i/30,"capture_sha256":sha(source),"previous_pilot_sha256":sha(a.pilot),"mp4_sha256":sha(final),"capture_source_dimensions":c["dimensions"],"embedded_dimensions":[720,572],"source_state_change_frames":changes,"target_scene_boundaries":dest,"capture_time_remapped":True,"audio_samples":len(x),"pcm_identical_to_prior_pilot":True,"audio_energy":energy(x),"encoded_loudness":measure(a.ffmpeg,final),"full_decode_pass":True,"contact_sha256":sha(a.out/"real-proof-contact.jpg"),"legacy_capture_validator_pass":False,"creative_policy_full_pass":False,"owner_full_playback_approved":False,"release_authorized":False}
    (a.out/"REAL_PROOF_SHORT_QA.json").write_text(json.dumps(r,indent=2)+"\n",encoding="utf-8");print(json.dumps(r,indent=2))
if __name__=="__main__":main()
