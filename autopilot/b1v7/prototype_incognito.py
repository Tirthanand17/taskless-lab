"""B1v7 proof-first pilot. Isolated Chromium off-the-record context; harmless local file.
No YouTube or user-profile changes. Requires existing local Kokoro and FFmpeg vendor directories.
"""
from pathlib import Path
import base64, json, hashlib, subprocess, tempfile, threading, time, math, sys, urllib.request, html, wave, os
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import websocket
from PIL import Image, ImageDraw, ImageFont, ImageOps
import numpy as np
R=Path(__file__).resolve().parent
B=R.parent/'nov24-b1v6'
sys.path[:0]=[str(B/'kokoro_vendor'),str(R.parent/'nov22-branch1-recovery'/'ffmpeg_vendor')]
import imageio_ffmpeg, soundfile as sf, espeakng_loader
from phonemizer.backend.espeak.wrapper import EspeakWrapper
EspeakWrapper.set_library(espeakng_loader.get_library_path())
from kokoro_onnx import Kokoro
F=imageio_ffmpeg.get_ffmpeg_exe()
P=R/'evidence';P.mkdir(exist_ok=True)
D=P/'downloads';D.mkdir(exist_ok=True)
payload=b'FlowMinute Lab controlled test file. No personal information.\n'
name='private-window-test.txt'
file=D/name
if file.exists():file.unlink() # only our generated sample, never user files
def digest(x):return hashlib.sha256(x).hexdigest()
def cmd(args):
 p=subprocess.run([F,'-hide_banner','-loglevel','error','-y',*map(str,args)],capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr[-1800:])
def page(body):
 return ('<!doctype html><meta charset=utf-8><style>body{background:#f3f5f8;color:#18212c;font:34px Segoe UI,sans-serif;margin:0;padding:52px}small{font-size:25px;color:#48596a;font-weight:600}h1{font-size:60px;line-height:1.02;margin:42px 0 25px}p{line-height:1.4}a{display:block;text-decoration:none;background:#2464d6;color:white;padding:28px;border-radius:15px;font-weight:700;margin:38px 0}code{display:block;background:white;padding:26px;border:2px solid #cbd5df;border-radius:15px;font-size:28px;overflow-wrap:anywhere}.ok{color:#087f5b;font-weight:800;font-size:46px}</style>'+body).encode()
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  if self.path=='/sample':
   self.send_response(200);self.send_header('Content-Type','text/plain');self.send_header('Content-Disposition','attachment; filename="'+name+'"');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload);return
  if self.path=='/proof':
   present=file.is_file() and file.read_bytes()==payload
   data=page('<small>LOCAL TEST RESULT · FILE SYSTEM READ</small><h1>File still exists</h1><p class=ok>'+('VERIFIED' if present else 'NOT FOUND')+'</p><code>'+name+'<br>'+str(file.stat().st_size if present else 0)+' bytes</code><p>'+html.escape(file.read_text() if present else '')+'</p>')
  else:
   data=page('<small>LOCAL TEST PAGE · SAFE SAMPLE</small><h1>Download a test file</h1><p>This file contains no private data.</p><a id="download" href="/sample" onclick="this.textContent=\'Download requested\';this.style.background=\'#087f5b\'">Download sample TXT ↓</a><code>'+name+'</code>')
  self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(data)
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
url='http://127.0.0.1:'+str(server.server_port)
chrome=Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe')
events=[]
with tempfile.TemporaryDirectory(prefix='fm-b1v7-') as profile:
 proc=subprocess.Popen([str(chrome),'--headless=new','--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-extensions','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 ws=None
 try:
  portfile=Path(profile)/'DevToolsActivePort'
  for _ in range(100):
   if portfile.exists():break
   time.sleep(.15)
  port,path=portfile.read_text().splitlines()[:2]
  ws=websocket.create_connection('ws://127.0.0.1:'+port+path,timeout=15,suppress_origin=True)
  seq=0
  def cdp(method,params=None,sid=None):
   global seq
   seq+=1;m={'id':seq,'method':method,'params':params or {}}
   if sid:m['sessionId']=sid
   ws.send(json.dumps(m))
   while True:
    v=json.loads(ws.recv())
    if v.get('id')==seq:
     if 'error' in v:raise RuntimeError(str(v['error']))
     return v.get('result',{})
  def target(ctx=None):
   params={'url':'about:blank'}
   if ctx:params['browserContextId']=ctx
   tid=cdp('Target.createTarget',params)['targetId'];sid=cdp('Target.attachToTarget',{'targetId':tid,'flatten':True})['sessionId']
   cdp('Page.enable',sid=sid);cdp('Emulation.setDeviceMetricsOverride',{'width':900,'height':1050,'deviceScaleFactor':1,'mobile':False},sid)
   return sid
  def nav(sid,link):
   cdp('Page.navigate',{'url':link},sid);time.sleep(1.2)
  def snap(sid,n):
   data=cdp('Page.captureScreenshot',{'format':'png','fromSurface':True},sid)['data'];(P/n).write_bytes(base64.b64decode(data))
  ctx=cdp('Target.createBrowserContext',{'disposeOnDetach':True})['browserContextId']
  cdp('Browser.setDownloadBehavior',{'behavior':'allow','downloadPath':str(D),'browserContextId':ctx})
  sid=target(ctx);nav(sid,url);snap(sid,'01_private_before.png')
  pos=cdp('Runtime.evaluate',{'expression':"(()=>{const r=document.querySelector('#download').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()", 'returnByValue':True},sid)['result']['value']
  for typ in ['mouseMoved','mousePressed','mouseReleased']:
   cdp('Input.dispatchMouseEvent',{'type':typ,'x':pos['x'],'y':pos['y'],**({'button':'left','clickCount':1} if typ!='mouseMoved' else {})},sid)
  for _ in range(80):
   if file.exists() and file.read_bytes()==payload:break
   time.sleep(.15)
  assert file.read_bytes()==payload
  snap(sid,'02_download_requested.png');events.append('actual CDP mouse click; download bytes matched')
  cdp('Target.disposeBrowserContext',{'browserContextId':ctx})
  assert file.exists() and file.read_bytes()==payload
  events.append('off-the-record browser context destroyed; downloaded file still present')
  sid2=target();nav(sid2,url+'/proof');snap(sid2,'03_file_persists.png')
  events.append('new browser context rendered actual filesystem verification')
 finally:
  if ws:ws.close()
  proc.terminate()
  try:proc.wait(timeout=8)
  except subprocess.TimeoutExpired:proc.kill()
server.shutdown()
proof={'test':'isolated Chrome off-the-record browser context','click':pos,'download_sha256':digest(file.read_bytes()),'bytes':file.stat().st_size,'file_persisted_after_context_closed':True,'events':events,'source':'https://support.google.com/chrome/answer/95464','captures':{f.name:digest(f.read_bytes()) for f in P.glob('*.png')}}
(P/'proof.json').write_text(json.dumps(proof,indent=2))
print('REAL_BROWSER_PROOF',json.dumps(proof),flush=True)
# Actual recorded states, not simulated browser UI. Cursor/ring are editorial annotations.
scenes=[
 ('03_file_persists.png','INCOGNITO ≠ DELETE','This file survived.','This file is still here, even after I closed the private browsing session.'),
 ('01_private_before.png','WATCH THE TEST','Private browser session','I opened an isolated private Chrome session and clicked download on this harmless sample.'),
 ('02_download_requested.png','DOWNLOAD COMPLETE','Then I closed the private session.','The file downloaded. Then I closed the entire private session.'),
 ('03_file_persists.png','STILL ON THE DEVICE','Same file. Same contents.','I checked the file again. It is still on disk, with exactly the same contents.'),
 ('03_file_persists.png','DELETE IT YOURSELF','Private browsing does not erase files.','Incognito clears its browsing record when the session ends, not your downloaded files. Delete those separately when you need to.')
]
engine=Kokoro(str(B/'kokoro-v1.0.int8.onnx'),str(B/'voices-v1.0.bin'))
fonts=Path('C:/Windows/Fonts');W,H,FPS=1080,1920,24
def ft(n,b=False):return ImageFont.truetype(str(fonts/('segoeuib.ttf' if b else 'segoeui.ttf')),n)
def center(d,text,y,size,col='#ffffff'):
 d.text((W/2,y),text,font=ft(size,True),fill=col,anchor='mt')
def srt_time(t):
 ms=round(t*1000);s,ms=divmod(ms,1000);m,s=divmod(s,60);h,m=divmod(m,60);return f'{h:02}:{m:02}:{s:02},{ms:03}'
vfiles=[];afiles=[];cues=[];starts=[];offset=0;thumb=None
for i,(capture,headline,callout,spoken) in enumerate(scenes):
 samples,sr=engine.create(spoken,voice='af_heart',speed=1.04,lang='en-us')
 assert sr==24000 and len(samples)>1000
 raw=R/f's{i}.wav';sf.write(str(raw),samples,sr,subtype='PCM_16')
 dur=math.ceil((len(samples)/sr+.25)*FPS)/FPS;frames=round(dur*FPS)
 audio=R/f'a{i}.wav';cmd(['-i',raw,'-af','loudnorm=I=-16:TP=-2:LRA=7,apad','-t',str(dur),'-ar','48000','-ac','1','-c:a','pcm_s16le',audio])
 # Render a distinct layout per semantic beat: result, action, transition, verification, takeaway.
 im=Image.open(P/capture).convert('RGB');im=ImageOps.fit(im,(1000,1166),method=Image.Resampling.LANCZOS)
 bg=Image.new('RGB',(W,H),'#101d2b');draw=ImageDraw.Draw(bg)
 accent='#55e2b2' if i in (0,3,4) else '#8ebaff'
 center(draw,headline,132,72 if i!=4 else 68,accent)
 center(draw,callout,247,46)
 bg.paste(im,(40,365))
 draw.rectangle((40,365,1040,1531),outline=accent,width=5)
 if i==0: center(draw,'REAL DOWNLOAD TEST',1580,42,accent)
 elif i==2:center(draw,'PRIVATE SESSION CLOSED',1580,44,accent)
 elif i==3:center(draw,'FILE HASH MATCHED',1580,48,accent)
 elif i==4:center(draw,'FILES ≠ BROWSING HISTORY',1580,40,accent)
 else:center(draw,'Actual browser capture',1580,40,accent)
 draw.text((540,1748),'FLOWMINUTE LAB  •  CONTROLLED TEST',font=ft(26),anchor='mt',fill='#a2b3c5')
 # Actual cursor location, only annotation moves. No stock / decorative zoom.
 if i==0:thumb=bg.copy()
 v=R/f's{i}.mp4';proc=subprocess.Popen([F,'-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','-','-c:v','libx264','-preset','veryfast','-crf','20','-threads','3','-pix_fmt','yuv420p',str(v)],stdin=subprocess.PIPE)
 for f in range(frames):
  frame=bg.copy();dd=ImageDraw.Draw(frame)
  if i==1:
   tx=40+pos['x']*1000/900;ty=365+pos['y']*1166/1050
   a=min(1,f/(FPS*1.1));x=900+(tx-900)*a;y=1250+(ty-1250)*a
   dd.polygon([(x,y),(x+12,y+52),(x+24,y+33),(x+43,y+31)],fill='white',outline='#1a2330',width=3)
   if a>=1:
    rad=int(28+18*math.sin((f/FPS-1.1)*5)**2);dd.ellipse((tx-rad,ty-rad,tx+rad,ty+rad),outline='#ffb34f',width=7)
  elif i in (0,3,4):
   # Highlight the actual proof field; no fake UI motion.
   y=365+int(345*1166/1050);dd.line((74,y,74+int(910*min(1,f/(FPS*.7))),y),fill=accent,width=7)
  elif i==2:
   # A clear transition annotation, not a fabricated browser action.
   x=int(40+1000*min(1,f/(FPS*1.2)));dd.rectangle((40,1519,x,1531),fill=accent)
  proc.stdin.write(frame.tobytes())
 proc.stdin.close();assert proc.wait()==0
 vfiles.append(v);afiles.append(audio);starts.append(offset);cues.append((offset,offset+len(samples)/sr,spoken));offset+=dur
 print('SCENE_RENDERED',i+1,round(dur,2),flush=True)
def listing(files,dst):dst.write_text('\n'.join("file '"+x.as_posix()+"'" for x in files)+'\n')
listing(vfiles,R/'vcat.txt');listing(afiles,R/'acat.txt')
narr=R/'narration.wav';cmd(['-f','concat','-safe','0','-i',R/'acat.txt','-c:a','pcm_s16le',narr])
sr=48000;t=np.arange(round(offset*sr))/sr;bed=.009*np.sin(2*np.pi*110*t)+.006*np.sin(2*np.pi*165*t)
for at in starts[1:]:
 j=round(at*sr);n=min(round(.14*sr),len(bed)-j);u=np.arange(n)/sr
 bed[j:j+n]+=.025*np.sin(2*np.pi*(620*u+1000*u*u))*np.sin(np.pi*u/.14)**2
bed[:sr//3]*=np.linspace(0,1,sr//3);bed[-sr//2:]*=np.linspace(1,0,sr//2)
sf.write(str(R/'original_bed.wav'),bed,sr,subtype='PCM_16')
out=R/'B1V7_INCOGNITO_PROOF_PILOT_REVIEW.mp4'
cmd(['-f','concat','-safe','0','-i',R/'vcat.txt','-i',narr,'-i',R/'original_bed.wav','-filter_complex','[1:a][2:a]amix=inputs=2:duration=first:normalize=0,alimiter=limit=.92[a]','-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',out])
cmd(['-i',out,'-map','0:v','-map','0:a','-f','null','NUL'])
srt=R/'pilot.srt';srt.write_text('\n\n'.join(f'{i+1}\n{srt_time(a)} --> {srt_time(b)}\n{s}' for i,(a,b,s) in enumerate(cues))+'\n',encoding='utf8')
thumb.save(R/'pilot_thumbnail.png')
report={'duration':offset,'sha256':digest(out.read_bytes()),'caption_sha256':digest(srt.read_bytes()),'proof_sha256':digest((P/'proof.json').read_bytes()),'full_decode':True,'real_browser_test':True,'voice_model':'Kokoro Apache-2.0','human_playback_verified':False,'release':'REVIEW_ONLY','script':[s[3] for s in scenes]}
(R/'pilot_qa.json').write_text(json.dumps(report,indent=2))
print('PILOT_DONE',json.dumps(report),flush=True)
