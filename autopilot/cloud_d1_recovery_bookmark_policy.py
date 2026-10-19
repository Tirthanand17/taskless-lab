"""Phase 4I — Cloudflare D1 Time Travel bookmark read-only evidence policy.

Cloudflare provides GET /time_travel/bookmark (D1 Read) and a separate,
MUTATING POST /time_travel/restore. This module has ZERO transport methods:
it strictly parses two untrusted GET-shaped responses supplied by a caller
and compares the opaque bookmark in memory, without returning its contents.

D1 Free plan Time Travel recovery is documented at <=7 days; this policy
NEVER claims that the retention horizon is proven on a particular account,
that a historical bookmark can be restored, or that equal bookmarks prove
snapshot isolation / real Cloudflare identity. No read/write/cloud call.
"""
from __future__ import annotations

from typing import Any
import re

from .agent_org import WorkflowError

MAX_BOOKMARK_CHARS=256
BOOKMARK=re.compile(r"[A-Za-z0-9._-]{8,256}\Z")
MAX_RESPONSE_MESSAGES=20


def _parse_untrusted_bookmark(body:Any)->str:
    # Refuse error metadata that can carry injected strings in logs.
    if type(body) is not dict or not {"success","result"}.issubset(body):
        raise WorkflowError("D1 recovery bookmark response is malformed")
    if (body["success"] is not True
            or body.get("errors",[])!=[]
            or type(body["result"]) is not dict
            or set(body["result"])!={"bookmark"}):
        raise WorkflowError("D1 recovery bookmark response is not read-only evidence")
    if "messages" in body and (
            type(body["messages"]) is not list
            or len(body["messages"])>MAX_RESPONSE_MESSAGES):
        raise WorkflowError("D1 bookmark response messages are malformed")
    value=body["result"]["bookmark"]
    if (type(value) is not str
            or BOOKMARK.fullmatch(value) is None
            or len(value)>MAX_BOOKMARK_CHARS):
        raise WorkflowError("D1 bookmark absent or unsupported")
    # Do not parse age, database ID, restoration availability or account
    # identity from this opaque string; its pattern is not a timestamp.
    return value


def screen_untrusted_d1_time_travel_bookmarks(
    *,initial_response:dict,final_response:dict,
    recovery_plan:str,
)->dict:
    """Compare two entirely caller-provided GET-shaped bookmarks, no I/O."""
    if recovery_plan!="workers_free":
        raise WorkflowError("Only explicitly modeled zero-spend D1 Free recovery policy")
    initial=_parse_untrusted_bookmark(initial_response)
    final=_parse_untrusted_bookmark(final_response)
    changed=initial!=final
    reasons={
        "D1_REAL_PROVIDER_IDENTITY_NOT_INDEPENDENTLY_AUTHENTICATED",
        "D1_BOOKMARK_DOES_NOT_PROVE_RECOVERABLE_RESTORE",
        "D1_FREE_RETENTION_ACTUAL_ACCOUNT_NOT_VERIFIED",
        "D1_TIME_TRAVEL_RESTORE_NOT_EXECUTED",
        "D1_RELEASE_BACKUP_EVENT_LOG_NOT_VERIFIED",
        "D1_CROSS_PROVIDER_SNAPSHOT_ATOMICITY_NOT_PROVEN",
    }
    if changed:
        reasons.add("D1_BOOKMARK_CHANGED_BETWEEN_READS_QUARANTINE")
    else:
        reasons.add("D1_BOOKMARK_EQUALITY_DOES_NOT_PROVE_SNAPSHOT")
    return {
        "status":"D1_TIME_TRAVEL_BOOKMARK_SHAPE_SCREEN_UNTRUSTED",
        "modeled_workers_plan":"free",
        "documented_free_plan_recovery_days":7,
        "two_bookmark_responses_well_formed":True,
        "bookmark_changed_between_reads":changed,
        "bookmark_values_exposed":False,
        "live_source_verified":False,
        "recovery_bookmark_freshness_verified":False,
        "real_historical_restore_verified":False,
        "full_database_backup_available_verified":False,
        "event_log_restore_verified":False,
        "production_writer_fence_verified":False,
        "source_channel_identity_verified":False,
        "d1_restore_post_authorized":False,
        "d1_export_post_authorized":False,
        "d1_schema_migration_authorized":False,
        "youtube_upload_retry_authorized":False,
        "youtube_publishing_authorized":False,
        "blocker_codes":tuple(sorted(reasons)),
        "provider_api_requests":0,
        "cloud_database_writes":0,
        "monthly_recurring_infrastructure_inr":0,
    }
