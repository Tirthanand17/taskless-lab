"""Real Python float demonstration in a dedicated console. No external inputs."""
import ctypes,sys,time,os,json
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
 result={}
 for i in range(3):
  os.system("cls")
  print(" PYTHON | ACTUAL EXECUTION",flush=True)
  if i==0:
   v=0.1+0.2;result["float_result"]=repr(v)
   print("\n >>> 0.1 + 0.2\n "+repr(v),flush=True)
   print("\n >>> (0.1 + 0.2) == 0.3\n "+str(v==0.3),flush=True)
  elif i==1:
   v=Fraction.from_float(0.1);result["stored_fraction"]=str(v)
   print("\n >>> Fraction.from_float(0.1)\n "+str(v),flush=True)
   print("\n >>> Fraction(1, 10)\n "+str(Fraction(1,10)),flush=True)
  else:
   v=Decimal("0.1")+Decimal("0.2");result["decimal_result"]=str(v)
   print("\n >>> Decimal('0.1') + Decimal('0.2')\n "+str(v),flush=True)
   print("\n >>> result == Decimal('0.3')\n "+str(v==Decimal("0.3")),flush=True)
  (root/f"ready-{i}").touch()
  deadline=time.monotonic()+35
  while not (root/f"ack-{i}").exists():
   if time.monotonic()>deadline:raise TimeoutError("capture handshake")
   time.sleep(.05)
 (root/"result.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
if __name__=="__main__":main()
