"""Run a scripted, timed demonstration of real Python expressions, in one console."""
import ctypes,json,os,sys,time
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
def main():
 root=Path(sys.argv[1]);title=sys.argv[2]
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
 def page():os.system("cls");print(" PYTHON | LIVE EXECUTION",flush=True)
 page();print("\n >>> 0.1 + 0.2",flush=True)
 (root/"ready").touch()
 deadline=time.monotonic()+30
 while not (root/"go").exists():
  if time.monotonic()>deadline:raise TimeoutError("capture handshake")
  time.sleep(.01)
 start=time.monotonic();events=[]
 def wait(t):
  while time.monotonic()-start<t:time.sleep(.005)
 def event(label,t,fn):
  wait(t);result=fn();events.append({"id":label,"planned_seconds":t,"actual_seconds":round(time.monotonic()-start,4),"result":result})
 def result(expr,show=True):
  if show:print("\n >>> "+expr,flush=True)
  value=eval(expr,{"__builtins__":{},"Decimal":Decimal,"Fraction":Fraction})
  print(" "+str(value),flush=True);return str(value)
 event("sum",.55,lambda:result("0.1 + 0.2",False))
 event("equality",1.8,lambda:result("(0.1 + 0.2) == 0.3"))
 def fraction():
  page();return result("Fraction.from_float(0.1)")
 event("fraction",8.6,fraction)
 event("target",11.4,lambda:result("Fraction(1, 10)"))
 def fix():
  page();print("\n >>> Decimal('0.1') + Decimal('0.2')",flush=True)
  return "command shown"
 event("fix_command",15.73,fix)
 event("decimal",16.65,lambda:result("Decimal('0.1') + Decimal('0.2')",False))
 event("verify",18.8,lambda:result("(Decimal('0.1') + Decimal('0.2')) == Decimal('0.3')"))
 # Long command can wrap naturally in the dedicated console.
 (root/"events.json").write_text(json.dumps(events,indent=2),encoding="utf-8")
 wait(25)
if __name__=="__main__":main()
