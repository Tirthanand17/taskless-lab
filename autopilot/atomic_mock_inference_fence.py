"""B3d4c2b1: transaction-fenced, one-use, MOCK-ONLY script inference ledger.

This verifies the B3d4c2a owner-signed *synthetic* lease at each reservation,
then burns one request slot with SQLite BEGIN IMMEDIATE + FULL synchronous
durability on one filesystem. Ambiguous/crashed reservations NEVER get reused.
No provider client, HTTP, private key, secret vault, paid service, YouTube or
publish authority exists in this module.

SQLite on GitHub-hosted runner is EPHEMERAL AND NOT A MULTI-JOB CLOUD LEDGER.
An authenticated, access-controlled private persistent DB with independent
actual owner enrollment, provider project/billing verification and a scoped
provider credential is REQUIRED before real inference can be implemented.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import secrets
import sqlite3
import stat
from typing import Mapping

from autopilot.owner_provider_lease_gate import (
    HEX64, ModelLeaseError, SignedProviderLease, TrustedProviderOwner,
    verify_owner_provider_lease, digest,
)
from autopilot.script_draft_agent import (
    build_draft_input, validate_proposal, ScriptDraftError,
)

SCHEMA_VERSION = 1
RESERVED = "BURNED_UNCERTAIN_NO_RETRY"
ACCEPTED = "MOCK_DRAFT_VALIDATED_NO_RELEASE"
REJECTED = "MOCK_DRAFT_REJECTED_NO_RETRY"
STATES = (RESERVED, ACCEPTED, REJECTED)
MOCK_STATUS = "ATOMIC_TEST_LEDGER_MOCK_VALIDATION_ONLY_NO_MODEL_CALL"
MAX_PER_DAY = 3


class InferenceFenceError(ValueError):
    """Never issue a second lease or infer a safe retry."""


@dataclass(frozen=True)
class Reservation:
    """Single-use local proof needed to close a mock reservation.

    fence_token is a local test secret: do not log it, persist it as plaintext,
    or interpret it as an API/provider credential.
    """
    lease_id: str
    episode_id: str
    fence_token: str


def _utc(clock: datetime | None) -> datetime:
    value = clock if clock is not None else datetime.now(timezone.utc)
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise InferenceFenceError("Timezone-aware durable inference ledger clock required")
    return value.astimezone(timezone.utc)


class EphemeralOneUseLedger:
    """Test reference design; never move DB onto user's laptop or public repo.

    SQLite BEGIN IMMEDIATE serializes same-filesystem competing writers.
    State BURNED_UNCERTAIN_NO_RETRY is COMMITTED before mock validation.
    A crash between reservation and closing leaves the slot burned permanently.
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        if (
            not self.path.is_absolute()
            or self.path.suffix != ".sqlite3"
            or not self.path.parent.is_dir()
            or self.path.parent.is_symlink()
            or self.path.is_symlink()
            or (self.path.exists() and not self.path.is_file())
        ):
            raise InferenceFenceError("Require a private existing cloud test directory and SQLite path")
        if not self.path.exists():
            flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            try:
                descriptor = os.open(self.path, flags, 0o600)
            except FileExistsError:
                pass
            except OSError as exc:
                raise InferenceFenceError("Could not create private ledger") from exc
            else:
                os.close(descriptor)
        try:
            attrs = self.path.stat()
        except OSError as exc:
            raise InferenceFenceError("Ledger file unavailable") from exc
        if (
            not stat.S_ISREG(attrs.st_mode)
            or self.path.is_symlink()
            or stat.S_IMODE(attrs.st_mode) & 0o077
        ):
            raise InferenceFenceError("Ledger file must be private 0600 regular file")
        self._prepare()

    def _connect(self):
        # No URI or shared in-memory SQLite database: only a file for which
        # multiple GitHub-hosted TEST processes can observe the same burns.
        conn = sqlite3.connect(str(self.path), timeout=6.0, isolation_level=None)
        try:
            conn.execute("PRAGMA busy_timeout=6000")
            conn.execute("PRAGMA synchronous=FULL")
            conn.execute("PRAGMA journal_mode=DELETE")
            conn.execute("PRAGMA foreign_keys=ON")
            return conn
        except Exception:
            conn.close()
            raise

    @contextmanager
    def _write(self):
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
                conn.execute("COMMIT")
            except BaseException:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise
        except sqlite3.Error as exc:
            raise InferenceFenceError("Atomic ledger unavailable: fail closed") from exc
        finally:
            conn.close()

    def _prepare(self):
        with self._write() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, SCHEMA_VERSION):
                raise InferenceFenceError("Unknown inference ledger schema: no writes")
            if version == 0:
                db.execute("""
                    CREATE TABLE inference_burns (
                        lease_id TEXT PRIMARY KEY NOT NULL,
                        episode_id TEXT NOT NULL UNIQUE,
                        release_day_ist TEXT NOT NULL,
                        owner_id TEXT NOT NULL,
                        project_fingerprint_sha256 TEXT NOT NULL,
                        provider_id TEXT NOT NULL,
                        model_id TEXT NOT NULL,
                        context_sha256 TEXT NOT NULL,
                        owner_anchor_sha256 TEXT NOT NULL,
                        consent_sha256 TEXT NOT NULL,
                        fenced_token_sha256 TEXT NOT NULL,
                        state TEXT NOT NULL CHECK (
                            state IN (
                                'BURNED_UNCERTAIN_NO_RETRY',
                                'MOCK_DRAFT_VALIDATED_NO_RELEASE',
                                'MOCK_DRAFT_REJECTED_NO_RETRY'
                            )
                        ),
                        burned_at_utc TEXT NOT NULL,
                        closed_at_utc TEXT,
                        mock_response_sha256 TEXT
                    )
                """)
                db.execute(
                    "CREATE INDEX burns_day_index ON inference_burns(release_day_ist)"
                )
                db.execute("PRAGMA user_version=1")
            else:
                # Deny suspicious/corrupted schema without trusting caller data.
                col = {r[1] for r in db.execute("PRAGMA table_info(inference_burns)")}
                required = {
                    "lease_id", "episode_id", "release_day_ist",
                    "owner_id", "project_fingerprint_sha256",
                    "provider_id", "model_id", "context_sha256",
                    "owner_anchor_sha256", "consent_sha256",
                    "fenced_token_sha256", "state", "burned_at_utc",
                    "closed_at_utc", "mock_response_sha256",
                }
                if col != required:
                    raise InferenceFenceError("Inference ledger schema incompatible")

    def reserve_synthetic_owner_lease(
        self, *, slot: dict, observations: dict,
        signed_lease: SignedProviderLease,
        external_lease_anchor_sha256: str,
        owner_registry: Mapping[str, TrustedProviderOwner],
        excluded_automated_agent_ids: frozenset[str],
        now: datetime | None = None,
    ) -> Reservation:
        """Burn an episode+owner lease atomically; do not contact any provider.

        The owner registry, external anchor, and all project attestations in
        these tests are invented. A real program must NOT use this result as
        proof of account tier/consent or authorization to transmit prompts.
        """
        at = _utc(now)
        report = verify_owner_provider_lease(
            slot=slot, observations=observations, signed_lease=signed_lease,
            external_lease_anchor_sha256=external_lease_anchor_sha256,
            owner_registry=owner_registry,
            excluded_automated_agent_ids=excluded_automated_agent_ids,
            now=at,
        )
        t = signed_lease.terms
        if (
            report["provider_live_call_enabled"] is not False
            or report["actual_provider_project_and_zero_spend_verified"] is not False
            or report["private_key_vault_connected"] is not False
            or report["release_authorized"] is not False
            or report["external_lease_anchor_sha256"] != external_lease_anchor_sha256
        ):
            raise InferenceFenceError("Untrusted consent status cannot unlock a provider")
        day = t.episode_id[3:11]
        token = secrets.token_hex(32)
        with self._write() as db:
            # Same-day quota and scope are checked with a write lock.
            previous = db.execute(
                """SELECT owner_id,project_fingerprint_sha256,provider_id
                   FROM inference_burns WHERE release_day_ist=?""",
                (day,),
            ).fetchall()
            if len(previous) >= MAX_PER_DAY or any(
                row != (
                    t.owner_id, t.free_tier_billing_project_fingerprint_sha256,
                    t.provider_id,
                )
                for row in previous
            ):
                raise InferenceFenceError("Daily request count or signed project scope conflict")
            try:
                db.execute("""
                    INSERT INTO inference_burns (
                        lease_id,episode_id,release_day_ist,owner_id,
                        project_fingerprint_sha256,provider_id,model_id,
                        context_sha256,owner_anchor_sha256,consent_sha256,
                        fenced_token_sha256,state,burned_at_utc
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    t.lease_id, t.episode_id, day, t.owner_id,
                    t.free_tier_billing_project_fingerprint_sha256,
                    t.provider_id, t.model_id, t.draft_context_sha256,
                    external_lease_anchor_sha256,
                    t.owner_provider_data_use_consent_record_sha256,
                    sha256(token.encode("ascii")).hexdigest(), RESERVED,
                    at.isoformat(),
                ))
            except sqlite3.IntegrityError as exc:
                raise InferenceFenceError(
                    "Owner inference lease or release episode already burned: NEVER retry"
                ) from exc
        return Reservation(t.lease_id, t.episode_id, token)

    def close_mock(
        self, reservation: Reservation, *, mock_result_sha256: str,
        valid_structured_draft: bool, now: datetime | None = None,
    ) -> dict:
        """One-time closure of an already burned mock; no external inference."""
        at = _utc(now)
        if (
            not isinstance(reservation, Reservation)
            or not isinstance(reservation.fence_token, str)
            or len(reservation.fence_token) != 64
            or any(c not in "0123456789abcdef" for c in reservation.fence_token)
            or not isinstance(mock_result_sha256, str)
            or not HEX64.fullmatch(mock_result_sha256)
            or type(valid_structured_draft) is not bool
        ):
            raise InferenceFenceError("Malformed mock-only closure request")
        new_state = ACCEPTED if valid_structured_draft else REJECTED
        token_hash = sha256(reservation.fence_token.encode("ascii")).hexdigest()
        with self._write() as db:
            row = db.execute("""
                SELECT state, fenced_token_sha256, burned_at_utc
                FROM inference_burns WHERE lease_id=? AND episode_id=?
            """, (reservation.lease_id, reservation.episode_id)).fetchone()
            if (
                row is None or row[0] != RESERVED
                or not secrets.compare_digest(row[1], token_hash)
                or datetime.fromisoformat(row[2]) > at
            ):
                raise InferenceFenceError("Missing, closed, changed or stale mock reservation")
            changed = db.execute("""
                UPDATE inference_burns
                SET state=?, closed_at_utc=?, mock_response_sha256=?
                WHERE lease_id=? AND episode_id=? AND state=?
            """, (
                new_state, at.isoformat(), mock_result_sha256,
                reservation.lease_id, reservation.episode_id, RESERVED,
            )).rowcount
            if changed != 1:
                raise InferenceFenceError("Atomic mock closure lost reservation race")
        return {
            "status": new_state,
            "lease_id": reservation.lease_id,
            "episode_id": reservation.episode_id,
            "mock_response_sha256": mock_result_sha256,
            "provider_inference_executed": False,
            "private_production_ledger_deployed": False,
            "owner_account_entitlement_verified": False,
            "real_provider_data_terms_verified": False,
            "youtube_upload_enabled": False,
            "release_authorized": False,
        }

    def inspect(self, lease_id: str) -> dict:
        """Read-only metadata snapshot; never expose tokens/source/API keys."""
        if not isinstance(lease_id, str) or not lease_id or len(lease_id) > 64:
            raise InferenceFenceError("Invalid lease lookup")
        conn = self._connect()
        try:
            row = conn.execute("""
                SELECT lease_id,episode_id,owner_anchor_sha256,context_sha256,
                       state,burned_at_utc,closed_at_utc,mock_response_sha256
                FROM inference_burns WHERE lease_id=?
            """, (lease_id,)).fetchone()
        finally:
            conn.close()
        if row is None:
            raise InferenceFenceError("Unknown burned owner lease")
        keys = (
            "lease_id","episode_id","owner_anchor_sha256","context_sha256",
            "state","burned_at_utc","closed_at_utc","mock_response_sha256",
        )
        return {
            **dict(zip(keys,row)),
            "safely_retryable": False,
            "mock_only": True,
            "provider_inference_executed": False,
            "real_owner_auth_verified": False,
            "real_project_billing_guaranteed": False,
            "provider_live_call_enabled": False,
            "youtube_upload_enabled": False,
            "release_authorized": False,
        }


def evaluate_one_synthetic_mock_script(
    ledger: EphemeralOneUseLedger, *,
    slot: dict, observations: dict, signed_lease: SignedProviderLease,
    external_lease_anchor_sha256: str,
    owner_registry: Mapping[str, TrustedProviderOwner],
    excluded_automated_agent_ids: frozenset[str],
    raw_synthetic_proposal: object,
    now: datetime | None = None,
) -> dict:
    """Simulate an inference return with NO API key, transport or network.

    A structural mock result NEVER counts as a factual, quality or rights pass.
    An invalid mock still burns its lease; the caller never automatically retries.
    """
    reservation = ledger.reserve_synthetic_owner_lease(
        slot=slot,observations=observations,signed_lease=signed_lease,
        external_lease_anchor_sha256=external_lease_anchor_sha256,
        owner_registry=owner_registry,
        excluded_automated_agent_ids=excluded_automated_agent_ids,now=now,
    )
    try:
        draft_input = build_draft_input(slot, observations)
        result = validate_proposal(raw_synthetic_proposal, draft_input)
        sha = digest(result)
    except (ScriptDraftError, TypeError, ValueError) as exc:
        # A failed mock response MUST NOT reopen the already burned lease.
        ledger.close_mock(
            reservation, mock_result_sha256=sha256(
                b"INVALID_STRUCTURED_MOCK_RESPONSE_NO_RETRY"
            ).hexdigest(), valid_structured_draft=False, now=now,
        )
        raise InferenceFenceError("Mock validation failed after lease burned") from exc
    receipt = ledger.close_mock(
        reservation, mock_result_sha256=sha, valid_structured_draft=True, now=now,
    )
    return {
        "status": MOCK_STATUS,
        "receipt": receipt,
        "synthetic_structurally_validated_script_sha256": sha,
        "actual_generative_model_output_created": False,
        "full_original_content_reviewed": False,
        "factual_claims_verified": False,
        "asset_and_voice_rights_approved": False,
        "durable_private_cloud_ledger_connected": False,
        "real_provider_inference_enabled": False,
        "youtube_upload_enabled": False,
        "youtube_schedule_enabled": False,
        "release_authorized": False,
    }
