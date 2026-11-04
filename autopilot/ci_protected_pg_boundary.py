"""B3d4c2b3a: TEST-ONLY least-privileged PostgreSQL client role boundary.

The actual SQL permissions in the isolated GitHub Actions database prevent
worker/auditor logins from writing, erasing or spoofing ledger tables. Even the
mock gateway has NO direct table privileges: only fixed SECURITY DEFINER
stored procedures with a trusted search_path.

The Python gateway authenticates B3d4c2a *synthetic* external owner signatures
BEFORE invoking the PostgreSQL stored burn procedure. A compromised gateway
could still supply fabricated arguments: real workload identity, owner trust,
billable provider entitlement, vault access and independent immutable storage
are UNIMPLEMENTED. No provider HTTP or YouTube client is imported.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import re
import secrets
from typing import Callable, Mapping

from autopilot.owner_provider_lease_gate import (
    SignedProviderLease, TrustedProviderOwner, verify_owner_provider_lease,
)
from autopilot.atomic_mock_inference_fence import InferenceFenceError, RESERVED
from autopilot.postgres_mock_inference_fence import CI_DB

GATEWAY_ROLE = "fm_ci_gateway"
WORKER_ROLE = "fm_ci_worker"
AUDITOR_ROLE = "fm_ci_auditor"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
LEASE_ID = re.compile(r"[a-z][a-z0-9_]{2,63}\Z")
STATUS = "LEAST_PRIVILEGED_POSTGRES_CI_MOCK_ONLY_NO_DEPLOYMENT"


@dataclass(frozen=True)
class MockCiTicket:
    lease_id: str
    episode_id: str
    # Never expose in repr, audit rows, status response or job log.
    ephemeral_fence_token: str = field(repr=False)


def _now(value: datetime | None) -> datetime:
    result = value if value is not None else datetime.now(timezone.utc)
    if not isinstance(result, datetime) or result.tzinfo is None or result.utcoffset() is None:
        raise InferenceFenceError("Test-only gateway requires aware clock")
    return result.astimezone(timezone.utc)


def _strict_role(connect: Callable, expected: str) -> None:
    if not callable(connect):
        raise InferenceFenceError("Isolated PostgreSQL CI connection factory required")
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT current_database(), session_user,
                              (SELECT rolsuper OR rolcreatedb OR rolcreaterole OR rolbypassrls
                                 FROM pg_catalog.pg_roles
                                WHERE rolname=session_user),
                              pg_catalog.has_table_privilege(
                                session_user, 'fm_private_ci.burns', 'INSERT'),
                              pg_catalog.has_table_privilege(
                                session_user, 'fm_private_ci.burns', 'DELETE')
                    """
                )
                row = cur.fetchone()
        if tuple(row) != (CI_DB, expected, False, False, False):
            raise InferenceFenceError(
                "Only matching non-privileged isolated CI role may use this adapter"
            )
    except InferenceFenceError:
        raise
    except Exception as exc:
        raise InferenceFenceError("CI private-schema roles not available") from exc


class ProtectedMockGateway:
    """The sole CI role allowed to call fixed ledger burn/close procedures."""

    def __init__(self, connect: Callable):
        _strict_role(connect, GATEWAY_ROLE)
        self._connect = connect

    def reserve_synthetic_signed_intent(
        self, *, slot: dict, observations: dict,
        signed_lease: SignedProviderLease,
        external_lease_anchor_sha256: str,
        owner_registry: Mapping[str, TrustedProviderOwner],
        excluded_automated_agent_ids: frozenset[str],
        now: datetime | None = None,
    ) -> MockCiTicket:
        at = _now(now)
        receipt = verify_owner_provider_lease(
            slot=slot, observations=observations, signed_lease=signed_lease,
            external_lease_anchor_sha256=external_lease_anchor_sha256,
            owner_registry=owner_registry,
            excluded_automated_agent_ids=excluded_automated_agent_ids,
            now=at,
        )
        if (
            receipt["provider_live_call_enabled"] is not False
            or receipt["actual_provider_project_and_zero_spend_verified"] is not False
            or receipt["owner_identity_real_world_authenticated_by_software"] is not False
            or receipt["release_authorized"] is not False
        ):
            raise InferenceFenceError("Signed mock owner intent cannot activate a provider")
        t=signed_lease.terms
        token=secrets.token_hex(32)
        token_sha=sha256(token.encode("ascii")).hexdigest()
        try:
            with self._connect() as conn:
                with conn.transaction():
                    with conn.cursor() as cur:
                        cur.execute(
                            """SELECT fm_private_ci.burn_mock_once(
                                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                            )""",
                            (
                                t.lease_id, t.episode_id, t.owner_id,
                                t.free_tier_billing_project_fingerprint_sha256,
                                t.provider_id,t.model_id,t.draft_context_sha256,
                                external_lease_anchor_sha256, token_sha, at,
                            ),
                        )
                        state=cur.fetchone()[0]
                        if state!=RESERVED:
                            raise InferenceFenceError("Unsigned or ambiguous mock reservation state")
        except InferenceFenceError:
            raise
        except Exception as exc:
            raise InferenceFenceError(
                "CI mock reservation failed or duplicate; never retry an inference"
            ) from exc
        return MockCiTicket(t.lease_id,t.episode_id,token)

    def close_mock(
        self, ticket: MockCiTicket, *,
        mock_output_sha256: str, structurally_valid: bool,
        now: datetime | None = None,
    ) -> dict:
        at=_now(now)
        if (
            not isinstance(ticket,MockCiTicket)
            or not isinstance(ticket.lease_id,str)
            or not LEASE_ID.fullmatch(ticket.lease_id)
            or not isinstance(ticket.ephemeral_fence_token,str)
            or not HEX64.fullmatch(ticket.ephemeral_fence_token)
            or not isinstance(mock_output_sha256,str)
            or not HEX64.fullmatch(mock_output_sha256)
            or type(structurally_valid) is not bool
        ):
            raise InferenceFenceError("Invalid test-only fenced close")
        token_sha=sha256(ticket.ephemeral_fence_token.encode("ascii")).hexdigest()
        try:
            with self._connect() as conn:
                with conn.transaction():
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT fm_private_ci.close_mock_once(%s,%s,%s,%s,%s,%s)",
                            (
                                ticket.lease_id,ticket.episode_id,token_sha,
                                mock_output_sha256,structurally_valid,at,
                            ),
                        )
                        state=cur.fetchone()[0]
        except Exception as exc:
            raise InferenceFenceError("One-shot mock completion rejected; no retry") from exc
        return {
            "status":state,
            "episode_id":ticket.episode_id,
            "lease_id":ticket.lease_id,
            "mock_output_sha256":mock_output_sha256,
            "cross_process_mock_fencing_tested":True,
            "human_owner_enrollment_or_billing_verified":False,
            "private_vault_connected":False,
            "production_cloud_database_deployed":False,
            "provider_call_enabled":False,
            "youtube_upload_enabled":False,
            "release_authorized":False,
        }


class LimitedMockLedgerObserver:
    """Worker/auditor can only call a sanitized status procedure, never edit DB."""

    def __init__(self, connect: Callable, *, role: str):
        if role not in (WORKER_ROLE,AUDITOR_ROLE):
            raise InferenceFenceError("Unknown nonprivileged CI observer role")
        _strict_role(connect,role)
        self._connect=connect
        self.role=role

    def inspect(self, lease_id: str) -> dict:
        if not isinstance(lease_id,str) or not LEASE_ID.fullmatch(lease_id):
            raise InferenceFenceError("Invalid limited mock ledger query")
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT state,audit_count,episode_id "
                        "FROM fm_private_ci.read_mock_state(%s)",(lease_id,)
                    )
                    result=cur.fetchone()
        except Exception as exc:
            raise InferenceFenceError("Restricted status observation failed") from exc
        if result is None:
            raise InferenceFenceError("Unknown lease in restricted mock audit")
        state,count,episode=result
        return {
            "status":state,
            "audit_event_count":count,
            "episode_id":episode,
            "observer_role":self.role,
            "contains_fence_secret":False,
            "append_only_against_runtime_roles":True,
            "admin_or_backup_tampering_excluded":False,
            "production_secret_vault_verified":False,
            "provider_inference_performed":False,
            "youtube_upload_enabled":False,
            "release_authorized":False,
        }
