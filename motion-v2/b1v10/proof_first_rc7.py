"""RC7 proof-first opening variants, exact source identity and audio preserved.
Recorded result crops are held editorial inserts, not continuous live action.
"""
import argparse,json,subprocess,tempfile
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
from production_review_rc6 import CATALOG,read,sha,exact,need,inspect_video,inspect_audio
from narration_review import pcm
D=Path(__file__).resolve().parent
# Each tuple: capture frame, crop, headline, supporting text, output interval.
PLANS={
 "sha256":[(35,(0,65,520,98),"One byte. New hash.","Actual output / first 24 hex digits",0,60),(35,(0,198,535,100),"Two one-byte files","Actual Python file reads",60,90)],
 "float":[(12,(0,65,330,68),"Python prints this","Actual addition result",0,60),(12,(0,165,355,66),"Equal to 0.3?","Actual equality test",60,102)],
 "git":[(36,(0,65,440,134),"Git narrows the search","Actual bisect command / selected revision",0,60),(60,(0,65,455,196),"Test the selected revision","Actual test and classification",60,90)]
}
def make_plate(frame,plan,kind):
    sf,(x,y,w,h),title,detail,start,end=plan
    short=kind!="git";size=(824,606) if short else (1000,510)
    im=Image.new("RGB",size,"#132536");d=ImageDraw.Draw(im)
    def f(n):return ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf",n)
    d.rounded_rectangle((1,1,size[0]-2,size[1]-2),24,outline="#45627A",width=2)
    d.text((28,22),"RECORDED SOFTWARE OUTPUT",font=f(29),fill="#72E3ED")
    ft=f(52 if short else 46)
    need(d.textlength(title,font=ft)<size[0]-56,"title overflow")
    d.text((28,83),title,font=ft,fill="#D1FA83")
    crop=Image.fromarray(cv2.cvtColor(frame[y:y+h,x:x+w],cv2.COLOR_BGR2RGB))
    factor=min(2.1,(size[0]-56)/w,260/h)
    dw,dh=int(w*factor)//2*2,int(h*factor)//2*2
    crop=crop.resize((dw,dh),Image.Resampling.LANCZOS)
    xx=(size[0]-dw)//2;yy=174+(260-dh)//2
    im.paste(crop,(xx,yy))
    need(d.textlength(detail,font=f(28))<size[0]-56,"detail overflow")
    d.text((28,size[1]-64),detail,font=f(28),fill="#B7CBDD")
    return im,(xx,yy,dw,dh)
def run(kind,capture,video,out,ffmpeg):
    cfile,rfile,nfile,*_=CATALOG[kind];c,r,n=read(cfile),read(rfile),read(nfile)
    exact(capture,c["capture_sha256"]);exact(video,r["mp4_sha256"])
    out.mkdir(parents=True,exist_ok=False);out=out.absolute()
    origin=(72,440) if kind!="git" else (96,294)
    cap=cv2.VideoCapture(str(capture));records=[];refs=[]
    for i,plan in enumerate(PLANS[kind]):
        sf,crop,title,detail,start,end=plan
        cap.set(cv2.CAP_PROP_POS_FRAMES,sf);ok,frame=cap.read();need(ok,"source frame unavailable")
        im,roi=make_plate(frame,plan,kind);im.save(out/f"plate-{i}.png")
        x,y,w,h=roi;refs.append(np.array(im.convert("L"))[y:y+h,x:x+w])
        records.append({"capture_frame":sf,"crop":list(crop),"start_frame":start,"end_frame":end,"roi":[origin[0]+x,origin[1]+y,w,h]})
    cap.release()
    filters=[];last="0:v"
    for i,rec in enumerate(records):
        filters.append(f"[{last}][{i+1}:v]overlay={origin[0]}:{origin[1]}:eof_action=repeat:enable='between(n,{rec['start_frame']},{rec['end_frame']-1})'[v{i}]");last=f"v{i}"
    def ff(args):subprocess.run([ffmpeg,"-nostdin","-v","error",*map(str,args)],check=True)
    final=out/"PROOF_FIRST_REVIEW.mp4";silent=out/"silent.mp4"
    print("Rendering",kind,flush=True)
    ff(["-i",video,"-i",out/"plate-0.png","-i",out/"plate-1.png","-filter_complex_threads","1","-filter_complex",";".join(filters),"-map",f"[{last}]","-an","-frames:v",r["frames"],"-c:v","libx264","-preset","ultrafast","-crf","18","-threads","2","-pix_fmt","yuv420p",silent])
    ff(["-i",silent,"-i",video,"-map","0:v:0","-map","1:a:0","-c","copy","-movflags","+faststart",final])
    inspect_video(final,r["resolution"],30,r["frames"],ffmpeg,True)
    audio=inspect_audio(final,ffmpeg,r["audio_samples"])
    with tempfile.TemporaryDirectory() as temp:
        paths=[Path(temp)/f"{i}.wav" for i in range(2)]
        for p,v in zip(paths,(video,final)):ff(["-i",v,"-map","0:a:0","-ar","48000","-ac","1","-c:a","pcm_s16le",p])
        need(np.array_equal(pcm(paths[0]),pcm(paths[1])),"audio changed")
    cap=cv2.VideoCapture(str(final));observed=[];stills=[]
    for i,rec in enumerate(records):
        x,y,w,h=rec["roi"]
        for fr in (rec["start_frame"],(rec["start_frame"]+rec["end_frame"])//2,rec["end_frame"]-1):
            cap.set(cv2.CAP_PROP_POS_FRAMES,fr);ok,f=cap.read();need(ok,"final frame unavailable")
            gray=cv2.cvtColor(f[y:y+h,x:x+w],cv2.COLOR_BGR2GRAY)
            err=float(np.mean(cv2.absdiff(gray,refs[i])));need(err<4,"opening evidence mismatch")
            observed.append({"panel":i,"frame":fr,"gray_error":round(err,4)})
            if fr==rec["start_frame"]:stills.append(Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)))
    cap.release()
    for i,im in enumerate(stills):
        im.thumbnail((480,640));im.save(out/f"opening-{i}.jpg",quality=95)
    report={"version":"1.0.0-rc7","pilot":kind,"capture_sha256":sha(capture),"prior_video_sha256":sha(video),"mp4_sha256":sha(final),"source_sha256":sha(D/"proof_first_rc7.py"),"resolution":r["resolution"],"frames":r["frames"],"audio":audio,"pcm_identical":True,"full_decode_pass":True,"opening_panels":records,"observed":observed,"first_recorded_evidence_frame":0,"second_recorded_result_frame":60,"opening_proof_timing_pass":True,"continuous_live_action_verified":False,"legacy_creative_pass":False,"owner_approval":False,"release_authorized":False}
    (out/"OPENING_QA.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2),flush=True)
def main():
    p=argparse.ArgumentParser();p.add_argument("--pilot",choices=PLANS,required=True);p.add_argument("--capture",type=Path,required=True);p.add_argument("--video",type=Path,required=True);p.add_argument("--out",type=Path,required=True);p.add_argument("--ffmpeg",required=True);a=p.parse_args()
    run(a.pilot,a.capture.absolute(),a.video.absolute(),a.out,a.ffmpeg)
if __name__=="__main__":main()
