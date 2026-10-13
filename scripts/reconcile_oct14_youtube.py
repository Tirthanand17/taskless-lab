"""Reconcile Oct14 YouTube schedules without any YouTube writes or duplicate actions.

Always require exact channel/title/video ID, successful processing, private
visibility, exact RFC3339 publish time. An ambiguous CLI response cannot be
blindly retried. Local ledger repairs only after remote schedule is verified.
"""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,sys
repo=Path(__file__).resolve().parents[1]
workspace=repo.parent
sys.path.insert(0,str(workspace/"flowminute-publisher-worktree"/"scripts"))
import youtube_publisher as p
channel="UCCcL9Q_jqVq6LJmnYUSAFZA"
ledger_file=workspace/".flowminute-private"/"youtube-ledger.json"
api=p.youtube_client(workspace/".flowminute-private"/"youtube_readonly_token.json",writable=False)
p.guard_channel(api,channel)
approved=["pilot_019","long_009","pilot_020"]
now=datetime.now(timezone(timedelta(hours=5,minutes=30))).isoformat(timespec="seconds")
confirmed=[]
for episode in approved:
 manifest=workspace/"oct14-production"/"manifests"/(episode+".release.json")
 plan=p.validate_manifest(manifest)
 led=p.get_ledger(ledger_file)
 record=led["episodes"].get(episode)
 if not record or not record.get("video_id"):
  print(episode,"NO_VIDEO_ID_OR_PENDING_UPLOAD",record.get("state") if record else None)
  continue
 p.require_matching_record(led,plan)
 video_id=record["video_id"]
 remote=p.video_info(api,video_id)
 status=remote.get("status",{})
 p.require(remote.get("snippet",{}).get("title")==plan["title"],episode+" remote title differs")
 p.require(remote.get("snippet",{}).get("channelId")==channel,episode+" remote channel differs")
 p.check_processing_succeeded(remote)
 p.require(status.get("privacyStatus")=="private",episode+" already public or privacy not private")
 actual=status.get("publishAt")
 if not actual:
  print(episode,"UPLOADED_BUT_NOT_SCHEDULED",video_id)
  continue
 p.require(abs((p.parse_utc(actual)-p.parse_utc(plan["publish_at"])).total_seconds())<=1,episode+" schedule different")
 if record["state"]=="scheduling_unresolved":
  with p.exclusive_ledger(ledger_file):
   latest=p.get_ledger(ledger_file)
   row=p.require_matching_record(latest,plan)
   p.require(row["state"]=="scheduling_unresolved" and row["video_id"]==video_id,"State changed during recovery")
   row.update({"state":"scheduled_verified","confirmed_publish_at":p.as_rfc3339(p.parse_utc(actual)),
    "reconciled_after_ambiguous_response":True,
    "reconciliation_source":"authenticated read-only YouTube videos.list exact publishAt/status"})
   p.write_json_secure(ledger_file,latest)
 elif record["state"]!="scheduled_verified":
  raise RuntimeError(f"Unsafe ledger state {episode}: {record['state']}")
 confirmed.append({"id":episode,"video_id":video_id,"title":plan["title"],
   "remote_status":"scheduled_verified","remote_publish_at_utc":p.as_rfc3339(p.parse_utc(actual)),
   "scheduled_ist":p.parse_utc(actual).astimezone(timezone(timedelta(hours=5,minutes=30))).isoformat(timespec="seconds"),
   "url":f"https://youtube.com/shorts/{video_id}" if episode.startswith("pilot_") else f"https://youtu.be/{video_id}"})
 print(episode,"SCHEDULE_INDEPENDENTLY_VERIFIED",video_id,actual)
record_path=repo/"state"/"reconciliation"/"2026-10-14-verified-youtube-schedules.json"
record_path.parent.mkdir(parents=True,exist_ok=True)
record_path.write_text(json.dumps({"checked_at_ist":now,"channel_id":channel,"source":"YouTube Data API read-only",
  "number_verified":len(confirmed),"expected":3,"items":confirmed},indent=2)+"\n",encoding="utf-8")
print("TOTAL_VERIFIED",len(confirmed),"OF",len(approved))
