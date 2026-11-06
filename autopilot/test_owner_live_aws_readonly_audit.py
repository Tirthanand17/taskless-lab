"""B4c7 synthetic tests for manual protected AWS read-only adapter.

No GitHub OIDC token, public PR AWS client, real account, paid cloud, OAuth,
YouTube calls, or release approval is used in these fixtures.
"""
from __future__ import annotations

import base64
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import unittest

from autopilot.owner_live_aws_readonly_audit import (
    ALLOWED_METHODS, ENVIRONMENT_NAME, REPO, SCHEMA, STATUS,
    LiveAuditRefused, OnlyReadMethods, load_inputs, parse_scope,
    run_readonly_audit,
)
from autopilot.test_owner_inert_composite_preflight import (
    IAM, NETWORK, SCOPE, TEMPLATE, FakeSTS, FakeIAM, FakeEC2, FakeECR,
)
from autopilot.test_owner_private_network_image_preflight import NOW, signed_context

WORKFLOW = Path(".github/workflows/flowminute-b4c7-owner-live-readonly.yml")


def configured_scope() -> dict:
    return {
        "schema": SCHEMA,
        "aws_account_id": IAM.aws_account_id,
        "aws_region": IAM.aws_region,
        "inspector_role_name": SCOPE.inspector_role_name,
        "execution_role_name": IAM.execution_role_name,
        "task_role_name": IAM.task_role_name,
        "ecr_repository_name": IAM.ecr_repository_name,
        "existing_log_group_name": IAM.existing_log_group_name,
        "owner_change_reference": IAM.owner_change_reference,
        "vpc_id": NETWORK.vpc_id,
        "subnet_ids": list(NETWORK.subnet_ids),
        "task_security_group_id": NETWORK.task_security_group_id,
        "endpoint_security_group_id": NETWORK.endpoint_security_group_id,
        "image_digest": NETWORK.image_digest,
        "source_commit_sha": NETWORK.source_commit_sha,
    }


def safe_environment() -> dict[str, str]:
    _, signed, signature, public_key, fingerprint, _ = signed_context(NETWORK)
    return {
        "GITHUB_REPOSITORY": REPO,
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_ACTOR": "Tirthanand17",
        "GITHUB_SHA": "c"*40,
        "FLOWMINUTE_B4C7_PROTECTED_ENVIRONMENT": ENVIRONMENT_NAME,
        "FLOWMINUTE_B4C7_AUDIT_MODE": "INERT_READ_ONLY_ONLY",
        "FLOWMINUTE_B4C7_CHANGE_REFERENCE": IAM.owner_change_reference,
        "FLOWMINUTE_B4C7_SCOPE_JSON": json.dumps(configured_scope()),
        "FLOWMINUTE_B4C7_SIGNED_IMAGE_B64": base64.b64encode(signed).decode(),
        "FLOWMINUTE_B4C7_IMAGE_SIGNATURE_B64": signature,
        "FLOWMINUTE_B4C7_SIGNER_PUBKEY_B64": public_key,
        "FLOWMINUTE_B4C7_SIGNER_FINGERPRINT": fingerprint,
        "AWS_REGION": IAM.aws_region,
        "FLOWMINUTE_ENABLE_PUBLISH": "0",
        "FLOWMINUTE_ALLOW_LAPTOP": "0",
        "PUBLISH_ENABLED": "false",
        "FLOWMINUTE_OWNER_RELEASE_AUTHORIZED": "0",
        "FLOWMINUTE_MODEL_PAID_SPEND_USD": "0",
        "AWS_ACCESS_KEY_ID": "ASIAINVENTEDFAKE",
        "AWS_SECRET_ACCESS_KEY": "INVENTED_NONE_REAL",
        "AWS_SESSION_TOKEN": "INVENTED_TEMPORARY_TOKEN",
        "AWS_EC2_METADATA_DISABLED": "true",
    }


class FakeSession:
    def __init__(self):
        self.sts=FakeSTS()
        self.iam=FakeIAM()
        self.ec2=FakeEC2()
        self.ecr=FakeECR()
        self.calls=[]
        self.clients={"sts":self.sts,"iam":self.iam,"ec2":self.ec2,"ecr":self.ecr}

    def client(self, service, *, region_name):
        self.calls.append((service,region_name))
        return self.clients[service]


class B4c7ProtectedAuditTests(unittest.TestCase):
    def setUp(self):
        self.env=safe_environment()
        self.session=FakeSession()

    def gate(self, manual_template=TEMPLATE):
        return run_readonly_audit(
            env=self.env,session=self.session,at=NOW,
            manual_task_template_json=manual_template,
        )

    def deny(self):
        with self.assertRaises(LiveAuditRefused):
            self.gate()

    def test_full_synthetic_audit_is_readonly_and_redacted(self):
        value=self.gate()
        self.assertEqual(value["status"], STATUS)
        self.assertIs(value["bounded_owner_sts_iam_ec2_ecr_readback_finished"],True)
        self.assertIs(value["release_authorized"],False)
        self.assertIs(value["actual_fargate_task_launched"],False)
        self.assertIs(value["youtube_oauth_or_publish_performed"],False)
        self.assertIs(value["owner_activation_still_required"],True)
        serialized=json.dumps(value)
        for private in (IAM.aws_account_id,NETWORK.vpc_id,
                        IAM.execution_role_name,NETWORK.image_digest,
                        self.env["FLOWMINUTE_B4C7_SIGNER_PUBKEY_B64"]):
            self.assertNotIn(private,serialized)
        self.assertEqual(
            self.session.calls,
            [(service,IAM.aws_region) for service in ("sts","iam","ec2","ecr")],
        )
        self.assertEqual(self.session.sts.calls,["get_caller_identity"])
        self.assertEqual(self.session.iam.calls.count("get_role"),2)
        self.assertEqual(
            self.session.ecr.methods,
            ["describe_repositories","describe_images","describe_image_scan_findings"],
        )

    def test_shape_only_preflight_does_not_create_clients(self):
        x=load_inputs(self.env,live=False)
        self.assertEqual(x.scope.iam_scope.aws_region,IAM.aws_region)
        self.assertEqual(self.session.calls,[])

    def test_missing_token_refuses_before_any_client(self):
        del self.env["AWS_SESSION_TOKEN"]
        self.deny()
        self.assertEqual(self.session.calls,[])

    def test_untrusted_branch_denied_before_client(self):
        self.env["GITHUB_REF"]="refs/heads/feature/foo"
        self.deny()
        self.assertEqual(self.session.calls,[])

    def test_pr_event_denied_before_client(self):
        self.env["GITHUB_EVENT_NAME"]="pull_request"
        self.deny()
        self.assertEqual(self.session.calls,[])

    def test_push_event_denied_before_client(self):
        self.env["GITHUB_EVENT_NAME"]="push"
        self.deny()
        self.assertEqual(self.session.calls,[])

    def test_wrong_actor_denied_before_client(self):
        self.env["GITHUB_ACTOR"]="not-the-owner"
        self.deny()
        self.assertEqual(self.session.calls,[])

    def test_wrong_repo_denied_before_client(self):
        self.env["GITHUB_REPOSITORY"]="other/repo"
        self.deny()
        self.assertEqual(self.session.calls,[])

    def test_missing_environment_marker_denied_before_client(self):
        self.env["FLOWMINUTE_B4C7_PROTECTED_ENVIRONMENT"]="other"
        self.deny()
        self.assertEqual(self.session.calls,[])

    def test_publish_mode_denied_before_client(self):
        self.env["FLOWMINUTE_B4C7_AUDIT_MODE"]="PUBLISH_ENABLED"
        self.deny()
        self.assertEqual(self.session.calls,[])

    def test_any_release_spend_or_laptop_escalation_denied_before_client(self):
        for key, bad in (
            ("FLOWMINUTE_ENABLE_PUBLISH", "1"),
            ("PUBLISH_ENABLED", "true"),
            ("FLOWMINUTE_OWNER_RELEASE_AUTHORIZED", "1"),
            ("FLOWMINUTE_MODEL_PAID_SPEND_USD", "0.01"),
            ("FLOWMINUTE_ALLOW_LAPTOP", "1"),
        ):
            with self.subTest(key=key):
                clean=self.env[key]
                self.env[key]=bad
                self.deny()
                self.assertEqual(self.session.calls, [])
                self.env[key]=clean

    def test_change_reference_not_matching_protected_scope_denied(self):
        self.env["FLOWMINUTE_B4C7_CHANGE_REFERENCE"]="OWNER-OTHER-CHANGE-0001"
        self.deny()
        self.assertEqual(self.session.calls,[])

    def test_region_mismatch_denied_before_client(self):
        self.env["AWS_REGION"]="us-east-1"
        self.deny()
        self.assertEqual(self.session.calls,[])

    def test_missing_signed_attestation_denied_before_client(self):
        del self.env["FLOWMINUTE_B4C7_SIGNED_IMAGE_B64"]
        self.deny()
        self.assertEqual(self.session.calls,[])

    def test_bad_public_signing_key_denied_before_client(self):
        self.env["FLOWMINUTE_B4C7_SIGNER_PUBKEY_B64"]="not-base64?"
        self.deny()
        self.assertEqual(self.session.calls,[])

    def test_bad_owner_signing_key_pin_denied_before_client(self):
        self.env["FLOWMINUTE_B4C7_SIGNER_FINGERPRINT"]="wrong"
        self.deny()
        self.assertEqual(self.session.calls,[])

    def test_account_mismatch_against_injected_sts_denied(self):
        self.session.sts.identity["Account"]="999999999999"
        self.deny()
        self.assertEqual(self.session.ec2.methods,[])

    def test_iam_admin_escalation_denied(self):
        self.session.iam.inline[IAM.task_role_name]=["AdministratorAccess"]
        self.deny()
        self.assertEqual(self.session.ec2.methods,[])

    def test_wrong_ecr_scan_severity_denied(self):
        self.session.ecr.scan["imageScanFindings"]["findingSeverityCounts"]["HIGH"]=1
        self.deny()

    def test_broken_signature_denied(self):
        self.env["FLOWMINUTE_B4C7_IMAGE_SIGNATURE_B64"]=base64.b64encode(
            bytes(64)).decode()
        self.deny()

    def test_tampered_inert_template_denied(self):
        with self.assertRaises(LiveAuditRefused):
            self.gate(TEMPLATE.replace(
                "OWNER_READ_ONLY_BOOT_GUARD","OWNER_PUBLISH_MODE",1))
        self.assertEqual(self.session.sts.calls,[])

    def test_unknown_aws_method_prohibited(self):
        wrapped=OnlyReadMethods(self.session.iam,ALLOWED_METHODS["iam"])
        with self.assertRaises(LiveAuditRefused):
            wrapped.create_role(RoleName="fake")
        with self.assertRaises(LiveAuditRefused):
            wrapped.attach_role_policy(RoleName="fake")

    def test_unknown_client_exception_scrubbed(self):
        def explode(**_):
            raise RuntimeError("PRIVATE_OWNER_ACCOUNT_ID_123456")
        self.session.sts.get_caller_identity=explode
        try:
            self.gate()
        except LiveAuditRefused as exc:
            self.assertIsNone(exc.__cause__)
            self.assertNotIn("PRIVATE_OWNER_ACCOUNT",str(exc))
        else:
            self.fail("Expected protected live readback denial")

    def test_duplicate_json_keys_denied(self):
        raw=self.env["FLOWMINUTE_B4C7_SCOPE_JSON"]
        self.env["FLOWMINUTE_B4C7_SCOPE_JSON"]=raw[:-1]+',"schema":"shadow"}'
        self.deny()
        self.assertEqual(self.session.calls,[])

    def test_unknown_json_fields_denied(self):
        p=configured_scope()
        p["auto_publish"]=True
        self.env["FLOWMINUTE_B4C7_SCOPE_JSON"]=json.dumps(p)
        self.deny()
        self.assertEqual(self.session.calls,[])

    def test_mismatched_network_details_denied_before_client(self):
        p=configured_scope()
        p["subnet_ids"][1]=p["subnet_ids"][0]
        self.env["FLOWMINUTE_B4C7_SCOPE_JSON"]=json.dumps(p)
        self.deny()
        self.assertEqual(self.session.calls,[])

    def test_nonnumeric_injected_commit_ref_denied(self):
        self.env["GITHUB_SHA"]="untrusted"
        self.deny()
        self.assertEqual(self.session.calls,[])

    def test_unsafe_b64_size_denied(self):
        self.env["FLOWMINUTE_B4C7_SIGNED_IMAGE_B64"]="YQ=="*3000
        self.deny()
        self.assertEqual(self.session.calls,[])

    def test_workflow_is_manual_protected_and_no_deployment(self):
        s=WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("\non:\n  workflow_dispatch:\n",s)
        for event in ("pull_request","pull_request_target","push","schedule"):
            self.assertNotIn("\n  "+event+":",s)
        self.assertIn("environment: "+ENVIRONMENT_NAME,s)
        self.assertIn("github.ref == 'refs/heads/main'",s)
        self.assertIn("github.actor == 'Tirthanand17'",s)
        self.assertIn("contents: read",s)
        self.assertIn("id-token: write",s)
        self.assertIn("persist-credentials: false",s)
        self.assertIn("mask-aws-account-id: true",s)
        self.assertIn("allowed-account-ids:",s)
        self.assertIn("--preflight-only",s)
        self.assertIn("--live-readonly",s)
        self.assertLess(s.index("--preflight-only"),s.index("configure-aws-credentials"))
        self.assertNotIn("aws-access-key-id:",s)
        self.assertNotIn("aws-secret-access-key:",s)
        for op in ("ecs run-task","cloudformation deploy","ecr put-image",
                   "videos().insert(","aws iam create-role"):
            self.assertNotIn(op,s)


if __name__=="__main__":
    unittest.main()
