"""Spec-driven live file-demo runner, restricted to disposable files."""
import ctypes,hashlib,json,os,sys,time,zipfile,zlib,sqlite3
from pathlib import Path
def main():
 root=Path(sys.argv[1]);title=sys.argv[2];key=sys.argv[3];n=json.loads(Path(sys.argv[4]).read_text())
 if key not in ("zip_crc","sql_null"):raise ValueError("Unregistered demo")
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
 fixture=root/"fixture";fixture.mkdir()
 def page(lines):
  os.system("cls");print("\n".join(lines),flush=True)
 if key=="zip_crc":
  good=fixture/"intact.zip";bad=fixture/"broken.zip";payload=b"FLOWMINUTE TEST DATA"
  with zipfile.ZipFile(good,"w",compression=zipfile.ZIP_STORED) as z:z.writestr("note.txt",payload)
  data=good.read_bytes();assert data.count(payload)==1
  pos=data.index(payload);changed=bytes([payload[0]^1])+payload[1:];bad.write_bytes(data[:pos]+changed+data[pos+len(payload):])
  page([" ZIP | LIVE INTEGRITY TEST",""," >>> ZipFile('broken.zip')"])
 else:
  db=sqlite3.connect(":memory:")
  db.executescript("CREATE TABLE customers(id INTEGER); INSERT INTO customers VALUES(1),(2),(3),(4); CREATE TABLE blocked(id INTEGER); INSERT INTO blocked VALUES(2),(NULL);")
  q=lambda sql:[list(x) for x in db.execute(sql)]
  badq="SELECT id FROM customers WHERE id NOT IN (SELECT id FROM blocked) ORDER BY id"
  fixedq="SELECT c.id FROM customers c WHERE NOT EXISTS (SELECT 1 FROM blocked b WHERE b.id=c.id) ORDER BY c.id"
  filteredq="SELECT id FROM customers WHERE id NOT IN (SELECT id FROM blocked WHERE id IS NOT NULL) ORDER BY id"
  page([" SQL | LIVE SQLITE TEST",""," SELECT id FROM customers"," WHERE id NOT IN"," (SELECT id FROM blocked);"])
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
 if key=="zip_crc":
  def hook():
   with zipfile.ZipFile(bad) as z:r=z.namelist()
   page([" ZIP | LIVE INTEGRITY TEST",""," Archive opened successfully"," >>> z.namelist()"," "+str(r),""," Listing is not an integrity test."]);return r
  def demo():
   with zipfile.ZipFile(bad) as z:r=z.testzip()
   print(" >>> z.testzip()\n Broken file: "+str(r),flush=True);return r
  def cause():
   with zipfile.ZipFile(bad) as z:stored=z.getinfo("note.txt").CRC
   actual=zlib.crc32(changed)
   page([" ZIP | CHECK VALUE",""," Stored CRC: "+format(stored,"08x")," Actual CRC: "+format(actual,"08x"),""," Values match: "+str(stored==actual)]);return stored!=actual
  def fix():
   page([" ZIP | TEST EVERY FILE",""," >>> ZipFile('broken.zip').testzip()"," >>> ZipFile('intact.zip').testzip()",""," Running both checks..."]);return "testzip"
  def payoff():
   with zipfile.ZipFile(bad) as z:b=z.testzip()
   with zipfile.ZipFile(good) as z:g=z.testzip()
   page([" ZIP | ACTUAL RESULTS",""," Broken archive: "+str(b)," Intact archive: "+str(g),""," None means no bad file found."]);return [b,g]
  def takeaway():
   print("\n CRC is not a signature.\n Authenticity is a separate check.",flush=True);return "not authenticity"
 else:
  def hook():
   r=q(badq);page([" SQL | LIVE SQLITE TEST",""," SELECT id FROM customers"," WHERE id NOT IN"," (SELECT id FROM blocked);",""," Result: "+str(r)," No matching rows returned."]);return r
  def demo():
   a=q("SELECT id FROM customers");b=q("SELECT id FROM blocked")
   page([" SQL | SOURCE TABLES",""," Customers: "+str([x[0] for x in a])," Blocked: "+str([x[0] for x in b]),""," None represents SQL NULL."]);return [a,b]
  def cause():
   r=q("SELECT id,id NOT IN (SELECT id FROM blocked) FROM customers ORDER BY id")
   page([" SQL | THREE-VALUED LOGIC",""," ID   NOT IN result"]+[" "+str(i)+"    "+("UNKNOWN" if v is None else "FALSE" if v==0 else "TRUE") for i,v in r]+[""," WHERE keeps only TRUE."]);return r
  def fix():
   r=q(fixedq)
   page([" SQL | MATCHING ROW TEST",""," SELECT c.id FROM customers c"," WHERE NOT EXISTS (","   SELECT 1 FROM blocked b","   WHERE b.id = c.id"," );",""," Result: "+str([x[0] for x in r])]);return r
  def payoff():
   a=q(fixedq);b=q(filteredq);assert a==b==[[1],[3],[4]]
   page([" SQL | VERIFIED RESULTS",""," NOT EXISTS: "+str([x[0] for x in a])," Filtered NOT IN: "+str([x[0] for x in b]),""," Exclude NULL in blocked list."," Both queries return 1, 3, 4."]);return [a,b]
  def takeaway():
   db.execute("INSERT INTO customers VALUES(NULL)")
   a=q(fixedq);b=q("SELECT c.id FROM customers c WHERE c.id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM blocked b WHERE b.id=c.id) ORDER BY c.id")
   page([" SQL | OUTER NULL LIMIT",""," NOT EXISTS: "+str([x[0] for x in a])," With c.id IS NOT NULL:"," "+str([x[0] for x in b]),""," Choose the intended data rule."]);return [a,b]
 event("hook",.4,hook);event("demonstration",2.0,demo);event("cause",t[2]+.15,cause);event("fix",t[3]+.15,fix);event("payoff",t[4]+.15,payoff);event("takeaway",t[5]+.15,takeaway)
 (root/"events.json").write_text(json.dumps(events,indent=2),encoding="utf8")
 wait(n["duration_seconds"]+3)
if __name__=="__main__":main()
