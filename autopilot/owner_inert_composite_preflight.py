"""B4c6: compose the *existing* inert owner Fargate preflight boundaries.

This read-only gate performs no client discovery, cloud deployment, task run,
network mutation, billing query, secret read, Google OAuth or YouTube write.
A separately approved operator must inject real read-only STS/IAM/EC2/ECR
clients and an independently enrolled owner signing public-key fingerprint.

Even when all structural readbacks pass, a caller can supply fake clients;
actual AWS identity, effective IAM, task runtime, consent and model/media
rights are NOT established by this module. Never interpret as launch approval.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re

from autopilot.owner_fargate_taskdef_lint import (
    lint_inert_task_definition, strict_load, UnsafeCloudRuntimeTemplate,
)
from autopilot.owner_inert_iam_preflight import (
    InertIamScope, IamPreflightRefused, verify_inert_iam_roles, _check_scope,
)
from autopilot.owner_private_network_image_preflight import (
    OwnerInertNetworkScope, PreflightRefused, verify_scope, safe_read_only_gate,
)

SESSION = re.compile(r"[A-Za-z0-9+=,.@_-]{1,64}\Z")
INSPECTOR = re.compile(r"[A-Za-z0-9+=,.@_-]{3,64}\Z")
STATUS = "B4C6_INJECTED_INERT_RUNTIME_PREFLIGHT_READONLY_NO_DEPLOY"


class CompositeOwnerPreflightRefused(ValueError):
    """Any missing, incoherent, or unsafe owner evidence blocks activation."""


@dataclass(frozen=True)
class InertOwnerCompositeScope:
    iam_scope: InertIamScope
    network_scope: OwnerInertNetworkScope
    inspector_role_name: str


def _validate_cross_scope(scope: InertOwnerCompositeScope) -> None:
    if type(scope) is not InertOwnerCompositeScope:
        raise CompositeOwnerPreflightRefused("Owner runtime scope absent")
    try:
        _check_scope(scope.iam_scope)
        verify_scope(scope.network_scope)
    except (IamPreflightRefused, PreflightRefused):
        raise CompositeOwnerPreflightRefused("Malformed owner runtime scope") from None
    if (scope.iam_scope.aws_account_id != scope.network_scope.account_id
        or scope.iam_scope.aws_region != scope.network_scope.region
        or scope.iam_scope.ecr_repository_name != scope.network_scope.ecr_repository):
        raise CompositeOwnerPreflightRefused("IAM / ECR / VPC scopes are inconsistent")
    if (type(scope.inspector_role_name) is not str
        or INSPECTOR.fullmatch(scope.inspector_role_name) is None
        or scope.inspector_role_name in (
            scope.iam_scope.execution_role_name, scope.iam_scope.task_role_name)):
        raise CompositeOwnerPreflightRefused("Independent owner inspector role required")


def _verify_injected_sts(sts: object, scope: InertOwnerCompositeScope) -> None:
    try:
        identity=sts.get_caller_identity()
    except Exception:
        # AWS exceptions can contain credentials, account metadata and URLs.
        raise CompositeOwnerPreflightRefused("Owner STS readback unavailable") from None
    arn_prefix=(
        f"arn:aws:sts::{scope.iam_scope.aws_account_id}:"
        f"assumed-role/{scope.inspector_role_name}/"
    )
    if (type(identity) is not dict
        or identity.get("Account") != scope.iam_scope.aws_account_id
        or type(identity.get("Arn")) is not str
        or not identity["Arn"].startswith(arn_prefix)
        or SESSION.fullmatch(identity["Arn"][len(arn_prefix):]) is None):
        raise CompositeOwnerPreflightRefused("Injected STS role identity mismatch")


def inspect_inert_owner_runtime(
    *, scope: InertOwnerCompositeScope, sts: object, iam: object,
    ec2: object, ecr: object, manual_task_template_json: str,
    signed_image_json: bytes, owner_signature_b64: str,
    owner_public_key_b64: str, owner_public_key_sha256: str,
    at: datetime,
) -> dict:
    """Fail closed at each boundary; never use any API with side effects.

    A safe result means ONLY that injected client responses and signed metadata
    matched the static *inert* template. It never grants owner/cloud release.
    """
    _validate_cross_scope(scope)
    if (type(manual_task_template_json) is not str
        or len(manual_task_template_json.encode("utf-8")) > 65536):
        raise CompositeOwnerPreflightRefused("Manual task template absent or oversized")
    if not isinstance(at,datetime) or at.tzinfo is None or at.utcoffset() is None:
        raise CompositeOwnerPreflightRefused("Timezone-aware inspection required")

    try:
        template=lint_inert_task_definition(strict_load(manual_task_template_json))
    except UnsafeCloudRuntimeTemplate:
        raise CompositeOwnerPreflightRefused("Unsafe manual inert task template") from None
    if (template["release_authorized"] is not False
        or template["real_ecs_task_run"] is not False
        or template["real_youtube_oauth_or_video"] is not False):
        raise CompositeOwnerPreflightRefused("Manual task unexpectedly enabled release")

    _verify_injected_sts(sts,scope)
    try:
        roles=verify_inert_iam_roles(iam=iam,scope=scope.iam_scope)
        cloud=safe_read_only_gate(
            scope.network_scope,ec2,ecr,signed_image_json,owner_signature_b64,
            owner_public_key_b64,owner_public_key_sha256,at=at)
    except (IamPreflightRefused,PreflightRefused):
        raise CompositeOwnerPreflightRefused("IAM, network or image evidence denied") from None
    except Exception:
        # Never return or chain untrusted boto3 client exception values.
        raise CompositeOwnerPreflightRefused("External owner readback failed") from None

    if (roles["release_authorized"] is not False
        or roles["actual_ecs_task_deployed"] is not False
        or cloud["release_authorized"] is not False
        or cloud["cloud_resources_created"] is not False
        or cloud["real_cloud_task_executed"] is not False
        or cloud["image_provenance_evidence"]["release_authorized"] is not False
        or cloud["network_configuration_evidence"]["release_authorized"] is not False):
        raise CompositeOwnerPreflightRefused("Owner source gates attempted privilege escalation")

    # No identifiers, source text, key material, IAM policy, account number,
    # private bucket, token, or image signature should enter public evidence.
    return {
        "status": STATUS,
        "manual_inert_template_structurally_verified": True,
        "injected_sts_role_account_structure_verified": True,
        "injected_iam_inert_role_policy_structure_verified": True,
        "injected_private_ec2_network_structure_verified": True,
        "pinned_ed25519_source_attestation_and_ecr_scan_readback_verified": True,
        "actual_aws_client_origin_independently_attested": False,
        "real_live_owner_account_inspected_by_public_ci": False,
        "runtime_iam_effective_permissions_verified": False,
        "actual_signed_image_runtime_proven": False,
        "real_oci_registry_signature_verified": False,
        "owner_approved_billing_or_spend": False,
        "production_media_or_postgres_verified": False,
        "oauth_or_youtube_channel_verified": False,
        "real_ecs_task_launched": False,
        "cloud_resources_created": False,
        "youtube_video_uploaded_or_scheduled": False,
        "release_authorized": False,
        "owner_activation_still_required": True,
        "next_step": "OWNER_APPROVED_LIVE_ACCOUNT_BUDGET_IDENTITY_NETWORK_AND_IMAGE_ATTESTATION",
    }
