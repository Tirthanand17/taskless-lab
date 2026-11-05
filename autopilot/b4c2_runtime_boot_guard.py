"""B4c2 CloudFormation Fargate image entry point: deliberately inert.

This is an owner-operator manual read-only runtime boot guard, NOT a worker.
It does not open a network socket, read cloud credentials, run a media render,
call AWS/Google, change a secret, or publish. Its return value always denies
real OAuth identity, owner release, uploads and schedules.

A task definition registering an ECR image containing this module does not
launch an ECS task. Public CI is never allowed to deploy the template.
"""
from __future__ import annotations

import json
import os
from typing import Mapping

STATUS = "INERT_OWNER_PREFLIGHT_BOOT_ONLY_NO_PROVIDER_CALL"
REQUIRED_OFF = {
    "FLOWMINUTE_ENABLE_PUBLISH": "0",
    "PUBLISH_ENABLED": "false",
    "FLOWMINUTE_ALLOW_LAPTOP": "0",
    "FLOWMINUTE_ENABLE_GEMINI": "0",
    "FLOWMINUTE_MODEL_PAID_SPEND_USD": "0",
    "FLOWMINUTE_RUNTIME_NETWORK_AUTHORIZED": "0",
    "FLOWMINUTE_OWNER_RELEASE_AUTHORIZED": "0",
}
DISALLOWED_PRESENT = frozenset({
    "YOUTUBE_TOKEN_JSON",
    "YOUTUBE_REFRESH_TOKEN",
    "GOOGLE_OAUTH_REFRESH_TOKEN",
    "FLOWMINUTE_YOUTUBE_OAUTH_SECRET_VALUE",
    "FLOWMINUTE_API_KEY",
    "FLOWMINUTE_PRIVATE_DATABASE_DSN",
    "FLOWMINUTE_YOUTUBE_OAUTH_SECRET_REF",
    "FLOWMINUTE_OWNER_SIGNING_SECRET",
})


class BootGuardRefused(RuntimeError):
    """The entry point refuses escalation, even by a runtime environment."""


def inspect_inert_boot(env: Mapping[str, str]) -> dict:
    """Inspect only controlled non-sensitive flag names; never log values."""
    if not isinstance(env, Mapping):
        raise BootGuardRefused("Invalid environment mapping")
    if env.get("FLOWMINUTE_RUNTIME_MODE") != "OWNER_READ_ONLY_BOOT_GUARD":
        raise BootGuardRefused("Unapproved runtime mode")
    if any(env.get(key) != expected for key, expected in REQUIRED_OFF.items()):
        raise BootGuardRefused("Cloud runtime privilege or spend control is not disabled")
    if any(key in env for key in DISALLOWED_PRESENT):
        raise BootGuardRefused("Credential/secret input forbidden for inert boot guard")
    return {
        "status": STATUS,
        "run_task_was_executed_by_this_module": False,
        "cloud_identity_signature_independently_verified": False,
        "real_youtube_channel_oauth_validated": False,
        "external_private_database_connected": False,
        "protected_secret_access_attempted": False,
        "actual_media_render_performed": False,
        "actual_youtube_insert_performed": False,
        "actual_youtube_schedule_verified": False,
        "real_owner_release_approved": False,
        "network_client_or_provider_call_permitted": False,
        "billable_service_deployed_by_this_module": False,
        "release_authorized": False,
        "next_step": "OWNER_APPROVED_MANUAL_PRIVATE_IDENTITY_AND_COST_PREFLIGHT",
    }


def main() -> int:
    """Only clean fixed JSON status on safe flags; generic error on refusal."""
    try:
        result = inspect_inert_boot(os.environ)
    except BootGuardRefused:
        print("B4C2_INERT_BOOT_GUARD_REFUSED")
        return 70
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
