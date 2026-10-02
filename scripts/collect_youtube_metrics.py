from __future__ import annotations

import argparse
import json
import os
from datetime import date, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def credentials():
    from google.oauth2.credentials import Credentials
    raw=os.environ.get("YOUTUBE_TOKEN_JSON")
    if not raw:
        raise SystemExit("YOUTUBE_TOKEN_JSON is not configured")
    return Credentials.from_authorized_user_info(json.loads(raw))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--video-id",required=True)
    ap.add_argument("--episode-id",required=True)
    ap.add_argument("--days",type=int,default=7)
    args=ap.parse_args()

    from googleapiclient.discovery import build
    creds=credentials()
    yt=build("youtube","v3",credentials=creds)
    ya=build("youtubeAnalytics","v2",credentials=creds)

    info=yt.videos().list(part="snippet,statistics,status",id=args.video_id).execute()
    if not info.get("items"):
        raise SystemExit("video not found for authorized channel")
    item=info["items"][0]

    end=date.today()
    start=end-timedelta(days=max(1,args.days))
    report=ya.reports().query(
        ids="channel==MINE",
        startDate=start.isoformat(),
        endDate=end.isoformat(),
        metrics="engagedViews,views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,comments,shares,subscribersGained,subscribersLost",
        filters=f"video=={args.video_id}"
    ).execute()

    columns=[h["name"] for h in report.get("columnHeaders",[])]
    rows=report.get("rows",[])
    metrics=dict(zip(columns,rows[0])) if rows else {}

    result={
      "episode_id":args.episode_id,
      "video_id":args.video_id,
      "window_days":args.days,
      "start_date":start.isoformat(),
      "end_date":end.isoformat(),
      "title":item["snippet"]["title"],
      "privacy_status":item["status"]["privacyStatus"],
      "public_statistics":item.get("statistics",{}),
      "analytics":metrics
    }

    out=ROOT/"analytics"/args.episode_id/f"{args.days}d.json"
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(out)

if __name__=="__main__":
    main()
