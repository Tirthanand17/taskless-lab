"""Assemble a verified, review-only fresh two-Short/one-long batch; no publisher calls."""
import argparse,json,re
from pathlib import Path
from production_review_rc6 import read,sha,exact,need
from autopilot.branch1_recovery import verify_capture,validate_creative
from autopilot.daily_cloud_plan import PUBLISH_SLOTS,parse_day_ist
from scripts.publish_youtube import approval_allows_exact_video
D=Path(__file__).resolve().parent
KEYS=("zip_crc","sql_null","path_suffix")
def load(p):return json.loads(p.read_text(encoding="utf8"))
def verify_row(key,folder,capdir,renderdir,day):
    long=key=="sql_null"
    n=load(folder/"audio/NARRATION_REVIEW_QA.json");r=load(renderdir/("NEW_LONG_QA.json" if long else "NEW_SHORT_QA.json"))
    c=load(capdir/"LIVE_CAPTURE_QA.json");brief=load(renderdir/"CREATIVE_BRIEF.json")
    final=renderdir/("NEW_DAILY_LONG_REVIEW.mp4" if long else "NEW_DAILY_SHORT_REVIEW.mp4")
    need(r["topic"]==key and c["topic"]==key and r["episode_id"]==brief["episode_id"]=="fm_"+day.replace("-","")+"_"+key+"_"+brief["format"],"episode mismatch")
    need(brief["format"]==("long" if long else "short"),"format mismatch")
    need(n["asr_screen_pass"] is True and r["full_decode_pass"] is True and not n["release_authorized"] and not c["release_authorized"] and not r["release_authorized"] and not r["human_playback_approved"],"review fence")
    exact(folder/"narration_spec.json",n["spec_sha256"]);exact(folder/"audio/narration.wav",n["narration_sha256"])
    exact(folder/"audio/word_captions.json",n["word_captions_sha256"])
    exact(folder/"audio/NARRATION_REVIEW_QA.json",r["narration_report_sha256"]);exact(capdir/"LIVE_CAPTURE_QA.json",r["capture_report_sha256"])
    exact(renderdir/"CREATIVE_BRIEF.json",r["creative_brief_sha256"]);exact(renderdir/"CAPTURE_RECEIPT.json",r["receipt_sha256"])
    exact(final,r["mp4_sha256"])
    src="render_daily_rc9.py" if key=="path_suffix" else "render_daily_sql_rc9p3.py" if long else "render_daily_rc9p3.py"
    exact(D/src,r["render_source_sha256"])
    for name,h in c["source_sha256"].items():
        need(re.fullmatch("[A-Za-z0-9_]+[.]py",name) is not None,"source name");exact(D/name,h)
    need(r["spec_sha256"]==n["spec_sha256"] and r["capture_sha256"]==c["capture_sha256"] and c["narration_report_sha256"]==r["narration_report_sha256"],"cross-report mismatch")
    identity=verify_capture(brief,capdir/"DAILY_LIVE_CAPTURE.mp4",renderdir/"CAPTURE_RECEIPT.json",windows_evidence=capdir/"LIVE_CAPTURE_QA.json")
    need(identity==r["identity"] and r["resolution"]==([1920,1080] if long else [1080,1920]) and r["fps"]==30 and r["audio"]["decoded_samples"]==r["frames"]*1600 and r["audio"]["clipped_samples"]==0,"technical report mismatch")
    if long:
        exact(renderdir/"CAPTION_REVIEW.json",r["caption_review_sha256"])
        need(load(renderdir/"CAPTION_REVIEW.json")["corrected_tokens_match_script"] is True,"SQL captions not corrected")
    need(not approval_allows_exact_video({"approved_video_sha256":sha(final)},sha(final)),"unsigned accepted")
    return {"topic":key,"episode_id":brief["episode_id"],"title":brief["title"],"format":brief["format"],"duration_seconds":r["duration_seconds"],"frames":r["frames"],"video_sha256":r["mp4_sha256"],"capture_sha256":r["capture_sha256"],"render_report_sha256":sha(renderdir/("NEW_LONG_QA.json" if long else "NEW_SHORT_QA.json")),"audio":r["audio"],"identity":identity,"technical_review_pass":True,"release_authorized":False}
def build(day,rows):
    day=parse_day_ist(day).isoformat()
    need(set(rows)==set(KEYS),"missing topics")
    need(len({x["episode_id"] for x in rows.values()})==len({x["video_sha256"] for x in rows.values()})==len({x["capture_sha256"] for x in rows.values()})==3,"duplicate video/capture")
    slots=[]
    for key,(slot,fmt,clock,_) in zip(KEYS,PUBLISH_SLOTS):
        x=rows[key];need(x["topic"]==key and x["format"]==fmt and x["technical_review_pass"] is True and x["release_authorized"] is False,"slot hold")
        slots.append({"slot":slot,"reference_local_time":clock,**x,"disposition":"HOLD_NOT_SCHEDULED"})
    return {"version":"1.0.0-rc9-phase3","review_date_ist":day,"slots":slots,"fresh_video_count":3,"technical_review_pass_count":3,"live_inventory_complete":False,"human_playback_approved":False,"unattended_generation_verified":False,"release_ready_count":0,"youtube_uploads":0,"youtube_schedules":0}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--day",required=True);p.add_argument("--path",type=Path,required=True);p.add_argument("--zip",type=Path,required=True);p.add_argument("--sql",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    day=parse_day_ist(a.day).isoformat()
    rows={}
    for key,folder,cap,render in [("path_suffix",a.path,"capture-r2","render-r2"),("zip_crc",a.zip,"capture","render"),("sql_null",a.sql,"capture","render")]:
        rows[key]=verify_row(key,folder,folder/cap,folder/render,day)
    result=build(day,rows)
    with a.output.open("x",encoding="utf8") as f:json.dump(result,f,indent=2);f.write("\n")
    print(json.dumps({k:v for k,v in result.items() if k!="slots"},indent=2))
if __name__=="__main__":main()
