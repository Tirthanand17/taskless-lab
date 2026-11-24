"""Private editorial benchmark: local human event labels, never platform metrics.

Pure timecode comparison, no media input, external accounts or release
authority. This tool cannot verify the provenance of human labels.
"""
from __future__ import annotations

import re

HEX=re.compile(r"[0-9a-f]{64}\Z")


def need(ok, reason):
    if not ok:
        raise ValueError("CLIVOX_V3_BENCHMARK_"+reason)


def windows(items,duration,cap):
    need(type(items) is list and len(items)<=cap,"WINDOWS")
    for w in items:
        need(type(w) is list and len(w)==2 and all(type(x) is int for x in w)
             and 0<=w[0]<w[1]<=duration,"TIME")
    return items


def compare(cases, top_k=5):
    """Same top-k budget for both engines, one-to-one IoU>=0.5 matching.

    Caller must supply held-out episodes only. Results are technical editor
    label agreement, not engagement predictions or licensed-source proof.
    """
    need(type(top_k) is int and 1<=top_k<=20,"TOP_K")
    need(type(cases) is list and 0<len(cases)<=100,"CASES")
    seen=set()
    totals={k:{"proposed":0,"matched":0,"labels":0} for k in ("baseline","v3")}
    per=[]
    for case in cases:
        need(type(case) is dict and set(case)=={"source_sha256","duration_ms","labels","baseline","v3"},
             "FIELDS")
        sha,duration=case["source_sha256"],case["duration_ms"]
        need(type(sha) is str and HEX.fullmatch(sha) is not None and sha not in seen,"SOURCE")
        seen.add(sha)
        need(type(duration) is int and 1<=duration<=7200000,"DURATION")
        labels=windows(case["labels"],duration,1000)
        need(len(labels)==len(set(map(tuple,labels))),"DUPLICATE_LABEL")
        row={"source_sha256":sha}
        for engine in ("baseline","v3"):
            picks=windows(case[engine],duration,20)[:top_k]
            matches={}
            def assign(i,visited):
                a,b=picks[i]
                for j,(c,d) in enumerate(labels):
                    inter=max(0,min(b,d)-max(a,c))
                    union=(b-a)+(d-c)-inter
                    if inter*2<union or j in visited:
                        continue
                    visited.add(j)
                    if j not in matches or assign(matches[j],visited):
                        matches[j]=i
                        return True
                return False
            for i in range(len(picks)):
                assign(i,set())
            item={"proposed":len(picks),"matched":len(matches),"labels":len(labels)}
            for key,val in item.items():
                totals[engine][key]+=val
            row[engine]=item
        per.append(row)
    for t in totals.values():
        t["label_precision"]=round(t["matched"]/t["proposed"],4) if t["proposed"] else None
        t["label_recall"]=round(t["matched"]/t["labels"],4) if t["labels"] else None
    return {"stage":"UNVERIFIED_LOCAL_EDITOR_LABEL_COMPARISON","top_k":top_k,
            "episode_count":len(cases),"per_episode":per,"totals":totals,
            "human_label_provenance_verified":False,"real_benchmark_accepted":False,
            "viral_probability":None,"youtube_upload_authorized":False}
