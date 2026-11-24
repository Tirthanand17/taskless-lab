"""B1v7 final caption/semantic emphasis pass. Original audio is copied exactly.
Uses captured browser states; editorial highlights are labeled. Never approves/releases.
"""
from pathlib import Path
import json,re,sys,subprocess,hashlib,math
from PIL import Image,ImageDraw,ImageFont
from quality_gate import check
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parent/'nov22-branch1-recovery'/'ffmpeg_vendor'))
import imageio_ffmpeg
F=imageio_ffmpeg.get_ffmpeg_exe()
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def art(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
def run(args,cwd=None):
 p=subprocess.run([F,'-hide_banner','-loglevel','error','-y',*map(str,args)],cwd=cwd,capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr[-2400:])
 return p.stdout
def sec(t):
 h,m,s=t.replace(',','.').split(':');return int(h)*3600+int(m)*60+float(s)
def stamp(t):
 ms=round(t*1000);s,ms=divmod(ms,1000);m,s=divmod(s,60);h,m=divmod(m,60)
 return f'{h:02}:{m:02}:{s:02},{ms:03}'
def at(t):
 n=round(t*100);s,n=divmod(n,100);m,s=divmod(s,60);h,m=divmod(m,60)
 return f'{h}:{m:02}:{s:02}.{n:02}'
def cues(p):
 a=[]
 for block in p.read_text(encoding='utf-8-sig').strip().split('\n\n'):
  ls=block.splitlines();x,y=ls[1].split(' --> ');a.append([sec(x),sec(y),' '.join(ls[2:])])
 return a
def normalized(items,kind):
 # Punctuation/casing only; uncertain past-tense recognition is retained and flagged.
 for c in items:
  c[2]=c[2].replace('pop -up','pop-up').replace('site -specific','site-specific')
  c[2]=re.sub(r'\bchrome\b','Chrome',c[2],flags=re.I)
 if kind=='long':
  for i in range(len(items)-1):
   if items[i][2].endswith('pop') and items[i+1][2].startswith('-up,'):
    items[i][2]+='-up,';items[i+1][2]=items[i+1][2][4:].lstrip()
 # Merge very short trailing fragments within the same speech phrase, without moving the last boundary.
 out=[]
 for c in items:
  if out and c[1]-c[0]<.85 and c[0]-out[-1][1]<=.10 and len(out[-1][2]+' '+c[2])<=70:
   out[-1][1]=c[1];out[-1][2]+=' '+c[2]
  else:out.append(c)
 return out
def write_ass(path,cs,w,h):
 fs=46 if w<h else 48
 y=1500 if w<h else 950
 lines=['[Script Info]','ScriptType: v4.00+','PlayResX: '+str(w),'PlayResY: '+str(h),'WrapStyle: 0','[V4+ Styles]','Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding',f'Style: Default,Segoe UI,{fs},&H00FFFFFF,&H00FFFFFF,&H000B111B,&H000B111B,-1,0,0,0,100,100,0,0,1,2,0,5,100,120,0,1','[Events]','Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text']
 for a,b,t in cs:
  if len(t)>42:
   ws=t.split();i=min(range(1,len(ws)),key=lambda j:abs(len(' '.join(ws[:j]))-len(' '.join(ws[j:]))));t=' '.join(ws[:i])+r'\N'+' '.join(ws[i:])
  lines.append(f'Dialogue: 0,{at(a)},{at(b)},Default,,0,0,0,,'+r'{\pos('+str(w//2-30 if w<h else w//2)+','+str(y)+')}'+t)
 path.write_text('\n'.join(lines)+'\n',encoding='utf8')
def streamhash(p):
 return run(['-v','error','-i',p,'-map','0:a:0','-c','copy','-f','streamhash','-hash','sha256','-']).strip()
FONT=Path('C:/Windows/Fonts')
def ft(n,b=True):return ImageFont.truetype(str(FONT/('segoeuib.ttf' if b else 'segoeui.ttf')),n)
BG='#111c2a';A='#70e4bd';WHITE='#f5f8fc';DIM='#aabaca';BLUE='#94baff';ORANGE='#ffba78'
E=R/'notifications'
def text(d,t,x,y,n,c=WHITE,b=True):
 d.text((x,y),t,font=ft(n,b),fill=c)
def photo(im,name,box,x,y,width):
 p=Image.open(E/name).convert('RGB').crop(box);p=p.resize((width,round(width*p.height/p.width)),Image.Resampling.LANCZOS);im.paste(p,(x,y));ImageDraw.Draw(im).rectangle((x,y,x+p.width,y+p.height),outline=A,width=4)
def block(d,x,y,w,h,t,c=WHITE,bg='#24384b',n=54):
 d.rounded_rectangle((x,y,x+w,y+h),radius=22,fill=bg);text(d,t,x+26,y+22,n,c)
def long_frame(i,phase):
 im=Image.new('RGB',(1920,1080),BG);d=ImageDraw.Draw(im)
 headings=['Stop one website’s notifications','Why alerts can appear','Open Site settings','Find Notifications','Change Allow to Block','Verify the permission','Only this website','Remember these steps']
 text(d,'FLOWMINUTE LAB  /  CONTROLLED CHROME TEST',70,45,28,A)
 text(d,headings[i],70,105,70)
 granted='01_granted.png';denied='04_denied.png';before='02_site_details.png';after='03_site_blocked.png'
 row=(395,433,1024,513);proof=(48,110,1120,533)
 if i in (0,1,5):
  src=denied if i in (0,5) else granted
  photo(im,src,proof,70,260,1150)
  if i==1:
   block(d,1280,270,560,124,'Permission granted',ORANGE,n=42)
   if phase>=1:block(d,1280,430,560,124,'Saved per website',BLUE,n=43)
   if phase>=2:text(d,'Not a normal page popup.',1280,625,34,DIM)
  else:
   block(d,1280,270,560,124,'GRANTED',ORANGE,n=57)
   if phase>=1:text(d,'↓',1510,425,78)
   block(d,1280,550,560,124,'DENIED',A,n=57)
   if phase>=2:text(d,'Actual API result',1280,730,42,DIM)
 elif i==2:
  photo(im,before,(340,55,1040,860),70,235,550)
  for j,label in enumerate(['Open the website','Site information icon','Site settings']):
   block(d,690,260+j*165,1120,135,str(j+1)+'. '+label,A if j==phase else WHITE,bg='#215344' if j==phase else '#24384b',n=58)
  text(d,'Navigation instructions · actual destination shown',690,792,32,DIM,False)
 elif i==3:
  photo(im,before,(350,55,1035,540),70,240,650)
  photo(im,before,row,780,280,1020)
  text(d,'Notifications',780,470,77,A)
  if phase>=1:text(d,'Change this setting only.',780,590,57)
  if phase>=2:text(d,'Leave other permissions unchanged.',780,720,43,DIM)
 elif i==4:
  text(d,'BEFORE: ALLOW',70,250,58,ORANGE)
  photo(im,before,row,70,345,810)
  if phase>=1:
   text(d,'AFTER: BLOCK',1030,250,58,A);photo(im,after,row,1030,345,810)
   text(d,'→',900,350,80,A)
  else:text(d,'Select Block from the menu',1030,360,51,A)
  if phase>=2:block(d,70,660,1770,115,'Chrome saves the permission automatically.',A,n=57)
 elif i==6:
  photo(im,after,row,70,255,1420)
  block(d,70,515,860,140,'This site: Block',A,bg='#215344',n=60)
  if phase>=1:block(d,970,515,870,140,'Other sites: unchanged',BLUE,n=51)
  if phase>=2:text(d,'Re-enable only for a trusted site.',70,750,56,DIM)
 else:
  for j,label in enumerate(['Site settings','Notifications','Block','Verify']):
   x=70+(j%2)*900;y=245+(j//2)*230
   block(d,x,y,840,178,str(j+1)+'. '+label,A if j==phase else WHITE,bg='#215344' if j==phase else '#24384b',n=70)
  if phase>=4:text(d,'Different problem? Check Pop-ups and redirects.',70,780,48,BLUE)
 return im
# semantic beat boundaries from the original measured caption timings, not invented interaction
BEATS=[[0,2.5,5.54],[0,11.26-9,14.52-9],[0,20.812-18.7916667,23.732-18.7916667],[0,31.898-29.9583333,35.378-29.9583333],[0,42.402-40.0416667,45.382-40.0416667],[0,52.745-48.125,56.165-48.125],[0,64.262-59.5416667,67.222-59.5416667],[0,74.928-71.7083333,78.168-71.7083333,80.928-71.7083333,82.588-71.7083333]]
def process(name):
 p=R/name;doc=read(p);assert not check(doc,R)
 old=R/doc['video']['path'];w,h=(1080,1920) if doc['format']=='short' else (1920,1080)
 work=R/('final_'+name.replace('_plan.json',''));work.mkdir(exist_ok=True)
 cs=normalized(cues(R/doc['captions']['path']),doc['format'])
 srt=work/'captions.srt';srt.write_text('\n\n'.join(f'{i+1}\n{stamp(a)} --> {stamp(b)}\n{t}' for i,(a,b,t) in enumerate(cs))+'\n',encoding='utf8')
 ass=work/'captions.ass';write_ass(ass,cs,w,h)
 src=old
 if doc['format']=='long':
  entries=[]
  for i,s in enumerate(doc['scenes']):
   dur=s['end']-s['start'];bounds=sorted(set([0]+[round(x*24)/24 for x in BEATS[i] if 0<x<dur]+[round(dur*24)/24]))
   for j,(a,b) in enumerate(zip(bounds,bounds[1:])):
    im=long_frame(i,j);f=work/f'{i:02}_{j:02}.png';im.save(f)
    entries.extend([f"file '{f.name}'",f'duration {b-a:.9f}'])
   doc['scenes'][i]['motion']='comparison_reveal' if i in (0,4,5,6) else 'annotation'
   doc['scenes'][i]['visual_action']+='; synchronized progressive editorial emphasis at measured speech beats.'
  entries.append(f"file '{f.name}'");(work/'frames.txt').write_text('\n'.join(entries)+'\n')
  src=work/'semantic.mp4';n=round(doc['scenes'][-1]['end']*24)
  run(['-f','concat','-safe','0','-i','frames.txt','-vf','fps=24','-frames:v',n,'-c:v','libx264','-threads','4','-preset','veryfast','-crf','20','-pix_fmt','yuv420p',src],cwd=work)
  thumb=work/'thumbnail.png';long_frame(0,2).resize((1280,720),Image.Resampling.LANCZOS).save(thumb);doc['thumbnail']=art(thumb)
 # cover old captions only, preserving the previous underlying actions and source pictures.
 # Shorts original caption area spans y=1455..1610 (incognito may reach 1630).
 vf=("drawbox=x=40:y=1438:w=950:h=210:color=0x101A28:t=fill," if w<h else "")+"subtitles=captions.ass"
 final=work/'B1V7_FINAL_REVIEW.mp4'
 run(['-i',src,'-i',old,'-vf',vf,'-map','0:v:0','-map','1:a:0','-c:v','libx264','-threads','4','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',final],cwd=work)
 run(['-i',final,'-map','0:v','-map','0:a','-f','null','NUL'])
 assert streamhash(old)==streamhash(final)
 review={'previous_video':art(old),'video':art(final),'audio_stream_identical':True,'caption_changes':'typography, capitalization, short trailing fragment merge; uncertain tense retained pending listening','human_review':False,'long_semantic_reveal':doc['format']=='long','caption_cues_before':len(cues(R/doc['captions']['path'])),'caption_cues_after':len(cs)}
 (work/'edit_receipt.json').write_text(json.dumps(review,indent=2))
 doc.update(video=art(final),captions=art(srt),review={},owner_release_authorized=False)
 assert not check(doc,R),check(doc,R)
 p.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding='utf8')
 print('FINAL_EDIT_PASS',name,json.dumps(review),flush=True)
for n in sys.argv[1:] or ['pilot_v2_plan.json','notification_short_plan.json','notification_long_plan.json']:process(n)
