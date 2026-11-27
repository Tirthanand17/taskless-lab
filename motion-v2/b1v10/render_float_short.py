"""RC5 original vertical float pilot, real captured evidence, offline review only."""
import argparse,json,subprocess,math
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
from narration_review import pcm,wav,energy,validate_words,normalized
from sound_mix import mix,measure
from integrate_real_long import sha,read,need
D=Path(__file__).resolve().parent
W,H=1080,1920
BG="#09131F";P="#132536";C="#72E3ED";L="#D1FA83";I="#F3F7FC";M="#B7CBDD";E="#45627A"
def font(n,bold=False,mono=False):
 return ImageFont.truetype("C:/Windows/Fonts/"+("consola.ttf" if mono else "segoeuib.ttf" if bold else "segoeui.ttf"),n)
def txt(d,xy,s,n,color=I,bold=False,mono=False):
 f=font(n,bold,mono);need(d.textlength(s,font=f)<=824,"text too wide "+s);d.text(xy,s,font=f,fill=color)
def center(d,y,s,n,color=I,bold=False,mono=False):
 f=font(n,bold,mono);width=d.textlength(s,font=f);need(width<=780,"center text too wide "+s);d.text((484-width/2,y),s,font=f,fill=color)
def base(idx,phase,frames):
 im=Image.new("RGB",(W,H),BG);d=ImageDraw.Draw(im)
 txt(d,(72,190),"FLOWMINUTE / PYTHON LAB",30,C,True)
 titles=[("Simple math.","Unexpected answer."),("The real result","Tiny extra digits."),("Why it happens","Binary approximation."),("Use decimal strings","Get the expected sum.")]
 txt(d,(72,246),titles[idx][0],66,I,True);txt(d,(72,329),titles[idx][1],54,L,True)
 for box in [(72,440,895,1045),(72,1070,895,1369),(72,1394,895,1559)]:
  d.rounded_rectangle(box,22,fill=P,outline=E,width=2)
 if idx==0:
  for j,v in enumerate(["0.1","0.2"]):
   x=112+408*j;d.rounded_rectangle((x+8,525,x+320,770),24,fill="#07111C");d.rounded_rectangle((x,510,x+312,755),24,fill="#24485F",outline=C,width=3)
   d.text((x+156,622),v,font=font(91,True),anchor="mm",fill=I)
  d.text((484,622),"+",font=font(65,True),fill=C,anchor="mm")
  center(d,842,"= ?" if phase==0 else "= 0.3 ?",94,L,True)
  txt(d,(100,1110),"PREDICT THE OUTPUT",31,C,True)
  txt(d,(100,1180),"What will Python print?",48,I,True)
  txt(d,(100,1270),"A tiny difference matters.",34,M)
 elif idx==1:
  center(d,530,"0.1 + 0.2",72,I,True)
  center(d,680,"0.30000000000000004",62,L,True,True)
  center(d,800,"The extra digit is real.",42,I,True)
  center(d,936,"Not exactly equal to 0.3",36,M)
 elif idx==2:
  center(d,490,"DECIMAL INPUT",30,C,True);center(d,550,"0.1 = 1/10",78,I,True)
  d.line((140,765,828,765),fill=M,width=5)
  for x in (140,484,828):d.line((x,748,x,782),fill=M,width=4)
  d.ellipse((464,745,504,785),fill=I)
  if phase:d.ellipse((525,745,565,785),fill=L);d.line((504,765,525,765),fill=L,width=4)
  center(d,830,"Exact target    vs    stored float",35,I,True)
  center(d,928,"Gap exaggerated for illustration",28,M)
 else:
  center(d,510,"Decimal",76,C,True)
  center(d,645,"'0.1' + '0.2'",65,I,True,True)
  center(d,795,"= 0.3",110,L,True)
  center(d,958,"Decimal arithmetic has precision limits.",28,M)
 # meaningful step marker, not perpetual motion.
 for j in range(4):d.rounded_rectangle((72+j*209,1378,72+j*209+195,1386),5,fill=L if j<=idx else E)
 return im
def at(t):
 n=round(t*100);h,n=divmod(n,360000);m,n=divmod(n,6000);s,n=divmod(n,100)
 return f"{h}:{m:02}:{s:02}.{n:02}"
def ass(path,cues):
 lines=["[Script Info]","ScriptType: v4.00+","PlayResX: 1080","PlayResY: 1920","WrapStyle: 2","[V4+ Styles]","Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding","Style: Main,Segoe UI,49,&H00FCF7F3,&H0083FAD1,&H00191007,&H00191007,-1,0,0,0,100,100,0,0,1,2,0,5,0,0,0,1","[Events]","Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
 for c in cues:
  ws=c["words"]
  for i,w in enumerate(ws):
   end=ws[i+1]["start"] if i+1<len(ws) else c["end"]
   if round(end*100)<=round(w["start"]*100):continue
   line=" ".join(("{\\c&H83FAD1&}"+x["word"]+"{\\c&HFCF7F3&}") if j==i else x["word"] for j,x in enumerate(ws))
   need(all(ch not in c["text"] for ch in ("{","}","\\")),"unsafe caption")
   # left safe region centered x=484; fit single or two lines at phone size.
   lines.append(f"Dialogue: 0,{at(w['start'])},{at(end)},Main,,0,0,0,,{{\\pos(484,1476)\\clip(82,1400,886,1550)}}"+line)
 path.write_text("\n".join(lines)+"\n",encoding="utf-8")
def main():
 p=argparse.ArgumentParser();p.add_argument("--audio",type=Path,required=True);p.add_argument("--capture",type=Path,required=True);p.add_argument("--out",type=Path,required=True);p.add_argument("--ffmpeg",required=True);a=p.parse_args()
 a.audio=a.audio.resolve();a.capture=a.capture.resolve();a.out=a.out.resolve()
 n=read(a.audio/"NARRATION_REVIEW_QA.json");c=read(a.capture/"FLOAT_CAPTURE_QA.json");source=a.capture/"FLOAT_CAPTURE.mp4"
 need(n["voice"]=="af_heart" and n["release_authorized"] is False and sha(a.audio/"narration.wav")==n["narration_sha256"],"narration changed")
 need(sha(source)==c["capture_sha256"] and c["frames"]==72 and c["dimensions"]==[870,494],"capture changed")
 cp=a.audio/"word_captions.json";need(sha(cp)==n["word_captions_sha256"],"caption hash")
 cues=read(cp);validate_words([w for c in cues for w in c["words"]],n["duration_seconds"])
 corrections=[]
 for cue in cues:
  for w in cue["words"]:
   old=w["word"]
   if old.startswith("-tenths"):w["word"]=old[1:]
   elif old=="decimal" and w["start"]>=n["scene_timeline"][3]["start_frame"]/30 and "use decimal" in cue["text"].lower():w["word"]="Decimal"
   if old!=w["word"]:corrections.append({"from":old,"to":w["word"],"start":w["start"],"end":w["end"]})
  cue["text"]=" ".join(w["word"] for w in cue["words"])
 need(normalized(" ".join(w["word"] for cue in cues for w in cue["words"]))==normalized(" ".join(s["expected"] for s in n["scene_timeline"])),"caption script mismatch")
 a.out.mkdir(parents=True,exist_ok=False);ass(a.out/"captions.ass",cues)
 (a.out/"caption_review.json").write_text(json.dumps({"corrections":corrections,"cues":cues,"release_authorized":False},indent=2)+"\n",encoding="utf-8")
 cap=cv2.VideoCapture(str(source));pages=[]
 for j in range(3):
  cap.set(cv2.CAP_PROP_POS_FRAMES,j*24+12);ok,f=cap.read();need(ok,"missing source frame");pages.append(f)
 cap.release()
 crops=[(0,65,355,164),(0,65,540,68),(0,65,550,164)]
 refs=[];records=[];parts=[];events=[]
 for idx,s in enumerate(n["scene_timeline"]):
  lo,hi=s["start_frame"],s["end_frame"];mid=lo+min(35,(hi-lo)//3) if idx==0 else lo+(hi-lo)//2
  for phase,(start,end) in enumerate(((lo,mid),(mid,hi))):
   im=base(idx,phase,end-start);d=ImageDraw.Draw(im)
   if idx:
    page=idx-1;x,y,w,h=crops[page];img=Image.fromarray(cv2.cvtColor(pages[page][y:y+h,x:x+w],cv2.COLOR_BGR2RGB))
    scale=min(2,760/w,205/h);dw,dh=round(w*scale)//2*2,round(h*scale)//2*2
    img=img.resize((dw,dh),Image.Resampling.LANCZOS);xx=484-dw//2;yy=1120+(205-dh)//2
    txt(d,(100,1082),"RECORDED PYTHON OUTPUT",27,C,True);im.paste(img,(xx,yy))
    if idx==2:txt(d,(100,1330),"Exact stored fraction of 0.1",24,M)
    if idx==3:txt(d,(100,1330),"Strings preserve the decimal inputs",24,M)
    if phase==1:
     refs.append(np.array(img.convert("L")));records.append({"page":page,"frame":(start+end)//2,"crop":list(crops[page]),"roi":[xx,yy,dw,dh]})
   name=f"state-{len(parts):02}.png";im.save(a.out/name);parts.append((name,end-start))
  if idx:events.append({"sample":lo*1600,"frame":lo,"scene":s["id"],"effect":["soft_tick","reveal_pulse","soft_ping"][idx-1]})
 v=pcm(a.audio/"narration.wav").astype(np.float64)/32768;y,b,e=mix(v,events);wav(a.out/"mix.wav",np.round(y*32768).astype(np.int16))
 concat=["ffconcat version 1.0"]
 for name,frames in parts:concat.extend([f"file '{name}'",f"duration {frames/30:.9f}"])
 concat.append(f"file '{parts[-1][0]}'");(a.out/"frames.ffconcat").write_text("\n".join(concat)+"\n",encoding="utf-8")
 def ff(args):subprocess.run([a.ffmpeg,"-nostdin","-v","error",*map(str,args)],cwd=a.out,check=True)
 total=n["frames_at_30fps"];final=a.out/"B1V10_FLOAT_PRECISION_REVIEW.mp4"
 print("Encoding",total,"frames",flush=True)
 ff(["-f","concat","-safe","0","-i","frames.ffconcat","-vf","fps=30,ass=captions.ass","-an","-frames:v",total,"-c:v","libx264","-preset","ultrafast","-crf","18","-threads","2","-filter_threads","1","-pix_fmt","yuv420p","silent.mp4"])
 ff(["-i","silent.mp4","-i","mix.wav","-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k","-movflags","+faststart",final])
 ff(["-xerror","-i",final,"-map","0:v:0","-map","0:a:0","-f","null","-"])
 ff(["-i",final,"-map","0:a:0","-ar","48000","-ac","1","-c:a","pcm_s16le","decoded.wav"])
 x=pcm(a.out/"decoded.wav");need(len(x)==n["samples"],"decoded audio clock")
 loud=measure(a.ffmpeg,final);need(-20<=loud["input_i"]<=-13 and loud["input_tp"]<=-1 and energy(x)["clipped_samples"]==0,"audio quality")
 cap=cv2.VideoCapture(str(final));w,h=int(cap.get(3)),int(cap.get(4));fps=cap.get(5);i=0;observed=[];stills=[]
 sample={r["frame"]:j for j,r in enumerate(records)};sample[20]=None
 while True:
  ok,f=cap.read()
  if not ok:break
  if i in sample:
   j=sample[i]
   if j is not None:
    xx,yy,dw,dh=records[j]["roi"];g=cv2.cvtColor(f[yy:yy+dh,xx:xx+dw],cv2.COLOR_BGR2GRAY);err=float(np.mean(cv2.absdiff(g,refs[j])));need(err<4,"capture crop mismatch");observed.append({"page":j,"frame":i,"error":round(err,4)})
   stills.append(Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).resize((360,640),Image.Resampling.LANCZOS))
  i+=1
 cap.release();need((w,h)==(W,H) and abs(fps-30)<.01 and i==total and len(observed)==3,"frame clock or evidence")
 sheet=Image.new("RGB",(1440,664),BG);d=ImageDraw.Draw(sheet)
 for j,im in enumerate(stills):sheet.paste(im,(j*360,24));d.text((j*360+8,5),f"Phone preview {j+1}",fill=I)
 sheet.save(a.out/"float-contact.jpg",quality=94)
 r={"version":"1.0.0-rc5","resolution":[w,h],"fps":fps,"frames":i,"duration_seconds":i/fps,"audio_samples":len(x),"voice":n["voice"],"narration_sha256":n["narration_sha256"],"narration_report_sha256":sha(a.audio/"NARRATION_REVIEW_QA.json"),"raw_asr_screen_pass":n["asr_screen_pass"],"all_exact_token_matches":n["all_exact_token_matches"],"audio_energy":energy(x),"loudness":loud,"capture_sha256":sha(source),"observed_crops":observed,"capture_panels":records,"caption_corrections":corrections,"corrected_captions_sha256":sha(a.out/"caption_review.json"),"source_sha256":sha(Path(__file__)),"events":events,"full_decode_pass":True,"mp4_sha256":sha(final),"contact_sha256":sha(a.out/"float-contact.jpg"),"visual_style":"original native typography and held cropped real console frames; no continuous motion claim","human_playback_approved":False,"release_authorized":False}
 (a.out/"FLOAT_SHORT_QA.json").write_text(json.dumps(r,indent=2)+"\n",encoding="utf-8");print(json.dumps(r,indent=2))
if __name__=="__main__":main()
