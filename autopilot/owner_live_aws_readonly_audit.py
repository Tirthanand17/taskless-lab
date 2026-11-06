"""B4c7 manual protected owner-cloud READ-ONLY audit adapter (never deploy).

The production CLI is intended ONLY for a protected GitHub Actions environment
after an independent owner-selected OIDC read-only IAM role has been configured.
No PR invokes this module with AWS credentials. Tests inject *fake* clients.

B4c6 remains the authority for inert ECS task/network/IAM/image validation.
Passing this readback is still NOT consent to deploy, spend, generate content,
retrieve YouTube OAuth or schedule/publish a video.
"""
from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from typing import Mapping

from autopilot.owner_inert_composite_preflight import (
    InertOwnerCompositeScope,
    CompositeOwnerPreflightRefused,
    _validate_cross_scope,
    inspect_inert_owner_runtime,
)
from autopilot.owner_inert_iam_preflight import InertIamScope
from autopilot.owner_private_network_image_preflight import OwnerInertNetworkScope

STATUS = "B4C7_PROTECTED_OWNER_LIVE_READONLY_SNAPSHOT_NOT_DEPLOYMENT"
REPO = "Tirthanand17/taskless-lab"
OWNER_ACTOR = "Tirthanand17"
ENVIRONMENT_NAME = "flowminute-owner-cloud-readonly"
MANUAL_TEMPLATE = "infra/aws/owner-readonly-fargate-taskdef.cfn.json"
SCHEMA = "flowminute-b4c7-protected-owner-audit-scope-v1"
OPERATOR_KEYS = frozenset({
    "schema", "aws_account_id", "aws_region", "inspector_role_name",
    "execution_role_name", "task_role_name", "ecr_repository_name",
    "existing_log_group_name", "owner_change_reference", "vpc_id",
    "subnet_ids", "task_security_group_id", "endpoint_security_group_id",
    "image_digest", "source_commit_sha",
})
SECRET_ENV = {
    "FLOWMINUTE_B4C7_SCOPE_JSON",
    "FLOWMINUTE_B4C7_SIGNED_IMAGE_B64",
    "FLOWMINUTE_B4C7_IMAGE_SIGNATURE_B64",
    "FLOWMINUTE_B4C7_SIGNER_PUBKEY_B64",
    "FLOWMINUTE_B4C7_SIGNER_FINGERPRINT",
}
ALLOWED_METHODS = {
    "sts": frozenset(("get_caller_identity",)),
    "iam": frozenset((
        "get_role", "list_attached_role_policies", "list_role_policies",
        "get_role_policy",
    )),
    "ec2": frozenset((
        "describe_vpcs", "describe_vpc_attribute", "describe_subnets",
        "describe_vpc_endpoints", "describe_route_tables",
        "describe_security_groups",
    )),
    "ecr": frozenset((
        "describe_repositories", "describe_images",
        "describe_image_scan_findings",
    )),
}


class LiveAuditRefused(ValueError):
    """Blocked or indeterminate manual owner-cloud read-only audit."""


@dataclass(frozen=True)
class AuditInputs:
    scope: InertOwnerCompositeScope
    signed_image_json: bytes
    signature_b64: str
    signer_pubkey_b64: str
    signer_fingerprint: str


def _json_strict(raw: str) -> object:
    def unique(pairs: list[tuple[str, object]]) -> dict:
        out = {}
        for k, v in pairs:
            if k in out:
                raise LiveAuditRefused("Duplicate protected input property")
            out[k] = v
        return out
    try:
        return json.loads(
            raw, object_pairs_hook=unique,
            parse_constant=lambda _: (_ for _ in ()).throw(
                LiveAuditRefused("Nonfinite protected input")),
        )
    except (UnicodeError, ValueError, TypeError):
        raise LiveAuditRefused("Malformed protected input") from None


def parse_scope(raw: object) -> InertOwnerCompositeScope:
    """Owner private scope shape only; a JSON string is not consent."""
    if (type(raw) is not str or not 50 <= len(raw.encode("utf-8")) <= 8192):
        raise LiveAuditRefused("Private owner scope missing or oversized")
    data = _json_strict(raw)
    if type(data) is not dict or set(data) != OPERATOR_KEYS or data["schema"] != SCHEMA:
        raise LiveAuditRefused("Unrecognized owner scope schema")
    if (type(data["subnet_ids"]) is not list or len(data["subnet_ids"]) != 2
        or any(type(value) is not str for value in data["subnet_ids"])):
        raise LiveAuditRefused("Expected two pinned private subnets")
    try:
        scope = InertOwnerCompositeScope(
            iam_scope=InertIamScope(
                aws_account_id=data["aws_account_id"],
                aws_region=data["aws_region"],
                execution_role_name=data["execution_role_name"],
                task_role_name=data["task_role_name"],
                ecr_repository_name=data["ecr_repository_name"],
                existing_log_group_name=data["existing_log_group_name"],
                owner_change_reference=data["owner_change_reference"],
            ),
            network_scope=OwnerInertNetworkScope(
                account_id=data["aws_account_id"],
                region=data["aws_region"],
                vpc_id=data["vpc_id"],
                subnet_ids=tuple(data["subnet_ids"]),
                task_security_group_id=data["task_security_group_id"],
                endpoint_security_group_id=data["endpoint_security_group_id"],
                ecr_repository=data["ecr_repository_name"],
                image_digest=data["image_digest"],
                source_commit_sha=data["source_commit_sha"],
            ),
            inspector_role_name=data["inspector_role_name"],
        )
        _validate_cross_scope(scope)
    except (CompositeOwnerPreflightRefused, KeyError, TypeError, ValueError):
        raise LiveAuditRefused("Invalid or inconsistent protected owner scope") from None
    return scope


def _require_protected_context(
    env: Mapping[str, str], scope: InertOwnerCompositeScope, *, live: bool,
) -> None:
    """Check mandatory GitHub run conditions before requesting AWS clients.

    GitHub actor/ref checks are defense-in-depth, NOT a replacement for IAM
    OIDC trust, GitHub environment reviewers, or authentic owner consent.
    """
    if (env.get("GITHUB_REPOSITORY") != REPO
        or env.get("GITHUB_REF") != "refs/heads/main"
        or env.get("GITHUB_EVENT_NAME") != "workflow_dispatch"
        or env.get("GITHUB_ACTOR") != OWNER_ACTOR
        or env.get("FLOWMINUTE_B4C7_PROTECTED_ENVIRONMENT") != ENVIRONMENT_NAME
        or env.get("FLOWMINUTE_B4C7_AUDIT_MODE") != "INERT_READ_ONLY_ONLY"
        or env.get("AWS_REGION") != scope.iam_scope.aws_region
        or env.get("FLOWMINUTE_B4C7_CHANGE_REFERENCE")
            != scope.iam_scope.owner_change_reference
        or re.fullmatch(r"[a-f0-9]{40}", env.get("GITHUB_SHA", "")) is None):
        raise LiveAuditRefused("Protected owner GitHub run scope not verified")
    if live and not (
        env.get("AWS_SESSION_TOKEN")
        and env.get("AWS_ACCESS_KEY_ID")
        and env.get("AWS_SECRET_ACCESS_KEY")
        and env.get("AWS_EC2_METADATA_DISABLED", "").lower() == "true"
    ):
        raise LiveAuditRefused("Short-lived OIDC role credentials not available")


def _b64(raw: object, *, max_bytes: int) -> bytes:
    if (type(raw) is not str or len(raw) > ((max_bytes + 2) // 3 * 4 + 8)):
        raise LiveAuditRefused("Protected signed data missing or oversized")
    try:
        value = base64.b64decode(raw, validate=True)
    except (ValueError, base64.binascii.Error):
        raise LiveAuditRefused("Protected signed data malformed") from None
    if not value or len(value) > max_bytes:
        raise LiveAuditRefused("Protected signed data incorrect length")
    return value


def load_inputs(env: Mapping[str, str], *, live: bool) -> AuditInputs:
    if any(type(env.get(name)) is not str or not env.get(name) for name in SECRET_ENV):
        raise LiveAuditRefused("Protected owner configuration incomplete")
    scope = parse_scope(env["FLOWMINUTE_B4C7_SCOPE_JSON"])
    _require_protected_context(env, scope, live=live)
    signed = _b64(env["FLOWMINUTE_B4C7_SIGNED_IMAGE_B64"], max_bytes=8192)
    signature = env["FLOWMINUTE_B4C7_IMAGE_SIGNATURE_B64"]
    key = env["FLOWMINUTE_B4C7_SIGNER_PUBKEY_B64"]
    fingerprint = env["FLOWMINUTE_B4C7_SIGNER_FINGERPRINT"]
    if (len(_b64(signature, max_bytes=64)) != 64
        or len(_b64(key, max_bytes=32)) != 32
        or type(fingerprint) is not str
        or re.fullmatch("[0-9a-f]{64}", fingerprint) is None):
        raise LiveAuditRefused("Protected owner image trust anchor invalid")
    # B4c3 verifies actual cryptography, image content and live ECR readback.
    return AuditInputs(scope, signed, signature, key, fingerprint)


class OnlyReadMethods:
    """Restrict the injected boto3 client surface to explicit read calls."""

    __slots__ = ("__source", "__allowed")

    def __init__(self, source: object, allowed: frozenset[str]):
        object.__setattr__(self, "_OnlyReadMethods__source", source)
        object.__setattr__(self, "_OnlyReadMethods__allowed", allowed)

    def __getattr__(self, name: str):
        if name not in self.__allowed:
            raise LiveAuditRefused("Unsupported AWS API operation blocked")
        target = getattr(self.__source, name, None)
        if not callable(target):
            raise LiveAuditRefused("Required read-only AWS operation unavailable")
        return target


def run_readonly_audit(
    *, env: Mapping[str, str], session: object, at: datetime,
    manual_task_template_json: str,
) -> dict:
    """Use real AWS clients ONLY with a provided owner session after checks.

    Public CI injects fake boto3-compatible sessions. The adapter never calls
    Session() or reads credentials itself, and never exposes input identifiers.
    """
    inputs = load_inputs(env, live=True)
    if (type(manual_task_template_json) is not str
        or len(manual_task_template_json.encode("utf-8")) > 65536):
        raise LiveAuditRefused("Unapproved task source")
    if not isinstance(at, datetime) or at.tzinfo is None or at.utcoffset() is None:
        raise LiveAuditRefused("Timezone-aware inspection time required")
    clients = {}
    try:
        for name, allowed in ALLOWED_METHODS.items():
            # A session object has no permission to assume a new role here.
            source = session.client(name, region_name=inputs.scope.iam_scope.aws_region)
            clients[name] = OnlyReadMethods(source, allowed)
        report = inspect_inert_owner_runtime(
            scope=inputs.scope,
            sts=clients["sts"], iam=clients["iam"],
            ec2=clients["ec2"], ecr=clients["ecr"],
            manual_task_template_json=manual_task_template_json,
            signed_image_json=inputs.signed_image_json,
            owner_signature_b64=inputs.signature_b64,
            owner_public_key_b64=inputs.signer_pubkey_b64,
            owner_public_key_sha256=inputs.signer_fingerprint,
            at=at,
        )
    except (LiveAuditRefused, CompositeOwnerPreflightRefused):
        raise LiveAuditRefused("Protected read-only snapshot denied") from None
    except Exception:
        raise LiveAuditRefused("Protected AWS client readback unavailable") from None

    if (report.get("release_authorized") is not False
        or report.get("real_ecs_task_launched") is not False
        or report.get("youtube_video_uploaded_or_scheduled") is not False):
        raise LiveAuditRefused("Cloud audit attempted release escalation")
    return {
        "status": STATUS,
        "bounded_owner_sts_iam_ec2_ecr_readback_finished": True,
        "inert_configuration_checks_matched": True,
        "signed_image_metadata_checked_using_injected_client": True,
        # Independently verifiable owner identity needs external OIDC/IAM audit.
        "oidc_policy_and_environment_review_independently_verified": False,
        "live_owner_account_proven_by_public_ci": False,
        "effective_iam_and_runtime_permissions_verified": False,
        "approved_aws_budget_or_cost_cap_verified": False,
        "real_oci_registry_signature_verified": False,
        "actual_fargate_task_launched": False,
        "real_private_media_and_ledger_connected": False,
        "youtube_oauth_or_publish_performed": False,
        "release_authorized": False,
        "owner_activation_still_required": True,
    }


def main() -> int:
    """Machine output deliberately contains no owner identifier or secret."""
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--preflight-only", action="store_true")
    modes.add_argument("--live-readonly", action="store_true")
    args = parser.parse_args()
    try:
        env = os.environ
        if args.preflight_only:
            load_inputs(env, live=False)
            result = {
                "status": "B4C7_PROTECTED_INPUT_SHAPE_OK_NO_AWS_CALL",
                "real_aws_readback_performed": False,
                "owner_consent_authenticated": False,
                "release_authorized": False,
            }
        else:
            inputs = load_inputs(env, live=True)
            # Only the protected OIDC workflow may reach this code.
            import boto3
            from botocore.config import Config
            # SDK obtains only the already issued temporary OIDC role
            # credentials; no AWS key is embedded or persisted here.
            session = boto3.session.Session(
                region_name=inputs.scope.iam_scope.aws_region,
                botocore_session=None,
            )
            # use short timeouts to fail closed on IAM / network outages
            safe_config = Config(
                connect_timeout=5, read_timeout=12,
                retries={"max_attempts": 1},
            )
            class BoundedSession:
                def client(self, service, *, region_name):
                    if service not in ALLOWED_METHODS:
                        raise LiveAuditRefused("Unexpected AWS client")
                    return session.client(
                        service, region_name=region_name, config=safe_config,
                    )
            result = run_readonly_audit(
                env=env, session=BoundedSession(),
                at=datetime.now(timezone.utc),
                manual_task_template_json=Path(MANUAL_TEMPLATE).read_text(
                    encoding="utf-8"),
            )
        print(json.dumps(result, separators=(",", ":"), sort_keys=True))
        return 0
    except Exception:
        # Even leaked provider exceptions must not leave GitHub runner logs.
        print("B4C7_PROTECTED_READONLY_AUDIT_REFUSED")
        return 70


if __name__ == "__main__":
    raise SystemExit(main())
