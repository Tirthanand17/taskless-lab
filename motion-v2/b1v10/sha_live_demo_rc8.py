"""Continuous first-party SHA-256 demonstration, using only generated one-byte files."""
import ctypes,hashlib,json,os,sys,time
from pathlib import Path
def main():
 root=Path(sys.argv[1]);title=sys.argv[2];k=ctypes.windll.kernel32
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
 a=root/"A.bin";b=root/"B.bin";a.write_bytes(b"A");b.write_bytes(b"B")
 def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
 trusted=digest(a)
 def page():os.system("cls");print(" SHA-256 | LIVE EXECUTION",flush=True)
 page();print("\n >>> SHA-256: A.bin vs B.bin",flush=True)
 (root/"ready").touch()
 deadline=time.monotonic()+30
 while not (root/"go").exists():
  if time.monotonic()>deadline:raise TimeoutError("capture handshake")
  time.sleep(.01)
 start=time.monotonic();events=[]
 def wait(t):
  while time.monotonic()-start<t:time.sleep(.005)
 def event(label,t,fn):
  wait(t);v=fn();events.append({"id":label,"planned_seconds":t,"actual_seconds":round(time.monotonic()-start,4),"result":v})
 def show(v):print(v,flush=True);return v
 def preview():
  x,y=digest(a),digest(b);print(" A: "+x[:24]+"\n B: "+y[:24]+"\n First 24 hex digits",flush=True);return [x,y]
 def input_a():page();return show(" A.bin = "+repr(a.read_bytes()))
 def input_b():return show("\n B.bin = "+repr(b.read_bytes()))
 def hashes():
  page();x,y=digest(a),digest(b)
  for key,v in (("A",x),("B",y)):print(" "+key+": "+v[:32]+"\n    "+v[32:],flush=True)
  return [x,y]
 def reference():
  page();print(" Trusted original SHA-256:\n "+trusted[:32]+"\n "+trusted[32:],flush=True);return trusted
 def matches():
  v=[digest(a)==trusted,digest(b)==trusted]
  print("\n A matches: "+str(v[0])+"\n B matches: "+str(v[1]),flush=True);return v
 event("preview",.55,preview)
 event("read_a",1.85,input_a)
 event("read_b",4.5,input_b)
 event("hashes",7.8,hashes)
 event("trusted_reference",12.8,reference)
 event("comparison",14.45,matches)
 event("rule",17.1,lambda:show("\n Integrity is not proof of safety."))
 (root/"events.json").write_text(json.dumps(events,indent=2),encoding="utf-8")
 wait(22)
if __name__=="__main__":main()

