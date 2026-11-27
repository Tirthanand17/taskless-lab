"""RC10 restartable local review production for the registered Nov 28 topic set.

No upload, scheduler, network research, or approval. New dates require a new
researched, implemented topic set; never recycle this catalog by changing a date.
"""
from __future__ import annotations
import argparse,datetime,json,shutil,subprocess,sys
from pathlib import Path
from production_review_rc6 import exact,sha,need
from daily_topics_rc9 import inventory,screen_topics,experiment
from fresh_batch_rc9p3 import verify_row,build,load
D=Path(__file__).resolve().parent
ROOT=D.parents[1]
DAY="2026-11-28"
KEYS=("zip_crc","sql_null","path_suffix")
STAGES=("audio","capture","render")
SEEDS={"zip_crc":("fresh-daily-rc9-r2/zip_crc","capture","render"),
       "sql_null":("fresh-daily-rc9-r3/sql_null","capture","render"),
       "path_suffix":("fresh-daily-rc9/path_suffix","capture-r2","render-r2")}
def save(path,value):
    tmp=path.with_name(path.name+".tmp")
    tmp.write_text(json.dumps(value,indent=2)+"\n",encoding="utf8");tmp.replace(path)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def catalog():
    topics=load(D/"RC9_TOPIC_BANK.json");topics[1]=load(D/"RC9_SQL_TOPIC_R3.json")
    need(tuple(x["id"] for x in topics)==KEYS,"topic order")
    return {x["id"]:x for x in topics}
def spec(topic):
    return {"version":"1.0.0-rc9","candidate_id":topic["id"],"voice":"af_heart","language":"en-us","fps":30,"sample_rate":48000,"review_only":True,
      "scenes":[{"id":s[0],"text":s[2],"speed":1.04 if i==0 else 1.03,"pause_ms":80 if i==0 else 200} for i,s in enumerate(topic["scenes"])]}
def audio_check(folder):
    a=folder/"audio";n=load(a/"NARRATION_REVIEW_QA.json")
    need(n["voice"]=="af_heart" and n["asr_screen_pass"] is True and n["release_authorized"] is False and n["samples"]==n["frames_at_30fps"]*1600,"narration gate")
    for p,h in [(folder/"narration_spec.json",n["spec_sha256"]),(a/"narration.wav",n["narration_sha256"]),(a/"word_captions.json",n["word_captions_sha256"]),(D/"narration_daily_rc9.py",n["script_sha256"])]:exact(p,h)
    return n
def capture_check(folder,key):
    c=load(folder/"capture/LIVE_CAPTURE_QA.json");n=audio_check(folder)
    need(c["topic"]==key and c["continuous"] is True and c["release_authorized"] is False,"capture gate")
    exact(folder/"capture/DAILY_LIVE_CAPTURE.mp4",c["capture_sha256"])
    exact(folder/"audio/NARRATION_REVIEW_QA.json",c["narration_report_sha256"])
    for name,h in c["source_sha256"].items():
        need(name in ("live_topic_demo_rc9.py","capture_daily_rc9.py","live_topic_demo_rc9p3.py","capture_daily_rc9p3.py"),"unknown source")
        exact(D/name,h);exact(folder/"capture"/name,h)
    return c
def copy_files(src,dst,names):
    need(not dst.exists(),"stage already exists")
    dst.mkdir()
    for name in names:
        p=src/name;need(p.is_file() and not p.is_symlink(),"missing seed "+name);shutil.copyfile(p,dst/name)
def adopt(folder,key,stage,seedroot):
    seed,cap,render=SEEDS[key];src=seedroot/seed
    if stage=="audio":copy_files(src/"audio",folder/stage,["NARRATION_REVIEW_QA.json","narration.wav","word_captions.json"])
    elif stage=="capture":
        c=load(src/cap/"LIVE_CAPTURE_QA.json")
        copy_files(src/cap,folder/stage,["LIVE_CAPTURE_QA.json","DAILY_LIVE_CAPTURE.mp4",*c["source_sha256"]])
    else:
        long=key=="sql_null"
        copy_files(src/render,folder/stage,["CREATIVE_BRIEF.json","CAPTURE_RECEIPT.json","NEW_LONG_QA.json" if long else "NEW_SHORT_QA.json","NEW_DAILY_LONG_REVIEW.mp4" if long else "NEW_DAILY_SHORT_REVIEW.mp4",*(["CAPTION_REVIEW.json"] if long else [])])
def command(stage,key,folder,assets,ffmpeg):
    if stage=="audio":return ["narration_daily_rc9.py","--spec",folder/"narration_spec.json","--assets",assets,"--ffmpeg",ffmpeg,"--output",folder/"audio"]
    if stage=="capture":return ["capture_daily_rc9.py" if key=="path_suffix" else "capture_daily_rc9p3.py","--topic",key,"--narration",folder/"audio/NARRATION_REVIEW_QA.json","--out",folder/"capture","--ffmpeg",ffmpeg]
    return ["render_daily_rc9.py" if key=="path_suffix" else "render_daily_sql_rc9p3.py" if key=="sql_null" else "render_daily_rc9p3.py","--topic",key,"--day",DAY,"--folder",folder,"--capture",folder/"capture","--out",folder/"render","--ffmpeg",ffmpeg]
def check_stage(stage,key,folder):
    if stage=="audio":audio_check(folder);return sha(folder/"audio/NARRATION_REVIEW_QA.json")
    if stage=="capture":capture_check(folder,key);return sha(folder/"capture/LIVE_CAPTURE_QA.json")
    row=verify_row(key,folder,folder/"capture",folder/"render",DAY)
    return row["render_report_sha256"]
def parse_seeds(values):
    out={}
    for item in values:
        k,sep,v=item.partition("=");need(sep and k in KEYS and v in STAGES and k not in out,"seed syntax topic=audio|capture|render");out[k]=STAGES.index(v)
    return out
def run(workspace,local,assets,ffmpeg,seedroot,seeds):
    workspace=workspace.absolute();workspace.mkdir(parents=True,exist_ok=True)
    lock=workspace/".run-lock"
    try:lock.mkdir()
    except FileExistsError:raise ValueError("Batch is locked; inspect prior process before removing stale lock")
    journal_path=workspace/"RUN_STATE.json"
    try:
        topics=catalog()
        # A stable content identity and date bind every resume.
        identity={"day":DAY,"topic_bank_sha256":sha(D/"RC9_TOPIC_BANK.json"),"sql_revision_sha256":sha(D/"RC9_SQL_TOPIC_R3.json")}
        if journal_path.exists():
            journal=load(journal_path);need(journal["identity"]==identity,"registered content changed")
            need(not journal["release_authorized"],"invalid journal approval")
        else:
            rows,errors=inventory(ROOT,local);need(rows and errors==0,"historical inventory incomplete")
            screen_topics(list(topics.values()),rows)
            journal={"identity":identity,"status":"RUNNING_REVIEW_ONLY","historical_manifest_rows":len(rows),"live_inventory_complete":False,"release_authorized":False,"stages":{}}
            save(journal_path,journal)
        journal["status"]="RUNNING_REVIEW_ONLY";save(journal_path,journal)
        for key in KEYS:
            folder=workspace/key;folder.mkdir(exist_ok=True)
            sp=folder/"narration_spec.json"
            if sp.exists():need(load(sp)==spec(topics[key]),"spec changed")
            else:save(sp,spec(topics[key]))
            ep=folder/"experiment.json"
            if not ep.exists():
                # Partial fixture directories are intentionally not overwritten.
                save(ep,experiment(key,folder/"fixture"))
            for i,stage in enumerate(STAGES):
                jid=key+"/"+stage;dst=folder/stage
                previous=journal["stages"].get(jid)
                if previous and previous["status"]=="COMPLETE":
                    need(check_stage(stage,key,folder)==previous["report_sha256"],"completed stage changed: "+jid)
                    print("RESUME "+jid,flush=True);continue
                if dst.exists():raise ValueError("Incomplete stage "+jid+"; inspect and move the directory to a separate quarantine before rerun")
                mode="adopted" if i<=seeds.get(key,-1) else "generated"
                journal["stages"][jid]={"status":"RUNNING","mode":mode,"started_utc":now()};save(journal_path,journal)
                try:
                    print(mode.upper()+" "+jid,flush=True)
                    if mode=="adopted":adopt(folder,key,stage,seedroot)
                    else:
                        subprocess.run([sys.executable,*map(str,command(stage,key,folder,assets,ffmpeg))],cwd=D,check=True,timeout=900)
                    h=check_stage(stage,key,folder)
                    journal["stages"][jid].update(status="COMPLETE",report_sha256=h,finished_utc=now());save(journal_path,journal)
                except Exception as e:
                    journal["stages"][jid].update(status="FAILED",error=type(e).__name__);save(journal_path,journal);raise
        rows={k:verify_row(k,workspace/k,workspace/k/"capture",workspace/k/"render",DAY) for k in KEYS}
        result=build(DAY,rows)
        result["version"]="1.0.0-rc10-phase1";result["execution_modes"]={k:v["mode"] for k,v in journal["stages"].items()};result["orchestrator_source_sha256"]=sha(Path(__file__))
        out=workspace/"RC10_RUN_QA.json"
        if out.exists():need(load(out)==result,"completed batch changed")
        else:save(out,result)
        journal["status"]="COMPLETE_REVIEW_HOLD";journal["batch_sha256"]=sha(out);save(journal_path,journal)
        print(json.dumps({"status":journal["status"],"stages":len(journal["stages"]),"release_ready_count":0,"execution_modes":result["execution_modes"]},indent=2));return result
    except Exception:
        if journal_path.exists():
            journal=load(journal_path);journal["status"]="FAILED_REVIEW_HOLD";save(journal_path,journal)
        raise
    finally:lock.rmdir()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--day",required=True);p.add_argument("--workspace",type=Path,required=True);p.add_argument("--local",type=Path,required=True);p.add_argument("--assets",type=Path,required=True);p.add_argument("--ffmpeg",required=True);p.add_argument("--seed-root",type=Path);p.add_argument("--seed",action="append",default=[]);a=p.parse_args()
    need(a.day==DAY,"No new registered topic set for this date; refusing to recycle topics")
    seeds=parse_seeds(a.seed);need(not seeds or a.seed_root is not None,"seed root required")
    run(a.workspace,a.local,a.assets,a.ffmpeg,a.seed_root,seeds)
if __name__=="__main__":main()
