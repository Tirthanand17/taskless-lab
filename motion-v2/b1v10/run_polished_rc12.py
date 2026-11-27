"""RC12 registered daily workflow with mandatory polished review outputs.
The supported registry is limited to November 29; unknown dates fail closed.
No scheduling, approval, or publisher calls.
"""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
from production_review_rc6 import read,sha,exact,need
from run_daily_rc10 import save
from run_registered_rc10p2 import run as base_run,check_render
from topic_registry_rc10 import topics,D
from autopilot.daily_cloud_plan import PUBLISH_SLOTS
from scripts.publish_youtube import approval_allows_exact_video
PREFIX={"shared_lists":"SHARED","outer_join_filter":"JOIN","group_runs":"GROUP"}
def names(t):
    fmt=t["format"].upper()
    return "RC11_"+fmt+"_QA.json","RC11_POLISHED_"+fmt+".mp4"
def verify(folder,t,day):
    old=check_render(folder,t,day);key=t["id"];fmt=t["format"];report,mp4=names(t)
    d=folder/"polish-rc12";r=json.loads((d/report).read_text())
    exact(d/mp4,r["video_sha256"]);exact(d/"captions.ass",r["caption_ass_sha256"])
    exact(D/("polish_long_rc11.py" if fmt=="long" else "polish_shorts_rc11.py"),r["source_sha256"])
    if fmt=="long":exact(D/"polish_shorts_rc11.py",r["design_dependency_sha256"])
    need(r["topic"]==key and r["prior_report_sha256"]==old["render_report_sha256"] and r["prior_sha256"]==old["video_sha256"] and r["capture_sha256"]==old["capture_sha256"] and r["frames"]==old["frames"],"base identity mismatch")
    need(r["video_sha256"]!=old["video_sha256"] and r["pcm_identical"] is True and r["full_decode_pass"] is True and r["human_playback_approved"] is False and r["release_authorized"] is False,"polish review gate")
    need(r["resolution"]==([1920,1080] if fmt=="long" else [1080,1920]) and r["fps"]==30 and r["audio"]["decoded_samples"]==r["frames"]*1600 and r["audio"]["clipped_samples"]==0,"media gate")
    c=json.loads((folder/"capture/LIVE_CAPTURE_QA.json").read_text())
    need(r["event_starts_frames"]==[0]+[x["frame"]*5 for x in c["changes"]] and r["actual_event_times_seconds"]==[x["actual_seconds"] for x in c["events"]],"event link")
    need(len(r["source_checks"])==7 and all(x["error"]<4 for x in r["source_checks"]),"source checks")
    need(not approval_allows_exact_video({"approved_video_sha256":r["video_sha256"]},r["video_sha256"]),"unsigned acceptance")
    return {"topic":key,"format":fmt,"slot":t["slot"],"title":t["title"],"episode_id":"fm_"+day.replace("-","")+"_"+key+"_"+fmt,"video_relative_path":str(Path(key)/"polish-rc12"/mp4).replace("\\","/"),"video_sha256":r["video_sha256"],"base_video_sha256":old["video_sha256"],"capture_sha256":r["capture_sha256"],"polish_report_sha256":sha(d/report),"frames":r["frames"],"release_authorized":False}
def adopt(folder,t):
    report,mp4=names(t);src=folder/"polish-rc11";dst=folder/"polish-rc12"
    exact(src/report,sha(D/("RC11_"+PREFIX[t["id"]]+"_"+t["format"].upper()+"_QA.json")))
    dst.mkdir()
    for n in (report,mp4,"captions.ass"):
        p=src/n;need(p.is_file() and not p.is_symlink(),"missing seed artifact");shutil.copyfile(p,dst/n)
def run(day,workspace,local,assets,ffmpeg,adopt_keys=()):
    bank=topics(day);need(set(adopt_keys)<={t["id"] for t in bank},"unknown adopt topic")
    workspace=workspace.absolute()
    # Existing registered runner prepares a new workspace and performs all base stages.
    # The additional lock covers the full orchestration, including base production.
    lock=workspace.with_name(workspace.name+".rc12-lock");lock.parent.mkdir(parents=True,exist_ok=True);lock.mkdir()
    try:
        base=base_run(day,workspace,local,assets,ffmpeg)
        need(base["all_three_complete"] is True and base["release_authorized"] is False,"base incomplete")
        stage_lock=workspace/".run-lock";stage_lock.mkdir()
        try:
            state=workspace/"RC12_STATE.json";identity={"day":day,"base_batch_sha256":sha(workspace/"BATCH_QA.json"),"runner_sha256":sha(Path(__file__))}
            j=json.loads(state.read_text()) if state.exists() else {"identity":identity,"stages":{},"release_authorized":False}
            need(j["identity"]==identity and j["release_authorized"] is False,"checkpoint identity")
            rows=[]
            for t,slot in zip(bank,PUBLISH_SLOTS):
                key=t["id"];folder=workspace/key;dst=folder/"polish-rc12";prior=j["stages"].get(key)
                if prior and prior["status"]=="COMPLETE":
                    row=verify(folder,t,day);need(row["polish_report_sha256"]==prior["report_sha256"],"checkpoint changed")
                else:
                    need(not dst.exists(),"incomplete polish; inspect/quarantine before retry")
                    mode="adopted_exact_rc11" if key in adopt_keys else "generated"
                    j["stages"][key]={"status":"RUNNING","mode":mode};save(state,j)
                    try:
                        if mode=="adopted_exact_rc11":adopt(folder,t)
                        else:
                            cmd=["polish_long_rc11.py"] if t["format"]=="long" else ["polish_shorts_rc11.py","--topic",key]
                            subprocess.run([sys.executable,*cmd,"--folder",str(folder),"--out",str(dst),"--ffmpeg",ffmpeg],cwd=D,check=True,timeout=900)
                        row=verify(folder,t,day)
                        j["stages"][key].update(status="COMPLETE",report_sha256=row["polish_report_sha256"]);save(state,j)
                    except Exception:
                        j["stages"][key]["status"]="FAILED";save(state,j);raise
                need(row["slot"]==slot[0] and row["format"]==slot[1],"slot mismatch")
                rows.append({**row,"mode":j["stages"][key]["mode"],"reference_local_time":slot[2],"disposition":"HOLD_NOT_SCHEDULED"})
                print("POLISHED "+key,flush=True)
            need(len({x["video_sha256"] for x in rows})==3,"duplicate final")
            result={"version":"1.0.0-rc12-phase1",**identity,"slots":rows,"polished_count":3,"verified_frames":sum(x["frames"] for x in rows),"release_ready_count":0,"live_inventory_complete":False,"scheduler_verified":False,"youtube_uploads":0,"youtube_schedules":0}
            output=workspace/"RC12_REVIEW_QA.json"
            if output.exists():need(json.loads(output.read_text())==result,"review batch changed")
            else:save(output,result)
            print(json.dumps(result,indent=2));return result
        finally:stage_lock.rmdir()
    finally:lock.rmdir()
def main():
    p=argparse.ArgumentParser();p.add_argument("--day",required=True);p.add_argument("--workspace",type=Path,required=True);p.add_argument("--local",type=Path,required=True);p.add_argument("--assets",type=Path,required=True);p.add_argument("--ffmpeg",required=True);p.add_argument("--adopt-rc11",action="append",default=[]);a=p.parse_args()
    run(a.day,a.workspace,a.local,a.assets,a.ffmpeg,a.adopt_rc11)
if __name__=="__main__":main()
