"""Generate a new native-HD Short from a researched topic, measured narration and live capture."""
import argparse,json,math,subprocess,tempfile
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
from production_review_rc6 import read,sha,exact,need,inspect_video,inspect_audio
from narration_review import pcm,validate_words
from sound_mix import mix,write
from render_float_short import ass
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
VIEWER_NOTES={"zip_crc":["Opening is not an integrity check.","The test identifies note.txt.","Stored and computed CRC differ.","Test both copies, not just the listing.","Broken: note.txt. Intact: None.","CRC detects errors, not authenticity."],"sql_null":["The query returned zero rows.","Four customers; two blocked-list entries.","WHERE only keeps TRUE.","Use a matching-row test.","Both fixes return 1, 3, 4.","Decide whether outer NULL belongs."],"path_suffix":["The original file is still on disk.","A new path is not a new file.","Original exists. New path does not.","Check the destination before renaming.","New name. Same file contents.","A new extension does not convert the file."]}
def plate(topic,i):
    if topic["format"]=="long":
        im=Image.new("RGB",(1920,1080),"#09131F");d=ImageDraw.Draw(im)
        role,title,_,_=topic["scenes"][i]
        text(d,"FLOWMINUTE / REAL SQL",96,80,30,1728,"#72E3ED",True)
        need(text(d,title,96,142,70,1728,"#F3F7FC",True)<=1,"header overflow")
        for box in [(96,294,1095,804),(1120,294,1823,804),(96,828,1823,975)]:
            d.rounded_rectangle(box,22,fill="#132536",outline="#45627A",width=2)
        text(d,"ACTUAL SQLITE RECORDING",120,310,26,950,"#72E3ED",True)
        text(d,role.upper(),1150,325,30,640,"#72E3ED",True)
        need(text(d,VIEWER_NOTES[topic["id"]][i],1150,404,55,640,"#F3F7FC",True)<=4,"proof overflow")
        # Simple table-derived illustrations; avoid inventing data.
        if i>=4:
            for j,k in enumerate([1,3,4]):
                x=1150+j*207;d.rounded_rectangle((x,680,x+180,753),12,fill="#24485F",outline="#D1FA83",width=2);d.text((x+90,716),str(k),font=font(42,True),anchor="mm",fill="#D1FA83")
        else:
            text(d,"Synthetic database",1150,726,28,640,"#B7CBDD")
        for j in range(6):
            x=96+j*288;d.rounded_rectangle((x,810,x+274,818),4,fill="#D1FA83" if j<=i else "#45627A")
        return im
    im=Image.new("RGB",(1080,1920),"#09131F");d=ImageDraw.Draw(im)
    role,title,_,action=topic["scenes"][i]
    text(d,"FLOWMINUTE / REAL PYTHON",72,192,30,824,"#72E3ED",True)
    need(text(d,title,72,260,65,824,"#F3F7FC",True)<=2,"header overflow")
    for box in [(72,440,895,1045),(72,1070,895,1369),(72,1394,895,1559)]:
        d.rounded_rectangle(box,22,fill="#132536",outline="#45627A",width=2)
    text(d,"ACTUAL SOFTWARE RECORDING",100,458,28,768,"#72E3ED",True)
    text(d,"Controlled local file / not personal data",100,999,27,768,"#B7CBDD")
    text(d,role.upper(),100,1094,30,768,"#72E3ED",True)
    need(text(d,VIEWER_NOTES[topic["id"]][i],100,1161,43,768,"#F3F7FC",True)<=3,"proof text overflow")
    for j in range(6):
        x=72+j*138;d.rounded_rectangle((x,1378,x+126,1386),4,fill="#D1FA83" if j<=i else "#45627A")
    return im
def run(key,day,folder,capture_dir,out,ffmpeg):
    topic=read("RC9_SQL_TOPIC_R3.json") if key=="sql_null" else next(t for t in read("RC9_TOPIC_BANK.json") if t["id"]==key)
    long=topic["format"]=="long";dims=[1920,1080] if long else [1080,1920]

    n=load(folder/"audio/NARRATION_REVIEW_QA.json");c=load(capture_dir/"LIVE_CAPTURE_QA.json")
    cap=capture_dir/"DAILY_LIVE_CAPTURE.mp4";exact(cap,c["capture_sha256"]);exact(folder/"audio/narration.wav",n["narration_sha256"])
    exact(folder/"audio/NARRATION_REVIEW_QA.json",c["narration_report_sha256"])
    exact(folder/"narration_spec.json",n["spec_sha256"])
    need(n["asr_screen_pass"] is True and n["release_authorized"] is False and c["topic"]==key and c["release_authorized"] is False,"review hold")
    need([s[2] for s in topic["scenes"]]==[t["expected"] for t in n["scene_timeline"]],"topic narration mismatch")
    cp=folder/"audio/word_captions.json";exact(cp,n["word_captions_sha256"]);cues=load(cp)
    validate_words([w for cue in cues for w in cue["words"]],n["duration_seconds"])
    total=n["frames_at_30fps"];out.mkdir(parents=True,exist_ok=False);out=out.absolute()
    brief={"schema":SCHEMA,"episode_id":"fm_"+day.replace("-","")+"_"+key+"_"+topic["format"],"format":topic["format"],"series":"python_automation","duration_seconds":total/30,"title":topic["title"],"viewer_problem":"Unexpected result from a real software operation","viewer_promise":"See the actual operation and verify its effect","source_url":topic["source_url"],"demo":{"mode":"real_software_capture","application":"Python terminal","fixture_only":True,"recording_provenance":"first_party_executed_software","local_only":True},"approval":{"owner_watched_exact_video":False,"rights_reviewed":False,"facts_reviewed":False,"release_signed":False,"youtube_scheduled":False},"beats":[{"role":s[0],"start_seconds":t["start_frame"]/30,"end_seconds":t["end_frame"]/30,"visual_evidence":"actual_executed_software_frame","spoken_purpose":s[2],"action_or_result":s[3]} for s,t in zip(topic["scenes"],n["scene_timeline"])]}
    receipt={"schema":RECEIPT_SCHEMA,"episode_id":brief["episode_id"],"capture_method":METHOD,"capture_sha256":c["capture_sha256"],"capture_bytes":cap.stat().st_size,"brief_sha256":brief_digest(brief),"evidence_sha256":sha(capture_dir/"LIVE_CAPTURE_QA.json"),"private_data":False,"release_approved":False,"youtube_uploads":0}
    def save(name,obj):(out/name).write_text(json.dumps(obj,indent=2)+"\n",encoding="utf8")
    save("CREATIVE_BRIEF.json",brief);save("CAPTURE_RECEIPT.json",receipt)
    identity=verify_capture(brief,cap,out/"CAPTURE_RECEIPT.json",windows_evidence=capture_dir/"LIVE_CAPTURE_QA.json")
    inspect_video(cap,c["dimensions"],c["fps"],c["frames"],ffmpeg,False)
    concat=["ffconcat version 1.0"]
    for i,t in enumerate(n["scene_timeline"]):
        name=f"plate-{i}.png";plate(topic,i).save(out/name);concat.extend([f"file '{name}'",f"duration {(t['end_frame']-t['start_frame'])/30:.9f}"])
    concat.append(f"file 'plate-{len(n['scene_timeline'])-1}.png'");(out/"plates.ffconcat").write_text("\n".join(concat)+"\n",encoding="utf8")
    ass(out/"captions.ass",cues)
    if long:
        path=out/"captions.ass";a=path.read_text(encoding="utf8").replace("PlayResX: 1080","PlayResX: 1920").replace("PlayResY: 1920","PlayResY: 1080").replace("Segoe UI,49,","Segoe UI,43,").replace("pos(484,1476)","pos(960,902)").replace("clip(82,1400,886,1550)","clip(108,840,1812,964)");path.write_text(a,encoding="utf8")
    events=[{"sample":n["scene_timeline"][i]["start_frame"]*1600,"effect":effect} for i,effect in [(1,"soft_tick"),(3,"soft_sweep"),(4,"reveal_pulse")]]
    v=pcm(folder/"audio/narration.wav").astype(np.float64)/32768;y,_,_=mix(v,events);write(out/"mix.wav",y)
    def ff(args):subprocess.run([ffmpeg,"-nostdin","-v","error",*map(str,args)],cwd=out,check=True)
    final=out/("NEW_DAILY_LONG_REVIEW.mp4" if long else "NEW_DAILY_SHORT_REVIEW.mp4")
    crop=(0,40,820,390) if long else (0,40,680,400);dw,dh=(944,448) if long else (792,466);xx,yy=(124,349) if long else (88,520);cx,cy,cw,ch=crop
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
    result={"version":"1.0.0-rc9-phase3","topic":key,"episode_id":brief["episode_id"],"resolution":dims,"fps":30,"frames":total,"duration_seconds":total/30,"voice":n["voice"],"audio":audio,"capture_sha256":c["capture_sha256"],"capture_report_sha256":sha(capture_dir/"LIVE_CAPTURE_QA.json"),"narration_report_sha256":sha(folder/"audio/NARRATION_REVIEW_QA.json"),"spec_sha256":n["spec_sha256"],"mp4_sha256":sha(final),"render_source_sha256":sha(Path(__file__)),"creative_brief_sha256":sha(out/"CREATIVE_BRIEF.json"),"receipt_sha256":sha(out/"CAPTURE_RECEIPT.json"),"identity":identity,"observed":observed,"opening_changes":changes,"full_decode_pass":True,"human_playback_approved":False,"release_authorized":False}
    save("NEW_LONG_QA.json" if long else "NEW_SHORT_QA.json",result);print(json.dumps(result,indent=2))
def main():
    p=argparse.ArgumentParser();p.add_argument("--topic",choices=["zip_crc","sql_null"],required=True);p.add_argument("--day",required=True);p.add_argument("--folder",type=Path,required=True);p.add_argument("--capture",type=Path,required=True);p.add_argument("--out",type=Path,required=True);p.add_argument("--ffmpeg",required=True);a=p.parse_args()
    run(a.topic,a.day,a.folder.absolute(),a.capture.absolute(),a.out,a.ffmpeg)
if __name__=="__main__":main()
