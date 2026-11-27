"""Spec-driven live file-demo runner, restricted to disposable files."""
import ctypes,hashlib,json,os,sys,time
from pathlib import Path
def main():
 root=Path(sys.argv[1]);title=sys.argv[2];key=sys.argv[3];n=json.loads(Path(sys.argv[4]).read_text())
 if key!="path_suffix":raise ValueError("Only tested demo registered")
 k=ctypes.windll.kernel32
 if not k.SetConsoleTitleW(title):raise RuntimeError("console unavailable")
 class COORD(ctypes.Structure):
  _fields_=[("X",ctypes.c_short),("Y",ctypes.c_short)]
 class FONT(ctypes.Structure):
  _fields_=[("cbSize",ctypes.c_ulong),("nFont",ctypes.c_ulong),("dwFontSize",COORD),("FontFamily",ctypes.c_uint),("FontWeight",ctypes.c_uint),("FaceName",ctypes.c_wchar*32)]
 k.GetStdHandle.restype=ctypes.c_void_p
 info=FONT();info.cbSize=ctypes.sizeof(FONT);info.dwFontSize=COORD(0,26);info.FontFamily=54;info.FontWeight=400;info.FaceName="Consolas"
 k.SetCurrentConsoleFontEx.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.POINTER(FONT)]
 if not k.SetCurrentConsoleFontEx(k.GetStdHandle(-11),False,ctypes.byref(info)):raise RuntimeError("font failed")
 os.system("mode con: cols=58 lines=15 >nul")
 fixture=root/"fixture";fixture.mkdir();original=fixture/"report.csv";original.write_bytes(b"number\n42\n")
 digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 before=digest(original);new=None
 def page():os.system("cls");print(" PYTHON | LIVE FILE TEST\n",flush=True)
 page();print(" >>> path = Path('report.csv')\n >>> path.with_suffix('.txt')",flush=True)
 (root/"ready").touch();deadline=time.monotonic()+30
 while not (root/"go").exists():
  if time.monotonic()>deadline:raise TimeoutError("capture handshake")
  time.sleep(.01)
 start=time.monotonic();events=[]
 def wait(t):
  while time.monotonic()-start<t:time.sleep(.005)
 def event(id,t,fn):
  wait(t);v=fn();events.append({"id":id,"planned_seconds":t,"actual_seconds":round(time.monotonic()-start,4),"result":v})
 def suffix():
  nonlocal new
  new=original.with_suffix(".txt");page();print(" >>> path.with_suffix('.txt')\n "+new.name+"\n\n Returned path only.\n Original on disk: "+original.name,flush=True);return new.name
 def exists():
  print("\n >>> path.exists(), new.exists()\n "+str((original.exists(),new.exists())),flush=True);return [original.exists(),new.exists()]
 def cause():
  page();print(" >>> path.exists()\n "+str(original.exists())+"\n\n >>> new.exists()\n "+str(new.exists()),flush=True);return [original.exists(),new.exists()]
 def rename():
  page();assert not new.exists();print(" >>> assert not new.exists()\n >>> path.rename(new)",flush=True);original.rename(new);print(" Renamed "+new.name,flush=True);return new.name
 def payoff():
  page();v=[original.exists(),new.exists(),digest(new)==before];print(" >>> path.exists(), new.exists()\n "+str(tuple(v[:2]))+"\n\n >>> sha256_before == sha256_after\n "+str(v[2]),flush=True);return v
 def takeaway():
  print("\n >>> new.read_text()\n "+repr(new.read_text()),flush=True);return new.read_text()
 t=[s["start_frame"]/30 for s in n["scene_timeline"]]
 event("suffix",.4,suffix);event("exists",1.8,exists);event("cause",t[2]+.15,cause);event("rename",t[3]+.15,rename);event("payoff",t[4]+.15,payoff);event("takeaway",t[5]+.15,takeaway)
 (root/"events.json").write_text(json.dumps(events,indent=2),encoding="utf8")
 wait(n["duration_seconds"]+3)
if __name__=="__main__":main()
