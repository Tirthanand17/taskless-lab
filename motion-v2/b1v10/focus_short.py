"""RC4 review-only Short: original animated hero plus focused real-recording evidence."""
import argparse, hashlib,json,subprocess
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
from narration_review import pcm,energy
from sound_mix import measure
D=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,msg):
    if not ok:raise ValueError(msg)
# source frame range; destination range; native crop x,y,w,h; displayed w,h; title.
PLAN=[
    (25,49,156,214,(0,232,310,34),(620,68),"REAL CAPTURE / FILE A"),
    (25,49,214,232,(0,232,310,66),(620,132),"REAL CAPTURE / INPUT BYTES"),
    (49,73,282,354,(0,364,560,66),(756,90),"REAL CAPTURE / HASH A"),
    (49,73,354,383,(0,364,560,132),(756,178),"REAL CAPTURE / FULL HASHES"),
    (73,120,417,581,(0,562,410,68),(738,122),"REAL CAPTURE / MATCH CHECK"),
]
def font(n):return ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf",n)
def main():
    p=argparse.ArgumentParser();p.add_argument("--capture",type=Path,required=True);p.add_argument("--pilot",type=Path,required=True);p.add_argument("--out",type=Path,required=True);p.add_argument("--ffmpeg",required=True);a=p.parse_args()
    c=read(D/"REAL_CAPTURE_QA.json");s=read(D/"SHORT_PILOT_QA.json")
    need(sha(a.capture)==c["capture_sha256"] and sha(a.pilot)==s["mp4_sha256"],"source changed")
    need(c["dimensions"]==[870,692],"wrong source dimensions")
    a.out.mkdir(parents=True,exist_ok=False)
    # Native label plates, with clear distinction between recorded evidence and illustration.
    for i,(_,_,_,_,crop,size,label) in enumerate(PLAN):
        im=Image.new("RGB",(824,300),"#132536");d=ImageDraw.Draw(im)
        d.rounded_rectangle((1,1,822,298),radius=22,outline="#45627A",width=2)
        d.text((28,17),label,font=font(29),fill="#72E3ED")
        d.text((28,255),["Actual bytes read by Python","Original one-byte files","Computed SHA-256 of file A","Compare all 64 hexadecimal characters","A match is not proof of safety"][i],font=font(25),fill="#B7CBDD")
        im.save(a.out/f"plate-{i}.png")
    filters=["[1:v]split="+str(len(PLAN))+"".join(f"[c{i}]" for i in range(len(PLAN)))]
    last="0:v"
    for i,(lo,hi,start,end,crop,size,label) in enumerate(PLAN):
        x,y,w,h=crop;dw,dh=size;count=end-start
        need(x+w<=870 and y+h<=692 and dw<=770 and dh<=190,"invalid crop")
        factor=count/30/((hi-lo)/12)
        filters.append(f"[c{i}]trim=start_frame={lo}:end_frame={hi},setpts=(PTS-STARTPTS)*{factor:.12f},fps=30,tpad=stop_mode=clone:stop_duration=1,trim=end_frame={count},crop={w}:{h}:{x}:{y},scale={dw}:{dh}:flags=lanczos,setsar=1,setpts=N/(30*TB)+{start}/(30*TB)[ev{i}]")
        enable=f"between(n,{start},{end-1})"
        filters.append(f"[{last}][{i+2}:v]overlay=72:1070:enable='{enable}'[plate{i}]")
        xx=72+(824-dw)//2;yy=1070+68+(178-dh)//2
        filters.append(f"[plate{i}][ev{i}]overlay={xx}:{yy}:eof_action=repeat:enable='{enable}'[v{i}]")
        last=f"v{i}"
    def ff(args):subprocess.run([a.ffmpeg,"-nostdin","-v","error",*map(str,args)],check=True)
    final=a.out/"B1V10_SHA256_FOCUS_REVIEW.mp4";silent=a.out/"silent.mp4"
    print("Encoding 581 frames with focused real capture panels",flush=True)
    ff(["-i",a.pilot,"-i",a.capture,*[v for i in range(len(PLAN)) for v in ("-i",a.out/f"plate-{i}.png")],"-filter_complex_threads","1","-filter_complex",";".join(filters),"-map",f"[v{len(PLAN)-1}]","-an","-frames:v","581","-c:v","libx264","-preset","ultrafast","-crf","18","-threads","2","-pix_fmt","yuv420p",silent])
    ff(["-i",silent,"-i",a.pilot,"-map","0:v:0","-map","1:a:0","-c","copy","-movflags","+faststart",final])
    ff(["-xerror","-i",final,"-map","0:v:0","-map","0:a:0","-f","null","-"])
    for name,path in [("prior",a.pilot),("new",final)]:
        ff(["-i",path,"-map","0:a:0","-ar","48000","-ac","1","-c:a","pcm_s16le",a.out/(name+".wav")])
    v=pcm(a.out/"new.wav");need(len(v)==929600 and np.array_equal(v,pcm(a.out/"prior.wav")),"audio differs")
    cap=cv2.VideoCapture(str(final));w,h=int(cap.get(3)),int(cap.get(4));fps=cap.get(5);n=0
    samples=[35]+[(x[2]+x[3])//2 for x in PLAN];stills=[];matches=[]
    src=cv2.VideoCapture(str(a.capture))
    for i,(lo,hi,start,end,crop,size,label) in enumerate(PLAN):
        src.set(cv2.CAP_PROP_POS_FRAMES,(lo+hi)//2);ok,frame=src.read();need(ok,"source decode")
        x,y,cw,ch=crop;dw,dh=size
        ref=cv2.resize(cv2.cvtColor(frame[y:y+ch,x:x+cw],cv2.COLOR_BGR2GRAY),(dw,dh),interpolation=cv2.INTER_LANCZOS4)
        matches.append((i,ref))
    src.release()
    observed=[]
    while True:
        ok,f=cap.read()
        if not ok:break
        if n in samples:
            stills.append(Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).resize((360,640),Image.Resampling.LANCZOS))
            if n!=35:
                i=samples.index(n)-1;dw,dh=PLAN[i][5];xx=72+(824-dw)//2;yy=1070+68+(178-dh)//2
                gray=cv2.cvtColor(f[yy:yy+dh,xx:xx+dw],cv2.COLOR_BGR2GRAY)
                error=float(np.mean(cv2.absdiff(gray,matches[i][1])))
                need(error<10,f"recorded crop mismatch {i}: {error}")
                observed.append({"panel":i,"frame":n,"mean_gray_error":round(error,3)})
        n+=1
    cap.release();need((w,h)==(1080,1920) and abs(fps-30)<.01 and n==581 and len(observed)==len(PLAN),"video clock mismatch")
    sheet=Image.new("RGB",(1080,1328),"#09131F");d=ImageDraw.Draw(sheet)
    for i,im in enumerate(stills):
        xx=i%3*360;yy=i//3*664;sheet.paste(im,(xx,yy+24));d.text((xx+8,yy+5),f"Phone-width preview / frame {samples[i]}",fill="white")
    sheet.save(a.out/"mobile-contact.jpg",quality=94)
    report={"version":"1.0.0-rc4","resolution":[w,h],"fps":fps,"frames":n,"audio_samples":len(v),"pcm_identical":True,"audio_energy":energy(v),"loudness":measure(a.ffmpeg,final),"capture_sha256":sha(a.capture),"prior_pilot_sha256":sha(a.pilot),"mp4_sha256":sha(final),"panels":[{"crop":list(crop),"display":list(size),"start":start,"end":end,"scale":round(size[0]/crop[2],3),"label":label} for lo,hi,start,end,crop,size,label in PLAN],"observed_crops":observed,"phone_preview_width":360,"contact_sha256":sha(a.out/"mobile-contact.jpg"),"full_decode_pass":True,"human_mobile_approved":False,"release_authorized":False}
    (a.out/"FOCUS_SHORT_QA.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");print(json.dumps(report,indent=2))
if __name__=="__main__":main()
