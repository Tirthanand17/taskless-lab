"""RC8 long video: continuous capture plus native revision-range explanations. Review only."""
import argparse,json,subprocess,tempfile,math
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
from production_review_rc6 import read,sha,exact,need,inspect_video,inspect_audio
from narration_review import pcm
from autopilot.branch1_recovery import SCHEMA,validate_creative
from scripts.publish_youtube import approval_allows_exact_video
D=Path(__file__).resolve().parent
W,H=1920,1080
def font(n,bold=False):return ImageFont.truetype("C:/Windows/Fonts/"+("segoeuib.ttf" if bold else "segoeui.ttf"),n)
def plate(title,detail,bounds=None,test=None):
    im=Image.new("RGB",(704,510),"#132536");d=ImageDraw.Draw(im)
    d.rounded_rectangle((1,1,702,508),24,outline="#45627A",width=2)
    d.text((28,22),"ACTUAL TEST / EDITORIAL EXPLANATION",font=font(24,True),fill="#72E3ED")
    f=font(46,True);need(d.textlength(title,font=f)<650,"title overflow: "+title)
    d.text((28,83),title,font=f,fill="#D1FA83")
    lines=[];line=""
    for word in detail.split():
        new=(line+" "+word).strip()
        if line and d.textlength(new,font=font(33))>640:lines.append(line);line=word
        else:line=new
    if line:lines.append(line)
    need(len(lines)<=3,"detail overflow")
    for j,line in enumerate(lines):d.text((28,152+j*43),line,font=font(33),fill="#F3F7FC")
    if bounds:
        lo,hi=bounds
        for i in range(16):
            x=28+(i%8)*80;y=302+(i//8)*69
            bg="#24485F" if lo<=i<=hi else "#09131F"
            edge="#D1FA83" if i==lo else "#FFB29E" if i==hi else "#45627A"
            if i==test:bg="#45627A"
            d.rounded_rectangle((x,y,x+70,y+57),8,fill=bg,outline=edge,width=2)
            d.text((x+35,y+28),str(i),font=font(25,True),anchor="mm",fill="#F3F7FC")
        d.text((28,462),"Green = good boundary / red = bad boundary",font=font(22),fill="#B7CBDD")
    else:
        d.text((28,445),"Controlled local example",font=font(26),fill="#B7CBDD")
    return im
def run(capture_dir,prior,out,ffmpeg):
    c=json.loads((capture_dir/"LIVE_CAPTURE_QA.json").read_text())
    old=next(x for x in read("RC7_OPENING_QA.json")["pilots"] if x["pilot"]=="git")
    capture=capture_dir/"GIT_LIVE_CAPTURE.mp4"
    exact(capture,c["capture_sha256"]);exact(prior,old["mp4_sha256"])
    exact(D/"GIT_BISECT_DEMO.json",c["original_evidence_sha256"])
    for k,h in c["source_sha256"].items():exact(D/k,h)
    need(c["continuous"] is True and c["release_authorized"] is False and c["dimensions"]==[870,494] and c["frames"]==672 and c["fps"]==6,"capture scope")
    events={x["id"]:x for x in c["events"]["events"]}
    need(c["events"]["repair_test_exit"]==0 and c["events"]["reset_completed"],"repair absent")
    inspect_video(capture,c["dimensions"],6,672,ffmpeg,False)
    out.mkdir(parents=True,exist_ok=False);out=out.absolute()
    # Delay outcome labels until the corresponding real command has completed.
    defs=[
      (None,"A broken test","Run the same Python test on the revision.",None,None),
      ("bad_endpoint","Test failed","Revision 15 fails the reproducible test.",None,None),
      ("good_endpoint","Known endpoints","Revision 0 passes; revision 15 fails.",(0,15),None),
      ("setup","Sixteen revisions","One test, a controlled linear history.",(0,15),None),
      ("bisect_start","Git selects 7","Mark good and bad; test the midpoint.",(0,15),7),
      ("step1","Revision 7: PASS","Move the known good boundary.",(7,15),7),
      ("step2","Revision 11: FAIL","Move the known bad boundary.",(7,11),11),
      ("step3","Revision 9: PASS","Keep narrowing the range.",(9,11),9),
      ("step4","Revision 10: PASS","Only adjacent boundaries remain.",(10,11),10),
      ("identified","First bad: 11","Inspect the change from 42 to 41.",(10,11),11),
      ("fix","Repair the code","Reset bisect and restore return 42.",None,None),
      ("retest","Retest: PASS","The repaired example now passes the original test.",None,None),
      ("takeaway","Use reliable tests","Skipped revisions, merges and flaky tests complicate the search.",None,None)
    ]
    starts=[0 if ev is None else math.ceil((events[ev]["actual_seconds"]+.25)*10)*3 for ev,*_ in defs]
    need(starts==sorted(set(starts)) and starts[-1]<3360,"event timeline")
    # One timestamped note stream, not many expensive full-frame overlays.
    concat=["ffconcat version 1.0"];panels=[]
    for i,(ev,title,detail,bounds,test) in enumerate(defs):
        name=f"note-{i:02}.png";plate(title,detail,bounds,test).save(out/name)
        start=starts[i];end=starts[i+1] if i+1<len(starts) else 3360
        concat.extend([f"file '{name}'",f"duration {(end-start)/30:.9f}"])
        panels.append({"event":ev,"start_frame":start,"end_frame":end,"title":title})
    concat.append(f"file 'note-{len(defs)-1:02}.png'")
    (out/"notes.ffconcat").write_text("\n".join(concat)+"\n",encoding="utf-8")
    def ff(args):subprocess.run([ffmpeg,"-nostdin","-v","error",*map(str,args)],cwd=out,check=True)
    final=out/"GIT_CONTINUOUS_REVIEW.mp4";silent=out/"silent.mp4"
    prior=prior.absolute();capture=capture.absolute()
    filters="[1:v]fps=30,crop=820:420:0:40,scale=936:480:flags=lanczos,setsar=1[real];[0:v]drawbox=x=96:y=294:w=1000:h=510:color=0x132536:t=fill[base];[base][real]overlay=128:309:eof_action=repeat[hero];[2:v]fps=30,setsar=1[note];[hero][note]overlay=1120:294:eof_action=repeat[out]"
    print("Encoding continuous 112-second long pilot",flush=True)
    ff(["-i",prior,"-i",capture,"-f","concat","-safe","0","-i","notes.ffconcat","-filter_complex_threads","1","-filter_complex",filters,"-map","[out]","-an","-frames:v",3360,"-c:v","libx264","-preset","ultrafast","-crf","18","-threads","2","-pix_fmt","yuv420p",silent])
    ff(["-i",silent,"-i",prior,"-map","0:v:0","-map","1:a:0","-c","copy","-movflags","+faststart",final])
    print("Checking full decode, original audio and actual capture pixels",flush=True)
    inspect_video(final,[1920,1080],30,3360,ffmpeg,True);audio=inspect_audio(final,ffmpeg,5376000)
    with tempfile.TemporaryDirectory() as t:
        paths=[Path(t)/f"{i}.wav" for i in range(2)]
        for path,v in zip(paths,(prior,final)):ff(["-i",v,"-map","0:a:0","-ar","48000","-ac","1","-c:a","pcm_s16le",path])
        need(np.array_equal(pcm(paths[0]),pcm(paths[1])),"audio differs")
    src=cv2.VideoCapture(str(capture));vid=cv2.VideoCapture(str(final));obs=[];stills=[];changes=[];last=None
    samples=sorted(set([0,30,75,335,760,1140,1470,1815,2010,2175,2400,2510,2980,3359]))
    try:
        for i in range(90):
            ok,f=vid.read();need(ok,"opening decode")
            roi=cv2.cvtColor(f[309:789,128:1064],cv2.COLOR_BGR2GRAY);g=cv2.resize(roi,(180,90))
            if last is not None:
                delta=float(np.mean(cv2.absdiff(g,last)))
                if delta>.65:changes.append({"frame":i,"seconds":i/30,"delta":round(delta,4)})
            last=g
        for i in samples:
            vid.set(cv2.CAP_PROP_POS_FRAMES,i);ok,f=vid.read();need(ok,"missing final sample")
            roi=cv2.cvtColor(f[309:789,128:1064],cv2.COLOR_BGR2GRAY);errors=[]
            for j in range(max(0,round(i*c["fps"]/30)-1),min(c["frames"],round(i*c["fps"]/30)+2)):
                src.set(cv2.CAP_PROP_POS_FRAMES,j);good,z=src.read()
                if good:
                    ref=cv2.resize(cv2.cvtColor(z[40:460,0:820],cv2.COLOR_BGR2GRAY),(936,480),interpolation=cv2.INTER_LANCZOS4)
                    errors.append((float(np.mean(cv2.absdiff(roi,ref))),j))
            need(errors and min(errors)[0]<4,"capture match failure "+str(i))
            err,j=min(errors);obs.append({"frame":i,"source_frame":j,"error":round(err,4)})
            stills.append(Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).resize((480,270),Image.Resampling.LANCZOS))
    finally:src.release();vid.release()
    need(changes and changes[0]["seconds"]<=2 and any(1.5<=x["seconds"]<=3 for x in changes),"opening action not verified")
    sheet=Image.new("RGB",(1440,math.ceil(len(stills)/3)*294),"#09131F");d=ImageDraw.Draw(sheet)
    for j,im in enumerate(stills):
        xx=j%3*480;yy=j//3*294;sheet.paste(im,(xx,yy+24));d.text((xx+8,yy+5),f"Frame {samples[j]}",fill="white")
    sheet.save(out/"contact.jpg",quality=94)
    fix=events["fix"]["planned_seconds"];payoff=starts[11]/30;takeaway=starts[12]/30
    beats=[("hook",0,1.5,"Show the real failing test.","Run the failing test."),
           ("demonstration",1.5,24.7,"Establish reliable endpoints.","Check the passing revision."),
           ("cause",24.7,fix,"Use repeated test results to narrow the range.","Run bisect and inspect the first bad commit."),
           ("fix",fix,payoff,"The identified commit is a suspect, not an automatic repair.","Reset and repair the disposable program."),
           ("payoff",payoff,takeaway,"The result depends on the reliability of the test.","Display the successful retest."),
           ("takeaway",takeaway,112,"Use a reproducible test and reset the session.","Keep the verified example and limits visible.")]
    brief={"schema":SCHEMA,"episode_id":"fm_rc8_git_live_pilot","format":"long","series":"python_automation","duration_seconds":112,
      "title":"Find the first failing Git commit without checking every revision","viewer_problem":"Find the regression in a history of changes",
      "viewer_promise":"See Git bisect locate a real regression and verify a manual repair","source_url":"https://git-scm.com/docs/git-bisect",
      "demo":{"mode":"real_software_capture","application":"Python terminal","fixture_only":True,"recording_provenance":"first_party_executed_software","local_only":True},
      "approval":{"owner_watched_exact_video":False,"rights_reviewed":False,"facts_reviewed":False,"release_signed":False,"youtube_scheduled":False},
      "beats":[{"role":role,"start_seconds":lo,"end_seconds":hi,"visual_evidence":"actual_executed_software_frame","spoken_purpose":purpose,"action_or_result":action} for role,lo,hi,purpose,action in beats]}
    creative=validate_creative(brief)
    (out/"CREATIVE_BRIEF.json").write_text(json.dumps(brief,indent=2)+"\n",encoding="utf-8")
    need(not approval_allows_exact_video({"approved_video_sha256":sha(final)},sha(final)),"unsigned approval")
    report={"version":"1.0.0-rc8","pilot":"git","capture_sha256":sha(capture),"capture_report_sha256":sha(capture_dir/"LIVE_CAPTURE_QA.json"),"prior_sha256":sha(prior),"mp4_sha256":sha(final),"source_sha256":sha(D/"render_live_git_rc8.py"),"frames":3360,"resolution":[1920,1080],"audio":audio,"pcm_identical":True,"full_decode_pass":True,"observed":obs,"opening_changes":changes,"note_panels":panels,"source_crop":[0,40,820,420],"display_size":[936,480],"creative_brief_sha256":sha(out/"CREATIVE_BRIEF.json"),"creative_schema_result":creative,"repair_test_exit":0,"legacy_capture_receipt_compatible":False,"human_playback_approved":False,"release_authorized":False}
    (out/"LIVE_LONG_QA.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");print(json.dumps(report,indent=2))
def main():
    p=argparse.ArgumentParser();p.add_argument("--capture",type=Path,required=True);p.add_argument("--prior",type=Path,required=True);p.add_argument("--out",type=Path,required=True);p.add_argument("--ffmpeg",required=True);a=p.parse_args();run(a.capture.absolute(),a.prior.absolute(),a.out,a.ffmpeg)
if __name__=="__main__":main()
