"""Record already confirmed October 13 YouTube schedules without changing YouTube.
Only exact title/channel/video-ID/time matches from the remote API become receipts.
Use AFTER attempting all publisher schedule operations; makes no API write.
"""
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import sys

REPO=Path(__file__).resolve().parents[1]
WS=REPO.parent
PRIVATE=WS/".flowminute-private"
sys.path.insert(0,str(WS/"flowminute-publisher-worktree"/"scripts"))
import youtube_publisher as pub

DAY="2026-10-13"
CHANNEL="UCCcL9Q_jqVq6LJmnYUSAFZA"
SCHEDULE={
 "pilot_017":"2026-10-13T11:00:00+05:30",
 "long_008":"2026-10-13T16:00:00+05:30",
 "pilot_018":"2026-10-13T20:30:00+05:30",
}
IST=timezone(timedelta(hours=5,minutes=30))

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def write_json(path,doc):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+".tmp")
    temp.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    temp.replace(path)

def run():
    ledger=read_json(PRIVATE/"youtube-ledger.json")["episodes"]
    client=pub.youtube_client(PRIVATE/"youtube_readonly_token.json",writable=False)
    pub.guard_channel(client,CHANNEL)
    now=datetime.now(IST).isoformat(timespec="seconds")
    record=[]
    for ep,local in SCHEDULE.items():
        led=ledger.get(ep) or {}
        if led.get("state")!="scheduled_verified":
            print(ep,"NOT_SCHEDULED_LEDGER",led.get("state","missing"))
            continue
        vid=led.get("video_id")
        metadata=read_json(REPO/"content"/"episodes"/f"{ep}.json")
        expected_utc=pub.as_rfc3339(pub.parse_utc(local))
        item=pub.video_info(client,vid)
        remote=item.get("status",{})
        assert led.get("publish_at")==expected_utc,ep+" ledger publishAt mismatch"
        assert led.get("confirmed_publish_at")==expected_utc,ep+" ledger confirmation mismatch"
        assert item.get("snippet",{}).get("channelId")==CHANNEL,ep+" channel mismatch"
        assert item.get("snippet",{}).get("title")==metadata.get("title"),ep+" title mismatch"
        assert remote.get("privacyStatus")=="private",ep+" privacy mismatch"
        assert remote.get("uploadStatus")=="processed",ep+" processing mismatch"
        assert pub.parse_utc(remote.get("publishAt"))==pub.parse_utc(local),ep+" time mismatch"
        receipt={
            "id":ep,"date_local":DAY,"scheduled_local":local,"timezone":"Asia/Kolkata",
            "youtube_video_id":vid,
            "url":f"https://youtube.com/shorts/{vid}" if ep.startswith("pilot_") else f"https://youtu.be/{vid}",
            "title_in_studio":metadata["title"],"status":"scheduled_verified",
            "verified_at_local":now,
            "verified_source":"Read-only authenticated YouTube Data API videos.list + private uploader ledger",
            "remote_privacy":"private","remote_publish_at_utc":expected_utc,
            "remote_upload_status":remote["uploadStatus"],
            "thumbnail_status":led.get("assets",{}).get("thumbnail","not_uploaded"),
            "captions_status":"not_uploaded_draft_caption_timing_unreviewed",
            "owner_approval":"explicit owner approved for Oct 13 scheduling in ChatGPT on 2026-10-12",
            "no_duplicate_upload":True
        }
        path=REPO/"state"/"scheduled"/(ep+".json")
        if path.exists():
            old=read_json(path)
            assert old.get("youtube_video_id")==vid,"Receipt ID conflict"
        write_json(path,receipt)
        record.append({"id":ep,"video_id":vid,"status":"scheduled_verified","scheduled_local":local,"url":receipt["url"]})
        print(ep,"VERIFIED_SCHEDULE",vid,local)
    pack=REPO/"state"/"planned"/"oct13-pack.json"
    doc=read_json(pack)
    for episode in doc.get("entries",[]):
        match=next((r for r in record if r["id"]==episode.get("id")),None)
        if match:
            episode["status"]="scheduled_verified"
            episode["youtube_id"]=match["video_id"]
            episode["url"]=match["url"]
            episode["scheduled_time"]=match["scheduled_local"]
    doc["status"]="all_scheduled_verified" if len(record)==len(SCHEDULE) else "partially_scheduled"
    doc["scheduled_in_youtube"]=len(record)==len(SCHEDULE)
    doc["last_schedule_verification"]=now
    write_json(pack,doc)
    write_json(REPO/"state"/"reconciliation"/"2026-10-13-schedule-api-verification.json",{
        "at_local":now,"date_local":DAY,"expected":len(SCHEDULE),"verified":len(record),
        "channel_id":CHANNEL,"items":record,"verification":"authenticated_readonly_api",
        "no_duplicate_upload":True})
    print(json.dumps({"verified":len(record),"expected":len(SCHEDULE),"items":record},indent=2))

if __name__=="__main__":
    run()
