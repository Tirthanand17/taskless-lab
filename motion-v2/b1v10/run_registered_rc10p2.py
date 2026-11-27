"""Registered-date review runner. No scheduling, network discovery, or approval."""
import argparse,json,subprocess,sys
from pathlib import Path
from topic_registry_rc10 import topics,prepare,experiment,REGISTRY,D
from run_daily_rc10 import audio_check,save,now,spec
from production_review_rc6 import exact,sha,need
from autopilot.branch1_recovery import verify_capture
from scripts.publish_youtube import approval_allows_exact_video
def check_capture(folder,key):
    c= json.loads((folder/"capture/LIVE_CAPTURE_QA.json").read_text())
    need(c["topic"]==key and c["continuous"] is True and c["release_authorized"] is False,"capture gate")
    exact(folder/"capture/DAILY_LIVE_CAPTURE.mp4",c["capture_sha256"])
    exact(folder/"audio/NARRATION_REVIEW_QA.json",c["narration_report_sha256"])
    need(set(c["source_sha256"])=={"capture_rc10p2.py","live_topic_rc10p2.py"},"source set")
    for n,h in c["source_sha256"].items():exact(D/n,h);exact(folder/"capture"/n,h)
    return c
def check_render(folder,t,day):
    key=t["id"];c=check_capture(folder,key);n=audio_check(folder);long=t["format"]=="long";o=folder/"render"
    name="NEW_LONG_QA.json" if long else "NEW_SHORT_QA.json"
    r=json.loads((o/name).read_text());b=json.loads((o/"CREATIVE_BRIEF.json").read_text())
    final=o/("NEW_DAILY_LONG_REVIEW.mp4" if long else "NEW_DAILY_SHORT_REVIEW.mp4")
    for path,h in [(final,r["mp4_sha256"]),(D/"render_rc10p2.py",r["render_source_sha256"]),(folder/"capture/LIVE_CAPTURE_QA.json",r["capture_report_sha256"]),(folder/"audio/NARRATION_REVIEW_QA.json",r["narration_report_sha256"]),(o/"CREATIVE_BRIEF.json",r["creative_brief_sha256"]),(o/"CAPTURE_RECEIPT.json",r["receipt_sha256"])]:exact(path,h)
    need(r["topic"]==key and r["capture_sha256"]==c["capture_sha256"] and r["spec_sha256"]==n["spec_sha256"] and r["episode_id"]==b["episode_id"]=="fm_"+day.replace("-","")+"_"+key+"_"+t["format"] and b["title"]==t["title"],"episode link")
    identity=verify_capture(b,folder/"capture/DAILY_LIVE_CAPTURE.mp4",o/"CAPTURE_RECEIPT.json",windows_evidence=folder/"capture/LIVE_CAPTURE_QA.json")
    need(identity==r["identity"] and r["full_decode_pass"] is True and r["release_authorized"] is False and r["human_playback_approved"] is False and r["frames"]==n["frames_at_30fps"] and r["resolution"]==([1920,1080] if long else [1080,1920]) and r["audio"]["decoded_samples"]==r["frames"]*1600 and r["audio"]["clipped_samples"]==0,"render gate")
    need(not approval_allows_exact_video({"approved_video_sha256":r["mp4_sha256"]},r["mp4_sha256"]),"unsigned release")
    return {"topic":key,"format":t["format"],"slot":t["slot"],"title":t["title"],"frames":r["frames"],"duration_seconds":r["duration_seconds"],"video_sha256":r["mp4_sha256"],"capture_sha256":c["capture_sha256"],"render_report_sha256":sha(o/name),"release_authorized":False}
def command(stage,folder,key,day,assets,ffmpeg):
    if stage=="audio":return ["narration_daily_rc9.py","--spec",folder/"narration_spec.json","--assets",assets,"--ffmpeg",ffmpeg,"--output",folder/"audio"]
    if stage=="capture":return ["capture_rc10p2.py","--topic",key,"--narration",folder/"audio/NARRATION_REVIEW_QA.json","--out",folder/"capture","--ffmpeg",ffmpeg]
    return ["render_rc10p2.py","--topic",key,"--day",day,"--folder",folder,"--capture",folder/"capture","--out",folder/"render","--ffmpeg",ffmpeg]
def run(day,workspace,local,assets,ffmpeg,only=None):
    bank=topics(day);workspace=workspace.absolute()
    if not workspace.exists():prepare(day,local,workspace)
    report=json.loads((workspace/"TOPIC_QA.json").read_text())
    need(report["day"]==day and report["bank_sha256"]==sha(D/REGISTRY[day]) and report["release_authorized"] is False,"registry mismatch")
    lock=workspace/".run-lock";lock.mkdir()
    state=workspace/"RUN_STATE.json";journal={"day":day,"bank_sha256":report["bank_sha256"],"stages":{},"release_authorized":False}
    try:
        if state.exists():
            journal=json.loads(state.read_text());need(journal["day"]==day and journal["bank_sha256"]==report["bank_sha256"] and journal["release_authorized"] is False,"journal mismatch")
        result=[]
        for t in bank:
            key=t["id"]
            if only and key!=only:continue
            folder=workspace/key
            need(json.loads((folder/"narration_spec.json").read_text())==spec(t),"script changed")
            r=next(x for x in report["topics"] if x["topic"]==key);exact(folder/"experiment.json",r["experiment_sha256"]);exact(folder/"narration_spec.json",r["spec_sha256"])
            for stage in ("audio","capture","render"):
                jid=key+"/"+stage;dst=folder/stage;prior=journal["stages"].get(jid)
                if not dst.exists():
                    need(not prior or prior["status"]!="COMPLETE","completed stage missing")
                    journal["stages"][jid]={"status":"RUNNING","mode":"generated","started":now()};save(state,journal)
                    subprocess.run([sys.executable,*map(str,command(stage,folder,key,day,assets,ffmpeg))],cwd=D,check=True,timeout=900)
                    mode="generated"
                else:
                    need(not prior or prior["status"]=="COMPLETE","incomplete stage; quarantine before retry")
                    mode=prior["mode"] if prior else "adopted_same_date"
                if stage=="audio":audio_check(folder);h=sha(dst/"NARRATION_REVIEW_QA.json")
                elif stage=="capture":check_capture(folder,key);h=sha(dst/"LIVE_CAPTURE_QA.json")
                else:row=check_render(folder,t,day);h=row["render_report_sha256"];result.append(row)
                if prior and prior["status"]=="COMPLETE":need(prior["sha256"]==h,"checkpoint changed")
                journal["stages"][jid]={"status":"COMPLETE","mode":mode,"sha256":h};save(state,journal)
                print("VERIFIED "+jid,flush=True)
        need(len({r["video_sha256"] for r in result})==len(result)==len({r["capture_sha256"] for r in result}),"duplicate media")
        qa={"version":"1.0.0-rc10-phase2","day":day,"rows":result,"completed_topics":len(result),"all_three_complete":len(result)==3,"live_inventory_complete":False,"release_ready_count":0,"release_authorized":False}
        save(workspace/("BATCH_QA.json" if not only else only+"_QA.json"),qa)
        print(json.dumps(qa,indent=2));return qa
    finally:lock.rmdir()
def main():
    p=argparse.ArgumentParser();p.add_argument("--day",required=True);p.add_argument("--workspace",type=Path,required=True);p.add_argument("--local",type=Path,required=True);p.add_argument("--assets",type=Path,required=True);p.add_argument("--ffmpeg",required=True);p.add_argument("--only",choices=["shared_lists","outer_join_filter","group_runs"]);a=p.parse_args()
    run(a.day,a.workspace,a.local,a.assets,a.ffmpeg,a.only)
if __name__=="__main__":main()
