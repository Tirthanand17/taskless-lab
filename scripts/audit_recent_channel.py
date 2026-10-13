"""Read-only recent FlowMinute channel baseline from YouTube Data API.
Stats may lag; no access to Studio-only CTR, retention or impression data.
"""
from pathlib import Path
import sys,json,statistics
repo=Path(__file__).resolve().parents[1]
workspace=repo.parent
sys.path.insert(0,str(workspace/"flowminute-publisher-worktree"/"scripts"))
import youtube_publisher as pub
api=pub.youtube_client(workspace/".flowminute-private"/"youtube_readonly_token.json",writable=False)
pub.guard_channel(api,"UCCcL9Q_jqVq6LJmnYUSAFZA")
ch=api.channels().list(part="statistics,contentDetails",mine=True).execute()["items"][0]
playlist=ch["contentDetails"]["relatedPlaylists"]["uploads"]
items=[]
page=None
for i in range(3):
 r=api.playlistItems().list(part="contentDetails,snippet",playlistId=playlist,maxResults=50,pageToken=page).execute()
 items.extend(r.get("items",[]))
 page=r.get("nextPageToken")
 if not page:break
ids=[v["contentDetails"]["videoId"] for v in items]
videos={}
for n in range(0,len(ids),50):
 for v in api.videos().list(part="statistics,status,snippet,contentDetails",id=",".join(ids[n:n+50])).execute().get("items",[]):
  videos[v["id"]]=v
rows=[]
for it in items:
 v=videos.get(it["contentDetails"]["videoId"])
 if not v:continue
 title=v["snippet"]["title"]
 date=v["snippet"].get("publishedAt")
 status=v["status"].get("privacyStatus")
 stats=v.get("statistics",{})
 rows.append({"id":v["id"],"title":title[:92],"date":date,"privacy":status,"scheduled":v["status"].get("publishAt"),"duration":v["contentDetails"].get("duration"),"views":int(stats.get("viewCount",0)),"likes":int(stats.get("likeCount",0)),"comments":int(stats.get("commentCount",0))})
output={"channel_statistics":ch.get("statistics",{}),"count":len(rows),"recent":rows[:45],"limitation":"YouTube Data API public counts only; no CTR, retention, impressions, subscriber-attribution or average view duration"}
print(json.dumps(output,indent=2))
