"""Phase 4B offline schema and release reconciliation preflight.

This module has no Cloudflare, YouTube, upload or network integration. Its only
SQLite connection is explicitly read-only; no table DATA is ever read. A schema
snapshot or claimed YouTube record cannot authorize real publishing.
"""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
from pathlib import Path
import re
import sqlite3
from typing import Mapping, Sequence

from .core import CHANNEL_ID

PROTECTED = re.compile(r"oauth|secret|token|credential|grant|cipher|encrypted|private_key|refresh|auth", re.I)
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}\Z")
SOURCES = frozenset({"private_sqlite_claim", "public_draft_claim", "d1_claim", "youtube_claim"})
STAGES = frozenset({
    "planned", "facts_verified", "research_verified", "script_verified",
    "qa_passed", "media_qa_passed", "upload_started", "upload_uncertain",
    "private_uploaded", "processing_succeeded", "remote_private_verified",
    "schedule_unresolved", "schedule_uncertain", "scheduled_verified",
    "public_verified", "quarantined",
})


class AuditBlocked(ValueError):
    """Unsafe or unauthenticated snapshot is not eligible for migration."""


def _quoted_identifier(identifier: str) -> str:
    """Quote an identifier from sqlite_schema, never use row values as SQL."""
    if not isinstance(identifier, str) or not identifier or len(identifier) > 255 or '\x00' in identifier:
        raise AuditBlocked("Unsafe schema identifier")
    return '"' + identifier.replace('"', '""') + '"'


def inspect_local_schema_only(path: str | Path, *, max_objects: int = 200) -> dict:
    """Open an EXISTING local SQLite fixture with mode=ro and inspect schema only.

    Do not pass credentials, Cloudflare URLs, SQLite journal files, real OAuth
    database dumps, or a path to a database on the user's machine. Intended for
    independently supplied synthetic CI fixtures and voluntarily supplied
    sanitized, non-secret *local* backups only.
    """
    p = Path(path).resolve(strict=True)
    if not p.is_file() or p.suffix.lower() not in {".db", ".sqlite", ".sqlite3"}:
        raise AuditBlocked("Existing SQLite fixture file required")
    if not isinstance(max_objects,int) or not 1 <= max_objects <= 500:
        raise AuditBlocked("Bounded schema object limit required")
    # Local URI mode=ro is an enforced filesystem guard, independent of query_only.
    conn = sqlite3.connect(p.as_uri() + "?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        names = conn.execute(
            "SELECT name,type FROM sqlite_schema WHERE type IN ('table','view') ORDER BY name"
        ).fetchall()
        if len(names) > max_objects:
            raise AuditBlocked("Too many schema objects to inspect safely")
        inspected = []
        protected_count = 0
        for name, kind in names:
            if name.startswith("sqlite_"):
                continue
            if PROTECTED.search(name):
                protected_count += 1
                inspected.append({"name": "protected_" + sha256(name.encode()).hexdigest()[:12],
                                  "kind": kind, "protected": True})
                continue
            columns = [row[1] for row in conn.execute("PRAGMA table_info(" + _quoted_identifier(name) + ")")]
            # Sensitive *column names* do not need to be included in this report.
            columns = [c if not PROTECTED.search(c) else "protected_column" for c in columns]
            indexes = []
            if kind == 'table':
                for item in conn.execute("PRAGMA index_list(" + _quoted_identifier(name) + ")"):
                    index_name, unique = item[1], bool(item[2])
                    indexed = [r[2] for r in conn.execute(
                        "PRAGMA index_info(" + _quoted_identifier(index_name) + ")")]
                    # Do not include index names or expressions, only safe column lists.
                    fields = [v if v and not PROTECTED.search(v) else "protected_column"
                              for v in indexed]
                    indexes.append({"unique": unique, "columns": fields})
            inspected.append({"name": name, "kind": kind, "protected": False,
                              "columns": columns, "indexes": indexes})
        return {"origin": "OFFLINE_SQLITE_SCHEMA_ONLY_NOT_D1",
                "verified_production_d1": False, "object_count": len(inspected),
                "protected_object_count": protected_count, "objects": inspected,
                "contains_data_rows": False, "migration_authorized": False}
    finally:
        conn.close()


def known_ledger_compatibility(snapshot: Mapping) -> dict:
    """Compare metadata shape to known local adapters, never to unseen D1 tables."""
    if snapshot.get("origin") != "OFFLINE_SQLITE_SCHEMA_ONLY_NOT_D1" or snapshot.get("verified_production_d1") is not False:
        raise AuditBlocked("Only trustworthy-form offline fixture inventory accepted")
    objects = snapshot.get("objects")
    if not isinstance(objects,list) or len(objects)>500:
        raise AuditBlocked("Malformed inventory")
    visible = {item["name"]: set(item["columns"])
               for item in objects if isinstance(item,dict) and
               item.get("protected") is False and isinstance(item.get("columns"),list)}
    p = visible.get("releases", set())
    versions = []
    if {"release_date","episode_id","stage","youtube_id"}.issubset(p):
        versions.append("private_sqlite_v1")
    if {"episode","kind","planned_utc","stage","channel"}.issubset(p):
        versions.append("public_draft_v1")
    if {"channel_id","episode_id","planned_utc","media_sha256","version"}.issubset(p):
        versions.append("possible_canonical_candidate")
    if "phase4_releases" in visible:
        versions.append("phase4a_offline_simulator_only")
    blockers = ["LIVE_D1_TABLES_NOT_AUTHENTICATED_OR_INSPECTED",
                "NO_AUTHENTICATED_YOUTUBE_RELEASE_RECONCILIATION",
                "NO_PRODUCTION_MIGRATION_APPROVAL"]
    if len(versions) != 1:
        blockers.append("UNKNOWN_OR_AMBIGUOUS_LOCAL_LEDGER_LAYOUT")
    return {"recognized_local_shapes": versions, "blockers": blockers,
            "production_migration_ready": False,
            "reconciliation_authority": "NONE"}


def _optional_string(row: Mapping, key: str) -> str | None:
    value = row.get(key)
    if value is None:
        return None
    if not isinstance(value,str) or not value.strip() or len(value)>180:
        raise AuditBlocked("Invalid optional metadata: " + key)
    return value


def _normalize_record(row: Mapping) -> dict:
    if not isinstance(row, Mapping) or row.get("source") not in SOURCES:
        raise AuditBlocked("Unknown claimed record source")
    channel = _optional_string(row, "channel_id")
    episode = _optional_string(row, "episode_id")
    stage = _optional_string(row, "stage")
    if channel != CHANNEL_ID or episode is None or stage not in STAGES:
        raise AuditBlocked("Wrong channel, missing episode or unknown stage")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}", episode):
        raise AuditBlocked("Unsafe episode ID")
    digest = _optional_string(row, "media_sha256")
    if digest is not None and HEX64.fullmatch(digest) is None:
        raise AuditBlocked("Invalid media SHA256")
    video = _optional_string(row, "youtube_id")
    if video is not None and VIDEO_ID.fullmatch(video) is None:
        raise AuditBlocked("Invalid YouTube ID")
    slot = _optional_string(row,"planned_utc")
    if slot is not None:
        from datetime import datetime, timedelta, timezone
        try:
            t=datetime.fromisoformat(slot.replace("Z","+00:00"))
        except ValueError as exc:
            raise AuditBlocked("Malformed schedule timestamp") from exc
        if t.tzinfo is None or t.utcoffset()!=timedelta(0) or t.microsecond:
            raise AuditBlocked("Schedule must have exact UTC second granularity")
        slot=t.astimezone(timezone.utc).isoformat(timespec="seconds")
    return {"source":row["source"],"channel_id":channel,"episode_id":episode,
            "stage":stage,"media_sha256":digest,"youtube_id":video,"planned_utc":slot}


def reconcile_claimed_releases(rows: Sequence[Mapping]) -> dict:
    """Deterministic conflict diagnostics, with no database or API access.

    ALL evidence is *claimed* input, even if source='youtube_claim'. Callers can
    forge these labels, so this function NEVER returns publish/migration approval.
    """
    if not isinstance(rows, (list,tuple)) or len(rows)>5000:
        raise AuditBlocked("Bounded list of claimed records required")
    normalized = [_normalize_record(r) for r in rows]
    by_episode = defaultdict(list)
    by_video = defaultdict(set)
    by_slot = defaultdict(set)
    for r in normalized:
        ep=r["episode_id"]
        by_episode[ep].append(r)
        if r["youtube_id"]:
            by_video[r["youtube_id"]].add(ep)
        if r["planned_utc"]:
            by_slot[r["planned_utc"]].add(ep)
    conflicts=[]
    for ep, claims in sorted(by_episode.items()):
        for field,problem in (("media_sha256","MEDIA_HASH_MISMATCH"),
                              ("youtube_id","REMOTE_VIDEO_ID_MISMATCH"),
                              ("planned_utc","SCHEDULE_SLOT_MISMATCH")):
            values={row[field] for row in claims if row[field] is not None}
            if len(values)>1:
                conflicts.append({"episode_id":ep,"problem":problem})
        if any(row["stage"] in {"remote_private_verified","scheduled_verified","public_verified"}
               and row["youtube_id"] is None for row in claims):
            conflicts.append({"episode_id":ep,"problem":"REMOTE_STATE_WITHOUT_VIDEO_ID"})
    for video, eps in sorted(by_video.items()):
        if len(eps)>1:
            conflicts.append({"problem":"REMOTE_ID_SHARED_BY_DIFFERENT_EPISODES",
                              "episodes":sorted(eps)})
    for slot, eps in sorted(by_slot.items()):
        if len(eps)>1:
            conflicts.append({"problem":"SLOT_SHARED_BY_DIFFERENT_EPISODES",
                              "episodes":sorted(eps)})
    all_sources=sorted({x["source"] for x in normalized})
    blockers=["UNTRUSTED_CALLER_SUPPLIED_OBSERVATIONS_NOT_PRODUCTION_EVIDENCE",
              "NO_AUTHENTICATED_D1_AND_YOUTUBE_SNAPSHOT_ATTESTATION",
              "PRODUCTION_MIGRATION_AND_PUBLISHING_DISABLED"]
    if not normalized:
        blockers.append("NO_RELEASE_OBSERVATIONS")
    if conflicts:
        blockers.append("RELEASE_METADATA_CONFLICTS")
    # Never surface credential contents, plaintext private filenames or raw rows.
    return {"sources":all_sources,"release_count":len(by_episode),
            "claimed_rows":len(normalized), "conflicts":conflicts,
            "blockers":blockers,"safe_to_migrate":False,"safe_to_publish":False,
            "writes_performed":0}
