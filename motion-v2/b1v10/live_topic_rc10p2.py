"""Spec-driven live file-demo runner, restricted to disposable files."""
import ctypes,json,os,sys,time,sqlite3
from itertools import groupby
from pathlib import Path
def main():
 root=Path(sys.argv[1]);title=sys.argv[2];key=sys.argv[3];n=json.loads(Path(sys.argv[4]).read_text())
 if key not in ("shared_lists","outer_join_filter","group_runs"):raise ValueError("Unregistered demo")
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
 if key=="shared_lists":
  d=dict.fromkeys(("a","b"),[])
  page([" PYTHON | LIVE OBJECT TEST",""," >>> d = dict.fromkeys(('a','b'), [])"," >>> d['a'].append('item')"])
 elif key=="group_runs":
  data=["A","B","A"]
  groups=lambda x:[[k,list(v)] for k,v in groupby(x)]
  page([" PYTHON | LIVE GROUP TEST",""," >>> data = ['A','B','A']"," >>> groupby(data)"])
 else:
  db=sqlite3.connect(":memory:")
  db.executescript("CREATE TABLE c(id); INSERT INTO c VALUES(1),(2),(3); CREATE TABLE o(id,status); INSERT INTO o VALUES(1,'paid'),(2,'pending');")
  q=lambda sql:[list(x) for x in db.execute(sql)]
  base="SELECT c.id,o.status FROM c LEFT JOIN o ON c.id=o.id"
  page([" SQL | LIVE JOIN TEST",""," SELECT c.id, o.status"," FROM c LEFT JOIN o ON c.id=o.id"," WHERE o.status='paid';"])
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
 if key=="shared_lists":
  def hook():
   d["a"].append("item");v={k:list(x) for k,x in d.items()}
   page([" PYTHON | LIVE OBJECT TEST",""," >>> d['a'].append('item')"," a: "+str(d["a"])," b: "+str(d["b"]),""," Both keys changed."]);return v
  def demo():
   page([" PYTHON | TWO VALUES",""," >>> d['a']"," "+str(d["a"])," >>> d['b']"," "+str(d["b"]),""," Only key a was modified."]);return [d["a"][:],d["b"][:]]
  def cause():
   v=d["a"] is d["b"];page([" PYTHON | OBJECT IDENTITY",""," >>> d['a'] is d['b']"," "+str(v),""," Same list object."]);return v
  def fix():
   nonlocal d
   d={k:[] for k in ("a","b")};page([" PYTHON | SEPARATE OBJECTS",""," >>> d = {k: [] for k in ('a','b')}"," a: "+str(d["a"])," b: "+str(d["b"]),""," New list for each key."]);return d["a"] is not d["b"]
  def payoff():
   d["a"].append("item");v={k:list(x) for k,x in d.items()};page([" PYTHON | VERIFIED RESULT",""," >>> d['a'].append('item')"," a: "+str(d["a"])," b: "+str(d["b"]),""," Only a changed."]);return v
  def takeaway():
   v=d["a"] is d["b"];print("\n >>> d['a'] is d['b']\n "+str(v),flush=True);return v
 elif key=="group_runs":
  def hook():
   v=groups(data);page([" PYTHON | LIVE GROUP TEST",""," Input: "+str(data)," Groups:"]+[str(x) for x in v]+[""," Count: "+str(len(v))]);return v
  def demo():
   page([" PYTHON | ORIGINAL ORDER",""," "+str(data)," First equals last: "+str(data[0]==data[-1]),""," Same value, separate runs."]);return data
  def cause():
   v=groups(data);page([" PYTHON | CONSECUTIVE GROUPS",""," Run 1: "+str(v[0])," Run 2: "+str(v[1])," Run 3: "+str(v[2])]);return len(v)
  def fix():
   v=sorted(data);page([" PYTHON | SORT FIRST",""," >>> sorted(data)"," "+str(v),""," Equal values are now adjacent."]);return v
  def payoff():
   v=groups(sorted(data));page([" PYTHON | VERIFIED RESULT",""," Groups after sorting:"]+[str(x) for x in v]+[""," Count: "+str(len(v))]);return v
  def takeaway():
   print("\n Original: "+str(data)+"\n Sorted: "+str(sorted(data)),flush=True);return data!=sorted(data)
 else:
  def hook():
   v=q(base+" WHERE o.status='paid' ORDER BY c.id");page([" SQL | LIVE JOIN TEST",""," LEFT JOIN ..."," WHERE o.status='paid'",""," Result: "+str(v),""," Only one customer returned."]);return v
  def demo():
   c=q("SELECT * FROM c");o=q("SELECT * FROM o");page([" SQL | SOURCE TABLES",""," Customers: "+str(c)," Orders:"]+[str(x) for x in o]);return [c,o]
  def cause():
   v=q(base+" ORDER BY c.id");page([" SQL | BEFORE WHERE FILTER",""," All joined rows:"]+[str(x) for x in v]+[""," WHERE excludes pending and NULL."]);return v
  def fix():
   v=q(base+" AND o.status='paid' ORDER BY c.id");page([" SQL | CORRECTED JOIN",""," SELECT c.id, o.status"," FROM c LEFT JOIN o"," ON c.id=o.id AND o.status='paid'",""," Rows: "+str(len(v))]);return v
  def payoff():
   v=q(base+" AND o.status='paid' ORDER BY c.id");assert v==[[1,"paid"],[2,None],[3,None]];page([" SQL | VERIFIED RESULT",""," All customers:"]+[str(x) for x in v]+[""," None represents SQL NULL."]);return v
  def takeaway():
   a=q(base+" WHERE o.status='paid'");b=q(base+" AND o.status='paid'");page([" SQL | CHOOSE YOUR GOAL",""," WHERE: "+str(len(a))+" customer"," ON: "+str(len(b))+" customers",""," Different questions, different results."]);return [len(a),len(b)]
 event("hook",.4,hook);event("demonstration",2.0,demo);event("cause",t[2]+.15,cause);event("fix",t[3]+.15,fix);event("payoff",t[4]+.15,payoff);event("takeaway",t[5]+.15,takeaway)
 (root/"events.json").write_text(json.dumps(events,indent=2),encoding="utf8")
 wait(n["duration_seconds"]+3)
if __name__=="__main__":main()
