"""Safely finalize October 14 verified schedule receipts; no YouTube writes."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys, json
REPO=Path(__file__).resolve().parents[1]
WS=REPO.parent
sys.path.insert(0,str(WS/"flowminute-publisher-worktree"/"scripts"))
import youtube_publisher as pub

CHANNEL="UCCcL9Q_jqVq6LJmnYUSAFZA"
SLOTS={"pilot_019":"2026-10-14T11:00:00+05:30","long_009":"2026-10-14T16:00:00+05:30","pilot_020":"2026-10-14T20:30:00+05:30"}
def read(path): return json.loads(path.read_text(encoding="utf-8-sig"))
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+".tmp")
    temp.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    temp.replace(path)

api=pub.youtube_client(WS/".flowminute-private"/"youtube_readonly_token.json",writable=False)
pub.guard_channel(api,CHANNEL)
ledger=read(WS/".flowminute-private"/"youtube-ledger.json")["episodes"]
now=datetime.now(timezone(timedelta(hours=5,minutes=30))).isoformat(timespec="seconds")
confirmed=[]
for ep,local in SLOTS.items():
    m=read(WS/"oct14-production"/"manifests"/f"{ep}.release.json")
    meta=read(REPO/"content"/"episodes"/f"{ep}.json")
    led=ledger.get(ep)
    assert led is not None and led["state"]=="scheduled_verified",(ep,"ledger not confirmed")
    assert m["qa_approved"] is True
    assert m["video_sha256"]==led["video_sha256"]
    assert led["title"]==meta["title"] and led["channel_id"]==CHANNEL
    expected=pub.parse_utc(local)
    assert pub.parse_utc(led["confirmed_publish_at"])==expected
    vid=led["video_id"]
    remote=pub.video_info(api,vid)
    assert remote["snippet"]["channelId"]==CHANNEL
    assert remote["snippet"]["title"]==meta["title"]
    assert remote["status"]["privacyStatus"]=="private"
    assert pub.parse_utc(remote["status"]["publishAt"])==expected
    pub.check_processing_succeeded(remote)
    link=f"https://youtube.com/shorts/{vid}" if ep.startswith("pilot_") else f"https://youtu.be/{vid}"
    receipt={"id":ep,"date_local":"2026-10-14","scheduled_local":local,"timezone":"Asia/Kolkata",
     "youtube_video_id":vid,"url":link,"title_in_studio":meta["title"],"status":"scheduled_verified",
     "remote_privacy":"private","remote_upload_status":"processed","remote_processing":"succeeded",
     "remote_publish_at_utc":pub.as_rfc3339(expected),"verified_at_local":now,
     "verified_source":"Authenticated read-only YouTube Data API videos.list",
     "video_sha256":m["video_sha256"],
     "thumbnail_status":led.get("assets",{}).get("thumbnail","not_uploaded"),
     "captions_status":"not_uploaded; draft captions are unreviewed",
     "owner_approval":"Explicit user approval in chat October 13, 2026",
     "human_narration_listening_review":"Not independently performed or asserted",
     "no_duplicate_upload":True}
    path=REPO/"state"/"scheduled"/f"{ep}.json"
    if path.exists():
        old=read(path)
        assert old["youtube_video_id"]==vid,(ep,"conflicting receipt")
    save(path,receipt)
    confirmed.append(receipt)
    print("VERIFIED",ep,vid,local,flush=True)
assert len(confirmed)==3
planpath=REPO/"state"/"planned"/"oct14-pack.json"
plan=read(planpath)
for item in plan["entries"]:
    receipt=next(x for x in confirmed if x["id"]==item["id"])
    item.update({"status":"scheduled_verified","approved":True,
     "owner_approval":"Explicit approval to publish in conversation on October 13",
     "youtube_id":receipt["youtube_video_id"],"url":receipt["url"],
     "scheduled_time":receipt["scheduled_local"],"thumbnail_status":receipt["thumbnail_status"]})
plan.update({"status":"all_scheduled_verified","scheduled_in_youtube":True,
 "verified_scheduled_count":3,"youtube_video_ids":[x["youtube_video_id"] for x in confirmed],
 "editorial_approval":"Owner approved publication, full human listening/watching not independently observed",
 "full_narration_listening_review":"Not independently performed",
 "captions_human_review":"Not completed; draft captions not uploaded",
 "youtube_upload_status":"THREE_PRIVATE_UPLOADS_SCHEDULED",
 "last_schedule_verification":now,
 "notes":"API-confirmed future releases; YouTube will make public automatically. No duplicate uploads."})
save(planpath,plan)
reconcile=REPO/"state"/"reconciliation"/"2026-10-14-final-api-scheduled.json"
save(reconcile,{"checked_at_local":now,"channel_id":CHANNEL,"expected":3,"verified":3,
 "source":"Authenticated read-only YouTube Data API","video_ids":[x["youtube_video_id"] for x in confirmed],
 "items":[{"id":x["id"],"video_id":x["youtube_video_id"],"scheduled_local":x["scheduled_local"],
 "thumbnail_status":x["thumbnail_status"]} for x in confirmed]})
print("SUCCESS_3_OF_3_INDEPENDENTLY_VERIFIED",flush=True)
