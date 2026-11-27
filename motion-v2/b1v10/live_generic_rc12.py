"""Spec-driven live file-demo runner, restricted to disposable files."""
import ctypes,json,os,sys,time,sqlite3
from select_topics_rc12 import steps,ROLES,load
from pathlib import Path
def main():
 root=Path(sys.argv[1]);title=sys.argv[2];topic=load(Path(sys.argv[3]));n=json.loads(Path(sys.argv[4]).read_text())

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
 def page(lines):
  os.system("cls");print("\n".join(lines),flush=True)
 page([" FLOWMINUTE | LOCAL TEST",""," Input: "+repr(topic["input"]),""," Running actual experiment..."])
 (root/"ready").touch();deadline=time.monotonic()+30
 while not (root/"go").exists():
  if time.monotonic()>deadline:raise TimeoutError("capture handshake")
  time.sleep(.01)
 start=time.monotonic();events=[]
 def wait(t):
  while time.monotonic()-start<t:time.sleep(.005)
 def event(id,t,fn):
  wait(t);v=fn();events.append({"id":id,"planned_seconds":t,"actual_seconds":round(time.monotonic()-start,4),"result":v})
 t=[s["start_frame"]/30 for s in n["scene_timeline"]]
 def action(i):
  r=steps(topic)[i]
  page([" FLOWMINUTE | "+ROLES[i].upper(),"", " "+r["command"],"", " Result:", " "+repr(r["result"]),"", " "+topic["head"][i]])
  return r["result"]
 for i,role in enumerate(ROLES):
  event(role,.4 if i==0 else 2.0 if i==1 else t[i]+.15,lambda i=i:action(i))
 (root/"events.json").write_text(json.dumps(events,indent=2),encoding="utf8")
 wait(n["duration_seconds"]+3)
if __name__=="__main__":main()
