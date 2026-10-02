from __future__ import annotations

import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def service():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    raw=os.environ.get("YOUTUBE_TOKEN_JSON")
    if not raw:
        raise SystemExit("YOUTUBE_TOKEN_JSON is not configured")
    creds=Credentials.from_authorized_user_info(json.loads(raw))
    return build("youtube","v3",credentials=creds)

def main():
    if os.environ.get("CHANNEL_CONFIG_ENABLED") != "true":
        raise SystemExit("CHANNEL_CONFIG_ENABLED is not true; channel changes are disabled")

    from googleapiclient.http import MediaFileUpload
    yt=service()

    current=yt.channels().list(part="id,brandingSettings",mine=True).execute()
    items=current.get("items",[])
    if len(items)!=1:
        raise SystemExit(f"expected exactly one authorized brand channel; found {len(items)}")
    channel_id=items[0]["id"]

    description=(
      "Practical tutorials for getting repetitive work done faster with AI, Excel, CSV files, "
      "Power Query, and Python automation. FlowMinute Lab focuses on real workflows, visible "
      "before-and-after examples, safer automation, and clear validation — not generic AI news or hype. "
      "Expect concise Shorts for quick fixes and deeper tutorials for complete workflows."
    )
    keywords="AI productivity Excel CSV data cleaning Power Query Python automation ChatGPT workflows"

    banner_path=ROOT/"assets"/"brand"/"banner.png"
    uploaded=yt.channelBanners().insert(
      body={},
      media_body=MediaFileUpload(str(banner_path),mimetype="image/png")
    ).execute()
    banner_url=uploaded["url"]

    body={
      "id":channel_id,
      "brandingSettings":{
        "channel":{
          "description":description,
          "keywords":keywords,
          "defaultLanguage":"en"
        },
        "image":{
          "bannerExternalUrl":banner_url
        }
      }
    }
    yt.channels().update(part="brandingSettings",body=body).execute()
    print(f"configured FlowMinute Lab channel {channel_id}")

if __name__=="__main__":
    main()
