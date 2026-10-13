"""Reconcile an already-applied Oct 13 schedule after a stale API read-back.

NO YouTube writes and NO duplicate upload. Verify the exact video, owner, title,
processed status and publishAt from fresh authenticated videos.list first.
"""
import sys,json
from pathlib import Path
from datetime import datetime,timezone,timedelta
REPO=Path(__file__).resolve().parents[1]
WS=REPO.parent
PRIVATE=WS/".flowminute-private"
sys.path.insert(0,str(WS/"flowminute-publisher-worktree"/"scripts"))
import youtube_publisher as pub

REPLACEMENT_ID="long_008_recovery_v2"
VIDEO_ID="NCLp6YibFMs"
OLD_ID="-_6iX5o3EfY"
CHANNEL="UCCcL9Q_jqVq6LJmnYUSAFZA"
DUE="2026-10-13T16:00:00+05:30"
SHA="01301b60f09c58765afb90b36af59b4ea91f42141d2108030df3ad97785f7e17"
IST=timezone(timedelta(hours=5,minutes=30))

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+".tmp")
    temp.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    temp.replace(path)

def verify_item(api,vid,title,due):
    item=pub.video_info(api,vid)
    status=item["status"]
    pub.require(item["snippet"].get("channelId")==CHANNEL,vid+" channel mismatch")
    pub.require(item["snippet"].get("title")==title,vid+" title mismatch")
    pub.require(status.get("privacyStatus")=="private",vid+" not private")
    pub.require(status.get("uploadStatus")=="processed",vid+" upload not processed")
    pub.require(item.get("processingDetails",{}).get("processingStatus")=="succeeded",vid+" processing not succeeded")
    pub.require(pub.parse_utc(status.get("publishAt"))==pub.parse_utc(due),vid+" publishAt mismatch")
    return item

def main():
    api=pub.youtube_client(PRIVATE/"youtube_readonly_token.json",writable=False)
    pub.guard_channel(api,CHANNEL)
    manifest=pub.validate_manifest(WS/"oct13-production"/"manifests"/(REPLACEMENT_ID+".release.json"))
    pub.require(manifest["video_sha256"]==SHA and manifest["publish_at"]==pub.as_rfc3339(pub.parse_utc(DUE)),"Manifest mismatch")
    title=manifest["title"]
    main_video=verify_item(api,VIDEO_ID,title,DUE)
    old=pub.video_info(api,OLD_ID)
    pub.require(old["snippet"].get("channelId")==CHANNEL,"Original channel mismatch")
    pub.require(old["status"].get("privacyStatus")=="private" and not old["status"].get("publishAt"),"Original video is public or scheduled; STOP and inspect!")
    # Update only the new upload's scheduling state after read-only verification.
    ledger_path=PRIVATE/"youtube-ledger.json"
    with pub.exclusive_ledger(ledger_path):
        ledger=pub.get_ledger(ledger_path)
        entry=pub.require_matching_record(ledger,manifest)
        pub.require(entry["state"]=="scheduling_unresolved" and entry["video_id"]==VIDEO_ID,"Ledger no longer matches recovered schedule")
        pub.require(entry.get("video_sha256")==SHA,"Hash mismatch")
        entry["state"]="scheduled_verified"
        entry["confirmed_publish_at"]=pub.as_rfc3339(pub.parse_utc(DUE))
        entry["recovery_provenance"]="videos.update response ambiguously verified; fresh read-only videos.list confirms publishAt, private, correct video"
        entry["reconciled_at_local"]=datetime.now(IST).isoformat(timespec="seconds")
        pub.write_json_secure(ledger_path,ledger)
    stamp=datetime.now(IST).isoformat(timespec="seconds")
    receipt={
        "id":"long_008","date_local":"2026-10-13",
        "scheduled_local":DUE,"timezone":"Asia/Kolkata",
        "youtube_video_id":VIDEO_ID,"url":f"https://youtu.be/{VIDEO_ID}",
        "title_in_studio":title,
        "status":"scheduled_verified",
        "verification_source":"Authenticated read-only YouTube Data API videos.list after earlier uncertain schedule response",
        "verified_at_local":stamp,
        "remote_privacy":"private",
        "remote_upload_status":"processed",
        "remote_processing":"succeeded",
        "remote_publish_at_utc":"2026-10-13T10:30:00Z",
        "canonical_episode_id":"long_008",
        "local_recovery_manifest_id":REPLACEMENT_ID,
        "replacement_reason":"Original API upload interrupted and processing stuck; clean H264 export uploaded privately and fully processed",
        "stalled_original_video_id":OLD_ID,
        "stalled_original_remains_private_unscheduled":True,
        "no_duplicate_publication":True,
        "captions_status":"not_uploaded_unreviewed_timing"
    }
    dest=REPO/"state"/"scheduled"/"long_008.json"
    if dest.exists():
        pub.require(read(dest).get("youtube_video_id")==VIDEO_ID,"Existing scheduled receipt ID conflict")
    save(dest,receipt)
    packpath=REPO/"state"/"planned"/"oct13-pack.json"
    pack=read(packpath)
    for ep in pack["entries"]:
        if ep["id"]=="long_008":
            ep.update({"status":"scheduled_verified","youtube_id":VIDEO_ID,"url":receipt["url"],
                       "scheduled_time":DUE,"recovery_manifest_id":REPLACEMENT_ID,
                       "stalled_original_video_id":OLD_ID})
    # Confirm the other Shorts remain scheduled before marking entire pack completed.
    for ep in pack["entries"]:
        pub.require((REPO/"state"/"scheduled"/(ep["id"]+".json")).exists(),"Missing scheduled receipt: "+ep["id"])
        existing=read(REPO/"state"/"scheduled"/(ep["id"]+".json"))
        verify_item(api,existing["youtube_video_id"],existing["title_in_studio"],existing["scheduled_local"])
        ep["status"]="scheduled_verified"
    pack["status"]="all_scheduled_verified"
    pack["scheduled_in_youtube"]=True
    pack["verified_scheduled_count"]=3
    pack["last_schedule_verification"]=stamp
    save(packpath,pack)
    record=[{"id":ep["id"],"video_id":read(REPO/"state"/"scheduled"/(ep["id"]+".json"))["youtube_video_id"],"status":"scheduled_verified","scheduled_local":read(REPO/"state"/"scheduled"/(ep["id"]+".json"))["scheduled_local"]} for ep in pack["entries"]]
    save(REPO/"state"/"reconciliation"/"2026-10-13-schedule-api-verification.json",
         {"at_local":stamp,"date_local":"2026-10-13","expected":3,"verified":3,"channel_id":CHANNEL,
          "items":record,"verification":"authenticated read-only videos.list", "no_duplicate_publication":True})
    print(json.dumps({"result":"ALL_THREE_YOUTUBE_SCHEDULED_VERIFIED","long_video_id":VIDEO_ID,"scheduled_local":DUE,
                      "original_still_private":True,"time_verified":stamp},indent=2))

if __name__=="__main__":
    main()
