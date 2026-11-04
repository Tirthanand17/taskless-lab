"""B3d4c2b3c1: offline cloud identity and endpoint *policy lint*, NEVER activation.

This validates exactly-allowed hypothetical AWS OIDC or GCP WIF claims,
limited secret access roles, and PostgreSQL verify-full client intentions.
There is NO OIDC/JWT verification, cloud API, secret retrieval, credential,
cloud resource, production TLS socket, service deployment, YouTube API or
provider call. Passing static policy lint CAN NEVER authorize a live call.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Mapping, Sequence
from urllib.parse import urlsplit

from autopilot.private_cloud_recovery_preflight import (
    ROLE_PURPOSE, ReadinessError, canonical,
)

REPO = "Tirthanand17/taskless-lab"
REPO_ID = "1400950275"  # Public GitHub repo ID; validate against owner registry at runtime.
OWNER_ID = "157124436"  # Public account ID; a static literal is NOT a trust anchor.
BRANCH = "refs/heads/main"
ENVIRONMENT = "flowminute-prod"
WORKFLOW = f"{REPO}/.github/workflows/flowminute-private-publisher.yml@{BRANCH}"
OIDC_ISSUER = "https://token.actions.githubusercontent.com"
ALLOWED_EVENTS = frozenset({"schedule", "workflow_dispatch"})
AWS_AUDIENCE = "sts.amazonaws.com"
AWS_ROLE_SUBJECT = f"repo:{REPO}:environment:{ENVIRONMENT}"
BACKENDS = frozenset({"aws_secrets_manager", "gcp_secret_manager"})
HEX = re.compile(r"[0-9a-f]{64}\Z")
AWS_ACCOUNT = re.compile(r"[0-9]{12}\Z")
GCP_PROJECT = re.compile(r"[0-9]{6,15}\Z")
DB_HOST = re.compile(r"[a-z][a-z0-9.-]{2,180}\Z")
ROLE_NAMES = ("inference_gateway", "ledger_gateway", "youtube_publisher")
STATUS = "OFFLINE_CLOUD_IDENTITY_LINT_ONLY_NO_ACTIVATION"
MAX = 18000


class IdentityBoundaryError(ReadinessError):
    """Requested deployment trust may allow a fork/PR or credential escalation."""


@dataclass(frozen=True)
class ProductionIdentityIntent:
    """Not a credential; only fixed expectations for *future* reviewed jobs."""
    provider: str
    cloud_project: str
    repository: str
    repository_id: str
    repository_owner_id: str
    branch_ref: str
    environment: str
    workflow_ref: str
    oidc_issuer: str
    token_audience: str
    project_spend_cap_verified_independently: bool
    owner_account_data_use_consent_verified_independently: bool
    real_environment_protection_verified: bool
    private_ledger_connected: bool
    actual_api_key_in_vault: bool


@dataclass(frozen=True)
class SecretAccessIntent:
    """A hypothetical per-resource binding; never an actual IAM readback."""
    workload_role: str
    secret_purpose: str
    resource: str
    action: str
    principal_digest_sha256: str


@dataclass(frozen=True)
class PostgresConnectionIntent:
    """TLS intentions only. No DSN, username, password, socket or CA bytes."""
    db_hostname: str
    database_name: str
    runtime_db_role: str
    tls_minimum_version: str
    sslmode: str
    trusted_ca_certificate_sha256: str
    private_endpoint_policy_sha256: str
    server_hostname_verification_required: bool
    live_tls_handshake_verified: bool


def _sha(s: object) -> bool:
    return isinstance(s, str) and HEX.fullmatch(s) is not None


def _basic(intent: ProductionIdentityIntent) -> None:
    if not isinstance(intent, ProductionIdentityIntent):
        raise IdentityBoundaryError("Unknown typed future deployment intent")
    if (
        intent.provider not in BACKENDS
        or intent.repository != REPO
        or intent.repository_id != REPO_ID
        or intent.repository_owner_id != OWNER_ID
        or intent.branch_ref != BRANCH
        or intent.environment != ENVIRONMENT
        or intent.workflow_ref != WORKFLOW
        or intent.oidc_issuer != OIDC_ISSUER
        or type(intent.project_spend_cap_verified_independently) is not bool
        or type(intent.owner_account_data_use_consent_verified_independently) is not bool
        or type(intent.real_environment_protection_verified) is not bool
        or type(intent.private_ledger_connected) is not bool
        or type(intent.actual_api_key_in_vault) is not bool
        or any(value is not False for value in (
            intent.project_spend_cap_verified_independently,
            intent.owner_account_data_use_consent_verified_independently,
            intent.real_environment_protection_verified,
            intent.private_ledger_connected,
            intent.actual_api_key_in_vault,
        ))
    ):
        raise IdentityBoundaryError("Unsafe or foreign workload identity scope")
    if intent.provider == "aws_secrets_manager":
        if not AWS_ACCOUNT.fullmatch(intent.cloud_project) or intent.token_audience != AWS_AUDIENCE:
            raise IdentityBoundaryError("AWS account/AUD must be explicit")
    else:
        if (
            not GCP_PROJECT.fullmatch(intent.cloud_project)
            or intent.token_audience != (
                f"//iam.googleapis.com/projects/{intent.cloud_project}/"
                "locations/global/workloadIdentityPools/flowminute-production/"
                "providers/github"
            )
        ):
            raise IdentityBoundaryError("GCP WIF audience/project number scope must be exact")


def lint_aws_oidc_trust(intent: ProductionIdentityIntent, policy: Mapping) -> None:
    """Strict AWS IAM role trust policy *shape*, not a real IAM API response.

    The environment-scoped AWS sub does NOT itself bind main branch. GitHub
    protected environment branch restrictions must be independently verified.
    """
    _basic(intent)
    if intent.provider != "aws_secrets_manager" or type(policy) is not dict:
        raise IdentityBoundaryError("No AWS trust policy for this provider")
    expected = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Federated": (
                f"arn:aws:iam::{intent.cloud_project}:"
                "oidc-provider/token.actions.githubusercontent.com"
            )},
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": AWS_AUDIENCE,
                    "token.actions.githubusercontent.com:sub": AWS_ROLE_SUBJECT,
                },
            },
        }],
    }
    if canonical(policy) != canonical(expected):
        raise IdentityBoundaryError("AWS trust policy permits extra scope or wrong AUD/sub")


def lint_gcp_oidc_provider(intent: ProductionIdentityIntent, settings: Mapping) -> None:
    """Strict hypothetical Google WIF condition/mapping; no actual IAM access."""
    _basic(intent)
    if intent.provider != "gcp_secret_manager" or type(settings) is not dict:
        raise IdentityBoundaryError("No GCP provider settings for this scope")
    expected = {
        "issuer_uri": OIDC_ISSUER,
        "allowed_audiences": [intent.token_audience],
        "attribute_mapping": {
            "google.subject": "assertion.repository_id + '/' + assertion.workflow_ref",
            "attribute.repository_id": "assertion.repository_id",
            "attribute.repository_owner_id": "assertion.repository_owner_id",
        },
        "attribute_condition": (
            f"assertion.repository_id == '{REPO_ID}'"
            f" && assertion.repository_owner_id == '{OWNER_ID}'"
            f" && assertion.ref == '{BRANCH}'"
            f" && assertion.environment == '{ENVIRONMENT}'"
            f" && assertion.workflow_ref == '{WORKFLOW}'"
            " && (assertion.event_name == 'schedule'"
            " || assertion.event_name == 'workflow_dispatch')"
        ),
        "scoped_service_account_only": True,
        "disable_persistent_service_account_keys": True,
    }
    if canonical(settings) != canonical(expected):
        raise IdentityBoundaryError("GCP WIF mapping/claims/provider scope too broad")


def inspect_claim_shape(intent: ProductionIdentityIntent, claims: Mapping) -> dict:
    """Compares FAKE/ALREADY-VERIFIED claim values only; NO JWT validation.

    Actual tokens require signature, issuer, audience, expiry and nonce
    validation by an externally enrolled OIDC relying party. Never accept
    values here to authorize secrets or inference.
    """
    _basic(intent)
    if type(claims) is not dict or set(claims) != {
        "iss", "aud", "sub", "repository", "repository_id",
        "repository_owner_id", "ref", "event_name", "environment", "workflow_ref"
    }:
        raise IdentityBoundaryError("Unknown OIDC claim keys or missing claims")
    if (
        claims["iss"] != intent.oidc_issuer
        or claims["aud"] != intent.token_audience
        or claims["sub"] != AWS_ROLE_SUBJECT
        or claims["repository"] != intent.repository
        or claims["repository_id"] != intent.repository_id
        or claims["repository_owner_id"] != intent.repository_owner_id
        or claims["ref"] != intent.branch_ref
        or claims["event_name"] not in ALLOWED_EVENTS
        or claims["environment"] != intent.environment
        or claims["workflow_ref"] != intent.workflow_ref
    ):
        raise IdentityBoundaryError("Fork, pull request, branch, workflow, role or audience rejected")
    return {
        "claim_shape_matches_hypothetical_restricted_workload": True,
        "cryptographic_jwt_signature_verified": False,
        "issuer_or_repo_identity_independently_verified": False,
        "protected_environment_current_rules_verified": False,
        "cloud_security_principal_authenticated": False,
        "allow_assume_cloud_role": False,
        "allow_secret_read": False,
        "allow_provider_call": False,
        "allow_youtube_upload": False,
    }


def lint_secret_scopes(intent: ProductionIdentityIntent,
                       scopes: Sequence[SecretAccessIntent]) -> None:
    """A role MUST only access its own single versioned secret, never '*'."""
    _basic(intent)
    if type(scopes) is not tuple or len(scopes) != len(ROLE_NAMES):
        raise IdentityBoundaryError("Exactly three separately scoped secret roles required")
    seen_roles,seen_principals,seen_resources=set(),set(),set()
    for rule in scopes:
        if not isinstance(rule, SecretAccessIntent) or rule.workload_role not in ROLE_NAMES:
            raise IdentityBoundaryError("Unknown role in secrets matrix")
        expected_purpose=ROLE_PURPOSE[rule.workload_role]
        if rule.secret_purpose != expected_purpose or not _sha(rule.principal_digest_sha256):
            raise IdentityBoundaryError("Mixed-purpose secret principal")
        if intent.provider == "aws_secrets_manager":
            want_action="secretsmanager:GetSecretValue"
            want_resource=(
                f"arn:aws:secretsmanager:ap-south-1:{intent.cloud_project}:"
                f"secret:flowminute/{rule.workload_role}/{expected_purpose}-fixture"
            )
        else:
            want_action="secretmanager.versions.access"
            want_resource=(
                f"projects/{intent.cloud_project}/secrets/"
                f"flowminute-{rule.workload_role}-{expected_purpose}/versions/1"
            )
        if (
            rule.action != want_action or rule.resource != want_resource
            or rule.workload_role in seen_roles
            or rule.principal_digest_sha256 in seen_principals
            or rule.resource in seen_resources
        ):
            raise IdentityBoundaryError("Shared principal or wildcard/cross-purpose secrets")
        seen_roles.add(rule.workload_role)
        seen_principals.add(rule.principal_digest_sha256)
        seen_resources.add(rule.resource)
    if seen_roles != set(ROLE_NAMES):
        raise IdentityBoundaryError("Missing separately isolated secret workload")


def lint_postgres_tls(profile: PostgresConnectionIntent) -> None:
    """Require pinning intent AND hostname verification; no TLS connection."""
    if not isinstance(profile, PostgresConnectionIntent):
        raise IdentityBoundaryError("No structured PostgreSQL TLS intent")
    if (
        not isinstance(profile.db_hostname,str)
        or not DB_HOST.fullmatch(profile.db_hostname)
        or profile.db_hostname.endswith(".")
        or ".." in profile.db_hostname
        or profile.db_hostname in ("localhost", "127.0.0.1")
        or not profile.db_hostname.endswith(".private.example")
        or profile.database_name!="flowminute_private_ledger"
        or profile.runtime_db_role!="fm_runtime_gateway"
        or profile.tls_minimum_version!="TLS1.3"
        or profile.sslmode!="verify-full"
        or not _sha(profile.trusted_ca_certificate_sha256)
        or not _sha(profile.private_endpoint_policy_sha256)
        or profile.server_hostname_verification_required is not True
        or profile.live_tls_handshake_verified is not False
    ):
        raise IdentityBoundaryError("PostgreSQL lacks exact TLS verify-full/private endpoint requirements")


def inspect_offline_deployment_intent(
    *, identity: ProductionIdentityIntent,
    oidc_policy: Mapping,
    simulated_claims: Mapping,
    secrets: tuple[SecretAccessIntent,...],
    database_tls: PostgresConnectionIntent,
) -> dict:
    """Aggregate only static fixtures; NEVER construct a release credential."""
    _basic(identity)
    if identity.provider=="aws_secrets_manager":
        lint_aws_oidc_trust(identity, oidc_policy)
    else:
        lint_gcp_oidc_provider(identity, oidc_policy)
    claim=inspect_claim_shape(identity, simulated_claims)
    lint_secret_scopes(identity,secrets)
    lint_postgres_tls(database_tls)
    return {
        "status": STATUS,
        "provider_option": identity.provider,
        "hypothetical_policy_and_claim_shape_checked": True,
        "three_separate_secret_scopes_linted": True,
        "postgres_client_tls_verify_full_required": True,
        "independently_authenticated_oidc_claims": False,
        "real_cloud_iam_policy_readback_verified": False,
        "actual_github_protected_environment_rules_verified": False,
        "actual_cloud_vault_credentials_accessed": False,
        "owner_consent_or_project_entitlement_verified": False,
        "account_actual_zero_charge_guaranteed": False,
        "production_database_connected": False,
        "external_immutable_backup_anchor_connected": False,
        "real_generative_provider_called": False,
        "youtube_upload_enabled": False,
        "release_authorized": False,
        "cloud_deployment_authorized": False,
    }
