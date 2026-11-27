"""Continuous window-only capture at 6fps; record actual capture times and content changes."""
import argparse,ctypes,hashlib,json,subprocess,sys,time,uuid
from pathlib import Path
import cv2,numpy as np
from PIL import ImageGrab,ImageStat
D=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,msg):
 if not ok:raise ValueError(msg)
def main():
 p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);p.add_argument("--topic",choices=["zip_crc","sql_null"],required=True);p.add_argument("--narration",type=Path,required=True);p.add_argument("--ffmpeg",required=True);a=p.parse_args()
 narr=json.loads(a.narration.read_text());need(narr["asr_screen_pass"] is True and narr["release_authorized"] is False,"narration review hold");count=__import__("math").ceil(narr["duration_seconds"]*6);out=a.out.absolute();out.mkdir(parents=True,exist_ok=False);title="FlowMinuteLive-"+uuid.uuid4().hex
 proc=subprocess.Popen(["C:/Windows/System32/conhost.exe",sys.executable,str(D/"live_topic_demo_rc9p3.py"),str(out),title,a.topic,str(a.narration.absolute())],cwd=out,creationflags=subprocess.CREATE_NEW_CONSOLE)
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
  video=out/"DAILY_LIVE_CAPTURE.mp4"
  writer=subprocess.Popen([a.ffmpeg,"-nostdin","-v","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{w}x{z}","-r","6","-i","-","-an","-c:v","libx264","-preset","ultrafast","-crf","18","-threads","1","-pix_fmt","yuv420p",str(video)],stdin=subprocess.PIPE)
  # Start the recording before the actual calculation. No cuts or per-page handshakes.
  start=time.monotonic();(out/"go").touch();times=[];blank=[];consecutive_blank=0;retries=[]
  for i in range(count):
   delay=start+i/6-time.monotonic()
   if delay>0:time.sleep(delay)
   need(user.FindWindowW("ConsoleWindowClass",title)==h,"window changed")
   for attempt in range(4):
    try:
     im=ImageGrab.grab(window=h).convert("RGB");break
    except OSError:
     retries.append({"frame":i,"attempt":attempt+1})
     need(attempt<3,"window grab repeatedly failed")
     time.sleep(.025)
   need(im.size[0]//2*2==w and im.size[1]//2*2==z,"window resized")
   im=im.crop((0,0,w,z))
   times.append(round(time.monotonic()-start,5))
   if max(ImageStat.Stat(im.resize((160,90))).stddev)<=10:
    blank.append(i);consecutive_blank+=1
   else:consecutive_blank=0
   need(consecutive_blank<=3 and len(blank)<=20,"sustained blank screen")
   writer.stdin.write(im.tobytes())
   if i and i%120==0:print("Captured seconds:",i/6,flush=True)

  writer.stdin.close();need(writer.wait(timeout=30)==0,"encode failed");writer=None
  events=json.loads((out/"events.json").read_text())
  values=[e["result"] for e in events]
  expected={"zip_crc":[["note.txt"],"note.txt",True,"testzip",["note.txt",None],"not authenticity"],"sql_null":[[],[[[1],[2],[3],[4]],[[2],[None]]],[[1,None],[2,0],[3,None],[4,None]],[[1],[3],[4]],[[[1],[3],[4]],[[1],[3],[4]]],[[[None],[1],[3],[4]],[[1],[3],[4]]]]}
  need(values==expected[a.topic],"actual fixture results differ")
  subprocess.run([a.ffmpeg,"-nostdin","-v","error","-xerror","-i",str(video),"-f","null","-"],check=True)
  c=cv2.VideoCapture(str(video));n=0;last=None;changes=[]
  while True:
   ok,f=c.read()
   if not ok:break
   gray=cv2.resize(cv2.cvtColor(f[:350,:],cv2.COLOR_BGR2GRAY),(180,90))
   if last is not None:
    delta=float(np.mean(cv2.absdiff(gray,last)))
    if delta>.65:changes.append({"frame":n,"seconds":n/6,"delta":round(delta,4)})
   last=gray;n+=1
  c.release()
  need(n==count and len(changes)>=6 and changes[0]["seconds"]<=2 and any(1.5<=v["seconds"]<=3 for v in changes),"missing opening live changes")
  lag=max(abs(t-i/6) for i,t in enumerate(times));(out/"TIMING_DIAGNOSTICS.json").write_text(json.dumps({"times":times,"max_sample_lag_seconds":lag,"blank":blank,"retries":retries},indent=2),encoding="utf-8");print("Maximum sample lag",lag,flush=True);need(lag<.35,"capture timing drift")
  report={"version":"1.0.0-rc8","method":"windows_classic_console_window_only_live","continuous":True,"scripted_demo":True,"dimensions":[w,z],"fps":6,"frames":n,"capture_sha256":sha(video),"events":events,"narration_report_sha256":sha(a.narration),"topic":a.topic,"changes":changes,"capture_times_seconds":times,"transient_blank_frames":blank,"grab_retries":retries,"max_sample_lag_seconds":round(lag,5),"source_sha256":{k:sha(D/k) for k in ("live_topic_demo_rc9p3.py","capture_daily_rc9p3.py")},"release_authorized":False}
  import shutil
  for name in report["source_sha256"]:shutil.copyfile(D/name,out/name)
  (out/"LIVE_CAPTURE_QA.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
  print(json.dumps({k:v for k,v in report.items() if k!="capture_times_seconds"},indent=2))
 finally:
  if writer is not None:writer.kill();writer.wait()
  if proc.poll() is None:proc.terminate()
if __name__=="__main__":main()
