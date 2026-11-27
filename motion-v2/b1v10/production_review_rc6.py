"""RC6 adapter: verify exact B1v10 Windows capture + final render, then apply legacy policy.
Local review only; never generates an approval, upload, or schedule.
The committed catalog is a review trust anchor, not a signature or a generic receipt format.
"""
from __future__ import annotations
import argparse, hashlib, json, math, re, subprocess, sys, tempfile, wave
from pathlib import Path
import numpy as np
import cv2

D=Path(__file__).resolve().parent
ROOT=D.parents[1]
sys.path.insert(0,str(ROOT))
from autopilot.branch1_recovery import validate_creative, RecoveryRefused, SCHEMA
from scripts.publish_youtube import approval_allows_exact_video
from sound_mix import measure

CATALOG={
 "sha256":("REAL_CAPTURE_QA.json","FOCUS_SHORT_QA.json","NARRATION_REVIEW_QA.json","short","SHA-256: change one byte","https://docs.python.org/3/library/hashlib.html"),
 "float":("FLOAT_CAPTURE_QA.json","FLOAT_SHORT_QA.json","FLOAT_NARRATION_QA.json","short","Why Python float addition looks wrong","https://docs.python.org/3/tutorial/floatingpoint.html"),
 "git":("GIT_CAPTURE_QA.json","FOCUS_LONG_QA.json","LONG_NARRATION_QA.json","long","Find the first failing Git commit","https://git-scm.com/docs/git-bisect"),
}
def need(ok,msg):
    if not ok:raise RecoveryRefused(msg)
def file_ok(p,limit=250_000_000):
    need(p.is_file() and not p.is_symlink() and 0<p.stat().st_size<=limit,"UNSAFE_OR_MISSING_FILE")
def sha(p):
    file_ok(p)
    h=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()
def read(name):
    p=D/name;file_ok(p,200_000)
    return json.loads(p.read_text(encoding="utf-8"))
def exact(p,digest):
    need(type(digest) is str and re.fullmatch("[0-9a-f]{64}",digest) is not None and sha(p)==digest,"EXACT_HASH_MISMATCH")
def verify_catalog(kind,c,r,n):
    need(kind in CATALOG,"UNKNOWN_PILOT")
    need(c["release_authorized"] is False and c["legacy_xvfb_receipt_compatible"] is False and r["release_authorized"] is False,"APPROVAL_OR_METHOD_SPOOF")
    need(c.get("capture_method",c.get("method"))=="windows_classic_console_window_only_live","WINDOWS_METHOD_REQUIRED")
    need(c["capture_sha256"]==r["capture_sha256"],"CAPTURE_RENDER_LINK_MISMATCH")
    need(n["voice"]=="af_heart" and n["release_authorized"] is False,"NARRATION_IDENTITY")
    expected={"sha256":([870,692],120,5,10),"float":([870,494],72,3,4),"git":([870,494],192,8,3)}
    dims,frames,count,err=expected[kind]
    need(c["dimensions"]==dims and c["fps"]==12 and c.get("decoded_frames",c.get("frames"))==frames,"CAPTURE_CLOCK")
    if kind=="sha256":
        need(c["private_data"] is False and c["observed_state_changes"]==3,"SHA_CAPTURE_SCOPE")
        need(c["actual_result"]["sha256_a"]==hashlib.sha256(b"A").hexdigest() and c["actual_result"]["sha256_b"]==hashlib.sha256(b"B").hexdigest() and c["actual_result"]["equal"] is False,"SHA_RESULT")
        exact(D/"sha256_console_demo.py",c["source_sha256"])
        first=min(x["start"] for x in r["panels"])
    elif kind=="float":
        need(c["result"]=={"float_result":"0.30000000000000004","stored_fraction":"3602879701896397/36028797018963968","decimal_result":"0.3"} and min(c["page_deltas"])>.5,"FLOAT_RESULT")
        need(c["source_sha256"].keys()=={"float_console_demo.py","capture_float.py"},"FLOAT_SOURCE_SET")
        for key,digest in c["source_sha256"].items():exact(D/key,digest)
        exact(D/"render_float_short.py",r["source_sha256"])
        exact(D/"FLOAT_NARRATION_QA.json",r["narration_report_sha256"])
        exact(D/"FLOAT_CAPTION_REVIEW.json",r["corrected_captions_sha256"])
        first=n["scene_timeline"][1]["start_frame"]
    else:
        old=read("GIT_BISECT_DEMO.json");g=c["actual_git_result"]
        exact(D/"GIT_BISECT_DEMO.json",c["original_git_evidence_sha256"])
        need(g["commits"]==old["commits"] and g["first_bad_commit"]==old["first_bad_commit"] and g["reset_completed"] is True and [x["revision"] for x in g["steps"]]==[7,11,9,10],"GIT_RESULT")
        need(c["source_sha256"].keys()=={"git_console_demo.py","capture_git_console.py"},"GIT_SOURCE_SET")
        for key,digest in c["source_sha256"].items():exact(D/key,digest)
        first=min(x["start_frame"] for x in r["panels"])
    obs=r["observed_crops"]
    need(len(obs)==count and all(type(x.get("error",x.get("mean_gray_error"))) in (float,int) and 0<=x.get("error",x.get("mean_gray_error"))<err for x in obs),"CROP_EVIDENCE")
    fmt=CATALOG[kind][3]
    need(r["resolution"]==([1080,1920] if fmt=="short" else [1920,1080]) and r["fps"]==30 and r["frames"]==n["frames_at_30fps"] and r["audio_samples"]==n["samples"]==r["frames"]*1600,"FINAL_CLOCK")
    need(r["full_decode_pass"] is True and r["audio_energy"]["clipped_samples"]==0,"HISTORICAL_QA")
    return first
def inspect_video(path,dims,fps,frames,ffmpeg,with_audio):
    file_ok(path)
    c=cv2.VideoCapture(str(path))
    try:
        need(c.isOpened() and [int(c.get(3)),int(c.get(4))]==dims and abs(c.get(5)-fps)<.01,"VIDEO_FORMAT")
    finally:c.release()
    cmd=[ffmpeg,"-nostdin","-v","error","-xerror","-progress","pipe:1","-nostats","-i",str(path),"-map","0:v:0"]
    if with_audio:cmd+=["-map","0:a:0"]
    cmd+=["-f","null","-"]
    p=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=240)
    count=re.findall(r"^frame=(\d+)\s*$",p.stdout,re.M)
    need(bool(count) and int(count[-1])==frames and "progress=end" in p.stdout,"DECODED_FRAME_COUNT")
    return int(count[-1])
def inspect_audio(path,ffmpeg,samples):
    with tempfile.TemporaryDirectory() as t:
        p=Path(t)/"decoded.wav"
        subprocess.run([ffmpeg,"-nostdin","-v","error","-xerror","-i",str(path),"-map","0:a:0","-ar","48000","-ac","1","-c:a","pcm_s16le",str(p)],check=True,timeout=120)
        with wave.open(str(p),"rb") as f:
            need((f.getframerate(),f.getnchannels(),f.getsampwidth(),f.getnframes())==(48000,1,2,samples),"AUDIO_CLOCK")
            v=np.frombuffer(f.readframes(samples),dtype="<i2").astype(np.int32)
        clipped=int(np.sum(np.abs(v)>=32767));need(clipped==0,"AUDIO_CLIPPING")
    loud=measure(ffmpeg,path)
    need(-20<=loud["input_i"]<=-13 and loud["input_tp"]<=-1,"LOUDNESS_OR_PEAK")
    return {"decoded_samples":samples,"clipped_samples":clipped,"loudness":loud}
def legacy_policy(kind,n,first):
    # Truthful scene-derived draft, not a fabricated proof-first brief. An
    # illustrative opening MUST fail the unchanged legacy validator.
    _,_,_,fmt,title,url=CATALOG[kind]
    timeline=n["scene_timeline"]
    roles={"hook":"hook","proof":"demonstration","explain":"cause","setup":"demonstration","start":"demonstration","step1":"demonstration","step2":"demonstration","step3":"demonstration","result":"payoff","limits":"cause","payoff":"takeaway"}
    beats=[{"role":roles[s["id"]],"start_seconds":s["start_frame"]/30,"end_seconds":s["end_frame"]/30,
            "visual_evidence":"illustrative_graphics_or_mixed_capture","spoken_purpose":s["expected"],"action_or_result":"See exact pilot evidence"} for s in timeline]
    brief={"schema":SCHEMA,"episode_id":"fm_rc6_"+kind+"_pilot","format":fmt,"series":"python_automation","duration_seconds":n["duration_seconds"],
           "title":title,"viewer_problem":"Understand the observed software result","viewer_promise":"Explain a reproducible local example","source_url":url,
           "demo":{"mode":"real_software_capture","application":"Python terminal","fixture_only":True,"recording_provenance":"first_party_executed_software","local_only":True},
           "beats":beats,"approval":{"owner_watched_exact_video":False,"rights_reviewed":False,"facts_reviewed":False,"release_signed":False,"youtube_scheduled":False}}
    try:validate_creative(brief)
    except RecoveryRefused as e:rejection=str(e)
    else:raise RecoveryRefused("UNEXPECTED_LEGACY_CREATIVE_ACCEPTANCE")
    return {"creative_pass":False,"legacy_rejection":rejection,"first_recorded_evidence_seconds":first/30,
            "proof_within_two_seconds":first<=60,"first_real_action_by_three_seconds":first<=90,
            "legacy_linux_receipt_compatible":False,"fix_payoff_takeaway_review_pending":True}
def verify(kind,capture,video,ffmpeg):
    cfile,rfile,nfile,*_=CATALOG[kind]
    c,r,n=read(cfile),read(rfile),read(nfile)
    first=verify_catalog(kind,c,r,n)
    exact(capture,c["capture_sha256"]);exact(video,r["mp4_sha256"])
    frames=inspect_video(capture,c["dimensions"],12,c.get("decoded_frames",c.get("frames")),ffmpeg,False)
    final_frames=inspect_video(video,r["resolution"],30,r["frames"],ffmpeg,True)
    audio=inspect_audio(video,ffmpeg,r["audio_samples"])
    need(not approval_allows_exact_video({"approved_video_sha256":r["mp4_sha256"]},r["mp4_sha256"]),"UNSIGNED_PUBLISHER_ACCEPTANCE")
    return {"pilot":kind,"capture_receipt_sha256":sha(D/cfile),"render_report_sha256":sha(D/rfile),"narration_report_sha256":sha(D/nfile),
            "capture_sha256":c["capture_sha256"],"video_sha256":r["mp4_sha256"],"capture_decoded_frames":frames,"video_decoded_frames":final_frames,
            "resolution":r["resolution"],"audio":audio,"capture_identity_verified":True,"technical_review_pass":True,
            "policy":legacy_policy(kind,n,first),"publisher_unsigned_rejected":True,"owner_approval":False,"release_authorized":False}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pilot",choices=CATALOG,required=True);p.add_argument("--capture",type=Path,required=True);p.add_argument("--video",type=Path,required=True);p.add_argument("--ffmpeg",required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    r=verify(a.pilot,a.capture.absolute(),a.video.absolute(),a.ffmpeg)
    with a.output.open("x",encoding="utf-8") as f:json.dump(r,f,indent=2);f.write("\n")
    print(json.dumps(r,indent=2),flush=True)
if __name__=="__main__":main()
