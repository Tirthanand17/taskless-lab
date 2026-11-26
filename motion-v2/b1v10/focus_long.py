"""RC4 widescreen editorial pass using cropped frames from the verified Git recording.
Retains the original narrated video outside eight evidence inserts. Review only.
"""
import argparse,json,subprocess
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
from integrate_real_long import sha,read,need
from narration_review import pcm,energy
from sound_mix import measure
D=Path(__file__).resolve().parent
# Page, inclusive start, exclusive end, source crop, large outcome, interpretation.
PLAN=[
 (0,537,660,(0,196,470,38),"0 / 15","Known passing and failing endpoints."),
 (1,932,1052,(0,65,440,134),"7","Git selects the next revision."),
 (2,1291,1411,(0,65,455,196),"PASS / 7","Remaining boundaries: 7 to 15."),
 (3,1626,1746,(0,65,455,196),"FAIL / 11","Remaining boundaries: 7 to 11."),
 (4,1887,1976,(0,65,455,196),"PASS / 9","Remaining boundaries: 9 to 11."),
 (5,2065,2155,(0,65,455,196),"PASS / 10","Remaining boundaries: 10 to 11."),
 (6,2155,2305,(0,198,340,101),"REVISION 11","First bad commit. Inspect the change."),
 (7,3200,3320,(0,65,330,134),"RESET","Back at the original revision."),
]
def font(n,bold=False):return ImageFont.truetype("C:/Windows/Fonts/"+("segoeuib.ttf" if bold else "segoeui.ttf"),n)
def panel(frame,entry):
    page,start,end,(x,y,w,h),headline,detail=entry
    crop=Image.fromarray(cv2.cvtColor(frame[y:y+h,x:x+w],cv2.COLOR_BGR2RGB))
    scale=min(2.0,920/w,320/h)
    dw,dh=round(w*scale)//2*2,round(h*scale)//2*2
    # Preserve aspect ratio within rounding tolerance. Enlarging does not create new detail.
    crop=crop.resize((dw,dh),Image.Resampling.LANCZOS)
    im=Image.new("RGB",(1728,510),"#09131F");d=ImageDraw.Draw(im)
    d.rounded_rectangle((0,0,1000,509),24,fill="#132536",outline="#45627A",width=2)
    d.rounded_rectangle((1024,0,1727,509),24,fill="#132536",outline="#72E3ED",width=2)
    d.text((32,26),"RECORDED GIT EVIDENCE",font=font(30,True),fill="#72E3ED")
    xx=(1000-dw)//2;yy=96+(320-dh)//2
    im.paste(crop,(xx,yy))
    d.text((32,450),"Focused crop from actual local execution",font=font(28),fill="#B7CBDD")
    d.text((1058,28),"OBSERVED RESULT",font=font(30,True),fill="#72E3ED")
    col="#FFB29E" if page in (3,6) else "#D1FA83"
    d.text((1058,112),headline,font=font(64,True),fill=col)
    words=detail.split();line="";lines=[]
    for word in words:
        candidate=(line+" "+word).strip()
        if d.textlength(candidate,font=font(39))>625 and line:lines.append(line);line=word
        else:line=candidate
    if line:lines.append(line)
    for j,line in enumerate(lines):d.text((1058,220+52*j),line,font=font(39),fill="#F3F7FC")
    d.text((1058,443),"Controlled example / real test",font=font(27),fill="#B7CBDD")
    return im,(96+xx,294+yy,dw,dh),scale
def main():
    p=argparse.ArgumentParser();p.add_argument("--capture",type=Path,required=True);p.add_argument("--pilot",type=Path,required=True);p.add_argument("--out",type=Path,required=True);p.add_argument("--ffmpeg",required=True);a=p.parse_args()
    c=read(D/"GIT_CAPTURE_QA.json");n=read(D/"LONG_PILOT_QA.json")
    need(sha(a.capture)==c["capture_sha256"] and sha(a.pilot)==n["mp4_sha256"],"source mismatch")
    need(c["dimensions"]==[870,494] and n["frames"]==3360,"unexpected source")
    a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False)
    src=cv2.VideoCapture(str(a.capture));records=[];refs=[]
    for i,entry in enumerate(PLAN):
        page,start,end,crop,headline,detail=entry
        src.set(cv2.CAP_PROP_POS_FRAMES,page*24+12);ok,frame=src.read();need(ok,"capture frame")
        im,roi,scale=panel(frame,entry);im.save(a.out/f"panel-{i}.png")
        x,y,w,h=roi
        refs.append(np.array(im.convert("L"))[y-294:y-294+h,x-96:x-96+w])
        records.append({"page":page,"source_frame":page*24+12,"start_frame":start,"end_frame":end,"crop":list(crop),"output_roi":list(roi),"magnification":round(scale,4),"outcome":headline})
    src.release()
    # Use an exact frame-count timeline at 30fps. The recorded crop is a held excerpt,
    # not a new animation or continuous real-time terminal capture.
    Image.new("RGB",(1728,510),"#09131F").save(a.out/"blank.png")
    # Encode the eight inserts with independent looped still inputs and timed overlays.
    # Only one full-size video is decoded; keep processing threads bounded.
    filters=[];last="0:v"
    for i,entry in enumerate(PLAN):
        _,start,end,*_=entry
        filters.append(f"[{last}][{i+1}:v]overlay=96:294:eof_action=repeat:enable='between(n,{start},{end-1})'[v{i}]")
        last=f"v{i}"
    def ff(args):subprocess.run([a.ffmpeg,"-nostdin","-v","error",*map(str,args)],check=True)
    final=a.out/"B1V10_GIT_BISECT_FOCUS_REVIEW.mp4";silent=a.out/"silent.mp4"
    print("Encoding 3360 frames with 8 focused recorded inserts",flush=True)
    ff(["-i",a.pilot,*[v for i in range(len(PLAN)) for v in ("-i",a.out/f"panel-{i}.png")],"-filter_complex_threads","1","-filter_complex",";".join(filters),"-map",f"[{last}]","-an","-frames:v","3360","-c:v","libx264","-preset","ultrafast","-crf","18","-threads","2","-pix_fmt","yuv420p",silent])
    ff(["-i",silent,"-i",a.pilot,"-map","0:v:0","-map","1:a:0","-c","copy","-movflags","+faststart",final])
    print("Checking full decode and original audio",flush=True)
    ff(["-xerror","-i",final,"-map","0:v:0","-map","0:a:0","-f","null","-"])
    for label,path in [("prior",a.pilot),("new",final)]:
        ff(["-i",path,"-map","0:a:0","-ar","48000","-ac","1","-c:a","pcm_s16le",a.out/(label+".wav")])
    x=pcm(a.out/"new.wav");need(len(x)==5376000 and np.array_equal(x,pcm(a.out/"prior.wav")),"audio mismatch")
    cap=cv2.VideoCapture(str(final));w,h=int(cap.get(3)),int(cap.get(4));fps=cap.get(5)
    samples={ (r["start_frame"]+r["end_frame"])//2:i for i,r in enumerate(records)}
    samples[80]=None;samples[2700]=None
    i=0;observed=[];stills=[]
    while True:
        ok,f=cap.read()
        if not ok:break
        if i in samples:
            j=samples[i]
            if j is not None:
                xx,yy,dw,dh=records[j]["output_roi"]
                g=cv2.cvtColor(f[yy:yy+dh,xx:xx+dw],cv2.COLOR_BGR2GRAY)
                err=float(np.mean(cv2.absdiff(g,refs[j])))
                need(err<3,f"capture crop mismatch {j}: {err}")
                observed.append({"page":j,"frame":i,"mean_gray_error":round(err,4)})
            stills.append((i,Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).resize((480,270),Image.Resampling.LANCZOS)))
        i+=1
    cap.release();need((w,h)==(1920,1080) and abs(fps-30)<.01 and i==3360 and len(observed)==8,"frame count mismatch")
    sheet=Image.new("RGB",(1440,4*294),"#09131F");d=ImageDraw.Draw(sheet)
    for k,(fr,im) in enumerate(stills):
        xx=k%3*480;yy=k//3*294;sheet.paste(im,(xx,yy+24));d.text((xx+6,yy+5),f"480px preview / frame {fr}",fill="white")
    sheet.save(a.out/"mobile-long-contact.jpg",quality=94)
    r={"version":"1.0.0-rc4","resolution":[w,h],"fps":fps,"frames":i,"duration_seconds":i/fps,"audio_samples":len(x),"pcm_identical":True,"audio_energy":energy(x),"loudness":measure(a.ffmpeg,final),"capture_sha256":sha(a.capture),"prior_pilot_sha256":sha(a.pilot),"mp4_sha256":sha(final),"panels":records,"observed_crops":observed,"phone_preview_width":480,"contact_sha256":sha(a.out/"mobile-long-contact.jpg"),"full_decode_pass":True,"opening_capture_spoiler_removed":True,"capture_mode":"held cropped frames from actual recorded console","human_mobile_approved":False,"release_authorized":False}
    (a.out/"FOCUS_LONG_QA.json").write_text(json.dumps(r,indent=2)+"\n",encoding="utf-8");print(json.dumps(r,indent=2))
if __name__=="__main__":main()
