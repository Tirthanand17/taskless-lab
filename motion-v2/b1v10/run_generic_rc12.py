"""RC12 phase 3: restartable curated-pool daily review production.

Only approved bounded operations; no network discovery, scheduling or publishing.
Completed reports are revalidated. Existing partial directories are never overwritten.
"""
import argparse,json,subprocess,sys
from pathlib import Path
from production_review_rc6 import exact,sha,need
from select_topics_rc12 import D,BANK,load,prepare,steps
from run_daily_rc10 import audio_check,save,spec,now
from revise_narration_rc12 import verify as verify_revision
from autopilot.branch1_recovery import verify_capture
from autopilot.daily_cloud_plan import PUBLISH_SLOTS,parse_day_ist
from scripts.publish_youtube import approval_allows_exact_video
def selection(work,day):
    r=load(work/"SELECTION_QA.json")
    need(r["day"]==day and r["bank_sha256"]==sha(D/BANK) and r["source_sha256"]==sha(D/"select_topics_rc12.py") and r["release_authorized"] is False,"selection scope")
    rows=r["selected"];need(len(rows)==3 and len({x["topic"] for x in rows})==3,"selection count")
    bank={x["id"]:x for x in load(D/BANK)}
    for row,slot in zip(rows,PUBLISH_SLOTS):
        key=row["topic"];need(key in bank and row["slot"]==slot[0] and row["format"]==slot[1],"slot mismatch")
        f=work/key;t=load(f/"topic.json")
        need(all(t[k]==v for k,v in bank[key].items()) and t["slot"]==slot[0] and row["title"]==t["title"],"topic mismatch")
        exact(f/"experiment.json",row["experiment_sha256"])
        if (f/"NARRATION_REVISION_QA.json").exists():verify_revision(work,row)
        else:
            exact(f/"topic.json",row["topic_sha256"]);exact(f/"narration_spec.json",row["spec_sha256"])
        need(load(f/"experiment.json")==row["experiment"]==steps(t) and load(f/"narration_spec.json")==spec(t),"fixture or spec mismatch")
    return rows
def capture_check(f,key):
    c=load(f/"capture/LIVE_CAPTURE_QA.json")
    need(c["topic"]==key and c["continuous"] is True and c["release_authorized"] is False,"capture gate")
    exact(f/"topic.json",c["topic_sha256"])
    exact(f/"capture/DAILY_LIVE_CAPTURE.mp4",c["capture_sha256"])
    exact(f/"audio/NARRATION_REVIEW_QA.json",c["narration_report_sha256"])
    need(set(c["source_sha256"])=={"select_topics_rc12.py","capture_generic_rc12.py","live_generic_rc12.py"},"source set")
    for n,h in c["source_sha256"].items():exact(D/n,h);exact(f/"capture"/n,h)
    need([x["result"] for x in c["events"]]==[x["result"] for x in steps(load(f/"topic.json"))],"event results")
    return c
def render_check(f,topic,day,o):
    key=topic["topic"];long=topic["format"]=="long"
    n=audio_check(f);c=capture_check(f,key)
    r=load(o/("NEW_LONG_QA.json" if long else "NEW_SHORT_QA.json"));b=load(o/"CREATIVE_BRIEF.json")
    final=o/("NEW_DAILY_LONG_REVIEW.mp4" if long else "NEW_DAILY_SHORT_REVIEW.mp4")
    for p,h in [(final,r["mp4_sha256"]),(D/"render_generic_rc12.py",r["render_source_sha256"]),(D/"polish_shorts_rc11.py",r["design_dependency_sha256"]),(f/"topic.json",r["topic_sha256"]),(f/"capture/LIVE_CAPTURE_QA.json",r["capture_report_sha256"]),(f/"audio/NARRATION_REVIEW_QA.json",r["narration_report_sha256"]),(o/"CREATIVE_BRIEF.json",r["creative_brief_sha256"]),(o/"CAPTURE_RECEIPT.json",r["receipt_sha256"])]:exact(p,h)
    need(r["topic"]==key and r["episode_id"]==b["episode_id"]=="fm_"+day.replace("-","")+"_"+key+"_"+topic["format"] and b["title"]==topic["title"] and r["capture_sha256"]==c["capture_sha256"] and r["spec_sha256"]==n["spec_sha256"],"media identity")
    identity=verify_capture(b,f/"capture/DAILY_LIVE_CAPTURE.mp4",o/"CAPTURE_RECEIPT.json",windows_evidence=f/"capture/LIVE_CAPTURE_QA.json")
    need(identity==r["identity"] and r["full_decode_pass"] is True and r["release_authorized"] is False and r["human_playback_approved"] is False,"render gate")
    need(r["frames"]==n["frames_at_30fps"] and r["resolution"]==([1920,1080] if long else [1080,1920]) and r["fps"]==30 and r["audio"]["decoded_samples"]==r["frames"]*1600 and r["audio"]["clipped_samples"]==0,"technical gate")
    need(len(r["observed"])>=7 and all(x["error"]<4 for x in r["observed"]),"footage match")
    need(not approval_allows_exact_video({"approved_video_sha256":sha(final)},sha(final)),"unsigned release")
    return {"topic":key,"title":topic["title"],"format":topic["format"],"slot":topic["slot"],"frames":r["frames"],"duration_seconds":r["duration_seconds"],"video_sha256":r["mp4_sha256"],"capture_sha256":c["capture_sha256"],"narration_sha256":n["narration_sha256"],"render_report_sha256":sha(o/("NEW_LONG_QA.json" if long else "NEW_SHORT_QA.json")),"video_relative_path":final.relative_to(f.parent).as_posix(),"release_authorized":False}
def run(day,work,local,assets,ffmpeg,prior=(),adopt_existing=False):
    parse_day_ist(day);work=work.absolute()
    lock=work.with_name(work.name+".rc12p3-lock");lock.parent.mkdir(parents=True,exist_ok=True);lock.mkdir()
    try:
        if not work.exists():prepare(day,local,work,prior)
        rows=selection(work,day)
        state=work/"RUN_GENERIC_STATE.json"
        ident={"day":day,"selection_sha256":sha(work/"SELECTION_QA.json"),"runner_sha256":sha(Path(__file__)),"revisions":{t["topic"]:sha(work/t["topic"]/"NARRATION_REVISION_QA.json") for t in rows if (work/t["topic"]/"NARRATION_REVISION_QA.json").exists()}}
        j=load(state) if state.exists() else {"identity":ident,"stages":{},"release_authorized":False}
        need(j["identity"]==ident and j["release_authorized"] is False,"journal scope")
        output=[]
        for t,slot in zip(rows,PUBLISH_SLOTS):
            key=t["topic"];f=work/key;long=t["format"]=="long"
            for stage in ("audio","capture","render"):
                jid=key+"/"+stage;old=j["stages"].get(jid)
                # A corrected existing export must be explicitly adopted, never silently fall back.
                dst=f/stage
                if stage=="render" and key=="strip_chars" and day=="2026-11-30" and ((old and old.get("directory")=="render-r2") or (not old and adopt_existing and (f/"render-r2/NEW_SHORT_QA.json").is_file())):dst=f/"render-r2"
                if old and old["status"]=="COMPLETE":
                    need(old["directory"]==dst.name and dst.is_dir(),"checkpoint directory")
                    mode=old["mode"]
                elif dst.exists():
                    need(not old and adopt_existing,"unverified existing or incomplete stage; inspect before retry")
                    mode="adopted_same_date"
                else:
                    need(not old or old["status"]!="COMPLETE","missing completed stage")
                    mode="generated"
                    j["stages"][jid]={"status":"RUNNING","mode":mode,"directory":dst.name,"started":now()};save(state,j)
                    cmd={"audio":["narration_daily_rc9.py","--spec",f/"narration_spec.json","--assets",assets,"--ffmpeg",ffmpeg,"--output",dst],"capture":["capture_generic_rc12.py","--topic",f/"topic.json","--narration",f/"audio/NARRATION_REVIEW_QA.json","--out",dst,"--ffmpeg",ffmpeg],"render":["render_generic_rc12.py","--topic",key,"--day",day,"--folder",f,"--capture",f/"capture","--out",dst,"--ffmpeg",ffmpeg]}[stage]
                    try:subprocess.run([sys.executable,*map(str,cmd)],cwd=D,check=True,timeout=900)
                    except Exception:
                        j["stages"][jid]["status"]="FAILED";save(state,j);raise
                if stage=="audio":audio_check(f);h=sha(dst/"NARRATION_REVIEW_QA.json")
                elif stage=="capture":capture_check(f,key);h=sha(dst/"LIVE_CAPTURE_QA.json")
                else:
                    row=render_check(f,t,day,dst);h=row["render_report_sha256"];output.append({**row,"reference_local_time":slot[2],"disposition":"HOLD_NOT_SCHEDULED"})
                if old and old["status"]=="COMPLETE":need(old["sha256"]==h,"completed report changed")
                j["stages"][jid]={"status":"COMPLETE","mode":mode,"directory":dst.name,"sha256":h};save(state,j);print("VERIFIED "+jid,flush=True)
        for field in ("video_sha256","capture_sha256","narration_sha256"):
            need(len({x[field] for x in output})==3,"duplicate "+field)
        result={"version":"1.0.0-rc12-phase3",**ident,"slots":output,"verified_stages":9,"execution_modes":{k:v["mode"] for k,v in j["stages"].items()},"release_ready_count":0,"live_inventory_complete":False,"scheduler_verified":False,"youtube_uploads":0,"youtube_schedules":0}
        out=work/"GENERIC_BATCH_QA.json"
        if out.exists():need(load(out)==result,"batch changed")
        else:save(out,result)
        print(json.dumps(result,indent=2));return result
    finally:lock.rmdir()
def main():
    p=argparse.ArgumentParser();p.add_argument("--day",required=True);p.add_argument("--workspace",type=Path,required=True);p.add_argument("--local",type=Path,required=True);p.add_argument("--assets",type=Path,required=True);p.add_argument("--ffmpeg",required=True);p.add_argument("--prior-report",type=Path,action="append",default=[]);p.add_argument("--adopt-existing",action="store_true");a=p.parse_args()
    run(a.day,a.workspace,a.local,a.assets,a.ffmpeg,a.prior_report,a.adopt_existing)
if __name__=="__main__":main()
