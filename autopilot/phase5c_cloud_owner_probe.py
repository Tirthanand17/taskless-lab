"""Phase 5C: bounded, read-only cloud credential handoff and owner audit.

Staging integration contract, NOT a deployed provider connection. The token is
borrowed only inside a provider-owned context manager. No token is serialized,
persisted, printed, refreshed or uploaded. Dynamic provider errors are redacted.
This component cannot promote its observations to production upload approval.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from autopilot.cloud_oauth_lifecycle_gate import (
    CHANNEL_ID, READONLY_SCOPE, OAuthScreenError, screen_claims,
)
from autopilot.owner_youtube_readonly_monitor import (
    OwnerYouTubeReader, ReleaseAuditError, SLOTS, _entry_format,
    _expected, audit_day,
)


class CloudProbeError(ValueError):
    """Static error messages only; do not include token/provider exceptions."""


def _validate_manifest(day: str, planned: Mapping[str, Any]) -> None:
    if not isinstance(planned, Mapping) or set(planned) != set(SLOTS):
        raise CloudProbeError("EXACT_THREE_RELEASE_SLOTS_REQUIRED")
    ids = []
    for slot in SLOTS:
        try:
            _expected(day, slot)
        except ReleaseAuditError:
            raise CloudProbeError("INVALID_RELEASE_DAY") from None
        if not _entry_format(planned[slot]):
            raise CloudProbeError("UNSAFE_RELEASE_MANIFEST")
        video_id = planned[slot]["video_id"]
        if video_id is not None:
            ids.append(video_id)
    if len(ids) != len(set(ids)):
        raise CloudProbeError("DUPLICATE_VIDEO_ID")


def _fail(reason: str, *, claim_reasons: tuple[str, ...] = ()) -> dict:
    """Always omit OAuth tokens, titles, private YouTube IDs and raw errors."""
    return {
        "state": "HOLD_UNVERIFIED",
        "reason": reason,
        "claim_reasons": list(claim_reasons),
        "owner_api_observation": False,
        "source_trust": "UNATTESTED_STAGING_ADAPTER",
        "provider_collector_enrolled": False,
        "live_cloud_deployment_verified": False,
        "production_upload_authorized": False,
        "production_schedule_authorized": False,
        "production_autopilot_ready": False,
        "mutating_youtube_requests": 0,
    }


def inspect_owner_readonly(
    *,
    day: str,
    planned: Mapping[str, Any],
    sanitized_claims: Mapping[str, Any],
    provider: Any,
    now: datetime,
) -> dict:
    """Exercise the credential-leasing boundary, never mutate YouTube.

    provider.borrow_readonly(channel_id=..., scope=...) must return a context
    manager yielding a short-lived access token. Production integrations must
    supply an independently approved encrypted cloud secret custodian; tests
    supply only a fake. Caller-provided claims and providers are NOT signed or
    trusted merely because this integration accepts them.
    """
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise CloudProbeError("AWARE_TIME_REQUIRED")
    try:
        _validate_manifest(day, planned)
    except CloudProbeError as exc:
        return _fail(str(exc))
    try:
        preliminary = screen_claims(sanitized_claims, purpose="read_only", now=now)
    except (OAuthScreenError, TypeError, ValueError):
        return _fail("INVALID_SANITIZED_CLAIMS")
    if not preliminary["claim_screen_pass"]:
        return _fail("OAUTH_OR_CLOUD_CLAIM_SCREEN_BLOCKED",
                     claim_reasons=tuple(preliminary["reasons"]))
    # The contract is privileged and deliberately not auto-discovered from
    # global environment / a public CI runner.
    borrow = getattr(provider, "borrow_readonly", None)
    if not callable(borrow):
        return _fail("PROVIDER_CREDENTIAL_LEASE_UNAVAILABLE")
    try:
        with borrow(channel_id=CHANNEL_ID, scope=READONLY_SCOPE) as access_token:
            if not isinstance(access_token, str):
                return _fail("INVALID_EPHEMERAL_ACCESS_TOKEN")
            reader = OwnerYouTubeReader(access_token)
            observation = audit_day(day=day, planned=planned, reader=reader, now=now)
    except Exception:
        # Never include the message/traceback: a provider can include secrets.
        return _fail("PROVIDER_OR_OWNER_READ_FAILED")

    # Only sanitized, bounded slots are emitted. Even a successful read can be
    # forged by a substituted provider/reader; no attested collector here.
    slots = [
        {
            "slot": lane["slot"],
            "publish_at_utc": lane["publish_at_utc"],
            "state": lane["status"],
            "reason": lane["reason"],
        }
        for lane in observation["lanes"]
    ]
    observed = bool(observation["account_verified"])
    return {
        "state": "OWNER_READ_OBSERVED_UNATTESTED" if observed else "HOLD_UNVERIFIED",
        "reason": "LIVE_PROVIDER_ATTESTATION_REQUIRED" if observed
                  else "OWNER_CHANNEL_NOT_VERIFIED",
        "channel_id": CHANNEL_ID,
        "date": day,
        "owner_api_observation": observed,
        "platform_state_count": observation["verified_platform_state_count"],
        "slots": slots,
        "source_trust": "UNATTESTED_STAGING_ADAPTER",
        "provider_collector_enrolled": False,
        "live_cloud_deployment_verified": False,
        "production_upload_authorized": False,
        "production_schedule_authorized": False,
        "production_autopilot_ready": False,
        "mutating_youtube_requests": 0,
    }
