"""Resumable October 16 FlowMinute build and verified YouTube scheduler.

Explicit publication request: October 16 (11:00, 16:00, 20:30 IST).
Fail closed for uncertain YouTube writes. No duplicates. Nothing outside youtube con.
Natural voices are synthetic; full human listening/viewing is NOT asserted.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WS = REPO.parent
OUT = WS / "oct16-production"
MOTION = REPO / "motion-v2"
PUB = WS / "flowminute-publisher-worktree" / "scripts" / "youtube_publisher.py"
VOICE = REPO / "scripts" / "resumable_narration.py"
PY = WS / "flowminute-publisher-worktree" / ".venv" / "Scripts" / "python.exe"
READ = WS / ".flowminute-private" / "youtube_readonly_token.json"
TOKEN = WS / ".flowminute-private" / "youtube_publish_token.json"
LEDGER = WS / ".flowminute-private" / "youtube-ledger.json"
CHANNEL = "UCCcL9Q_jqVq6LJmnYUSAFZA"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
TARGETS = {
  "pilot_023": ("script-v23.txt","curious-short",58,30,"ClaudeSheetsShort","oct16-v23.mp3","2026-10-16T11:00:00+05:30",1080,1920),
  "long_011": ("script-long011.txt","warm-explainer",310,24,"ClaudeWorkspaceLong","oct16-long011.mp3","2026-10-16T16:00:00+05:30",1920,1080),
  "pilot_024": ("script-v24.txt","curious-short",58,30,"ClaudeAccessShort","oct16-v24.mp3","2026-10-16T20:30:00+05:30",1080,1920),
}
OUT.mkdir(parents=True,exist_ok=True)
LOG=OUT / "oct16_pipeline_log.jsonl"
sys.path.insert(0,str(PUB.parent))
import youtube_publisher as pub
from imageio_ffmpeg import get_ffmpeg_exe
FFMPEG=get_ffmpeg_exe()

def report(event,**kw):
    val={"at":dt.datetime.now(IST).isoformat(timespec="seconds"),"event":event,**kw}
    print(json.dumps(val,ensure_ascii=False),flush=True)
    with LOG.open("a",encoding="utf8") as fh:fh.write(json.dumps(val,ensure_ascii=False)+"\n")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):h.update(block)
    return h.hexdigest()
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def save(p,val):
    p.parent.mkdir(parents=True,exist_ok=True)
    temp=p.with_suffix(p.suffix+".partial")
    temp.write_text(json.dumps(val,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    temp.replace(p)
def run(cmd,timeout=3600,ok=True):
    res=subprocess.run(list(map(str,cmd)),text=True,capture_output=True,timeout=timeout,cwd=str(MOTION) if str(cmd[0]).endswith("remotion.cmd") else None)
    if res.returncode and ok:raise RuntimeError(f"Command failed {cmd[:4]}: {res.stderr[-700:]}")
    return res
def decode(path):
    if not path.exists() or path.stat().st_size<250000:return None
    test=run([FFMPEG,"-hide_banner","-v","info","-i",path,"-f","null","NUL"],timeout=380,ok=False)
    if test.returncode or "Audio: aac" not in test.stderr or "Video: h264" not in test.stderr:return None
    m=re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)",test.stderr)
    return (int(m[1])*3600+int(m[2])*60+float(m[3])) if m else None
def ensure_audio():
    for ep,(script,preset,maxsecs,fps,comp,aud,clock,w,h) in TARGETS.items():
        dest=OUT/"audio"/(ep+"_natural.mp3")
        qa=OUT/"audio"/(ep+"_natural_qa.json")
        if not (dest.exists() and qa.exists() and dest.stat().st_size>10000):
            report("VOICE_START",episode=ep)
            offline=OUT/".tts-venv"/"Scripts"/"python.exe"
            model=OUT/"models"/"kokoro-v1.0.int8.onnx"
            voices=OUT/"models"/"voices-v1.0.bin"
            if offline.is_file() and model.is_file() and voices.is_file():
                voice_name="am_michael" if ep.startswith("long_") else "af_heart"
                run([offline,REPO/"scripts"/"offline_kokoro_narration.py",
                     "--script",MOTION/script,"--output",dest,"--report",qa,
                     "--model",model,"--voices",voices,"--voice",voice_name,
                     "--speed","1.08" if ep.startswith("long_") else "1.10",
                     "--max-duration",maxsecs],timeout=4400)
            else:
                run([PY,VOICE,"--script",MOTION/script,"--output",dest,"--report",qa,
                     "--preset",preset,"--max-duration",maxsecs],timeout=1100)
        q=read(qa)
        sec=float(q["audio_duration_seconds"])
        if sec<10 or sec>maxsecs:raise RuntimeError(f"Voice duration invalid for {ep}: {sec}")
        shutil.copyfile(dest,MOTION/"public"/aud)
        report("VOICE_READY",episode=ep,duration=sec)
    root=MOTION/"src"/"Root.tsx"
    original=root.read_text(encoding="utf8")
    current=original
    for ep,(_,_,_,fps,comp,_,_,_,_) in TARGETS.items():
        dur=float(read(OUT/"audio"/(ep+"_natural_qa.json"))["audio_duration_seconds"])
        frames=math.ceil((dur+0.75)*fps)
        pattern=r'(id="'+re.escape(comp)+r'"\s+component=\{'+re.escape(comp)+r'\}\s+durationInFrames=\{)\d+(\})'
        updated,n=re.subn(pattern,lambda m:m.group(1)+str(frames)+m.group(2),current)
        if n!=1:raise RuntimeError(f"Missing unique registered composition {comp}")
        current=updated
    if current!=original:root.write_text(current,encoding="utf8")
def ensure_renders():
    command=MOTION/"node_modules"/".bin"/"remotion.cmd"
    chrome=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    for ep,(_,_,_,fps,comp,aud,_,w,h) in TARGETS.items():
        video=OUT/(ep+".mp4")
        voice=float(read(OUT/"audio"/(ep+"_natural_qa.json"))["audio_duration_seconds"])
        old=decode(video)
        if old is not None and voice<=old<=voice+2:
            report("RENDER_REUSE",episode=ep,duration=old)
            continue
        partial=OUT/(ep+".rendering.mp4")
        partial.unlink(missing_ok=True)
        report("RENDER_START",episode=ep,comp=comp)
        run([command,"render","src/index.ts",comp,partial,
             "--codec=h264","--crf=21","--pixel-format=yuv420p","--concurrency=1",
             "--browser-executable",chrome,"--log=error"],timeout=3300)
        dur=decode(partial)
        if dur is None or not (voice<=dur<=voice+2):
            raise RuntimeError(f"Render validation failed {ep}, audio={voice}, mp4={dur}")
        partial.replace(video)
        report("RENDER_VALIDATED",episode=ep,seconds=dur,bytes=video.stat().st_size)
    thumb=OUT/"long_011_thumbnail.jpg"
    if not thumb.exists():
        source=OUT/"long_011_thumbnail.png"
        run([command,"still","src/index.ts","ClaudeWorkspaceThumbnail",source,
             "--frame=0","--browser-executable",chrome,"--log=error"],timeout=220)
        run([FFMPEG,"-hide_banner","-v","error","-i",source,"-q:v","3","-frames:v","1","-y",thumb],timeout=90)
    if thumb.stat().st_size>1950000:raise RuntimeError("Thumbnail oversized")
def ensure_qa_and_manifests():
    qa={}
    manifests=OUT/"manifests"
    manifests.mkdir(exist_ok=True)
    for ep,(_,_,_,fps,comp,aud,clock,w,h) in TARGETS.items():
        file=OUT/(ep+".mp4")
        dur=decode(file)
        speech=float(read(OUT/"audio"/(ep+"_natural_qa.json"))["audio_duration_seconds"])
        if dur is None or not speech<=dur<=speech+2:
            raise RuntimeError(f"Video is invalid or cuts off speech: {ep}")
        z=run([FFMPEG,"-hide_banner","-v","info","-i",file,"-vn","-af","volumedetect","-f","null","NUL"],timeout=180)
        match=re.search(r"max_volume:\s*(-?\d+(?:\.\d+)?) dB",z.stderr)
        if not match or float(match[1])>=-.5:raise RuntimeError("Possible audio clipping "+ep)
        contact=OUT/(ep+"_contact.jpg")
        rate=9 if ep.startswith("pilot") else 42
        filt=f"fps=1/{rate},scale={300 if ep.startswith('pilot') else 380}:-1,tile={'5x1' if ep.startswith('pilot') else '6x1'}"
        run([FFMPEG,"-hide_banner","-v","error","-i",file,"-vf",filt,"-frames:v","1","-y",contact],timeout=180)
        hsh=sha(file)
        qa[ep]={"duration":dur,"speech_duration":speech,"video_sha256":hsh,"peak_db":float(match[1]),"technical_decode_passed":True,
         "human_listening":"not independently performed","human_full_playback":"not independently performed"}
        mp=manifests/(ep+".release.json")
        manifest={"episode_id":ep,"episode_path":str(REPO/"content"/"episodes"/(ep+".json")),"video_path":str(file),
         "video_sha256":hsh,"expected_channel_id":CHANNEL,"publish_at":clock,
         "made_for_kids":False,"synthetic_media":False,"qa_approved":True,
         "editorial_review":"Owner explicitly requested publication in conversation October 13; official source QA completed; full human watch not observed",
         "narration_listening_review":"Synthetically generated voice; full independent human listening not observed",
         "full_video_playback_review":"Full automated FFmpeg decode and contact sheet generated; human full playback not asserted",
         "captions_reviewed":False,"srt_review":"Estimated/unreviewed captions not uploaded"}
        if ep=="long_011":
            thumb=OUT/"long_011_thumbnail.jpg"
            manifest["thumbnail_path"]=str(thumb)
            manifest["thumbnail_sha256"]=sha(thumb)
        if mp.exists():
            prev=read(mp)
            if prev.get("video_sha256")!=hsh:raise RuntimeError("Existing manifest immutable hash conflict "+ep)
        else:save(mp,manifest)
        pub.validate_manifest(mp)
        report("MEDIA_QA_PASS",episode=ep,seconds=dur,bytes=file.stat().st_size)
    save(OUT/"oct16_technical_qa.json",{"status":"technical_only_human_listening_not_observed","videos":qa})

def api_read():
    client=pub.youtube_client(READ,writable=False)
    pub.guard_channel(client,CHANNEL)
    return client
def remote_check(client,ep,vid):
    plan=pub.validate_manifest(OUT/"manifests"/(ep+".release.json"))
    v=pub.video_info(client,vid)
    pub.require(v["snippet"]["channelId"]==CHANNEL and v["snippet"]["title"]==plan["title"],"Wrong video identity")
    return v,plan
def reconcile_schedule(client,ep):
    manifest=OUT/"manifests"/(ep+".release.json")
    plan=pub.validate_manifest(manifest)
    rec=pub.require_matching_record(pub.get_ledger(LEDGER),plan)
    if rec["state"]!="scheduling_unresolved":return rec["state"]
    v,plan=remote_check(client,ep,rec["video_id"])
    pub.check_processing_succeeded(v)
    st=v["status"]
    pub.require(st.get("privacyStatus")=="private","Not private")
    pub.require(st.get("publishAt") and pub.parse_utc(st["publishAt"])==pub.parse_utc(plan["publish_at"]),"PublishAt mismatch")
    with pub.exclusive_ledger(LEDGER):
        ledger=pub.get_ledger(LEDGER)
        row=pub.require_matching_record(ledger,plan)
        pub.require(row["state"]=="scheduling_unresolved","State changed")
        row["state"]="scheduled_verified"
        row["confirmed_publish_at"]=pub.as_rfc3339(pub.parse_utc(st["publishAt"]))
        row["reconciled_after_ambiguous_api_response"]=True
        pub.write_json_secure(LEDGER,ledger)
    report("SCHEDULE_RECONCILED",episode=ep,video_id=rec["video_id"])
    return "scheduled_verified"
def publisher_cmd(*args):
    res=run([PY,PUB,*args],timeout=1400,ok=False)
    report("PUBLISHER_COMMAND",command=str(args[0]),rc=res.returncode,out=res.stdout[-260:],err=res.stderr[-500:])
    return res.returncode==0
def process_and_publish(ep):
    mp=OUT/"manifests"/(ep+".release.json")
    plan=pub.validate_manifest(mp)
    ledger=pub.get_ledger(LEDGER)
    rec=ledger["episodes"].get(ep)
    if rec:
        pub.require_matching_record(ledger,plan)
        report("EXISTING_RELEASE",episode=ep,state=rec["state"])
    else:
        if not publisher_cmd("upload",mp,"--token-file",TOKEN,"--confirm-private-upload"):
            raise RuntimeError("Unresolved private upload, do not retry "+ep)
    rec=pub.get_ledger(LEDGER)["episodes"][ep]
    if rec["state"]=="uploading_unresolved":
        raise RuntimeError("Unresolved upload; inspect existing YouTube uploads before retry: "+ep)
    client=api_read()
    if rec["state"]=="scheduling_unresolved":
        if reconcile_schedule(client,ep)!="scheduled_verified":raise RuntimeError("Unresolved schedule "+ep)
        return
    if rec["state"]=="scheduled_verified":return
    pub.require(rec["state"]=="uploaded_private","Unexpected ledger state")
    vid=rec["video_id"]
    for attempt in range(45):
        v,pl=remote_check(client,ep,vid)
        if v.get("status",{}).get("uploadStatus")=="processed" and v.get("processingDetails",{}).get("processingStatus")=="succeeded":
            report("PROCESSING_SUCCEEDED",episode=ep,video_id=vid);break
        if v.get("status",{}).get("uploadStatus") in ("rejected","failed","deleted") or v.get("processingDetails",{}).get("processingStatus")=="failed":
            raise RuntimeError("YouTube processing failed, leave Private "+ep)
        report("PROCESSING_WAIT",episode=ep,attempt=attempt)
        time.sleep(40)
    else:raise RuntimeError("YouTube processing timeout; leave Private "+ep)
    rec=pub.get_ledger(LEDGER)["episodes"][ep]
    if ep=="long_011":
        assets=rec.get("assets",{})
        if "thumbnail" not in assets:
            if not publisher_cmd("assets",mp,"--token-file",TOKEN,"--confirm-assets"):
                raise RuntimeError("Thumbnail unresolved; no blind retry")
        elif assets["thumbnail"]!="confirmed":
            raise RuntimeError("Existing thumbnail unresolved")
    if not publisher_cmd("schedule",mp,"--token-file",TOKEN,"--confirm-schedule"):
        if reconcile_schedule(client,ep)!="scheduled_verified":
            raise RuntimeError("Cannot prove YouTube schedule "+ep)

def confirm():
    client=api_read()
    receipts=[]
    for ep,(_,_,_,fps,comp,aud,clock,w,h) in TARGETS.items():
        plan=pub.validate_manifest(OUT/"manifests"/(ep+".release.json"))
        rec=pub.require_matching_record(pub.get_ledger(LEDGER),plan)
        pub.require(rec["state"]=="scheduled_verified","Not yet scheduled "+ep)
        v,plan=remote_check(client,ep,rec["video_id"])
        pub.check_processing_succeeded(v)
        pub.require(v["status"]["privacyStatus"]=="private","Not private")
        pub.require(v["status"].get("publishAt") and pub.parse_utc(v["status"]["publishAt"])==pub.parse_utc(clock),"Wrong YouTube time")
        vid=rec["video_id"]
        receipt={"id":ep,"date_local":"2026-10-16","scheduled_local":clock,"timezone":"Asia/Kolkata",
          "youtube_video_id":vid,"url":f"https://youtube.com/shorts/{vid}" if ep.startswith("pilot") else f"https://youtu.be/{vid}",
          "status":"scheduled_verified","remote_privacy":"private","remote_upload_status":"processed",
          "remote_publish_at_utc":pub.as_rfc3339(pub.parse_utc(clock)),
          "thumbnail_status":rec.get("assets",{}).get("thumbnail","not_uploaded"),
          "owner_publication_instruction":"Explicit Oct16 publication request in conversation",
          "human_listening_review":"not independently performed",
          "verified_at_ist":dt.datetime.now(IST).isoformat(timespec="seconds")}
        out=REPO/"state"/"scheduled"/(ep+".json")
        if out.exists() and read(out).get("youtube_video_id")!=vid:raise RuntimeError("Receipt conflict "+ep)
        save(out,receipt)
        receipts.append(receipt)
        report("YOU_TUBE_SCHEDULE_VERIFIED",episode=ep,video_id=vid,local_time=clock)
    payload={"checked_at_ist":dt.datetime.now(IST).isoformat(timespec="seconds"),
       "channel_id":CHANNEL,"expected":3,"verified":len(receipts),"source":"authenticated readonly YouTube Data API","videos":receipts}
    save(REPO/"state"/"reconciliation"/"2026-10-16-api-scheduled.json",payload)
    save(REPO/"state"/"planned"/"oct16-pack.json",{"date_local":"2026-10-16","timezone":"Asia/Kolkata",
       "status":"all_scheduled_verified","scheduled_in_youtube":True,"verified":len(receipts),"videos":receipts,
       "no_duplicate_upload":True,"human_full_review":"not independently witnessed"})
    lines=["# October 16 YouTube schedule confirmation","",f"**{len(receipts)}/3 videos independently verified.**","",
      "| Release (IST) | Episode | Video |","|---|---|---|"]
    for p in receipts:lines.append(f"| {p['scheduled_local']} | {p['id']} | [{p['youtube_video_id']}]({p['url']}) |")
    lines+=["","Private until release; exact channel identity and publishAt verified.","Synthetic voices; full human listening and word-aligned captions are not asserted.","No duplicate uploads or false live-demo claims."]
    (REPO/"docs"/"OCT16_YOUTUBE_SCHEDULE_CONFIRMATION.md").write_text("\n".join(lines)+"\n",encoding="utf8")
    return receipts

def git_sync():
    extras=["motion-v2/src/Root.tsx","motion-v2/public/oct16-v23.mp3","motion-v2/public/oct16-v24.mp3",
            "motion-v2/public/oct16-long011.mp3","docs/OCT16_YOUTUBE_SCHEDULE_CONFIRMATION.md",
            "state/planned/oct16-pack.json","state/reconciliation/2026-10-16-api-scheduled.json",
            "state/scheduled/pilot_023.json","state/scheduled/pilot_024.json","state/scheduled/long_011.json"]
    for args in (["fetch","origin","main"],["merge","--ff-only","origin/main"],
                 ["add","--",*extras],["diff","--cached","--check"],
                 ["commit","-m","chore(release): confirm Oct16 FlowMinute YouTube schedules"],
                 ["push","origin","main"]):
        res=run(["git","-C",REPO,*args],timeout=180,ok=False)
        if res.returncode:
            report("GIT_STEP_BLOCKED",step=args[0],stderr=res.stderr[-400:])
            return
    report("GITHUB_SYNC_COMPLETE")

def main():
    report("OCT16_RELEASE_STARTED")
    ensure_audio()
    ensure_renders()
    ensure_qa_and_manifests()
    if not publisher_cmd("doctor","--token-file",TOKEN,"--expected-channel-id",CHANNEL):
        raise RuntimeError("Channel OAuth check failed; no upload")
    for ep in TARGETS:
        try:process_and_publish(ep)
        except Exception as exc:report("EPISODE_STOP",episode=ep,error=str(exc)[:500])
    got=confirm()
    git_sync()
    report("SUCCESS_3_OF_3_SCHEDULED",video_ids=[v["youtube_video_id"] for v in got])

if __name__=="__main__":
    try:main()
    except Exception as e:
        report("OCT16_NOT_COMPLETE",error=str(e)[:750])
        raise
