"""Capture eight live console pages with a per-page handshake. No desktop fallback."""
import argparse,ctypes,hashlib,json,subprocess,sys,time,uuid
from pathlib import Path
from PIL import ImageGrab
import numpy as np,cv2
D=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,msg):
    if not ok:raise ValueError(msg)
def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);p.add_argument("--repo",type=Path,required=True);p.add_argument("--evidence",type=Path,required=True);p.add_argument("--ffmpeg",required=True);a=p.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    evidence=json.loads(a.evidence.read_text(encoding="utf-8"))
    title="FlowMinuteGit-"+uuid.uuid4().hex
    proc=subprocess.Popen(["C:/Windows/System32/conhost.exe",sys.executable,str(D/"git_console_demo.py"),str(out),title,str(a.repo.resolve()),str(a.evidence.resolve())],cwd=out,creationflags=subprocess.CREATE_NEW_CONSOLE)
    writer=None
    try:
        user=ctypes.windll.user32;user.FindWindowW.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p];user.FindWindowW.restype=ctypes.c_void_p
        def await_page(i):
            deadline=time.monotonic()+35
            while time.monotonic()<deadline:
                hwnd=user.FindWindowW("ConsoleWindowClass",title)
                if hwnd and (out/f"ready-{i}").exists():return hwnd
                time.sleep(.1)
            raise TimeoutError("page "+str(i))
        hwnd=await_page(0)
        im=ImageGrab.grab(window=hwnd).convert("RGB");w,h=im.size;w-=w%2;h-=h%2
        need(w>=750 and h>=350 and np.asarray(im).std()>10,"bad console")
        video=out/"ACTUAL_GIT_CONSOLE.mp4"
        writer=subprocess.Popen([a.ffmpeg,"-nostdin","-v","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{w}x{h}","-r","12","-i","-","-an","-c:v","libx264","-preset","ultrafast","-crf","18","-threads","1","-pix_fmt","yuv420p",str(video)],stdin=subprocess.PIPE)
        pages=[]
        for i in range(8):
            need(await_page(i)==hwnd,"window changed")
            time.sleep(.15);start=time.monotonic()
            for j in range(24):
                delay=start+j/12-time.monotonic()
                if delay>0:time.sleep(delay)
                need(user.FindWindowW("ConsoleWindowClass",title)==hwnd,"window changed")
                img=ImageGrab.grab(window=hwnd).convert("RGB").crop((0,0,w,h))
                need(img.size==(w,h) and np.asarray(img).std()>10,"invalid frame")
                writer.stdin.write(img.tobytes())
                if j==12:img.save(out/f"page-{i}.png")
            pages.append({"page":i,"start_frame":i*24,"end_frame":(i+1)*24,"sample_sha256":sha(out/f"page-{i}.png")})
            (out/f"ack-{i}").touch()
        writer.stdin.close();need(writer.wait(timeout=30)==0,"encode failed");writer=None
        result=json.loads((out/"actual_git_result.json").read_text())
        need(result["commits"]==evidence["commits"] and result["first_bad_commit"]==evidence["first_bad_commit"] and result["reset_completed"],"wrong actual result")
        subprocess.run([a.ffmpeg,"-nostdin","-v","error","-xerror","-i",str(video),"-f","null","-"],check=True)
        cap=cv2.VideoCapture(str(video));n=0;stills=[]
        while True:
            ok,f=cap.read()
            if not ok:break
            if n%24==12:stills.append(cv2.resize(cv2.cvtColor(f,cv2.COLOR_BGR2GRAY),(160,100)))
            n+=1
        cap.release();need(n==192 and len(stills)==8,"frame count")
        deltas=[float(np.mean(cv2.absdiff(x,y))) for x,y in zip(stills,stills[1:])]
        need(min(deltas)>.5,"missing distinct pages")
        report={"version":"1.0.0-rc3","capture_method":"windows_classic_console_window_only_live","dimensions":[w,h],"fps":12,"decoded_frames":n,"capture_sha256":sha(video),"original_git_evidence_sha256":sha(a.evidence),"actual_git_result":result,"pages":pages,"page_deltas":deltas,"source_sha256":{k:sha(D/k) for k in ("git_console_demo.py","capture_git_console.py")},"release_authorized":False,"legacy_xvfb_receipt_compatible":False}
        (out/"GIT_CAPTURE_QA.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");print(json.dumps({k:v for k,v in report.items() if k!="actual_git_result"},indent=2))
    finally:
        if writer is not None:writer.kill();writer.wait()
        if proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill()
if __name__=="__main__":main()
