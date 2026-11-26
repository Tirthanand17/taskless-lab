"""B1v8: real photo + executed byte-level experiments; no fake native UI.
Commercially licensed Kokoro voice, original foley-style synthesis and timed captions.
No YouTube writes. Render and exact-byte QA first.
"""
from pathlib import Path
import sys,json,math,hashlib,subprocess,zipfile,shutil,io,re,difflib,wave
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
R=Path(__file__).resolve().parent;B=R.parent;OLD=B/'nov24-b1v6';E=R/'evidence';E.mkdir(exist_ok=True)
sys.path[:0]=[str(OLD/'kokoro_vendor'),str(B/'nov22-branch1-recovery'/'ffmpeg_vendor')]
import imageio_ffmpeg,soundfile as sf,espeakng_loader
from phonemizer.backend.espeak.wrapper import EspeakWrapper
EspeakWrapper.set_library(espeakng_loader.get_library_path())
from kokoro_onnx import Kokoro
from faster_whisper import WhisperModel
F=imageio_ffmpeg.get_ffmpeg_exe();FPS=24
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cmd(args,cwd=None):
 q=subprocess.run([F,'-hide_banner','-loglevel','error','-y',*map(str,args)],cwd=cwd,capture_output=True,text=True)
 if q.returncode:raise RuntimeError(q.stderr[-2400:])
 return q.stdout
def art(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
# Original licensed Pexels photo, actual files used in the experiments.
source=OLD/'drive.jpg';shutil.copyfile(source,E/'photo.jpg')
photo=E/'photo.jpg';renamed=E/'renamed.png';converted=E/'converted.png';shutil.copyfile(photo,renamed)
im=Image.open(photo).convert('RGB');im.save(converted,format='PNG')
sample=E/'notes.txt';sample.write_bytes((b'Name,Item,Quantity\nSample,Notebook,1\n'*2500))
def ziptest(p):
 out=E/(p.name+'.zip')
 with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.write(p,p.name)
 with zipfile.ZipFile(out) as z:assert z.read(p.name)==p.read_bytes()
 return {'input':p.stat().st_size,'zip':out.stat().st_size,'saved_pct':round((1-out.stat().st_size/p.stat().st_size)*100,1)}
Z={'text':ziptest(sample),'jpeg':ziptest(photo)}
def fproof(p):
 with Image.open(p) as img:return {'name':p.name,'format':img.format,'bytes':p.stat().st_size,'dimensions':list(img.size),'header':p.read_bytes()[:8].hex(' ').upper(),'sha256':sha(p)}
A=fproof(photo);N=fproof(renamed);P=fproof(converted)
assert A['sha256']==N['sha256'] and N['format']=='JPEG' and P['format']=='PNG' and A['dimensions']==P['dimensions']
assert np.array_equal(np.asarray(Image.open(photo).convert('RGB')),np.asarray(Image.open(converted).convert('RGB')))
proof={'zip':Z,'original':A,'renamed':N,'converted':P,'decoded_pixels_equal':True,'photo_source':'https://www.pexels.com/photo/man-showing-usb-stick-on-hand-4792750/','license':'https://www.pexels.com/license/','method':'Python zipfile and Pillow, executed locally on disposable copies; all archive contents round-tripped; image format detected from bytes'}
(E/'proof.json').write_text(json.dumps(proof,indent=2));print('ACTUAL_TESTS',json.dumps(proof),flush=True)
engine=Kokoro(str(OLD/'kokoro-v1.0.int8.onnx'),str(OLD/'voices-v1.0.bin'))
asr=WhisperModel('base',device='cpu',compute_type='int8',local_files_only=True,cpu_threads=4)
SOURCE_EXT='https://support.microsoft.com/en-us/windows/experience/storage-filemanagement/common-file-name-extensions-in-windows'
SOURCE_ZIP='https://support.microsoft.com/en-us/windows/experience/storage-filemanagement/zip-and-unzip-files'
# role, layout, headline, speech, lower-screen takeaway
SPECS={
'zip_short':{'kind':'short','title':'Why ZIP Barely Shrinks Your Photos #Shorts','sources':[SOURCE_ZIP],'hook':'result_first','scenes':[
('hook','zip_compare','ZIP: same tool, different results','Same ZIP tool. Two files. The text archive is tiny. The photo barely shrinks.','Repeated text compresses much more than this photo.'),
('action','text','Text has patterns','The text repeats the same words. A ZIP archive can store those patterns much more efficiently.','ZIP stores repeated patterns; extraction restores the text.'),
('result','jpeg','JPEG is already compressed','This photo is already compressed. A ZIP file cannot magically remove much more data.','JPEG already reduces image data; ZIP adds little here.'),
('takeaway','zip_final','Use ZIP for the right job','ZIP is great for bundling files. For smaller photos, resize them or use an appropriate image export setting.','Bundle with ZIP. Resize a copy to reduce photo size.')]},
'rename_short':{'kind':'short','title':'Renaming JPG to PNG Does NOT Convert It #Shorts','sources':[SOURCE_EXT],'hook':'problem_first','scenes':[
('hook','rename','A new name is not a new format','I renamed this photo from J P G to P N G. Looks converted, right? But the file is still a J peg.','Same photo • different filename'),
('action','bytes','The bytes tell the truth','Look at the actual file header. Both copies have identical bytes.','The extension is only a label'),
('result','convert','This is a real conversion','Then I exported the photo as P N G. Now the file header and the detected format actually changed.','Real export • new format'),
('takeaway','rename_final','Export, don’t just rename','Use your image editor and choose Save as P N G. Keep your original photo, just in case.','Save As → PNG')]},
'long':{'kind':'long','title':'JPG vs PNG: Why Renaming a File Does Not Convert It (Real Test)','sources':[SOURCE_EXT,SOURCE_ZIP],'hook':'result_first','scenes':[
('hook','rename','Same picture. Different filename.','These two photos look the same. One says J P G, and one says P N G. But both are actually J peg files. Here is how I know.','Two filenames; one actual format'),
('setup','photo','Start with the original','I used a real sample photo. I made a separate copy first, so the original stays safe. I did not change anyone’s personal files.','Work with a copy'),
('action','bytes','Read the file header','An extension is part of the name. The actual contents tell an image reader what format it is. This is the header from my original photo.','Header bytes identify the example format'),
('result','rename','Rename the copy','Now I give the copy a P N G extension. The filename changes. The header stays exactly the same, and the image reader still detects J peg.','Verified: identical file hash'),
('action','convert','Export to a new format','Next, I actually decode the picture and export it as P N G. This is a different operation. Notice the new header and the new detected format.','Executed with a local image conversion tool'),
('explanation','size','Does PNG make it smaller?','Not necessarily. Look at the measured sizes of these two images. P N G uses a different compression method. The size depends on the image, so conversion is not a guaranteed saving.','Measured sizes from this photo only'),
('explanation','pixels','What happens to the picture?','I compared the decoded pixels from the two files. For this conversion, they match exactly. But saving a J peg as P N G cannot restore details that were lost earlier.','The converted pixels match this source'),
('takeaway','rename_final','How to do this yourself','In an image editor, open the original photo, choose Save as or Export, select P N G, and save a separate copy. Do not simply rename the extension.','Keep the original • verify the exported file')]}}
FONT=Path('C:/Windows/Fonts')
def ft(n,b=True,mono=False):return ImageFont.truetype(str(FONT/('consola.ttf' if mono else 'segoeuib.ttf' if b else 'segoeui.ttf')),n)
def norm(t):
 t=t.lower().replace('j p g','jpg').replace('p n g','png').replace('j peg','jpeg').replace('j-peg','jpeg').replace('j.p.g.','jpg').replace('p.n.g.','png')
 return re.findall(r'[a-z0-9]+',t)
def stamp(t):
 ms=round(t*1000);s,ms=divmod(ms,1000);m,s=divmod(s,60);h,m=divmod(m,60);return f'{h:02}:{m:02}:{s:02},{ms:03}'
def kb(n):return f'{n/1024:,.1f} KB'
def audio_rms(p):
 with wave.open(str(p),'rb') as f:x=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(float)/32768
 return 20*math.log10(max(np.sqrt(np.mean(x*x)),1e-9))
def groups(words,offset,dur):
 g=[];out=[]
 def flush():
  if not g:return
  a,b=max(0,g[0].start),min(dur,g[-1].end)
  t=' '.join(x.word.strip() for x in g)
  t=re.sub(r'\bJ P G\b','JPG',t,flags=re.I);t=re.sub(r'\bP N G\b','PNG',t,flags=re.I);t=re.sub(r'\bJ peg\b','JPEG',t,flags=re.I)
  if b>a:out.append([offset+a,offset+b,t])
 for w in words:
  if g and (len(' '.join(x.word.strip() for x in g+[w]))>44 or len(g)>=7):flush();g=[]
  g.append(w)
 flush()
 merged=[]
 for c in out:
  if merged and c[1]-c[0]<.85 and c[0]-merged[-1][1]<.13 and len(merged[-1][2]+' '+c[2])<=68:merged[-1][1]=c[1];merged[-1][2]+=' '+c[2]
  else:merged.append(c)
 return merged
BG='#111b27';PANEL='#203246';WHITE='#f2f6fb';DIM='#bdcad8';TEAL='#68e7bd';AMBER='#ffbb7d';BLUE='#a8c8ff'
def renderer(kind):
 W,H=(1080,1920) if kind=='short' else (1920,1080);v=kind=='short'
 ph=Image.open(photo).convert('RGB')
 def txt(d,t,x,y,n,c=WHITE,b=True,mono=False,anchor='lt'):
  d.text((x,y),t,font=ft(n,b,mono),fill=c,anchor=anchor)
 def wrap(d,t,x,y,n,w,c=WHITE,b=True):
  f=ft(n,b);line='';ls=[]
  for word in t.split():
   z=(line+' '+word).strip()
   if line and d.textlength(z,font=f)>w:ls.append(line);line=word
   else:line=z
  if line:ls.append(line)
  for i,l in enumerate(ls):
   assert d.textlength(l,font=f)<=w+1,(l,w)
   txt(d,l,x,y+i*int(n*1.16),n,c,b)
  return y+len(ls)*int(n*1.16)
 def box(d,xy,col=PANEL,r=22):d.rounded_rectangle(xy,r,fill=col)
 def picture(img,x,y,w,h):
  a=ImageOps.fit(ph,(w,h),method=Image.Resampling.LANCZOS);img.paste(a,(x,y));ImageDraw.Draw(img).rectangle((x,y,x+w,y+h),outline='#52708a',width=3)
 def tag(d,t,x,y,c=TEAL):txt(d,t,x,y,30 if v else 28,c)
 def stat(d,x,y,w,label,value,c=TEAL,sub=None):
  box(d,(x,y,x+w,y+(164 if v else 145)))
  txt(d,label,x+24,y+18,34 if v else 30,DIM)
  txt(d,value,x+24,y+65,57 if v else 53,c)
  if sub:txt(d,sub,x+w-24,y+23,26,DIM,False,anchor='rt')
 def header(d,head,idx):
  tag(d,'FLOWMINUTE LAB  /  ACTUAL FILE TEST',60,112 if v else 40)
  if v:return wrap(d,head,60,188,76,900)+28
  return wrap(d,head,70,95,70,1770)+28
 def render(scene,idx,phase,progress,cap=None):
  role,layout,head,spoken,tip=scene;img=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(img)
  # intentional full-width gradient/photo content; title and captions use contrast.
  for y0 in range(0,H,8):
   k=y0/H;d.rectangle((0,y0,W,y0+8),fill=(17+int(5*k),27+int(9*k),39+int(12*k)))
  top=header(d,head,idx)
  if v:
   x=60;w=900
   if layout in ('zip_compare','zip_final'):
    for j,(k,label) in enumerate([('text','TEXT FILE'),('jpeg','REAL JPEG PHOTO')]):
     z=Z[k];y=top+j*385;box(d,(x,y,x+w,y+350))
     txt(d,label,x+26,y+18,35,BLUE)
     txt(d,kb(z['input']),x+26,y+80,50);txt(d,'→',x+384,y+76,49,DIM);txt(d,kb(z['zip']),x+480,y+80,50,TEAL)
     base=z['input'];ratio=min(1,z['zip']/base)
     d.rounded_rectangle((x+26,y+165,x+w-26,y+203),radius=17,fill='#4c5e71')
     rr=max(4,int((w-52)*(1+(ratio-1)*progress)))
     d.rounded_rectangle((x+26,y+221,x+26+rr,y+259),radius=17,fill=TEAL if k=='text' else AMBER)
     txt(d,f"{z['saved_pct']:+.1f}% space saved",x+26,y+278,42,TEAL if k=='text' else AMBER)
    y=top+782
   elif layout=='text':
    box(d,(x,top,x+w,top+730),'#1f3548')
    txt(d,'ACTUAL SAMPLE TEXT',x+30,top+30,37,BLUE)
    for j in range(5):txt(d,'Sample,Notebook,1',x+35,top+106+j*68,43,TEAL if phase>j else WHITE,False,True)
    stat(d,x+25,top+482,w-50,'ZIP OUTPUT',kb(Z['text']['zip']),TEAL)
    y=top+755
   elif layout=='jpeg':
    picture(img,x,top,w,500)
    stat(d,x,top+526,w,'ORIGINAL PHOTO',kb(Z['jpeg']['input']),WHITE)
    stat(d,x,top+708,w,'ZIPPED PHOTO',kb(Z['jpeg']['zip']),AMBER);y=top+890
   elif layout=='rename_final':
    picture(img,x,top,w,300)
    for j,label in enumerate(['Open the original photo','Choose Save As / Export','Select PNG; save a copy']):
     yy0=top+320+j*138;box(d,(x,yy0,x+w,yy0+120),'#22434a' if j<=phase else PANEL)
     txt(d,str(j+1)+'. '+label,x+24,yy0+32,44,TEAL if j<=phase else WHITE)
    y=top+734
   elif layout in ('rename','convert'):
    picture(img,x,top,w,470)
    first=A;second=P if layout=='convert' else N
    stat(d,x,top+490,w,'ORIGINAL: '+first['name'],first['format'],WHITE)
    stat(d,x,top+672,w,'NEW: '+second['name'],second['format'],TEAL if layout=='convert' else AMBER)
    y=top+854
   else:
    picture(img,x,top,w,340)
    box(d,(x,top+360,x+w,top+725))
    txt(d,'ACTUAL FILE HEADER',x+30,top+385,34,BLUE)
    txt(d,A['header'],x+30,top+455,47,WHITE,True,True)
    txt(d,'RENAMED COPY',x+30,top+540,34,BLUE)
    txt(d,N['header'],x+30,top+610,47,TEAL,True,True);y=top+760
   # Lower-screen content is a useful, persistent takeaway, not empty decorative footer.
   yy=min(max(y+22,1220),1370);box(d,(60,yy,960,1515),'#163e3b',20)
   txt(d,'WHAT THIS MEANS',84,yy+18,27,DIM)
   end=wrap(d,tip,84,yy+58,39,850,TEAL)
   assert end<=1515,(tip,end)
   if cap:
    box(d,(55,1540,965,1662),'#070d15',18);end=wrap(d,cap,80,1555,43,860)
    assert end<=1662,(cap,end)
  else:
   x=70;right=1020
   picture(img,x,235,860,510)
   if layout=='rename_final':
    for j,label in enumerate(['Open original image','Save As / Export','Select PNG and save']):
     yy0=235+j*158;box(d,(right,yy0,1840,yy0+138),'#22434a' if j<=phase else PANEL)
     txt(d,str(j+1)+'. '+label,right+25,yy0+35,48,TEAL if j<=phase else WHITE)
    txt(d,'Verified output: '+P['format'],right,720,34,TEAL)
   elif layout in ('rename','convert'):
    other=P if layout=='convert' else N
    stat(d,right,235,820,'ORIGINAL: '+A['name'],A['format'],WHITE)
    stat(d,right,410,820,'SECOND: '+other['name'],other['format'],TEAL if layout=='convert' else AMBER)
    if phase>=1:wrap(d,'Header: '+other['header'],right,603,42,820,TEAL)
   elif layout=='size':
    for j,f in enumerate([A,P]):
     y=250+j*210;stat(d,right,y,820,f['format']+' FILE SIZE',kb(f['bytes']),TEAL if j else WHITE)
     ratio=f['bytes']/max(A['bytes'],P['bytes'])
     d.rounded_rectangle((right,y+160,right+int(820*ratio*progress),y+183),radius=10,fill=TEAL if j else BLUE)
   elif layout=='bytes':
    tag(d,'ORIGINAL HEADER',right,240,BLUE);txt(d,A['header'],right,304,52,WHITE,True,True)
    tag(d,'RENAMED HEADER',right,430,BLUE);txt(d,N['header'],right,493,52,TEAL,True,True)
    if phase>=1:txt(d,'SHA-256 MATCH',right,630,59,TEAL)
   elif layout=='pixels':
    stat(d,right,235,820,'DECODED PIXELS','MATCH',TEAL)
    stat(d,right,410,820,'IMAGE DIMENSIONS',f"{A['dimensions'][0]} × {A['dimensions'][1]}",WHITE)
    if phase>=1:wrap(d,'Lost JPEG detail cannot be recovered.',right,605,43,820,AMBER)
   else:
    stat(d,right,235,820,'SOURCE FORMAT',A['format'],WHITE)
    stat(d,right,410,820,'SEPARATE COPY','Original kept',TEAL)
   box(d,(70,780,1840,878),'#163e3b');wrap(d,tip,100,798,43,1700,TEAL)
   if cap:box(d,(160,914,1760,1009),'#070d15');txt(d,cap,960,938,45,WHITE,True,anchor='mt')
  return img
 return W,H,render
def produce(key,spec):
 kind=spec['kind'];scenes=spec['scenes'];work=R/key;work.mkdir(exist_ok=True)
 W,H,render=renderer(kind);durations=[];starts=[];audits=[];cues=[];audio=[];offset=0
 prior=None;priorvoice=None;priorcues=[]
 if (work/'qa.json').exists():
  prior=json.loads((work/'qa.json').read_text(encoding='utf8'));priorvoice=json.loads((work/'audio_audit.json').read_text(encoding='utf8'))
  def seconds(x):
   hh,mm,ss=x.replace(',','.').split(':');return int(hh)*3600+int(mm)*60+float(ss)
  for block in (work/'captions.srt').read_text(encoding='utf8').strip().split('\n\n'):
   ls=block.splitlines();a,b=ls[1].split(' --> ');priorcues.append((seconds(a),seconds(b),' '.join(ls[2:])))
 for i,scene in enumerate(scenes):
  spoken=scene[3];raw=work/f'raw{i}.wav';a=work/f'a{i}.wav'
  if prior and prior['scenes'][i]['spoken']==spoken and a.exists():
   old=prior['scenes'][i];dur=old['end']-old['start'];delta=offset-old['start']
   with wave.open(str(a),'rb') as wav:assert abs(wav.getnframes()/wav.getframerate()-dur)<.15
   starts.append(offset);durations.append(dur);audio.append(a);audits.append(priorvoice['scenes'][i])
   cues.extend([[max(offset,x+delta),min(offset+dur,y+delta),t] for x,y,t in priorcues if x>=old['start']-.002 and x<old['end']-.002])
   offset+=dur;print('REUSED_VERIFIED_SPEECH',key,i+1,flush=True);continue
  # Voice used by the best-performing Nov24 USB-C Short. Phrase punctuation is intentional.
  samples,sr=engine.create(spoken,voice='af_heart',speed=1.04 if kind=='short' else 1.01,lang='en-us')
  assert len(samples)>1000 and sr==24000
  sf.write(str(raw),samples,sr,subtype='PCM_16');dur=math.ceil((len(samples)/sr+.18)*FPS)/FPS
  cmd(['-i',raw,'-af','loudnorm=I=-16:TP=-2:LRA=7,apad','-t',str(dur),'-ar','48000','-ac','1','-c:a','pcm_s16le',a])
  segments,_=asr.transcribe(str(a),language='en',word_timestamps=True,beam_size=3,condition_on_previous_text=False,vad_filter=False)
  words=[w for z in list(segments) for w in (z.words or [])];heard=' '.join(w.word.strip() for w in words)
  match=difflib.SequenceMatcher(None,norm(spoken),norm(heard),autojunk=False).ratio()
  if match<.80:raise RuntimeError(f'Speech verification failed {key} {i} {match} {heard}')
  starts.append(offset);durations.append(dur);audio.append(a);cues.extend(groups(words,offset,dur))
  audits.append({'scene':i+1,'expected':spoken,'recognized':heard,'similarity':round(match,3)})
  print('SPEECH',key,i+1,round(match,3),round(dur,2),heard,flush=True);offset+=dur
 # Each scene includes actual visual evidence and multiple synchronized semantic reveals.
 entries=[];stills=[];frame_count=0
 for i,(scene,dur) in enumerate(zip(scenes,durations)):
  nf=round(dur*FPS);base=starts[i];cuts={0,nf}
  for c in cues:
   for t in c[:2]:
    j=round((t-base)*FPS)
    if 0<j<nf:cuts.add(j)
  # Short, purposeful bar reveal based on measured data; actual file-state comparisons stay readable.
  if scene[1] in ('zip_compare','zip_final','size'):
   cuts.update(j for j in range(3,min(nf,21),3))
  cuts.update(round(nf*f) for f in (.38,.68))
  cuts=sorted(cuts)
  for j,(a,b) in enumerate(zip(cuts,cuts[1:])):
   if b<=a:continue
   t=a/FPS;absolute=base+t;cap=next((c[2] for c in cues if c[0]<=absolute+.02<c[1]),None)
   progress=min(1,.15+t/.8);phase=int(t>=dur*.38)+int(t>=dur*.68)
   f=work/f'frame_{i:02}_{j:03}.png';render(scene,i,phase,progress,cap).save(f)
   entries.extend([f"file '{f.name}'", 'option framerate 24', f'duration {(b-a)/FPS:.9f}'])
   frame_count+=b-a
  st=render(scene,i,2,1,None);st.thumbnail((270,480) if kind=='short' else (480,270));stills.append(st)
  print('SCENE_VISUAL',key,i+1,flush=True)
 entries.extend([f"file '{f.name}'",'option framerate 24'])
 (work/'vcat.txt').write_text('\n'.join(entries)+'\n',encoding='utf8')
 (work/'acat.txt').write_text('\n'.join("file '"+p.as_posix()+"'" for p in audio)+'\n')
 narr=work/'narration.wav';cmd(['-f','concat','-safe','0','-i',work/'acat.txt','-c:a','pcm_s16le',narr])
 sr=48000;t=np.arange(round(offset*sr))/sr
 # Original quiet acoustic-style bed and foley-inspired clicks/rustles; not recordings.
 rng=np.random.default_rng(26);bed=np.zeros(len(t))
 for f0 in [110,164.81,220]:
  bed+=.0035*np.sin(2*np.pi*f0*t+.22*np.sin(2*np.pi*.24*t))
 for at in starts[1:]:
  j=round(at*sr);n=min(int(.16*sr),len(bed)-j);u=np.arange(n)/sr
  noise=rng.normal(0,1,n);noise=np.diff(noise,prepend=0)
  bed[j:j+n]+=(.018*noise*np.exp(-u*48)+.022*np.sin(2*np.pi*760*u)*np.exp(-u*50))
 # Foley cues synchronized with the demonstrated state, rather than a looping effect.
 for scene,at,dur in zip(scenes,starts,durations):
  layout=scene[1]
  if layout in ('zip_compare','zip_final','size'):
   for tick in range(7):
    j=round((at+.12+tick*.075)*sr);n=min(int(.055*sr),len(bed)-j);u=np.arange(n)/sr
    if n>0:bed[j:j+n]+=.011*np.diff(rng.normal(0,1,n),prepend=0)*np.exp(-u*75)
  elif layout in ('rename','convert','bytes','pixels'):
   j=round((at+dur*.38)*sr);n=min(int(.075*sr),len(bed)-j);u=np.arange(n)/sr
   if n>0:bed[j:j+n]+=.017*np.diff(rng.normal(0,1,n),prepend=0)*np.exp(-u*80)+.012*np.sin(2*np.pi*1040*u)*np.exp(-u*60)
 bed[:sr//3]*=np.linspace(0,1,sr//3);bed[-sr//2:]*=np.linspace(1,0,sr//2)
 music=work/'foley_bed.wav';sf.write(str(music),bed,sr,subtype='PCM_16')
 final=work/'B1V8_FINAL.mp4'
 cmd(['-f','concat','-safe','0','-i','vcat.txt','-i',narr,'-i',music,'-vf','fps=24','-filter_complex','[1:a][2:a]amix=inputs=2:duration=first:normalize=0,alimiter=limit=.92[a]','-map','0:v:0','-map','[a]','-frames:v',frame_count,'-c:v','libx264','-preset','veryfast','-crf','20','-threads','4','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',final],cwd=work)
 cmd(['-i',final,'-map','0:v','-map','0:a','-f','null','NUL'])
 srt=work/'captions.srt';srt.write_text('\n\n'.join(f'{j+1}\n{stamp(a)} --> {stamp(b)}\n{s}' for j,(a,b,s) in enumerate(cues))+'\n',encoding='utf8')
 thumbnail=work/'thumbnail.jpg';thumb=render(scenes[0],0,2,1,None);thumb.thumbnail((1280,1920));thumb.save(thumbnail,quality=90)
 cols=3;tw,th=stills[0].size;sheet=Image.new('RGB',(cols*tw,math.ceil(len(stills)/cols)*th),BG)
 for j,img in enumerate(stills):sheet.paste(img,(j%cols*tw,j//cols*th))
 sheet.save(work/'contact.jpg',quality=88)
 margin=audio_rms(narr)-audio_rms(music);assert margin>=15
 audit=work/'audio_audit.json';audit.write_text(json.dumps({'scenes':audits,'voice':'af_heart','voice_over_bed_db':round(margin,2),'human_listening':False,'sound_effects':'original synthesized foley-inspired clicks'},indent=2))
 import cv2
 cap=cv2.VideoCapture(str(final));fps=cap.get(cv2.CAP_PROP_FPS);n=cap.get(cv2.CAP_PROP_FRAME_COUNT);dim=(int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)));cap.release()
 assert dim==(W,H) and abs(n/fps-offset)<.15 and abs(fps-24)<.1
 assert all(a>=0 and b>a and b<=offset+.06 for a,b,s in cues) and all(cues[j][1]<=cues[j+1][0]+.001 for j in range(len(cues)-1))
 doc={'key':key,'title':spec['title'],'format':kind,'hook':spec['hook'],'sources':spec['sources'],'duration':round(offset,3),'video':art(final),'captions':art(srt),'thumbnail':art(thumbnail),'audio_audit':art(audit),'proof':art(E/'proof.json'),'caption_cues':len(cues),'voice_over_bed_db':round(margin,2),'full_decode':True,'owner_delegated_review':True,'human_listening':False,'scenes':[{'role':s[0],'layout':s[1],'spoken':s[3],'takeaway':s[4],'start':starts[i],'end':starts[i]+durations[i]} for i,s in enumerate(scenes)]}
 (work/'qa.json').write_text(json.dumps(doc,indent=2,ensure_ascii=False),encoding='utf8');print('FINAL_PASS',key,doc['duration'],doc['video']['sha256'],flush=True)
 return doc
if __name__=='__main__':
 keys=sys.argv[1:] or list(SPECS)
 for key in keys:produce(key,SPECS[key])
 print('RENDER_COMPLETE',flush=True)
