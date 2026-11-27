"""Verify second registered daily batch against both November 28 review variants."""
import argparse,json
from pathlib import Path
from run_registered_rc10p2 import check_render
from topic_registry_rc10 import topics,D
from production_review_rc6 import read,sha,need,exact
from autopilot.daily_cloud_plan import PUBLISH_SLOTS
from run_daily_rc10 import save
def compare_history(rows,prior):
    for key in ("topic","video_sha256","capture_sha256"):
        values=[x[key] for x in rows]
        need(len(set(values))==len(values),"duplicate "+key+" within new batch")
        need(not set(values)&{x[key] for x in prior},"prior batch reused "+key)
def audit(workspace,output):
    day="2026-11-29";bank=topics(day)
    batch=json.loads((workspace/"BATCH_QA.json").read_text())
    need(batch["day"]==day and batch["all_three_complete"] is True and batch["completed_topics"]==3 and batch["release_authorized"] is False and batch["release_ready_count"]==0,"batch hold")
    state=json.loads((workspace/"RUN_STATE.json").read_text())
    need(state["day"]==day and state["release_authorized"] is False,"journal hold")
    rows=[check_render(workspace/t["id"],t,day) for t in bank]
    need(rows==batch["rows"],"batch evidence changed")
    prior=read("RC9_FRESH_BATCH_QA.json")["slots"]+read("RC10_RUN_QA.json")["slots"]
    compare_history(rows,prior)
    old_narration={read(n)["narration_sha256"] for n in ("RC9_ZIP_NARRATION_QA.json","RC9_SQL_NARRATION_R3_QA.json","RC9_PATH_NARRATION_QA.json")}
    narration=set();slots=[]
    for row,t,slot in zip(rows,bank,PUBLISH_SLOTS):
        folder=workspace/t["id"];n=json.loads((folder/"audio/NARRATION_REVIEW_QA.json").read_text())
        need(row["slot"]==slot[0] and row["format"]==slot[1],"slot mismatch")
        h=n["narration_sha256"];need(h not in old_narration and h not in narration,"reused narration");narration.add(h)
        modes={}
        for stage,name in (("audio","NARRATION_REVIEW_QA.json"),("capture","LIVE_CAPTURE_QA.json"),("render","NEW_LONG_QA.json" if row["format"]=="long" else "NEW_SHORT_QA.json")):
            j=state["stages"][t["id"]+"/"+stage];need(j["status"]=="COMPLETE","incomplete checkpoint")
            exact(folder/stage/name,j["sha256"]);modes[stage]=j["mode"]
        slots.append({**row,"reference_local_time":slot[2],"narration_sha256":h,"execution_modes":modes,"disposition":"HOLD_NOT_SCHEDULED"})
    result={"version":"1.0.0-rc10-phase3","day":day,"batch_sha256":sha(workspace/"BATCH_QA.json"),"runner_sha256":sha(D/"run_registered_rc10p2.py"),"source_sha256":sha(Path(__file__)),"prior_report_sha256":{n:sha(D/n) for n in ("RC9_FRESH_BATCH_QA.json","RC10_RUN_QA.json")},"slots":slots,"fresh_media_count":3,"prior_batch_hash_overlap":0,"verified_stages":9,"live_inventory_complete":False,"human_playback_approved":False,"unattended_scheduler_verified":False,"release_ready_count":0,"youtube_uploads":0,"youtube_schedules":0}
    need(not output.exists(),"new report required");save(output,result);print(json.dumps(result,indent=2))
def main():
    p=argparse.ArgumentParser();p.add_argument("--workspace",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args();audit(a.workspace.absolute(),a.output.absolute())
if __name__=="__main__":main()
