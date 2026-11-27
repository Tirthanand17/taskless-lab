"""Bind the polished RC11 review batch to original approved-for-review evidence; never publish."""
import argparse,json
from pathlib import Path
from production_review_rc6 import read,sha,exact,need
from run_daily_rc10 import save
from scripts.publish_youtube import approval_allows_exact_video
D=Path(__file__).resolve().parent
MAP=[("shared_lists","SHARED","SHORT"),("outer_join_filter","JOIN","LONG"),("group_runs","GROUP","SHORT")]
def audit(workspace,out):
    prior=read("RC10_SECOND_BATCH_QA.json");slots=[]
    for (topic,prefix,fmt),old in zip(MAP,prior["slots"]):
        need(topic==old["topic"],"slot mismatch")
        folder=workspace/topic/"polish-rc11";report=folder/("RC11_"+fmt+"_QA.json");r=json.loads(report.read_text(encoding="utf8"))
        mp4=folder/("RC11_POLISHED_"+fmt+".mp4")
        exact(mp4,r["video_sha256"])
        exact(D/("polish_long_rc11.py" if fmt=="LONG" else "polish_shorts_rc11.py"),r["source_sha256"])
        exact(D/f"RC10_{prefix}_{fmt}_QA.json",r["prior_report_sha256"])
        exact(folder/"captions.ass",r["caption_ass_sha256"])
        need(r["topic"]==topic and r["prior_sha256"]==old["video_sha256"] and r["capture_sha256"]==old["capture_sha256"] and r["frames"]==old["frames"],"prior link")
        need(r["video_sha256"]!=old["video_sha256"] and r["pcm_identical"] is True and r["full_decode_pass"] is True and r["release_authorized"] is False and r["human_playback_approved"] is False,"review gate")
        need(r["audio"]["decoded_samples"]==r["frames"]*1600 and r["audio"]["clipped_samples"]==0,"audio gate")
        need(r["resolution"]==([1920,1080] if fmt=="LONG" else [1080,1920]) and r["fps"]==30,"format gate")
        need(len(r["source_checks"])==7 and all(x["error"]<4 for x in r["source_checks"]),"evidence samples")
        need(all(f/30>=s-.001 for f,s in zip(r["event_starts_frames"][1:],r["actual_event_times_seconds"])),"premature evidence")
        need(not approval_allows_exact_video({"approved_video_sha256":r["video_sha256"]},r["video_sha256"]),"unsigned accepted")
        slots.append({"topic":topic,"format":old["format"],"slot":old["slot"],"reference_local_time":old["reference_local_time"],"prior_video_sha256":r["prior_sha256"],"video_sha256":r["video_sha256"],"capture_sha256":r["capture_sha256"],"polish_report_sha256":sha(report),"frames":r["frames"],"audio_unchanged":True,"source_scale_gain_percent":round(100*(r["new_source_scale"]/r["prior_source_scale"]-1),2),"caption_gain_percent":round(100*(r["caption_font_px"]/r["prior_caption_font_px"]-1),2),"disposition":"HOLD_NOT_SCHEDULED","release_authorized":False})
    need(len({r["video_sha256"] for r in slots})==3,"duplicate polish")
    result={"version":"1.0.0-rc11-phase2","review_date":"2026-11-29","original_batch_sha256":sha(D/"RC10_SECOND_BATCH_QA.json"),"audit_source_sha256":sha(Path(__file__)),"slots":slots,"polished_count":3,"verified_frames":sum(x["frames"] for x in slots),"release_ready_count":0,"live_inventory_complete":False,"unattended_scheduler_verified":False,"youtube_uploads":0,"youtube_schedules":0}
    need(not out.exists(),"new report required");save(out,result);print(json.dumps(result,indent=2))
def main():
    p=argparse.ArgumentParser();p.add_argument("--workspace",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args();audit(a.workspace.absolute(),a.output.absolute())
if __name__=="__main__":main()
