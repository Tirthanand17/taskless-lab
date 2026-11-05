"""Major Phase 5: assert compatibility with ACTUAL deployed D1 table names.

Offline/static only. This module never imports credentials, network clients,
Cloudflare SDKs, remote desktop APIs, or deploys a Worker. It exists to stop
staged shadow-table SQL being mistaken for a production-ready D1 writer.
Even a perfect schema match does not grant write or publishing permission.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
import re

EXPECTED_CANONICAL=frozenset(("releases","release_events"))
OBSERVED_OTHER=frozenset(("youtube_release_observations","audit_heartbeats","fm_upload_auth_attempts","fm_oauth_channel_proofs"))
LEGACY_CAS=frozenset(("fm_release_writer_lease","fm_writer_release_shadow",
                      "fm_release_lease_shadow","fm_releases_shadow"))
SENSITIVE_SOURCE=re.compile(r"(?i)(refresh.token|client.secret|bearer\s+[a-z0-9_-]{12,})")


class UnsafeSchema(ValueError):
    """Never expose caller-provided SQL, credentials or IDs in errors."""


def _names(value:Any)->frozenset[str]:
    if type(value) is not list or not 2<=len(value)<=100 or any(
        type(x) is not str or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}",x)
        for x in value
    ):
        raise UnsafeSchema("INVALID_TABLE_INVENTORY")
    if len(set(value))!=len(value):
        raise UnsafeSchema("DUPLICATE_TABLE_INVENTORY")
    return frozenset(value)


def inspect(schema_names:list[str], *, repo_root:Path)->dict:
    """Check candidate Cloudflare SQL references against schema names.

    A risk-free synthetic result still remains untrusted and cannot enable
    production migration, D1 writes or Google publishing.
    """
    if not isinstance(repo_root,Path):
        raise UnsafeSchema("INVALID_REPO_ROOT")
    live=_names(schema_names)
    source=repo_root/"autopilot"/"cloud_d1_worker_candidate.mjs"
    try:
        if source.is_symlink() or not source.is_file() or source.stat().st_size>20000:
            raise OSError()
        code=source.read_text(encoding="utf-8")
    except (OSError,UnicodeError):
        raise UnsafeSchema("CAS_CANDIDATE_MISSING") from None
    if SENSITIVE_SOURCE.search(code):
        raise UnsafeSchema("UNEXPECTED_SENSITIVE_SOURCE_DATA")
    mentions=sorted(x for x in LEGACY_CAS|EXPECTED_CANONICAL
                    if re.search(r"\b"+re.escape(x)+r"\b",code))
    missing=sorted(x for x in mentions if x not in live)
    risks=[]
    if not EXPECTED_CANONICAL.issubset(live):
        risks.append("CANONICAL_D1_SCHEMA_MISSING")
    if missing:
        risks.append("STAGED_SQL_REFERENCES_MISSING_LIVE_TABLES")
    if "LIVE_CLOUDFLARE_WRITES_ENABLED = false" not in code:
        risks.append("CLOUD_WRITER_KILL_SWITCH_NOT_LOCKED_OFF")
    if "SYNTHETIC_D1_CAS_NOT_PRODUCTION_AUTHORITY" not in code:
        risks.append("CANDIDATE_SYNTHETIC_SCOPE_NOT_DECLARED")
    return {
        "state":"HOLD_MAJOR_PHASE5_SCHEMA_AND_WRITE_ADMISSION",
        "canonical_table_presence_confirmed_in_input":EXPECTED_CANONICAL.issubset(live),
        "staged_sql_missing_live_tables":missing,
        "staged_sql_missing_count":len(missing),
        "staged_sql_mentions":mentions,
        "blocking_risk_codes":risks,
        "observed_live_table_metadata_authenticated_here":False,
        "source_revision_is_provider_attestation":False,
        "writer_deployment_allowed":False,
        "production_schema_migration_authorized":False,
        "production_database_backfill_authorized":False,
        "production_worker_deployed":False,
        "youtube_uploads_authorized":False,
        "youtube_schedule_writes_authorized":False,
        "production_d1_writes":0,
        "cloud_autopilot_ready":False
    }
