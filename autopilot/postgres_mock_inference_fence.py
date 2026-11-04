"""B3d4c2b2: PostgreSQL multi-connection, one-use *mock* inference fence.

A real PostgreSQL service is used in isolated GitHub Actions integration tests.
This module ONLY works against the deliberately named CI test database/user;
it contains NO provider client, API keys, live HTTP, production deployment,
YouTube upload, external owner enrollment, or actual billing safeguards.

Durability spans database connections and worker process restarts while that
Postgres service is alive. A GitHub Actions Postgres service is EPHEMERAL;
neither its data nor its tests demonstrate a deployed private persistent DB.

Never replay or reset a burn on timeout/ambiguous provider outcome.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import hmac
import re
import secrets
from typing import Callable, Mapping

from autopilot.owner_provider_lease_gate import (
    SignedProviderLease, TrustedProviderOwner, verify_owner_provider_lease,
)
from autopilot.atomic_mock_inference_fence import (
    ACCEPTED, REJECTED, RESERVED, InferenceFenceError,
)
from autopilot.script_draft_agent import ScriptDraftError, build_draft_input, validate_proposal
from autopilot.owner_provider_lease_gate import digest

CI_DB = "flowminute_fence_ci"
CI_DB_USER = "flowminute_test"
STATUS = "POSTGRES_TWO_WORKER_SYNTHETIC_INFERENCE_LEDGER_NO_LIVE_PROVIDER"
MAX_PER_DAY = 3
HEX = re.compile(r"[a-f0-9]{64}\Z")
ID = re.compile(r"[a-z][a-z0-9_]{2,63}\Z")


@dataclass(frozen=True)
class PgReservation:
    episode_id: str
    lease_id: str
    # Ephemeral mock fencing secret only, never return through status or logs.
    token: str


def _utc(now: datetime | None) -> datetime:
    result = now if now is not None else datetime.now(timezone.utc)
    if not isinstance(result, datetime) or result.tzinfo is None or result.utcoffset() is None:
        raise InferenceFenceError("Postgres fence requires an aware clock")
    return result.astimezone(timezone.utc)


class PostgresMockInferenceFence:
    """The connection factory represents independent clients in ONE test DB.

    A production service would need separate deployment, database roles,
    TLS/IAM, owner-approved external trust store, secret vault, actual project
    account entitlement, monitoring and a strict billing-safe permission flow.
    No such environment is configurable from this class.
    """

    def __init__(self, connect: Callable):
        if not callable(connect):
            raise InferenceFenceError("Test-only PostgreSQL connector required")
        self._connect = connect
        try:
            with self._connect() as db:
                with db.cursor() as cursor:
                    cursor.execute("SELECT current_database(), current_user")
                    identity = cursor.fetchone()
                    if tuple(identity) != (CI_DB, CI_DB_USER):
                        raise InferenceFenceError(
                            "Only isolated mock-only PostgreSQL CI database/user permitted"
                        )
                    cursor.execute(
                        "SELECT to_regclass('public.fm_owner_inference_days'), "
                        "to_regclass('public.fm_owner_inference_burns')"
                    )
                    if not all(cursor.fetchone()):
                        raise InferenceFenceError("Test ledger schema migration not installed")
        except InferenceFenceError:
            raise
        except Exception as exc:
            raise InferenceFenceError("Isolated PostgreSQL test service unavailable") from exc

    def reserve_synthetic_owner_lease(
        self, *, slot: dict, observations: dict,
        signed_lease: SignedProviderLease,
        external_lease_anchor_sha256: str,
        owner_registry: Mapping[str, TrustedProviderOwner],
        excluded_automated_agent_ids: frozenset[str],
        now: datetime | None = None,
    ) -> PgReservation:
        """Reverify complete signed intent, then commit atomic, forever-burned row."""
        at = _utc(now)
        report = verify_owner_provider_lease(
            slot=slot, observations=observations,
            signed_lease=signed_lease,
            external_lease_anchor_sha256=external_lease_anchor_sha256,
            owner_registry=owner_registry,
            excluded_automated_agent_ids=excluded_automated_agent_ids,
            now=at,
        )
        if (
            report["provider_live_call_enabled"] is not False
            or report["actual_provider_project_and_zero_spend_verified"] is not False
            or report["private_immutable_request_ledger_connected"] is not False
            or report["release_authorized"] is not False
        ):
            raise InferenceFenceError("Provider entitlement must not be self-asserted")
        terms = signed_lease.terms
        day = terms.episode_id[3:11]
        token = secrets.token_hex(32)
        if not HEX.fullmatch(token):
            raise InferenceFenceError("Invalid single-use local fence token")
        try:
            with self._connect() as db:
                with db.transaction():
                    with db.cursor() as cur:
                        cur.execute("SET LOCAL lock_timeout = '8000ms'")
                        # Two newly started workers can both attempt to insert
                        # the day; ON CONFLICT waits until creator commits.
                        cur.execute(
                            """INSERT INTO fm_owner_inference_days
                                (day_ist, owner_id, project_sha256, provider_id,
                                 burned_count)
                                VALUES (%s,%s,%s,%s,0)
                                ON CONFLICT (day_ist) DO NOTHING""",
                            (
                                day, terms.owner_id,
                                terms.free_tier_billing_project_fingerprint_sha256,
                                terms.provider_id,
                            ),
                        )
                        cur.execute(
                            """SELECT owner_id, project_sha256, provider_id,
                                      burned_count
                               FROM fm_owner_inference_days
                               WHERE day_ist=%s FOR UPDATE""",
                            (day,),
                        )
                        row = cur.fetchone()
                        if not row or (
                            row[0], row[1], row[2]
                        ) != (
                            terms.owner_id,
                            terms.free_tier_billing_project_fingerprint_sha256,
                            terms.provider_id,
                        ) or row[3] >= MAX_PER_DAY:
                            raise InferenceFenceError(
                                "Cross-worker owner/project mismatch or daily mock cap reached"
                            )
                        # Unique lease and episode constraints are shared by
                        # all independent workers connecting to THIS database.
                        cur.execute(
                            """INSERT INTO fm_owner_inference_burns (
                                lease_id, episode_id, day_ist, owner_id,
                                project_sha256, model_id,
                                context_sha256, anchor_sha256,
                                token_sha256, state, burned_at_utc
                               ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                            (
                                terms.lease_id, terms.episode_id, day,
                                terms.owner_id,
                                terms.free_tier_billing_project_fingerprint_sha256,
                                terms.model_id, terms.draft_context_sha256,
                                external_lease_anchor_sha256,
                                sha256(token.encode("ascii")).hexdigest(),
                                RESERVED, at,
                            ),
                        )
                        cur.execute(
                            """UPDATE fm_owner_inference_days
                               SET burned_count=burned_count+1
                               WHERE day_ist=%s AND burned_count < 3""",
                            (day,),
                        )
                        if cur.rowcount != 1:
                            raise InferenceFenceError("Atomic daily mock quota update failed")
        except InferenceFenceError:
            raise
        except Exception as exc:
            # A database failure or ambiguous commit is NOT a reason to
            # launch a mock or provider retry. Reservation may have committed.
            raise InferenceFenceError(
                "Postgres reservation unavailable or duplicate: NO automatic retry"
            ) from exc
        return PgReservation(terms.episode_id, terms.lease_id, token)

    def close_mock(self, reservation: PgReservation, *,
                   mock_response_sha256: str, structurally_valid: bool,
                   now: datetime | None = None) -> dict:
        """Close a single mock response after burn; never authorize an upload."""
        at = _utc(now)
        if (
            not isinstance(reservation, PgReservation)
            or not isinstance(reservation.lease_id, str)
            or not ID.fullmatch(reservation.lease_id)
            or not isinstance(reservation.episode_id, str)
            or not isinstance(reservation.token, str)
            or not HEX.fullmatch(reservation.token)
            or not isinstance(mock_response_sha256, str)
            or not HEX.fullmatch(mock_response_sha256)
            or type(structurally_valid) is not bool
        ):
            raise InferenceFenceError("Invalid fenced mock completion")
        digest_token = sha256(reservation.token.encode("ascii")).hexdigest()
        state = ACCEPTED if structurally_valid else REJECTED
        try:
            with self._connect() as db:
                with db.transaction():
                    with db.cursor() as cur:
                        cur.execute(
                            """SELECT token_sha256, state, burned_at_utc
                               FROM fm_owner_inference_burns
                               WHERE lease_id=%s AND episode_id=%s
                               FOR UPDATE""",
                            (reservation.lease_id, reservation.episode_id),
                        )
                        row = cur.fetchone()
                        if (
                            row is None or row[1] != RESERVED
                            or not hmac.compare_digest(row[0], digest_token)
                            or row[2] > at
                        ):
                            raise InferenceFenceError(
                                "Already closed or forged cross-worker mock completion"
                            )
                        cur.execute(
                            """UPDATE fm_owner_inference_burns
                               SET state=%s, closed_at_utc=%s,
                                   mock_response_sha256=%s
                               WHERE lease_id=%s AND episode_id=%s
                                     AND state=%s""",
                            (
                                state, at, mock_response_sha256,
                                reservation.lease_id, reservation.episode_id, RESERVED,
                            ),
                        )
                        if cur.rowcount != 1:
                            raise InferenceFenceError("Fenced mock close race lost")
        except InferenceFenceError:
            raise
        except Exception as exc:
            raise InferenceFenceError(
                "Ambiguous mock closure: do not retry an inference request"
            ) from exc
        return {
            "status": state,
            "episode_id": reservation.episode_id,
            "lease_id": reservation.lease_id,
            "mock_response_sha256": mock_response_sha256,
            "mock_transcript_structurally_validated": structurally_valid,
            "live_provider_call_made": False,
            "owner_identity_verified_in_private_system": False,
            "account_spend_protected": False,
            "production_cloud_database_deployed": False,
            "youtube_upload_enabled": False,
            "release_authorized": False,
        }

    def inspect(self, lease_id: str) -> dict:
        if not isinstance(lease_id, str) or not ID.fullmatch(lease_id):
            raise InferenceFenceError("Invalid mock ledger lookup")
        try:
            with self._connect() as db:
                with db.cursor() as cur:
                    cur.execute(
                        """SELECT episode_id, state, burned_at_utc, closed_at_utc,
                                  mock_response_sha256
                           FROM fm_owner_inference_burns WHERE lease_id=%s""",
                        (lease_id,),
                    )
                    row = cur.fetchone()
        except Exception as exc:
            raise InferenceFenceError("Test DB inaccessible: no retry") from exc
        if row is None:
            raise InferenceFenceError("No such signed owner lease burn")
        return {
            "status": row[1],
            "episode_id": row[0],
            "burned_at_utc": row[2].isoformat(),
            "closed_at_utc": row[3].isoformat() if row[3] else None,
            "mock_response_sha256": row[4],
            "safe_to_retry": False,
            "provider_inference_performed": False,
            "production_ledger_deployed": False,
            "live_provider_enabled": False,
            "owner_real_consent_verified": False,
            "youtube_upload_enabled": False,
            "release_authorized": False,
        }


def evaluate_synthetic_pg_mock(
    fence: PostgresMockInferenceFence, *,
    slot: dict, observations: dict, signed_lease: SignedProviderLease,
    external_lease_anchor_sha256: str,
    owner_registry: Mapping[str,TrustedProviderOwner],
    excluded_automated_agent_ids: frozenset[str],
    raw_proposal: object, now: datetime | None = None,
) -> dict:
    """Local fake response structure test, after committing irreversible burn."""
    reservation = fence.reserve_synthetic_owner_lease(
        slot=slot, observations=observations, signed_lease=signed_lease,
        external_lease_anchor_sha256=external_lease_anchor_sha256,
        owner_registry=owner_registry,
        excluded_automated_agent_ids=excluded_automated_agent_ids,
        now=now,
    )
    try:
        proposal = validate_proposal(raw_proposal, build_draft_input(slot, observations))
        script_sha = digest(proposal)
    except (ScriptDraftError, TypeError, ValueError) as exc:
        fence.close_mock(
            reservation,
            mock_response_sha256=sha256(b"REJECTED_MOCK_DRAFT_NO_RETRY").hexdigest(),
            structurally_valid=False, now=now,
        )
        raise InferenceFenceError("Mock draft failed structural validation: burned") from exc
    closed=fence.close_mock(
        reservation, mock_response_sha256=script_sha,
        structurally_valid=True, now=now,
    )
    return {
        "status": STATUS,
        "receipt": closed,
        "synthetic_draft_sha256": script_sha,
        "live_provider_request_sent": False,
        "private_spend_cap_enforced": False,
        "owner_or_human_review_complete": False,
        "external_claim_fact_checked": False,
        "private_persistent_cloud_ledger_deployed": False,
        "youtube_upload_enabled": False,
        "youtube_schedule_enabled": False,
        "release_authorized": False,
    }
