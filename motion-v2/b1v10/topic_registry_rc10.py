"""RC10 date registry and executable, original local experiments."""
import argparse,json,sqlite3
from itertools import groupby
from pathlib import Path
from daily_topics_rc9 import inventory,screen_topics,load,sha,need
from run_daily_rc10 import spec,save,catalog as old_catalog
from autopilot.daily_cloud_plan import PUBLISH_SLOTS,parse_day_ist
D=Path(__file__).resolve().parent;ROOT=D.parents[1]
REGISTRY={"2026-11-29":"RC10_TOPIC_BANK_1129.json"}
def topics(day):
    parse_day_ist(day);need(day in REGISTRY,"No registered fresh topic set")
    rows=load(D/REGISTRY[day]);need(len(rows)==3 and [x["slot"] for x in rows]==[x[0] for x in PUBLISH_SLOTS],"slot order")
    need(len({x["id"] for x in rows})==3,"duplicate keys")
    return rows
def experiment(key):
    if key=="shared_lists":
        d=dict.fromkeys(("a","b"),[]);d["a"].append("item")
        before={k:list(v) for k,v in d.items()};shared=d["a"] is d["b"]
        d={k:[] for k in ("a","b")};d["a"].append("item")
        after={k:list(v) for k,v in d.items()}
        need(before=={"a":["item"],"b":["item"]} and shared and after=={"a":["item"],"b":[]} and d["a"] is not d["b"],"unexpected identity")
        return {"before":before,"shared":shared,"after":after,"independent":d["a"] is not d["b"]}
    if key=="group_runs":
        data=["A","B","A"];groups=lambda x:[[k,list(v)] for k,v in groupby(x)]
        before=groups(data);after=groups(sorted(data));need(len(before)==3 and after==[["A",["A","A"]],["B",["B"]]],"grouping changed")
        return {"input":data,"before":before,"sorted":sorted(data),"after":after}
    if key=="outer_join_filter":
        db=sqlite3.connect(":memory:")
        try:
            db.executescript("CREATE TABLE c(id); INSERT INTO c VALUES(1),(2),(3); CREATE TABLE o(id,status); INSERT INTO o VALUES(1,'paid'),(2,'pending');")
            q=lambda s:[list(x) for x in db.execute(s)]
            base="SELECT c.id,o.status FROM c LEFT JOIN o ON c.id=o.id"
            before=q(base+" WHERE o.status='paid' ORDER BY c.id");allrows=q(base+" ORDER BY c.id");after=q(base+" AND o.status='paid' ORDER BY c.id")
            need(before==[[1,"paid"]] and allrows==[[1,"paid"],[2,"pending"],[3,None]] and after==[[1,"paid"],[2,None],[3,None]],"join result")
            return {"before":before,"joined_rows":allrows,"after":after,"sqlite_version":sqlite3.sqlite_version}
        finally:db.close()
    raise ValueError("unregistered fixture")
def prepare(day,local,out):
    bank=topics(day);rows,errors=inventory(ROOT,local);need(rows and not errors,"historical inventory incomplete")
    prior=list(old_catalog().values())
    # Cross-date topic IDs, titles and aliases must be screened against the previous bank.
    history=rows+[(x["id"],x["title"]+" "+" ".join(x["aliases"])) for x in prior]
    screen_topics(bank,history);need(not ({x["id"] for x in bank}&{x["id"] for x in prior}),"recycled topic id")
    out.mkdir(parents=True,exist_ok=False);results=[]
    for t in bank:
        key=t["id"];folder=out/key;folder.mkdir()
        save(folder/"experiment.json",experiment(key));save(folder/"narration_spec.json",spec(t))
        results.append({"topic":key,"slot":t["slot"],"title":t["title"],"format":t["format"],"source_url":t["source_url"],"experiment":load(folder/"experiment.json"),"experiment_sha256":sha(folder/"experiment.json"),"spec_sha256":sha(folder/"narration_spec.json")})
    report={"day":day,"historical_rows":len(rows),"prior_registered_topics":len(prior),"duplicate_flags":0,"topics":results,"bank_sha256":sha(D/REGISTRY[day]),"live_inventory_complete":False,"release_authorized":False}
    save(out/"TOPIC_QA.json",report);print(json.dumps(report,indent=2))
def main():
    p=argparse.ArgumentParser();p.add_argument("--day",required=True);p.add_argument("--local",type=Path,required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args();prepare(a.day,a.local,a.out)
if __name__=="__main__":main()
