"""B3d4c2b3b: provider-neutral SECRET METADATA and backup-evidence integrity.

This module intentionally contains no vault SDK, credential material, live
cloud endpoints, paid resource provisioning, model inference or publishing.
It checks synthetic deployment *requirements* and cryptographic evidence
formats. A fake role digest, hash or signature is not proof of real IAM,
identity, provider terms, billing limits, immutable anchor storage or backup.

For production all anchor roots, signer public keys, secret handles and
provider account credentials MUST be obtained from independent authenticated
owner-approved private systems; the public GitHub CI has NONE of them.
"""
from __future__ import annotations

import base64
import binascii
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import re
from typing import Mapping, Sequence

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

STATUS = "CLOUD_VAULT_REQUIREMENTS_ONLY_NO_REAL_SECRET_OR_DEPLOYMENT"
RECOVERY_STATUS = "SYNTHETIC_BACKUP_REPLAY_AND_SIGNED_ANCHOR_VALIDATED_NO_PRODUCTION"
DOMAIN = b"FLOWMINUTE_B3D4C2B3B_RECOVERY_RECEIPT_V1\x00"
ROLE_PURPOSE = {
    "inference_gateway": "gemini_draft_api_credential",
    "ledger_gateway": "postgres_mock_gateway_credential",
    "youtube_publisher": "youtube_oauth_refresh_credential",
}
HEX = re.compile(r"[a-f0-9]{64}\Z")
NAME = re.compile(r"[a-z][a-z0-9_]{2,63}\Z")
EPISODE = re.compile(r"fm_[0-9]{8}_(?:short_am|long|short_pm)\Z")
REF = re.compile(
    r"flowminute://vault/(?:inference_gateway|ledger_gateway|youtube_publisher)/"
    r"(?:gemini_draft_api_credential|postgres_mock_gateway_credential|"
    r"youtube_oauth_refresh_credential)/version-[1-9][0-9]{0,5}\Z"
)
MAX_BACKUP_BYTES = 2_000_000
MAX_EVENTS = 1000


class ReadinessError(ValueError):
    """Reject fabricated entitlement, reused secrets, tampered or stale backups."""


@dataclass(frozen=True)
class SecretRequirement:
    role: str
    purpose: str
    logical_secret_ref: str
    workload_principal_sha256: str
    resource_policy_sha256: str
    private_endpoint_policy_sha256: str
    encryption_policy_sha256: str
    cloud_backend: str
    region_id: str
    allowed_operation: str
    session_ttl_seconds: int
    max_rotation_interval_days: int
    requires_private_endpoint: bool
    requires_access_audit: bool
    requires_workload_identity: bool


@dataclass(frozen=True)
class PrivateCloudRequirements:
    schema_version: int
    isolated_owner_project_sha256: str
    cloud_backend: str
    region_id: str
    planned_secret_requirements: tuple[SecretRequirement, ...]
    database_tls_minimum: str
    database_owner_no_login: bool
    deny_runtime_db_superuser: bool
    independent_backup_reader_required: bool
    independent_external_audit_anchor_required: bool
    max_backup_rpo_minutes: int
    max_backup_rto_minutes: int


@dataclass(frozen=True)
class MockAuditEvent:
    sequence: int
    lease_id: str
    episode_id: str
    action: str
    value_sha256: str


@dataclass(frozen=True)
class RecoveryManifest:
    schema_version: int
    backup_id: str
    generation: int
    parent_manifest_sha256: str
    parent_event_count: int
    event_count: int
    ordered_event_head_sha256: str
    snapshot_sha256: str
    snapshot_bytes: int


def _hash(s: object) -> bool:
    return isinstance(s,str) and HEX.fullmatch(s) is not None


def canonical(obj: object) -> bytes:
    try:
        raw = json.dumps(obj, ensure_ascii=False,sort_keys=True,
                         separators=(",",":"),allow_nan=False).encode("utf-8")
    except (ValueError, TypeError, OverflowError, RecursionError) as exc:
        raise ReadinessError("Cannot canonicalize evidence") from exc
    if len(raw)>MAX_BACKUP_BYTES:
        raise ReadinessError("Unbounded evidence record")
    return raw


def _sha_bytes(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def inspect_private_cloud_requirements(plan: PrivateCloudRequirements) -> dict:
    """Static REQUIREMENTS lint; never an IAM proof or live activation gate."""
    if not isinstance(plan,PrivateCloudRequirements):
        raise ReadinessError("Unknown typed cloud requirements")
    if (
        type(plan.schema_version) is not int or plan.schema_version!=1
        or not _hash(plan.isolated_owner_project_sha256)
        or plan.cloud_backend not in ("aws_secrets_manager","gcp_secret_manager")
        or not isinstance(plan.region_id,str)
        or not re.fullmatch(r"[a-z]{2}(?:-[a-z]+){1,2}-[0-9]",plan.region_id)
        or plan.database_tls_minimum!="TLS1.3"
        or plan.database_owner_no_login is not True
        or plan.deny_runtime_db_superuser is not True
        or plan.independent_backup_reader_required is not True
        or plan.independent_external_audit_anchor_required is not True
        or type(plan.max_backup_rpo_minutes) is not int
        or not 1<=plan.max_backup_rpo_minutes<=60
        or type(plan.max_backup_rto_minutes) is not int
        or not 1<=plan.max_backup_rto_minutes<=240
    ):
        raise ReadinessError("Insufficient private cloud design requirements")
    entries=plan.planned_secret_requirements
    if not isinstance(entries,tuple) or len(entries)!=len(ROLE_PURPOSE):
        raise ReadinessError("Require three separated non-privileged secret purposes")
    seen_roles=set()
    seen_refs=set()
    seen_principals=set()
    for item in entries:
        if not isinstance(item,SecretRequirement):
            raise ReadinessError("Invalid typed vault requirement")
        if (
            item.role not in ROLE_PURPOSE
            or ROLE_PURPOSE[item.role]!=item.purpose
            or not isinstance(item.logical_secret_ref,str)
            or not REF.fullmatch(item.logical_secret_ref)
            or item.logical_secret_ref != (
                f"flowminute://vault/{item.role}/{item.purpose}/"
                +item.logical_secret_ref.rsplit("/",1)[-1]
            )
            or item.cloud_backend != plan.cloud_backend
            or item.region_id != plan.region_id
            or item.allowed_operation!="read_secret_version"
            or type(item.session_ttl_seconds) is not int
            or not 60<=item.session_ttl_seconds<=900
            or type(item.max_rotation_interval_days) is not int
            or not 1<=item.max_rotation_interval_days<=90
            or item.requires_private_endpoint is not True
            or item.requires_access_audit is not True
            or item.requires_workload_identity is not True
            or any(not _hash(value) for value in (
                item.workload_principal_sha256,
                item.resource_policy_sha256,
                item.private_endpoint_policy_sha256,
                item.encryption_policy_sha256,
            ))
        ):
            raise ReadinessError("Overbroad, cross-purpose or unscoped vault requirement")
        if (
            item.role in seen_roles
            or item.logical_secret_ref in seen_refs
            or item.workload_principal_sha256 in seen_principals
        ):
            raise ReadinessError("No shared identities, secrets or wildcard access")
        seen_roles.add(item.role)
        seen_refs.add(item.logical_secret_ref)
        seen_principals.add(item.workload_principal_sha256)
    if seen_roles != set(ROLE_PURPOSE):
        raise ReadinessError("Missing expected isolated workload roles")
    return {
        "status": STATUS,
        "requirements_schema_valid":True,
        "distinct_secret_purposes":len(seen_roles),
        "separate_workload_principals_described":True,
        "private_network_required_not_verified":True,
        "cloud_secret_actually_exists":False,
        "cloud_iam_permissions_independently_verified":False,
        "private_endpoint_exists":False,
        "kms_key_policy_verified":False,
        "actual_workload_identity_authenticated":False,
        "owner_provider_account_and_terms_approved":False,
        "actual_backup_restore_proven":False,
        "independent_immutable_audit_service_connected":False,
        "live_generative_inference_enabled":False,
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }


def _ordered_head(events: Sequence[MockAuditEvent]) -> str:
    if not isinstance(events,(list,tuple)) or not 1<=len(events)<=MAX_EVENTS:
        raise ReadinessError("Nonempty bounded ordered audit events required")
    previous = _sha_bytes(DOMAIN+b"initial")
    opened:dict[str,str]={}
    closed:set[str]=set()
    episodes:set[str]=set()
    for index,event in enumerate(events,1):
        if (
            not isinstance(event,MockAuditEvent)
            or type(event.sequence) is not int or event.sequence!=index
            or not isinstance(event.lease_id,str) or not NAME.fullmatch(event.lease_id)
            or not isinstance(event.episode_id,str) or not EPISODE.fullmatch(event.episode_id)
            or event.action not in ("BURN","MOCK_CLOSE")
            or not _hash(event.value_sha256)
        ):
            raise ReadinessError("Noncanonical or reordered mock audit log")
        if event.action=="BURN":
            if event.lease_id in opened or event.episode_id in episodes:
                raise ReadinessError("Duplicate burned lease or episode in audit log")
            opened[event.lease_id]=event.episode_id
            episodes.add(event.episode_id)
        else:
            if opened.get(event.lease_id)!=event.episode_id or event.lease_id in closed:
                raise ReadinessError("Mock close without corresponding unique burn")
            closed.add(event.lease_id)
        previous=_sha_bytes(bytes.fromhex(previous)+canonical(asdict(event)))
    return previous


def build_mock_recovery_manifest(
    *, events: Sequence[MockAuditEvent], snapshot_bytes: bytes,
    backup_id: str, generation: int,
    parent: RecoveryManifest | None = None,
) -> RecoveryManifest:
    """Calculate a test-only exact byte + ordered audit evidence manifest."""
    if (
        not isinstance(snapshot_bytes,bytes)
        or not 1<=len(snapshot_bytes)<=MAX_BACKUP_BYTES
        or not isinstance(backup_id,str) or not NAME.fullmatch(backup_id)
        or type(generation) is not int or generation<1 or generation>1_000_000
    ):
        raise ReadinessError("Invalid bounded mock backup")
    head=_ordered_head(events)
    if parent is None:
        if generation!=1:
            raise ReadinessError("Missing prior backup generation trust record")
        parent_hash="0"*64
        parent_count=0
    else:
        if not isinstance(parent,RecoveryManifest) or generation!=parent.generation+1:
            raise ReadinessError("Generation reset, jump, or nontrusted previous backup")
        if len(events)<parent.event_count:
            raise ReadinessError("Audit log sequence rolled back")
        if _ordered_head(events[:parent.event_count])!=parent.ordered_event_head_sha256:
            raise ReadinessError("Historical audit events rewritten after backup")
        parent_hash=_sha_bytes(canonical(asdict(parent)))
        parent_count=parent.event_count
    return RecoveryManifest(
        schema_version=1,
        backup_id=backup_id,
        generation=generation,
        parent_manifest_sha256=parent_hash,
        parent_event_count=parent_count,
        event_count=len(events),
        ordered_event_head_sha256=head,
        snapshot_sha256=_sha_bytes(snapshot_bytes),
        snapshot_bytes=len(snapshot_bytes),
    )


def verify_mock_restored_backup(
    *, manifest: RecoveryManifest,
    restored_bytes: bytes,
    restored_events: Sequence[MockAuditEvent],
    parent: RecoveryManifest | None,
    externally_pinned_manifest_sha256: str,
    detached_external_signature_b64: str,
    trusted_external_anchor_public_key_b64: str,
    expected_generation: int,
    expected_event_count: int,
) -> dict:
    """Verify externally *supplied* anchor/signature; NEVER issue one here.

    A caller may fabricate a test trust root: no real independent cloud WORM
    anchor, authenticated enrollment, physical backup integrity or PostgreSQL
    recovery is proved by this routine.
    """
    if (
        not isinstance(manifest,RecoveryManifest)
        or not _hash(externally_pinned_manifest_sha256)
        or type(expected_generation) is not int
        or type(expected_event_count) is not int
        or expected_generation!=manifest.generation
        or expected_event_count!=manifest.event_count
    ):
        raise ReadinessError("Missing independently expected backup head")
    expected=build_mock_recovery_manifest(
        events=restored_events,snapshot_bytes=restored_bytes,
        backup_id=manifest.backup_id,generation=manifest.generation,
        parent=parent,
    )
    if manifest!=expected:
        raise ReadinessError("Backup bytes or ordered audit history changed")
    head=_sha_bytes(canonical(asdict(expected)))
    if head!=externally_pinned_manifest_sha256:
        raise ReadinessError("Backup root mismatches externally pinned digest")
    try:
        key_raw=base64.b64decode(trusted_external_anchor_public_key_b64,validate=True)
        sig=base64.b64decode(detached_external_signature_b64,validate=True)
        if len(key_raw)!=32 or len(sig)!=64:
            raise ReadinessError("Malformed independent backup signer material")
        Ed25519PublicKey.from_public_bytes(key_raw).verify(
            sig,DOMAIN+bytes.fromhex(head)
        )
    except (ValueError,TypeError,binascii.Error,InvalidSignature) as exc:
        raise ReadinessError("External backup manifest signature invalid") from exc
    return {
        "status": RECOVERY_STATUS,
        "restored_mock_bytes_match_external_signature":True,
        "ordered_mock_audit_history_match":True,
        "backup_generation":expected.generation,
        "audit_event_count":expected.event_count,
        "manifest_sha256":head,
        "actual_database_backup_restored_by_this_function":False,
        "real_external_anchor_independently_deployed":False,
        "trusted_real_world_signer_enrolled":False,
        "private_cloud_secret_vault_connected":False,
        "actual_paid_model_account_verified":False,
        "provider_live_call_enabled":False,
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }
