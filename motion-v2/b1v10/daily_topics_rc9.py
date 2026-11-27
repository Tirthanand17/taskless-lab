"""RC9 researched daily topic intake. Executes only synthetic local fixtures; no uploads."""
from __future__ import annotations
import argparse,hashlib,json,re,sqlite3,sys,zipfile
from pathlib import Path
D=Path(__file__).resolve().parent
ROOT=D.parents[1]
sys.path.insert(0,str(ROOT))
from autopilot.daily_cloud_plan import PUBLISH_SLOTS,parse_day_ist
def need(ok,msg):
    if not ok:raise ValueError(msg)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):return " ".join(re.findall(r"[a-z0-9]+",s.casefold()))
def load(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def inventory(root,local):
    # Public/repository drafts and local episode manifests are not live Studio evidence.
    paths=list((root/"content/episodes").glob("*.json"))+list((root/"state/scheduled").glob("*.json"))
    paths += [p for folder in local.glob("nov*") if folder.is_dir() and not folder.is_symlink() for p in folder.glob("fm_*.json") if not p.name.endswith(".release.json")]
    rows=[];errors=0
    for p in sorted(set(paths)):
        if p.is_symlink() or not p.is_file() or p.stat().st_size>2000000:errors+=1;continue
        try:d=load(p)
        except (ValueError,OSError,UnicodeError):errors+=1;continue
        if type(d) is not dict:errors+=1;continue
        # Do not retain raw local paths/titles in public reports.
        title=d.get("title",d.get("topic",d.get("platform_title","")))
        rows.append((norm(p.stem.replace("_"," ")),norm(title) if type(title) is str else ""))
    return rows,errors
def duplicate(topic,rows):
    aliases=[norm(x) for x in topic["aliases"]]
    target=norm(topic["title"])
    # Whole phrase matching, exact title, and near-title token overlap.
    flags=0
    for eid,title in rows:
        eid,title=norm(eid),norm(title)
        words=set(title.split());base=set(target.split())
        if title==target or any(" "+a+" " in " "+eid+" "+title+" " for a in aliases) or (len(base&words)>=5 and len(base&words)/max(1,len(base|words))>=.65):flags+=1
    return flags
def screen_topics(topics,rows):
    flags={t['id']:duplicate(t,rows) for t in topics}
    need(not any(flags.values()),'Historical duplicate candidate; choose a different topic before generation')
    return flags
def experiment(key,root):
    root.mkdir(parents=True,exist_ok=False)
    if key=="zip_crc":
        intact=root/"intact.zip";broken=root/"broken.zip";payload=b"FLOWMINUTE TEST DATA"
        with zipfile.ZipFile(intact,"w",compression=zipfile.ZIP_STORED) as z:z.writestr("note.txt",payload)
        data=intact.read_bytes();need(data.count(payload)==1,"fixture ambiguity")
        pos=data.index(payload);broken.write_bytes(data[:pos]+bytes([data[pos]^1])+data[pos+1:])
        with zipfile.ZipFile(broken) as z:listing=z.namelist();bad=z.testzip()
        with zipfile.ZipFile(intact) as z:good=z.testzip()
        need(listing==["note.txt"] and bad=="note.txt" and good is None,"ZIP fixture failed")
        return {"archive_opens":True,"entries":listing,"broken_testzip":bad,"intact_testzip":good,"changed_payload_bytes":1,"crc_not_authenticity":True}
    if key=="sql_null":
        db=sqlite3.connect(":memory:")
        try:
            db.executescript("CREATE TABLE customers(id INTEGER); INSERT INTO customers VALUES(1),(2),(3),(4); CREATE TABLE blocked(id INTEGER); INSERT INTO blocked VALUES(2),(NULL);")
            q=lambda s:[list(x) for x in db.execute(s)]
            bad=q("SELECT id FROM customers WHERE id NOT IN (SELECT id FROM blocked) ORDER BY id")
            truth=q("SELECT id,id NOT IN (SELECT id FROM blocked) FROM customers ORDER BY id")
            fixed=q("SELECT c.id FROM customers c WHERE NOT EXISTS (SELECT 1 FROM blocked b WHERE b.id=c.id) ORDER BY c.id")
            filtered=q("SELECT id FROM customers WHERE id NOT IN (SELECT id FROM blocked WHERE id IS NOT NULL) ORDER BY id")
            db.execute("INSERT INTO customers VALUES(NULL)")
            outer=q("SELECT c.id FROM customers c WHERE NOT EXISTS (SELECT 1 FROM blocked b WHERE b.id=c.id) ORDER BY c.id")
            strict=q("SELECT c.id FROM customers c WHERE c.id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM blocked b WHERE b.id=c.id) ORDER BY c.id")
            need(bad==[] and truth==[[1,None],[2,0],[3,None],[4,None]] and fixed==filtered==strict==[[1],[3],[4]] and outer==[[None],[1],[3],[4]],"SQL fixture failed")
            return {"sqlite_version":sqlite3.sqlite_version,"not_in":bad,"truth_values":truth,"not_exists":fixed,"filtered_not_in":filtered,"outer_null_included":outer,"explicit_non_null":strict}
        finally:db.close()
    if key=="path_suffix":
        original=root/"report.csv";original.write_bytes(b"number\n42\n");before=sha(original);new=original.with_suffix(".txt")
        paths=[original.exists(),new.exists()];need(paths==[True,False],"suffix changed disk")
        need(not new.exists(),"destination exists");original.rename(new)
        after=[original.exists(),new.exists()];need(after==[False,True] and sha(new)==before,"rename failed")
        return {"original_name":"report.csv","returned_path":"report.txt","exists_after_with_suffix":paths,"exists_after_rename":after,"content_sha256_before":before,"content_sha256_after":sha(new),"format_unchanged":True}
    raise ValueError("Unregistered fixture")
def prepare(day,root,local,out):
    day=parse_day_ist(day).isoformat();topics=load(D/"RC9_TOPIC_BANK.json")
    need(len(topics)==3 and [x["slot"] for x in topics]==[s[0] for s in PUBLISH_SLOTS],"slot mapping")
    rows,errors=inventory(root,local);need(rows,"no historical inventory")
    flags_by_topic=screen_topics(topics,rows)
    out.mkdir(parents=True,exist_ok=False);result=[]
    for topic,slot in zip(topics,PUBLISH_SLOTS):
        key=topic["id"];flags=flags_by_topic[key];folder=out/key;folder.mkdir()
        evidence=experiment(key,folder/"fixture")
        (folder/"experiment.json").write_text(json.dumps(evidence,indent=2)+"\n",encoding="utf8")
        spec={"version":"1.0.0-rc9","candidate_id":key,"voice":"af_heart","language":"en-us","fps":30,"sample_rate":48000,"review_only":True,
              "scenes":[{"id":role,"text":spoken,"speed":1.04 if role=="hook" else 1.03,"pause_ms":80 if role=="hook" else 200} for role,title,spoken,action in topic["scenes"]]}
        (folder/"narration_spec.json").write_text(json.dumps(spec,indent=2)+"\n",encoding="utf8")
        result.append({"id":key,"episode_id":"fm_"+day.replace("-","")+"_"+key+"_"+topic["format"],"slot":slot[0],"format":slot[1],"reference_local_time":slot[2],"title":topic["title"],"source_url":topic["source_url"],"editorial_rationale":topic["rationale"],"historical_duplicate_flags":flags,"experiment":evidence,"experiment_sha256":sha(folder/"experiment.json"),"narration_spec_sha256":sha(folder/"narration_spec.json"),"release_authorized":False})
    report={"version":"1.0.0-rc9-phase2","review_date_ist":day,"status":"FRESH_LOCAL_DEMOS_RESEARCH_HANDOFF_HOLD","historical_manifest_rows":len(rows),"unreadable_manifests":errors,"inventory_scope":"repository episodes/schedule receipts and local dated episode manifests; not full channel inventory","live_title_inventory_complete":False,"source_research":"official reference pages manually checked 2026-11-27; no measured demand or trending score","topics":result,"topic_bank_sha256":sha(D/"RC9_TOPIC_BANK.json"),"release_ready_count":0,"youtube_uploads":0,"youtube_schedules":0}
    (out/"RC9_TOPIC_RESEARCH_QA.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
    print(json.dumps(report,indent=2));return report
def main():
    p=argparse.ArgumentParser();p.add_argument("--day",required=True);p.add_argument("--local",type=Path,required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args();prepare(a.day,ROOT,a.local,a.out)
if __name__=="__main__":main()
