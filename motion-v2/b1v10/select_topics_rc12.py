"""Rank source-backed evergreen candidates and execute bounded, reusable local demonstrations.

No arbitrary code execution, network scraping, popularity estimates or publisher calls.
"""
import argparse,json,sqlite3,re,datetime
from collections import Counter,deque
from pathlib import Path
from daily_topics_rc9 import inventory,duplicate,load,sha,need
from run_daily_rc10 import save,spec,catalog
from topic_registry_rc10 import topics
from autopilot.daily_cloud_plan import PUBLISH_SLOTS,parse_day_ist
D=Path(__file__).resolve().parent;ROOT=D.parents[1]
BANK="RC12_CANDIDATES.json"
ROLES=("hook","demonstration","cause","fix","payoff","takeaway")
def steps(t):
    """Same six-result interface for every registered operation, actual operations only."""
    op=t["op"];x=t["input"]
    def result(cmd,v):return {"command":cmd,"result":v}
    if op=="strip_compare":
        need(type(x) is str and x=="abcab","fixture");a=x.strip("abc");b=x.removeprefix("abc")
        r=[result("text.strip('abc')",a),result("text",x),result("set('abc')",sorted(set("abc"))),result("text.removeprefix('abc')",b),result("strip vs removeprefix",[a,b]),result("text.endswith('ab')",x.endswith("ab"))]
        need([a,b]==["","ab"],"strip result")
    elif op=="deque_compare":
        need(x==[1,2,3,4],"fixture");d=deque(x[:3],maxlen=3);d.append(x[-1]);v=list(d)
        r=[result("deque(..., maxlen=3)",v),result("input",x),result("queue.maxlen",d.maxlen),result("deque([1,2,3], maxlen=3)",list(deque(x[:3],maxlen=3))),result("queue after append(4)",v),result("oldest retained?",1 in d)]
        need(v==[2,3,4],"queue result")
    elif op=="counter_compare":
        need(x==[2,5],"fixture");a=Counter(a=x[0]);b=Counter(a=x[1]);v=dict(a-b);a.subtract(b);w=dict(a)
        r=[result("Counter(a=2)-Counter(a=5)",v),result("counts",x),result("positive count keys",list(v)),result("a.subtract(b)",w),result("operator vs method",[v,w]),result("negative count kept?",a["a"]<0)]
        need(v=={} and w=={"a":-3},"counter result")
    elif op=="partition_compare":
        need(x=="a:b:c","fixture");a=x.split(":");b=list(x.partition(":"))
        r=[result("text.split(':')",a),result("text",x),result("text.count(':')",x.count(":")),result("text.partition(':')",b),result("partition remainder",b[2]),result("'abc'.partition(':')",list("abc".partition(":")))]
        need(a==["a","b","c"] and b==["a",":","b:c"],"partition result")
    elif op in ("count_compare","union_compare"):
        db=sqlite3.connect(":memory:")
        try:
            if op=="count_compare":
                need(x==[10,None,20,None],"fixture");db.execute("CREATE TABLE t(v)");db.executemany("INSERT INTO t VALUES(?)",[(v,) for v in x])
                q=lambda s:db.execute(s).fetchone()[0]
                a=q("SELECT count(v) FROM t");b=q("SELECT count(*) FROM t");m=q("SELECT count(*)-count(v) FROM t")
                r=[result("SELECT count(v) FROM t",a),result("SELECT v FROM t",[v[0] for v in db.execute("SELECT v FROM t")]),result("SELECT count(v) FROM t",a),result("SELECT count(*) FROM t",b),result("total / recorded / missing",[b,a,m]),result("count(*) = count(v)?",b==a)]
                need([b,a,m]==[4,2,2],"count result")
            else:
                need(x==[["A","B"],["A","C"]],"fixture");db.executescript("CREATE TABLE a(v); CREATE TABLE b(v)");db.executemany("INSERT INTO a VALUES(?)",[(v,) for v in x[0]]);db.executemany("INSERT INTO b VALUES(?)",[(v,) for v in x[1]])
                q=lambda s:[v[0] for v in db.execute(s)]
                a=q("SELECT v FROM a UNION SELECT v FROM b ORDER BY v");b=q("SELECT v FROM a UNION ALL SELECT v FROM b ORDER BY v")
                r=[result("SELECT v FROM a UNION SELECT v FROM b",a),result("source values",x),result("unique row count",len(a)),result("SELECT v FROM a UNION ALL SELECT v FROM b",b),result("unique / all",[len(a),len(b)]),result("both lists equal?",a==b)]
                need(a==["A","B","C"] and b==["A","A","B","C"],"union result")
        finally:db.close()
    else:raise ValueError("unregistered operation")
    return r
def validate(t):
    need(set(t)=={"id","format","title","source_url","aliases","score","input","op","head","spoken","notes"},"candidate fields")
    need(re.fullmatch("[a-z_]+",t["id"]) and t["format"] in ("short","long"),"candidate identity")
    need(t["source_url"].startswith(("https://docs.python.org/3/","https://www.sqlite.org/")),"source allowlist")
    need(type(t["score"]) is list and len(t["score"])==3 and all(type(x) is int and 1<=x<=5 for x in t["score"]),"score")
    for k in ("head","spoken","notes"):
        need(type(t[k]) is list and len(t[k])==6 and all(type(x) is str and 0<len(x)<=500 for x in t[k]),"scene fields")
    need(type(t["aliases"]) is list and t["aliases"] and all(type(x) is str and x.strip() for x in t["aliases"]),"aliases")
    return steps(t)
def select(bank,history,reserved):
    valid=[];rejections=[]
    need(len({t["id"] for t in bank})==len(bank),"duplicate pool ids")
    for t in bank:
        validate(t)
        if t["id"] in reserved or duplicate(t,history):
            rejections.append(t["id"]);continue
        valid.append(t)
    selected=[];used=set()
    for slot,fmt,clock,_ in PUBLISH_SLOTS:
        eligible=sorted((t for t in valid if t["format"]==fmt and t["id"] not in used),key=lambda t:(-sum(t["score"]),t["id"]))
        need(eligible,"candidate pool exhausted for "+slot)
        t=eligible[0];used.add(t["id"])
        selected.append({**t,"slot":slot,"reference_local_time":clock,"scenes":[[role,h,s,"Inspect "+role+" result."] for role,h,s in zip(ROLES,t["head"],t["spoken"])]})
    return selected,rejections
def prepare(day,local,out,prior_reports):
    parse_day_ist(day);need(day>"2026-11-29","existing day reserved")
    bank=load(D/BANK);rows,errors=inventory(ROOT,local);need(rows and not errors,"historical inventory incomplete")
    prior=list(catalog().values())+topics("2026-11-29")
    rows+= [(t["id"],t["title"]+" "+" ".join(t["aliases"])) for t in prior];reserved={t["id"] for t in prior}
    expected_days=set()
    cursor=datetime.date(2026,11,30);end=datetime.date.fromisoformat(day)
    need((end-cursor).days<=31,"replenish candidate pool")
    while cursor<end:
        expected_days.add(cursor.isoformat());cursor+=datetime.timedelta(days=1)
    seen=set();by_id={t["id"]:t for t in bank}
    for path in prior_reports:
        r=load(path);need(r["day"] in expected_days and r["day"] not in seen and r["release_authorized"] is False and r["bank_sha256"]==sha(D/BANK),"prior report scope")
        seen.add(r["day"]);need(len(r["selected"])==3,"prior selection incomplete")
        for t in r["selected"]:
            key=t["topic"];need(key in by_id and key not in reserved and t["title"]==by_id[key]["title"],"prior topic mismatch")
            reserved.add(key);rows.append((key,t["title"]+" "+" ".join(by_id[key]["aliases"])))
    need(seen==expected_days,"missing prior daily selection receipt")
    selected,rejected=select(bank,rows,reserved)
    out.mkdir(parents=True,exist_ok=False);result=[]
    for t in selected:
        folder=out/t["id"];folder.mkdir()
        save(folder/"topic.json",t);save(folder/"experiment.json",steps(t));save(folder/"narration_spec.json",spec(t))
        result.append({"topic":t["id"],"title":t["title"],"slot":t["slot"],"format":t["format"],"source_url":t["source_url"],"editorial_score":sum(t["score"]),"experiment":steps(t),"topic_sha256":sha(folder/"topic.json"),"experiment_sha256":sha(folder/"experiment.json"),"spec_sha256":sha(folder/"narration_spec.json")})
    r={"version":"1.0.0-rc12-phase2","day":day,"candidate_count":len(bank),"history_rows":len(rows),"historical_rejections":rejected,"selected":result,"bank_sha256":sha(D/BANK),"source_sha256":sha(Path(__file__)),"source_review_date":"2026-11-27","ranking_basis":"editorial judgments: surprise, usefulness, visual clarity; not measured audience demand","live_inventory_complete":False,"release_authorized":False}
    save(out/"SELECTION_QA.json",r);print(json.dumps(r,indent=2))
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--day",required=True);p.add_argument("--local",type=Path,required=True);p.add_argument("--out",type=Path,required=True);p.add_argument("--prior-report",type=Path,action="append",default=[]);a=p.parse_args();prepare(a.day,a.local,a.out,a.prior_report)
if __name__=="__main__":main()
