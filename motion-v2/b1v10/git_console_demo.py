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
    def ready(i):
        (root/f"ready-{i}").touch()
        deadline=time.monotonic()+40
        while not (root/f"ack-{i}").exists():
            if time.monotonic()>deadline:raise TimeoutError("capture handshake")
            time.sleep(.025)
    page(["","16 actual Git revisions","Prior experiment: first bad revision 11","Re-running the same test in an isolated clone.","","Known good: 0 / Known bad: 15"])
    ready(0)
    output=git("bisect","start",commits[-1],commits[0])
    current=commits.index(git("rev-parse","HEAD"))
    page(["","$ git bisect start BAD GOOD","", "Selected revision: "+str(current),git("rev-parse","--short","HEAD"),"",output.splitlines()[0][:55]])
    ready(1)
    steps=[]
    for j,expected in enumerate(evidence["steps"]):
        sha=git("rev-parse","HEAD");i=commits.index(sha)
        assert i==expected["revision"]
        result=run([sys.executable,"-B","test_example.py"],repo,False)
        classification="bad" if result.returncode else "good"
        assert classification==expected["classification"]
        output=git("bisect",classification)
        page(["","$ python -B test_example.py","Revision "+str(i)+" / exit code "+str(result.returncode),"","$ git bisect "+classification,"","Remaining: "+str(expected["range_after"][0])+" to "+str(expected["range_after"][1]),output.splitlines()[0][:55]])
        steps.append({"revision":i,"commit":sha,"exit_code":result.returncode,"classification":classification,"git_output":output})
        ready(j+2)
    assert commits[11] in steps[-1]["git_output"]
    diff=git("show","--format=","--unified=0",commits[11],"--","example.py")
    assert "-    return 42" in diff and "+    return 41" in diff
    page(["","Git reports first bad commit:",commits[11][:32],commits[11][32:],"","Actual code change:","-    return 42","+    return 41","","4 midpoint tests"])
    ready(6)
    git("bisect","reset")
    assert git("rev-parse","HEAD")==commits[-1]
    page(["","$ git bisect reset","","Back at revision 15",git("rev-parse","--short","HEAD"),"","Inspect the change, fix, and rerun tests."])
    (root/"actual_git_result.json").write_text(json.dumps({"commits":commits,"steps":steps,"first_bad":11,"first_bad_commit":commits[11],"reset_completed":True,"diff":diff},indent=2),encoding="utf-8")
    ready(7)
if __name__=="__main__":main()
