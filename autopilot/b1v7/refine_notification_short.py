"""Tight second edit of the Chrome notification Short. Reuse verified speech and proof.
Actual cropped native captures, editorial annotations and before/after state changes.
No API writes.
"""
from pathlib import Path
import sys,json,re,subprocess,math,hashlib
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent; E=R/'notifications'; D=R/'notification_short'
sys.path.insert(0,str(R.parent/'nov22-branch1-recovery'/'ffmpeg_vendor'))
import imageio_ffmpeg
from quality_gate import check
F=imageio_ffmpeg.get_ffmpeg_exe()
W,H,FPS=1080,1920,24
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf8'))
def art(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
def cmd(args):
 r=subprocess.run([F,'-hide_banner','-loglevel','error','-y',*map(str,args)],capture_output=True,text=True)
 if r.returncode:raise RuntimeError(r.stderr[-1800:])
doc=read(R/'notification_short_plan.json');assert not check(doc,R)
proof=read(E/'proof.json')
for n,h in proof['captures'].items():assert sha(E/n)==h
def tstamp(t):
 h,m,s=t.replace(',','.').split(':');return int(h)*3600+int(m)*60+float(s)
cues=[]
for item in (D/'captions.srt').read_text(encoding='utf8').strip().split('\n\n'):
 ls=item.splitlines();a,b=ls[1].split(' --> ');cues.append((tstamp(a),tstamp(b),' '.join(ls[2:])))
FONT=Path('C:/Windows/Fonts')
def ft(n,b=True):return ImageFont.truetype(str(FONT/('segoeuib.ttf' if b else 'segoeui.ttf')),n)
A='#82f2cb';OR='#ffc38a';BLUE='#a9c6ff';WHITE='#f1f6fd';DIM='#b4c5d7';BG='#101a28'
def text(d,t,x,y,n,c=WHITE,b=True,anchor='lt'):d.text((x,y),t,font=ft(n,b),fill=c,anchor=anchor)
def wrap(d,t,x,y,n,w,c=WHITE,b=True):
 lines=[];line='';font=ft(n,b)
 for word in t.split():
  trial=(line+' '+word).strip()
  if line and d.textlength(trial,font=font)>w:lines.append(line);line=word
  else:line=trial
 if line:lines.append(line)
 for j,l in enumerate(lines):text(d,l,x,y+j*int(n*1.24),n,c,b)
 return y+len(lines)*int(n*1.24)
def crop(name,box,width):
 im=Image.open(E/name).convert('RGB').crop(box)
 return im.resize((width,round(im.height*width/im.width)),Image.Resampling.LANCZOS)
pics={
 'granted':crop('01_granted.png',(45,105,1120,535),900),
 'denied':crop('04_denied.png',(45,105,1120,535),900),
 'page':crop('02_site_details.png',(350,55,1035,540),900),
 'allow':crop('02_site_details.png',(395,433,1024,513),900),
 'block':crop('03_site_blocked.png',(395,433,1024,513),900)}
def paste(im,k,x,y):
 a=pics[k];im.paste(a,(x,y));d=ImageDraw.Draw(im);d.rectangle((x,y,x+a.width,y+a.height),outline=BLUE,width=4)
def box(d,b,c,r=26):d.rounded_rectangle(b,r,fill=c)
def arrow(d,x,y,c=A):
 d.line((x,y,x,y+102),fill=c,width=13);d.polygon([(x-31,y+80),(x+31,y+80),(x,y+120)],fill=c)
def bell(d,x,y,s=1,color=OR):
 # Editorial icon only, not a fabricated Chrome notification.
 d.rounded_rectangle((x,y+55*s,x+180*s,y+205*s),radius=int(70*s),fill=color)
 d.polygon([(x-22*s,y+205*s),(x+202*s,y+205*s),(x+180*s,y+165*s),(x,y+165*s)],fill=color)
 d.ellipse((x+66*s,y+214*s,x+114*s,y+262*s),fill=color)
def frame(i,t,active):
 im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
 if i==0:
  text(d,'CHROME PRIVACY',60,115,37,A)
  wrap(d,'Unwanted website alerts?',60,205,88,900)
  bell(d,410,425,1.35,OR)
  text(d,'WHY THEY CAN APPEAR',60,800,39,OR)
  paste(im,'granted',60,885)
  text(d,'Actual test site: granted',60,1280,55,OR)
 elif i==1:
  text(d,'1  /  SITE SETTINGS',60,115,38,BLUE)
  text(d,'Open the website.',60,203,75)
  box(d,(60,335,960,465),'#243c55')
  text(d,'Site information → Site settings',88,365,47,WHITE)
  paste(im,'page',60,505)
  d.rectangle((67,1030,951,1131),outline=OR,width=6)
  text(d,'Find Notifications',60,1245,65,A)
 elif i==2:
  text(d,'2  /  CHANGE THE PERMISSION',60,115,37,BLUE)
  text(d,'Allow → Block',60,215,91)
  text(d,'BEFORE',60,385,47,OR);paste(im,'allow',60,480)
  arrow(d,510,660)
  if t>=min(1.35,(doc['scenes'][i]['end']-doc['scenes'][i]['start'])*.45):
   text(d,'AFTER',60,865,47,A);paste(im,'block',60,960)
   text(d,'BLOCKED',60,1180,93,A)
  else:text(d,'Choose Block.',60,1000,66,A)
 elif i==3:
  text(d,'3  /  VERIFY',60,115,38,A)
  text(d,'It worked.',60,210,110)
  box(d,(60,395,960,560),'#50392c')
  text(d,'GRANTED',95,440,68,OR)
  arrow(d,510,600)
  paste(im,'denied',60,785)
  text(d,'DENIED',60,1190,97,A)
 elif i==4:
  text(d,'ONE SITE ONLY',60,115,38,A)
  wrap(d,'Keep the alerts you want.',60,200,86,900)
  box(d,(60,465,960,730),'#1f443d')
  text(d,'This website',95,505,53,WHITE);text(d,'BLOCK',95,603,90,A)
  box(d,(60,765,960,1030),'#233a51')
  text(d,'Other websites',95,805,53,WHITE);text(d,'Their own settings',95,905,58,BLUE)
  paste(im,'block',60,1160)
 if active:
  box(d,(55,1455,970,1610),'#080d15',20)
  end=wrap(d,active,80,1479,44,865)
  assert end<1600,'caption overflow'
 text(d,'FLOWMINUTE LAB  /  CONTROLLED TEST',60,1700,27,DIM,False)
 return im
clips=[];stills=[]
for i,s in enumerate(doc['scenes']):
 dur=s['end']-s['start'];n=round(dur*FPS);f=D/f'v2_{i}.mp4'
 cache={};proc=subprocess.Popen([F,'-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','-','-c:v','libx264','-preset','ultrafast','-crf','21','-threads','4','-pix_fmt','yuv420p',str(f)],stdin=subprocess.PIPE)
 for j in range(n):
  t=j/FPS;active=next((c[2] for c in cues if c[0]<=s['start']+t<c[1]),None)
  key=(active,t>=min(1.35,dur*.45))
  if key not in cache:cache[key]=frame(i,t,active).tobytes()
  proc.stdin.write(cache[key])
 proc.stdin.close();assert proc.wait()==0;clips.append(f)
 st=frame(i,dur*.75,None);st.thumbnail((216,384));stills.append(st)
 print('REFINED',i+1,flush=True)
cat=D/'v2cat.txt';cat.write_text('\n'.join("file '"+p.as_posix()+"'" for p in clips)+'\n')
final=D/'B1V7_CHROME_NOTIFICATIONS_SHORT_V2_REVIEW.mp4'
old=R/doc['video']['path']
cmd(['-f','concat','-safe','0','-i',cat,'-i',old,'-map','0:v','-map','1:a','-c:v','copy','-c:a','copy','-movflags','+faststart',final])
cmd(['-i',final,'-map','0:v:0','-map','0:a:0','-f','null','NUL'])
# Exact audio packet stream is preserved from already audited final.
def streamhash(p):
 return subprocess.run([F,'-v','error','-i',str(p),'-map','0:a:0','-c','copy','-f','streamhash','-hash','sha256','-'],capture_output=True,text=True,check=True).stdout.strip()
assert streamhash(old)==streamhash(final),'audio changed'
thumbnail=D/'thumbnail_v2.png';frame(0,0,None).save(thumbnail)
sheet=Image.new('RGB',(1080,384),BG)
for i,f in enumerate(stills):sheet.paste(f,(i*216,0))
sheet.save(D/'contact_v2.jpg',quality=90)
doc.update(video=art(final),thumbnail=art(thumbnail),review={},owner_release_authorized=False)
doc['scenes'][2]['motion']='comparison_reveal'
doc['scenes'][4]['visual_kind']='comparison'
doc['scenes'][4]['layout']='scope comparison with native row'
assert not check(doc,R),check(doc,R)
(R/'notification_short_plan.json').write_text(json.dumps(doc,indent=2,ensure_ascii=False),encoding='utf8')
print('REFINED_FINAL',final.name,sha(final),flush=True)
