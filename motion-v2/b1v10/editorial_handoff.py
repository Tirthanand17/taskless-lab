"""Local B1v10 production-research handoff. No publishing, web crawling or model calls."""
from __future__ import annotations
import argparse
from datetime import date
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from autopilot.daily_editorial_board import _subject_tokens

SCORE_KEYS = ("freshness", "audience_fit", "demonstrability", "payoff", "curiosity", "evidence", "originality", "effort")
SLOTS = ("short", "long", "short")
def require(ok, message):
    if not ok:
        raise ValueError(message)
def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
def digest(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()
def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))
def text(value, name):
    require(isinstance(value, str) and 1 <= len(value.strip()) <= 2000, "invalid "+name)
    return value.strip()
def related(a, b):
    a,b = _subject_tokens(a), _subject_tokens(b)
    return bool(a and b and (a == b or (len(a & b) >= 3 and len(a & b)/len(a | b) >= .5)))
def inventory(root, extra=()):
    paths = sorted((root/"content"/"episodes").glob("*.json"))
    require(paths, "repository episode history missing")
    entries=[]
    for path in paths:
        obj=read(path)
        if isinstance(obj,dict) and isinstance(obj.get("title"),str) and obj["title"].strip():
            entries.append(obj["title"])
    require(entries, "no usable historical titles")
    for p in extra:
        obj=read(p)
        rows=obj.get("rows")
        require(isinstance(rows,list) and rows, "invalid extra release receipt")
        for row in rows:
            entries.append(text(row.get("title"),"receipt title"))
    return sorted(set(entries)),len(paths)
def demo_result(key):
    if key=="float":
        return {"expression":"0.1 + 0.2", "float_result":repr(0.1+0.2),
                "decimal_result":str(Decimal("0.1")+Decimal("0.2"))}
    if key=="sha256":
        return {"input_a":"A","input_b":"B","sha256_a":hashlib.sha256(b"A").hexdigest(),
                "sha256_b":hashlib.sha256(b"B").hexdigest()}
    if key=="bisect":
        good,bad,first=0,15,11
        steps=[]
        while bad-good>1:
            mid=(good+bad)//2
            result=mid>=first
            steps.append({"revision":mid,"bad":result})
            if result: bad=mid
            else: good=mid
        return {"mode":"simulated_linear_history","initial_good":0,"initial_bad":15,
                "first_bad":bad,"midpoint_tests":len(steps),"steps":steps}
    raise ValueError("unknown demo")
def validate(c,day):
    for k in ("id","title","family","angle","limitation","demo"):
        text(c.get(k),k)
    require(c.get("format") in SLOTS,"unknown format")
    require(re.fullmatch(r"[a-z0-9-]+",c["id"]) is not None,"bad candidate id")
    scores=c.get("scores")
    require(isinstance(scores,dict) and set(scores)==set(SCORE_KEYS),"invalid rubric")
    require(all(type(v) is int and 0<=v<=5 for v in scores.values()),"invalid score")
    s=c.get("source")
    require(isinstance(s,dict),"source missing")
    for k in ("url","publisher","checked","claim"): text(s.get(k),k)
    u=urlsplit(s["url"])
    require(u.scheme=="https" and bool(u.hostname) and not u.username and not u.password and not u.fragment,"invalid source URL")
    checked=date.fromisoformat(s["checked"])
    require(0 <= (day-checked).days <= 7,"stale or future source review")
    scenes=c.get("scenes")
    require(isinstance(scenes,list) and (4<=len(scenes)<=8 if c["format"]=="short" else 7<=len(scenes)<=20),"invalid scene count")
    require(scenes[0].get("role")=="hook" and scenes[-1].get("role")=="payoff","missing hook or payoff")
    require(scenes[0].get("seconds") in (1,2,3),"hook too late")
    require(any(x.get("role")=="proof" for x in scenes[1:3]),"no early proof")
    for x in scenes:
        require(x.get("role") in ("hook","proof","explain","limitation","payoff"),"invalid role")
        require(type(x.get("seconds")) is int and 1<=x["seconds"]<=30,"invalid scene duration")
        for k in ("headline","visual"): text(x.get(k),k)
        require(x.get("zone") in ("hero","proof"),"invalid visual zone")
        refs=x.get("claim_ids")
        require(isinstance(refs,list) and refs and all(r in ("source","demo") for r in refs),"unknown claim reference")
        require(x.get("asset_origin")=="original_illustration_or_pending_real_capture","unreviewed asset")
    duration=sum(x["seconds"] for x in scenes)
    require(15<=duration<=60 if c["format"]=="short" else 90<=duration<=600,"duration outside pilot range")
    return duration
def build(data, titles, scanned):
    require(data.get("schema")=="B1V10_EDITORIAL_INPUT_V1" and data.get("release_authorized") is False,"invalid input authority")
    require(data.get("mode")=="evergreen_review_fixture" and data.get("demand_observed") is False,"only unmeasured evergreen pilot supported")
    day=date.fromisoformat(data["plan_day"])
    pool=data.get("candidates")
    require(isinstance(pool,list) and 3<=len(pool)<=24,"candidate count outside bounds")
    require(len({c["id"] for c in pool})==len(pool),"duplicate candidate ID")
    eligible=[]; rejected=[]
    for c in pool:
        seconds=validate(c,day)
        if any(related(c["title"],h) for h in titles):
            rejected.append({"id":c["id"],"reason":"historical_title_similarity_review_hold"})
            continue
        eligible.append((sum(c["scores"].values()),c,seconds))
    eligible.sort(key=lambda r:(-r[0],r[1]["id"]))
    picked=[]; used=set()
    for slot in SLOTS:
        chosen=next((row for row in eligible if row[1]["format"]==slot and row[1]["family"] not in used and not any(related(row[1]["title"],p["title"]) for p in picked)),None)
        if chosen is None: continue
        score,c,seconds=chosen
        used.add(c["family"])
        t=0; beats=[]
        for scene in c["scenes"]:
            beats.append({**scene,"start":t,"end":t+scene["seconds"]})
            t+=scene["seconds"]
        picked.append({**c,"score_out_of_40":score,"duration_seconds":seconds,"scenes":beats,
                       "demo_result":demo_result(c["demo"]),"candidate_sha256":digest(c)})
    return {"schema":"B1V10_EDITORIAL_REVIEW_V1","version":"0.3.0","plan_day":day.isoformat(),
            "input_sha256":digest(data),"historical_title_set_sha256":digest(titles),
            "repo_episode_files_scanned":scanned,"distinct_history_titles":len(titles),
            "selected":picked,"rejected":rejected,"unfilled_slots":3-len(picked),
            "history_complete":False,"live_demand_verified":False,"score_type":"manual editorial heuristic, not measured demand",
            "source_claims_independently_approved":False,"actual_assets_approved":False,"release_authorized":False}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("input",type=Path); p.add_argument("output",type=Path)
    p.add_argument("--receipt",type=Path,action="append",default=[])
    args=p.parse_args()
    titles,count=inventory(ROOT,args.receipt)
    result=build(read(args.input),titles,count)
    with args.output.open("x",encoding="utf-8") as f: json.dump(result,f,indent=2,ensure_ascii=False);f.write("\n")
    print("Selected",len(result["selected"]),"of 3; history titles",len(titles),"rejected",len(result["rejected"]),"review only")
if __name__=="__main__": main()
