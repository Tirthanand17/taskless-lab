"""FlowMinute B1v9: original native-HD illustrated motion graphics.
Actual OpenCV QR experiments, unit calculations, licensed existing Kokoro voice.
Reference reel used only as design research; no third-party audio, frames or mascot.
"""
from pathlib import Path
import sys,json,math,re,hashlib,subprocess,wave,difflib
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;B=R.parent;OLD=B/'nov24-b1v6';E=R/'evidence';E.mkdir(exist_ok=True)
sys.path[:0]=[str(OLD/'kokoro_vendor'),str(B/'nov22-branch1-recovery'/'ffmpeg_vendor')]
import imageio_ffmpeg,soundfile as sf,espeakng_loader
from phonemizer.backend.espeak.wrapper import EspeakWrapper
EspeakWrapper.set_library(espeakng_loader.get_library_path())
from kokoro_onnx import Kokoro
from faster_whisper import WhisperModel
F=imageio_ffmpeg.get_ffmpeg_exe();FPS=30
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def art(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
def cmd(a,cwd=None):
 r=subprocess.run([F,'-hide_banner','-loglevel','error','-y',*map(str,a)],capture_output=True,text=True,cwd=cwd)
 if r.returncode:raise RuntimeError(r.stderr[-2000:])
 return r.stdout
# Actual QR generation/decode; only harmless text, never a URL.
payload='FLOWMINUTE TEST 27'
par=cv2.QRCodeEncoder_Params();par.correction_level=cv2.QRCodeEncoder_CORRECT_LEVEL_H
raw=cv2.QRCodeEncoder_create(par).encode(payload)
# OpenCV supplies a border; add white quiet margin for reliable independent decoding.
base=cv2.copyMakeBorder(raw,4,4,4,4,cv2.BORDER_CONSTANT,value=255)
det=cv2.QRCodeDetector()
def decode(a):
 return det.detectAndDecode(cv2.resize(a,None,fx=14,fy=14,interpolation=cv2.INTER_NEAREST))[0]
assert decode(base)==payload
# Find a reproducible small central obscuration that succeeds, and a larger one that fails.
m=base.shape[0]//2
samples={}
for side in range(3,base.shape[0]-8,2):
 a=base.copy();lo=m-side//2;a[lo:lo+side,lo:lo+side]=255
 result=decode(a)
 if result==payload:samples['recover']=(a,side,result)
 elif 'recover' in samples and 'fail' not in samples:samples['fail']=(a,side,result);break
assert 'recover' in samples and 'fail' in samples
for name,a in [('intact',base),('recover',samples['recover'][0]),('fail',samples['fail'][0])]:
 Image.fromarray(a).save(E/(name+'.png'))
proof={'qr':{'payload':payload,'level':'H','intact_decode':decode(base),'recovered_decode':samples['recover'][2],'failure_decode':samples['fail'][2],'mask_success_modules':samples['recover'][1],'mask_failure_modules':samples['fail'][1],'grid_with_quiet_zone':base.shape[0],'engine':'OpenCV QRCodeEncoder/Detector','assets':{n:art(E/(n+'.png')) for n in ('intact','recover','fail')}},'storage':{'decimal_bytes':128_000_000_000,'binary_unit_bytes':2**30,'gib':128_000_000_000/2**30,'examples':{str(n):round(n*10**9/2**30,2) for n in [64,128,256,512,1000]},'note':'calculated capacity before formatting/reserved space; not physical drive benchmark'}}
(E/'proof.json').write_text(json.dumps(proof,indent=2));print('PROOF',json.dumps(proof),flush=True)
ST='https://www.seagate.com/in/en/support/kb/lacie/why-does-my-hard-drive-report-less-capacity-than-indicated-on-the-drives-label-172191en/'
QR='https://www.qrcode.com/en/about/error_correction.html'
# label, heading, type, narration, takeaway. One visual idea per beat.
SPECS={
'storage_short':('short','Why Your 128 GB Drive Shows Only 119 GB #Shorts',[ST],[
('THE MYSTERY','Where did 9 GB go?','storage_hook','You bought a one hundred twenty eight gigabyte drive. Windows shows about one hundred nineteen. Where did the rest go?','Same bytes. Different units.'),
('THE LABEL','One billion bytes','decimal','Drive makers count one billion bytes as one gigabyte. That is the decimal system printed on the box.','128 GB = 128 billion bytes'),
('THE MATH','Windows counts differently','binary','Windows traditionally uses a larger binary unit. Divide the same number of bytes by that larger unit.','1 GiB = 1,073,741,824 bytes'),
('THE ANSWER','Nothing vanished.','storage_result','That is about one hundred nineteen point two in binary units. The bytes have not vanished. Formatting can use some space too.','128 GB ≈ 119.21 GiB')]),
'qr_short':('short','Why a Damaged QR Code Can Still Scan #Shorts',[QR],[
('THE TEST','This code has a hole.','qr_recover','I covered part of this QR code. Can it still scan? Watch. The decoder recovered the original text.','Actual local decode test'),
('THE SECRET','Extra information','redundancy','A QR code stores extra error correction information. A scanner can use it to recover some damaged data.','Redundancy helps repair errors'),
('THE LIMIT','Too much damage?','qr_fail','I made the missing area larger. Now the same decoder fails. Recovery depends on the location and amount of damage.','Not every damaged code works'),
('THE FACT','Four correction levels','levels','There are four correction levels. Higher levels can recover more damaged codewords, but that does not mean you can cover the same percentage of the picture.','Percentages refer to codewords, not image area')]),
'qr_long':('long','How QR Codes Survive Damage: The Hidden Error Correction Test',[QR],[
('01 / THE TEST','A damaged code that still works','qr_recover','This QR code has a missing square in the middle. It looks broken, but the local scanner still reads the exact original text. Let me show you why.','Real test. Plain text, no link.'),
('02 / STRUCTURE','Three big corner markers','finders','Those three large corner squares help the scanner locate the code and its orientation. The smaller black and white modules encode information.','Finder patterns help locate the grid'),
('03 / REDUNDANCY','Extra data helps repair errors','redundancy','The code contains data and extra error correction codewords. The extra information helps reconstruct some missing or incorrect codewords. This diagram is a simplified explanation.','Reed–Solomon error correction'),
('04 / THE LEVELS','Four ways to trade capacity','levels','The four standard correction levels are L, M, Q and H. Their approximate recovery rates are seven, fifteen, twenty five and thirty percent of codewords.','More correction uses more capacity'),
('05 / PROOF','Same text, damaged code','qr_recover','I generated this test code with level H. I covered a small central square, then decoded it with the same local scanner. The recovered text matched exactly.','Measured successful recovery'),
('06 / THE LIMIT','When recovery stops','qr_fail','Then I increased the covered area. The decoder no longer returned the text. The percentage of visible area is not the same as the percentage of codewords.','Damage location and scanner matter'),
('07 / TAKEAWAY','Keep the code readable','final','If you print a QR code, keep the white margin clear, avoid covering the corner markers, and test the actual printed version. Error correction helps, but it is not a guarantee.','Test the final code before sharing')])}
fontroot=Path('C:/Windows/Fonts')
def ft(n,b=True,mono=False):return ImageFont.truetype(str(fontroot/('consola.ttf' if mono else 'segoeuib.ttf' if b else 'segoeui.ttf')),n)
def norm(t):return re.findall(r'[a-z0-9]+',t.lower().replace('qr','q r').replace('gigabytes','gigabyte').replace('gibibytes','gibibyte'))
def ts(t):
 m=round(t*1000);s,m=divmod(m,1000);mi,s=divmod(s,60);h,mi=divmod(mi,60);return f'{h:02}:{mi:02}:{s:02},{m:03}'
def rgba_hex(c):return tuple(int(c[i:i+2],16) for i in (1,3,5))
BG='#0c1119';WHITE='#f4f7fb';LIME='#b8f55b';CYAN='#69d9ec';DIM='#aab7c7';ORANGE='#ffb36a';PANEL='#1b2835'
def ease(t):return 1-(1-min(1,max(0,t)))**3
# Native 1080x1920 or 1920x1080; 30 fps. Central object art and text are generated at target pixels.
def visual(kind,scene,phase,t,caption,wordidx,base=None):
 W,H=(1080,1920) if kind=='short' else (1920,1080);v=kind=='short'
 label,heading,layout,spoken,tip=scene
 # Original radial studio-light gradient, cached by aspect.
 if base is None:
  yy,xx=np.mgrid[:H,:W];r=np.sqrt(((xx-W*.45)/(W*.9))**2+((yy-H*.42)/(H*.9))**2)
  f=np.maximum(0,1-r*1.6);rgb=np.stack([12+15*f,17+28*f,25+35*f],axis=-1).astype(np.uint8);base=Image.fromarray(rgb)
 im=base.copy();d=ImageDraw.Draw(im)
 def text(s,x,y,n,c=WHITE,b=True,mono=False,anchor='lt'):
  d.text((x,y),s,font=ft(n,b,mono),fill=c,anchor=anchor)
 def wrap(s,x,y,n,w,c=WHITE,b=True):
  font=ft(n,b);ls=[];l=''
  for word in s.split():
   trial=(l+' '+word).strip()
   if l and d.textlength(trial,font=font)>w:ls.append(l);l=word
   else:l=trial
  if l:ls.append(l)
  for j,l in enumerate(ls):text(l,x,y+j*int(n*1.13),n,c,b)
  return y+len(ls)*int(n*1.13)
 def pill(s,x,y,c=CYAN):
  wid=int(d.textlength(s,font=ft(28,True,True)))+36
  d.rounded_rectangle((x,y,x+wid,y+49),radius=12,fill=PANEL,outline=c,width=2);text(s,x+18,y+9,28,c,True,True)
 def rect(x,y,w,h,col=PANEL,r=22,outline=None):d.rounded_rectangle((x,y,x+w,y+h),radius=r,fill=col,outline=outline,width=3 if outline else 1)
 def qr(name,x,y,size):
  q=Image.open(E/(name+'.png')).convert('RGB').resize((size,size),Image.Resampling.NEAREST);im.paste(q,(x,y));d.rectangle((x-4,y-4,x+size+3,y+size+3),outline=CYAN,width=4)
 def drive(x,y,w,h):
  # Original dimensional USB illustration, not a product photo.
  d.rounded_rectangle((x+14,y+20,x+w+14,y+h+20),radius=35,fill='#070a10')
  rect(x,y,w,h,'#324958',32,CYAN);rect(x+18,y+18,w-36,h-36,'#162632',24)
  d.rounded_rectangle((x+w*.33,y-h*.34,x+w*.67,y+10),radius=8,fill='#c4cbd1',outline='#e4e9ef',width=3)
  for i in range(2):rect(x+w*.39+i*w*.12,y-h*.23,w*.065,h*.12,'#79858f',3)
  text('128 GB',x+w/2,y+h*.46,int(w*.17),WHITE,True,True,'mm')
 def result(text0,x,y,w,c=LIME):
  rect(x,y,w,94,'#182c32',18,c);text(text0,x+w/2,y+47,42,c,True,False,'mm')
 # Short safe layout: main content up to 1400; captions around 1450; bottom reserved for player UI.
 if v:
  pill('FLOWMINUTE / LAB',55,86);text(label,55,164,33,LIME,True,True)
  yy=wrap(heading,55,227,80,895)+28
  cx=510;left=60;right=960
  if layout=='storage_hook':
   drive(340,yy+110,340,300)
   text('128',270,yy+505,114,WHITE,True,True,'mm');text('119',750,yy+505,114,LIME,True,True,'mm')
   text('GB LABEL',270,yy+595,33,DIM,True,True,'mm');text('GiB DISPLAY',750,yy+595,33,DIM,True,True,'mm')
   d.line((425,yy+505,590,yy+505),fill=CYAN,width=8);d.polygon([(590,yy+485),(620,yy+505),(590,yy+525)],fill=CYAN)
  elif layout in ('decimal','binary','storage_result'):
   if layout=='decimal':
    big='1,000,000,000';sub='BYTES / GB';small='128 × 1 billion'
   elif layout=='binary':
    big='1,073,741,824';sub='BYTES / GiB';small='128,000,000,000 ÷ unit'
   else:big='119.21';sub='GiB';small='128 billion bytes'
   text(big,cx,yy+190,98 if layout=='storage_result' else 65,LIME,True,True,'mm');text(sub,cx,yy+295,42,DIM,True,True,'mm')
   # Equal unit labels, distinct semantic visual: decimal box label, binary unit and exact result.
   if layout=='decimal':
    rect(190,yy+365,640,230,'#243444',26,CYAN)
    text('128 GB',510,yy+426,82,WHITE,True,True,'mm')
    text('MANUFACTURER LABEL',510,yy+530,35,DIM,True,True,'mm')
    text('128 × 1,000,000,000',510,yy+655,43,LIME,True,True,'mm')
   elif layout=='binary':
    text('A LARGER MEASURING UNIT',510,yy+370,34,CYAN,True,True,'mm')
    rect(95,yy+425,890,100,'#283749',18)
    rect(95,yy+425,int(890*1000000000/1073741824),100,CYAN,18)
    text('1 GB',120,yy+452,40,BG,True,True)
    rect(95,yy+560,890,100,'#304331',18)
    rect(95,yy+560,max(10,int(890*ease(t/.7))),100,LIME,18)
    text('1 GiB',120,yy+587,40,BG,True,True)
    text('Same bytes, different unit size.',510,yy+720,39,WHITE,True,False,'mm')
   else:
    rect(75,yy+365,870,350,'#172b35',26,CYAN)
    text('128,000,000,000',510,yy+430,54,WHITE,True,True,'mm')
    d.line((155,yy+485,865,yy+485),fill=DIM,width=3)
    text('1,073,741,824',510,yy+548,52,CYAN,True,True,'mm')
    text('= 119.21 GiB',510,yy+650,57,LIME,True,True,'mm')
    text('Before formatting / reserved space',510,yy+755,35,DIM,True,False,'mm')
  elif layout in ('qr_recover','qr_fail','finders'):
   name='recover' if layout=='qr_recover' else 'fail' if layout=='qr_fail' else 'intact'
   size=580;qx=220;qy=yy+30;qr(name,qx,qy,size)
   sy=int(qy+size*min(1,t/1.15));d.line((qx,sy,qx+size,sy),fill=CYAN,width=5)
   if t>=.8:result('DECODED: TEST TEXT' if layout=='qr_recover' else 'NO RESULT' if layout=='qr_fail' else 'FINDER PATTERNS',60,qy+620,900,LIME if layout!='qr_fail' else ORANGE)
   else:result('SCANNING...',60,qy+620,900,CYAN)
  elif layout=='redundancy':
   # Labeled simplified codeword model; not actual QR placement.
   for j in range(12):
    x=100+(j%4)*210;y=yy+65+(j//4)*170
    erased=j==5 and t<1.1
    rect(x,y,160,130,'#253442' if erased else CYAN if j<8 else '#49692e',18)
    text('?' if erased else str(j+1).zfill(2),x+80,y+65,58,WHITE if erased or j>=8 else BG,True,True,'mm')
   text('DATA',95,yy+610,38,CYAN);text('CORRECTION',540,yy+610,38,LIME)
   text('SIMPLIFIED MODEL',95,yy+675,29,DIM,True,True)
  else:
   for j,(lab,num) in enumerate([('L',7),('M',15),('Q',25),('H',30)]):
    y=yy+45+j*160;text(lab,70,y+13,54,WHITE,True,True);rect(170,y+18,660,60,'#263343',12)
    ww=max(1,int(660*num/30*ease(t/.85)));rect(170,y+18,ww,60,LIME if j==3 else CYAN,12)
    text(str(num)+'%',865,y+10,48,LIME if j==3 else WHITE,True,True)
   text('Approx. codeword recovery',60,yy+715,37,DIM)
  rect(55,1280,900,130,'#162d32',20)
  wrap(tip,78,1303,39,850,LIME)
  if caption:
   # Highlight active spoken word; line wraps and measures at native resolution.
   words=caption.split();font=ft(47);lines=[];line=[];wid=0
   for j,w in enumerate(words):
    n=d.textlength(w+' ',font=font)
    if line and wid+n>850:lines.append(line);line=[];wid=0
    line.append((j,w));wid+=n
   if line:lines.append(line)
   assert len(lines)<=2,(caption,lines)
   for j,line in enumerate(lines):
    total=sum(d.textlength(w+' ',font=font) for _,w in line);x=(1010-total)/2
    for k,w in line:
     text(w,x,1470+j*57,47,LIME if k==wordidx else WHITE)
     x+=d.textlength(w+' ',font=font)
 else:
  pill('FLOWMINUTE / LAB',68,47);text(label,70,117,30,LIME,True,True)
  wrap(heading,70,173,71,1770)
  x=95;y=310
  if layout in ('qr_recover','qr_fail','finders'):
   name='recover' if layout=='qr_recover' else 'fail' if layout=='qr_fail' else 'intact';size=480;qr(name,x,y,size)
   if layout=='finders':
    # Mark the approximate positions of the three finder regions on the illustrative enlarged grid.
    for dx,dy in [(0,0),(size-150,0),(0,size-150)]:d.rounded_rectangle((x+dx+10,y+dy+10,x+dx+140,y+dy+140),radius=10,outline=LIME,width=5)
    text('Locate',690,330,64,CYAN);text('Orient',690,430,64,WHITE);text('Read the grid',690,530,64,LIME)
   else:
    sy=int(y+size*min(1,t/1.15));d.line((x,sy,x+size,sy),fill=CYAN,width=5)
    text('LOCAL DECODER',690,330,39,DIM,True,True)
    result('MATCHED ORIGINAL TEXT' if layout=='qr_recover' else 'NO DECODE RESULT',690,460,1100,LIME if layout=='qr_recover' else ORANGE)
    if layout=='qr_recover':text(payload,710,600,55,WHITE,True,True)
  elif layout=='redundancy':
   for j in range(12):
    xx=115+(j%6)*275;yy=335+(j//6)*185;erased=j==4 and t<1.1
    rect(xx,yy,205,140,'#263343' if erased else CYAN if j<8 else '#49692e',20)
    text('?' if erased else str(j+1).zfill(2),xx+102,yy+70,64,WHITE if erased or j>=8 else BG,True,True,'mm')
   text('DATA CODEWORDS',115,735,32,CYAN);text('EXTRA CORRECTION',1120,735,32,LIME)
  elif layout=='levels':
   for j,(l,n) in enumerate([('L',7),('M',15),('Q',25),('H',30)]):
    yy=310+j*116;text(l,105,yy,53,WHITE,True,True);rect(220,yy+8,1300,62,'#293847',12);rect(220,yy+8,max(1,int(1300*n/30*ease(t/.85))),62,LIME if j==3 else CYAN,12);text(str(n)+'%',1580,yy,53,LIME if j==3 else WHITE,True,True)
  else:
   qr('intact',95,310,480)
   for j,s in enumerate(['Keep white margin clear','Protect corner markers','Test the printed code']):
    rect(670,320+j*150,1090,115,'#234337' if phase>=j else PANEL,20);text(str(j+1)+'. '+s,705,351+j*150,49,LIME if phase>=j else WHITE)
  rect(70,820,1775,72,'#162d32',18);text(tip,95,836,37,LIME)
  if caption:
   f=ft(44);width=sum(d.textlength(s+' ',font=f) for s in caption.split());x=(W-width)/2
   for j,s in enumerate(caption.split()):text(s,x,945,44,LIME if j==wordidx else WHITE);x+=d.textlength(s+' ',font=f)
 return im
engine=Kokoro(str(OLD/'kokoro-v1.0.int8.onnx'),str(OLD/'voices-v1.0.bin'))
asr=WhisperModel('base',device='cpu',compute_type='int8',local_files_only=True,cpu_threads=4)
def produce(key):
 kind,title,sources,scenes=SPECS[key];work=R/key;work.mkdir(exist_ok=True);W,H=(1080,1920) if kind=='short' else (1920,1080)
 dur=[];starts=[];audits=[];audio=[];cues=[];total=0
 for i,s in enumerate(scenes):
  spoken=s[3];rawp=work/f'raw{i}.wav';a=work/f'a{i}.wav'
  oldqa=json.loads((work/'qa.json').read_text(encoding='utf8')) if (work/'qa.json').exists() else None
  if oldqa and oldqa['scenes'][i]['spoken']==spoken and a.exists():
   dt=oldqa['scenes'][i]['end']-oldqa['scenes'][i]['start']
   with wave.open(str(a),'rb') as wav:assert abs(wav.getnframes()/wav.getframerate()-dt)<.002
  else:
   samples,sr=engine.create(spoken,voice='af_heart',speed=1.04,lang='en-us')
   sf.write(str(rawp),samples,sr,subtype='PCM_16');dt=math.ceil((len(samples)/sr+.30)*FPS)/FPS
   cmd(['-i',rawp,'-af','loudnorm=I=-16:TP=-2:LRA=7,apad','-t',str(dt),'-ar','48000','-ac','1','-c:a','pcm_s16le',a])
   # Pad the exact PCM length; avoid cumulative drift in concatenation.
   x,sr2=sf.read(str(a),dtype='int16');target=round(dt*48000);x=np.pad(x,(0,max(0,target-len(x))))[:target];sf.write(str(a),x,48000,subtype='PCM_16')
  seg,_=asr.transcribe(str(a),language='en',word_timestamps=True,beam_size=3,condition_on_previous_text=False,vad_filter=False)
  words=[w for z in list(seg) for w in (z.words or [])];heard=' '.join(w.word.strip() for w in words);match=difflib.SequenceMatcher(None,norm(spoken),norm(heard),autojunk=False).ratio()
  # Numeric ASR formatting can differ; explicit semantic review required below, no fake perfect transcript.
  if match<.65:raise RuntimeError(f'ASR failed {key} {i} {match} {heard}')
  group=[]
  def flush():
   if group:
    text0=' '.join(w.word.strip() for w in group);t0=max(0,group[0].start);t1=min(dt,group[-1].end)
    if t1>t0:cues.append({'start':total+t0,'end':total+t1,'text':text0,'words':[(total+w.start,total+min(w.end,dt)) for w in group]})
  for w in words:
   if group and (len(group)>=6 or len(' '.join(z.word.strip() for z in group+[w]))>43):flush();group=[]
   group.append(w)
  flush();starts.append(total);dur.append(dt);total+=dt;audio.append(a);audits.append({'scene':i+1,'expected':spoken,'recognized':heard,'similarity':round(match,3)});print('SPEECH',key,i+1,round(match,3),round(dt,2),heard,flush=True)
 # Rasterize at native resolution. Precompute scene backgrounds and draw semantic moving parts per frame.
 yy,xx=np.mgrid[:H,:W];rad=np.sqrt(((xx-W*.45)/(W*.9))**2+((yy-H*.42)/(H*.9))**2);f=np.maximum(0,1-rad*1.6);base=Image.fromarray(np.stack([12+15*f,17+28*f,25+35*f],axis=-1).astype(np.uint8));del yy,xx,rad,f
 clips=[];stills=[]
 # Use 30 fps exact timeline. Cache static frames; active animation is rendered on every frame.
 for i,(s,dt) in enumerate(zip(scenes,dur)):
  p=work/f'scene{i}.mp4';n=round(dt*FPS)
  proc=subprocess.Popen([F,'-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','-','-c:v','libx264','-preset','ultrafast','-crf','17','-threads','4','-pix_fmt','yuv420p',str(p)],stdin=subprocess.PIPE)
  cache={}
  for j in range(n):
   t=j/FPS;absolute=starts[i]+t;c=next((c for c in cues if c['start']<=absolute<c['end']),None)
   wordidx=next((k for k,(a,b) in enumerate(c['words']) if a<=absolute<b),-1) if c else -1
   phase=min(2,int(t/dt*3));layout=s[2]
   anim=j if (t<1.2 and layout in ('qr_recover','qr_fail','finders')) or (t<.9 and layout in ('levels','decimal','binary','storage_result')) or (layout=='redundancy' and t<1.15) else -1
   ck=(anim,phase,c['text'] if c else None,wordidx)
   if ck not in cache:
    frame=visual(kind,s,phase,t,c['text'] if c else None,wordidx,base)
    data=frame.tobytes()
    # Only cache held frames, not all full-HD animation frames.
    if anim==-1:
     cache.clear();cache[ck]=data
   else:data=cache[ck]
   proc.stdin.write(data)
  proc.stdin.close();assert proc.wait()==0
  st=visual(kind,s,2,1.2,None,-1,base);st.thumbnail((270,480) if kind=='short' else (480,270));stills.append(st);clips.append(p);print('SCENE',key,i+1,flush=True)
 (work/'vcat.txt').write_text('\n'.join("file '"+p.as_posix()+"'" for p in clips)+'\n')
 (work/'acat.txt').write_text('\n'.join("file '"+p.as_posix()+"'" for p in audio)+'\n')
 narr=work/'narration.wav';cmd(['-f','concat','-safe','0','-i',work/'acat.txt','-c:a','pcm_s16le',narr])
 sr=48000;tt=np.arange(round(total*sr))/sr;bed=.004*np.sin(2*np.pi*110*tt)+.0025*np.sin(2*np.pi*164.81*tt);rng=np.random.default_rng(27)
 # Original restrained foley: transient ticks for moving states, short scan confirmation sound.
 for i,(at,dt,s) in enumerate(zip(starts,dur,scenes)):
  for delay in ([.12,.8] if 'qr_' in s[2] else [.18,.55] if s[2] in ('levels','decimal','binary','storage_result') else [.18]):
   j=round((at+delay)*sr);n=min(round(.14*sr),len(bed)-j);u=np.arange(n)/sr
   if n>0:bed[j:j+n]+=.019*np.diff(rng.normal(0,1,n),prepend=0)*np.exp(-u*65)+.017*np.sin(2*np.pi*(560 if s[2]=='qr_fail' else 840)*u)*np.exp(-u*38)
 bed[:sr//3]*=np.linspace(0,1,sr//3);bed[-sr//2:]*=np.linspace(1,0,sr//2);music=work/'original_bed.wav';sf.write(str(music),bed,sr,subtype='PCM_16')
 final=work/'B1V9_FINAL.mp4'
 cmd(['-f','concat','-safe','0','-i',work/'vcat.txt','-i',narr,'-i',music,'-filter_complex','[1:a][2:a]amix=inputs=2:duration=first:normalize=0,alimiter=limit=.92[a]','-map','0:v','-map','[a]','-c:v','libx264','-preset','veryfast','-crf','17','-maxrate','12M','-bufsize','24M','-threads','4','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','192k','-movflags','+faststart',final])
 cmd(['-i',final,'-map','0:v','-map','0:a','-f','null','NUL'])
 captions=work/'captions.srt';captions.write_text('\n\n'.join(f"{i+1}\n{ts(c['start'])} --> {ts(c['end'])}\n{c['text']}" for i,c in enumerate(cues))+'\n',encoding='utf8')
 thumb=work/'thumbnail.jpg';im=visual(kind,scenes[0],2,1.2,None,-1,base);im.thumbnail((1280,1920));im.save(thumb,quality=95)
 tw,th=stills[0].size;sheet=Image.new('RGB',(tw*3,math.ceil(len(stills)/3)*th),BG)
 for i,s in enumerate(stills):sheet.paste(s,(i%3*tw,i//3*th))
 sheet.save(work/'contact.jpg',quality=93)
 def rms(p):
  a,_=sf.read(str(p));return 20*np.log10(max(np.sqrt(np.mean(a*a)),1e-8))
 margin=float(rms(narr)-rms(music));assert margin>=15
 audit=work/'audio_audit.json';audit.write_text(json.dumps({'voice':'af_heart','human_listening':False,'voice_over_bed_db':round(margin,2),'scenes':audits},indent=2))
 doc={'key':key,'title':title,'format':kind,'duration':round(total,3),'sources':sources,'video':art(final),'captions':art(captions),'thumbnail':art(thumb),'audio_audit':art(audit),'proof':art(E/'proof.json'),'full_decode':True,'voice_over_bed_db':round(margin,2),'scenes':[{'start':starts[i],'end':starts[i]+dur[i],'role':s[0],'layout':s[2],'spoken':s[3],'takeaway':s[4]} for i,s in enumerate(scenes)]}
 (work/'qa.json').write_text(json.dumps(doc,indent=2,ensure_ascii=False),encoding='utf8');print('FINAL',key,doc['duration'],doc['video']['sha256'],flush=True)
if __name__=='__main__':
 for key in sys.argv[1:] or list(SPECS):produce(key)
 print('ALL_RENDERED',flush=True)
