"""Offline-only Phase 4E release identity and collision-risk audit.

Consumes previously sanitized *claimed* D1 schema metadata. Never queries a
provider, reads ledger rows, approves migrations or publishes media. Index
metadata is caller supplied: even an apparent complete set proves nothing
about the real database or partial constraints.
"""
from __future__ import annotations
from collections.abc import Mapping
from .phase4d_signed_observations import ObservationBlocked

CANONICAL_FIELDS=frozenset(("channel_id","episode_id","planned_utc","media_sha256","version"))
LEGACY_FIELDS=frozenset(("release_date","episode_id","stage","youtube_id"))
REQUIRED_UNIQUE_INDEXES=(
    frozenset(("channel_id","episode_id")),
    frozenset(("channel_id","planned_utc")),
    frozenset(("channel_id","media_sha256")),
    frozenset(("youtube_id",)),
    frozenset(("intent_id",)),
)

def inspect_release_identity_risks(snapshot: Mapping) -> dict:
    """Classify D1-shaped source claims without trusting or exposing any rows."""
    if (not isinstance(snapshot,dict)
            or snapshot.get("origin")!="UNAUTHENTICATED_D1_SHAPED_METADATA"
            or snapshot.get("saw_authenticated_provider_request") is not False
            or snapshot.get("migration_authorized") is not False
            or snapshot.get("contains_data_rows") is not False
            or snapshot.get("production_writes")!=0
            or snapshot.get("generated_sql")!=[]
            or not isinstance(snapshot.get("objects"),list)
            or len(snapshot["objects"])>200):
        raise ObservationBlocked("Untrusted schema shape cannot establish authority")
    legacy=canonical=complete=0
    reported_missing_by_key=[0]*len(REQUIRED_UNIQUE_INDEXES)
    for item in snapshot["objects"]:
        if (not isinstance(item,dict)
                or item.get("kind") not in ("table","view","virtual","shadow")
                or not isinstance(item.get("columns"),list)
                or not isinstance(item.get("indexes"),list)
                or len(item["columns"])>100 or len(item["indexes"])>40):
            raise ObservationBlocked("Untrusted schema object invalid")
        fields=set()
        for c in item["columns"]:
            if (not isinstance(c,dict) or not isinstance(c.get("name"),str)
                    or c["name"] in fields):
                raise ObservationBlocked("Duplicate or malformed column")
            fields.add(c["name"])
        if item["kind"]!="table":
            continue
        if LEGACY_FIELDS<=fields and "channel_id" not in fields:
            legacy+=1
        if CANONICAL_FIELDS<=fields:
            canonical+=1
            unique_sets=set()
            for ix in item["indexes"]:
                if not isinstance(ix,dict) or type(ix.get("unique")) is not bool:
                    raise ObservationBlocked("Malformed claimed index")
                names=ix.get("columns")
                if not isinstance(names,list) or not names:
                    raise ObservationBlocked("Missing claimed index columns")
                if len(names)!=len(set(names)) or any(
                    not isinstance(n,str) or n not in fields for n in names
                ):
                    raise ObservationBlocked("Impossible claimed index")
                if ix["unique"]:
                    # A claimed unique index is not proof of global uniqueness.
                    # Caller omitted index predicates and actual D1 row history.
                    unique_sets.add(frozenset(names))
            present=[req in unique_sets for req in REQUIRED_UNIQUE_INDEXES]
            complete+=int(all(present))
            for i,found in enumerate(present):
                reported_missing_by_key[i]+=int(not found)
    issues=["PROVIDER_AUTHENTICITY_AND_ROW_HISTORY_UNVERIFIED",
            "REAL_UNIQUENESS_AND_INDEX_PREDICATES_UNVERIFIED",
            "APPROVED_BACKUP_ROLLBACK_AND_MIGRATION_MISSING"]
    if legacy:
        issues.append("LEGACY_RELEASE_DATE_KEY_REQUIRES_EXPLICIT_UTC_RECONCILIATION")
    if canonical!=1:
        issues.append("NO_SINGLE_CANONICAL_RELEASE_TABLE")
    elif complete!=1:
        issues.append("MISSING_DECLARED_RELEASE_COLLISION_CONSTRAINTS")
    return {
        "status":"OFFLINE_SCHEMA_COLLISION_REVIEW_ONLY",
        "legacy_date_key_table_count":legacy,
        "canonical_shape_candidate_count":canonical,
        "candidate_with_five_declared_unique_indexes_count":complete,
        "missing_declared_unique_index_groups":tuple(reported_missing_by_key),
        "blockers":tuple(sorted(issues)),
        "live_schema_authenticated":False,
        "real_global_uniqueness_verified":False,
        "historical_video_identity_reconciled":False,
        "date_to_utc_slot_mapping_verified":False,
        "private_video_upload_approved":False,
        "migration_or_writes_authorized":False,
        "generated_sql":[],
        "network_calls":0,
        "database_writes":0,
    }
