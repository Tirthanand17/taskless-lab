"""Phase 5J: offline, fail-closed multi-Worker production safety inventory.

This is not a Cloudflare API client, OAuth client, or provider readback.
Observations must come from a separately authenticated, owner-approved
read-only audit. No secret values, Worker URLs, tokens, IDs, or route paths
are accepted or returned. All evidence is considered caller-asserted and
NEVER authorizes D1 writes or YouTube publication.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

ROLES = frozenset(("upload_oauth_vault", "brand_readonly_probe",
                   "zero_cost_controller"))
WORKER_FIELDS = frozenset(("deployed", "public_route", "d1_binding",
                          "triggers_reviewed", "secrets_not_exported",
                          "d1_mutation_routes_reviewed",
                          "d1_writes_denied_under_zero_budget"))
ROOT_FIELDS = frozenset(("observed_at_utc", "account_list_fully_enumerated",
                         "unrelated_workers_reviewed", "workers"))
MAX_AGE=timedelta(hours=24)


class UnsafeInventory(ValueError):
    """Use static error codes only. Never echo user-provided data."""


def _exact(value:Any, fields:frozenset[str], code:str)->dict:
    if type(value) is not dict or set(value)!=fields:
        raise UnsafeInventory(code)
    return value


def _utc(value:Any)->datetime:
    if type(value) is not str or len(value)>40 or not value.endswith("Z"):
        raise UnsafeInventory("INVALID_UTC")
    try:
        instant=datetime.fromisoformat(value.replace("Z","+00:00"))
        if instant.utcoffset()!=timedelta(0):
            raise ValueError
        return instant
    except (ValueError,OverflowError):
        raise UnsafeInventory("INVALID_UTC") from None


def inspect_workers(evidence:dict,*,now:datetime)->dict:
    """Only report the completeness of an OWNER-supplied bounded snapshot.

    A synthetically perfect input is still unauthenticated, cannot prove
    code behavior, and is never production admission approval.
    """
    _exact(evidence,ROOT_FIELDS,"INVALID_WORKER_INVENTORY")
    if type(evidence["workers"]) is not dict or set(evidence["workers"])!=ROLES:
        raise UnsafeInventory("MISSING_OR_EXTRA_FLOWMINUTE_WORKER")
    if type(evidence["account_list_fully_enumerated"]) is not bool or \
       type(evidence["unrelated_workers_reviewed"]) is not bool:
        raise UnsafeInventory("INVALID_ACCOUNT_ENUMERATION_EVIDENCE")
    if not isinstance(now,datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise UnsafeInventory("AWARE_TIME_REQUIRED")
    now=now.astimezone(timezone.utc)
    stamp=_utc(evidence["observed_at_utc"])
    risks=[]
    if stamp>now or now-stamp>MAX_AGE:
        risks.append("MULTI_WORKER_ACCOUNT_SNAPSHOT_NOT_FRESH")
    if not evidence["account_list_fully_enumerated"]:
        risks.append("CLOUDFLARE_ACCOUNT_WORKER_LIST_INCOMPLETE")
    if not evidence["unrelated_workers_reviewed"]:
        risks.append("OTHER_CLOUDFLARE_WORKER_INTERACTION_UNREVIEWED")
    labels=[]
    for role in sorted(ROLES):
        w=_exact(evidence["workers"][role],WORKER_FIELDS,"INVALID_WORKER_METADATA")
        if any(type(w[k]) is not bool for k in WORKER_FIELDS):
            raise UnsafeInventory("INVALID_WORKER_BOOLEAN")
        if not w["deployed"]:
            risks.append("EXPECTED_FLOWMINUTE_WORKER_NOT_VERIFIED_DEPLOYED")
        if not w["triggers_reviewed"]:
            risks.append("WORKER_TRIGGERS_ROUTES_CRON_UNVERIFIED")
        if not w["d1_mutation_routes_reviewed"]:
            risks.append("WORKER_D1_MUTATION_SURFACE_UNVERIFIED")
        if w["d1_binding"] and w["public_route"] and \
           not w["d1_writes_denied_under_zero_budget"]:
            risks.append("PUBLIC_D1_BOUND_WORKER_MAY_WRITE")
        if not w["secrets_not_exported"]:
            risks.append("CREDENTIAL_HANDLING_UNVERIFIED")
        labels.append({
            "role":role, "deployed":w["deployed"],
            "public_route":w["public_route"],
            "d1_bound":w["d1_binding"],
            "trigger_evidence_complete":w["triggers_reviewed"],
            "write_guard_evidence_complete":w["d1_mutation_routes_reviewed"] and
                  w["d1_writes_denied_under_zero_budget"],
        })
    return {
        "state":"HOLD_MULTI_WORKER_PRODUCTION_ADMISSION",
        "input_trust":"CALLER_ASSERTED_NOT_PROVIDER_AUTHENTICATED",
        "expected_worker_roles_reviewed":len(labels),
        "worker_evidence":labels,
        "risk_codes":sorted(set(risks)),
        "risk_count":len(set(risks)),
        "account_enumeration_claimed_complete":evidence["account_list_fully_enumerated"],
        "real_cloudflare_api_called":False,
        "secrets_exported":False,
        "global_zero_spend_proven":False,
        "real_d1_writes":0,
        "real_youtube_writes":0,
        "production_migration_authorized":False,
        "cloud_publisher_authorized":False,
        "cloud_autopilot_ready":False,
    }
