"""Record only a dedicated live console window; never capture the full desktop."""
from __future__ import annotations
import argparse, ctypes, hashlib, json, subprocess, sys, time, uuid
from pathlib import Path
from PIL import ImageGrab, Image
import numpy as np
import cv2

D=Path(__file__).resolve().parent
def need(ok,msg):
    if not ok:raise ValueError(msg)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--out",type=Path,required=True);p.add_argument("--ffmpeg",required=True);a=p.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    title="FlowMinuteCapture-"+uuid.uuid4().hex
    proc=subprocess.Popen([str(Path("C:/Windows/System32/conhost.exe")),sys.executable,str(D/"sha256_console_demo.py"),str(out),title],cwd=out,creationflags=subprocess.CREATE_NEW_CONSOLE)
    writer=None
    try:
        user=ctypes.windll.user32
        user.FindWindowW.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p];user.FindWindowW.restype=ctypes.c_void_p
        deadline=time.monotonic()+15;hwnd=0
        while time.monotonic()<deadline:
            hwnd=user.FindWindowW("ConsoleWindowClass",title)
            if hwnd and (out/"ready").exists():break
            time.sleep(.15)
        need(hwnd and (out/"ready").exists(),"dedicated classic console unavailable")
        frame=ImageGrab.grab(window=hwnd).convert("RGB")
        # Verify nonblank window image. No fallback to desktop capture.
        need(np.asarray(frame).std()>10,"blank window capture")
        w,h=frame.size;w-=w%2;h-=h%2
        need(w>=400 and h>=250,"capture too small")
        video=out/"ACTUAL_SHA256_CONSOLE.mp4"
        writer=subprocess.Popen([a.ffmpeg,"-nostdin","-v","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{w}x{h}","-r","12","-i","-","-an","-c:v","libx264","-preset","ultrafast","-crf","18","-threads","1","-pix_fmt","yuv420p",str(video)],stdin=subprocess.PIPE)
        (out/"go").touch();start=time.monotonic();samples=[]
        for i in range(120):
            deadline=start+i/12
            if deadline>time.monotonic():time.sleep(deadline-time.monotonic())
            need(user.FindWindowW("ConsoleWindowClass",title)==hwnd,"capture window identity changed")
            im=ImageGrab.grab(window=hwnd).convert("RGB").crop((0,0,w,h))
            need(im.size==(w,h),"capture dimensions changed")
            writer.stdin.write(im.tobytes())
            if i in (0,35,65,95,119):
                im.save(out/f"capture-{i:03}.png");samples.append(i)
        writer.stdin.close();need(writer.wait(timeout=30)==0,"capture encode failed");writer=None
        need((out/"actual_result.json").exists(),"execution did not finish during capture")
        result=json.loads((out/"actual_result.json").read_text())
        need(result["sha256_a"]==hashlib.sha256(b"A").hexdigest() and result["sha256_b"]==hashlib.sha256(b"B").hexdigest() and result["equal"] is False,"incorrect real computation")
        subprocess.run([a.ffmpeg,"-nostdin","-v","error","-xerror","-i",str(video),"-f","null","-"],check=True)
        cap=cv2.VideoCapture(str(video));n=0;last=None;changes=0
        while True:
            ok,f=cap.read()
            if not ok:break
            gray=cv2.resize(cv2.cvtColor(f,cv2.COLOR_BGR2GRAY),(160,120))
            if last is not None and float(np.mean(cv2.absdiff(gray,last)))>.8:changes+=1
            last=gray;n+=1
        cap.release();need(n==120 and changes>=2,"capture missing live state changes")
        report={"version":"1.0.0-rc2","capture_method":"windows_classic_console_window_only_live","capture_sha256":sha(video),"dimensions":[w,h],"fps":12,"decoded_frames":n,"observed_state_changes":changes,"actual_result":result,"fixture_sha256":{x:sha(out/x) for x in ("A.bin","B.bin")},"source_sha256":sha(D/"sha256_console_demo.py"),"private_data":False,"release_authorized":False,"legacy_xvfb_receipt_compatible":False,"inspection_frames":samples}
        (out/"CAPTURE_QA.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");print(json.dumps(report,indent=2),flush=True)
    finally:
        if writer is not None:
            writer.kill();writer.wait()
        if proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill()
if __name__=="__main__":main()
