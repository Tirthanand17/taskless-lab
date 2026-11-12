"""Clivox A1: deterministic, read-only candidate intake & editorial triage.

Input is PUBLIC-SAFE source discovery metadata, not a rights license.
Only standard library, no HTTP, no media download, no upload, no token access.

Example:
    python -B scripts/branch3_discovery_pipeline.py \
      --input branch3/discovery/fixtures/research-candidates.json \
      --output /tmp/clivox-discovery-report.json
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, urlsplit

CHANNEL="UCfPEvy0SefE_5nNlYlY_CyQ"
OTHER_CHANNEL="UCCcL9Q_jqVq6LJmnYUSAFZA"
CATEGORIES=("gaming","livestream","comedy","entertainment","podcast_interview")
SIGNALS=("fast_hook","clear_payoff","surprise_or_humor","source_context","original_commentary_idea","sharing_potential")
YT_VIDEO=re.compile(r"[A-Za-z0-9_-]{11}\Z")
MAX_BYTES=512_000
MAX_CANDIDATES=100
ALLOWED_CAMPAIGN_HOSTS=frozenset({
    "contentrewards.com",
    "b4e0vdqv6zgqeqj4pfgm.apps.whop.com",
    "dev-b4e0vdqv6zgqeqj4pfgm.apps.whop.com",
})
RELEASE_FLAGS=("rights_verified","creator_approved","media_downloaded","upload_authorized","publication_authorized","paid_campaign_joined")

class DiscoveryDenied(ValueError):
    pass

def require(predicate: bool, error: str) -> None:
    if not predicate:
        raise DiscoveryDenied("CLIVOX_DISCOVERY_DENIED_"+error)

def clean_string(value: object, limit: int=200) -> str:
    require(type(value) is str and value==value.strip() and 0<len(value)<=limit,"STRING")
    require(all(ord(c)>=32 for c in value),"CONTROL_CHARACTER")
    return value

def canonical_url(kind: str, url: str, video_id: str | None) -> str:
    clean_string(url,2048)
    p=urlsplit(url)
    require(p.scheme=="https" and p.username is None and p.password is None
            and p.port in (None,443) and p.fragment=="" and not p.query.startswith("token="),
            "UNTRUSTED_URL")
    if kind=="youtube_video":
        require(p.netloc=="www.youtube.com" and p.path=="/watch" and video_id is not None
                and YT_VIDEO.fullmatch(video_id) is not None,"YOUTUBE_SOURCE")
        params=parse_qs(p.query,keep_blank_values=True)
        require(set(params)=={"v"} and params["v"]==[video_id],"YOUTUBE_QUERY")
        return "https://www.youtube.com/watch?v="+video_id
    require(kind=="campaign" and p.hostname in ALLOWED_CAMPAIGN_HOSTS
            and p.path.startswith("/c/campaigns/")
            and p.query=="","CAMPAIGN_SCOPE")
    return url

def parse_int(value: object, maximum: int) -> int | None:
    require(value is None or (type(value) is int and 0<=value<=maximum),"METRIC")
    return value

def validate_record(item: object) -> dict:
    require(type(item) is dict,"CANDIDATE_OBJECT")
    allowed={"candidate_id","category","source_kind","source_url","source_video_id",
             "creator_channel_id","title","description","observed_utc","signals",
             "video_statistics","notes"}
    require(set(item)<=allowed and {"candidate_id","category","source_kind","source_url",
                                    "source_video_id","creator_channel_id","title",
                                    "observed_utc","signals","video_statistics"}<=set(item),
            "FIELDS")
    candidate_id=clean_string(item["candidate_id"],80)
    require(re.fullmatch(r"[a-z0-9][a-z0-9_-]{4,79}",candidate_id) is not None,"CANDIDATE_ID")
    require(item["category"] in CATEGORIES,"CATEGORY")
    kind=item["source_kind"]
    vid=item["source_video_id"]
    require(vid is None or (type(vid) is str and YT_VIDEO.fullmatch(vid) is not None),"VIDEO_ID")
    if kind=="youtube_video":
        require(vid is not None,"MISSING_VIDEO_ID")
        channel_id=clean_string(item["creator_channel_id"],30)
        require(re.fullmatch(r"UC[A-Za-z0-9_-]{22}",channel_id) is not None
                and channel_id not in (CHANNEL,OTHER_CHANNEL),"CHANNEL_ID")
    else:
        require(kind=="campaign" and vid is None
                and item["creator_channel_id"] is None,"CAMPAIGN_ID")
    canonical=canonical_url(kind,item["source_url"],vid)
    title=clean_string(item["title"],160)
    if "description" in item:
        clean_string(item["description"],500)
    if "notes" in item:
        clean_string(item["notes"],500)
    observed=clean_string(item["observed_utc"],40)
    require(observed.endswith("Z"),"OBSERVED_UTC")
    try:
        dt=datetime.fromisoformat(observed.replace("Z","+00:00"))
    except ValueError:
        raise DiscoveryDenied("CLIVOX_DISCOVERY_DENIED_OBSERVED_UTC") from None
    require(dt.tzinfo is not None and dt.year>=2020,"OBSERVED_DATE")
    signals=item["signals"]
    require(type(signals) is dict and set(signals)==set(SIGNALS)
            and all(type(signals[s]) is bool for s in SIGNALS),"SIGNALS")
    stats=item["video_statistics"]
    require(type(stats) is dict and set(stats)=={"views","likes","comments"},"STATS")
    views=parse_int(stats["views"],10**15)
    likes=parse_int(stats["likes"],10**15)
    comments=parse_int(stats["comments"],10**15)
    require(kind=="youtube_video" or all(v is None for v in (views,likes,comments)),
            "UNATTRIBUTED_CAMPAIGN_STATS")
    if views is not None and likes is not None:
        require(likes<=views,"IMPOSSIBLE_LIKES")
    if views is not None and comments is not None:
        require(comments<=views,"IMPOSSIBLE_COMMENTS")
    require(not any(x in item for x in RELEASE_FLAGS),"CLAIMED_RIGHTS")
    return {"candidate_id":candidate_id,"category":item["category"],
        "source_kind":kind,"source_url":canonical,"source_video_id":vid,
        "creator_channel_id":item["creator_channel_id"],
        "title":title,"observed_utc":observed,"signals":signals,"video_statistics":stats}

def editorial_score(item: dict) -> int:
    """Editorial triage score, NOT a proven prediction of viral success."""
    weights={"fast_hook":24,"clear_payoff":24,"surprise_or_humor":18,
             "source_context":12,"original_commentary_idea":14,"sharing_potential":8}
    return sum(weight for name,weight in weights.items() if item["signals"][name])

def intake(payload: object) -> dict:
    require(type(payload) is dict and set(payload)=={"schema_version","channel_id",
            "dataset_status","candidates"},"DATASET_FIELDS")
    require(payload["schema_version"]==1 and payload["channel_id"]==CHANNEL
            and payload["dataset_status"]=="RESEARCH_ONLY_UNLICENSED","DATASET_GATE")
    source=payload["candidates"]
    require(type(source) is list and 0<len(source)<=MAX_CANDIDATES,"DATASET_SIZE")
    items=[validate_record(x) for x in source]
    ids=set()
    source_keys=set()
    for item in items:
        cid=item["candidate_id"]
        key=(item["source_kind"],item["source_url"])
        require(cid not in ids and key not in source_keys,"DUPLICATE_CANDIDATE")
        ids.add(cid)
        source_keys.add(key)
    queue=[]
    for item in items:
        score=editorial_score(item)
        digest=hashlib.sha256(json.dumps(item,sort_keys=True,separators=(",",":")).encode()).hexdigest()
        queue.append({
            "candidate_id":item["candidate_id"],
            "source_kind":item["source_kind"],
            "source_url":item["source_url"],
            "category":item["category"],
            "editorial_hypothesis_score_0_to_100":score,
            "metric_evidence_available":any(v is not None for v in item["video_statistics"].values()),
            "candidate_digest_sha256":digest,
            "next_state":"RIGHTS_PENDING",
            "current_state":"DISCOVERED",
            "rights_verified":False,
            "creator_permission_verified":False,
            "source_acquisition_authorized":False,
            "render_authorized":False,
            "youtube_upload_authorized":False,
            "publishing_authorized":False,
        })
    queue.sort(key=lambda x:(-x["editorial_hypothesis_score_0_to_100"],x["candidate_id"]))
    return {"schema_version":1,"channel_id":CHANNEL,"pipeline":"A1_OFFLINE_METADATA_ONLY",
            "status":"RESEARCH_ONLY_UNLICENSED",
            "ranking_is_a_hypothesis_not_proof_of_viral_success":True,
            "all_creator_permissions_pending":True,"source_media_download_enabled":False,
            "youtube_write_enabled":False,"candidate_count":len(queue),
            "queue":queue}

def load(path: Path) -> dict:
    require(path.is_file() and not path.is_symlink() and path.stat().st_size<=MAX_BYTES,
            "INPUT_FILE")
    return intake(json.loads(path.read_text(encoding="utf-8")))

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    report=load(args.input)
    encoded=json.dumps(report,indent=2,ensure_ascii=False)+"\n"
    if args.output:
        require(not args.output.is_symlink(),"OUTPUT_LINK")
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(encoded,encoding="utf-8")
    else:
        print(encoded,end="")
    print("CLIVOX_A1_DISCOVERY_METADATA_ONLY_NO_PERMISSIONS_NO_MEDIA_NO_YOUTUBE_WRITE",flush=True)

if __name__=="__main__":
    main()
