"""Render short and long distinct edits from verified isolated Chrome settings test.
Original Kokoro narration, actual capture crops, editorial motion, music and captions.
No publishing operations.
"""
from pathlib import Path
import sys,json,math,hashlib,subprocess,wave,re,difflib
from PIL import Image,ImageDraw,ImageFont
import numpy as np
R=Path(__file__).resolve().parent;E=R/'notifications';B=R.parent
sys.path[:0]=[str(B/'nov24-b1v6'/'kokoro_vendor'),str(B/'nov22-branch1-recovery'/'ffmpeg_vendor')]
import imageio_ffmpeg,soundfile as sf,espeakng_loader
from phonemizer.backend.espeak.wrapper import EspeakWrapper
EspeakWrapper.set_library(espeakng_loader.get_library_path())
from kokoro_onnx import Kokoro
F=imageio_ffmpeg.get_ffmpeg_exe();FPS=24
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cmd(args):
 r=subprocess.run([F,'-hide_banner','-loglevel','error','-y',*map(str,args)],capture_output=True,text=True)
 if r.returncode:raise RuntimeError(r.stderr[-1600:])
e=json.loads((E/'proof.json').read_text())
assert e['before']=='granted' and e['after']=='denied' and e['isolated_profile']
for n,h in e['captures'].items():assert sha(E/n)==h
engine=Kokoro(str(B/'nov24-b1v6'/'kokoro-v1.0.int8.onnx'),str(B/'nov24-b1v6'/'voices-v1.0.bin'))
from faster_whisper import WhisperModel
asr=WhisperModel('base',device='cpu',compute_type='int8',local_files_only=True,cpu_threads=4)
# scene: role, layout, headline, one-sentence explanation, source capture, visual action
SHORT=[
 ('hook','permission_problem','Unwanted Chrome alerts?','A website can keep sending notifications if you allowed them.','01_granted.png','Show actual granted state immediately.'),
 ('action','navigation','Open Site settings','On that website, click the site information icon beside the address. Open site settings.','02_site_details.png','Show real site details; label preceding steps as instructions.'),
 ('action','setting_change','Allow to Block','Find Notifications. Choose the Block option.','02_site_details.png','Show actual native notifications row before and after.'),
 ('result','proof','Permission denied','I tested this on a separate Chrome profile. The permission changed from granted to denied.','04_denied.png','Show actual local permission API result.'),
 ('takeaway','one_site','Block just that site','Other websites keep their own settings. You do not have to block every notification.','03_site_blocked.png','Show the per-site setting.')]
LONG=[
 ('hook','proof','Stop one website’s notifications','Here is a real Chrome test. One website was allowed to send notifications. After changing its setting, permission was denied.','04_denied.png','Show actual denied result.'),
 ('explanation','permission_problem','Why do these alerts appear?','Websites can ask for permission to send notifications. If you grant permission, it is a saved site setting, not simply a popup on the page.','01_granted.png','Show actual granted permission; explain distinction.'),
 ('setup','navigation','Step 1. Open Site settings','Visit the website whose alerts you want to stop. Select the site information icon next to the address, then choose Site settings. I am using a local sample website.','02_site_details.png','Show native per-site page; navigation steps labeled as instructions.'),
 ('action','row_focus','Step 2. Find Notifications','The permissions page contains many controls. Look for Notifications. Do not change camera, microphone, or other settings unless you need to.','02_site_details.png','Focus on the actual notifications row.'),
 ('action','setting_change','Step 3. Change Allow to Block','For this test website, notifications were enabled. Select Block from the menu. Chrome saves that change automatically.','02_site_details.png','Reveal actual Allow and Block screenshots.'),
 ('result','proof','Step 4. Verify the result','I returned to the local test page and checked the browser permission. It changed from granted to denied. No actual notifications were sent in this controlled experiment.','04_denied.png','Show actual API result.'),
 ('explanation','one_site','One site, not every site','This is a site specific permission. It does not require turning off all notifications. To restore notifications later, return here and enable them only if you trust the site.','03_site_blocked.png','Show native blocked setting and site scope.'),
 ('takeaway','summary','Keep the alerts you actually want','For unwanted website notifications, open Site settings, find Notifications, choose Block, and verify the setting. If the problem is a different type of popup, check the separate popups and redirects control.','03_site_blocked.png','Summarize the demonstrated setting and distinguish popup controls.')]
def norm(t):return re.findall(r'[a-z0-9]+',t.lower())
def stamp(t):
 ms=round(t*1000);s,ms=divmod(ms,1000);m,s=divmod(s,60);h,m=divmod(m,60);return f'{h:02}:{m:02}:{s:02},{ms:03}'
def rms(p):
 with wave.open(str(p),'rb') as f:a=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(float)/32768
 return 20*math.log10(max(np.sqrt(np.mean(a*a)),1e-9))
fonts=Path('C:/Windows/Fonts')
def ft(n,b=True):return ImageFont.truetype(str(fonts/('segoeuib.ttf' if b else 'segoeui.ttf')),n)
def caption_groups(words,offset,dur):
 g=[];out=[]
 for w in words:
  if g and (len(' '.join(z.word.strip() for z in g+[w]))>42 or len(g)>=7):
   out.append((offset+g[0].start,offset+min(g[-1].end,dur),' '.join(z.word.strip() for z in g)));g=[]
  g.append(w)
 if g:out.append((offset+g[0].start,offset+min(g[-1].end,dur),' '.join(z.word.strip() for z in g)))
 return [x for x in out if x[1]>x[0]]
def art(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
def render(kind,scenes):
 W,H=(1080,1920) if kind=='short' else (1920,1080)
 work=R/('notification_'+kind);work.mkdir(exist_ok=True)
 A='#70e4bd';BLUE='#94baff';WHITE='#f5f8fc';DIM='#aabaca';BG='#111c2a';ORANGE='#ffba78'
 def txt(d,t,x,y,n,c=WHITE,b=True,anchor='lt'):
  d.text((x,y),t,font=ft(n,b),fill=c,anchor=anchor)
 def wrap(d,t,x,y,n,width,c=WHITE,b=True):
  line='';ls=[];f=ft(n,b)
  for word in t.split():
   trial=(line+' '+word).strip()
   if line and d.textlength(trial,font=f)>width:ls.append(line);line=word
   else:line=trial
  if line:ls.append(line)
  for j,l in enumerate(ls):txt(d,l,x,y+j*int(n*1.22),n,c,b)
  return y+len(ls)*int(n*1.22)
 def photo(im,n,box,x,y,width,mark=False):
  a=Image.open(E/n).convert('RGB').crop(box);a=a.resize((width,round(a.height*width/a.width)),Image.Resampling.LANCZOS)
  im.paste(a,(x,y));d=ImageDraw.Draw(im)
  if mark:d.rectangle((x,y,x+a.width,y+a.height),outline=A,width=5)
  return a.height
 def callout(d,label,x,y,accent=A):
  txt(d,label,x,y,30 if kind=='short' else 28,accent)
 def frame(i,t,active=None):
  role,layout,heading,spoken,source,action=scenes[i]
  im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
  # Distinct visual compositions; native UI remains unchanged.
  if kind=='short':
   x=66; width=900; callout(d,('ACTUAL CHROME TEST' if layout in ('proof','permission_problem') else 'CHROME SITE PERMISSIONS'),x,115)
   y=wrap(d,heading,x,205,77,width)+42
   if layout=='permission_problem':
    photo(im,source,(54,102,1090,530),x,y,width,True)
    wrap(d,'Allowed = this site has permission',x,y+445,52,width,ORANGE)
   elif layout=='navigation':
    photo(im,source,(350,55,1035,540),x,y,width,True)
    wrap(d,'Site information → Site settings',x,y+690,46,width,BLUE)
   elif layout=='setting_change':
    sw=t>=min(2.15,durations[i]*.52)
    name='03_site_blocked.png' if sw else '02_site_details.png'
    photo(im,name,(395,433,1024,513),x,y+100,width,True)
    txt(d,'BLOCK' if sw else 'ALLOW',x,y+390,105,A if sw else ORANGE)
    wrap(d,'Actual settings before / after',x,y+535,42,width,DIM,False)
    if sw: d.line((x,y+545,x+min(width,int((t-2)*width)),y+545),fill=A,width=4)
   elif layout=='proof':
    photo(im,source,(48,110,1120,533),x,y,width,True)
    txt(d,'GRANTED → DENIED',x,y+460,67,A)
   else:
    photo(im,source,(350,55,1035,540),x,y,width,True)
    wrap(d,'One website. Other sites unchanged.',x,y+690,48,width,A)
   if active:
    d.rounded_rectangle((55,1460,970,1605),radius=22,fill='#080d15')
    wrap(d,active,80,1480,44,860)
   txt(d,'FLOWMINUTE LAB  /  CONTROLLED DEMO',66,1695,27,DIM,False)
  else:
   x=70;callout(d,'REAL CHROME TEST  /  '+str(i+1).zfill(2),x,55)
   if layout in ('navigation','row_focus'):
    wrap(d,heading,x,113,67,1750)
    photo(im,source,(340,55,1040,860),70,230,540,True)
    tx=685
    if layout=='row_focus':
     photo(im,source,(395,433,1024,513),tx,270,1110,True)
     wrap(d,'Change Notifications only.',tx,460,58,1060,A)
     wrap(d,'Leave other permissions alone unless needed.',tx,570,43,1060,DIM,False)
    else:
     wrap(d,'1. Open the website',tx,260,57,1100)
     wrap(d,'2. Site information icon',tx,390,57,1100)
     wrap(d,'3. Site settings',tx,520,57,1100,A)
     txt(d,'Navigation instructions; captured destination shown.',tx,690,33,DIM,False)
   elif layout=='setting_change':
    wrap(d,heading,x,113,67,1750)
    photo(im,'02_site_details.png',(395,433,1024,513),70,300,810,True)
    txt(d,'BEFORE: ALLOW',70,230,46,ORANGE)
    if t>=min(3.3,durations[i]*.4):
     photo(im,'03_site_blocked.png',(395,433,1024,513),1030,300,810,True)
     txt(d,'AFTER: BLOCK',1030,230,46,A)
     d.polygon([(903,350),(1005,350),(1005,325),(1030,375),(1005,425),(1005,400),(903,400)],fill=A)
    wrap(d,'Chrome saves the site permission.',70,550,64,1750)
   elif layout in ('proof','permission_problem'):
    wrap(d,heading,x,120,73,1770)
    photo(im,source,(48,110,1120,533),70,300,1130,True)
    if layout=='proof':
     wrap(d,'GRANTED',1270,350,66,570,ORANGE);wrap(d,'↓',1270,445,66,570);wrap(d,'DENIED',1270,540,66,570,A)
    else:
     wrap(d,'A saved site permission',1270,350,61,560,BLUE)
     wrap(d,'Not the same as page popups.',1270,575,42,560,DIM,False)
   else:
    wrap(d,heading,x,120,70,1750)
    photo(im,source,(350,55,1035,680),70,245,650,True)
    if layout=='summary':
     for j,t0 in enumerate(['Site settings','Notifications','Block','Verify']):
      txt(d,str(j+1)+'. '+t0,825,255+j*124,59,A if j==2 else WHITE)
    else:
     wrap(d,'This site: Block',820,285,63,1060,A)
     wrap(d,'Other sites: their own permissions',820,430,60,1060,WHITE)
     wrap(d,'Re-enable only for a trusted site.',820,650,43,1060,DIM,False)
   if active:
    d.rounded_rectangle((180,910,1740,1004),radius=20,fill='#080d15')
    txt(d,active,960,928,43,WHITE,True,'mt')
  return im
 durations=[];cues=[];audio=[];audits=[];starts=[];offset=0
 for i,scene in enumerate(scenes):
  speech=scene[3];raw=work/f'raw{i}.wav';a=work/f'a{i}.wav'
  samples,sr=engine.create(speech,voice='af_heart' if kind=='short' else 'am_michael',speed=1.04 if kind=='short' else 1.0,lang='en-us')
  sf.write(str(raw),samples,sr,subtype='PCM_16')
  dur=math.ceil((len(samples)/sr+.20)*FPS)/FPS
  cmd(['-i',raw,'-af','loudnorm=I=-16:TP=-2:LRA=7,apad','-t',str(dur),'-ar','48000','-ac','1','-c:a','pcm_s16le',a])
  seg,_=asr.transcribe(str(a),language='en',word_timestamps=True,beam_size=3,vad_filter=False,condition_on_previous_text=False)
  words=[w for z in list(seg) for w in (z.words or [])];heard=' '.join(w.word.strip() for w in words)
  sim=difflib.SequenceMatcher(None,norm(speech),norm(heard),autojunk=False).ratio()
  if sim<.84:raise RuntimeError(f'Speech review required {kind} {i}: {sim} {heard}')
  audits.append({'scene':i+1,'similarity':round(sim,3),'expected':speech,'recognized':heard})
  starts.append(offset);cues.extend(caption_groups(words,offset,dur));durations.append(dur);audio.append(a);offset+=dur
  print('VOICE_PASS',kind,i+1,round(sim,3),round(dur,2),flush=True)
 clips=[];stills=[]
 for i,dur in enumerate(durations):
  out=work/f'v{i}.mp4';nf=round(dur*FPS)
  # Encode only changed frames: native source state changes at the planned beat; captions are timed.
  # Cached bitmap per cue and phase avoids rerendering expensive screenshot crops every frame.
  cache={}
  proc=subprocess.Popen([F,'-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','-','-c:v','libx264','-preset','ultrafast','-crf','21','-threads','4','-pix_fmt','yuv420p',str(out)],stdin=subprocess.PIPE)
  for n in range(nf):
   t=n/FPS;absolute=starts[i]+t;active=next((c[2] for c in cues if c[0]<=absolute<c[1]),None)
   # Cut between actual before/after states, no generic looping motion.
   phase=t>=min(2.15,dur*.52) if kind=='short' else t>=min(3.3,dur*.4)
   key=(active,phase)
   if key not in cache:cache[key]=frame(i,t,active).tobytes()
   proc.stdin.write(cache[key])
  proc.stdin.close();assert proc.wait()==0
  still=frame(i,dur*.75,None);still.thumbnail((360,640));stills.append(still)
  clips.append(out);print('VIDEO_SCENE',kind,i+1,flush=True)
 def cat(files,p):p.write_text('\n'.join("file '"+x.as_posix()+"'" for x in files)+'\n',encoding='utf8')
 cat(clips,work/'vcat.txt');cat(audio,work/'acat.txt')
 narr=work/'narration.wav';cmd(['-f','concat','-safe','0','-i',work/'acat.txt','-c:a','pcm_s16le',narr])
 sr=48000;t=np.arange(round(offset*sr))/sr
 bed=.009*np.sin(2*np.pi*98*t)+.006*np.sin(2*np.pi*147*t)
 for j,at in enumerate(starts):
  if j==0:continue
  if scenes[j][1]=='setting_change':at+=min(2.15,durations[j]*.52) if kind=='short' else min(3.3,durations[j]*.4)
  idx=round(at*sr);n=min(round(.11*sr),len(bed)-idx);u=np.arange(n)/sr
  bed[idx:idx+n]+=.028*np.sin(2*np.pi*680*u)*np.exp(-u*35)
 bed[:sr//3]*=np.linspace(0,1,sr//3);bed[-sr//2:]*=np.linspace(1,0,sr//2)
 music=work/'bed.wav';sf.write(str(music),bed,sr,subtype='PCM_16')
 final=work/f'B1V7_CHROME_NOTIFICATIONS_{kind.upper()}_REVIEW.mp4'
 cmd(['-f','concat','-safe','0','-i',work/'vcat.txt','-i',narr,'-i',music,'-filter_complex','[1:a][2:a]amix=inputs=2:duration=first:normalize=0,alimiter=limit=.92[a]','-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',final])
 cmd(['-i',final,'-map','0:v:0','-map','0:a:0','-f','null','NUL'])
 srt=work/'captions.srt';srt.write_text('\n\n'.join(f'{j+1}\n{stamp(a)} --> {stamp(b)}\n{s}' for j,(a,b,s) in enumerate(cues))+'\n',encoding='utf8')
 thumbnail=work/'thumbnail.png';th=frame(0,0);th.thumbnail((1280,1920));th.save(thumbnail)
 sheet=Image.new('RGB',(min(4,len(stills))*360,math.ceil(len(stills)/4)*max(x.height for x in stills)),BG)
 for j,img in enumerate(stills):sheet.paste(img,(j%4*360,j//4*max(x.height for x in stills)))
 sheet.save(work/'contact.jpg',quality=88)
 margin=rms(narr)-rms(music);assert margin>=12
 audit=work/'audio_audit.json';audit.write_text(json.dumps({'scenes':audits,'voice_over_bed_db':round(margin,2),'human_listening':False},indent=2),encoding='utf8')
 doc={'format':kind,'audience':'Everyday Chrome users','promise':'Stop notifications from one unwanted website','practical_takeaway':'Site settings > Notifications > Block','topic_evidence':'Channel privacy and browser topics are among historical best performers; not verified search volume.','hook_variant':'problem_first' if kind=='short' else 'result_first','title':'Stop One Website’s Chrome Notifications #Shorts' if kind=='short' else 'How to Block Notifications from One Website in Chrome (Real Test)','thumbnail_concept':'Actual notification setting and permission change','research_sources':['https://support.google.com/chrome/answer/114662','https://support.google.com/chrome/answer/3220216'],'proof':art(E/'proof.json'),'video':art(final),'captions':art(srt),'thumbnail':art(thumbnail),'audio_audit':art(audit),'owner_release_authorized':False,'review':{},'scenes':[]}
 for i,(role,layout,heading,spoken,source,action) in enumerate(scenes):
  doc['scenes'].append({'start':starts[i],'end':starts[i]+durations[i],'visual_kind':'capture','layout':layout,'spoken':spoken,'visual_action':action,'learning_purpose':heading,'focal_label':heading,'motion':'comparison_reveal' if layout=='setting_change' else 'hold_for_reading','role':role,'shows_result':role=='result' or (kind=='long' and i==0),'shows_problem':kind=='short' and i==0,'intro_logo':False,'evidence_visible_at':0,'evidence':art(E/source)})
 plan=R/f'notification_{kind}_plan.json';plan.write_text(json.dumps(doc,indent=2,ensure_ascii=False),encoding='utf8')
 from quality_gate import check
 issues=check(doc,R);assert not issues,issues
 print('FINAL_PASS',kind,round(offset,2),len(cues),sha(final),round(margin,2),flush=True)
if __name__=='__main__':
 for k,sc in [('short',SHORT),('long',LONG)]:
  if len(sys.argv)==1 or k in sys.argv[1:]:render(k,sc)
