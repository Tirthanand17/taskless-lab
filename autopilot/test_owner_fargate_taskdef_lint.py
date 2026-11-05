"""B4c2 offline adversarial checks: owner manual Fargate task definition ONLY.

No ECS task, AWS account, private ECR image or authenticated owner runtime
exists in CI. All structural and bad-env checks run with pure fake inputs.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from autopilot.b4c2_runtime_boot_guard import (
    inspect_inert_boot, BootGuardRefused, REQUIRED_OFF, main
)
from autopilot.owner_fargate_taskdef_lint import (
    UnsafeCloudRuntimeTemplate, SOURCE, strict_load,
    lint_inert_task_definition, lint_repo_template,
)


def good_env():
    return {
        "FLOWMINUTE_RUNTIME_MODE":"OWNER_READ_ONLY_BOOT_GUARD",
        **REQUIRED_OFF,
    }


def original():
    return strict_load(Path(SOURCE).read_text(encoding="utf-8"))


class InertCloudRuntimeBootGuardTests(unittest.TestCase):
    def test_safe_inert_guard_never_claims_live_identity_or_release(self):
        info=inspect_inert_boot(good_env())
        self.assertEqual(info["status"],"INERT_OWNER_PREFLIGHT_BOOT_ONLY_NO_PROVIDER_CALL")
        self.assertEqual(len(info),13)
        for key,flag in info.items():
            if key.startswith("next_step") or key=="status":
                continue
            self.assertIs(flag,False,key)
        self.assertNotIn("token",str(info).lower())

    def test_actual_module_entrypoint_prints_only_redacted_inert_status(self):
        with patch.dict("os.environ",good_env(),clear=True):
            buf=StringIO()
            with redirect_stdout(buf):
                rc=main()
        self.assertEqual(rc,0)
        result=json.loads(buf.getvalue())
        self.assertEqual(result["status"],"INERT_OWNER_PREFLIGHT_BOOT_ONLY_NO_PROVIDER_CALL")
        self.assertFalse(result["release_authorized"])

    def test_unsafe_release_or_network_or_laptop_flags_refuse(self):
        for key,old in REQUIRED_OFF.items():
            for bad in ("1","true","","enabled","3.50",None):
                with self.subTest(key=key,bad=bad):
                    e=good_env()
                    if bad is None:
                        e.pop(key)
                    else:
                        e[key]=bad
                    with self.assertRaises(BootGuardRefused):
                        inspect_inert_boot(e)
        for value in (None,"PUBLISHER","OWNER_WRITE_ENABLED",""):
            with self.subTest(mode=value):
                e=good_env()
                if value is None:
                    e.pop("FLOWMINUTE_RUNTIME_MODE")
                else:
                    e["FLOWMINUTE_RUNTIME_MODE"]=value
                with self.assertRaises(BootGuardRefused):
                    inspect_inert_boot(e)

    def test_credential_names_fail_without_disclosing_sensitive_values(self):
        for name in (
            "YOUTUBE_TOKEN_JSON","YOUTUBE_REFRESH_TOKEN",
            "GOOGLE_OAUTH_REFRESH_TOKEN","FLOWMINUTE_YOUTUBE_OAUTH_SECRET_VALUE",
            "FLOWMINUTE_API_KEY","FLOWMINUTE_PRIVATE_DATABASE_DSN",
            "FLOWMINUTE_YOUTUBE_OAUTH_SECRET_REF",
            "FLOWMINUTE_OWNER_SIGNING_SECRET",
        ):
            with self.subTest(name=name):
                e=good_env()
                e[name]="never-print-this-secret-sensitive-value"
                with self.assertRaises(BootGuardRefused) as cm:
                    inspect_inert_boot(e)
                self.assertNotIn(e[name],str(cm.exception))
                with patch.dict("os.environ",e,clear=True):
                    buf=StringIO()
                    with redirect_stdout(buf):
                        self.assertEqual(main(),70)
                    self.assertEqual(buf.getvalue().strip(),
                                     "B4C2_INERT_BOOT_GUARD_REFUSED")

    def test_no_real_credentials_required_to_run_inert_gate(self):
        info=inspect_inert_boot(good_env())
        self.assertFalse(info["protected_secret_access_attempted"])
        self.assertFalse(info["real_youtube_oauth_or_video"] if "real_youtube_oauth_or_video" in info
                         else info["real_youtube_channel_oauth_validated"])


class OwnerManualFargateLintTests(unittest.TestCase):
    def test_real_repo_template_has_one_task_and_nothing_deployed(self):
        proof=lint_repo_template()
        self.assertTrue(proof["task_definition_only"])
        self.assertTrue(proof["pinned_same_account_region_ecr_image"])
        self.assertTrue(proof["nonroot_readonly_inert_entrypoint"])
        self.assertFalse(proof["real_cloud_task_definition_registered"])
        self.assertFalse(proof["real_ecs_task_run"])
        self.assertFalse(proof["real_youtube_oauth_or_video"])
        self.assertFalse(proof["release_authorized"])
        root=original()
        self.assertEqual(set(root["Resources"]),{"OwnerReadOnlyTaskDefinition"})
        p=root["Resources"]["OwnerReadOnlyTaskDefinition"]["Properties"]
        self.assertEqual(p["NetworkMode"],"awsvpc")
        self.assertEqual(p["RequiresCompatibilities"],["FARGATE"])
        self.assertEqual((p["Cpu"],p["Memory"]),("512","1024"))
        self.assertTrue(p["ContainerDefinitions"][0]["ReadonlyRootFilesystem"])
        self.assertEqual(p["ContainerDefinitions"][0]["User"],"65532")
        self.assertEqual(
            p["ContainerDefinitions"][0]["EntryPoint"],
            ["python","-B","-m","autopilot.b4c2_runtime_boot_guard"],
        )

    def test_duplicate_and_malformed_json_cannot_bypass_lint(self):
        for text in (
            "", "null", "[]", "{bad}",
            '{"Resources":{"safe":1,"safe":2}}',
            '{"Container":{"Image":"safe","Image":"malicious:latest"}}',
            '{"Release":NaN}',
        ):
            with self.subTest(text=text),self.assertRaises(
                    UnsafeCloudRuntimeTemplate):
                strict_load(text)

    def test_auto_service_scheduler_network_or_iam_resource_injection_denied(self):
        for extra in (
            "AWS::ECS::Service","AWS::Events::Rule","AWS::Scheduler::Schedule",
            "AWS::IAM::Role","AWS::Lambda::Function",
            "AWS::SecretsManager::Secret","AWS::RDS::DBInstance",
            "AWS::EC2::NatGateway","AWS::ECS::Cluster",
        ):
            with self.subTest(extra=extra):
                obj=original()
                obj["Resources"]["Injected"]={"Type":extra,"Properties":{}}
                with self.assertRaises(UnsafeCloudRuntimeTemplate):
                    lint_inert_task_definition(obj)

    def test_unreviewed_account_role_image_default_and_scope_denied(self):
        cases=(
            ("ExecutionRoleName","Default","public-pr-token-access"),
            ("ReadOnlyTaskRoleName","Default","admin"),
            ("EcrRepositoryName","Default","public/mutable-image"),
            ("ImageDigest","Default","sha256:"+"0"*64),
            ("OwnerApprovalReference","Default","OWNER-FORGE-12345678"),
            ("ImageDigest","AllowedPattern",".*"),
            ("EcrRepositoryName","AllowedPattern",".*"),
            ("ExistingLogGroupName","AllowedPattern",".*"),
            ("ExecutionRoleName","AllowedPattern",".*"),
        )
        for name,property,value in cases:
            with self.subTest(name=name,property=property):
                root=original()
                root["Parameters"][name][property]=value
                with self.assertRaises(UnsafeCloudRuntimeTemplate):
                    lint_inert_task_definition(root)

    def test_root_roles_risk_cpu_memory_and_wrong_image_denied(self):
        cases=(
            ("NetworkMode","bridge"),
            ("Cpu","4096"),
            ("Memory","30720"),
            ("RequiresCompatibilities",["EC2"]),
            ("TaskRoleArn","arn:aws:iam::111111111111:role/Admin"),
            ("ExecutionRoleArn","arn:aws:iam::111111111111:role/GitHubPR"),
            ("RuntimePlatform",{"OperatingSystemFamily":"WINDOWS_SERVER_2022_FULL"}),
            ("Family","flowminute-live-publisher"),
        )
        for name,value in cases:
            with self.subTest(name=name):
                root=original()
                root["Resources"]["OwnerReadOnlyTaskDefinition"]["Properties"][name]=value
                with self.assertRaises(UnsafeCloudRuntimeTemplate):
                    lint_inert_task_definition(root)
        root=original()
        root["Rules"]={}
        with self.assertRaises(UnsafeCloudRuntimeTemplate):
            lint_inert_task_definition(root)

    def test_nonroot_inert_entrypoint_and_logs_cannot_be_escalated(self):
        cases=(
            ("Image","attacker/flowminute:latest"),
            ("User","0"),
            ("ReadonlyRootFilesystem",False),
            ("Essential",False),
            ("EntryPoint",["python","scripts/publish_youtube.py"]),
            ("WorkingDirectory","/owner-secrets"),
            ("StopTimeout",0),
            ("LogConfiguration",{"LogDriver":"awslogs","Options":{"awslogs-create-group":"true"}}),
        )
        for name,value in cases:
            with self.subTest(name=name):
                root=original()
                c=root["Resources"]["OwnerReadOnlyTaskDefinition"]["Properties"]["ContainerDefinitions"][0]
                c[name]=value
                with self.assertRaises(UnsafeCloudRuntimeTemplate):
                    lint_inert_task_definition(root)

    def test_secret_volume_port_env_or_privileged_sidecar_injection_denied(self):
        for name,value in (
            ("Secrets",[{"Name":"YOUTUBE_TOKEN_JSON","ValueFrom":"arn:secret"}]),
            ("EnvironmentFiles",[{"Type":"s3","Value":"my-secret-bucket"}]),
            ("PortMappings",[{"ContainerPort":8080}]),
            ("MountPoints",[{"SourceVolume":"oauth","ContainerPath":"/secrets"}]),
            ("Privileged",True),
        ):
            with self.subTest(name=name):
                root=original()
                root["Resources"]["OwnerReadOnlyTaskDefinition"]["Properties"]["ContainerDefinitions"][0][name]=value
                with self.assertRaises(UnsafeCloudRuntimeTemplate):
                    lint_inert_task_definition(root)
        root=original()
        container=root["Resources"]["OwnerReadOnlyTaskDefinition"]["Properties"]["ContainerDefinitions"]
        container.append(deepcopy(container[0]))
        with self.assertRaises(UnsafeCloudRuntimeTemplate):
            lint_inert_task_definition(root)

    def test_publisher_release_flag_duplicate_or_extra_env_denied(self):
        for name,value in (
            ("FLOWMINUTE_ENABLE_PUBLISH","1"),
            ("PUBLISH_ENABLED","true"),
            ("FLOWMINUTE_RUNTIME_NETWORK_AUTHORIZED","1"),
            ("FLOWMINUTE_OWNER_RELEASE_AUTHORIZED","1"),
            ("FLOWMINUTE_RUNTIME_MODE","OWNER_WRITE_ENABLED"),
        ):
            with self.subTest(name=name):
                root=original()
                env=root["Resources"]["OwnerReadOnlyTaskDefinition"]["Properties"]["ContainerDefinitions"][0]["Environment"]
                next(item for item in env if item["Name"]==name)["Value"]=value
                with self.assertRaises(UnsafeCloudRuntimeTemplate):
                    lint_inert_task_definition(root)
        root=original()
        env=root["Resources"]["OwnerReadOnlyTaskDefinition"]["Properties"]["ContainerDefinitions"][0]["Environment"]
        env.append({"Name":"YOUTUBE_TOKEN_JSON","Value":"FAKE_NEVER_USE"})
        with self.assertRaises(UnsafeCloudRuntimeTemplate):
            lint_inert_task_definition(root)
        root=original()
        env=root["Resources"]["OwnerReadOnlyTaskDefinition"]["Properties"]["ContainerDefinitions"][0]["Environment"]
        env[-1]=deepcopy(env[0])
        with self.assertRaises(UnsafeCloudRuntimeTemplate):
            lint_inert_task_definition(root)

    def test_any_output_claiming_publishing_denied(self):
        for name,value in (
            ("RealYouTubePublishingAuthorized",{"Value":"true"}),
            ("DoesNotCreateServiceOrSchedule",{"Value":"SCHEDULE_CREATED"}),
        ):
            with self.subTest(name=name):
                root=original()
                root["Outputs"][name]=value
                with self.assertRaises(UnsafeCloudRuntimeTemplate):
                    lint_inert_task_definition(root)


if __name__ == "__main__":
    unittest.main()
