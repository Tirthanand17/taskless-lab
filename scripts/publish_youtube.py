from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import os
from pathlib import Path

UTC_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
REQUIRED_APPROVALS = (
    "human_voice_approved", "exact_captions_approved",
    "rights_cleared", "factual_review_approved", "final_video_approved"
)

def parse_scheduled_utc(value: str, *, now=None) -> str:
    """Strict scheduled UTC: reject anything but a future Z time, never publish immediately."""
    if not isinstance(value, str) or not UTC_TIME.fullmatch(value):
        raise ValueError("Schedule must be exact UTC YYYY-MM-DDTHH:MM:SSZ")
    target = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    now = now or datetime.datetime.now(datetime.timezone.utc)
    if target <= now + datetime.timedelta(minutes=15):
        raise ValueError("Scheduled time must be at least 15 minutes in the future")
    return target.isoformat(timespec="seconds").replace("+00:00", "Z")

def verify_youtube_schedule(video: dict, requested: str, channel_id: str) -> bool:
    """Accept real YouTube readback only, not request parameters or local clock."""
    status = video.get("status") if isinstance(video,dict) else None
    snippet = video.get("snippet") if isinstance(video,dict) else None
    if not isinstance(status,dict) or not isinstance(snippet,dict):
        return False
    if status.get("privacyStatus") != "private":
        return False
    if channel_id and snippet.get("channelId") != channel_id:
        return False
    got = status.get("publishAt", "")
    try:
        dt = datetime.datetime.fromisoformat(got.replace("Z", "+00:00"))
        requested_dt = datetime.datetime.fromisoformat(requested.replace("Z", "+00:00"))
        return dt == requested_dt and status.get("uploadStatus") != "rejected"
    except (ValueError, AttributeError, TypeError):
        return False

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
    ap.add_argument("--schedule-at-utc",default=None,
                    help="Private YouTube scheduling time, exact UTC YYYY-MM-DDTHH:MM:SSZ")
    ap.add_argument("--expected-sha256",default=None,
                    help="Pinned SHA-256 of approved final MP4")
    ap.add_argument("--expected-channel-id",default=None,
                    help="Expected YouTube channel identity for API readback")
    ap.add_argument("--approval-manifest",default=None,
                    help="Human review gate JSON with five explicit true approvals")
    args=ap.parse_args()

    if not args.confirm_publish:
        raise SystemExit("publishing is blocked unless --confirm-publish is passed")
    if os.environ.get("PUBLISH_ENABLED") != "true":
        raise SystemExit("PUBLISH_ENABLED is not true; publishing remains disabled")

    root=Path(__file__).resolve().parents[1]
    meta=json.loads((root/args.episode).read_text(encoding="utf-8"))
    video_path=root/args.video
    caption_path=root/args.captions

    schedule = None
    digest = None
    if args.schedule_at_utc is not None:
        schedule = parse_scheduled_utc(args.schedule_at_utc)
        if args.privacy != "private":
            raise SystemExit("Scheduled uploads must remain private until publishAt")
        if not args.expected_sha256 or not re.fullmatch(r"[0-9a-f]{64}",args.expected_sha256):
            raise SystemExit("Scheduled upload requires exact approved video SHA256")
        if not args.expected_channel_id or not re.fullmatch(r"UC[A-Za-z0-9_-]{22}",args.expected_channel_id):
            raise SystemExit("Scheduled upload requires a valid expected channel ID")
        if not args.approval_manifest:
            raise SystemExit("Scheduled upload requires human approval manifest")
        approval_file=root/args.approval_manifest
        if not approval_file.is_file():
            raise SystemExit("Approval manifest not found")
        approval=json.loads(approval_file.read_text(encoding="utf-8"))
        if any(approval.get(field) is not True for field in REQUIRED_APPROVALS):
            raise SystemExit("Final voice/captions/rights/facts/video approvals not all true")
        if approval.get("approved_video_sha256") != args.expected_sha256:
            raise SystemExit("Review approvals do not bind to exact MP4")
        if not video_path.is_file() or not caption_path.is_file():
            raise SystemExit("Approved MP4 and SRT must exist")
        with video_path.open("rb") as stream:
            digest=hashlib.file_digest(stream,"sha256").hexdigest()
        if digest != args.expected_sha256:
            raise SystemExit("Approved video hash does not match source bytes")
        if (root/args.receipt).exists():
            raise SystemExit("Publication receipt already exists: refuse duplicate upload")

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
        "selfDeclaredMadeForKids":False,
        "containsSyntheticMedia":True
      }
    }
    if schedule:
        body["status"]["publishAt"]=schedule
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

    schedule_readback=None
    if schedule:
        items=youtube.videos().list(part="snippet,status",id=video_id).execute().get("items",[])
        if len(items)!=1 or items[0].get("id") != video_id:
            raise SystemExit(f"Upload ID {video_id} exists, but schedule readback was not verified")
        if not verify_youtube_schedule(items[0],schedule,args.expected_channel_id):
            raise SystemExit(f"Upload ID {video_id} exists, but exact private publishAt verification failed")
        schedule_readback={"requested_publish_at_utc":schedule,
                           "verified_publish_at_utc":schedule,
                           "channel_id":args.expected_channel_id,
                           "source_mp4_sha256":digest,
                           "verified_via":"youtube.videos.list"}
        print(f"YouTube confirmed video {video_id} is scheduled at {schedule}")

    receipt_path=root/args.receipt
    receipt_path.parent.mkdir(parents=True,exist_ok=True)
    receipt_path.write_text(json.dumps({
      "episode_id":meta.get("id"),
      "video_id":video_id,
      "youtube_url":f"https://www.youtube.com/watch?v={video_id}",
      "privacy":args.privacy,
      "published_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
      "title":meta["title"],
      "youtube_schedule_verified": bool(schedule_readback),
      "schedule_readback":schedule_readback
    },indent=2)+"\\n",encoding="utf-8")
    print(f"wrote receipt {receipt_path}")

if __name__=="__main__":
    main()
