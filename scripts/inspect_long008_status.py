"""Read-only processing and file-integrity metadata for the already uploaded video."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WS=ROOT.parent
sys.path.insert(0,str(WS/"flowminute-publisher-worktree"/"scripts"))
import youtube_publisher as y
video_id="-_6iX5o3EfY"
api=y.youtube_client(WS/".flowminute-private"/"youtube_readonly_token.json",writable=False)
y.guard_channel(api,"UCCcL9Q_jqVq6LJmnYUSAFZA")
response=api.videos().list(part="id,snippet,status,processingDetails,fileDetails,contentDetails,suggestions",id=video_id).execute()
for video in response.get("items",[]):
    print(json.dumps({"id":video["id"],"title":video.get("snippet",{}).get("title"),"privacy":video.get("status",{}).get("privacyStatus"),"uploadStatus":video.get("status",{}).get("uploadStatus"),"duration":video.get("contentDetails",{}).get("duration"),"processingDetails":video.get("processingDetails"),"fileDetails":{k:v for k,v in video.get("fileDetails",{}).items() if k in ("fileName","fileSize","durationMs","container")},"suggestions":video.get("suggestions")},indent=2))
if not response.get("items"):
    print("NOT_RETURNED")
