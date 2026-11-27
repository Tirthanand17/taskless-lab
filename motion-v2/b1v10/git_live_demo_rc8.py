"""Repeat the actual bisect experiment in a fresh local clone, live in a dedicated console."""
import ctypes, json, os, subprocess, sys, time
from pathlib import Path

def main():
    root=Path(sys.argv[1]);title=sys.argv[2];original=Path(sys.argv[3])
    evidence=json.loads(Path(sys.argv[4]).read_text(encoding="utf-8"))
    repo=root/"isolated-demo"
    env={**os.environ,"GIT_CONFIG_NOSYSTEM":"1","GIT_CONFIG_GLOBAL":os.devnull,"GIT_TERMINAL_PROMPT":"0"}
    def run(args,cwd=root,check=True):
        return subprocess.run(args,cwd=cwd,env=env,capture_output=True,text=True,check=check)
    run(["git","-c","core.hooksPath=NUL","clone","--local","--no-hardlinks","--quiet",str(original),str(repo)])
    def git(*args):
        return run(["git","-c","core.hooksPath=NUL",*args],repo).stdout.strip()
    commits=evidence["commits"]
    assert len(commits)==16 and git("rev-parse","HEAD")==commits[-1]
    for sha in commits:assert git("cat-file","-t",sha)=="commit"
    k=ctypes.windll.kernel32
    if not k.SetConsoleTitleW(title):raise RuntimeError("isolated console required")
    class COORD(ctypes.Structure):
        _fields_=[("X",ctypes.c_short),("Y",ctypes.c_short)]
    class FONT(ctypes.Structure):
        _fields_=[("cbSize",ctypes.c_ulong),("nFont",ctypes.c_ulong),("dwFontSize",COORD),("FontFamily",ctypes.c_uint),("FontWeight",ctypes.c_uint),("FaceName",ctypes.c_wchar*32)]
    k.GetStdHandle.restype=ctypes.c_void_p
    handle=k.GetStdHandle(-11);info=FONT();info.cbSize=ctypes.sizeof(FONT);info.dwFontSize=COORD(0,26);info.FontFamily=54;info.FontWeight=400;info.FaceName="Consolas"
    k.SetCurrentConsoleFontEx.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.POINTER(FONT)]
    if not k.SetCurrentConsoleFontEx(handle,False,ctypes.byref(info)):raise RuntimeError("console font")
    os.system("mode con: cols=58 lines=15 >nul")
    def page(lines):
        os.system("cls")
        print(" GIT BISECT | REAL LOCAL EXECUTION",flush=True)
        for line in lines:print(" "+line,flush=True)
    page(["","$ python -B test_example.py","Revision 15 / running the test..."])
    (root/"ready").touch()
    deadline=time.monotonic()+30
    while not (root/"go").exists():
        if time.monotonic()>deadline:raise TimeoutError("capture handshake")
        time.sleep(.01)
    start=time.monotonic();events=[];steps=[]
    def wait(t):
        while time.monotonic()-start<t:time.sleep(.01)
    def event(id,t,fn):
        wait(t);v=fn();events.append({"id":id,"planned_seconds":t,"actual_seconds":round(time.monotonic()-start,4),"result":v})
    def test():
        return run([sys.executable,"-B","test_example.py"],repo,False).returncode
    def bad_endpoint():
        code=test();assert code!=0
        print(" Test FAIL / exit code "+str(code),flush=True);return code
    def good_endpoint():
        page(["","$ git checkout --detach GOOD","$ python -B test_example.py"])
        git("checkout","--detach",commits[0]);code=test();assert code==0
        print(" Revision 0 / PASS",flush=True);return code
    def setup():
        git("checkout","--detach",commits[-1])
        page(["","16 actual revisions","Known GOOD: revision 0","Known BAD: revision 15","","Same Python test at every step."])
        return git("rev-parse","HEAD")
    def begin():
        page(["","$ git bisect start BAD GOOD"])
        output=git("bisect","start",commits[-1],commits[0]);idx=commits.index(git("rev-parse","HEAD"))
        print(" Selected revision: "+str(idx),flush=True);return idx
    def step(j):
        expected=evidence["steps"][j];sha=git("rev-parse","HEAD");i=commits.index(sha)
        assert i==expected["revision"]
        page(["","$ python -B test_example.py","Revision "+str(i)])
        code=test();classification="bad" if code else "good"
        assert classification==expected["classification"]
        print(" Exit code: "+str(code)+" / "+classification.upper(),flush=True)
        print(" $ git bisect "+classification,flush=True)
        output=git("bisect",classification)
        print(" Remaining: "+str(expected["range_after"][0])+" to "+str(expected["range_after"][1]),flush=True)
        steps.append({"revision":i,"commit":sha,"exit_code":code,"classification":classification,"git_output":output})
        return i
    def identify():
        assert commits[11] in steps[-1]["git_output"]
        diff=git("show","--format=","--unified=0",commits[11],"--","example.py")
        assert "-    return 42" in diff and "+    return 41" in diff
        page(["","First bad commit: revision 11",commits[11][:32],commits[11][32:],"","Actual code change:","-    return 42","+    return 41"])
        return diff
    def fix():
        git("bisect","reset");assert git("rev-parse","HEAD")==commits[-1]
        page(["","$ git bisect reset","Back at revision 15","","Repair the isolated example:","-    return 41","+    return 42"])
        f=repo/"example.py";old=f.read_text();assert old.count("return 41")==1
        f.write_text(old.replace("return 41","return 42"));return "repaired disposable clone"
    def retest():
        print(" $ python -B test_example.py",flush=True)
        code=test();assert code==0
        print(" PASS / exit code 0",flush=True);return code
    def takeaway():
        page(["","Reproducible test + good/bad endpoints","4 midpoint tests / first bad: 11","Repair applied / retest PASS","","Linear example; flaky tests can mislead."])
        return "verified local repair"
    event("bad_endpoint",.4,bad_endpoint)
    event("good_endpoint",1.8,good_endpoint)
    event("setup",11.2,setup)
    event("bisect_start",24.7,begin)
    event("step1",37.6,lambda:step(0))
    event("step2",48.6,lambda:step(1))
    event("step3",60.0,lambda:step(2))
    event("step4",66.0,lambda:step(3))
    event("identified",72.0,identify)
    event("fix",79.5,fix)
    event("retest",82.5,retest)
    event("takeaway",98.4,takeaway)
    (root/"events.json").write_text(json.dumps({"events":events,"steps":steps,"commits":commits,"first_bad_commit":commits[11],"reset_completed":True,"repair_test_exit":0},indent=2),encoding="utf-8")
    wait(115)
if __name__=="__main__":main()
