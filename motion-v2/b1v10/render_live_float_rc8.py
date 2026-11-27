"""RC8 continuous recorded Python walkthrough, exact prior soundtrack, review only."""
import argparse,json,subprocess,tempfile
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
from production_review_rc6 import read,sha,exact,need,inspect_video,inspect_audio
from narration_review import pcm
from autopilot.branch1_recovery import SCHEMA,validate_creative
from scripts.publish_youtube import approval_allows_exact_video
D=Path(__file__).resolve().parent
# The whole console recording remains visible throughout. Graphic notes are supplemental.
BEATS=[
 ("hook",0,45,"REAL OUTPUT","0.1 + 0.2","Unexpected extra digits.","Show the actual sum."),
 ("demonstration",45,258,"REAL TEST","Equality returns False","Compare the calculated value.","Execute the equality test."),
 ("cause",258,472,"WHY IT HAPPENS","Binary approximation","Compare stored fraction and 1/10.","Inspect the exact stored fraction."),
 ("fix",472,504,"USE DECIMAL STRINGS","Decimal('0.1')","Use exact decimal inputs.","Show the replacement expression."),
 ("payoff",504,585,"VERIFIED RESULT","0.3","The decimal sum matches.","Compute and verify the decimal result."),
 ("takeaway",585,661,"REMEMBER","Use strings for Decimal","Precision limits still apply.","Keep the verified output visible.")
]
def make_plate(title,main,detail):
 im=Image.new("RGB",(824,300),"#132536");d=ImageDraw.Draw(im)
 d.rounded_rectangle((1,1,822,298),22,outline="#45627A",width=2)
 for s,y,n,col in [(title,24,30,"#72E3ED"),(main,91,49,"#D1FA83"),(detail,195,31,"#F3F7FC")]:
  font=ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf",n);need(d.textlength(s,font=font)<770,"note overflow");d.text((28,y),s,font=font,fill=col)
 return im
def run(capture_dir,prior,out,ffmpeg):
 c=json.loads((capture_dir/"LIVE_CAPTURE_QA.json").read_text());old=next(x for x in read("RC7_EDITORIAL_QA.json")["pilots"] if x["pilot"]=="float")
 cap=capture_dir/"FLOAT_LIVE_CAPTURE.mp4";exact(cap,c["capture_sha256"]);exact(prior,old["mp4_sha256"])
 need(c["continuous"] is True and c["release_authorized"] is False and c["dimensions"]==[870,494],"capture scope")
 for k,h in c["source_sha256"].items():exact(D/k,h)
 inspect_video(cap,c["dimensions"],c["fps"],c["frames"],ffmpeg,False)
 out.mkdir(parents=True,exist_ok=False);out=out.absolute()
 hero=Image.new("RGB",(824,606),"#132536");d=ImageDraw.Draw(hero);d.rounded_rectangle((1,1,822,604),22,outline="#45627A",width=2)
 for txt,y,n in [("CONTINUOUS SOFTWARE RECORDING",24,28),("Actual Python execution / controlled example",530,28)]:
  font=ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf",n);need(d.textlength(txt,font=font)<768,"hero overflow");d.text((28,y),txt,font=font,fill="#72E3ED")
 hero.save(out/"hero.png")
 for i,(_,start,end,kicker,main,detail,_) in enumerate(BEATS):make_plate(kicker,main,detail).save(out/f"note-{i}.png")
 # Native 870x494 capture: fit width, preserve aspect ratio, no invented UI.
 filters=["[1:v]fps=30,scale=792:450:flags=lanczos,setsar=1,tpad=stop_mode=clone:stop_duration=1[real]","[0:v][2:v]overlay=72:440[base]","[base][real]overlay=88:514:eof_action=repeat[hero]"]
 last="hero"
 for i,(_,start,end,*_) in enumerate(BEATS):
  filters.append(f"[{last}][{i+3}:v]overlay=72:1070:enable='between(n,{start},{end-1})'[n{i}]");last=f"n{i}"
 def ff(args):subprocess.run([ffmpeg,"-nostdin","-v","error",*map(str,args)],check=True)
 final=out/"FLOAT_CONTINUOUS_REVIEW.mp4";silent=out/"silent.mp4"
 ff(["-i",prior,"-i",cap,"-i",out/"hero.png",*[v for i in range(len(BEATS)) for v in ("-i",out/f"note-{i}.png")],"-filter_complex_threads","1","-filter_complex",";".join(filters),"-map",f"[{last}]","-an","-frames:v",661,"-c:v","libx264","-preset","ultrafast","-crf","18","-threads","2","-pix_fmt","yuv420p",silent])
 ff(["-i",silent,"-i",prior,"-map","0:v:0","-map","1:a:0","-c","copy","-movflags","+faststart",final])
 inspect_video(final,[1080,1920],30,661,ffmpeg,True);audio=inspect_audio(final,ffmpeg,1057600)
 with tempfile.TemporaryDirectory() as t:
  w=[Path(t)/f"{i}.wav" for i in range(2)]
  for path,v in zip(w,(prior,final)):ff(["-i",v,"-map","0:a:0","-ar","48000","-ac","1","-c:a","pcm_s16le",path])
  need(np.array_equal(pcm(w[0]),pcm(w[1])),"audio differs")
 src=cv2.VideoCapture(str(cap));vid=cv2.VideoCapture(str(final));obs=[];stills=[];changes=[];last=None
 samples={0,30,75,300,390,490,535,610,660}
 try:
  i=0
  while True:
   ok,f=vid.read()
   if not ok:break
   roi=cv2.cvtColor(f[514:964,88:880],cv2.COLOR_BGR2GRAY);g=cv2.resize(roi,(180,90))
   if last is not None:
    delta=float(np.mean(cv2.absdiff(g,last)))
    if delta>.65:changes.append({"frame":i,"seconds":i/30,"delta":round(delta,4)})
   last=g
   if i in samples:
    # FPS conversion may choose adjacent source samples at boundaries.
    errors=[]
    for j in range(max(0,round(i*c["fps"]/30)-1),min(c["frames"],round(i*c["fps"]/30)+2)):
     src.set(cv2.CAP_PROP_POS_FRAMES,j);good,z=src.read()
     if good:
      ref=cv2.resize(cv2.cvtColor(z,cv2.COLOR_BGR2GRAY),(792,450),interpolation=cv2.INTER_LANCZOS4)
      errors.append((float(np.mean(cv2.absdiff(roi,ref))),j))
    need(errors and min(errors)[0]<4,"continuous footage mismatch")
    err,j=min(errors);obs.append({"frame":i,"source_frame":j,"error":round(err,4)})
    stills.append(Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).resize((360,640),Image.Resampling.LANCZOS))
   i+=1
  need(i==661 and len(obs)==len(samples),"missing frames")
 finally:src.release();vid.release()
 need(len(changes)>=6 and changes[0]["seconds"]<=2 and any(1.5<=x["seconds"]<=3 for x in changes),"final opening action absent")
 sheet=Image.new("RGB",(1080,3*664),"#09131F");d=ImageDraw.Draw(sheet)
 for j,im in enumerate(stills):xx=j%3*360;yy=j//3*664;sheet.paste(im,(xx,yy+24));d.text((xx+8,yy+5),f"Frame {obs[j]['frame']}",fill="white")
 sheet.save(out/"contact.jpg",quality=94)
 brief={"schema":SCHEMA,"episode_id":"fm_rc8_float_live_pilot","format":"short","series":"python_automation","duration_seconds":661/30,"title":"Why Python prints extra digits when adding 0.1 and 0.2","viewer_problem":"Unexpected floating point equality result","viewer_promise":"See actual calculation, cause and decimal-string alternative","source_url":"https://docs.python.org/3/tutorial/floatingpoint.html","demo":{"mode":"real_software_capture","application":"Python terminal","fixture_only":True,"recording_provenance":"first_party_executed_software","local_only":True},"approval":{"owner_watched_exact_video":False,"rights_reviewed":False,"facts_reviewed":False,"release_signed":False,"youtube_scheduled":False},"beats":[{"role":role,"start_seconds":lo/30,"end_seconds":hi/30,"visual_evidence":"actual_executed_software_frame","spoken_purpose":detail,"action_or_result":action} for role,lo,hi,_,_,detail,action in BEATS]}
 creative=validate_creative(brief)
 (out/"CREATIVE_BRIEF.json").write_text(json.dumps(brief,indent=2)+"\n",encoding="utf-8")
 need(not approval_allows_exact_video({"approved_video_sha256":sha(final)},sha(final)),"unsigned approval")
 report={"version":"1.0.0-rc8","pilot":"float","capture_sha256":sha(cap),"capture_report_sha256":sha(capture_dir/"LIVE_CAPTURE_QA.json"),"prior_sha256":sha(prior),"mp4_sha256":sha(final),"source_sha256":sha(D/"render_live_float_rc8.py"),"frames":661,"resolution":[1080,1920],"audio":audio,"pcm_identical":True,"full_decode_pass":True,"observed":obs,"actual_changes":changes,"creative_brief_sha256":sha(out/"CREATIVE_BRIEF.json"),"creative_schema_result":creative,"legacy_capture_receipt_compatible":False,"human_playback_approved":False,"release_authorized":False}
 (out/"LIVE_SHORT_QA.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");print(json.dumps(report,indent=2))
def main():
 p=argparse.ArgumentParser();p.add_argument("--capture",type=Path,required=True);p.add_argument("--prior",type=Path,required=True);p.add_argument("--out",type=Path,required=True);p.add_argument("--ffmpeg",required=True);a=p.parse_args();run(a.capture.absolute(),a.prior.absolute(),a.out,a.ffmpeg)
if __name__=="__main__":main()
