"""CLIVOX A8: offline crash/ambiguous-upload safety evaluator and CAS fault model.

This module NEVER connects to GitHub, Google, or private footage. It accepts
only already-decoded, strict A8 chain records and an explicitly caller-supplied
(non-independently verified) prior head. Even a matching inventory *claim* is
not an upload receipt or video-binary SHA proof. EVERY path remains HOLD.

Deterministic synthetic adversarial interleavings test fail-closed behavior;
they do NOT establish live GitHub cross-run linearizability, rollback
resistance, Google OAuth authorization, legal rights, or video publishing.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import random

from scripts.branch3_a8_private_first_dryrun import (
    CLIVOX, SHA, ID, candidate_attempt_key
)
from scripts.branch3_a8_private_cas_ledger import (
    GENESIS, PrivateCASBlocked, new_ledger, append_simulated_event,
    build_github_put_contract, simulate_cas, verify_ledger,
)
from scripts.branch3_a2_private_ledger_cas import git_blob_sha
from scripts.branch3_a8_private_cas_ledger import bytes_for_ledger

SCENARIOS=frozenset((
    "NO_WRITE_STARTED", "GITHUB_READ_FAILED", "CAS_CONFLICT_409",
    "CAS_VALIDATION_422", "CAS_TIMEOUT_UNKNOWN", "CAS_HTTP_200_UNVERIFIED",
    "CAS_CONFIRMED_READBACK", "CRASH_AFTER_PUT_UNKNOWN",
    "READBACK_FAILED", "READBACK_MISMATCH",
    "YOUTUBE_UPLOAD_RESPONSE_UNKNOWN", "YOUTUBE_VIDEO_ID_UNVERIFIED"
))
INVENTORY_STAGE="A8_OWNER_READONLY_CLIVOX_UPLOAD_INVENTORY_SNAPSHOT"
MAX_WORKERS=12
ANCHOR={"sequence":0,"head_sha256":GENESIS}
NOW=datetime(2026,11,13,12,0,tzinfo=timezone.utc)
AT="2026-11-13T11:59:00Z"


class RecoveryBlocked(ValueError):
    """Safety invariant failed, never turn this exception into a retry."""


def require(ok:bool,reason:str)->None:
    if not ok:
        raise RecoveryBlocked("CLIVOX_A8_RECOVERY_DENY_"+reason)


def check_inventory_claim(claim:dict|None)->bool:
    """Only inspect the *shape* of caller-supplied aggregate metadata.

    A JSON report is not authenticated evidence. Owner OAuth + exact channel
    must be verified by the separate protected read-only adapter.
    """
    if claim is None:
        return False
    require(type(claim) is dict and claim.get("stage")==INVENTORY_STAGE
            and claim.get("channel_id")==CLIVOX
            and claim.get("owner_google_channel_identity_matched") is True
            and claim.get("uploaded_playlist_pagination_exhausted_within_limit") is True
            and claim.get("statuses_checked_through_videos_list") is True,
            "INVENTORY_CLAIM_ORIGIN")
    for k in ("real_time_remote_completeness_guaranteed",
              "exact_uploaded_binary_sha256_verified",
              "ambiguous_ledger_attempt_automatically_reconciled",
              "automatic_duplicate_retry_authorized",
              "youtube_upload_authorized","youtube_schedule_authorized",
              "youtube_publish_authorized"):
        require(claim.get(k) is False,"PROMOTED_INVENTORY_AUTH_"+k)
    require(claim.get("actual_youtube_write_calls")==0
            and type(claim.get("actual_youtube_write_calls")) is int,
            "INVENTORY_WRITE_CLAIM")
    keys=("uploaded_playlist_pages_checked","uploaded_playlist_videos_checked",
          "private_count","unlisted_count","public_count",
          "private_with_schedule_count","youtube_readonly_get_count")
    for k in keys:
        require(type(claim.get(k)) is int and claim[k]>=0,
                "INVENTORY_COUNT_"+k)
    total=(claim["private_count"]+claim["unlisted_count"]
           +claim["public_count"])
    require(total==claim["uploaded_playlist_videos_checked"]
            and claim["private_with_schedule_count"]<=claim["private_count"]
            and 1<=claim["uploaded_playlist_pages_checked"]<=20
            and total<=1000 and claim["youtube_readonly_get_count"]>=2,
            "INVENTORY_COUNTS_INCONSISTENT")
    # This deliberately does not return any private video identifiers,
    # and does not label the self-provided claim as a real authenticated read.
    return True


def classify_recovery(*,ledger:dict,anchor:dict,now:datetime,
                      release_id:str,media_sha256:str,
                      metadata_sha256:str,rights_evidence_sha256:str,
                      scenario:str,inventory_claim:dict|None=None)->dict:
    """Offline adjudication of ambiguous CAS/YouTube outcomes.

    We deliberately never return 'retry', 'upload', 'schedule' or 'publish'.
    A no-reservation result cannot prove the previous PUT failed to commit.
    """
    require(type(scenario) is str and scenario in SCENARIOS,"SCENARIO")
    require(type(now) is datetime and now.tzinfo is not None
            and now.utcoffset() is not None,"CLOCK")
    try:
        check=verify_ledger(ledger,anchor=anchor,now=now)
        attempt=candidate_attempt_key(
            channel_id=CLIVOX,release_id=release_id,
            media_sha256=media_sha256,metadata_sha256=metadata_sha256,
            rights_evidence_sha256=rights_evidence_sha256
        )
    except (PrivateCASBlocked,ValueError,TypeError):
        raise RecoveryBlocked(
            "CLIVOX_A8_RECOVERY_DENY_LEDGER_OR_ATTEMPT"
        ) from None
    claim_seen=check_inventory_claim(inventory_claim)
    events=ledger["events"]
    own=[x for x in events if x["attempt_key"]==attempt]
    reserved=any(x["kind"]=="RESERVE_SYNTHETIC" for x in own)
    unknown=any(x["kind"]=="MARK_UNKNOWN_NO_RETRY" for x in own)
    same_asset_other_subject=any(
        x["kind"]=="RESERVE_SYNTHETIC" and
        (x["release_id"]==release_id or x["media_sha256"]==media_sha256)
        and x["attempt_key"]!=attempt for x in events
    )
    if same_asset_other_subject:
        decision="HOLD_DUPLICATE_RELEASE_OR_MEDIA_CROSS_ATTEMPT"
    elif not reserved:
        if scenario=="CAS_CONFIRMED_READBACK":
            decision="HOLD_CONTRADICTORY_COMMIT_CONFIRMATION"
        else:
            decision="HOLD_NO_PROVEN_RESERVATION_NO_RETRY"
    elif unknown:
        decision="HOLD_UNKNOWN_REMOTE_STATE_OWNER_MUST_RECONCILE"
    elif scenario in ("YOUTUBE_UPLOAD_RESPONSE_UNKNOWN",
                      "YOUTUBE_VIDEO_ID_UNVERIFIED"):
        decision="HOLD_YOUTUBE_ID_OR_ORIGINAL_FILE_SHA_NOT_AUTHENTICATED"
    elif scenario=="CAS_CONFLICT_409":
        decision="HOLD_GITHUB_CAS_CONFLICT_NO_SECOND_WRITE"
    elif scenario=="CAS_CONFIRMED_READBACK":
        decision="HOLD_GITHUB_RESERVATION_CONFIRMED_NOT_YOUTUBE_PERMISSION"
    elif scenario in ("NO_WRITE_STARTED","GITHUB_READ_FAILED"):
        decision="HOLD_EXISTING_ATTEMPT_NO_NEW_WRITE"
    else:
        decision="HOLD_AMBIGUOUS_GITHUB_COMMIT_NO_RETRY"
    return {
        "stage":"A8_OFFLINE_CRASH_RECOVERY_STRICT_HOLD",
        "channel_id":CLIVOX,
        "scenario":scenario,
        "decision":decision,
        "exact_attempt_event_seen":reserved,
        "attempt_ever_marked_remote_unknown":unknown,
        "duplicate_release_or_media_other_attempt_seen":same_asset_other_subject,
        "global_event_chain_replayed":check["all_attempts_hold_no_network"],
        "caller_prior_anchor_matched":check["snapshot_matches_caller_supplied_anchor"],
        "owner_supplied_inventory_report_shape_checked":claim_seen,
        "authenticated_google_inventory_proven_by_this_function":False,
        "original_uploaded_video_binary_sha256_proven":False,
        "external_anchor_immutability_proven":False,
        "real_remote_cas_linearizability_proven":False,
        "owner_manual_reconciliation_required":True,
        "second_github_put_allowed":False,
        "automatic_upload_retry_allowed":False,
        "youtube_video_insert_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
        "github_api_calls":0,
        "google_api_calls":0,
    }


def synthetic_subject(i:int)->dict:
    require(type(i) is int and 0<=i<MAX_WORKERS,"WORKER_ID")
    # Every value is explicitly fake, synthetic, unrelated to actual media.
    return {
        "release_id":f"clivox_recovery_synthetic_{i:04}",
        "media_sha256":f"{i+1:064x}",
        "metadata_sha256":f"{100+i:064x}",
        "rights_evidence_sha256":f"{200+i:064x}",
    }


def simulate_competing_workers(*,workers:int,seed:int,
                               same_media:bool=True)->dict:
    """Model all workers reading same old global blob before a first CAS.

    One update wins in this synthetic server model; all stale PUTs fail;
    a post-CAS crash only causes holds. No modelled Google network.
    Not a claim about production GitHub linearizability.
    """
    require(type(workers) is int and 2<=workers<=MAX_WORKERS,
            "WORKERS_BOUNDS")
    require(type(seed) is int and 0<=seed<=100_000,"SEED_BOUNDS")
    require(type(same_media) is bool,"SHARED_MEDIA_FLAG")
    first=new_ledger()
    old_blob=git_blob_sha(bytes_for_ledger(first))
    subjects=[]
    requests=[]
    for i in range(workers):
        subject=synthetic_subject(i)
        if same_media:
            subject["media_sha256"]=synthetic_subject(0)["media_sha256"]
        subjects.append(subject)
        proposed=append_simulated_event(
            first,kind="RESERVE_SYNTHETIC",at_utc=AT,
            anchor=ANCHOR,now=NOW,**subject
        )
        requests.append((
            proposed,
            build_github_put_contract(
                existing_blob_sha=old_blob,updated=proposed,
                anchor=ANCHOR,now=NOW
            )
        ))
    order=list(range(workers))
    random.Random(seed).shuffle(order)
    current_blob=old_blob
    ledger=first
    accepted=0
    conflicts=0
    winner_index=None
    for i in order:
        next_ledger,body=requests[i]
        try:
            new_blob=simulate_cas(
                current_remote_blob_sha=current_blob,
                proposed_body=body,anchor=ANCHOR,now=NOW
            )
        except PrivateCASBlocked:
            conflicts+=1
            continue
        require(accepted==0,"SECOND_COMMIT_ACCEPTED_IN_MOCK")
        current_blob=new_blob
        ledger=next_ledger
        accepted+=1
        winner_index=i
    require(accepted==1 and conflicts==workers-1,"CAS_MODEL_CONFLICT")
    verified=verify_ledger(ledger,anchor=ANCHOR,now=NOW)
    require(verified["attempt_count"]==1 and verified["event_count"]==1,
            "GLOBAL_DUPLICATE_LEAK")
    decisions=[]
    for i,subject in enumerate(subjects):
        decisions.append(classify_recovery(
            ledger=ledger,anchor=ANCHOR,now=NOW,
            scenario="CRASH_AFTER_PUT_UNKNOWN"
                     if i==winner_index else "CAS_CONFLICT_409",
            **subject
        ))
    require(all(
        d["automatic_upload_retry_allowed"] is False and
        d["second_github_put_allowed"] is False and
        d["youtube_video_insert_authorized"] is False and
        d["youtube_publish_authorized"] is False
        for d in decisions),"MODEL_FAIL_OPEN")
    return {
        "stage":"A8_SYNTHETIC_MULTI_WORKER_CRASH_MODEL_NO_REMOTE_API",
        "worker_count":workers,
        "accepted_synthetic_cas_updates":accepted,
        "rejected_stale_cas_updates":conflicts,
        "global_attempt_count":verified["attempt_count"],
        "all_workers_explicit_hold":True,
        "crash_after_commit_reread_cannot_authorize_upload":True,
        "private_github_live_network_verified":False,
        "github_linearizable_concurrency_proven":False,
        "real_immutable_anchor_proven":False,
        "youtube_video_insert_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
        "actual_github_requests":0,
        "actual_google_requests":0,
    }


def fixture_report()->dict:
    all_runs=[
        simulate_competing_workers(workers=w,seed=seed,same_media=(seed%2==0))
        for w in (2,4,8,12) for seed in range(8)
    ]
    return {
        "stage":"A8_FAIL_CLOSED_MULTI_WORKER_RECOVERY_OFFLINE_ONLY",
        "synthetic_scenarios_exercised":len(all_runs),
        "max_worker_count":MAX_WORKERS,
        "all_scenarios_one_model_reservation_only":all(
            x["global_attempt_count"]==1 for x in all_runs
        ),
        "all_scenarios_never_retry_or_upload":all(
            x["all_workers_explicit_hold"] and
            x["accepted_synthetic_cas_updates"]==1
            for x in all_runs
        ),
        "real_global_cas_writer_deployed":False,
        "external_rollback_resistant_anchor_enrolled":False,
        "real_upload_receipt_reconciled":False,
        "real_owner_video_release_approved":False,
        "actual_github_api_calls":0,
        "actual_google_api_calls":0,
        "youtube_video_insert_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
    }


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("fixture",),default="fixture")
    p.parse_args()
    print(json.dumps(fixture_report(),sort_keys=True))


if __name__=="__main__":
    main()
