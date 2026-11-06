"""Synthetic adversarial B4c5 IAM snapshot tests; no AWS SDK or credentials."""
from __future__ import annotations

from copy import deepcopy
import unittest

from autopilot.owner_inert_iam_preflight import (
    EXECUTION_POLICY_NAME,
    IamPreflightRefused,
    InertIamScope,
    expected_execution_policy,
    expected_trust,
    verify_inert_iam_roles,
)

SCOPE = InertIamScope(
    aws_account_id="111122223333",
    aws_region="ap-south-1",
    execution_role_name="FlowminuteExec",
    task_role_name="FlowminuteTask",
    ecr_repository_name="flowminute/inert",
    existing_log_group_name="/flowminute/owner-private/guard",
    owner_change_reference="OWNER-TEST-CHANGE-00000001",
)


class FakeReadOnlyIam:
    def __init__(self):
        self.calls = []
        self.roles = {
            name: {
                "RoleName": name,
                "Arn": f"arn:aws:iam::{SCOPE.aws_account_id}:role/{name}",
                "Path": "/",
                "AssumeRolePolicyDocument": expected_trust(SCOPE),
            }
            for name in (SCOPE.task_role_name, SCOPE.execution_role_name)
        }
        self.managed = {name: [] for name in self.roles}
        self.inline = {
            SCOPE.task_role_name: [],
            SCOPE.execution_role_name: [EXECUTION_POLICY_NAME],
        }
        self.execution_doc = expected_execution_policy(SCOPE)
        self.truncate = False
        self.leak_error = False

    def get_role(self, *, RoleName):
        self.calls.append(("get_role", RoleName))
        if self.leak_error:
            raise RuntimeError("DO_NOT_LEAK_FAKE_CREDENTIAL_SECRET")
        return {"Role": deepcopy(self.roles[RoleName])}

    def list_attached_role_policies(self, *, RoleName):
        self.calls.append(("list_attached_role_policies", RoleName))
        return {"AttachedPolicies": deepcopy(self.managed[RoleName]),
                "IsTruncated": self.truncate}

    def list_role_policies(self, *, RoleName):
        self.calls.append(("list_role_policies", RoleName))
        return {"PolicyNames": deepcopy(self.inline[RoleName]),
                "IsTruncated": self.truncate}

    def get_role_policy(self, *, RoleName, PolicyName):
        self.calls.append(("get_role_policy", RoleName))
        return {"RoleName": RoleName, "PolicyName": PolicyName,
                "PolicyDocument": deepcopy(self.execution_doc)}


class B4C5InertIamTests(unittest.TestCase):
    def setUp(self):
        self.iam = FakeReadOnlyIam()

    def check_refused(self):
        with self.assertRaises(IamPreflightRefused):
            verify_inert_iam_roles(iam=self.iam, scope=SCOPE)

    def test_success_snapshot_never_authorizes_any_cloud_or_youtube_release(self):
        result = verify_inert_iam_roles(iam=self.iam, scope=SCOPE)
        self.assertTrue(result["task_role_policy_inventory_empty"])
        self.assertTrue(result["execution_policy_exact_allowlist"])
        self.assertTrue(result["ecs_service_trust_exactly_scoped"])
        for field in (
            "real_aws_account_and_client_origin_independently_attested",
            "effective_permissions_including_resource_policies_verified",
            "actual_ecs_task_deployed",
            "aws_budget_or_billing_approved", "youtube_oauth_verified",
            "youtube_upload_or_schedule_performed", "release_authorized",
        ):
            with self.subTest(field=field):
                self.assertIs(result[field], False)
        self.assertEqual(
            [c[0] for c in self.iam.calls],
            ["get_role", "list_attached_role_policies", "list_role_policies",
             "get_role", "list_attached_role_policies", "list_role_policies",
             "get_role_policy"],
        )
        self.assertEqual(
            expected_execution_policy(SCOPE)["Statement"][0]["Resource"], "*")

    def test_no_credential_discovery_or_private_cloud_client(self):
        with self.assertRaises(IamPreflightRefused):
            verify_inert_iam_roles(iam=None, scope=SCOPE)

    def test_wrong_account_arn(self):
        self.iam.roles[SCOPE.task_role_name]["Arn"] = (
            "arn:aws:iam::999999999999:role/FlowminuteTask")
        self.check_refused()

    def test_role_path_must_not_be_hidden(self):
        self.iam.roles[SCOPE.execution_role_name]["Path"] = "/admin/"
        self.check_refused()

    def test_unbounded_ecs_source_arn_is_rejected(self):
        self.iam.roles[SCOPE.task_role_name][
            "AssumeRolePolicyDocument"]["Statement"][0][
                "Condition"]["ArnLike"]["aws:SourceArn"] = "*"
        self.check_refused()

    def test_wrong_aws_source_account_rejected(self):
        self.iam.roles[SCOPE.task_role_name][
            "AssumeRolePolicyDocument"]["Statement"][0][
                "Condition"]["StringEquals"]["aws:SourceAccount"] = "999999999999"
        self.check_refused()

    def test_non_ecs_service_principal_rejected(self):
        self.iam.roles[SCOPE.execution_role_name][
            "AssumeRolePolicyDocument"]["Statement"][0][
                "Principal"] = {"AWS": "*"}
        self.check_refused()

    def test_extra_ecs_or_iam_trust_statement_rejected(self):
        trust = self.iam.roles[SCOPE.execution_role_name]["AssumeRolePolicyDocument"]
        trust["Statement"].append({"Effect": "Allow", "Action": "sts:AssumeRole",
                                   "Principal": {"AWS": "*"}})
        self.check_refused()

    def test_task_role_inline_grant_rejected(self):
        self.iam.inline[SCOPE.task_role_name] = ["Admin"]
        self.check_refused()

    def test_managed_attachment_on_task_role_rejected(self):
        self.iam.managed[SCOPE.task_role_name] = [{
            "PolicyName": "AdministratorAccess",
            "PolicyArn": "arn:aws:iam::aws:policy/AdministratorAccess",
        }]
        self.check_refused()

    def test_managed_attachment_on_execution_role_rejected(self):
        self.iam.managed[SCOPE.execution_role_name] = [{
            "PolicyName": "AmazonECSTaskExecutionRolePolicy",
            "PolicyArn": "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
        }]
        self.check_refused()

    def test_execution_must_have_exactly_one_inline_policy(self):
        self.iam.inline[SCOPE.execution_role_name] = [
            EXECUTION_POLICY_NAME, "Other"]
        self.check_refused()

    def test_duplicate_inline_policy_name_rejected(self):
        self.iam.inline[SCOPE.execution_role_name] = [
            EXECUTION_POLICY_NAME, EXECUTION_POLICY_NAME]
        self.check_refused()

    def test_policy_notaction_cannot_be_added(self):
        self.iam.execution_doc["Statement"][1]["NotAction"] = "iam:*"
        self.check_refused()

    def test_overbroad_s3_or_iam_permission_rejected(self):
        self.iam.execution_doc["Statement"].append({
            "Effect": "Allow", "Action": ["s3:*", "iam:PassRole"],
            "Resource": "*",
        })
        self.check_refused()

    def test_ecr_repo_wildcard_rejected(self):
        self.iam.execution_doc["Statement"][1]["Resource"] = "*"
        self.check_refused()

    def test_cloudwatch_loggroup_wildcard_rejected(self):
        self.iam.execution_doc["Statement"][2]["Resource"] = "*"
        self.check_refused()

    def test_policy_condition_drift_rejected(self):
        self.iam.execution_doc["Statement"][0]["Condition"] = {
            "Bool": {"aws:SecureTransport": "true"}}
        self.check_refused()

    def test_missing_required_ecr_image_action_rejected(self):
        self.iam.execution_doc["Statement"][1]["Action"].remove(
            "ecr:BatchGetImage")
        self.check_refused()

    def test_truncated_policy_pages_are_never_assumed_empty(self):
        self.iam.truncate = True
        self.check_refused()

    def test_permissions_boundary_not_assumed_to_prove_identity(self):
        self.iam.roles[SCOPE.task_role_name]["PermissionsBoundary"] = {
            "PermissionsBoundaryArn": "arn:aws:iam::aws:policy/ReadOnlyAccess"}
        self.check_refused()

    def test_external_exception_scrubbed(self):
        self.iam.leak_error = True
        try:
            verify_inert_iam_roles(iam=self.iam, scope=SCOPE)
        except IamPreflightRefused as exc:
            self.assertNotIn("DO_NOT_LEAK_FAKE_CREDENTIAL", str(exc))
            self.assertIsNone(exc.__cause__)
        else:
            self.fail("Expected fail-closed IAM refusal")

    def test_unpinned_scope_and_reused_role_rejected(self):
        with self.assertRaises(IamPreflightRefused):
            verify_inert_iam_roles(iam=self.iam, scope=InertIamScope(
                aws_account_id=SCOPE.aws_account_id,
                aws_region=SCOPE.aws_region,
                execution_role_name=SCOPE.execution_role_name,
                task_role_name=SCOPE.execution_role_name,
                ecr_repository_name=SCOPE.ecr_repository_name,
                existing_log_group_name=SCOPE.existing_log_group_name,
                owner_change_reference=SCOPE.owner_change_reference))
        with self.assertRaises(IamPreflightRefused):
            verify_inert_iam_roles(iam=self.iam, scope=InertIamScope(
                aws_account_id=SCOPE.aws_account_id,
                aws_region="not-a-region",
                execution_role_name=SCOPE.execution_role_name,
                task_role_name=SCOPE.task_role_name,
                ecr_repository_name=SCOPE.ecr_repository_name,
                existing_log_group_name=SCOPE.existing_log_group_name,
                owner_change_reference=SCOPE.owner_change_reference))


if __name__ == "__main__":
    unittest.main()
