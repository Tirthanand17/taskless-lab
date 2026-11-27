"""Capture three actual Python result screens, restricted to the dedicated HWND."""
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
 out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);title="FlowMinuteFloat-"+uuid.uuid4().hex
 proc=subprocess.Popen(["C:/Windows/System32/conhost.exe",sys.executable,str(D/"float_console_demo.py"),str(out),title],cwd=out,creationflags=subprocess.CREATE_NEW_CONSOLE)
 writer=None
 try:
  user=ctypes.windll.user32;user.FindWindowW.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p];user.FindWindowW.restype=ctypes.c_void_p
  def wait(i):
   deadline=time.monotonic()+25
   while time.monotonic()<deadline:
    h=user.FindWindowW("ConsoleWindowClass",title)
    if h and (out/f"ready-{i}").exists():return h
    time.sleep(.1)
   raise TimeoutError("page unavailable")
  h=wait(0);im=ImageGrab.grab(window=h).convert("RGB");w,z=im.size;w-=w%2;z-=z%2
  need(w>=750 and z>=350,"capture dimensions")
  video=out/"FLOAT_CAPTURE.mp4"
  writer=subprocess.Popen([a.ffmpeg,"-nostdin","-v","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{w}x{z}","-r","12","-i","-","-an","-c:v","libx264","-preset","ultrafast","-crf","18","-threads","1","-pix_fmt","yuv420p",str(video)],stdin=subprocess.PIPE)
  for i in range(3):
   need(wait(i)==h,"window changed");time.sleep(.15);start=time.monotonic()
   for j in range(24):
    delay=start+j/12-time.monotonic()
    if delay>0:time.sleep(delay)
    need(user.FindWindowW("ConsoleWindowClass",title)==h,"window changed")
    im=ImageGrab.grab(window=h).convert("RGB").crop((0,0,w,z))
    need(np.asarray(im).std()>10,"blank screen");writer.stdin.write(im.tobytes())
    if j==12:im.save(out/f"page-{i}.png")
   (out/f"ack-{i}").touch()
  writer.stdin.close();need(writer.wait(timeout=30)==0,"encode");writer=None
  need(proc.wait(timeout=15)==0,"demo failed")
  result=json.loads((out/"result.json").read_text())
  need(result=={"float_result":"0.30000000000000004","stored_fraction":"3602879701896397/36028797018963968","decimal_result":"0.3"},"wrong result")
  subprocess.run([a.ffmpeg,"-nostdin","-v","error","-xerror","-i",str(video),"-f","null","-"],check=True)
  c=cv2.VideoCapture(str(video));n=0;refs=[]
  while True:
   ok,f=c.read()
   if not ok:break
   if n%24==12:refs.append(cv2.resize(cv2.cvtColor(f,cv2.COLOR_BGR2GRAY),(160,100)))
   n+=1
  c.release();need(n==72 and len(refs)==3,"capture frames")
  deltas=[float(np.mean(cv2.absdiff(x,y))) for x,y in zip(refs,refs[1:])]
  need(min(deltas)>.5,"missing changes")
  report={"version":"1.0.0-rc5","method":"windows_classic_console_window_only_live","dimensions":[w,z],"fps":12,"frames":n,"result":result,"capture_sha256":sha(video),"page_deltas":deltas,"source_sha256":{k:sha(D/k) for k in ("float_console_demo.py","capture_float.py")},"release_authorized":False,"legacy_xvfb_receipt_compatible":False}
  (out/"FLOAT_CAPTURE_QA.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");print(json.dumps(report,indent=2))
 finally:
  if writer is not None:writer.kill();writer.wait()
  if proc.poll() is None:proc.terminate()
if __name__=="__main__":main()
