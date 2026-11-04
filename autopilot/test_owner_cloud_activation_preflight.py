"""B3d4c2d3 adversarial CloudFormation + external-client READ-ONLY preflight.

All AWS-like S3, KMS and STS responses are invented IN MEMORY. No actual
accounts/credentials/identity provider, owner approval, compliance retention,
cloud deployment or YouTube uploads can be inferred from these tests.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from datetime import datetime,timezone
import json
import re
import unittest

from autopilot.owner_cloud_activation_preflight import (
    OwnerSelectedStorageScope,ActivationBoundaryError,
    exact_bucket_name,verify_owner_selected_scope,
    inspect_owner_selected_storage_readonly,
    _expected_s3_policy,_expected_kms_policy,_json_policy,
)

NOW=datetime(2026,11,4,16,30,tzinfo=timezone.utc)
SCOPE=OwnerSelectedStorageScope(
    account_id="000000000000",
    region="us-east-1",
    deployment_suffix="synthetic8",
    writer_role_arn="arn:aws:iam::000000000000:role/flowminute-temporary-writer",
    auditor_role_arn="arn:aws:iam::000000000000:role/flowminute-temporary-auditor",
    kms_key_arn="arn:aws:kms:us-east-1:000000000000:key/00000000-0000-0000-0000-000000000000",
    compliance_retention_days=7,
    owner_approval_reference="OWNER-SYNTHETIC-ONLY-20261104",
)
TEMPLATE_PATH=Path("infra/aws/owner-approved-private-media-escrow.cfn.json")


def template():
    return json.loads(TEMPLATE_PATH.read_text(encoding="utf8"))


def resolve(value):
    """Offline CloudFormation Fn::Sub/Ref/GetAtt fixture projection only."""
    if isinstance(value,list):
        return [resolve(x) for x in value]
    if not isinstance(value,dict):
        return value
    if len(value)==1 and "Ref" in value:
        ref=value["Ref"]
        mapping={
            "WriterRoleArn":SCOPE.writer_role_arn,
            "AuditorRoleArn":SCOPE.auditor_role_arn,
            "OwnerApprovalReference":SCOPE.owner_approval_reference,
            "RetentionDays":SCOPE.compliance_retention_days,
            "DeploymentSuffix":SCOPE.deployment_suffix,
            "AWS::AccountId":SCOPE.account_id,
            "AWS::Region":SCOPE.region,
        }
        return mapping[ref]
    if len(value)==1 and "Fn::GetAtt" in value:
        resource,attribute=value["Fn::GetAtt"]
        if (resource,attribute)==("PrivateMediaBucket","Arn"):
            return "arn:aws:s3:::"+exact_bucket_name(SCOPE)
        if (resource,attribute)==("PrivateMediaKey","Arn"):
            return SCOPE.kms_key_arn
        raise AssertionError("Unexpected future cloud resource ref")
    if len(value)==1 and "Fn::Sub" in value:
        substitutions={
            "AWS::Partition":"aws",
            "AWS::AccountId":SCOPE.account_id,
            "AWS::Region":SCOPE.region,
            "DeploymentSuffix":SCOPE.deployment_suffix,
            "PrivateMediaBucket.Arn":"arn:aws:s3:::"+exact_bucket_name(SCOPE),
        }
        return re.sub(r"\$\{([^}]+)\}",
                      lambda m:substitutions[m.group(1)],value["Fn::Sub"])
    return {k:resolve(v) for k,v in value.items()}


def synthetic_services():
    """Independent fake service responses, not real AWS readbacks."""
    t=template()
    bucket=exact_bucket_name(SCOPE)
    bp=resolve(t["Resources"]["PrivateMediaBucketPolicy"]["Properties"]["PolicyDocument"])
    kp=resolve(t["Resources"]["PrivateMediaKey"]["Properties"]["KeyPolicy"])
    services={
        "sts":{"get_caller_identity":{
            "Account":SCOPE.account_id,
            "Arn":"arn:aws:sts::"+SCOPE.account_id+
                  ":assumed-role/flowminute-temporary-auditor/ci_read_only_session",
            "UserId":"fake_not_authenticated_by_a_real_identity_provider",
        }},
        "s3":{
            "get_bucket_versioning":{"Status":"Enabled"},
            "get_bucket_location":{"LocationConstraint":None},
            "get_object_lock_configuration":{"ObjectLockConfiguration":{
                "ObjectLockEnabled":"Enabled",
                "Rule":{"DefaultRetention":{
                    "Mode":"COMPLIANCE","Days":SCOPE.compliance_retention_days,
                }},
            }},
            "get_public_access_block":{"PublicAccessBlockConfiguration":{
                "BlockPublicAcls":True,"BlockPublicPolicy":True,
                "IgnorePublicAcls":True,"RestrictPublicBuckets":True,
            }},
            "get_bucket_encryption":{"ServerSideEncryptionConfiguration":{
                "Rules":[{
                    "ApplyServerSideEncryptionByDefault":{
                        "SSEAlgorithm":"aws:kms",
                        "KMSMasterKeyID":SCOPE.kms_key_arn,
                    },"BucketKeyEnabled":True,
                }],
            }},
            "get_bucket_ownership_controls":{"OwnershipControls":{"Rules":[
                {"ObjectOwnership":"BucketOwnerEnforced"},
            ]}},
            "get_bucket_policy_status":{"PolicyStatus":{"IsPublic":False}},
            "get_bucket_policy":{"Policy":json.dumps(bp,separators=(",",":"))},
            "get_bucket_tagging":{"TagSet":[
                {"Key":"FlowMinute","Value":"unapproved-media-escrow"},
                {"Key":"ReviewStatus","Value":"no-authorized-publish"},
                {"Key":"RetentionReference","Value":SCOPE.owner_approval_reference},
            ]},
        },
        "kms":{
            "describe_key":{"KeyMetadata":{
                "Arn":SCOPE.kms_key_arn,
                "AWSAccountId":SCOPE.account_id,
                "KeyManager":"CUSTOMER",
                "KeyState":"Enabled",
                "Enabled":True,
                "KeyUsage":"ENCRYPT_DECRYPT",
                "KeySpec":"SYMMETRIC_DEFAULT",
            }},
            "get_key_rotation_status":{"KeyRotationEnabled":True},
            "get_key_policy":{"Policy":json.dumps(kp,separators=(",",":"))},
        },
    }
    return services


class FakeReadOnlyClient:
    def __init__(self,replies):
        self.replies=replies
        self.calls=[]
    def __getattr__(self,name):
        if name not in self.replies:
            raise AssertionError("Unexpected AWS mutation/outbound request "+name)
        def only_read(**kwargs):
            self.calls.append((name,kwargs))
            return deepcopy(self.replies[name])
        return only_read


def check(replies=None,scope=SCOPE):
    s=deepcopy(replies if replies is not None else synthetic_services())
    clients={service:FakeReadOnlyClient(s[service]) for service in ("sts","s3","kms")}
    result=inspect_owner_selected_storage_readonly(
        scope=scope,now=NOW,**clients,
    )
    return result,clients


class OwnerCloudStackTemplateTests(unittest.TestCase):
    def test_requires_explicit_real_owner_inputs_no_defaults_or_secrets(self):
        t=template()
        self.assertEqual(t["AWSTemplateFormatVersion"],"2010-09-09")
        self.assertEqual(set(t["Parameters"]),{
            "DeploymentSuffix","WriterRoleArn","AuditorRoleArn",
            "RetentionDays","OwnerApprovalReference",
        })
        self.assertFalse(any("Default" in x for x in t["Parameters"].values()))
        self.assertEqual(t["Parameters"]["RetentionDays"]["MinValue"],1)
        self.assertEqual(t["Parameters"]["RetentionDays"]["MaxValue"],30)
        self.assertEqual(set(t["Resources"]),{
            "PrivateMediaKey","PrivateMediaBucket","PrivateMediaBucketPolicy",
        })
        self.assertFalse(any(x["Type"] in (
            "AWS::IAM::User","AWS::IAM::AccessKey",
            "AWS::Lambda::Function","AWS::Events::Rule",
            "AWS::CloudFormation::CustomResource",
        ) for x in t["Resources"].values()))
        for component in ("PrivateMediaKey","PrivateMediaBucket"):
            self.assertEqual(t["Resources"][component]["DeletionPolicy"],"Retain")
            self.assertEqual(t["Resources"][component]["UpdateReplacePolicy"],"Retain")

    def test_exact_customer_kms_seven_day_default_lock_private_and_versioning(self):
        t=template()
        b=resolve(t["Resources"]["PrivateMediaBucket"]["Properties"])
        self.assertEqual(b["VersioningConfiguration"],{"Status":"Enabled"})
        self.assertIs(b["ObjectLockEnabled"],True)
        self.assertEqual(b["ObjectLockConfiguration"]["ObjectLockEnabled"],"Enabled")
        self.assertEqual(b["ObjectLockConfiguration"]["Rule"]["DefaultRetention"],{
            "Mode":"COMPLIANCE","Days":7,
        })
        self.assertEqual(b["PublicAccessBlockConfiguration"],{
            "BlockPublicAcls":True,"BlockPublicPolicy":True,
            "IgnorePublicAcls":True,"RestrictPublicBuckets":True,
        })
        self.assertEqual(b["OwnershipControls"],{"Rules":[
            {"ObjectOwnership":"BucketOwnerEnforced"},
        ]})
        self.assertEqual(b["BucketEncryption"]["ServerSideEncryptionConfiguration"],[
            {"ServerSideEncryptionByDefault":{
                "SSEAlgorithm":"aws:kms",
                "KMSMasterKeyID":SCOPE.kms_key_arn,
            },"BucketKeyEnabled":True},
        ])
        self.assertEqual(b["BucketName"],exact_bucket_name(SCOPE))
        self.assertEqual(t["Resources"]["PrivateMediaKey"]["Properties"]["EnableKeyRotation"],True)
        self.assertEqual(t["Resources"]["PrivateMediaKey"]["Properties"]["PendingWindowInDays"],30)

    def test_exact_least_privilege_allow_and_deny_policy_shape(self):
        t=template()
        _expected_s3_policy(
            SCOPE,resolve(t["Resources"]["PrivateMediaBucketPolicy"]["Properties"]["PolicyDocument"])
        )
        _expected_kms_policy(
            SCOPE,resolve(t["Resources"]["PrivateMediaKey"]["Properties"]["KeyPolicy"])
        )
        ids=t["Rules"]["DifferentStorageRoles"]["Assertions"]
        self.assertEqual(len(ids),1)
        self.assertIn("Fn::Not",ids[0]["Assert"])

    def test_account_arn_region_role_trust_and_retention_invalids_fail_closed(self):
        changes=[
            {"account_id":"12345"},
            {"account_id":"000000000001"},
            {"region":"bad"},
            {"deployment_suffix":"UPPER"},
            {"deployment_suffix":"x"},
            {"writer_role_arn":SCOPE.auditor_role_arn},
            {"auditor_role_arn":"arn:aws:iam::999999999999:role/outside"},
            {"kms_key_arn":"arn:aws:kms:eu-west-1:000000000000:key/00000000-0000-0000-0000-000000000000"},
            {"kms_key_arn":"arn:aws:kms:us-east-1:123456789012:key/00000000-0000-0000-0000-000000000000"},
            {"compliance_retention_days":0},
            {"compliance_retention_days":31},
            {"compliance_retention_days":True},
            {"owner_approval_reference":"NOT_A_REAL_APPROVAL"},
        ]
        for patch in changes:
            with self.subTest(patch=patch),self.assertRaises(ActivationBoundaryError):
                verify_owner_selected_scope(replace(SCOPE,**patch))
        verify_owner_selected_scope(SCOPE)


class OwnerSelectedReadOnlyServiceTests(unittest.TestCase):
    def test_all_independently_fetched_fake_controls_match_but_no_real_approval(self):
        report,clients=check()
        self.assertEqual(report["status"],
                         "READ_ONLY_OWNER_CONFIGURED_STORAGE_TOPOLOGY_MATCH_NO_REAL_OWNER_APPROVAL")
        self.assertEqual(report["bucket"],exact_bucket_name(SCOPE))
        self.assertTrue(report["all_requested_s3_and_kms_configuration_readbacks_structurally_matched"])
        for flag in (
            "real_external_aws_signature_and_issuer_verified_by_this_module",
            "real_owner_identity_and_cost_approval_established",
            "real_media_bytes_persisted_and_recovered",
            "real_reviewers_factual_rights_and_full_watch_enrolled",
            "production_cloudtrail_and_cross_region_restore_verified",
            "youtube_upload_enabled","release_authorized",
        ):
            self.assertFalse(report[flag])
        self.assertEqual(len(clients["sts"].calls),1)
        self.assertEqual(len(clients["s3"].calls),9)
        self.assertEqual(len(clients["kms"].calls),3)
        self.assertEqual({x[0] for x in clients["s3"].calls},{
            "get_bucket_versioning","get_bucket_location",
            "get_object_lock_configuration","get_public_access_block",
            "get_bucket_encryption","get_bucket_ownership_controls",
            "get_bucket_policy_status","get_bucket_policy","get_bucket_tagging",
        })
        self.assertTrue(all(call[1]=={"Bucket":exact_bucket_name(SCOPE)}
                            for call in clients["s3"].calls))

    def test_wrong_sts_account_or_role_cannot_pass_even_if_bucket_and_kms_match(self):
        for key,value in (
            ("Account","111111111111"),
            ("Arn","arn:aws:iam::000000000000:root"),
            ("Arn","arn:aws:sts::000000000000:assumed-role/flowminute-temporary-writer/ci"),
            ("Arn","arn:aws:sts::000000000000:assumed-role/flowminute-temporary-auditor/"),
        ):
            replies=synthetic_services()
            replies["sts"]["get_caller_identity"][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ActivationBoundaryError):
                check(replies)

    def test_forged_s3_versioning_objectlock_retention_and_region_rejected(self):
        mutations=[
            ("get_bucket_versioning",["Status"],"Suspended"),
            ("get_object_lock_configuration",
             ["ObjectLockConfiguration","Rule","DefaultRetention","Mode"],"GOVERNANCE"),
            ("get_object_lock_configuration",
             ["ObjectLockConfiguration","Rule","DefaultRetention","Days"],6),
            ("get_object_lock_configuration",
             ["ObjectLockConfiguration","ObjectLockEnabled"],"Disabled"),
            ("get_bucket_location",["LocationConstraint"],"eu-west-1"),
        ]
        for api,path,value in mutations:
            reply=synthetic_services()
            current=reply["s3"][api]
            for part in path[:-1]:
                current=current[part]
            current[path[-1]]=value
            with self.subTest(api=api,path=path),self.assertRaises(ActivationBoundaryError):
                check(reply)

    def test_any_public_access_block_acl_mode_or_bucket_status_change_rejected(self):
        for key in (
            "BlockPublicAcls","BlockPublicPolicy","IgnorePublicAcls","RestrictPublicBuckets",
        ):
            s=synthetic_services()
            s["s3"]["get_public_access_block"]["PublicAccessBlockConfiguration"][key]=False
            with self.subTest(field=key),self.assertRaises(ActivationBoundaryError):
                check(s)
        s=synthetic_services()
        s["s3"]["get_bucket_ownership_controls"]["OwnershipControls"]["Rules"]=[
            {"ObjectOwnership":"ObjectWriter"},
        ]
        with self.assertRaises(ActivationBoundaryError):
            check(s)
        s=synthetic_services()
        s["s3"]["get_bucket_policy_status"]["PolicyStatus"]["IsPublic"]=True
        with self.assertRaises(ActivationBoundaryError):
            check(s)

    def test_changed_kms_encryption_key_mode_rotation_or_account_denied(self):
        edits=[
            ("s3","get_bucket_encryption",
             ["ServerSideEncryptionConfiguration","Rules",0,"ApplyServerSideEncryptionByDefault","SSEAlgorithm"],
             "AES256"),
            ("s3","get_bucket_encryption",
             ["ServerSideEncryptionConfiguration","Rules",0,"BucketKeyEnabled"],False),
            ("kms","describe_key",["KeyMetadata","KeyManager"],"AWS"),
            ("kms","describe_key",["KeyMetadata","Enabled"],False),
            ("kms","describe_key",["KeyMetadata","AWSAccountId"],"111111111111"),
            ("kms","get_key_rotation_status",["KeyRotationEnabled"],False),
        ]
        for service,api,path,value in edits:
            s=synthetic_services()
            target=s[service][api]
            for p in path[:-1]:
                target=target[p]
            target[path[-1]]=value
            with self.subTest(api=api,path=path),self.assertRaises(ActivationBoundaryError):
                check(s)

    def test_removed_tls_deny_or_escalated_reviewer_or_public_upload_denied(self):
        cases=[
            ("ExplicitDenyInsecureTransport","Condition",{"Bool":{"aws:SecureTransport":"true"}}),
            ("AuditorOnlyReadSpecificVersions","Action",["s3:GetObjectVersion","s3:PutObject"]),
            ("WriterOnlyFullVersionedUnapprovedMediaPrefix","Resource","*"),
            ("ExplicitDenyWrongCustomerKmsKey","Condition",{"StringNotEqualsIfExists":{
                "s3:x-amz-server-side-encryption-aws-kms-key-id":"arn:aws:kms:us-east-1:000000000000:key/other",
            }}),
            ("ExplicitDenyNonComplianceLockUpload","Condition",{"StringNotEqualsIfExists":{
                "s3:object-lock-mode":"GOVERNANCE",
            }}),
        ]
        for sid,key,value in cases:
            s=synthetic_services()
            policy=json.loads(s["s3"]["get_bucket_policy"]["Policy"])
            next(x for x in policy["Statement"] if x["Sid"]==sid)[key]=value
            s["s3"]["get_bucket_policy"]["Policy"]=json.dumps(policy)
            with self.subTest(sid=sid,key=key),self.assertRaises(ActivationBoundaryError):
                check(s)
        s=synthetic_services()
        policy=json.loads(s["s3"]["get_bucket_policy"]["Policy"])
        policy["Statement"].append({
            "Sid":"ForgedPublicRead","Effect":"Allow","Principal":"*",
            "Action":"s3:GetObject","Resource":"*",
        })
        s["s3"]["get_bucket_policy"]["Policy"]=json.dumps(policy)
        with self.assertRaises(ActivationBoundaryError):
            check(s)

    def test_kms_writer_decrypt_and_reviewer_only_decrypt_no_admin_grant(self):
        for sid,field,value in (
            ("IndependentAuditorOnlyDecryptForS3","Action",["kms:*"]),
            ("MediaWriterKmsForS3Only","Action",["kms:GenerateDataKey","kms:ScheduleKeyDeletion"]),
            ("IndependentAuditorOnlyDecryptForS3","Condition",{}),
            ("OwnerAccountAdministratorsRetainKeyControl","Principal",{"AWS":"*"}),
        ):
            s=synthetic_services()
            policy=json.loads(s["kms"]["get_key_policy"]["Policy"])
            next(x for x in policy["Statement"] if x["Sid"]==sid)[field]=value
            s["kms"]["get_key_policy"]["Policy"]=json.dumps(policy)
            with self.subTest(sid=sid,field=field),self.assertRaises(ActivationBoundaryError):
                check(s)

    def test_owner_approval_ticket_shape_is_not_cryptographic_owner_consent(self):
        report,_=check()
        self.assertTrue(report["owner_reference_format_matched_not_consent_verified"].startswith("OWNER-"))
        self.assertFalse(report["real_owner_identity_and_cost_approval_established"])
        changed=synthetic_services()
        changed["s3"]["get_bucket_tagging"]["TagSet"][-1]["Value"]="OWNER-A-NOTHER-TICKET"
        with self.assertRaises(ActivationBoundaryError):
            check(changed)

    def test_duplicate_bucket_iam_policy_json_fields_rejected(self):
        s=synthetic_services()
        s["s3"]["get_bucket_policy"]["Policy"]=(
            '{"Version":"2012-10-17","Version":"2012-10-17",'
            '"Statement":[]}'
        )
        with self.assertRaises(ActivationBoundaryError):
            check(s)
        with self.assertRaises(ActivationBoundaryError):
            _json_policy('{"Version":"2012-10-17","Statement":[],"extra":NaN}')

    def test_external_service_unavailable_fails_without_any_attempt_to_create(self):
        s=synthetic_services()
        del s["kms"]["describe_key"]
        with self.assertRaises(ActivationBoundaryError):
            check(s)
        import autopilot.owner_cloud_activation_preflight as m
        for name in (
            "create_cloudformation_stack","create_bucket","put_object",
            "create_aws_client","grant_real_oauth","sign_real_owner",
            "aws_login","upload_to_youtube",
        ):
            self.assertFalse(hasattr(m,name))

    def test_all_real_human_and_publisher_flags_always_false(self):
        report,_=check()
        self.assertFalse(report["release_authorized"])
        self.assertFalse(report["youtube_upload_enabled"])
        self.assertFalse(report["real_reviewers_factual_rights_and_full_watch_enrolled"])
        self.assertFalse(report["real_media_bytes_persisted_and_recovered"])
        self.assertFalse(report["real_external_aws_signature_and_issuer_verified_by_this_module"])


if __name__=="__main__":
    unittest.main()
