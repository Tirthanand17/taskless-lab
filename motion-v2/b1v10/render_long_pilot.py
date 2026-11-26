"""Native-HD long-form review renderer using real Git evidence and measured speech.
Lightweight Pillow + FFmpeg path for the local 8 GB workstation; no publication.
"""
from __future__ import annotations
import argparse, hashlib, json, math, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from narration_review import normalized, pcm, energy
from sound_mix import measure, mix

ROOT=Path(__file__).resolve().parent
W,H,FPS,SR=1920,1080,30,48000
BG="#09131F"; PANEL="#132536"; EDGE="#45627A"; INK="#F3F7FC"; MUTED="#B7CBDD"; CYAN="#72E3ED"; LIME="#D1FA83"; RED="#FFB29E"
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,msg):
    if not ok:raise ValueError(msg)
def font(size,bold=False,mono=False):
    name="consola.ttf" if mono else "segoeuib.ttf" if bold else "segoeui.ttf"
    return ImageFont.truetype(str(Path("C:/Windows/Fonts")/name),size)
def text(draw,xy,s,size=36,color=INK,bold=False,mono=False):
    draw.text(xy,s,font=font(size,bold,mono),fill=color)
def wrapped(draw,xy,s,width,size=38,color=INK,bold=False,maxlines=5):
    f=font(size,bold); lines=[];line=""
    for w in s.split():
        z=(line+" "+w).strip()
        if draw.textlength(z,font=f)>width and line:lines.append(line);line=w
        else:line=z
    if line:lines.append(line)
    need(len(lines)<=maxlines,"text overflow: "+s)
    for i,l in enumerate(lines):draw.text((xy[0],xy[1]+i*int(size*1.28)),l,font=f,fill=color)
def panel(draw,box,accent=False):
    draw.rounded_rectangle(box,radius=24,fill=PANEL,outline=CYAN if accent else EDGE,width=2)
def revision_grid(draw,good,bad,focus=None,result=None):
    for i in range(16):
        x=134+(i%8)*116;y=378+(i//8)*126
        active=i==focus
        col=LIME if i==good or (active and result=="good") else RED if i==bad or (active and result=="bad") else INK if good<i<bad else MUTED
        fill="#294851" if active else "#0B1927" if good<=i<=bad else "#111D29"
        draw.rounded_rectangle((x,y,x+100,y+106),radius=14,fill=fill,outline=col if active or i in (good,bad) else EDGE,width=3 if active else 1)
        draw.text((x+50,y+37),str(i),font=font(42,True),fill=col,anchor="mm")
        label="PASS" if i==good else "FAIL" if i==bad else result.upper() if active and result else "TEST" if active else "?"
        if i<good or i>bad:label="OUT"
        draw.text((x+50,y+82),label,font=font(18,True),fill=col,anchor="mm")
def image_for(scene,phase,evidence):
    im=Image.new("RGB",(W,H),BG);d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,12),fill="#172E41")
    text(d,(96,64),"FLOWMINUTE / REAL GIT DEMONSTRATION",27,CYAN,True)
    text(d,(96,111),scene["title"],67,INK,True)
    panel(d,(96,294,1096,804));panel(d,(1120,294,1824,804),True)
    text(d,(130,317),"REVISION HISTORY / 0–15",27,CYAN,True)
    sid=scene["id"]; steps=evidence["steps"]
    good,bad,focus,result=0,15,None,None
    title="";detail="";terminal=[]
    if sid=="hook":
        focus=15 if phase else None
        title="Find the first failing change";detail="16 revisions. One reproducible test."
        terminal=["Known good: revision 0","Known bad:  revision 15"]
    elif sid=="setup":
        focus=0 if phase==0 else 15
        title="Controlled local repository";detail="Each commit changes a small Python file. The same test checks answer() == 42."
        terminal=["python -B test_example.py","PASS at 0" if phase==0 else "FAIL at 15"]
    elif sid=="start":
        focus=steps[0]["revision"] if phase else None
        title="Mark good and bad";detail="Git chooses a candidate between known endpoints."
        terminal=["git bisect start BAD GOOD","Selected revision "+str(steps[0]["revision"]) if phase else "GOOD = 0 / BAD = 15"]
    elif sid in ("step1","step2","step3"):
        index={"step1":0,"step2":1,"step3":2}[sid]
        if sid=="step3" and phase>=2:index=3
        s=steps[index];after=phase%2==1
        good,bad=s["range_after"] if after else s["range_before"]
        focus=s["revision"];result=s["classification"] if after else None
        title=("Test "+str(index+1)+" / "+str(len(steps)))
        detail=("Result: "+s["classification"].upper()+". Remaining boundary: "+str(good)+" to "+str(bad)+".") if after else ("Test revision "+str(focus)+" using the same assertion.")
        terminal=["python -B test_example.py","exit code: "+str(s["exit_code"]) if after else "Running the test...",("git bisect "+s["classification"]) if after else "Await classification"]
    elif sid=="result":
        good,bad=10,11;focus=11;result="bad"
        title="First bad: revision 11";detail="Git found the first failing commit after four midpoint tests. Inspect the actual code change."
        terminal=["- return 42","+ return 41",evidence["first_bad_commit"][:12]]
    elif sid=="limits":
        good,bad=10,11;focus=11
        title="Classification must be reliable";detail="A flaky test, skipped revision, or complex history can complicate the result."
        terminal=["Do not guess PASS / FAIL","Use a reproducible test"]
    else:
        good,bad=10,11;focus=11
        title="A practical debugging workflow";detail="Inspect the reported change, fix the root cause, and rerun your tests."
        terminal=["git bisect reset","Return to your starting revision","Fix and verify"]
    revision_grid(d,good,bad,focus,result)
    text(d,(134,654),"GREEN = GOOD     CORAL = BAD     OUT = EXCLUDED",24,MUTED,True)
    text(d,(134,706),"Observed local example • not a real production incident",26,MUTED)
    wrapped(d,(1154,326),title,634,45,LIME,True,3)
    wrapped(d,(1154,457),detail,634,34,INK,False,4)
    d.rounded_rectangle((1154,635,1790,780),radius=14,fill="#07111C",outline=EDGE,width=1)
    for i,line in enumerate(terminal):
        text(d,(1174,650+i*37),line,26,RED if line.startswith("-") else LIME if line.startswith("+") else INK,False,True)
    d.rounded_rectangle((96,1002,1824,1010),radius=4,fill=EDGE)
    return im
def ass_time(t):
    n=round(t*100);h,n=divmod(n,360000);m,n=divmod(n,6000);s,n=divmod(n,100)
    return f"{h}:{m:02}:{s:02}.{n:02}"
def esc(t):return t.replace("\\","").replace("{","").replace("}","").replace("\n"," ")
def captions(path,cues):
    out=["[Script Info]","ScriptType: v4.00+","PlayResX: 1920","PlayResY: 1080","WrapStyle: 2","[V4+ Styles]","Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding","Style: Main,Segoe UI,42,&H00FCF7F3,&H0083FAD1,&H00191007,&H00191007,-1,0,0,0,100,100,0,0,3,12,0,2,96,96,122,1","[Events]","Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for c in cues:
        words=c["words"]
        for i,w in enumerate(words):
            start=w["start"];end=words[i+1]["start"] if i+1<len(words) else c["end"]
            if round(end*100)<=round(start*100):continue
            line=" ".join(("{\\c&H83FAD1&}"+esc(x["word"])+"{\\c&HFCF7F3&}") if j==i else esc(x["word"]) for j,x in enumerate(words))
            out.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Main,,0,0,0,,{line}")
    path.write_text("\n".join(out)+"\n",encoding="utf-8")
def ff(ffmpeg,args,cwd):
    subprocess.run([ffmpeg,"-nostdin","-hide_banner","-loglevel","error","-y",*map(str,args)],cwd=cwd,check=True)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--audio",type=Path,required=True);p.add_argument("--demo",type=Path,required=True);p.add_argument("--out",type=Path,required=True);p.add_argument("--ffmpeg",required=True);a=p.parse_args()
    a.out=a.out.resolve();a.audio=a.audio.resolve();a.demo=a.demo.resolve();a.out.mkdir(parents=True,exist_ok=False)
    n=read(a.audio/"NARRATION_REVIEW_QA.json");spec=read(ROOT/"long_narration_spec.json");e=read(a.demo)
    need(e["first_bad"]==11 and len(e["steps"])==4 and e["reset_completed"],"bad Git evidence")
    need(n["voice"]=="af_heart" and sha(a.audio/"narration.wav")==n["narration_sha256"],"voice mismatch")
    cues=read(a.audio/"word_captions.json")
    need(sha(a.audio/"word_captions.json")==n["word_captions_sha256"],"ASR evidence mismatch")
    # Preserve raw timestamps; correct only explicitly identified technical spellings / numerals.
    fixes=[]
    from narration_review import cues as group_words
    corrected=[]
    for scene in n["scene_timeline"]:
        lo,hi=scene["start_frame"]/30,scene["end_frame"]/30
        words=[dict(w) for c in cues for w in c["words"] if lo-1e-6<=w["start"]<hi-1e-6]
        i=0;out=[]
        while i<len(words):
            w=words[i];raw=w["word"];key=normalized(raw)
            triple=[normalized(x["word"]) for x in words[i:i+3]]
            if scene["id"]=="hook" and triple==[["get"],["bys"],["act"]]:
                out.append({**w,"word":"Git","end":words[i]["end"]})
                out.append({**words[i+1],"word":"bisect","end":words[i+2]["end"]})
                fixes.append({"from":" ".join(x["word"] for x in words[i:i+3]),"to":"Git bisect","start":w["start"],"end":words[i+2]["end"],"note":"technical spelling; merged observed adjacent intervals"})
                i+=3;continue
            if key==["16"] and "sixteen" in normalized(scene["expected"]):w["word"]="sixteen"+raw[2:]
            elif key==["get"] and "git" in normalized(scene["expected"]) and "get" not in normalized(scene["expected"]):w["word"]="Git"+raw[3:]
            if w["word"]!=raw:fixes.append({"from":raw,"to":w["word"],"start":w["start"],"end":w["end"]})
            out.append(w);i+=1
        corrected.extend(group_words(out))
    cues=corrected
    # Keep the raw ASR and visibly mark this as review-only; no silent claim of perfect transcription.
    captions(a.out/"captions.ass",cues)
    (a.out/"caption_review.json").write_text(json.dumps({"corrections":fixes,"cues":cues,"release_authorized":False},indent=2)+"\n",encoding="utf-8")
    events=[];phase_records=[];parts=[]
    for s,cfg in zip(n["scene_timeline"],spec["scenes"]):
        need(s["id"]==cfg["id"],"scene order differs")
        lo,hi=s["start_frame"],s["end_frame"];count=4 if s["id"]=="step3" else 2 if s["id"] in ("hook","setup","start","step1","step2") else 1
        cuts=[lo+round((hi-lo)*i/count) for i in range(count+1)]
        for j,(start,end) in enumerate(zip(cuts,cuts[1:])):
            name=f"state-{len(parts):02}.png";image_for(cfg,j,e).save(a.out/name)
            parts.append((name,end-start))
            phase_records.append({"scene":s["id"],"phase":j,"start_frame":start,"end_frame":end,"image":name})
            if j and s["id"] in ("setup","start","step1","step2","step3","result","payoff"):
                events.append({"sample":start*1600,"frame":start,"effect":"soft_tick" if j%2==0 else "soft_ping","scene":s["id"]})
    v=pcm(a.audio/"narration.wav").astype(np.float64)/32768
    y,b,fx=mix(v,events)
    from narration_review import wav
    wav(a.out/"mix.wav",np.round(y*32768).astype(np.int16))
    # FFconcat uses exact frame durations. Encode original native stills into 30fps with a
    # slow, bounded per-state hero-region push-in; captions remain fixed and native.
    concat=["ffconcat version 1.0"]
    for name,frames in parts:concat.extend([f"file '{name}'",f"duration {frames/30:.9f}"])
    concat.append(f"file '{parts[-1][0]}'")
    (a.out/"frames.ffconcat").write_text("\n".join(concat)+"\n",encoding="utf-8")
    print("ENCODING",len(parts),"states",n["frames_at_30fps"],"frames",flush=True)
    final=a.out/"B1V10_GIT_BISECT_LONG_REVIEW.mp4"
    # Native source pixels; no raster upscaling beyond a bounded hero camera crop.
    filtergraph="[0:v]fps=30,format=yuv420p,split=2[base][src];[src]crop=1000:510:96:294,zoompan=z='1.002+0.018*on/"+str(n["frames_at_30fps"])+"':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1000x510:fps=30[hero];[base][hero]overlay=96:294,ass=captions.ass[out]"
    ff(a.ffmpeg,["-f","concat","-safe","0","-i","frames.ffconcat","-i","mix.wav","-filter_complex_threads","1","-filter_complex",filtergraph,"-map","[out]","-map","1:a:0","-frames:v",n["frames_at_30fps"],"-c:v","libx264","-preset","ultrafast","-crf","18","-threads","2","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart",final.name],a.out)
    ff(a.ffmpeg,["-xerror","-i",final.name,"-map","0:v:0","-map","0:a:0","-f","null","-"],a.out)
    ff(a.ffmpeg,["-i",final.name,"-map","0:a:0","-ar","48000","-ac","1","-c:a","pcm_s16le","decoded.wav"],a.out)
    import cv2
    cap=cv2.VideoCapture(str(final));w,h=int(cap.get(3)),int(cap.get(4));fps=cap.get(5);i=0
    sample_frames={s["start_frame"]+min(30,s["end_frame"]-s["start_frame"]-1) for s in n["scene_timeline"]}
    stills=[]
    while True:
        ok,frame=cap.read()
        if not ok:break
        if i in sample_frames:stills.append((i,Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)).resize((480,270))))
        i+=1
    cap.release();need((w,h)==(W,H) and abs(fps-30)<.01 and i==n["frames_at_30fps"],f"video clock mismatch {i}")
    d=pcm(a.out/"decoded.wav");need(abs(len(d)-n["samples"])<=1024,"audio clock mismatch")
    sheet=Image.new("RGB",(1440,3*296),BG);draw=ImageDraw.Draw(sheet)
    for j,(k,img) in enumerate(stills):
        xx=j%3*480;yy=j//3*296;sheet.paste(img,(xx,yy+26));draw.text((xx+8,yy+4),f"Scene {j+1} / frame {k}",fill=INK)
    sheet.save(a.out/"long-contact.jpg",quality=93)
    report={"version":"0.8.0","resolution":[w,h],"fps":fps,"frames":i,"duration_seconds":i/fps,"audio_samples":len(d),"audio_energy":energy(d),"encoded_loudness":measure(a.ffmpeg,final),"narration_sha256":n["narration_sha256"],"actual_git_evidence_sha256":sha(a.demo),"narration_report_sha256":sha(a.audio/"NARRATION_REVIEW_QA.json"),"caption_corrections":fixes,"raw_asr_screen_pass":n["asr_screen_pass"],"visual_states":phase_records,"planned_sound_events":events,"full_decode_pass":True,"contact_sha256":sha(a.out/"long-contact.jpg"),"mp4_sha256":sha(final),"render_path":"Pillow native raster + FFmpeg lightweight camera and ASS captions","full_human_playback_approved":False,"release_authorized":False}
    (a.out/"LONG_PILOT_QA.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k not in ("visual_states","planned_sound_events")},indent=2))
if __name__=="__main__":main()
