"""Offline HMAC-verified entrypoint for staging task claims/completions.

The credentials are test-runtime secrets, never repository, file, or CI secrets.
This code is NOT a deployed authentication service or an unbypassable trust
boundary: the local coordinator can still be called directly by local code.
No upload, publication, provider connections, or paid actions are implemented.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
from typing import Callable, Mapping
import hmac
import json
import re

from .agent_org import Handoff, ROLES, WorkflowError
from .agent_staging_unified import UnifiedStagingCoordinator
from .agent_staging_key_policy import StagingKeyPolicy, KEY_ID_RE

WORKER_RE = re.compile(r"[a-z][a-z0-9_]{3,47}")
REQUEST_RE = re.compile(r"[a-z][a-z0-9_-]{7,63}")
MAX_REQUEST_TTL_SECONDS = 120


@dataclass(frozen=True)
class SignedStagingRequest:
    worker_id: str
    action: str
    episode_id: str
    task_id: str
    generation: int
    expires_epoch: int
    lease_seconds: int = 0
    handoff_sha: str = ""
    request_id: str = ""
    key_id: str = ""
    signature: str = ""

    def unsigned(self) -> dict:
        return {name: value for name, value in asdict(self).items()
                if name != "signature"}


def _canonical(request: SignedStagingRequest) -> bytes:
    return json.dumps(request.unsigned(), sort_keys=True,
                      separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sign_staging_request(request: SignedStagingRequest, *, key: bytes
                         ) -> SignedStagingRequest:
    """Sign a freshly constructed request in a no-secrets offline test."""
    if (not isinstance(request, SignedStagingRequest)
            or type(key) is not bytes or len(key) < 32
            or request.signature != ""):
        raise WorkflowError("Staging test request not fresh or key too weak")
    return replace(request, signature=hmac.new(
        key, _canonical(request), sha256
    ).hexdigest())


def handoff_digest(handoff: Handoff) -> str:
    if not isinstance(handoff, Handoff):
        raise WorkflowError("Signed completion requires a typed Handoff")
    return sha256(json.dumps(asdict(handoff), sort_keys=True,
                             separators=(",", ":"), ensure_ascii=True
                             ).encode("utf-8")).hexdigest()


class SignedStagingGateway:
    """Offline key registry: worker ID -> (allowed original role, HMAC secret).

    This resolves the role from a verified identity and holds the service
    clock rather than trusting the worker's asserted wall-clock timestamp.
    The clock is still not independently attested cloud database time.
    """
    def __init__(self, coordinator: UnifiedStagingCoordinator, *,
                 worker_keys: Mapping[str, tuple],
                 clock: Callable[[], datetime] | None = None,
                 key_policy: StagingKeyPolicy | None = None):
        if not isinstance(coordinator, UnifiedStagingCoordinator):
            raise WorkflowError("Signed gateway needs the unified coordinator")
        if not isinstance(worker_keys, Mapping) or not 1 <= len(worker_keys) <= 64:
            raise WorkflowError("Bounded worker registry missing")
        if key_policy is not None and (
            not isinstance(key_policy, StagingKeyPolicy)
            or key_policy.db_path != coordinator.path
        ):
            raise WorkflowError("Persistent policy must bind the SAME coordinator DB")
        checked = {}
        seen_secrets = set()
        for name, registration in worker_keys.items():
            if (not isinstance(name, str)
                    or WORKER_RE.fullmatch(name) is None
                    or not isinstance(registration, tuple)
                    or len(registration) != (3 if key_policy is not None else 2)):
                raise WorkflowError("Malformed worker enrollment")
            if key_policy is None:
                role, secret = registration
                key_id = ""
            else:
                role, key_id, secret = registration
                if not isinstance(key_id,str) or KEY_ID_RE.fullmatch(key_id) is None:
                    raise WorkflowError("Persistent worker key ID invalid")
            if (not isinstance(role, str) or role not in ROLES
                    or type(secret) is not bytes or len(secret) < 32
                    or secret in seen_secrets):
                raise WorkflowError("Unknown role, reused, or weak HMAC key")
            checked[name] = (role, key_id, secret)
            seen_secrets.add(secret)
        if clock is not None and not callable(clock):
            raise WorkflowError("Service clock must be callable")
        self._workers = checked
        self._key_policy = key_policy
        self.coordinator = coordinator
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def _authenticate(self, request: SignedStagingRequest,
                      action: str) -> tuple[str, datetime]:
        if (not isinstance(request, SignedStagingRequest)
                or not isinstance(request.worker_id, str)
                or WORKER_RE.fullmatch(request.worker_id) is None):
            raise WorkflowError("Invalid signed worker identity")
        registration = self._workers.get(request.worker_id)
        if (registration is None or request.action != action
                or action not in ("claim", "complete")
                or not isinstance(request.episode_id, str)
                or not isinstance(request.task_id, str)
                or type(request.generation) is not int
                or request.generation < 0
                or type(request.expires_epoch) is not int
                or type(request.lease_seconds) is not int
                or not isinstance(request.handoff_sha, str)
                or not isinstance(request.request_id, str)
                or not isinstance(request.key_id, str)
                or not isinstance(request.signature, str)
                or re.fullmatch(r"[0-9a-f]{64}", request.signature) is None):
            raise WorkflowError("Malformed authenticated staging scope")
        actor, key_id, key = registration
        if request.key_id != key_id:
            raise WorkflowError("Worker key ID does not match signed enrollment")
        expected = hmac.new(key, _canonical(request), sha256).hexdigest()
        if not hmac.compare_digest(expected, request.signature):
            raise WorkflowError("Worker HMAC authentication failed")
        now = self._clock()
        if (not isinstance(now, datetime) or now.tzinfo is None
                or now.utcoffset() is None):
            raise WorkflowError("Gateway clock must be timezone aware")
        stamp = now.timestamp()
        if (stamp != int(stamp) or request.expires_epoch <= int(stamp)
                or request.expires_epoch - int(stamp) > MAX_REQUEST_TTL_SECONDS):
            raise WorkflowError("Signed staging request expired or TTL too long")
        contract = self.coordinator.contracts.get(
            request.episode_id, {}
        ).get(request.task_id)
        if contract is None or contract.owner != actor:
            raise WorkflowError("Verified worker cannot perform this task")
        if action == "claim":
            if (request.handoff_sha or request.request_id
                    or not 10 <= request.lease_seconds <= 900):
                raise WorkflowError("Claim signature includes forbidden fields")
        elif (request.generation < 1 or request.lease_seconds != 0
              or re.fullmatch(r"[0-9a-f]{64}", request.handoff_sha) is None
              or REQUEST_RE.fullmatch(request.request_id) is None):
            raise WorkflowError("Completion scope invalid")
        return actor, now

    def _enforce_policy(self, request: SignedStagingRequest):
        if self._key_policy is None:
            return None
        role, key_id, _secret = self._workers[request.worker_id]
        return lambda db: self._key_policy.require_active(
            db, request.worker_id, role, key_id
        )

    def claim(self, request: SignedStagingRequest) -> int:
        role, now = self._authenticate(request, "claim")
        return self.coordinator.claim(
            request.episode_id, request.task_id, actor=role, now=now,
            lease_seconds=request.lease_seconds,
            expected_generation=request.generation,
            _authz_check=self._enforce_policy(request),
        )

    def complete(self, request: SignedStagingRequest, handoff: Handoff) -> dict:
        role, now = self._authenticate(request, "complete")
        if (not isinstance(handoff, Handoff)
                or handoff.task_id != request.task_id
                or handoff_digest(handoff) != request.handoff_sha):
            raise WorkflowError("Signed completion Handoff mismatch")
        return self.coordinator.complete(
            request.episode_id, handoff, actor=role,
            generation=request.generation, now=now,
            request_id=request.request_id,
            _authz_check=self._enforce_policy(request),
        )

    def status(self) -> dict:
        return {
            "offline_signed_claim_and_completion": True,
            "registered_workers": len(self._workers),
            "role_derived_from_verified_worker": True,
            "worker_secrets_stored_in_sqlite": False,
            "persistent_key_revocation_enforced": self._key_policy is not None,
            "real_remote_worker_identity_authenticated": False,
            "direct_coordinator_access_blocked": False,
            "remotely_trusted_database_clock": False,
            "real_execution_cancellation": False,
            "youtube_publishing_authorized": False,
            "monthly_infrastructure_inr": 0,
        }
