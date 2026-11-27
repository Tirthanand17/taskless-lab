"""Continuous window-only capture at 10fps; record actual capture times and content changes."""
import argparse,ctypes,hashlib,json,subprocess,sys,time,uuid
from pathlib import Path
import cv2,numpy as np
from PIL import ImageGrab
D=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,msg):
 if not ok:raise ValueError(msg)
def main():
 p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);p.add_argument("--ffmpeg",required=True);a=p.parse_args()
 out=a.out.absolute();out.mkdir(parents=True,exist_ok=False);title="FlowMinuteLive-"+uuid.uuid4().hex
 proc=subprocess.Popen(["C:/Windows/System32/conhost.exe",sys.executable,str(D/"sha_live_demo_rc8.py"),str(out),title],cwd=out,creationflags=subprocess.CREATE_NEW_CONSOLE)
 writer=None
 try:
  user=ctypes.windll.user32;user.FindWindowW.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p];user.FindWindowW.restype=ctypes.c_void_p
  deadline=time.monotonic()+25;h=0
  while time.monotonic()<deadline:
   h=user.FindWindowW("ConsoleWindowClass",title)
   if h and (out/"ready").exists():break
   time.sleep(.1)
  need(h and (out/"ready").exists(),"no dedicated console")
  im=ImageGrab.grab(window=h).convert("RGB");w,z=im.size;w-=w%2;z-=z%2
  need(w>=750 and z>=350 and np.asarray(im).std()>10,"bad window")
  video=out/"SHA_LIVE_CAPTURE.mp4"
  writer=subprocess.Popen([a.ffmpeg,"-nostdin","-v","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{w}x{z}","-r","10","-i","-","-an","-c:v","libx264","-preset","ultrafast","-crf","18","-threads","1","-pix_fmt","yuv420p",str(video)],stdin=subprocess.PIPE)
  # Start the recording before the actual calculation. No cuts or per-page handshakes.
  start=time.monotonic();(out/"go").touch();times=[]
  for i in range(194):
   delay=start+i/10-time.monotonic()
   if delay>0:time.sleep(delay)
   need(user.FindWindowW("ConsoleWindowClass",title)==h,"window changed")
   im=ImageGrab.grab(window=h).convert("RGB").crop((0,0,w,z))
   times.append(round(time.monotonic()-start,5))
   need(im.size==(w,z) and np.asarray(im).std()>10,"blank or resized screen")
   writer.stdin.write(im.tobytes())

  writer.stdin.close();need(writer.wait(timeout=30)==0,"encode failed");writer=None
  events=json.loads((out/"events.json").read_text())
  a_hash=hashlib.sha256(b"A").hexdigest();b_hash=hashlib.sha256(b"B").hexdigest()
  expected=[[a_hash,b_hash]," A.bin = b'A'","\n B.bin = b'B'",[a_hash,b_hash],a_hash,[True,False],"\n Integrity is not proof of safety."]
  need([e["result"] for e in events]==expected,"wrong result")
  subprocess.run([a.ffmpeg,"-nostdin","-v","error","-xerror","-i",str(video),"-f","null","-"],check=True)
  c=cv2.VideoCapture(str(video));n=0;last=None;changes=[]
  while True:
   ok,f=c.read()
   if not ok:break
   gray=cv2.resize(cv2.cvtColor(f[:350,:],cv2.COLOR_BGR2GRAY),(180,90))
   if last is not None:
    delta=float(np.mean(cv2.absdiff(gray,last)))
    if delta>.65:changes.append({"frame":n,"seconds":n/10,"delta":round(delta,4)})
   last=gray;n+=1
  c.release()
  need(n==194 and len(changes)>=6 and changes[0]["seconds"]<=1.5 and any(1.5<=v["seconds"]<=3 for v in changes),"missing opening live changes")
  lag=max(abs(t-i/10) for i,t in enumerate(times));print("Maximum sample lag",lag,flush=True);need(lag<.35,"capture timing drift")
  report={"version":"1.0.0-rc8","method":"windows_classic_console_window_only_live","continuous":True,"scripted_demo":True,"dimensions":[w,z],"fps":10,"frames":n,"capture_sha256":sha(video),"events":events,"changes":changes,"capture_times_seconds":times,"max_sample_lag_seconds":round(lag,5),"source_sha256":{k:sha(D/k) for k in ("sha_live_demo_rc8.py","capture_live_sha_rc8.py")},"release_authorized":False}
  (out/"LIVE_CAPTURE_QA.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
  print(json.dumps({k:v for k,v in report.items() if k!="capture_times_seconds"},indent=2))
 finally:
  if writer is not None:writer.kill();writer.wait()
  if proc.poll() is None:proc.terminate()
if __name__=="__main__":main()
