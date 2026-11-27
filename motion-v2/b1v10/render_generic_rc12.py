"""Generate a new native-HD Short from a researched topic, measured narration and live capture."""
import argparse,json,math,subprocess,tempfile
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
from production_review_rc6 import read,sha,exact,need,inspect_video,inspect_audio
from narration_review import pcm,validate_words,normalized
from sound_mix import mix,write
from render_float_short import ass
from select_topics_rc12 import steps, BANK
from polish_shorts_rc11 import caption_script
from autopilot.branch1_recovery import SCHEMA,verify_capture
from autopilot.branch1_windows_capture import SCHEMA as RECEIPT_SCHEMA,METHOD,brief_digest
from scripts.publish_youtube import approval_allows_exact_video
D=Path(__file__).resolve().parent
def load(p):return json.loads(p.read_text(encoding="utf8"))
def font(n,bold=False):return ImageFont.truetype("C:/Windows/Fonts/"+("segoeuib.ttf" if bold else "segoeui.ttf"),n)
def text(d,s,x,y,n,w,color,bold=False):
    f=font(n,bold);lines=[];line=""
    for word in s.split():
        v=(line+" "+word).strip()
        if line and d.textlength(v,font=f)>w:lines.append(line);line=word
        else:line=v
    if line:lines.append(line)
    need(all(d.textlength(v,font=f)<=w for v in lines),"unbreakable text")
    for j,v in enumerate(lines):d.text((x,y+j*int(n*1.2)),v,font=f,fill=color)
    return len(lines)
def plate(topic,i,results):
    long=topic["format"]=="long"
    im=Image.new("RGB",(1920,1080) if long else (1080,1920),"#09131F");d=ImageDraw.Draw(im)
    x,y,w=(96,80,1728) if long else (72,192,824)
    text(d,"FLOWMINUTE / REAL SOFTWARE",x,y,30,w,"#72E3ED",True)
    title="Watch the experiment" if i==0 else topic["head"][i-1]
    need(text(d,title,x,y+62,60,w,"#F3F7FC",True)<=2,"header overflow")
    boxes=[(96,294,1095,804),(1120,294,1823,804),(96,828,1823,975)] if long else [(72,354,896,744),(72,836,896,1332),(72,1385,896,1559)]
    for box in boxes:d.rounded_rectangle(box,22,fill="#132536",outline="#45627A",width=2)
    ax,ay,aw=(1150,326,640) if long else (100,376,768)
    text(d,"EXPLANATION / RESULT",ax,ay,29,aw,"#72E3ED",True)
    val="Run the test" if i==0 else repr(results[i-1]["result"])
    # Result values are generated from the bounded experiment, not marketing text.
    need(text(d,val,ax,ay+70,60 if len(val)<20 else 39,aw,"#D1FA83" if i>=4 else "#F3F7FC",True)<=3,"result overflow")
    note="Actual recording below" if i==0 else topic["notes"][i-1]
    need(text(d,note,ax,ay+245,36,aw,"#B7CBDD")<=3,"note overflow")
    bx,by=(120,310) if long else (98,854)
    text(d,"ACTUAL SOFTWARE RECORDING",bx,by,28,950 if long else 770,"#72E3ED",True)
    for j in range(6):
        start=96+j*288 if long else 72+j*138
        d.rounded_rectangle((start,810 if long else 1354,start+(274 if long else 126),818 if long else 1365),4,fill="#D1FA83" if j<i else "#45627A")
    return im
def run(key,day,folder,capture_dir,out,ffmpeg):
    topic=load(folder/"topic.json");base=next(t for t in load(D/BANK) if t["id"]==key);need(all(topic[k]==v for k,v in base.items()),"topic mismatch");results=steps(topic)
    long=topic["format"]=="long";dims=[1920,1080] if long else [1080,1920]

    n=load(folder/"audio/NARRATION_REVIEW_QA.json");c=load(capture_dir/"LIVE_CAPTURE_QA.json")
    cap=capture_dir/"DAILY_LIVE_CAPTURE.mp4";exact(cap,c["capture_sha256"]);exact(folder/"audio/narration.wav",n["narration_sha256"])
    exact(folder/"audio/NARRATION_REVIEW_QA.json",c["narration_report_sha256"])
    exact(folder/"narration_spec.json",n["spec_sha256"])
    need(n["asr_screen_pass"] is True and n["release_authorized"] is False and c["topic"]==key and c["release_authorized"] is False,"review hold")
    need([s[2] for s in topic["scenes"]]==[t["expected"] for t in n["scene_timeline"]],"topic narration mismatch")
    exact(folder/"topic.json",c["topic_sha256"]);need([e["result"] for e in c["events"]]==[r["result"] for r in results],"experiment mismatch")
    cp=folder/"audio/word_captions.json";exact(cp,n["word_captions_sha256"]);cues=load(cp)
    validate_words([w for cue in cues for w in cue["words"]],n["duration_seconds"])
    need(normalized(" ".join(w["word"] for cue in cues for w in cue["words"]))==normalized(" ".join(s[2] for s in topic["scenes"])),"caption review needed before rendering")
    total=n["frames_at_30fps"];out.mkdir(parents=True,exist_ok=False);out=out.absolute()
    brief={"schema":SCHEMA,"episode_id":"fm_"+day.replace("-","")+"_"+key+"_"+topic["format"],"format":topic["format"],"series":"python_automation","duration_seconds":total/30,"title":topic["title"],"viewer_problem":"Unexpected result from a real software operation","viewer_promise":"See the actual operation and verify its effect","source_url":topic["source_url"],"demo":{"mode":"real_software_capture","application":"Python terminal","fixture_only":True,"recording_provenance":"first_party_executed_software","local_only":True},"approval":{"owner_watched_exact_video":False,"rights_reviewed":False,"facts_reviewed":False,"release_signed":False,"youtube_scheduled":False},"beats":[{"role":s[0],"start_seconds":t["start_frame"]/30,"end_seconds":t["end_frame"]/30,"visual_evidence":"actual_executed_software_frame","spoken_purpose":s[2],"action_or_result":s[3]} for s,t in zip(topic["scenes"],n["scene_timeline"])]}
    receipt={"schema":RECEIPT_SCHEMA,"episode_id":brief["episode_id"],"capture_method":METHOD,"capture_sha256":c["capture_sha256"],"capture_bytes":cap.stat().st_size,"brief_sha256":brief_digest(brief),"evidence_sha256":sha(capture_dir/"LIVE_CAPTURE_QA.json"),"private_data":False,"release_approved":False,"youtube_uploads":0}
    def save(name,obj):(out/name).write_text(json.dumps(obj,indent=2)+"\n",encoding="utf8")
    save("CREATIVE_BRIEF.json",brief);save("CAPTURE_RECEIPT.json",receipt)
    identity=verify_capture(brief,cap,out/"CAPTURE_RECEIPT.json",windows_evidence=capture_dir/"LIVE_CAPTURE_QA.json")
    inspect_video(cap,c["dimensions"],c["fps"],c["frames"],ffmpeg,False)
    # Match each result to a measured visual change, delay labels to avoid early reveal.
    starts=[0]
    for e in c["events"]:
        candidates=[v["frame"]*5 for v in c["changes"] if e["actual_seconds"]-.02<=v["seconds"]<=e["actual_seconds"]+.55]
        need(candidates,"missing recorded event change")
        starts.append(max(starts[-1]+1,candidates[0]+3))
    need(len(starts)==7 and starts==sorted(set(starts)) and starts[-1]<total,"diagram timing")
    concat=["ffconcat version 1.0"]
    for i,t in enumerate(starts):
        name=f"plate-{i}.png";plate(topic,i,results).save(out/name);end=starts[i+1] if i+1<len(starts) else total;concat.extend([f"file '{name}'",f"duration {(end-t)/30:.9f}"])
    concat.append("file 'plate-6.png'");(out/"plates.ffconcat").write_text("\n".join(concat)+"\n",encoding="utf8")
    if long:
        ass(out/"captions.ass",cues)
        path=out/"captions.ass";a=path.read_text(encoding="utf8").replace("PlayResX: 1080","PlayResX: 1920").replace("PlayResY: 1920","PlayResY: 1080").replace("Segoe UI,49,","Segoe UI,43,").replace("pos(484,1476)","pos(960,902)").replace("clip(82,1400,886,1550)","clip(108,840,1812,964)");path.write_text(a,encoding="utf8")
    else:caption_script(out/"captions.ass",cues)
    events=[{"sample":n["scene_timeline"][i]["start_frame"]*1600,"effect":effect} for i,effect in [(1,"soft_tick"),(3,"soft_sweep"),(4,"reveal_pulse")]]
    v=pcm(folder/"audio/narration.wav").astype(np.float64)/32768;y,_,_=mix(v,events);write(out/"mix.wav",y)
    def ff(args):subprocess.run([ffmpeg,"-nostdin","-v","error",*map(str,args)],cwd=out,check=True)
    final=out/("NEW_DAILY_LONG_REVIEW.mp4" if long else "NEW_DAILY_SHORT_REVIEW.mp4")
    # Compute the crop from every actual frame, including all bright text.
    v=cv2.VideoCapture(str(cap));right=0;bottom=0;cnt=0
    while True:
        ok,f=v.read()
        if not ok:break
        ys,xs=np.where(cv2.cvtColor(f,cv2.COLOR_BGR2GRAY)[60:,:]>100)
        if len(xs):right=max(right,int(xs.max())+1);bottom=max(bottom,int(ys.max())+1)
        cnt+=1
    v.release();need(cnt==c["frames"],"capture decode")
    cw=min(c["dimensions"][0],max(360,(right+15)//2*2));ch=min(c["dimensions"][1]-60,max(220,(bottom+15)//2*2))
    cx,cy=0,60
    maxw,maxh=(944,440) if long else (800,414)
    scale=min(maxw/cw,maxh/ch,2.0);dw=round(cw*scale/2)*2;dh=round(ch*scale/2)*2
    xx,yy=(596-dw//2,350) if long else (484-dw//2,902)
    xx=xx//2*2
    filters=f"[0:v]fps=30,setsar=1,tpad=stop_mode=clone:stop_duration=1[base];[1:v]fps=30,crop={cw}:{ch}:{cx}:{cy},scale={dw}:{dh}:flags=lanczos,setsar=1[real];[base][real]overlay={xx}:{yy}:eof_action=repeat,ass=captions.ass[out]"
    ff(["-f","concat","-safe","0","-i","plates.ffconcat","-i",cap,"-filter_complex_threads","1","-filter_complex",filters,"-map","[out]","-an","-frames:v",total,"-c:v","libx264","-preset","fast","-crf","18","-threads","2","-pix_fmt","yuv420p","silent.mp4"])
    ff(["-i","silent.mp4","-i","mix.wav","-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k","-movflags","+faststart",final])
    inspect_video(final,dims,30,total,ffmpeg,True);audio=inspect_audio(final,ffmpeg,total*1600)
    src=cv2.VideoCapture(str(cap));vid=cv2.VideoCapture(str(final));observed=[];changes=[];last=None;stills=[]
    samples=sorted(set([0,30,75]+[(s["start_frame"]+s["end_frame"])//2 for s in n["scene_timeline"]]+[total-1]))
    try:
        for i in range(90):
            ok,f=vid.read();need(ok,"opening decode")
            g=cv2.resize(cv2.cvtColor(f[yy:yy+dh,xx:xx+dw],cv2.COLOR_BGR2GRAY),(180,90))
            if last is not None:
                delta=float(np.mean(cv2.absdiff(g,last)))
                if delta>.65:changes.append({"frame":i,"seconds":i/30,"delta":round(delta,4)})
            last=g
        for i in samples:
            vid.set(cv2.CAP_PROP_POS_FRAMES,i);ok,f=vid.read();need(ok,"sample unavailable")
            roi=cv2.cvtColor(f[yy:yy+dh,xx:xx+dw],cv2.COLOR_BGR2GRAY);errors=[]
            for j in range(max(0,round(i*c["fps"]/30)-1),min(c["frames"],round(i*c["fps"]/30)+2)):
                src.set(cv2.CAP_PROP_POS_FRAMES,j);good,z=src.read()
                if good:
                    ref=cv2.resize(cv2.cvtColor(z[cy:cy+ch,cx:cx+cw],cv2.COLOR_BGR2GRAY),(dw,dh),interpolation=cv2.INTER_LANCZOS4)
                    errors.append((float(np.mean(cv2.absdiff(roi,ref))),j))
            need(errors and min(errors)[0]<4,"source pixel mismatch")
            err,j=min(errors);observed.append({"frame":i,"source_frame":j,"error":round(err,4)})
            stills.append(Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).resize((480,270) if long else (360,640),Image.Resampling.LANCZOS))
    finally:src.release();vid.release()
    need(changes and changes[0]["seconds"]<=2 and any(1.5<=x["seconds"]<=3 for x in changes),"opening action not visible")
    sw,sh=(480,270) if long else (360,640);sheet=Image.new("RGB",(sw*3,math.ceil(len(stills)/3)*(sh+24)),"#09131F");d=ImageDraw.Draw(sheet)
    for j,im in enumerate(stills):
        x=j%3*sw;yy=j//3*(sh+24);sheet.paste(im,(x,yy+24));d.text((x+6,yy+5),f"Frame {samples[j]}",fill="white")
    sheet.save(out/"contact.jpg",quality=94)
    need(not approval_allows_exact_video({"approved_video_sha256":sha(final)},sha(final)),"unsigned acceptance")
    result={"version":"1.0.0-rc12-phase2","topic":key,"episode_id":brief["episode_id"],"resolution":dims,"fps":30,"frames":total,"duration_seconds":total/30,"voice":n["voice"],"audio":audio,"capture_sha256":c["capture_sha256"],"capture_report_sha256":sha(capture_dir/"LIVE_CAPTURE_QA.json"),"narration_report_sha256":sha(folder/"audio/NARRATION_REVIEW_QA.json"),"spec_sha256":n["spec_sha256"],"mp4_sha256":sha(final),"render_source_sha256":sha(Path(__file__)),"topic_sha256":sha(folder/"topic.json"),"design_dependency_sha256":sha(D/"polish_shorts_rc11.py"),"event_starts_frames":starts,"source_crop":[cx,cy,cw,ch],"display_rect":[xx,yy,dw,dh],"creative_brief_sha256":sha(out/"CREATIVE_BRIEF.json"),"receipt_sha256":sha(out/"CAPTURE_RECEIPT.json"),"identity":identity,"observed":observed,"opening_changes":changes,"full_decode_pass":True,"human_playback_approved":False,"release_authorized":False}
    save("NEW_LONG_QA.json" if long else "NEW_SHORT_QA.json",result);print(json.dumps(result,indent=2))
def main():
    p=argparse.ArgumentParser();p.add_argument("--topic",choices=["strip_chars","bounded_deque","counter_difference","partition_text","count_missing","union_duplicates"],required=True);p.add_argument("--day",required=True);p.add_argument("--folder",type=Path,required=True);p.add_argument("--capture",type=Path,required=True);p.add_argument("--out",type=Path,required=True);p.add_argument("--ffmpeg",required=True);a=p.parse_args()
    run(a.topic,a.day,a.folder.absolute(),a.capture.absolute(),a.out,a.ffmpeg)
if __name__=="__main__":main()
