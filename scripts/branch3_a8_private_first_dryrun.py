"""Clivox A8: private-first scheduling / idempotency **DRY RUN**.

NO network, OAuth, YouTube API, media or actual uploads. Proof fields cannot
be fabricated into authorization. Ledger operations are pure, in-memory
proposals only; GitHub Actions concurrency is not a distributed upload lock.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"branch3/a8/fixtures/private-first-dryrun.json"
LEDGER=ROOT/"branch3/a8/fixtures/empty-upload-ledger.json"
CLIVOX="UCfPEvy0SefE_5nNlYlY_CyQ"
SHA=re.compile(r"[0-9a-f]{64}\Z")
ID=re.compile(r"clivox_[a-z0-9][a-z0-9_-]{10,100}\Z")

class DryRunBlocked(ValueError):
    pass

def require(value:bool,reason:str)->None:
    if not value:
        raise DryRunBlocked("CLIVOX_A8_DENY_"+reason)

def utc(value:str)->datetime:
    require(type(value) is str and value.endswith("Z"),"UTC_REQUIRED")
    try: result=datetime.fromisoformat(value[:-1]+"+00:00")
    except (TypeError,ValueError):
        raise DryRunBlocked("CLIVOX_A8_DENY_INVALID_TIMESTAMP") from None
    require(result.utcoffset()==timedelta(0),"BAD_UTC")
    return result

def schedule_preflight(publish_at:str,now:datetime,privacy:str="private",
                       target_channel_id:str=CLIVOX)->dict:
    require(target_channel_id==CLIVOX,"WRONG_CHANNEL")
    require(privacy=="private","NOT_PRIVATE_FIRST")
    require(now.tzinfo is not None and now.utcoffset() is not None,"NAIVE_CLOCK")
    future=utc(publish_at)
    require(future>now.astimezone(timezone.utc)+timedelta(minutes=30),
            "PAST_OR_TOO_EARLY_SCHEDULE")
    return {
        "future_utc_timestamp_valid":True,
        "min_safety_margin_minutes":30,
        "initial_privacy":"private",
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False
    }

def validate_fixture(plan:dict,ledger:dict)->dict:
    require(type(plan) is dict and set(plan)=={
        "schema_version","channel_id","stage","mode","source_release_id",
        "license_status","owner_exact_asset_signature_verified",
        "owner_google_upload_oauth_verified",
        "github_protected_release_environment_verified",
        "real_media_sha256","metadata_sha256","rights_evidence_sha256",
        "privacy_status","planned_publish_at_utc","simulated_now_utc",
        "publish_at_is_not_a_real_schedule","production_actions",
        "idempotency","source_first_party_only","video_contains_licensed_clip",
        "plan_not_release_permission","notes"
    },"PLAN_FIELDS")
    require(plan["schema_version"]==1 and plan["channel_id"]==CLIVOX
            and plan["stage"]=="A8_PRIVATE_FIRST_RELEASE_DRYRUN"
            and plan["mode"]=="NO_YOUTUBE_NETWORK_NO_UPLOAD","LIVE_RUN_ATTEMPT")
    require(type(plan["source_release_id"]) is str and
            ID.fullmatch(plan["source_release_id"]) is not None,"RELEASE_ID")
    require(plan["license_status"]=="UNVERIFIED"
            and plan["source_first_party_only"] is False
            and plan["video_contains_licensed_clip"] is False,
            "FALSE_RIGHTS_STATE")
    for f in ("owner_exact_asset_signature_verified",
              "owner_google_upload_oauth_verified",
              "github_protected_release_environment_verified"):
        require(plan[f] is False,"PREMATURE_APPROVAL_"+f)
    for f in ("real_media_sha256","metadata_sha256","rights_evidence_sha256"):
        require(plan[f] is None,"FAKE_REAL_SHA_"+f)
    require(type(plan["production_actions"]) is dict and
            set(plan["production_actions"])=={
                "source_download","video_insert","video_update",
                "video_delete","video_schedule","video_publish"
            } and all(v is False for v in plan["production_actions"].values()),
            "PRODUCTION_WRITE_ON")
    require(plan["idempotency"]=={
        "require_attempt_lease":True,
        "require_remote_readback_before_retry":True,
        "allow_blind_retry":False,
        "ledger_is_durable":False,
        "real_remote_video_inventory_verified":False,
    },"IDEMPOTENCE_CLAIMS")
    require(plan["publish_at_is_not_a_real_schedule"] is True
            and plan["plan_not_release_permission"] is True,
            "CLAIMED_REAL_SCHEDULE")
    preview=schedule_preflight(plan["planned_publish_at_utc"],
        utc(plan["simulated_now_utc"]),plan["privacy_status"],plan["channel_id"])
    validate_empty_ledger(ledger)
    return {
        "stage":"A8_PRIVATE_FIRST_DRY_RUN",
        "channel_id":CLIVOX,
        "status":"QUARANTINED_LACKING_LICENSE_AND_SIGNED_ASSET",
        "fixture_timestamp_only":True,
        "future_utc_example_preflight":preview,
        "real_creator_license_verified":False,
        "real_exact_asset_signed":False,
        "real_google_upload_oauth_connected":False,
        "protected_environment_enabled":False,
        "persistent_atomic_upload_lock_implemented":False,
        "remote_video_inventory_reconciled":False,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
        "actual_youtube_network_calls":0
    }

def validate_empty_ledger(ledger:dict)->None:
    require(type(ledger) is dict and set(ledger)=={
        "schema_version","channel_id","state","reservations",
        "remote_video_ids","contains_private_data",
        "atomic_persistent_lock_enabled","remote_api_writes","notes"
    },"LEDGER_FIELDS")
    require(ledger["schema_version"]==1 and
            ledger["channel_id"]==CLIVOX and
            ledger["state"]=="EMPTY_NO_LIVE_UPLOADS"
            and ledger["reservations"]==[] and ledger["remote_video_ids"]==[]
            and ledger["contains_private_data"] is False
            and ledger["atomic_persistent_lock_enabled"] is False
            and ledger["remote_api_writes"]==0,"FALSE_LEDGER")
    require(type(ledger["notes"]) is str and
            len(ledger["notes"])<=500,"LEDGER_NOTES")

def candidate_attempt_key(*,channel_id:str,release_id:str,
                          media_sha256:str,metadata_sha256:str,
                          rights_evidence_sha256:str)->str:
    """Pure idempotency key for the *exact* release subject; not permission."""
    require(channel_id==CLIVOX,"WRONG_CHANNEL")
    require(type(release_id) is str and ID.fullmatch(release_id) is not None,
            "RELEASE_ID")
    for d in (media_sha256,metadata_sha256,rights_evidence_sha256):
        require(type(d) is str and SHA.fullmatch(d) is not None,"RELEASE_DIGEST")
    msg=json.dumps({
        "version":1,"channel_id":channel_id,"release_id":release_id,
        "media_sha256":media_sha256,"metadata_sha256":metadata_sha256,
        "rights_evidence_sha256":rights_evidence_sha256
    },sort_keys=True,separators=(",",":"))
    return hashlib.sha256(b"CLIVOX-A8-EXACT-ATTEMPT-V1\n"+msg.encode()).hexdigest()

def reserve_attempt_preview(existing:list[dict],attempt_key:str)->dict:
    """In-memory conflict detection only. NOT atomic across workflow runs."""
    require(type(existing) is list and len(existing)<=1000,"RESERVATION_COLLECTION")
    require(type(attempt_key) is str and SHA.fullmatch(attempt_key) is not None,"ATTEMPT_KEY")
    for r in existing:
        require(type(r) is dict and set(r)=={"key","status"},"RESERVATION_ENTRY")
        require(type(r["key"]) is str and SHA.fullmatch(r["key"]) is not None,
                "RESERVATION_KEY")
        require(r["status"] in {
            "ATTEMPT_RESERVED","UNKNOWN_REMOTE_STATE_RECONCILE",
            "PRIVATE_UPLOADED_CONFIRMED","SCHEDULED_CONFIRMED",
        },"UNKNOWN_RESERVATION_STATE")
        if r["key"]==attempt_key:
            return {
                "decision":"BLOCK_DUPLICATE_OR_AMBIGUOUS_ATTEMPT",
                "remote_inventory_reconciliation_required":True,
                "automatic_retry_allowed":False,
                "upload_authorized":False
            }
    return {
        "decision":"DRY_RUN_ONLY_KEY_NOT_PRESENT",
        "remote_inventory_reconciliation_required":True,
        "atomic_persistent_lock_required":True,
        "automatic_retry_allowed":False,
        "upload_authorized":False
    }

def reconcile_ambiguous_attempt(*,attempt_status:str,
                                remote_readback_verified:bool)->dict:
    require(attempt_status in (
        "ATTEMPT_RESERVED","UNKNOWN_REMOTE_STATE_RECONCILE",
        "PRIVATE_UPLOADED_CONFIRMED","SCHEDULED_CONFIRMED"
    ),"UNKNOWN_ATTEMPT")
    require(type(remote_readback_verified) is bool,"READBACK_FLAG")
    # Even fake JSON saying "readback verified" cannot clear a real ambiguity.
    return {
        "decision":"HOLD_FOR_AUTHENTICATED_REMOTE_READBACK_AND_OWNER_REVIEW",
        "blind_retry_allowed":False,
        "upload_authorized":False,
        "remote_readback_assertion_is_not_proof":True
    }

def perform_upload_or_schedule(*_args,**_kwargs)->None:
    raise DryRunBlocked("CLIVOX_A8_DENY_LIVE_YOUTUBE_WRITE_NOT_IMPLEMENTED")

def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    report=validate_fixture(json.loads(PLAN.read_text("utf-8")),
                            json.loads(LEDGER.read_text("utf-8")))
    text=json.dumps(report,indent=2)+"\n"
    if args.out:
        require(not args.out.is_symlink(),"OUTPUT_LINK")
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(text,encoding="utf-8")
    else:
        print(text,end="")
    print("CLIVOX_A8_PRIVATE_FIRST_DRYRUN_NO_GOOGLE_API_WRITES")

if __name__=="__main__":
    main()
