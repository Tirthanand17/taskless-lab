from __future__ import annotations

import argparse
import datetime
import json
import os
from pathlib import Path

def load_service():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    token_json=os.environ.get("YOUTUBE_TOKEN_JSON")
    if not token_json:
        raise SystemExit("YOUTUBE_TOKEN_JSON is not configured; publishing remains disabled")
    creds=Credentials.from_authorized_user_info(json.loads(token_json))
    return build("youtube","v3",credentials=creds)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--episode",default="content/episodes/pilot_001.json")
    ap.add_argument("--video",default="assets/pilot_001/pilot_001_final.mp4")
    ap.add_argument("--captions",default="assets/pilot_001/captions.srt")
    ap.add_argument("--thumbnail",default="assets/pilot_001/scene_01.png")
    ap.add_argument("--privacy",choices=["private","unlisted","public"],default="private")
    ap.add_argument("--receipt",default="state/published/pilot_001.json")
    ap.add_argument("--confirm-publish",action="store_true")
    args=ap.parse_args()

    if not args.confirm_publish:
        raise SystemExit("publishing is blocked unless --confirm-publish is passed")
    if os.environ.get("PUBLISH_ENABLED") != "true":
        raise SystemExit("PUBLISH_ENABLED is not true; publishing remains disabled")

    root=Path(__file__).resolve().parents[1]
    meta=json.loads((root/args.episode).read_text(encoding="utf-8"))
    video_path=root/args.video
    caption_path=root/args.captions

    from googleapiclient.http import MediaFileUpload
    youtube=load_service()

    body={
      "snippet":{
        "title":meta["title"],
        "description":meta["description"],
        "tags":meta.get("tags", []),
        "defaultLanguage":meta.get("language", "en"),
        "categoryId":"27"
      },
      "status":{
        "privacyStatus":args.privacy,
        "selfDeclaredMadeForKids":False
      }
    }
    req=youtube.videos().insert(
      part="snippet,status",
      body=body,
      media_body=MediaFileUpload(str(video_path),chunksize=-1,resumable=True)
    )
    response=None
    while response is None:
        _,response=req.next_chunk()
    video_id=response["id"]
    print(f"uploaded video {video_id} as {args.privacy}")

    thumb_path=root/args.thumbnail
    if thumb_path.exists():
        try:
            youtube.thumbnails().set(
              videoId=video_id,
              media_body=MediaFileUpload(str(thumb_path),mimetype="image/png")
            ).execute()
            print("uploaded vertical cover thumbnail")
        except Exception as exc:
            print(f"thumbnail upload skipped/failed: {exc}")

    if caption_path.exists():
        cap_body={"snippet":{
          "videoId":video_id,
          "language":"en",
          "name":"English",
          "isDraft":False
        }}
        youtube.captions().insert(
          part="snippet",
          body=cap_body,
          media_body=MediaFileUpload(str(caption_path),mimetype="application/octet-stream")
        ).execute()
        print("uploaded English SRT captions")

    receipt_path=root/args.receipt
    receipt_path.parent.mkdir(parents=True,exist_ok=True)
    receipt_path.write_text(json.dumps({
      "episode_id":meta.get("id"),
      "video_id":video_id,
      "youtube_url":f"https://www.youtube.com/watch?v={video_id}",
      "privacy":args.privacy,
      "published_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
      "title":meta["title"]
    },indent=2)+"\\n",encoding="utf-8")
    print(f"wrote receipt {receipt_path}")

if __name__=="__main__":
    main()
