"""RC9 actual capture and final media review via the existing Branch 1 validator."""
import argparse,json
from pathlib import Path
from production_review_rc6 import read,sha,exact,need,inspect_video,inspect_audio
from autopilot.branch1_recovery import verify_capture,validate_creative
from autopilot.branch1_windows_capture import SCHEMA,METHOD,brief_digest
from autopilot.daily_cloud_plan import PUBLISH_SLOTS,parse_day_ist
from scripts.publish_youtube import approval_allows_exact_video
D=Path(__file__).resolve().parent
PILOTS={
 "sha256":("RC8_SHA_CAPTURE_QA.json","RC8_SHA_SHORT_QA.json","RC8_SHA_CREATIVE_BRIEF.json","render_live_sha_rc8.py","sha-live-rc8/SHA_LIVE_CAPTURE.mp4","sha-continuous-rc8/SHA_CONTINUOUS_REVIEW.mp4"),
 "float":("RC8_LIVE_CAPTURE_QA.json","RC8_LIVE_SHORT_QA.json","RC8_CREATIVE_BRIEF.json","render_live_float_rc8.py","float-live-rc8-fixed/FLOAT_LIVE_CAPTURE.mp4","float-continuous-rc8/FLOAT_CONTINUOUS_REVIEW.mp4"),
 "git":("RC8_GIT_CAPTURE_QA.json","RC8_GIT_LONG_QA.json","RC8_GIT_CREATIVE_BRIEF.json","render_live_git_rc8.py","git-live-rc8-final/GIT_LIVE_CAPTURE.mp4","git-continuous-rc8/GIT_CONTINUOUS_REVIEW.mp4")
}
def receipt_for(brief,c,capture,evidence):
    return {"schema":SCHEMA,"episode_id":brief["episode_id"],"capture_method":METHOD,
            "capture_sha256":c["capture_sha256"],"capture_bytes":capture.stat().st_size,
            "brief_sha256":brief_digest(brief),"evidence_sha256":sha(evidence),
            "private_data":False,"release_approved":False,"youtube_uploads":0}
def verify_pilot(kind,root,out,ffmpeg):
    cn,rn,bn,source,cp,vp=PILOTS[kind]
    evidence=D/cn;c,r,b=map(read,(cn,rn,bn));capture=root/cp;video=root/vp
    need(r["pilot"]==kind and r["release_authorized"] is False and r["human_playback_approved"] is False and r["pcm_identical"] is True and r["full_decode_pass"] is True,"HISTORICAL_REVIEW_FENCE")
    need(r["capture_sha256"]==c["capture_sha256"] and r["capture_report_sha256"]==sha(evidence),"CAPTURE_REPORT_LINK")
    exact(D/bn,r["creative_brief_sha256"]);exact(D/source,r["source_sha256"])
    need(validate_creative(b)==r["creative_schema_result"],"CREATIVE_REPORT_LINK")
    receipt=receipt_for(b,c,capture,evidence)
    rp=out/(kind+"_receipt.json")
    with rp.open("x",encoding="utf-8") as f:json.dump(receipt,f,indent=2);f.write("\n")
    identity=verify_capture(b,capture,rp,windows_evidence=evidence)
    exact(video,r["mp4_sha256"])
    cf=inspect_video(capture,c["dimensions"],c["fps"],c["frames"],ffmpeg,False)
    vf=inspect_video(video,r["resolution"],30,r["frames"],ffmpeg,True)
    need(r["resolution"]==([1920,1080] if b["format"]=="long" else [1080,1920]) and abs(vf/30-b["duration_seconds"])<.001,"FINAL_FORMAT")
    audio=inspect_audio(video,ffmpeg,vf*1600)
    need(audio["decoded_samples"]==r["audio"]["decoded_samples"],"AUDIO_REPORT_LINK")
    need(not approval_allows_exact_video({"approved_video_sha256":r["mp4_sha256"]},r["mp4_sha256"]),"UNSIGNED_ACCEPTANCE")
    result={"pilot":kind,"format":b["format"],"episode_id":b["episode_id"],"video_sha256":r["mp4_sha256"],
            "capture_receipt":receipt,"identity":identity,"capture_report_sha256":sha(evidence),"render_report_sha256":sha(D/rn),
            "creative_brief_sha256":sha(D/bn),"capture_decoded_frames":cf,"final_decoded_frames":vf,"audio":audio,
            "technical_review_pass":True,"structured_creative_pass":True,"publisher_unsigned_rejected":True,"release_authorized":False}
    print("Verified "+kind,flush=True);return result
def build(day,rows):
    date=parse_day_ist(day).isoformat()
    need(set(rows)==set(PILOTS),"MISSING_PILOTS")
    need(len({r["video_sha256"] for r in rows.values()})==3 and len({r["episode_id"] for r in rows.values()})==3,"DUPLICATE_MEDIA")
    order={"short_am":"sha256","long":"git","short_pm":"float"};slots=[]
    for slot,fmt,clock,label in PUBLISH_SLOTS:
        r=rows[order[slot]]
        need(r["format"]==fmt and r["technical_review_pass"] is True and r["structured_creative_pass"] is True and r["release_authorized"] is False and r["publisher_unsigned_rejected"] is True,"REVIEW_SLOT")
        slots.append({"slot":slot,"reference_local_time":clock,**r,"disposition":"HOLD_NOT_SCHEDULED"})
    return {"version":"1.0.0-rc9-phase1","review_date_ist":date,"status":"TECHNICAL_AND_STRUCTURED_CREATIVE_REVIEW_PASS_HOLD","slots":slots,"technical_pass_count":3,"structured_creative_pass_count":3,"release_ready_count":0,
            "inventory_checked_live":False,"fresh_topics_generated":False,"auto_publish_enabled":False,"owner_approval":False,"youtube_uploads":0,"youtube_schedules":0}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--day",required=True);p.add_argument("--media-root",type=Path,required=True);p.add_argument("--ffmpeg",required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args()
    parse_day_ist(a.day);a.out.mkdir(parents=True,exist_ok=False)
    rows={k:verify_pilot(k,a.media_root.absolute(),a.out,a.ffmpeg) for k in PILOTS}
    result=build(a.day,rows)
    (a.out/"RC9_BATCH_QA.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="slots"},indent=2))
if __name__=="__main__":main()
