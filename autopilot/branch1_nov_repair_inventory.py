"""Branch 1: read-only November 5–11 GitHub release-evidence and repair audit.

Reports what is IN THE REPOSITORY, never claims a current YouTube API read.
No uploads, replacement, delete, remote scheduling, owner OAuth, or laptop.
A historical scheduled_verified JSON is NOT current remote evidence.

Do not automatically publish replacement media: YouTube cannot mutate MP4
bits in place. A different upload would create a DIFFERENT video ID.
"""
from __future__ import annotations

from datetime import date,datetime,time,timedelta,timezone
from hashlib import sha256
import json
from pathlib import Path
import re

STATUS="B1Q1_GITHUB_RECEIPT_ONLY_CANNOT_RECONCILE_LIVE_YOUTUBE"
CHANNEL="UCCcL9Q_jqVq6LJmnYUSAFZA"
START=date(2026,11,5)
END=date(2026,11,11)
SLOTS=(("short_am","short","11:00"),("long_pm","long","16:00"),
       ("short_pm","short","20:30"))
IST=timezone(timedelta(hours=5,minutes=30))
VIDEO_ID=re.compile(r"^[A-Za-z0-9_-]{11}$")
EPISODE_ID=re.compile(r"^fm_[0-9]{8}_[a-z0-9_]{8,80}$")

class NovAuditRejected(ValueError):
    """Malformed or contradictory historical schedule means stop and investigate."""


def _json(path:Path)->dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size>120000:
        raise NovAuditRejected("Missing, symlink or oversized repository release record")
    try:
        record=json.loads(path.read_text(encoding="utf8"))
    except (UnicodeError,ValueError) as exc:
        raise NovAuditRejected("Malformed repository JSON") from exc
    if type(record) is not dict:
        raise NovAuditRejected("Expected object release JSON")
    return record


def _utc_for(day:date,clock:str)->str:
    local=datetime.fromisoformat(day.isoformat()+"T"+clock+":00").replace(tzinfo=IST)
    return local.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")


def _slot_name(record:dict)->str:
    local=record.get("scheduled_local")
    if type(local) is not str:
        raise NovAuditRejected("Historical receipt lacks local scheduled time")
    try:
        dt=datetime.fromisoformat(local)
    except ValueError as exc:
        raise NovAuditRejected("Malformed historical local schedule") from exc
    if dt.utcoffset()!=IST.utcoffset(None):
        raise NovAuditRejected("Historical record is not IST")
    if dt.date().isoformat()!=record.get("date_local"):
        raise NovAuditRejected("Mismatch between scheduled and date_local")
    slot=next((name for name,kind,clock in SLOTS if dt.strftime("%H:%M")==clock),None)
    if not slot:
        raise NovAuditRejected("Outside the channel's three signed daily slot times")
    return slot


def _index_historical_receipts(root:Path)->dict:
    folder=root/"state"/"scheduled"
    if not folder.is_dir() or folder.is_symlink():
        raise NovAuditRejected("No safe repository schedule directory")
    records={}
    videos=set()
    for path in sorted(folder.glob("*.json")):
        # Retain only directly named NOVEMBER entries by asserted date_local.
        obj=_json(path)
        ds=obj.get("date_local")
        if not isinstance(ds,str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}",ds):
            continue
        day=date.fromisoformat(ds)
        if not START<=day<=END:
            continue
        slot=_slot_name(obj)
        video=obj.get("youtube_video_id")
        if not isinstance(video,str) or not VIDEO_ID.fullmatch(video):
            raise NovAuditRejected("Invalid original video ID, no replacement authorized")
        if video in videos or (ds,slot) in records:
            raise NovAuditRejected("Duplicate video ID or daily slot in old schedule")
        videos.add(video)
        if obj.get("remote_publish_at_utc")!=_utc_for(day,next(c for n,k,c in SLOTS if n==slot)):
            raise NovAuditRejected("Historical remote time does not match fixed IST slot")
        eid=obj.get("id")
        if not isinstance(eid,str) or not EPISODE_ID.fullmatch(eid):
            raise NovAuditRejected("Unrecognized episode identifier")
        if path.name!=eid+".json":
            raise NovAuditRejected("Receipt filename does not match episode")
        source=root/"content"/"episodes"/(eid+".json")
        has_source=False
        captions=0
        if source.is_file() and not source.is_symlink():
            episode=_json(source)
            if episode.get("id")!=eid or episode.get("youtube_video_id") not in (None,video):
                raise NovAuditRejected("Source episode no longer binds original ID")
            cues=episode.get("captions")
            if type(cues) is list and len(cues)>=3:
                captions=len(cues)
                has_source=True
        records[(ds,slot)]={
            "original_id":eid,
            "original_youtube_video_id":video,
            "previous_remote_privacy_recorded":obj.get("remote_privacy"),
            "previous_upload_status_recorded":obj.get("remote_upload_status"),
            "historically_scheduled_verified":obj.get("status")=="scheduled_verified",
            "historical_confirmation_not_live_readback":True,
            "source_caption_manifest_in_github":has_source,
            "source_caption_count":captions,
            "exact_original_render_project_archived_in_repo":False,
            "new_replacement_media_approved":False,
            "new_replacement_uploaded":False,
            "same_video_id_binary_replacement_possible":False,
        }
    return records


def build_nov_repair_inventory(root:Path)->dict:
    root=Path(root)
    if not root.is_dir() or root.is_symlink():
        raise NovAuditRejected("Requires checked out GitHub repository, not user machine")
    records=_index_historical_receipts(root)
    entries=[]
    day=START
    while day<=END:
        for name,kind,clock in SLOTS:
            key=(day.isoformat(),name)
            evidence=records.get(key)
            entries.append({
                "date_ist":day.isoformat(),
                "slot":name,"kind":kind,
                "local_clock_ist":clock,
                "utc_publish_at":_utc_for(day,clock),
                "evidence_state":(
                    "HISTORICAL_GITHUB_RECEIPT_CURRENT_REMOTE_UNCHECKED"
                    if evidence else
                    "NO_GITHUB_RECEIPT_REMOTE_STATUS_UNKNOWN"),
                "historical":evidence,
                "ring_spinner_problem_reported_by_owner_global_not_video_id_proven":True,
                "existing_remote_video_changed":False,
                "replacement_video_uploaded":False,
                "needs_readonly_owner_youtube_videos_list_for_current_status":True,
            })
        day+=timedelta(days=1)
    return {
        "status":STATUS,
        "source":"GitHub state/scheduled + content/episodes ONLY",
        "channel_expected":CHANNEL,
        "date_start_ist":START.isoformat(),
        "date_end_ist":END.isoformat(),
        "expected_three_slots":len(entries),
        "historical_repo_receipt_count":len(records),
        "no_repo_evidence_slot_count":len(entries)-len(records),
        "real_youtube_current_readback_performed":False,
        "owner_screenshot_specific_original_video_ids_verified":False,
        "original_video_bytes_in_repo_or_replacement_ready":False,
        "safe_replacement_order":[
            "Verify original video is currently private/scheduled and owned by expected channel",
            "Locate exact authorized original script/source and rights; reject if missing",
            "Re-render without repeating decorative circle; independently inspect complete voice and visuals",
            "Get owner full watch/listen/facts/rights approval for specific new MP4 SHA",
            "Upload only approved corrected file as private; check processing, original captions, channel and new ID",
            "Verify duplicate-free future IST slot and carefully remove or reschedule original only after explicit owner approval",
            "Verify final remote private publishAt readback, then update GitHub signed record",
        ],
        "never_delete_or_unpublish_original_automatically":True,
        "no_laptop_storage_or_api_secrets_used":True,
        "slots":entries,
    }


def render_inventory_json(root:Path)->str:
    return json.dumps(build_nov_repair_inventory(root),indent=2,sort_keys=True)+"\n"


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(description="GitHub-only Nov5–11 schedule audit, NO uploads")
    parser.add_argument("--repository",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    target=Path(args.out)
    if not target.is_absolute() or target.exists() or target.is_symlink():
        raise SystemExit("Use new absolute output under ephemeral CI workspace")
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(render_inventory_json(args.repository),encoding="utf8")
    print(json.dumps({
        "status":STATUS,"note":"Historical GitHub receipts, NOT current YouTube or repair",
        "out":str(target),
    }))
