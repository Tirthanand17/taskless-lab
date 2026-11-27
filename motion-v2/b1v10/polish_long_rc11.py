"""RC11 landscape visual upgrade: actual capture, event-timed table illustrations, exact audio."""
import argparse,json,math,subprocess,tempfile
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
from production_review_rc6 import read,sha,exact,need,inspect_video,inspect_audio
from polish_shorts_rc11 import BG,PANEL,EDGE,WHITE,MUTED,CYAN,LIME,ORANGE,font,fit,roundbox,center
from narration_review import pcm
from render_float_short import at
from run_registered_rc10p2 import check_render
from topic_registry_rc10 import topics
from scripts.publish_youtube import approval_allows_exact_video
D=Path(__file__).resolve().parent
CROP=(0,60,610,250);DISPLAY=(108,348,1000,410)
TITLES=["Where did the rows go?","Only one customer remains","Three customers, two orders","WHERE filters after the join","Put the condition in ON","All three customers remain","Two queries, different goals"]
NOTES=["Watch the original query.","Only paid orders survive.","The input tables contain invented data.","Keep only rows where the condition is true.","Preserve unmatched customers.","Missing order values are NULL.","Choose the query that answers your question."]
def events(c):
    e=[x["result"] for x in c["events"]]
    need(e==[[[1,"paid"]],[[[1],[2],[3]],[[1,"paid"],[2,"pending"]]],[[1,"paid"],[2,"pending"],[3,None]],[[1,"paid"],[2,None],[3,None]],[[1,"paid"],[2,None],[3,None]],[1,3]],"unexpected fixture")
    return e
def plate(state,e,offset=0,focus=-1):
    im=Image.new("RGB",(1920,1080),BG);d=ImageDraw.Draw(im)
    fit(d,"FLOWMINUTE  /  REAL SQLITE",96,76,1728,32,CYAN)
    fit(d,TITLES[state],96,128,1728,70,minsize=56)
    fit(d,NOTES[state],96,219,1728,35,MUTED,False)
    roundbox(d,(96,294,1120,804));roundbox(d,(1144,294,1824,804))
    fit(d,"ACTUAL RECORDED OUTPUT",120,308,976,30,CYAN)
    fit(d,"RESULT EXPLAINED",1170,308,628,30,MUTED)
    # Use observed data only. Colors encode inclusion/exclusion rather than SQL truth values.
    def row(j,cols,color=EDGE,active=False):
        y=434+j*82+offset
        roundbox(d,(1170,y,1798,y+72),"#24485F" if active else BG,color,12,3 if active else 2)
        if len(cols)==2:
            fit(d,str(cols[0]),1192,y+12,230,37,WHITE)
            fit(d,str(cols[1]),1436,y+12,340,37,color if color!=EDGE else WHITE)
        else:
            fit(d,str(cols[0]),1192,y+12,580,37,WHITE)
    def head(a,b):
        fit(d,a,1192,385,230,29,MUTED)
        fit(d,b,1436,385,340,29,MUTED)
    if state==0:
        center(d,"Run the query",1484,520,57);center(d,"Watch the actual result",1484,620,36,MUTED,False)
    elif state==1:
        head("Customer","Order status")
        for j,(k,v) in enumerate(e[0]):row(j,[k,v],LIME,True)
        center(d,"1 row returned",1484,705,53,ORANGE)
    elif state==2:
        head("Customers","Orders")
        a,b=e[1]
        for j,c in enumerate(a):row(j,[c[0],str(b[j][0])+" / "+b[j][1] if j<len(b) else "No order"],EDGE,focus==j)
        center(d,"3 customers / 2 orders",1484,738,42,CYAN)
    elif state==3:
        head("Joined row","WHERE result")
        for j,(k,v) in enumerate(e[2]):row(j,[str(k)+" / "+(v or "NULL"),"Keep" if v=="paid" else "Exclude"],LIME if v=="paid" else ORANGE,focus==j)
        center(d,"Only paid passes WHERE",1484,738,39,ORANGE)
    elif state in (4,5):
        head("Customer","Order status")
        for j,(k,v) in enumerate(e[state-1]):row(j,[k,v if v is not None else "NULL"],LIME,focus==j)
        center(d,"3 rows returned",1484,738,47,LIME)
    else:
        for j,(label,count,col) in enumerate(zip(["WHERE","ON"],e[5],[ORANGE,LIME])):
            y=414+j*146+offset;roundbox(d,(1170,y,1798,y+122),BG,col,14,3)
            fit(d,label,1196,y+33,240,46,WHITE);fit(d,str(count)+" row"+("s" if count!=1 else ""),1470,y+31,300,48,col)
        center(d,"Different intended results",1484,738,39,CYAN)
    roundbox(d,(96,844,1824,986))
    return im
def captions(path,cues):
    f=font(56,True);d=ImageDraw.Draw(Image.new("RGB",(1,1)))
    lines=["[Script Info]","ScriptType: v4.00+","PlayResX: 1920","PlayResY: 1080","WrapStyle: 2","[V4+ Styles]","Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding","Style: Main,Segoe UI,56,&H00FCF7F3,&H0083FAD1,&H00191007,&H00191007,-1,0,0,0,100,100,0,0,1,2,0,5,0,0,0,1","[Events]","Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    count=0
    for c in cues:
        ws=c["words"];need(all(not any(ch in w["word"] for ch in ("{","}","\\")) for w in ws),"unsafe caption")
        groups=[];g=[]
        for j,w in enumerate(ws):
            if g and d.textlength(" ".join(ws[k]["word"] for k in g+[j]),font=f)>1580:groups.append(g);g=[]
            g.append(j)
        if g:groups.append(g)
        need(len(groups)<=2 and all(d.textlength(" ".join(ws[k]["word"] for k in g),font=f)<=1580 for g in groups),"caption overflow")
        for i,w in enumerate(ws):
            end=ws[i+1]["start"] if i+1<len(ws) else c["end"]
            if round(end*100)<=round(w["start"]*100):continue
            line="\\N".join(" ".join(("{\\c&H83FAD1&}"+ws[j]["word"]+"{\\c&HFCF7F3&}") if j==i else ws[j]["word"] for j in g) for g in groups)
            lines.append(f"Dialogue: 0,{at(w['start'])},{at(end)},Main,,0,0,0,,{{\\pos(960,915)\\clip(108,850,1812,980)}}"+line);count+=1
    path.write_text("\n".join(lines)+"\n",encoding="utf8");return count
def run(folder,out,ffmpeg):
    topic=next(x for x in topics("2026-11-29") if x["id"]=="outer_join_filter")
    old=check_render(folder,topic,"2026-11-29")
    old_report=folder/"render/NEW_LONG_QA.json";exact(old_report,old["render_report_sha256"])
    prior=folder/"render/NEW_DAILY_LONG_REVIEW.mp4";capture=folder/"capture/DAILY_LIVE_CAPTURE.mp4"
    c=json.loads((folder/"capture/LIVE_CAPTURE_QA.json").read_text());n=json.loads((folder/"audio/NARRATION_REVIEW_QA.json").read_text())
    e=events(c);starts=[0]+[x["frame"]*5 for x in c["changes"]]
    need(len(starts)==7 and all(s/30>=v["actual_seconds"]-.001 for s,v in zip(starts[1:],c["events"])),"premature result")
    total=n["frames_at_30fps"];out.mkdir(parents=True,exist_ok=False);out=out.absolute()
    cp=folder/"audio/word_captions.json";exact(cp,n["word_captions_sha256"]);count=captions(out/"captions.ass",json.loads(cp.read_text()))
    x,y,w,h=CROP;xx,yy,dw,dh=DISPLAY
    # Verify crop on all actual source frames, with the console header intentionally omitted.
    src=cv2.VideoCapture(str(capture));nframes=0
    while True:
        ok,f=src.read()
        if not ok:break
        ys,xs=np.where(cv2.cvtColor(f,cv2.COLOR_BGR2GRAY)[60:,:]>100)
        need(not len(xs) or (xs.min()>=x and xs.max()<x+w and ys.min()+60>=y and ys.max()+60<y+h),"source crop lost text")
        nframes+=1
    src.release();need(nframes==c["frames"],"capture count")
    # Render the editorial plates natively. Animate row entrance over 12 frames and
    # rotate emphasis over the three rows during the source, cause and result holds.
    cache={};last_state=None;src=cv2.VideoCapture(str(capture));frame=None
    proc=subprocess.Popen([ffmpeg,"-nostdin","-v","error","-f","rawvideo","-pix_fmt","rgb24","-s","1920x1080","-r","30","-i","-","-vf","ass=captions.ass","-an","-c:v","libx264","-preset","ultrafast","-crf","18","-threads","2","-pix_fmt","yuv420p","silent.mp4"],cwd=out,stdin=subprocess.PIPE)
    try:
        for i in range(total):
            state=max(j for j,s in enumerate(starts) if s<=i);elapsed=i-starts[state]
            offset=max(0,round(14*(1-min(1,elapsed/12))**2))
            focus=min(2,elapsed//100) if state in (2,3,4,5) else -1
            if state!=last_state:cache.clear();last_state=state
            k=(state,offset,focus)
            if k not in cache:cache[k]=plate(state,e,offset,focus)
            if i%5==0:
                ok,f=src.read();need(ok,"source ended early")
                frame=Image.fromarray(cv2.cvtColor(cv2.resize(f[y:y+h,x:x+w],(dw,dh),interpolation=cv2.INTER_LANCZOS4),cv2.COLOR_BGR2RGB))
            im=cache[k].copy();im.paste(frame,(xx,yy));d=ImageDraw.Draw(im)
            d.rounded_rectangle((96,819,1824,831),5,fill=EDGE)
            d.rounded_rectangle((96,819,96+max(1,round(1728*(i+1)/total)),831),5,fill=LIME)
            proc.stdin.write(im.tobytes())
            if i and i%600==0:print("Rendered",i,"frames",flush=True)
        proc.stdin.close();need(proc.wait()==0,"encode failed")
    finally:
        src.release()
        if proc.poll() is None:proc.kill();proc.wait()
    def ff(a):subprocess.run([ffmpeg,"-nostdin","-v","error",*map(str,a)],cwd=out,check=True)
    final=out/"RC11_POLISHED_LONG.mp4"
    ff(["-i","silent.mp4","-i",prior,"-map","0:v:0","-map","1:a:0","-c","copy","-movflags","+faststart",final])
    inspect_video(final,[1920,1080],30,total,ffmpeg,True);audio=inspect_audio(final,ffmpeg,total*1600)
    with tempfile.TemporaryDirectory() as t:
        paths=[Path(t)/f"{i}.wav" for i in range(2)]
        for v,a in zip((prior,final),paths):ff(["-i",v,"-map","0:a:0","-ar","48000","-ac","1","-c:a","pcm_s16le",a])
        need(np.array_equal(pcm(paths[0]),pcm(paths[1])),"audio changed")
    a=cv2.VideoCapture(str(prior));v=cv2.VideoCapture(str(final));s=cv2.VideoCapture(str(capture));obs=[]
    picks=[0]+[min(total-1,i+15) for i in starts[1:]]
    sheet=Image.new("RGB",(960,len(picks)*294),BG);d=ImageDraw.Draw(sheet)
    try:
        for j,i in enumerate(picks):
            a.set(cv2.CAP_PROP_POS_FRAMES,i);ok,f=a.read();need(ok,"prior frame")
            v.set(cv2.CAP_PROP_POS_FRAMES,i);ok,g=v.read();need(ok,"new frame")
            s.set(cv2.CAP_PROP_POS_FRAMES,i//5);ok,z=s.read();need(ok,"source frame")
            ref=cv2.cvtColor(cv2.resize(z[y:y+h,x:x+w],(dw,dh),interpolation=cv2.INTER_LANCZOS4),cv2.COLOR_BGR2GRAY)
            err=float(np.mean(cv2.absdiff(ref,cv2.cvtColor(g[yy:yy+dh,xx:xx+dw],cv2.COLOR_BGR2GRAY))));need(err<4,"source mismatch")
            obs.append({"frame":i,"source_frame":i//5,"error":round(err,4)})
            for k,img in enumerate((f,g)):sheet.paste(Image.fromarray(cv2.cvtColor(img,cv2.COLOR_BGR2RGB)).resize((480,270),Image.Resampling.LANCZOS),(k*480,j*294+24))
            d.text((8,j*294+5),f"BEFORE / {i/30:.2f}s",fill="white");d.text((488,j*294+5),"AFTER / RC11",fill="white")
    finally:a.release();v.release();s.release()
    sheet.save(out/"comparison.jpg",quality=94)
    need(not approval_allows_exact_video({"approved_video_sha256":sha(final)},sha(final)),"unsigned acceptance")
    r={"version":"1.0.0-rc11-phase2","topic":"outer_join_filter","prior_sha256":sha(prior),"prior_report_sha256":sha(old_report),"capture_sha256":sha(capture),"source_sha256":sha(Path(__file__)),"design_dependency_sha256":sha(D/"polish_shorts_rc11.py"),"video_sha256":sha(final),"caption_ass_sha256":sha(out/"captions.ass"),"caption_font_px":56,"prior_caption_font_px":43,"caption_events":count,"source_crop":list(CROP),"display_rect":list(DISPLAY),"prior_source_scale":944/820,"new_source_scale":1000/610,"event_starts_frames":starts,"actual_event_times_seconds":[v["actual_seconds"] for v in c["events"]],"frames":total,"resolution":[1920,1080],"fps":30,"audio":audio,"pcm_identical":True,"full_decode_pass":True,"source_checks":obs,"row_entrance_frames":12,"diagram_uses_verified_result":True,"original_brief_unchanged":True,"human_playback_approved":False,"release_authorized":False}
    (out/"RC11_LONG_QA.json").write_text(json.dumps(r,indent=2)+"\n",encoding="utf8");print(json.dumps(r,indent=2))
def main():
    p=argparse.ArgumentParser();p.add_argument("--folder",type=Path,required=True);p.add_argument("--out",type=Path,required=True);p.add_argument("--ffmpeg",required=True);a=p.parse_args();run(a.folder.absolute(),a.out.absolute(),a.ffmpeg)
if __name__=="__main__":main()
