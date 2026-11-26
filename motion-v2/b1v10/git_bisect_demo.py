"""Execute an actual disposable Git history and bisect session; no network."""
import argparse,json,os,subprocess,sys
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument("output",type=Path);a=p.parse_args()
 d=a.output.resolve();d.mkdir(parents=True,exist_ok=False);repo=d/"demo-repo";repo.mkdir()
 env={**os.environ,"GIT_CONFIG_NOSYSTEM":"1","GIT_CONFIG_GLOBAL":os.devnull,"GIT_TERMINAL_PROMPT":"0"}
 def git(*args):
  return subprocess.run(["git","-c","user.name=FlowMinute Demo","-c","user.email=demo@example.invalid","-c","commit.gpgsign=false",*args],cwd=repo,env=env,text=True,capture_output=True,check=True).stdout.strip()
 git("init","-q")
 commits=[]
 for i in range(16):
  (repo/"example.py").write_text(f"REVISION = {i}\ndef answer():\n    return {42 if i<11 else 41}\n",encoding="utf-8")
  (repo/"test_example.py").write_text("from example import answer\nassert answer() == 42\n",encoding="utf-8")
  git("add","example.py","test_example.py");git("commit","-qm",f"Revision {i}")
  commits.append(git("rev-parse","HEAD"))
 def test():
  return subprocess.run([sys.executable,"-B","test_example.py"],cwd=repo,capture_output=True).returncode
 assert test()!=0
 git("checkout","--detach",commits[0]);assert test()==0
 git("checkout","--detach",commits[-1])
 git("bisect","start",commits[-1],commits[0])
 good,bad=0,15;steps=[]
 while bad-good>1:
  sha=git("rev-parse","HEAD");i=commits.index(sha)
  assert good<i<bad
  result=test();before=[good,bad]
  if result:bad=i
  else:good=i
  output=git("bisect","bad" if result else "good")
  steps.append({"revision":i,"commit":sha,"exit_code":result,"classification":"bad" if result else "good","range_before":before,"range_after":[good,bad],"git_output":output})
 assert bad==11 and commits[bad] in steps[-1]["git_output"]
 git("bisect","reset")
 evidence={"version":"0.8.0","mode":"actual_disposable_local_git_repository","git_version":git("--version"),"commits":commits,"initial_good":0,"initial_bad":15,"first_bad":bad,"first_bad_commit":commits[bad],"steps":steps,"diff":git("show","--format=short",commits[bad],"--","example.py"),"reset_completed":True,"release_authorized":False}
 (d/"GIT_BISECT_DEMO.json").write_text(json.dumps(evidence,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(evidence,indent=2))
if __name__=="__main__":main()
