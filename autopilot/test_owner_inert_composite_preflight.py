"""B4c6 adversarial fake STS/IAM/VPC/ECR cross-service preflight tests.

All actors, keys, accounts, routes and ECR images are disposable inventions.
No real owner credential, paid AWS account or YouTube service is connected.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import unittest

from autopilot.owner_inert_composite_preflight import (
    InertOwnerCompositeScope,
    CompositeOwnerPreflightRefused,
    inspect_inert_owner_runtime,
)
from autopilot.owner_inert_iam_preflight import (
    InertIamScope, EXECUTION_POLICY_NAME,
    expected_trust, expected_execution_policy,
)
from autopilot.test_owner_private_network_image_preflight import (
    NOW, scope as fake_network_scope, signed_context,
    FakeEC2, FakeECR,
)

NETWORK=fake_network_scope()
IAM=InertIamScope(
    aws_account_id=NETWORK.account_id, aws_region=NETWORK.region,
    execution_role_name="InertExecRole",task_role_name="InertTaskRole",
    ecr_repository_name=NETWORK.ecr_repository,
    existing_log_group_name="/flowminute/owner-private/synthetic-guard",
    owner_change_reference="OWNER-SYNTHETIC-CHANGE-001",
)
SCOPE=InertOwnerCompositeScope(
    iam_scope=IAM, network_scope=NETWORK, inspector_role_name="OnlyInspector"
)
TEMPLATE=Path("infra/aws/owner-readonly-fargate-taskdef.cfn.json").read_text()


class FakeSTS:
    def __init__(self):
        self.calls=[]
        self.identity={
            "Account":IAM.aws_account_id,
            "Arn":f"arn:aws:sts::{IAM.aws_account_id}:"
                  "assumed-role/OnlyInspector/synthetic-ci",
        }
        self.leak=False
    def get_caller_identity(self):
        self.calls.append("get_caller_identity")
        if self.leak:
            raise RuntimeError("FAKE_SECRET_SHOULD_NEVER_APPEAR")
        return deepcopy(self.identity)


class FakeIAM:
    def __init__(self):
        self.calls=[]
        self.roles={}
        for name in (IAM.execution_role_name,IAM.task_role_name):
            self.roles[name]={
                "RoleName":name,"Arn":f"arn:aws:iam::{IAM.aws_account_id}:role/{name}",
                "Path":"/","AssumeRolePolicyDocument":expected_trust(IAM),
            }
        self.attached={name:[] for name in self.roles}
        self.inline={IAM.execution_role_name:[EXECUTION_POLICY_NAME],
                     IAM.task_role_name:[]}
        self.document=expected_execution_policy(IAM)
        self.truncated=False
    def get_role(self,*,RoleName):
        self.calls.append("get_role")
        return {"Role":deepcopy(self.roles[RoleName])}
    def list_attached_role_policies(self,*,RoleName):
        self.calls.append("list_attached_role_policies")
        return {"AttachedPolicies":deepcopy(self.attached[RoleName]),
                "IsTruncated":self.truncated}
    def list_role_policies(self,*,RoleName):
        self.calls.append("list_role_policies")
        return {"PolicyNames":deepcopy(self.inline[RoleName]),
                "IsTruncated":self.truncated}
    def get_role_policy(self,*,RoleName,PolicyName):
        self.calls.append("get_role_policy")
        return {"RoleName":RoleName,"PolicyName":PolicyName,
                "PolicyDocument":deepcopy(self.document)}


class B4c6CompositeTests(unittest.TestCase):
    def setUp(self):
        self.sts=FakeSTS()
        self.iam=FakeIAM()
        self.ec2=FakeEC2()
        self.ecr=FakeECR()
        _,self.signed,self.signature,self.pub,self.fingerprint,_=signed_context(NETWORK)

    def run_gate(self,scope=SCOPE,template=TEMPLATE):
        return inspect_inert_owner_runtime(
            scope=scope,sts=self.sts,iam=self.iam,ec2=self.ec2,ecr=self.ecr,
            manual_task_template_json=template,signed_image_json=self.signed,
            owner_signature_b64=self.signature,owner_public_key_b64=self.pub,
            owner_public_key_sha256=self.fingerprint,at=NOW,
        )

    def denied(self,scope=SCOPE,template=TEMPLATE):
        with self.assertRaises(CompositeOwnerPreflightRefused):
            self.run_gate(scope,template)

    def test_full_all_readonly_boundaries_pass_injected_synthetic_fixtures(self):
        result=self.run_gate()
        self.assertTrue(result["injected_iam_inert_role_policy_structure_verified"])
        self.assertTrue(result["injected_private_ec2_network_structure_verified"])
        self.assertTrue(result["pinned_ed25519_source_attestation_and_ecr_scan_readback_verified"])
        for k,v in result.items():
            if k.startswith(("actual_","real_","runtime_","owner_approved_",
                             "production_","oauth_","cloud_resources_","youtube_")):
                with self.subTest(key=k):
                    self.assertIs(v,False)
        self.assertIs(result["release_authorized"],False)
        self.assertIs(result["owner_activation_still_required"],True)
        self.assertEqual(self.sts.calls,["get_caller_identity"])
        self.assertEqual(self.iam.calls.count("get_role"),2)
        self.assertEqual(self.ecr.methods,[
            "describe_repositories","describe_images","describe_image_scan_findings"])
        self.assertTrue(self.ec2.methods)
        self.assertTrue(set(self.ec2.methods)<={
            "describe_vpcs","describe_vpc_attribute","describe_subnets",
            "describe_vpc_endpoints","describe_route_tables",
            "describe_security_groups"})

    def test_refuse_account_drift_before_contacting_clients(self):
        wrong=replace(SCOPE,iam_scope=replace(IAM,aws_account_id="999999999999"))
        self.denied(wrong)
        self.assertEqual(self.sts.calls,[])
        self.assertEqual(self.iam.calls,[])

    def test_refuse_region_drift_before_client_call(self):
        wrong=replace(SCOPE,iam_scope=replace(IAM,aws_region="us-east-1"))
        self.denied(wrong)
        self.assertEqual(self.sts.calls,[])

    def test_refuse_ecr_repository_drift_before_client_call(self):
        wrong=replace(SCOPE,iam_scope=replace(IAM,ecr_repository_name="other/repo"))
        self.denied(wrong)
        self.assertEqual(self.sts.calls,[])

    def test_inspector_role_cannot_be_the_ecs_task_role(self):
        wrong=replace(SCOPE,inspector_role_name=IAM.task_role_name)
        self.denied(wrong)
        self.assertEqual(self.sts.calls,[])

    def test_inspector_role_cannot_be_the_execution_role(self):
        wrong=replace(SCOPE,inspector_role_name=IAM.execution_role_name)
        self.denied(wrong)

    def test_wrong_sts_account_fails_before_iam_ec2_ecr(self):
        self.sts.identity["Account"]="888888888888"
        self.denied()
        self.assertEqual(self.iam.calls,[])
        self.assertEqual(self.ec2.methods,[])
        self.assertEqual(self.ecr.methods,[])

    def test_wrong_sts_role_fails_before_iam(self):
        self.sts.identity["Arn"]=(
            f"arn:aws:sts::{IAM.aws_account_id}:assumed-role/Admin/attack")
        self.denied()
        self.assertEqual(self.iam.calls,[])

    def test_invalid_sts_session_rejected(self):
        self.sts.identity["Arn"]=(
            f"arn:aws:sts::{IAM.aws_account_id}:"
            "assumed-role/OnlyInspector/bad/session")
        self.denied()

    def test_untrusted_task_template_fails_before_any_provider_read(self):
        self.denied(template=TEMPLATE.replace(
            "OWNER_READ_ONLY_BOOT_GUARD","OWNER_RELEASE_ENABLED",1))
        self.assertEqual(self.sts.calls,[])

    def test_additional_service_in_taskdef_refused_before_sts(self):
        self.denied(template=TEMPLATE.replace(
            '"Resources": {',
            '"Resources": {"Extra":{"Type":"AWS::ECS::Service"},',1))
        self.assertEqual(self.sts.calls,[])

    def test_empty_or_oversized_template_fails(self):
        self.denied(template="")
        self.denied(template=" "*65537)
        self.assertEqual(self.sts.calls,[])

    def test_iam_admin_grant_rejected_before_network_reads(self):
        self.iam.inline[IAM.task_role_name]=["AdministratorAccess"]
        self.denied()
        self.assertEqual(self.ec2.methods,[])

    def test_managed_execution_policy_addition_refused(self):
        self.iam.attached[IAM.execution_role_name]=[{
            "PolicyName":"AdministratorAccess","PolicyArn":"arn:aws:iam::aws:policy/AdministratorAccess"
        }]
        self.denied()

    def test_iam_truncated_readback_rejected(self):
        self.iam.truncated=True
        self.denied()

    def test_missing_private_network_endpoint_fails_closed(self):
        self.ec2.data["endpoints"]=[
            x for x in self.ec2.data["endpoints"]
            if not x["ServiceName"].endswith("ecr.dkr")]
        self.denied()
        self.assertEqual(self.ecr.methods,[])

    def test_ecr_mutable_repository_rejected(self):
        self.ecr.repository["imageTagMutability"]="MUTABLE"
        self.denied()

    def test_high_risk_image_scan_rejected(self):
        self.ecr.scan["imageScanFindings"]["findingSeverityCounts"]["HIGH"]=1
        self.denied()

    def test_wrong_cryptographic_owner_signature_rejected(self):
        self.signature="AA"+self.signature[2:]
        self.denied()
        self.assertEqual(self.ecr.methods,[])

    def test_wrong_owner_public_key_pin_rejected(self):
        self.fingerprint="a"*64
        self.denied()

    def test_external_sts_secret_string_not_exposed_or_chained(self):
        self.sts.leak=True
        try:
            self.run_gate()
        except CompositeOwnerPreflightRefused as e:
            self.assertNotIn("FAKE_SECRET",str(e))
            self.assertIsNone(e.__cause__)
            self.assertEqual(self.iam.calls,[])
        else:
            self.fail("Expected fail-closed unreadable identity")

    def test_false_positive_injected_ec2_exception_scrubbed(self):
        def raise_secret(**_):
            raise RuntimeError("FAKE_SECRET_IN_PROVIDER_EXCEPTION")
        self.ec2.describe_vpcs=raise_secret
        try:
            self.run_gate()
        except CompositeOwnerPreflightRefused as e:
            self.assertNotIn("FAKE_SECRET",str(e))
            self.assertIsNone(e.__cause__)
        else:
            self.fail("Expected denial")

    def test_missing_current_clock_or_bad_scope_refused(self):
        with self.assertRaises(CompositeOwnerPreflightRefused):
            inspect_inert_owner_runtime(
                scope=SCOPE,sts=self.sts,iam=self.iam,ec2=self.ec2,ecr=self.ecr,
                manual_task_template_json=TEMPLATE,
                signed_image_json=self.signed,owner_signature_b64=self.signature,
                owner_public_key_b64=self.pub,
                owner_public_key_sha256=self.fingerprint,
                at=NOW.replace(tzinfo=None))
        self.denied(scope=object())


if __name__=="__main__":
    unittest.main()
