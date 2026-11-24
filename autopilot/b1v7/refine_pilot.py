"""B1v7 second-pass edit. Reuses executed browser proof, not unrelated stock.
Actual capture states are cropped; diagrams/cursor annotations are editorial.
No publishing operations.
"""
from pathlib import Path
import sys, json, math, hashlib, subprocess, wave, re, difflib
from PIL import Image, ImageDraw, ImageFont
import numpy as np
R=Path(__file__).resolve().parent;P=R/'evidence';B=R.parent
sys.path.insert(0,str(B/'nov22-branch1-recovery'/'ffmpeg_vendor'))
import imageio_ffmpeg
F=imageio_ffmpeg.get_ffmpeg_exe()
W,H,FPS=1080,1920,24
FONT=Path('C:/Windows/Fonts')
def ft(n,b=False):return ImageFont.truetype(str(FONT/('segoeuib.ttf' if b else 'segoeui.ttf')),n)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cmd(args):
 r=subprocess.run([F,'-hide_banner','-loglevel','error','-y',*map(str,args)],capture_output=True,text=True)
 if r.returncode:raise RuntimeError(r.stderr[-2000:])
def text(d,t,x,y,size,col='#ffffff',bold=True,anchor='lt'):
 d.text((x,y),t,font=ft(size,bold),fill=col,anchor=anchor)
def roundbox(d,xy,color,r=28,outline=None,width=2):d.rounded_rectangle(xy,r,fill=color,outline=outline,width=width)
def crop(name,box,width):
 im=Image.open(P/name).convert('RGB').crop(box)
 return im.resize((width,round(im.height*width/im.width)),Image.Resampling.LANCZOS)
before=crop('01_private_before.png',(34,42,866,565),908)
after=crop('02_download_requested.png',(34,42,866,565),908)
proof=crop('03_file_persists.png',(34,40,866,615),908)
proofdetail=crop('03_file_persists.png',(40,250,860,493),900)
rec=json.loads((P/'proof.json').read_text())
assert rec['file_persisted_after_context_closed'] and rec['bytes']==62
for n,h in rec['captures'].items():assert sha(P/n)==h
old=json.loads((R/'pilot_qa.json').read_text());script=old['script']
durations=[]
for i in range(5):
 with wave.open(str(R/f'a{i}.wav'),'rb') as a:durations.append(a.getnframes()/a.getframerate())
starts=list(np.cumsum([0]+durations[:-1]));total=sum(durations)
# Transcribe actual generated narration, then map the expected words to recognized word timestamps.
from faster_whisper import WhisperModel
model=WhisperModel('base',device='cpu',compute_type='int8',local_files_only=True,cpu_threads=4)
def norm(t):return re.findall(r"[a-z0-9]+(?:'[a-z]+)?",t.lower())
def fmt(t):
 m=round(t*1000);s,m=divmod(m,1000);mi,s=divmod(s,60);h,mi=divmod(mi,60);return f'{h:02}:{mi:02}:{s:02},{m:03}'
cues=[];audits=[]
for i,line in enumerate(script):
 segs,_=model.transcribe(str(R/f'a{i}.wav'),language='en',beam_size=3,word_timestamps=True,vad_filter=False,condition_on_previous_text=False)
 words=[w for z in list(segs) for w in (z.words or [])]
 heard=' '.join(w.word.strip() for w in words);sim=difflib.SequenceMatcher(None,norm(line),norm(heard),autojunk=False).ratio()
 audits.append({'scene':i+1,'expected':line,'asr':heard,'similarity':round(sim,3)})
 # ASR timestamps support review; captions use recognized words, not invented timings.
 group=[]
 for w in words:
  if group and (len(' '.join(z.word.strip() for z in group+[w]))>42 or len(group)>=7):
   cues.append((starts[i]+group[0].start,starts[i]+min(group[-1].end,durations[i]),' '.join(z.word.strip() for z in group)));group=[]
  group.append(w)
 if group:cues.append((starts[i]+group[0].start,starts[i]+min(group[-1].end,durations[i]),' '.join(z.word.strip() for z in group)))
 print('VOICE',i+1,round(sim,3),heard,flush=True)
assert min(a['similarity'] for a in audits)>=.78
cues=[c for c in cues if c[1]>c[0]]
srt=R/'pilot_v2.srt';srt.write_text('\n\n'.join(f'{i+1}\n{fmt(a)} --> {fmt(b)}\n{s}' for i,(a,b,s) in enumerate(cues))+'\n',encoding='utf8')
audit=R/'pilot_v2_audio_audit.json';audit.write_text(json.dumps({'scenes':audits,'human_review':False,'caption_method':'ASR word times; final human listening and transcript review required'},indent=2))
navy='#0c1725';blue='#7faaff';mint='#51e0af';white='#edf5fc';muted='#adbed0';red='#ff8f83'
def bg():
 im=Image.new('RGB',(W,H),navy);d=ImageDraw.Draw(im);d.rectangle((0,0,16,H),fill=mint);return im,d
def badge(d,t,x,y,c=mint):
 w=d.textlength(t,font=ft(31,True))+44;roundbox(d,(x,y,x+w,y+56),'#203447',20);text(d,t,x+22,y+8,31,c)
def fileicon(d,x,y,scale=1,c=mint):
 w=int(155*scale);h=int(194*scale);fold=int(42*scale)
 d.polygon([(x,y),(x+w-fold,y),(x+w,y+fold),(x+w,y+h),(x,y+h)],fill='#203b43',outline=c,width=5)
 d.line((x+w-fold,y,x+w-fold,y+fold,x+w,y+fold),fill=c,width=5)
 for j in range(3):d.line((x+25*scale,y+(80+23*j)*scale,x+w-25*scale,y+(80+23*j)*scale),fill=c,width=max(3,int(4*scale)))
def browser(d,x,y,w,h,closed=False):
 roundbox(d,(x,y,x+w,y+h),'#22354a',25,blue,3);d.line((x,y+70,x+w,y+70),fill=blue,width=3)
 for j in range(3):d.ellipse((x+25+33*j,y+25,x+43+33*j,y+43),fill=muted)
 text(d,'PRIVATE SESSION',x+25,y+110,36,white)
 if closed:
  d.line((x+w/2-45,y+h/2-5,x+w/2+45,y+h/2+85),fill=red,width=13)
  d.line((x+w/2+45,y+h/2-5,x+w/2-45,y+h/2+85),fill=red,width=13)
def frame(i,t):
 im,d=bg()
 if i==0:
  badge(d,'ACTUAL TEST RESULT',65,125)
  text(d,'Private session',65,230,79,white);text(d,'CLOSED.',65,323,100,red)
  text(d,'The file? Still here.',65,462,70,mint)
  im.paste(proof,(54,630));d.rectangle((54,630,962,630+proof.height),outline=mint,width=5)
  text(d,'Not deleted by Incognito.',65,1330,46,white)
 elif i==1:
  badge(d,'STEP 1  /  ACTUAL BROWSER CAPTURE',65,135,blue)
  text(d,'Download a file',65,244,82,white)
  text(d,'in a private session.',65,343,55,muted)
  shot=after if t>=3.0 else before;im.paste(shot,(54,505))
  tx=54+(rec['click']['x']-34)*908/832;ty=505+(rec['click']['y']-42)*908/832
  a=min(1,max(0,(t-1.3)/1.7));x=866+(tx-866)*a;y=1240+(ty-1240)*a
  if t>=1.3 and t<3.7:
   d.polygon([(x,y),(x+15,y+60),(x+29,y+39),(x+50,y+36)],fill='white',outline=navy,width=3)
   if t>=3:d.ellipse((tx-45,ty-45,tx+45,ty+45),outline=mint,width=7)
  text(d,'Harmless sample TXT',65,1160,55,white)
  text(d,'No personal data used.',65,1235,42,muted,False)
 elif i==2:
  badge(d,'STEP 2  /  EXPLANATORY DIAGRAM',65,130,blue)
  text(d,'Close the entire',65,245,75,white);text(d,'private session.',65,335,75,white)
  fileicon(d,690,720,1.08)
  a=min(1,max(0,(t-1.45)/1.0))
  browser(d,65,630,510,365,a>.7)
  text(d,'Session',65,1050,50,blue);text(d,'File on disk',635,1050,43,mint)
  d.line((577,815,670,815),fill=muted,width=8)
  d.polygon([(670,815),(642,796),(642,834)],fill=muted)
  if a>.7:text(d,'CLOSED',65,1120,64,red)
  text(d,'Actual private context ended.',65,1335,42,muted,False)
 elif i==3:
  badge(d,'STEP 3  /  FILESYSTEM VERIFIED',65,130)
  text(d,'Same file.',65,230,91,white);text(d,'Same contents.',65,340,81,mint)
  im.paste(proofdetail,(60,580));d.rectangle((60,580,960,580+proofdetail.height),outline=mint,width=5)
  fileicon(d,70,1030,.9);text(d,'62 bytes',275,1050,75,white);text(d,'SHA-256 match',275,1140,49,mint)
  text(d,'Read from the actual test file.',65,1335,42,muted,False)
 else:
  badge(d,'REMEMBER THIS',65,135)
  text(d,'Incognito is not',65,235,76,white);text(d,'a file eraser.',65,326,85,mint)
  roundbox(d,(60,545,960,860),'#23374b',30)
  text(d,'PRIVATE BROWSING RECORD',95,590,38,muted)
  text(d,'Not saved after',95,670,64,white);text(d,'the session ends.',95,750,58,white)
  roundbox(d,(60,915,960,1230),'#143c38',30)
  text(d,'DOWNLOADED FILES',95,960,39,mint)
  text(d,'Stay on the device.',95,1045,63,white)
  if t>3.1:text(d,'Delete them separately.',65,1335,53,mint)
 # Safe text zone: captions end before y=1590, controls below and at right.
 at=starts[i]+t
 active=next((c[2] for c in cues if c[0]<=at<c[1]),None)
 if active:
  f=ft(42,True);lines=[];line=''
  for w in active.split():
   trial=(line+' '+w).strip()
   if line and d.textlength(trial,font=f)>870:lines.append(line);line=w
   else:line=trial
  if line:lines.append(line)
  if len(lines)>2:raise RuntimeError('caption overflow')
  y=1495
  roundbox(d,(60,y-15,960,y+len(lines)*54+10),'#070d15',18)
  for j,l in enumerate(lines):text(d,l,510,y+j*54,42,white,True,'mt')
 text(d,'FLOWMINUTE LAB  /  CONTROLLED TEST',65,1690,26,muted,False)
 return im
thumb=frame(0,0);thumb.save(R/'pilot_v2_thumbnail.png')
clips=[];stills=[]
for i,dur in enumerate(durations):
 v=R/f'v2s{i}.mp4';frames=round(dur*FPS)
 # Preview at scene midpoint for visual verification.
 fr=frame(i,min(dur-.05,3.2));fr.save(R/f'v2_scene_{i+1}.jpg',quality=90);stills.append(fr)
 proc=subprocess.Popen([F,'-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','-','-c:v','libx264','-preset','ultrafast','-crf','21','-threads','4','-pix_fmt','yuv420p',str(v)],stdin=subprocess.PIPE)
 for n in range(frames):proc.stdin.write(frame(i,n/FPS).tobytes())
 proc.stdin.close();assert proc.wait()==0;clips.append(v);print('EDITED_SCENE',i+1,flush=True)
cat=R/'v2cat.txt';cat.write_text('\n'.join("file '"+p.as_posix()+"'" for p in clips)+'\n')
out=R/'B1V7_INCOGNITO_PROOF_PILOT_V2_REVIEW.mp4'
# Add an original, quiet click cue exactly at the annotated download.
with wave.open(str(R/'original_bed.wav'),'rb') as f:
 sr=f.getframerate();a=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(float)/32768
idx=int((starts[1]+3)*sr);n=int(.09*sr);t=np.arange(n)/sr;a[idx:idx+n]+=.045*np.sin(2*np.pi*950*t)*np.exp(-t*55)
bed=R/'v2_bed.wav'
with wave.open(str(bed),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes((np.clip(a,-1,1)*32767).astype('<i2').tobytes())
cmd(['-f','concat','-safe','0','-i',cat,'-i',R/'narration.wav','-i',bed,'-filter_complex','[1:a][2:a]amix=inputs=2:duration=first:normalize=0,alimiter=limit=.92[a]','-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',out])
cmd(['-i',out,'-map','0:v','-map','0:a','-f','null','NUL'])
sheet=Image.new('RGB',(5*216,384),'#0c1725')
for i,f in enumerate(stills):sheet.paste(f.resize((216,384),Image.Resampling.LANCZOS),(i*216,0))
sheet.save(R/'B1V7_V2_CONTACT.jpg',quality=92)
def art(path):return {'path':str(path.relative_to(R)).replace('\\','/'),'sha256':sha(path)}
layouts=['result-first split','actual before/after capture','session versus file diagram','tight proof closeup','comparison takeaway']
kinds=['capture','capture','diagram','capture','comparison']
roles=['hook','action','explanation','result','takeaway']
assets=['03_file_persists.png','01_private_before.png',None,'03_file_persists.png',None]
actions=['Show verified local file after private context closed','Show actual before/after button state with annotated cursor','Explain separate private session and disk file','Show cropped actual filename, size and hash proof','Contrast private session history with persistent download']
plan={'format':'short','audience':'Everyday Chrome users concerned about digital privacy','promise':'Show whether a download survives private browsing','practical_takeaway':'Delete downloaded files separately when needed','topic_evidence':'Own Incognito privacy Short led lifetime views (126); related topic, distinct executed test.','hook_variant':'result_first','title':'Incognito Does NOT Delete Downloaded Files #Shorts','thumbnail_concept':'Private session closed, actual file survives','research_sources':['https://support.google.com/chrome/answer/95464','https://support.google.com/youtube/answer/16559650'],'proof':art(P/'proof.json'),'video':art(out),'captions':art(srt),'thumbnail':art(R/'pilot_v2_thumbnail.png'),'audio_audit':art(audit),'owner_release_authorized':False,'review':{},'scenes':[]}
for i,dur in enumerate(durations):
 row=dict(start=float(starts[i]),end=float(starts[i]+dur),visual_kind=kinds[i],layout=layouts[i],spoken=script[i],visual_action=actions[i],learning_purpose=actions[i],focal_label=['File survived','Download button','Session versus disk','Actual file and size','Practical distinction'][i],role=roles[i],motion=['hold_for_reading','annotation','comparison_reveal','hold_for_reading','comparison_reveal'][i],shows_result=i in (0,3),intro_logo=False,evidence_visible_at=0)
 if assets[i]:row['evidence']=art(P/assets[i])
 plan['scenes'].append(row)
(R/'pilot_v2_plan.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False),encoding='utf8')
print('V2_DONE',out.name,sha(out),round(total,3),'captions',len(cues),flush=True)
