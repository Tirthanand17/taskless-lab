"""B3d4c2d3: read-only owner-activation topology evidence, never deployment.

This can INSPECT an owner-supplied S3/KMS/STS client against an externally
selected AWS account, role, bucket and KMS key. This does not create clients,
obtain AWS tokens, store credentials, provision cloud, sign owner intent, grant
copyright rights or authorize publishing. On public GitHub CI ALL clients are
pure in-memory synthetic fixtures, never actual AWS credentials.

Trust: successfully matching a *caller-provided* client is NOT an independent
owner, provider billing, legal retention or real human review attestation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Mapping

from autopilot.primary_sourced_storyboards import canonical

STATUS = "READ_ONLY_OWNER_CONFIGURED_STORAGE_TOPOLOGY_MATCH_NO_REAL_OWNER_APPROVAL"
ACCOUNT = re.compile(r"[0-9]{12}\Z")
SUFFIX = re.compile(r"[a-z0-9]{4,12}\Z")
REGION = re.compile(r"(?:us|eu|ap|sa|ca|me|af|il)-[a-z]+-[1-9][0-9]?\Z")
ROLE = re.compile(r"arn:aws:iam::([0-9]{12}):role/([A-Za-z0-9+=,.@_/-]{1,128})\Z")
KMS = re.compile(r"arn:aws:kms:([a-z0-9-]+):([0-9]{12}):key/([0-9a-fA-F-]{36})\Z")
REFERENCE = re.compile(r"OWNER-[A-Z0-9-]{8,64}\Z")
PREFIX = "flowminute/unapproved-media-v1"
MIN_RETENTION = 1
MAX_RETENTION = 30

S3_BUCKET_SIDS = frozenset({
    "ExplicitDenyInsecureTransport",
    "ExplicitDenyNonKmsUploadHeader",
    "ExplicitDenyWrongCustomerKmsKey",
    "ExplicitDenyNonComplianceLockUpload",
    "WriterOnlyFullVersionedUnapprovedMediaPrefix",
    "AuditorOnlyReadSpecificVersions",
    "AuditorOnlyReadBucketConfiguration",
    "ProhibitRuntimeIdentityDeletesOrRetentionBypass",
})
S3_WRITER_ACTIONS = frozenset({
    "s3:PutObject","s3:PutObjectRetention","s3:GetObjectVersion","s3:GetObjectRetention",
})
S3_AUDITOR_ACTIONS = frozenset({"s3:GetObjectVersion","s3:GetObjectRetention"})
S3_AUDITOR_BUCKET_READ_ACTIONS = frozenset({
    "s3:GetBucketVersioning","s3:GetBucketLocation",
    "s3:GetBucketObjectLockConfiguration","s3:GetBucketPublicAccessBlock",
    "s3:GetEncryptionConfiguration","s3:GetBucketOwnershipControls",
    "s3:GetBucketPolicyStatus","s3:GetBucketPolicy","s3:GetBucketTagging",
})
KMS_SIDS = frozenset({
    "OwnerAccountAdministratorsRetainKeyControl",
    "MediaWriterKmsForS3Only",
    "IndependentAuditorOnlyDecryptForS3",
    "IndependentAuditorReadOnlyKmsConfigurationInspection",
})


class ActivationBoundaryError(ValueError):
    """External control configuration mismatch; fail closed, do not activate."""


@dataclass(frozen=True)
class OwnerSelectedStorageScope:
    """Proposed input only; even a correct format is NOT genuine owner consent."""
    account_id: str
    region: str
    deployment_suffix: str
    writer_role_arn: str
    auditor_role_arn: str
    kms_key_arn: str
    compliance_retention_days: int
    owner_approval_reference: str


def exact_bucket_name(scope:OwnerSelectedStorageScope)->str:
    verify_owner_selected_scope(scope)
    return f"flowminute-private-{scope.account_id}-{scope.region}-{scope.deployment_suffix}"


def verify_owner_selected_scope(scope:OwnerSelectedStorageScope)->None:
    if (not isinstance(scope,OwnerSelectedStorageScope)
            or not isinstance(scope.account_id,str) or not ACCOUNT.fullmatch(scope.account_id)
            or not isinstance(scope.region,str) or not REGION.fullmatch(scope.region)
            or not isinstance(scope.deployment_suffix,str)
            or not SUFFIX.fullmatch(scope.deployment_suffix)
            or type(scope.compliance_retention_days) is not int
            or not MIN_RETENTION<=scope.compliance_retention_days<=MAX_RETENTION
            or not isinstance(scope.owner_approval_reference,str)
            or not REFERENCE.fullmatch(scope.owner_approval_reference)):
        raise ActivationBoundaryError("Missing independently owner-selected account/region/retention terms")
    writer=ROLE.fullmatch(scope.writer_role_arn) if isinstance(scope.writer_role_arn,str) else None
    auditor=ROLE.fullmatch(scope.auditor_role_arn) if isinstance(scope.auditor_role_arn,str) else None
    kms=KMS.fullmatch(scope.kms_key_arn) if isinstance(scope.kms_key_arn,str) else None
    if (not writer or not auditor or not kms
            or writer.group(1)!=scope.account_id
            or auditor.group(1)!=scope.account_id
            or kms.group(1)!=scope.region or kms.group(2)!=scope.account_id
            or scope.writer_role_arn==scope.auditor_role_arn
            or "/" in writer.group(2) or "/" in auditor.group(2)
            or writer.group(2)==auditor.group(2)):
        raise ActivationBoundaryError("Owner writer/auditor/KMS must be distinct scoped same-account roles")


def _json_policy(raw:object)->dict:
    if not isinstance(raw,str) or len(raw)>40000:
        raise ActivationBoundaryError("Missing authenticated service policy readback")
    def unique(items):
        seen={}
        for k,v in items:
            if k in seen:
                raise ActivationBoundaryError("Duplicate IAM policy JSON keys")
            seen[k]=v
        return seen
    try:
        policy=json.loads(raw,object_pairs_hook=unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(
                              ActivationBoundaryError("Nonfinite JSON policy")))
    except (TypeError,ValueError) as exc:
        raise ActivationBoundaryError("Invalid S3/KMS service policy JSON") from exc
    if not isinstance(policy,dict) or policy.get("Version")!="2012-10-17" or not isinstance(policy.get("Statement"),list):
        raise ActivationBoundaryError("Untrusted external policy version")
    return policy


def _statements(policy:dict,expected:frozenset[str])->dict:
    rows=policy["Statement"]
    if (len(rows)!=len(expected) or any(not isinstance(x,dict) or x.get("Sid") not in expected
                                        for x in rows)):
        raise ActivationBoundaryError("Unreviewed additional bucket/KMS grants")
    by_id={x["Sid"]:x for x in rows}
    if len(by_id)!=len(rows) or set(by_id)!=expected:
        raise ActivationBoundaryError("Missing/duplicate expected resource policies")
    return by_id


def _set_actions(value:object)->frozenset:
    return frozenset(value if isinstance(value,list) else [value])


def _expected_s3_policy(scope:OwnerSelectedStorageScope,body:dict)->None:
    records=_statements(body,S3_BUCKET_SIDS)
    bucket=exact_bucket_name(scope)
    arn=f"arn:aws:s3:::{bucket}"
    obj=arn+"/"+PREFIX+"/*"
    all_arn=frozenset((arn,arn+"/*"))
    deny=records["ExplicitDenyInsecureTransport"]
    if (deny.get("Effect")!="Deny" or deny.get("Principal")!="*"
            or deny.get("Action")!="s3:*"
            or _set_actions(deny.get("Resource"))!=all_arn
            or deny.get("Condition")!={"Bool":{"aws:SecureTransport":"false"}}):
        raise ActivationBoundaryError("Missing always-on TLS-only bucket denial")
    conditions=(
        ("ExplicitDenyNonKmsUploadHeader",
         {"StringNotEqualsIfExists":{"s3:x-amz-server-side-encryption":"aws:kms"}}),
        ("ExplicitDenyWrongCustomerKmsKey",
         {"StringNotEqualsIfExists":{"s3:x-amz-server-side-encryption-aws-kms-key-id":scope.kms_key_arn}}),
        ("ExplicitDenyNonComplianceLockUpload",
         {"StringNotEqualsIfExists":{"s3:object-lock-mode":"COMPLIANCE"}}),
    )
    for sid,c in conditions:
        st=records[sid]
        if (st.get("Effect")!="Deny" or st.get("Principal")!="*"
                or _set_actions(st.get("Action"))!=frozenset({"s3:PutObject"})
                or st.get("Resource")!=obj or st.get("Condition")!=c):
            raise ActivationBoundaryError("Missing exact SSE-KMS/compliance-object-lock upload restrictions")
    for sid,role,actions in (
        ("WriterOnlyFullVersionedUnapprovedMediaPrefix",scope.writer_role_arn,S3_WRITER_ACTIONS),
        ("AuditorOnlyReadSpecificVersions",scope.auditor_role_arn,S3_AUDITOR_ACTIONS),
    ):
        st=records[sid]
        if (st.get("Effect")!="Allow" or st.get("Principal")!={"AWS":role}
                or _set_actions(st.get("Action"))!=actions or st.get("Resource")!=obj
                or st.get("Condition") not in (None,{})):
            raise ActivationBoundaryError("Unauthorized writer/reviewer role or too broad S3 permission")
    # The independent auditor must really be able to READ exactly the nine
    # bucket-config APIs invoked above. Granting only GetObjectVersion would
    # make an otherwise valid owner-operated deployment impossible to audit.
    bucket_read=records["AuditorOnlyReadBucketConfiguration"]
    if (bucket_read.get("Effect")!="Allow"
            or bucket_read.get("Principal")!={"AWS":scope.auditor_role_arn}
            or _set_actions(bucket_read.get("Action"))!=S3_AUDITOR_BUCKET_READ_ACTIONS
            or bucket_read.get("Resource")!=arn
            or bucket_read.get("Condition") not in (None,{})):
        raise ActivationBoundaryError("Auditor may only inspect nine exact S3 bucket settings; no writer/admin actions")
    deny=records["ProhibitRuntimeIdentityDeletesOrRetentionBypass"]
    if (deny.get("Effect")!="Deny"
            or set(deny.get("Principal",{}).get("AWS",[]))!={
                scope.writer_role_arn,scope.auditor_role_arn
            } or _set_actions(deny.get("Resource"))!=all_arn
            or _set_actions(deny.get("Action"))!=frozenset({
                "s3:DeleteObject","s3:DeleteObjectVersion",
                "s3:BypassGovernanceRetention","s3:PutBucketObjectLockConfiguration",
                "s3:PutBucketVersioning"
            })):
        raise ActivationBoundaryError("Runtime principals could delete versions or bypass lock")


def _expected_kms_policy(scope:OwnerSelectedStorageScope,policy:dict)->None:
    rows=_statements(policy,KMS_SIDS)
    root=rows["OwnerAccountAdministratorsRetainKeyControl"]
    if (root.get("Effect")!="Allow"
            or root.get("Principal")!={"AWS":f"arn:aws:iam::{scope.account_id}:root"}
            or root.get("Action")!="kms:*" or root.get("Resource")!="*"):
        raise ActivationBoundaryError("Independent owner account cannot safely administer key")
    for sid,role,actions in (
        ("MediaWriterKmsForS3Only",scope.writer_role_arn,{
            "kms:GenerateDataKey","kms:Encrypt","kms:Decrypt","kms:DescribeKey",
        }),
        ("IndependentAuditorOnlyDecryptForS3",scope.auditor_role_arn,{
            "kms:Decrypt",
        }),
    ):
        r=rows[sid]
        if (r.get("Effect")!="Allow" or r.get("Principal")!={"AWS":role}
                or _set_actions(r.get("Action"))!=frozenset(actions)
                or r.get("Resource")!="*"
                or r.get("Condition")!={"StringEquals":{
                    "kms:ViaService":f"s3.{scope.region}.amazonaws.com",
                    "kms:CallerAccount":scope.account_id
                }}):
            raise ActivationBoundaryError("Incorrect owner-selected independent KMS crypto permissions")
    inspector=rows["IndependentAuditorReadOnlyKmsConfigurationInspection"]
    if (inspector.get("Effect")!="Allow"
            or inspector.get("Principal")!={"AWS":scope.auditor_role_arn}
            or _set_actions(inspector.get("Action"))!=frozenset({
                "kms:DescribeKey","kms:GetKeyRotationStatus","kms:GetKeyPolicy",
            })
            or inspector.get("Resource")!="*"
            or inspector.get("Condition")!={"StringEquals":{
                "kms:CallerAccount":scope.account_id,
            }}):
        raise ActivationBoundaryError("Auditor must have read-only direct KMS policy/rotation inspection without ViaService, no modification privileges")


def inspect_owner_selected_storage_readonly(*,sts,s3,kms,
                                             scope:OwnerSelectedStorageScope,
                                             now:datetime)->dict:
    """Only reads existing controls; NEVER deploys, bills, uploads or signs.

    Real clients must be supplied by an externally owner-authorized protected
    runtime. On CI tests fake in-memory client responses, so result is only a
    structural match; it can NEVER authenticate actual owner or rights.
    """
    verify_owner_selected_scope(scope)
    if not isinstance(now,datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ActivationBoundaryError("External readback needs independent aware clock")
    at=now.astimezone(timezone.utc)
    bucket=exact_bucket_name(scope)
    role_name=scope.auditor_role_arn.rsplit("/",1)[-1]
    try:
        identity=sts.get_caller_identity()
        version=s3.get_bucket_versioning(Bucket=bucket)
        location=s3.get_bucket_location(Bucket=bucket)
        locked=s3.get_object_lock_configuration(Bucket=bucket)
        public=s3.get_public_access_block(Bucket=bucket)
        encryption=s3.get_bucket_encryption(Bucket=bucket)
        owners=s3.get_bucket_ownership_controls(Bucket=bucket)
        policy_status=s3.get_bucket_policy_status(Bucket=bucket)
        bucket_policy=s3.get_bucket_policy(Bucket=bucket)
        tags=s3.get_bucket_tagging(Bucket=bucket)
        key=kms.describe_key(KeyId=scope.kms_key_arn)
        rotation=kms.get_key_rotation_status(KeyId=scope.kms_key_arn)
        key_policy=kms.get_key_policy(KeyId=scope.kms_key_arn,PolicyName="default")
    except Exception as exc:
        raise ActivationBoundaryError("External S3/KMS/STS topology cannot be read without exact owner grants") from exc

    arn=identity.get("Arn","") if isinstance(identity,dict) else ""
    assumed_prefix=f"arn:aws:sts::{scope.account_id}:assumed-role/{role_name}/"
    if (identity.get("Account")!=scope.account_id
            or not isinstance(arn,str) or not arn.startswith(assumed_prefix)
            or len(arn)<=len(assumed_prefix) or "/" in arn[len(assumed_prefix):]
            or version.get("Status")!="Enabled"
            or (location.get("LocationConstraint") or "us-east-1")!=scope.region):
        raise ActivationBoundaryError("Not the owner-selected standalone auditor session or versioned region")
    config=locked.get("ObjectLockConfiguration",{})
    retention=config.get("Rule",{}).get("DefaultRetention",{})
    if (config.get("ObjectLockEnabled")!="Enabled"
            or retention.get("Mode")!="COMPLIANCE"
            or type(retention.get("Days")) is not int
            or retention["Days"]!=scope.compliance_retention_days):
        raise ActivationBoundaryError("S3 ObjectLock COMPLIANCE must match owner-approved retention")
    public_bits=public.get("PublicAccessBlockConfiguration",{})
    if any(public_bits.get(k) is not True for k in (
        "BlockPublicAcls","BlockPublicPolicy","IgnorePublicAcls","RestrictPublicBuckets",
    )):
        raise ActivationBoundaryError("S3 public block/ACL protections not proven")
    if owners.get("OwnershipControls",{}).get("Rules")!=[
        {"ObjectOwnership":"BucketOwnerEnforced"}
    ]:
        raise ActivationBoundaryError("Unexpected public ACL ownership mode")
    enc=encryption.get("ServerSideEncryptionConfiguration",{}).get("Rules",[])
    if (len(enc)!=1 or enc[0].get("ApplyServerSideEncryptionByDefault")!={
            "SSEAlgorithm":"aws:kms","KMSMasterKeyID":scope.kms_key_arn,
        } or enc[0].get("BucketKeyEnabled") is not True):
        raise ActivationBoundaryError("Private bucket SSE-KMS not pinned to owner customer key")
    if policy_status.get("PolicyStatus",{}).get("IsPublic") is not False:
        raise ActivationBoundaryError("S3 reports bucket access may be public")
    raw_tags=tags.get("TagSet",[])
    tag_map={x.get("Key"):x.get("Value") for x in raw_tags}
    if (len(tag_map)!=len(raw_tags)
            or tag_map.get("FlowMinute")!="unapproved-media-escrow"
            or tag_map.get("ReviewStatus")!="no-authorized-publish"
            or tag_map.get("RetentionReference")!=scope.owner_approval_reference):
        raise ActivationBoundaryError("Cloud resource tag and owner change-ticket shape mismatch")
    _expected_s3_policy(scope,_json_policy(bucket_policy.get("Policy")))

    key_m=key.get("KeyMetadata",{})
    if (key_m.get("Arn")!=scope.kms_key_arn
            or key_m.get("AWSAccountId")!=scope.account_id
            or key_m.get("KeyManager")!="CUSTOMER"
            or key_m.get("KeyState")!="Enabled"
            or key_m.get("Enabled") is not True
            or key_m.get("KeyUsage")!="ENCRYPT_DECRYPT"
            or key_m.get("KeySpec")!="SYMMETRIC_DEFAULT"
            or rotation.get("KeyRotationEnabled") is not True):
        raise ActivationBoundaryError("S3 KMS key was not independently observed enabled and rotating")
    _expected_kms_policy(scope,_json_policy(key_policy.get("Policy")))
    facts={
        "schema_version":1,
        "status":STATUS,
        "observed_at_utc":at.isoformat(),
        "observed_sts_account_id":scope.account_id,
        "observed_auditor_principal_arn":arn,
        "bucket":bucket,
        "region":scope.region,
        "customer_kms_key_arn":scope.kms_key_arn,
        "owner_selected_compliance_days":scope.compliance_retention_days,
        "separate_owner_selected_writer_role_arn":scope.writer_role_arn,
        "separate_owner_selected_auditor_role_arn":scope.auditor_role_arn,
        "owner_reference_format_matched_not_consent_verified":scope.owner_approval_reference,
        "all_requested_s3_and_kms_configuration_readbacks_structurally_matched":True,
        "real_external_aws_signature_and_issuer_verified_by_this_module":False,
        "real_owner_identity_and_cost_approval_established":False,
        "real_media_bytes_persisted_and_recovered":False,
        "real_reviewers_factual_rights_and_full_watch_enrolled":False,
        "production_cloudtrail_and_cross_region_restore_verified":False,
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }
    return {**facts,"no_publish_topology_fingerprint_sha256":
            sha256(canonical(facts)).hexdigest()}
