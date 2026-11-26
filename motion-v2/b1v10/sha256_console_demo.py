"""Original fixture-only SHA-256 program, run inside a dedicated Windows console."""
import ctypes, hashlib, json, os, sys, time
from pathlib import Path

def main():
    root=Path(sys.argv[1])
    title=sys.argv[2]
    k=ctypes.windll.kernel32
    if not k.SetConsoleTitleW(title):
        raise RuntimeError("No isolated console")
    class COORD(ctypes.Structure):
        _fields_=[("X",ctypes.c_short),("Y",ctypes.c_short)]
    class FONT(ctypes.Structure):
        _fields_=[("cbSize",ctypes.c_ulong),("nFont",ctypes.c_ulong),("dwFontSize",COORD),("FontFamily",ctypes.c_uint),("FontWeight",ctypes.c_uint),("FaceName",ctypes.c_wchar*32)]
    k.GetStdHandle.restype=ctypes.c_void_p
    handle=k.GetStdHandle(-11)
    info=FONT();info.cbSize=ctypes.sizeof(FONT);info.dwFontSize=COORD(0,26);info.FontFamily=54;info.FontWeight=400;info.FaceName="Consolas"
    k.SetCurrentConsoleFontEx.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.POINTER(FONT)]
    if not k.SetCurrentConsoleFontEx(handle,False,ctypes.byref(info)):raise RuntimeError("Cannot enlarge dedicated console font")
    os.system("mode con: cols=58 lines=21 >nul")
    # Actual files, no network or personal records.
    a=root/"A.bin";b=root/"B.bin"
    a.write_bytes(b"A");b.write_bytes(b"B")
    def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    expected=digest(a)
    observed=digest(b)
    print(" SHA-256 | ACTUAL PYTHON EXECUTION",flush=True)
    print(" One byte changed. Two different hashes.",flush=True)
    print(" A.bin : "+expected[:24],flush=True)
    print(" B.bin : "+observed[:24],flush=True)
    print(" Preview: first 24 hex characters",flush=True)
    (root/"ready").touch()
    deadline=time.monotonic()+30
    while not (root/"go").exists():
        if time.monotonic()>deadline:raise TimeoutError("capture not ready")
        time.sleep(.03)
    time.sleep(2.0)
    print("\n >>> Read two actual one-byte files",flush=True)
    print(" A.bin = "+repr(a.read_bytes()),flush=True)
    print(" B.bin = "+repr(b.read_bytes()),flush=True)
    time.sleep(2.0)
    print("\n >>> hashlib.sha256(file_bytes)",flush=True)
    actual=[digest(a),digest(b)]
    for name,val in zip(("A","B"),actual):
        print(" "+name+": "+val[:32],flush=True)
        print("    "+val[32:],flush=True)
    time.sleep(2.0)
    print("\n >>> Compare ALL 64 hex characters",flush=True)
    print(" A matches expected: "+str(actual[0]==expected),flush=True)
    print(" B matches expected: "+str(actual[1]==expected),flush=True)
    print(" Integrity is not proof of safety.",flush=True)
    (root/"actual_result.json").write_text(json.dumps({"input_a_hex":a.read_bytes().hex(),"input_b_hex":b.read_bytes().hex(),"sha256_a":actual[0],"sha256_b":actual[1],"equal":actual[0]==actual[1],"expected_a_match":actual[0]==expected,"expected_b_match":actual[1]==expected},indent=2),encoding="utf-8")
    time.sleep(10)
if __name__=="__main__":main()
