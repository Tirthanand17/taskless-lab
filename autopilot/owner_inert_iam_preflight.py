"""B4c5: owner-injected READ-ONLY IAM snapshot gate for the B4c2 inert Fargate role pair.

This module NEVER discovers AWS credentials, creates resources, assumes a role,
starts a task, retrieves a token or enables publishing. A trusted owner runner
must inject a boto3-compatible IAM client. CI uses only invented role records.

It verifies a deliberately narrow role profile, not effective authorization:
resource policies, SCPs, endpoint policies, IAM propagation and runtime identity
still require independent owner live inspection. No public CI result authorizes
AWS or YouTube activity.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

ACCOUNT = re.compile(r"[0-9]{12}\Z")
REGION = re.compile(r"(?:us|eu|ap|sa|ca|me|af|il)-[a-z]+-[1-9][0-9]?\Z")
NAME = re.compile(r"[A-Za-z0-9+=,.@_-]{3,64}\Z")
REPO = re.compile(r"[a-z0-9][a-z0-9._/-]{1,159}\Z")
LOG = re.compile(r"/flowminute/owner-private/[A-Za-z0-9/_-]{3,80}\Z")
REFERENCE = re.compile(r"OWNER-[A-Z0-9-]{8,64}\Z")

EXECUTION_POLICY_NAME = "FlowMinuteInertExecutionV1"
STATUS = "OWNER_INJECTED_IAM_POLICY_SNAPSHOT_READ_ONLY_NO_ACTIVATION"


class IamPreflightRefused(ValueError):
    """Malformed, excessive or indeterminate permissions; deny activation."""


@dataclass(frozen=True)
class InertIamScope:
    aws_account_id: str
    aws_region: str
    execution_role_name: str
    task_role_name: str
    ecr_repository_name: str
    existing_log_group_name: str
    owner_change_reference: str


def _check_scope(scope: InertIamScope) -> None:
    if type(scope) is not InertIamScope:
        raise IamPreflightRefused("Owner IAM scope is required")
    for value, pattern in (
        (scope.aws_account_id, ACCOUNT),
        (scope.aws_region, REGION),
        (scope.execution_role_name, NAME),
        (scope.task_role_name, NAME),
        (scope.ecr_repository_name, REPO),
        (scope.existing_log_group_name, LOG),
        (scope.owner_change_reference, REFERENCE),
    ):
        if type(value) is not str or pattern.fullmatch(value) is None:
            raise IamPreflightRefused("Unpinned owner IAM scope")
    if scope.execution_role_name == scope.task_role_name:
        raise IamPreflightRefused("Execution and task roles must differ")


def expected_trust(scope: InertIamScope) -> dict:
    """An ECS-only trust, constrained to the owner's account and region."""
    _check_scope(scope)
    return {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
            "Action": "sts:AssumeRole",
            "Condition": {
                "ArnLike": {"aws:SourceArn": (
                    f"arn:aws:ecs:{scope.aws_region}:{scope.aws_account_id}:*"
                )},
                "StringEquals": {"aws:SourceAccount": scope.aws_account_id},
            },
        }],
    }


def expected_execution_policy(scope: InertIamScope) -> dict:
    """Small explicit inline permissions for ECR image pull and awslogs only."""
    _check_scope(scope)
    repo_arn = (f"arn:aws:ecr:{scope.aws_region}:{scope.aws_account_id}:"
                f"repository/{scope.ecr_repository_name}")
    stream_arn = (f"arn:aws:logs:{scope.aws_region}:{scope.aws_account_id}:"
                  f"log-group:{scope.existing_log_group_name}:"
                  "log-stream:flowminute-readonly-guard/*")
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "ecr:GetAuthorizationToken",
                "Resource": "*",  # ECR does not support resource scoping this action.
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer",
                ],
                "Resource": repo_arn,
            },
            {
                "Effect": "Allow",
                "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
                "Resource": stream_arn,
            },
        ],
    }


def _read(call, message: str) -> dict:
    """Never propagate client exceptions, which can include private metadata."""
    try:
        value = call()
    except Exception:
        raise IamPreflightRefused(message) from None
    if type(value) is not dict:
        raise IamPreflightRefused(message)
    return value


def _list_items(response: dict, field: str) -> list:
    # Refuse truncation rather than accidentally overlooking a hidden policy.
    if response.get("IsTruncated") is not False or response.get("Marker"):
        raise IamPreflightRefused("IAM policy enumeration incomplete")
    items = response.get(field)
    if type(items) is not list or len(items) > 1000:
        raise IamPreflightRefused("Malformed IAM policy enumeration")
    return items


def _role_snapshot(scope: InertIamScope, iam, name: str) -> dict:
    response = _read(
        lambda: iam.get_role(RoleName=name), "IAM role inspection unavailable")
    role = response.get("Role")
    arn = f"arn:aws:iam::{scope.aws_account_id}:role/{name}"
    if (type(role) is not dict or role.get("RoleName") != name
        or role.get("Arn") != arn or role.get("Path") != "/"
        or role.get("AssumeRolePolicyDocument") != expected_trust(scope)
        or role.get("PermissionsBoundary") is not None):
        raise IamPreflightRefused("IAM role trust, path or boundary differs")
    attached = _list_items(_read(
        lambda: iam.list_attached_role_policies(RoleName=name),
        "IAM attached policies unreadable"), "AttachedPolicies")
    if attached:
        raise IamPreflightRefused("Managed IAM attachments forbidden in inert roles")
    inline = _list_items(_read(
        lambda: iam.list_role_policies(RoleName=name),
        "IAM inline policies unreadable"), "PolicyNames")
    if any(type(x) is not str for x in inline) or len(set(inline)) != len(inline):
        raise IamPreflightRefused("Malformed IAM inline policy names")
    return {"role": role, "inline": inline}


def verify_inert_iam_roles(*, iam, scope: InertIamScope) -> dict:
    """Only IAM get/list calls; all evidence is an untrusted injected-client view.

    The task role must have zero identity policy grants. The execution role
    must have exactly one *inline* narrow policy and no managed attachments.
    This template is not suitable for the future real YouTube publisher.
    """
    _check_scope(scope)
    if iam is None:
        raise IamPreflightRefused("Trusted owner IAM read-only client required")

    task = _role_snapshot(scope, iam, scope.task_role_name)
    if task["inline"]:
        raise IamPreflightRefused("Inert application task role has inline permissions")

    execution = _role_snapshot(scope, iam, scope.execution_role_name)
    if execution["inline"] != [EXECUTION_POLICY_NAME]:
        raise IamPreflightRefused("Execution inline policy set differs")
    policy_response = _read(
        lambda: iam.get_role_policy(
            RoleName=scope.execution_role_name,
            PolicyName=EXECUTION_POLICY_NAME),
        "Execution policy readback unavailable")
    if policy_response.get("RoleName") != scope.execution_role_name or (
        policy_response.get("PolicyName") != EXECUTION_POLICY_NAME
        or policy_response.get("PolicyDocument")
        != expected_execution_policy(scope)
    ):
        raise IamPreflightRefused("Execution policy exceeds exact inert allowlist")

    return {
        "status": STATUS,
        "owner_scope_shape_checked": True,
        "task_role_policy_inventory_empty": True,
        "execution_policy_exact_allowlist": True,
        "ecs_service_trust_exactly_scoped": True,
        "identity_snapshot_checked_using_injected_client": True,
        "real_aws_account_and_client_origin_independently_attested": False,
        "effective_permissions_including_resource_policies_verified": False,
        "actual_ecs_task_deployed": False,
        "aws_budget_or_billing_approved": False,
        "youtube_oauth_verified": False,
        "youtube_upload_or_schedule_performed": False,
        "release_authorized": False,
        "next_step": "OWNER_APPROVED_LIVE_IAM_NETWORK_BUDGET_ECR_AND_OAUTH_READBACK",
    }
