"""Phase 4E.1: OFFLINE sanitized D1/YouTube read-only response adapters.

This module NEVER calls Cloudflare, Google, or the network, never reads credentials
and NEVER verifies that input was genuinely obtained from either provider.
It accepts manually supplied *sanitized provider-shaped* metadata and produces
a minimum-information compatibility report. Do not put real data in public CI.
"""
from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Mapping, Sequence

from .core import CHANNEL_ID
from .phase4b_readonly_audit import AuditBlocked, PROTECTED, VIDEO_ID

IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,99}\Z")
ALLOWED_KINDS = frozenset(("table", "view", "virtual", "shadow"))
PRIVACY = frozenset(("private", "public", "unlisted"))
PROCESSING = frozenset(("succeeded", "processing", "failed", "terminated"))


def _list(value, *, max_items: int, label: str) -> list:
    if not isinstance(value, list) or len(value) > max_items:
        raise AuditBlocked("Bounded " + label + " array required")
    return value


def _mapping(value, label: str) -> Mapping:
    if not isinstance(value, Mapping):
        raise AuditBlocked("Malformed " + label + " object")
    return value


def _safe_name(value: object) -> str | None:
    if not isinstance(value, str) or IDENTIFIER.fullmatch(value) is None:
        return None
    return value


def parse_d1_schema_observation(
    *, table_list_rows: list, table_details: Mapping,
) -> dict:
    """Read only already retrieved PRAGMA-shaped metadata; no SQL executes.

    Accepts PRAGMA table_list rows and optional safe per-table details:
    {"columns":[{"name":"...","type":"...","pk":0}], "indexes":[
      {"unique":true,"columns":["channel_id","episode_id"]}]}
    Drops default values and SQL definitions; skips protected table/column names.
    Presence of these shapes is not proof of an actual live D1 query.
    """
    rows=_list(table_list_rows,max_items=200,label="D1 table_list")
    _mapping(table_details,"table details")
    if len(table_details)>200:
        raise AuditBlocked("Excessive D1 table detail count")
    safe_objects=[]
    skipped_protected=0
    skipped_unsafe=0
    seen=set()
    for raw in rows:
        r=_mapping(raw,"table_list row")
        name=_safe_name(r.get("name"))
        if not name:
            skipped_unsafe+=1
            continue
        if name in seen:
            raise AuditBlocked("Duplicate D1 table metadata")
        seen.add(name)
        if PROTECTED.search(name):
            skipped_protected+=1
            continue
        if r.get("schema") not in ("main",None):
            skipped_unsafe+=1
            continue
        kind=r.get("type")
        if kind not in ALLOWED_KINDS:
            skipped_unsafe+=1
            continue
        if name.startswith("sqlite_") or name.startswith("_cf_"):
            continue
        detail = table_details.get(name, {})
        _mapping(detail,"table detail")
        cols=[]
        seen_cols=set()
        for item in _list(detail.get("columns",[]),max_items=100,label="columns"):
            row=_mapping(item,"column metadata")
            col=_safe_name(row.get("name"))
            if not col or PROTECTED.search(col):
                continue
            if col in seen_cols:
                raise AuditBlocked("Duplicate column metadata")
            seen_cols.add(col)
            typ=row.get("type","")
            # Types may be arbitrary SQL type expressions: do not echo them.
            cols.append({"name":col,"primary_key":bool(row.get("pk",0))})
        indexes=[]
        for item in _list(detail.get("indexes",[]),max_items=40,label="indexes"):
            row=_mapping(item,"index metadata")
            names=_list(row.get("columns",[]),max_items=30,label="index columns")
            fields=[]
            for column in names:
                safe=_safe_name(column)
                if safe is not None and not PROTECTED.search(safe):
                    fields.append(safe)
            if len(fields)!=len(names) or not fields:
                # Never claim that a redacted index proves uniqueness.
                continue
            indexes.append({"unique":row.get("unique") is True,"columns":fields})
        safe_objects.append({"name":name,"kind":kind,
                             "columns":sorted(cols,key=lambda x:x["name"]),
                             "indexes":sorted(indexes,key=lambda x:(x["columns"],x["unique"]))})
    safe_objects.sort(key=lambda x:x["name"])
    return {
        "origin":"UNAUTHENTICATED_D1_SHAPED_METADATA",
        "expected_channel_id":CHANNEL_ID,
        "objects":safe_objects,
        "object_count":len(safe_objects),
        "skipped_protected_objects":skipped_protected,
        "skipped_unsafe_objects":skipped_unsafe,
        "contains_data_rows":False,
        "saw_authenticated_provider_request":False,
        "requires_authorized_schema_provenance":True,
        "migration_authorized":False,
        "generated_sql":[],
        "production_writes":0,
    }


def _utc(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value,str) or len(value)>80:
        raise AuditBlocked("Invalid YouTube scheduled UTC timestamp")
    try:
        dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    except (TypeError,ValueError,OverflowError) as exc:
        raise AuditBlocked("Invalid YouTube scheduled UTC timestamp") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise AuditBlocked("Schedule is not timezone-aware")
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def parse_youtube_channel_video_observation(
    *, channel_response: Mapping, video_response: Mapping,
) -> dict:
    """Parse provider-shaped channel and video READBACK records, no API calls.

    Private video status can only be verified with actual authorized credentials.
    This adapter never treats its inputs as authenticated, even if callers add
    misleading flags such as 'verified': true.
    """
    channels=_list(_mapping(channel_response,"channel response").get("items"),max_items=2,label="channels")
    videos=_list(_mapping(video_response,"video response").get("items"),max_items=500,label="videos")
    if len(channels)!=1 or channels[0].get("id")!=CHANNEL_ID:
        raise AuditBlocked("Exactly the expected YouTube channel is required")
    raw_pagination=video_response.get("nextPageToken")
    if raw_pagination is not None and (not isinstance(raw_pagination,str) or not raw_pagination):
        raise AuditBlocked("Malformed pagination indicator")
    next_page = raw_pagination is not None
    cleaned=[]
    seen=set()
    for raw in videos:
        video=_mapping(raw,"video")
        vid=video.get("id")
        if not isinstance(vid,str) or VIDEO_ID.fullmatch(vid) is None:
            raise AuditBlocked("Invalid YouTube video ID")
        if vid in seen:
            raise AuditBlocked("Repeated YouTube video ID")
        seen.add(vid)
        snippet=_mapping(video.get("snippet"),"video snippet")
        if snippet.get("channelId") != CHANNEL_ID:
            raise AuditBlocked("Video owned by a different channel")
        status=_mapping(video.get("status"),"video status")
        privacy=status.get("privacyStatus")
        if privacy not in PRIVACY:
            raise AuditBlocked("Unknown video privacy status")
        scheduled=_utc(status.get("publishAt"))
        details=video.get("processingDetails")
        if details is None:
            processing="unknown"
        else:
            details=_mapping(details,"processing details")
            processing=details.get("processingStatus","unknown")
            if processing not in PROCESSING and processing!="unknown":
                raise AuditBlocked("Unrecognized processing status")
        inconsistent = bool(privacy!="private" and scheduled is not None)
        cleaned.append({"youtube_id":vid,"channel_id":CHANNEL_ID,
                        "privacy":privacy,"processing":processing,
                        "publish_at_utc":scheduled,
                        "uncertain_metadata":inconsistent or processing=="unknown"})
    cleaned.sort(key=lambda v:v["youtube_id"])
    return {
        "origin":"UNAUTHENTICATED_YOUTUBE_SHAPED_METADATA",
        "channel_id":CHANNEL_ID,
        "video_count":len(cleaned),
        "videos":cleaned,
        "pagination_complete":not next_page,
        "has_conflicting_state":any(v["uncertain_metadata"] for v in cleaned),
        "contains_titles_or_descriptions":False,
        "saw_authenticated_provider_request":False,
        "migration_authorized":False,
        "publication_authorized":False,
        "network_calls":0,
        "production_writes":0,
        "blockers":[
            "AUTHENTICATED_YOUTUBE_OAUTH_OWNER_BINDING_NOT_ESTABLISHED",
            "INPUTS_ARE_UNTRUSTED_PROVIDER_SHAPED_CLAIMS",
            * (["VIDEO_PAGINATION_INCOMPLETE"] if next_page else []),
        ],
    }
