"""Read-only YouTube Oct13 publication verification and truthful status ledger.
No uploads, scheduling writes or secret output.
"""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import sys,json
REPO=Path(__file__).resolve().parents[1]
ROOT=REPO.parent
sys.path.insert(0,str(ROOT/"flowminute-publisher-worktree"/"scripts"))
import youtube_publisher as api
IDS={
 "pilot_017":("mxB4fNx0Ua4","2026-10-13T11:00:00+05:30"),
 "long_008":("NCLp6YibFMs","2026-10-13T16:00:00+05:30"),
 "pilot_018":("-8B1X1n5XIU","2026-10-13T20:30:00+05:30"),
}
CHANNEL="UCCcL9Q_jqVq6LJmnYUSAFZA"
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
client=api.youtube_client(ROOT/".flowminute-private"/"youtube_readonly_token.json",writable=False)
api.guard_channel(client,CHANNEL)
ist=timezone(timedelta(hours=5,minutes=30))
at=datetime.now(ist)
results=[]
for episode,(id,slot) in IDS.items():
    remote=api.video_info(client,id)
    st=remote.get("status",{})
    title=read(REPO/"content"/"episodes"/(episode+".json"))["title"]
    assert remote["snippet"]["channelId"]==CHANNEL and remote["snippet"]["title"]==title
    assert st.get("uploadStatus")=="processed",episode+" not processed"
    privacy=st.get("privacyStatus")
    assert privacy in ("public","private"),episode+" surprising privacy"
    if privacy=="private":
        assert api.parse_utc(st.get("publishAt"))==api.parse_utc(slot),episode+" schedule drift"
    result={"id":episode,"youtube_video_id":id,"title":title,"status":"public_verified" if privacy=="public" else "scheduled_verified","remote_privacy":privacy,"remote_publish_at":st.get("publishAt"),"planned_local":slot,"checked_at_ist":at.isoformat(timespec="seconds"),"url":f"https://youtu.be/{id}"}
    results.append(result)
    print(episode,result["status"],id,flush=True)
doc={"checked_at_ist":at.isoformat(timespec="seconds"),"channel_id":CHANNEL,"source":"authenticated read-only YouTube Data API videos.list","items":results}
write(REPO/"state"/"reconciliation"/"2026-10-13-live-status.json",doc)
pack=REPO/"state"/"planned"/"oct13-pack.json"
state=read(pack)
for e in state["entries"]:
    entry=next((x for x in results if x["id"]==e["id"]),None)
    if entry:
        e["status"]=entry["status"]
        e["youtube_id"]=entry["youtube_video_id"]
        e["url"]=entry["url"]
        e["remote_privacy"]=entry["remote_privacy"]
        e["remote_upload_status"]="processed"
        if "remote_processing" in e:
            e["remote_processing"]="succeeded"
state["last_publication_verification"]=at.isoformat(timespec="seconds")
state["verified_public_count"]=sum(x["status"]=="public_verified" for x in results)
state["status"]="all_public_verified" if state["verified_public_count"]==3 else "partially_public_with_remaining_scheduled"
state["scheduled_in_youtube"]=True
state["youtube_video_ids"]=[x["youtube_video_id"] for x in results]
state["last_publication_verification_source"]="authenticated YouTube Data API at "+at.isoformat(timespec="seconds")
write(pack,state)
print("RECONCILED",state["verified_public_count"],"of",len(results),"public")
