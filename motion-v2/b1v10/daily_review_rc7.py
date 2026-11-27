"""RC7 daily review intake: generic Windows capture receipt format and exact media binding.

This is an offline adapter to the existing daily slot planner, NOT a publisher.
A receipt states provenance; hashes alone cannot authenticate a recording or an owner.
Only the known committed pilot catalog has a reviewed evidence anchor in this run.
"""
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path
from production_review_rc6 import CATALOG,read,sha,exact,need,inspect_video,inspect_audio
D=Path(__file__).resolve().parent
ROOT=D.parents[1]
sys.path.insert(0,str(ROOT))
from autopilot.daily_cloud_plan import parse_day_ist,PUBLISH_SLOTS
from scripts.publish_youtube import approval_allows_exact_video
SCHEMA="FLOWMINUTE_WINDOWS_CAPTURE_REVIEW_V1"
FIELDS={"schema","episode_id","method","capture_sha256","capture_bytes","dimensions","fps","frames","source_receipt_sha256","fixture_only","local_only","release_authorized"}
def hex64(v):return type(v) is str and re.fullmatch("[a-f0-9]{64}",v) is not None
def validate_receipt(receipt,capture,anchor=None):
    need(type(receipt) is dict and set(receipt)==FIELDS,"WINDOWS_RECEIPT_SCHEMA")
    r=receipt
    need(r["schema"]==SCHEMA and r["method"]=="windows_classic_console_window_only_live","WINDOWS_METHOD")
    need(type(r["episode_id"]) is str and re.fullmatch("fm_[a-z0-9_]{8,64}",r["episode_id"]) is not None,"EPISODE_ID")
    need(r["fixture_only"] is True and r["local_only"] is True and r["release_authorized"] is False,"SCOPE_OR_APPROVAL")
    need(type(r["capture_bytes"]) is int and 30000<=r["capture_bytes"]<=100000000 and capture.stat().st_size==r["capture_bytes"],"CAPTURE_SIZE")
    need(type(r["dimensions"]) is list and len(r["dimensions"])==2 and all(type(x) is int and 250<=x<=4096 and x%2==0 for x in r["dimensions"]),"DIMENSIONS")
    need(type(r["fps"]) is int and 1<=r["fps"]<=60 and type(r["frames"]) is int and 1<=r["frames"]<=r["fps"]*1200,"CAPTURE_CLOCK")
    need(hex64(r["source_receipt_sha256"]),"SOURCE_RECEIPT_HASH")
    exact(capture,r["capture_sha256"])
    if anchor is not None:
        need(r==anchor,"REVIEWED_CATALOG_ANCHOR_MISMATCH")
    return {"identity_verified":True,"known_evidence_anchor_matched":anchor is not None,"release_authorized":False}
def catalog_receipt(kind,capture):
    name=CATALOG[kind][0];c=read(name)
    need(c["release_authorized"] is False and c["legacy_xvfb_receipt_compatible"] is False,"INVALID_CATALOG_SCOPE")
    return {"schema":SCHEMA,"episode_id":"fm_rc7_"+kind+"_pilot","method":c.get("capture_method",c.get("method")),
            "capture_sha256":c["capture_sha256"],"capture_bytes":capture.stat().st_size,"dimensions":c["dimensions"],
            "fps":c["fps"],"frames":c.get("decoded_frames",c.get("frames")),"source_receipt_sha256":sha(D/name),
            "fixture_only":True,"local_only":True,"release_authorized":False}
def rows_for(root,ffmpeg,editorial):
    previous={x["pilot"]:x for x in read("RC7_OPENING_QA.json")["pilots"]}
    revised={x["pilot"]:x for x in editorial["pilots"]}
    specs={"sha256":("real-capture-rc2-hd/ACTUAL_SHA256_CONSOLE.mp4","editorial-sha-rc7/EDITORIAL_REVIEW.mp4"),
           "float":("float-capture-rc5/FLOAT_CAPTURE.mp4","editorial-float-rc7/EDITORIAL_REVIEW.mp4"),
           "git":("git-capture-rc3/ACTUAL_GIT_CONSOLE.mp4","proof-git-rc7/PROOF_FIRST_REVIEW.mp4")}
    rows={}
    for kind,(cap,vid) in specs.items():
        capture=root/cap;video=root/vid;old=previous[kind];r=revised.get(kind,old)
        need(r["release_authorized"] is False and r["legacy_creative_pass"] is False and r["pcm_identical"] is True,"REVIEW_FENCE")
        if kind!="git":need(r["prior_sha256"]==old["mp4_sha256"],"EDITORIAL_LINK")
        anchor=catalog_receipt(kind,capture);receipt_check=validate_receipt(anchor,capture,anchor)
        exact(video,r["mp4_sha256"])
        inspect_video(capture,anchor["dimensions"],anchor["fps"],anchor["frames"],ffmpeg,False)
        inspect_video(video,r["resolution"],30,r["frames"],ffmpeg,True)
        audio=inspect_audio(video,ffmpeg,r["audio"]["decoded_samples"])
        need(not approval_allows_exact_video({"approved_video_sha256":r["mp4_sha256"]},r["mp4_sha256"]),"UNSIGNED_ACCEPTANCE")
        rows[kind]={"pilot":kind,"format":CATALOG[kind][3],"episode_id":anchor["episode_id"],"capture_receipt":anchor,
          "receipt_validation":receipt_check,"video_sha256":r["mp4_sha256"],"duration_seconds":r["frames"]/30,
          "audio":audio,"technical_review_pass":True,"opening_evidence_seconds":0,"legacy_creative_pass":False,
          "continuous_live_action_verified":False,"release_authorized":False}
        print("Verified "+kind,flush=True)
    return rows
def build(day,rows):
    date=parse_day_ist(day).isoformat()
    need(set(rows)=={"sha256","float","git"},"THREE_DISTINCT_PILOTS_REQUIRED")
    need(len({r["video_sha256"] for r in rows.values()})==3 and len({r["episode_id"] for r in rows.values()})==3,"DUPLICATE_MEDIA")
    order={"short_am":"sha256","long":"git","short_pm":"float"}
    slots=[]
    for slot,fmt,clock,label in PUBLISH_SLOTS:
        r=rows[order[slot]]
        need(r["format"]==fmt and r["technical_review_pass"] is True and r["release_authorized"] is False and r["legacy_creative_pass"] is False,"SLOT_OR_APPROVAL")
        slots.append({"slot":slot,"format":fmt,"reference_local_time":clock,**r,"disposition":"HOLD_NOT_SCHEDULED"})
    return {"schema":"FLOWMINUTE_B1_DAILY_LOCAL_REVIEW_V1","review_date_ist":date,"status":"REVIEW_BATCH_HOLD",
      "channel":"FlowMinute Lab","slots":slots,"technical_pass_count":3,"release_ready_count":0,
      "inventory_checked_live":False,"fresh_topic_research_completed":False,"owner_approval":False,
      "blockers":["Fresh source/topic and channel inventory/duplicate verification","Existing creative policy including actual action, fix, payoff and takeaway","Full exact-video playback, pronunciation and mobile review","Factual and rights review","Exact signed approval and existing publisher handoff"],
      "windows_receipt_scope":"identity and catalog-linked review only; not authentication or legacy Linux receipt compatibility",
      "measurement_windows_hours":[24,72,168],"auto_publish_enabled":False,"youtube_uploads":0,"youtube_schedules":0}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--day",required=True);p.add_argument("--media-root",type=Path,required=True);p.add_argument("--ffmpeg",required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    parse_day_ist(a.day)
    result=build(a.day,rows_for(a.media_root.absolute(),a.ffmpeg,read("RC7_EDITORIAL_QA.json")))
    with a.output.open("x",encoding="utf-8") as f:json.dump(result,f,indent=2);f.write("\n")
    print(json.dumps({"status":result["status"],"technical_pass_count":3,"release_ready_count":0,"slots":[[s["slot"],s["pilot"]] for s in result["slots"]]},indent=2))
if __name__=="__main__":main()
