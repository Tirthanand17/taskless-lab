"""Offline-only Phase 4E release identity and collision-risk audit.

Consumes previously sanitized *claimed* D1 schema metadata. Never queries a
provider, reads ledger rows, approves migrations or publishes media. Index
metadata is caller supplied: even an apparent complete set proves nothing
about the real database or partial constraints.
"""
from __future__ import annotations
from collections.abc import Mapping

# Share the strict 4E.2 *untrusted* snapshot parser, rather than maintaining
# a second weaker validator. 4E.2 checks exact envelope/nested fields,
# ownership label, safe identifiers, bounded JSON, uniqueness-column shapes,
# all objects (including noncandidate views), and FALSE authority flags.
# It still does NOT prove any actual D1 request or global uniqueness.
from .phase4e2_signed_snapshot_bridge import _checked_d1

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
    """Classify *untrusted* schema claims; no release rows or SQL executed.

    All index entries, including ones on noncanonical objects, are validated
    before any set construction. A complete declaration is diagnostic ONLY.
    """
    _checked_d1(snapshot)
    legacy=canonical=complete=0
    reported_missing_by_key=[0]*len(REQUIRED_UNIQUE_INDEXES)
    for item in snapshot["objects"]:
        # Names and nested index column types were already checked by 4E.2.
        fields={column["name"] for column in item["columns"]}
        if item["kind"]!="table":
            continue
        if LEGACY_FIELDS<=fields and "channel_id" not in fields:
            legacy+=1
        if CANONICAL_FIELDS<=fields:
            canonical+=1
            # These are CLAIMED unique-column groups, never proven constraints.
            # 4E.2 rejects partial/SQL-expression or extra index fields:
            # predicate completeness of the actual DB remains unverified.
            unique_sets={
                frozenset(ix["columns"])
                for ix in item["indexes"] if ix["unique"]
            }
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
