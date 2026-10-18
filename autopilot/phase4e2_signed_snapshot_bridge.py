"""Phase 4E.2: join SANITIZED provider-shaped readback + detached receipts.

OFFLINE ONLY. Strict structural scrutiny checks that two reports have the
exact redacted shape produced by Phase 4E.1, that independent enrolled
collector keys signed SHA-256s of these particular snapshots, and that a
fresh request nonce binds both. No APIs or production databases are accessed.

IMPORTANT: signatures authenticate bytes by pinned *externally provided*
keys only. They cannot prove that a real Cloudflare D1/YouTube call occurred.
No provider identity, historical row reconciliation, migration, release,
upload, scheduling or owner consent is established by a successful report.
No output includes video IDs, private content, account names, raw snapshots,
signatures, keys or arbitrary claimant strings. All authority remains FALSE.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Mapping, Sequence

from .core import CHANNEL_ID
from .phase4b_readonly_audit import AuditBlocked, PROTECTED, VIDEO_ID
from .phase4d_signed_observations import (
    CollectorTrust, SignedObservation, ObservationBlocked,
    sanitized_snapshot_hash, verify_readonly_observation_bundle,
)

_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,99}\Z")
_D1_TOP = frozenset((
    "origin", "expected_channel_id", "objects", "object_count",
    "skipped_protected_objects", "skipped_unsafe_objects",
    "contains_data_rows", "saw_authenticated_provider_request",
    "requires_authorized_schema_provenance", "migration_authorized",
    "generated_sql", "production_writes",
))
_YT_TOP = frozenset((
    "origin", "channel_id", "video_count", "videos", "pagination_complete",
    "has_conflicting_state", "contains_titles_or_descriptions",
    "saw_authenticated_provider_request", "migration_authorized",
    "publication_authorized", "network_calls", "production_writes",
    "blockers",
))
_D1_COLUMNS = frozenset(("name", "primary_key"))
_D1_INDEX = frozenset(("unique", "columns"))
_D1_OBJECT = frozenset(("name", "kind", "columns", "indexes"))
_YT_VIDEO = frozenset((
    "youtube_id", "channel_id", "privacy", "processing",
    "publish_at_utc", "uncertain_metadata",
))
_CANON = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+00:00\Z")
_RECOGNIZED_CANONICAL = frozenset((
    "channel_id","episode_id","planned_utc","media_sha256","version",
))
_MAX_SCHEMA_OBJECTS = 200
_MAX_VIDEO_RECORDS = 500


def _bounded_snapshot(value: Mapping, expected_keys: frozenset, label:str)->None:
    if not isinstance(value,dict) or set(value)!=expected_keys:
        raise ObservationBlocked("Malformed or unredacted "+label+" snapshot")
    # Explicit bound also catches oversized arbitrary nested strings before a
    # response could be sent to a logging destination.
    sanitized_snapshot_hash(value)


def _safe_identifier(value:object)->bool:
    return (isinstance(value,str) and _IDENT.fullmatch(value) is not None
            and not PROTECTED.search(value))


def _checked_d1(s:dict)->tuple[list[str],int]:
    _bounded_snapshot(s,_D1_TOP,"D1")
    if (s["origin"]!="UNAUTHENTICATED_D1_SHAPED_METADATA"
            or s["expected_channel_id"]!=CHANNEL_ID
            or s["contains_data_rows"] is not False
            or s["saw_authenticated_provider_request"] is not False
            or s["requires_authorized_schema_provenance"] is not True
            or s["migration_authorized"] is not False
            or s["generated_sql"] != []
            or type(s["production_writes"]) is not int
            or s["production_writes"]!=0):
        raise ObservationBlocked("Untrusted D1 report asserted provider/write authority")
    rows=s["objects"]
    if (not isinstance(rows,list) or len(rows)>_MAX_SCHEMA_OBJECTS
            or type(s["object_count"]) is not int
            or s["object_count"]!=len(rows)
            or any(type(s[k]) is not int or not 0<=s[k]<=200
                   for k in ("skipped_protected_objects","skipped_unsafe_objects"))):
        raise ObservationBlocked("D1 shape/count or redaction invalid")
    names=set()
    canonical_candidates=[]
    for obj in rows:
        if not isinstance(obj,dict) or set(obj)!=_D1_OBJECT:
            raise ObservationBlocked("D1 metadata object has unapproved fields")
        name=obj["name"]
        if (not _safe_identifier(name) or name.startswith(("sqlite_","_cf_"))
                or name in names or obj["kind"] not in ("table","view","virtual","shadow")):
            raise ObservationBlocked("D1 object invalid, sensitive or duplicated")
        names.add(name)
        columns=obj["columns"]
        if not isinstance(columns,list) or len(columns)>100:
            raise ObservationBlocked("D1 column metadata oversized")
        fields=set()
        for col in columns:
            if (not isinstance(col,dict) or set(col)!=_D1_COLUMNS
                    or not _safe_identifier(col["name"])
                    or col["name"] in fields
                    or type(col["primary_key"]) is not bool):
                raise ObservationBlocked("D1 column metadata invalid or protected")
            fields.add(col["name"])
        indexes=obj["indexes"]
        if not isinstance(indexes,list) or len(indexes)>40:
            raise ObservationBlocked("D1 index metadata oversized")
        for ix in indexes:
            if (not isinstance(ix,dict) or set(ix)!=_D1_INDEX
                    or type(ix["unique"]) is not bool
                    or not isinstance(ix["columns"],list)
                    or not 1<=len(ix["columns"])<=30
                    # Validate types and allowed schema names BEFORE set().
                    # Unhashable nested JSON must produce a fixed refusal,
                    # never an uncontrolled TypeError or an echoed payload.
                    or any(not _safe_identifier(f) or f not in fields for f in ix["columns"])
                    or len(set(ix["columns"]))!=len(ix["columns"])):
                raise ObservationBlocked("D1 index metadata invalid or unproven")
        if fields>=_RECOGNIZED_CANONICAL and obj["kind"]=="table":
            canonical_candidates.append(name)
    # Schema names disclose no row values; do not include even sanitized
    # inventory in result, only bounded counts and compatibility flags.
    return canonical_candidates,len(rows)


def _checked_youtube(s:dict)->tuple[int,int,bool]:
    _bounded_snapshot(s,_YT_TOP,"YouTube")
    if (s["origin"]!="UNAUTHENTICATED_YOUTUBE_SHAPED_METADATA"
            or s["channel_id"]!=CHANNEL_ID
            or s["saw_authenticated_provider_request"] is not False
            or s["contains_titles_or_descriptions"] is not False
            or s["migration_authorized"] is not False
            or s["publication_authorized"] is not False
            or type(s["network_calls"]) is not int or s["network_calls"]!=0
            or type(s["production_writes"]) is not int or s["production_writes"]!=0
            or type(s["pagination_complete"]) is not bool
            or type(s["has_conflicting_state"]) is not bool):
        raise ObservationBlocked("YouTube report has unexpected authority or channel")
    records=s["videos"]
    if (not isinstance(records,list) or len(records)>_MAX_VIDEO_RECORDS
            or type(s["video_count"]) is not int
            or len(records)!=s["video_count"]
            or not isinstance(s["blockers"],list)
            or len(s["blockers"])>10
            or any(not isinstance(k,str) or not re.fullmatch(r"[A-Z_]{3,90}",k)
                   for k in s["blockers"])):
        raise ObservationBlocked("YouTube metadata array or blockers invalid")
    needed={
        "AUTHENTICATED_YOUTUBE_OAUTH_OWNER_BINDING_NOT_ESTABLISHED",
        "INPUTS_ARE_UNTRUSTED_PROVIDER_SHAPED_CLAIMS",
    }
    if not needed.issubset(s["blockers"]):
        raise ObservationBlocked("YouTube report omitted mandatory untrusted-source warning")
    video_ids=set()
    uncertain=0
    for rec in records:
        if not isinstance(rec,dict) or set(rec)!=_YT_VIDEO:
            raise ObservationBlocked("Unredacted YouTube video metadata")
        vid=rec["youtube_id"]
        if (not isinstance(vid,str) or VIDEO_ID.fullmatch(vid) is None
                or vid in video_ids or rec["channel_id"]!=CHANNEL_ID
                or rec["privacy"] not in ("private","public","unlisted")
                or rec["processing"] not in (
                    "succeeded","processing","failed","terminated","unknown")
                or type(rec["uncertain_metadata"]) is not bool):
            raise ObservationBlocked("Invalid or duplicated channel-owned video metadata")
        video_ids.add(vid)
        t=rec["publish_at_utc"]
        if t is not None:
            if not isinstance(t,str) or not _CANON.fullmatch(t):
                raise ObservationBlocked("Noncanonical sanitized YouTube schedule timestamp")
            try:
                instant=datetime.fromisoformat(t)
            except (ValueError,TypeError) as exc:
                raise ObservationBlocked("Bad YouTube UTC scheduled timestamp") from exc
            if instant.utcoffset().total_seconds()!=0:
                raise ObservationBlocked("Schedule must be UTC")
        should_uncertain=(rec["processing"]=="unknown"
                          or (rec["privacy"]!="private" and t is not None))
        if rec["uncertain_metadata"] is not should_uncertain:
            raise ObservationBlocked("Video privacy/processing uncertainty was suppressed")
        if should_uncertain:
            uncertain+=1
    if s["has_conflicting_state"] is not bool(uncertain):
        raise ObservationBlocked("Overall unknown processing state hidden")
    incomplete=not s["pagination_complete"]
    if incomplete != ("VIDEO_PAGINATION_INCOMPLETE" in s["blockers"]):
        raise ObservationBlocked("Pagination completeness issue concealed")
    return len(records),uncertain,incomplete


def inspect_signed_sanitized_phase4e_snapshots(
    *,d1_snapshot:dict,youtube_snapshot:dict,
    signed_observations:Sequence[SignedObservation],
    trusted_registry:Mapping[str,CollectorTrust],
    request_nonce:str,already_seen_nonces:frozenset[str],
    now:datetime,
) -> dict:
    """Bind two *untrusted* sanitized snapshots to externally pinned keys.

    The explicitly supplied nonce must be durably stored elsewhere to prevent
    cross-process replay; this function neither stores nonces nor authenticates
    a Cloudflare or Google API request. No source-to-ledger reconciliation.
    """
    candidate_tables,table_count=_checked_d1(d1_snapshot)
    video_count,uncertain_count,incomplete=_checked_youtube(youtube_snapshot)
    hashes={
        "d1_schema":sanitized_snapshot_hash(d1_snapshot),
        "youtube_history":sanitized_snapshot_hash(youtube_snapshot),
    }
    review=verify_readonly_observation_bundle(
        receipts=signed_observations,
        trusted_registry=trusted_registry,
        expected_payload_sha256=hashes,
        expected_nonce=request_nonce,
        already_seen_nonces=already_seen_nonces,
        now=now,
    )
    if (review.signature_integrity_valid is not True
            or review.status!="SIGNED_INTEGRITY_ONLY_PROVIDER_ACCESS_UNVERIFIED"
            or review.provider_connection_observed is not False
            or review.authenticated_channel_readback is not False
            or review.production_migration_ready is not False
            or review.production_upload_ready is not False
            or review.production_schedule_ready is not False):
        raise ObservationBlocked("Signed receipt verifier promoted untrusted evidence")
    issues=[
        "NO_LIVE_PROVIDER_REQUEST_ATTESTED",
        "NO_DURABLE_TRUSTED_NONCE_STORE_OR_COLLECTOR_ENROLLMENT",
        "NO_D1_RELEASE_ROW_RECONCILIATION",
        "NO_APPROVED_D1_MIGRATION_OR_ROLLBACK",
        "NO_OWNER_AUTHORIZED_UPLOAD_OR_YOUTUBE_READBACK",
    ]
    if len(candidate_tables)!=1:
        issues.append("NO_SINGLE_UNAMBIGUOUS_CANONICAL_LEDGER_TABLE")
    if incomplete:
        issues.append("INCOMPLETE_YOUTUBE_VIDEO_PAGINATION")
    if uncertain_count:
        issues.append("UNKNOWN_OR_CONFLICTING_VIDEO_STATUS")
    return {
        "status":"OFFLINE_SIGNED_SANITIZED_READBACK_ONLY_PRODUCTION_BLOCKED",
        "channel_bound_to_expected_label":True,
        "d1_metadata_object_count":table_count,
        "candidate_canonical_table_count":len(candidate_tables),
        "youtube_video_count":video_count,
        "youtube_unknown_or_conflicting_count":uncertain_count,
        "youtube_pagination_complete":not incomplete,
        "signed_integrity_for_exact_sanitized_snapshot_bytes":True,
        "separate_pinned_collector_keys_used":True,
        "snapshot_sha256_by_kind":hashes,
        "blockers":sorted(issues),
        "live_authenticated_d1_access_verified":False,
        "live_authenticated_youtube_channel_owner_verified":False,
        "historical_video_ids_reconciled_to_release_rows":False,
        "private_media_or_oauth_secret_accessed":False,
        "schema_specific_migration_sql_generated":False,
        "production_ledger_writer_deployed":False,
        "migration_authorized":False,
        "private_upload_or_scheduling_authorized":False,
        "public_publishing_authorized":False,
        "generated_sql":[],
        "network_calls":0,
        "database_writes":0,
    }
