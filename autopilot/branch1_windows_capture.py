"""Windows continuous capture identity checks. No publishing or authentication claims."""
import hashlib,json,math,re
from pathlib import Path
SCHEMA="FLOWMINUTE_B1_WINDOWS_CONTINUOUS_CAPTURE_V2"
METHOD="windows_classic_console_window_only_live"
FIELDS={"schema","episode_id","capture_method","capture_sha256","capture_bytes","brief_sha256","evidence_sha256","private_data","release_approved","youtube_uploads"}
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def brief_digest(brief):return hashlib.sha256(json.dumps(brief,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
def verify_windows(brief,capture,r,evidence,require):
    require(type(r) is dict and set(r)==FIELDS,"WINDOWS_RECEIPT_SCHEMA")
    require(r["schema"]==SCHEMA and r["capture_method"]==METHOD and r["episode_id"]==brief["episode_id"],"WINDOWS_METHOD_OR_EPISODE")
    require(r["private_data"] is False and r["release_approved"] is False and type(r["youtube_uploads"]) is int and r["youtube_uploads"]==0,"WINDOWS_SCOPE")
    require(type(r["capture_bytes"]) is int and r["capture_bytes"]==capture.stat().st_size,"WINDOWS_CAPTURE_SIZE")
    for key in ("capture_sha256","brief_sha256","evidence_sha256"):
        require(type(r[key]) is str and re.fullmatch("[a-f0-9]{64}",r[key]) is not None,"WINDOWS_DIGEST")
    require(digest(capture)==r["capture_sha256"] and brief_digest(brief)==r["brief_sha256"],"WINDOWS_IDENTITY")
    require(evidence is not None and evidence.is_file() and not evidence.is_symlink() and 0<evidence.stat().st_size<=1000000,"WINDOWS_EVIDENCE_REQUIRED")
    require(digest(evidence)==r["evidence_sha256"],"WINDOWS_EVIDENCE_HASH")
    e=json.loads(evidence.read_text("utf8"))
    require(type(e) is dict and e.get("method")==METHOD and e.get("continuous") is True and e.get("scripted_demo") is True and e.get("release_authorized") is False and e.get("capture_sha256")==r["capture_sha256"],"WINDOWS_EVIDENCE_SCOPE")
    fps=e.get("fps");n=e.get("frames");dims=e.get("dimensions")
    require(type(fps) is int and 1<=fps<=60 and type(n) is int and 1<=n<=fps*1201,"WINDOWS_CLOCK")
    require(type(dims) is list and len(dims)==2 and all(type(x) is int and 250<=x<=4096 and x%2==0 for x in dims),"WINDOWS_DIMENSIONS")
    require(abs(n/fps-brief["duration_seconds"])<=1/fps+.05,"WINDOWS_DURATION")
    times=e.get("capture_times_seconds")
    require(type(times) is list and len(times)==n and all(type(x) in (int,float) and math.isfinite(x) and x>=0 for x in times),"WINDOWS_TIMESTAMPS")
    lag=max(abs(t-i/fps) for i,t in enumerate(times))
    require(all(a<=b for a,b in zip(times,times[1:])) and lag<=.35 and type(e.get("max_sample_lag_seconds")) in (int,float) and abs(lag-e["max_sample_lag_seconds"])<=.001,"WINDOWS_TIMING")
    changes=e.get("changes")
    require(type(changes) is list and len(changes)>=6,"WINDOWS_CHANGES")
    for x in changes:
        require(type(x) is dict and set(x)=={"frame","seconds","delta"} and type(x["frame"]) is int and 0<x["frame"]<n and type(x["seconds"]) in (int,float) and abs(x["seconds"]-x["frame"]/fps)<.001 and type(x["delta"]) in (float,int) and .65<x["delta"]<=255,"WINDOWS_CHANGE_RECORD")
    require(all(a["frame"]<b["frame"] for a,b in zip(changes,changes[1:])) and changes[0]["seconds"]<=2 and any(1.5<=x["seconds"]<=3 for x in changes),"WINDOWS_OPENING_ACTION")
    sources=e.get("source_sha256")
    require(type(sources) is dict and 2<=len(sources)<=12,"WINDOWS_SOURCE_SET")
    for name,h in sources.items():
        require(type(name) is str and re.fullmatch("[a-zA-Z0-9_]+[.]py",name) is not None and type(h) is str and re.fullmatch("[a-f0-9]{64}",h) is not None,"WINDOWS_SOURCE_NAME")
        path=evidence.parent/name
        require(path.is_file() and not path.is_symlink() and 0<path.stat().st_size<1000000 and digest(path)==h,"WINDOWS_SOURCE_HASH")
    return {"capture_status":"WINDOWS_EXACT_HASH_VERIFIED_REVIEW_ONLY","capture_sha256":r["capture_sha256"],"capture_method":METHOD,"capture_frames":n,"capture_fps":fps,"capture_dimensions":dims,"measured_log_max_lag_seconds":round(lag,5),"first_recorded_change_seconds":changes[0]["seconds"],"provenance_authenticated":False,"owner_approval":False}
