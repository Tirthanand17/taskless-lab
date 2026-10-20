"""Allowlisted JSON commands over signed, offline FlowMinute staging.

Only signed worker.claim, worker.complete and admin.apply are accepted.
Never provides upload, release, SQL, arbitrary file or generic Python dispatch.
The protocol is NOT a remote security boundary: trusted local callers can
still open the SQLite DB or invoke the original coordinator directly.
"""
from __future__ import annotations

from dataclasses import asdict, fields
from datetime import datetime, timezone
from typing import Mapping
import json

from .agent_org import Handoff, WorkflowError
from .agent_staging_unified import UnifiedStagingCoordinator
from .agent_staging_auth_gateway import (
    SignedStagingGateway, SignedStagingRequest,
)
from .agent_staging_admin_gateway import (
    SignedStagingAdminGateway, SignedStagingAdminCommand,
)
from .agent_staging_key_policy import StagingKeyPolicy

MAX_COMMAND_BYTES = 8192


def _unique_pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise WorkflowError("Duplicate JSON field in staging command")
        out[key] = value
    return out


def _reject_constant(value):
    raise WorkflowError("Non-finite JSON staging field")


def _typed_record(typ, value, *, evidence=False):
    if not isinstance(value, dict):
        raise WorkflowError("Expected typed signed JSON object")
    if set(value) != {f.name for f in fields(typ)}:
        raise WorkflowError("Missing or extraneous signed JSON fields")
    if evidence:
        refs=value.get("evidence_refs")
        if (not isinstance(refs,list) or len(refs)>12
                or not all(isinstance(v,str) for v in refs)):
            raise WorkflowError("Evidence references must be bounded strings")
        value={**value,"evidence_refs":tuple(refs)}
    try:
        return typ(**value)
    except (TypeError, ValueError) as exc:
        raise WorkflowError("Invalid typed signed JSON request") from exc


class SQLiteHostClock:
    """One local SQLite host time source; NOT cloud-trusted database time."""

    def __init__(self, core: UnifiedStagingCoordinator):
        if not isinstance(core,UnifiedStagingCoordinator):
            raise WorkflowError("Clock requires original staging coordinator")
        self._core=core

    def now(self)->datetime:
        with self._core._tx() as db:
            second=db.execute(
                "SELECT CAST(strftime('%s','now') AS INTEGER)"
            ).fetchone()[0]
        if type(second) is not int or second<=0:
            raise WorkflowError("Local SQLite host time unavailable")
        return datetime.fromtimestamp(second,timezone.utc)


class StagingLocalCommandBoundary:
    """Signed command parser and policy wiring, still in one Python process."""

    def __init__(self, core:UnifiedStagingCoordinator, *,
                 worker_keys:Mapping[str,tuple[str,str,bytes]],
                 admin_id:str, admin_secret:bytes):
        if not isinstance(core,UnifiedStagingCoordinator):
            raise WorkflowError("Command boundary requires unified coordinator")
        clock=SQLiteHostClock(core)
        policy=StagingKeyPolicy(core)
        self._workers=SignedStagingGateway(
            core,worker_keys=worker_keys,key_policy=policy,
            clock=clock.now,use_local_sqlite_time=True,
        )
        self._admin=SignedStagingAdminGateway(
            policy,admin_id=admin_id,secret=admin_secret,
            clock=clock.now,use_local_sqlite_time=True,
        )

    def execute(self, raw:str)->dict:
        if (type(raw) is not str or not 0<len(raw.encode("utf-8"))
                <=MAX_COMMAND_BYTES):
            raise WorkflowError("Missing or oversized JSON staging command")
        try:
            obj=json.loads(
                raw,object_pairs_hook=_unique_pairs,
                parse_constant=_reject_constant,
            )
        except (ValueError,TypeError,UnicodeError) as exc:
            raise WorkflowError("Invalid JSON command") from exc
        if not isinstance(obj,dict) or set(obj)!={"action","signed","handoff"}:
            raise WorkflowError("Signed command envelope keys mismatch")
        route=obj["action"]
        if type(route) is not str:
            raise WorkflowError("Staging command action must be a string")
        if route=="worker.claim":
            if obj["handoff"] is not None:
                raise WorkflowError("Signed claim cannot contain output")
            request=_typed_record(SignedStagingRequest,obj["signed"])
            return {"generation":self._workers.claim(request),
                    "publish_enabled":False}
        if route=="worker.complete":
            request=_typed_record(SignedStagingRequest,obj["signed"])
            handoff=_typed_record(Handoff,obj["handoff"],evidence=True)
            return {"outcome":self._workers.complete(request,handoff),
                    "publish_enabled":False}
        if route=="admin.apply":
            if obj["handoff"] is not None:
                raise WorkflowError("Signed admin cannot contain output")
            request=_typed_record(SignedStagingAdminCommand,obj["signed"])
            return {"admin_outcome":self._admin.apply(request),
                    "publish_enabled":False}
        raise WorkflowError("Unapproved staging operation")

    def safety(self)->dict:
        return {
            "allowed_actions":("worker.claim","worker.complete","admin.apply"),
            "signed_workers":True,
            "signed_admin":True,
            "mutation_time_from_local_sqlite":True,
            "isolated_service":False,
            "direct_database_access_protected":False,
            "remotely_trusted_database_clock":False,
            "youtube_publishing_authorized":False,
            "monthly_recurring_infrastructure_inr":0,
        }
