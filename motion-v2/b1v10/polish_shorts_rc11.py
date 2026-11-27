"""RC11 evidence-led vertical polish. Original capture and audio, new editorial graphics."""
import argparse,json,math,subprocess,tempfile
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
from production_review_rc6 import read,sha,exact,need,inspect_video,inspect_audio
from narration_review import pcm
from render_float_short import at
from run_registered_rc10p2 import check_render
from topic_registry_rc10 import topics
from scripts.publish_youtube import approval_allows_exact_video
D=Path(__file__).resolve().parent
BG="#09131F";PANEL="#132536";EDGE="#45627A";WHITE="#F3F7FC";MUTED="#B7CBDD";CYAN="#72E3ED";LIME="#D1FA83";ORANGE="#FFB29E"
CONFIG={
 "shared_lists":{"crop":[0,60,564,312],"labels":["One change. Two lists.","One change. Two lists.","Two keys, same value","Same object? Yes.","Create separate lists","Only one key changes","Independent objects"],"notes":["Watch the actual operation.","One append, two affected keys.","Both values contain the item.","Both keys refer to one object.","A new list for each key.","The other list stays empty.","Check identity before sharing."],"prefix":"SHARED"},
 "group_runs":{"crop":[0,60,474,312],"labels":["Three groups?","Three groups","Same value, separate runs","Adjacent items only","Sort before grouping","Two groups","Order matters"],"notes":["Watch the actual operation.","A, B, A form three runs.","The first and last values match.","Only adjacent values group.","Sort if order can change.","Equal items now sit together.","Sorting changes input order."],"prefix":"GROUP"}
}
def font(n,bold=False):
    return ImageFont.truetype("C:/Windows/Fonts/"+("segoeuib.ttf" if bold else "segoeui.ttf"),n)
def fit(d,text,x,y,width,size,color=WHITE,bold=True,minsize=32):
    for n in range(size,min(size,minsize)-1,-1):
        f=font(n,bold)
        if d.textlength(text,font=f)<=width:
            d.text((x,y),text,font=f,fill=color);return n
    raise ValueError("text overflow: "+text)
def roundbox(d,box,fill=PANEL,outline=EDGE,r=24,width=2):
    d.rounded_rectangle(box,r,fill=fill,outline=outline,width=width)
def center(d,s,x,y,n,color=WHITE,bold=True):
    f=font(n,bold);d.text((x,y),s,anchor="mm",font=f,fill=color)
def arrow(d,x,y,x2,y2,color=CYAN):
    d.line((x,y,x2,y2),fill=color,width=5)
    ang=math.atan2(y2-y,x2-x)
    d.polygon([(x2,y2),(x2-15*math.cos(ang-.48),y2-15*math.sin(ang-.48)),(x2-15*math.cos(ang+.48),y2-15*math.sin(ang+.48))],fill=color)
def diagram(key,state):
    cfg=CONFIG[key];im=Image.new("RGB",(1080,1920),BG);d=ImageDraw.Draw(im)
    fit(d,"FLOWMINUTE  /  REAL PYTHON",72,192,824,30,CYAN)
    fit(d,cfg["labels"][state],72,252,824,62,minsize=42)
    roundbox(d,(72,354,896,742));fit(d,"RESULT EXPLAINED",98,376,770,27,MUTED)
    if state==0:
        center(d,"Watch the output",484,543,55)
        center(d,"Actual test begins below",484,627,34,MUTED,False)
    elif key=="shared_lists":
        shared=state<=3;item=state in (1,2,3,5,6)
        for x,k in [(244,"a"),(724,"b")]:
            roundbox(d,(x-100,437,x+100,507),BG,EDGE,15)
            center(d,"key "+k,x,472,38)
        if state in (1,2):
            for x in (244,724):
                roundbox(d,(x-150,559,x+150,650),"#24485F",ORANGE,18,3)
                center(d,"['item']",x,604,48,ORANGE)
            center(d,"Both values changed",484,692,33,ORANGE)
        elif shared:
            arrow(d,244,513,400,552,ORANGE);arrow(d,724,513,568,552,ORANGE)
            roundbox(d,(306,559,662,650),"#24485F",ORANGE,18,3)
            center(d,"['item']",484,603,50)
            center(d,"ONE shared list",484,692,33,ORANGE)
        else:
            for x,v in [(244,"['item']" if item else "[]"),(724,"[]")]:
                arrow(d,x,513,x,551,LIME)
                roundbox(d,(x-150,559,x+150,650),"#24485F",LIME,18,3)
                center(d,v,x,604,48,LIME)
            center(d,"TWO separate lists",484,692,33,LIME)
    else:
        sorted_=state>=4
        tokens=["A","A","B"] if sorted_ else ["A","B","A"]
        groups=[[0,1],[2]] if sorted_ else [[0],[1],[2]]
        for group in groups:
            x0=154+group[0]*225;x1=154+group[-1]*225+210
            roundbox(d,(x0-6,451,x1+6,628),"#24485F",LIME if sorted_ else ORANGE,18,3)
        for j,v in enumerate(tokens):
            x=154+j*225;roundbox(d,(x,464,x+210,590),BG,EDGE,14)
            center(d,v,x+105,527,76,CYAN if v=="A" else WHITE)
        center(d,("2 groups" if state>=5 else "Sorted input" if sorted_ else "3 separate runs"),484,686,46,LIME if sorted_ else ORANGE)
    fit(d,cfg["notes"][state],72,769,824,37,MUTED,False,29)
    roundbox(d,(72,836,896,1332),PANEL,EDGE,22)
    fit(d,"ACTUAL RECORDED OUTPUT",98,854,770,28,CYAN)
    roundbox(d,(72,1385,896,1559),PANEL,EDGE,22)
    return im
def caption_script(path,cues):
    f=font(58,True);d=ImageDraw.Draw(Image.new("RGB",(1,1)))
    lines=["[Script Info]","ScriptType: v4.00+","PlayResX: 1080","PlayResY: 1920","WrapStyle: 2","[V4+ Styles]","Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding","Style: Main,Segoe UI,58,&H00FCF7F3,&H0083FAD1,&H00191007,&H00191007,-1,0,0,0,100,100,0,0,1,2,0,5,0,0,0,1","[Events]","Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    count=0
    for cue in cues:
        ws=cue["words"];need(all(not any(ch in w["word"] for ch in ("{","}","\\")) for w in ws),"unsafe captions")
        groups=[];group=[]
        for j,w in enumerate(ws):
            if group and d.textlength(" ".join(ws[k]["word"] for k in group+[j]),font=f)>744:groups.append(group);group=[]
            group.append(j)
        if group:groups.append(group)
        need(len(groups)<=2 and all(d.textlength(" ".join(ws[k]["word"] for k in g),font=f)<=744 for g in groups),"caption layout")
        for i,w in enumerate(ws):
            end=ws[i+1]["start"] if i+1<len(ws) else cue["end"]
            if round(end*100)<=round(w["start"]*100):continue
            line="\\N".join(" ".join(("{\\c&H83FAD1&}"+ws[j]["word"]+"{\\c&HFCF7F3&}") if j==i else ws[j]["word"] for j in g) for g in groups)
            lines.append(f"Dialogue: 0,{at(w['start'])},{at(end)},Main,,0,0,0,,{{\\pos(484,1472)\\clip(88,1394,880,1550)}}"+line);count+=1
    path.write_text("\n".join(lines)+"\n",encoding="utf8");return count
def run(key,folder,out,ffmpeg):
    cfg=CONFIG[key];topic=next(x for x in topics("2026-11-29") if x["id"]==key)
    old=check_render(folder,topic,"2026-11-29")
    old_report=folder/"render/NEW_SHORT_QA.json";exact(old_report,old["render_report_sha256"])
    prior=folder/"render/NEW_DAILY_SHORT_REVIEW.mp4";capture=folder/"capture/DAILY_LIVE_CAPTURE.mp4"
    c=json.loads((folder/"capture/LIVE_CAPTURE_QA.json").read_text());n=json.loads((folder/"audio/NARRATION_REVIEW_QA.json").read_text())
    need(len(c["changes"])==6 and len(c["events"])==6,"unexpected event sequence")
    starts=[0]+[x["frame"]*5 for x in c["changes"]]
    need(all(starts[i]/30>=c["events"][i-1]["actual_seconds"]-.001 for i in range(1,7)),"premature diagram")
    total=n["frames_at_30fps"];out.mkdir(parents=True,exist_ok=False);out=out.absolute()
    cp=folder/"audio/word_captions.json";exact(cp,n["word_captions_sha256"]);caption_count=caption_script(out/"captions.ass",json.loads(cp.read_text()))
    x,y,w,h=cfg["crop"];dw=800;dh=round(h*dw/w/2)*2
    # Preserve aspect ratio; the taller groupby crop may need a smaller display width.
    if dh>410:dh=410;dw=round(w*dh/h/2)*2
    xx=484-dw//2;yy=903
    need(xx>=84 and yy+dh<=1320,"source fit")
    plates=[diagram(key,i) for i in range(7)]
    source=cv2.VideoCapture(str(capture));frames=[]
    while True:
        ok,f=source.read()
        if not ok:break
        gray=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY)
        # Verify the crop contains all bright command/result pixels below the header.
        ys,xs=np.where(gray[60:,:]>100)
        need(not len(xs) or (xs.min()>=x and xs.max()<x+w and ys.min()+60>=y and ys.max()+60<y+h),"source text cropped")
        frames.append(cv2.resize(f[y:y+h,x:x+w],(dw,dh),interpolation=cv2.INTER_LANCZOS4))
    source.release();need(len(frames)==c["frames"],"source frame count")
    # Native design, continuous actual footage and restrained linear progress.
    # The explanatory graphic switches only when the corresponding actual output is visible.
    cmd=[ffmpeg,"-nostdin","-v","error","-f","rawvideo","-pix_fmt","rgb24","-s","1080x1920","-r","30","-i","-","-vf","ass=captions.ass","-an","-c:v","libx264","-preset","ultrafast","-crf","18","-threads","2","-pix_fmt","yuv420p","silent.mp4"]
    proc=subprocess.Popen(cmd,cwd=out,stdin=subprocess.PIPE)
    try:
        for i in range(total):
            state=max(j for j,v in enumerate(starts) if v<=i)
            im=plates[state].copy();d=ImageDraw.Draw(im)
            frame=frames[min(len(frames)-1,i//5)]
            im.paste(Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)),(xx,yy))
            d.rounded_rectangle((72,1354,896,1365),5,fill=EDGE)
            d.rounded_rectangle((72,1354,72+max(1,round(824*(i+1)/total)),1365),5,fill=LIME)
            proc.stdin.write(im.tobytes())
        proc.stdin.close();need(proc.wait()==0,"encode failed")
    finally:
        if proc.poll() is None:proc.kill();proc.wait()
    def ff(a):subprocess.run([ffmpeg,"-nostdin","-v","error",*map(str,a)],cwd=out,check=True)
    final=out/"RC11_POLISHED_SHORT.mp4"
    ff(["-i","silent.mp4","-i",prior,"-map","0:v:0","-map","1:a:0","-c","copy","-movflags","+faststart",final])
    inspect_video(final,[1080,1920],30,total,ffmpeg,True);audio=inspect_audio(final,ffmpeg,total*1600)
    with tempfile.TemporaryDirectory() as t:
        paths=[Path(t)/f"{i}.wav" for i in range(2)]
        for v,a in zip((prior,final),paths):ff(["-i",v,"-map","0:a:0","-ar","48000","-ac","1","-c:a","pcm_s16le",a])
        need(np.array_equal(pcm(paths[0]),pcm(paths[1])),"audio changed")
    a=cv2.VideoCapture(str(prior));v=cv2.VideoCapture(str(final));obs=[]
    picks=[0]+[min(total-1,j+5) for j in starts[1:]]
    sheet=Image.new("RGB",(720,len(picks)*664),BG);d=ImageDraw.Draw(sheet)
    try:
        for j,i in enumerate(picks):
            a.set(cv2.CAP_PROP_POS_FRAMES,i);ok,f=a.read();need(ok,"old frame")
            v.set(cv2.CAP_PROP_POS_FRAMES,i);ok,g=v.read();need(ok,"new frame")
            ref=cv2.cvtColor(frames[min(len(frames)-1,i//5)],cv2.COLOR_BGR2GRAY)
            actual=cv2.cvtColor(g[yy:yy+dh,xx:xx+dw],cv2.COLOR_BGR2GRAY)
            err=float(np.mean(cv2.absdiff(ref,actual)));need(err<4,"source mismatch")
            obs.append({"frame":i,"source_frame":min(len(frames)-1,i//5),"error":round(err,4)})
            for k,img in enumerate((f,g)):sheet.paste(Image.fromarray(cv2.cvtColor(img,cv2.COLOR_BGR2RGB)).resize((360,640),Image.Resampling.LANCZOS),(k*360,j*664+24))
            d.text((8,j*664+5),f"BEFORE / {i/30:.2f}s",fill="white");d.text((368,j*664+5),"AFTER / RC11",fill="white")
    finally:a.release();v.release()
    sheet.save(out/"comparison.jpg",quality=93)
    need(not approval_allows_exact_video({"approved_video_sha256":sha(final)},sha(final)),"unsigned acceptance")
    result={"version":"1.0.0-rc11-phase1","topic":key,"prior_sha256":sha(prior),"prior_report_sha256":sha(old_report),"capture_sha256":sha(capture),"source_sha256":sha(Path(__file__)),"video_sha256":sha(final),"caption_ass_sha256":sha(out/"captions.ass"),"caption_font_px":58,"prior_caption_font_px":49,"caption_events":caption_count,"source_crop":cfg["crop"],"display_rect":[xx,yy,dw,dh],"prior_source_scale":792/680,"new_source_scale":dw/w,"event_starts_frames":starts,"actual_event_times_seconds":[e["actual_seconds"] for e in c["events"]],"frames":total,"resolution":[1080,1920],"fps":30,"audio":audio,"pcm_identical":True,"full_decode_pass":True,"source_checks":obs,"diagram_uses_verified_result":True,"original_brief_unchanged":True,"human_playback_approved":False,"release_authorized":False}
    (out/"RC11_SHORT_QA.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf8");print(json.dumps(result,indent=2))
def main():
    p=argparse.ArgumentParser();p.add_argument("--topic",choices=list(CONFIG),required=True);p.add_argument("--folder",type=Path,required=True);p.add_argument("--out",type=Path,required=True);p.add_argument("--ffmpeg",required=True);a=p.parse_args();run(a.topic,a.folder.absolute(),a.out.absolute(),a.ffmpeg)
if __name__=="__main__":main()
