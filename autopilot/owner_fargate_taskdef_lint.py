"""Offline Flowminute security lint for owner-manual inert ECS task definition.

Source comparison only: no AWS SDK, provider network, credential or deployment.
AWS cfn-lint separately validates the actual resource schema on hosted CI.
Passing source lint does NOT verify runtime IAM, image signing, VPC or consent.
"""
from __future__ import annotations

import json
from pathlib import Path

from autopilot.b4c2_runtime_boot_guard import REQUIRED_OFF

SOURCE = "infra/aws/owner-readonly-fargate-taskdef.cfn.json"


class UnsafeCloudRuntimeTemplate(ValueError):
    """Any changed privilege, secret, service, image tag or schedule is denied."""


def _expect(actual,expected,detail: str) -> None:
    if type(actual) is not type(expected) or actual!=expected:
        raise UnsafeCloudRuntimeTemplate(detail)


def _ref(value: str) -> dict:
    return {"Ref":value}


def _sub(value: str) -> dict:
    return {"Fn::Sub":value}


def strict_load(source: str) -> dict:
    """Reject JSON duplicate keys even inside nested IAM or container arrays."""
    def unique(pairs):
        result={}
        for k,v in pairs:
            if k in result:
                raise UnsafeCloudRuntimeTemplate("Duplicate JSON key")
            result[k]=v
        return result
    try:
        value=json.loads(source,object_pairs_hook=unique)
    except UnsafeCloudRuntimeTemplate:
        raise
    except Exception:
        raise UnsafeCloudRuntimeTemplate("Invalid CloudFormation JSON") from None
    if type(value) is not dict:
        raise UnsafeCloudRuntimeTemplate("CloudFormation must be JSON object")
    return value


def lint_inert_task_definition(root: object) -> dict:
    if type(root) is not dict:
        raise UnsafeCloudRuntimeTemplate("Invalid CloudFormation root")
    _expect(set(root),{
        "AWSTemplateFormatVersion","Description","Parameters",
        "Rules","Resources","Outputs",
    },"Unreviewed CloudFormation root field")
    _expect(root["AWSTemplateFormatVersion"],"2010-09-09","Bad CloudFormation version")
    if (not isinstance(root["Description"],str)
        or "owner" not in root["Description"].lower()
        or "no" not in root["Description"].lower()):
        raise UnsafeCloudRuntimeTemplate("Missing owner-only no-deploy warning")
    parameters=root["Parameters"]
    patterns={
        "DeploymentSuffix":r"^[a-z0-9]{4,12}$",
        "OwnerApprovalReference":r"^OWNER-[A-Z0-9-]{8,64}$",
        "ExecutionRoleName":r"^[A-Za-z0-9+=,.@_-]{3,64}$",
        "ReadOnlyTaskRoleName":r"^[A-Za-z0-9+=,.@_-]{3,64}$",
        "EcrRepositoryName":r"^[a-z0-9][a-z0-9._/-]{1,159}$",
        "ImageDigest":r"^sha256:[0-9a-f]{64}$",
        "ExistingLogGroupName":r"^/flowminute/owner-private/[a-zA-Z0-9/_-]{3,80}$",
    }
    if type(parameters) is not dict or set(parameters)!=set(patterns):
        raise UnsafeCloudRuntimeTemplate("Unexpected/missing owner input")
    for name,pattern in patterns.items():
        p=parameters[name]
        if (type(p) is not dict or p.get("Type")!="String"
            or p.get("AllowedPattern")!=pattern
            or "Default" in p or "AllowedValues" in p
            or not isinstance(p.get("Description"),str)
            or len(p["Description"])<15
            or set(p) not in (
                {"Type","Description","AllowedPattern"},
                {"Type","Description","AllowedPattern","MinLength","MaxLength"},
            )):
            raise UnsafeCloudRuntimeTemplate("Defaulted/unreviewed input: "+name)
    _expect(
        (parameters["DeploymentSuffix"].get("MinLength"),
         parameters["DeploymentSuffix"].get("MaxLength")),(4,12),
        "Unbounded task suffix",
    )
    _expect(
        (parameters["EcrRepositoryName"].get("MinLength"),
         parameters["EcrRepositoryName"].get("MaxLength")),(2,160),
        "Unbounded image repository",
    )
    _expect(root["Rules"],{
        "SeparateExecutionAndTaskRoles":{"Assertions":[{
            "Assert":{"Fn::Not":[{"Fn::Equals":[
                _ref("ExecutionRoleName"),_ref("ReadOnlyTaskRoleName")]}]},
            "AssertDescription":
                "Execution and task role names must be different existing owner-authorized IAM roles.",
        }]}
    },"Missing distinct execution/task role owner rule")

    resources=root["Resources"]
    if type(resources) is not dict or set(resources)!={"OwnerReadOnlyTaskDefinition"}:
        raise UnsafeCloudRuntimeTemplate(
            "Unexpected service, scheduler, IAM role, credential or billable resource")
    item=resources["OwnerReadOnlyTaskDefinition"]
    if type(item) is not dict or set(item)!={"Type","Properties"}:
        raise UnsafeCloudRuntimeTemplate("Unexpected task resource attributes")
    _expect(item["Type"],"AWS::ECS::TaskDefinition","Only an inert task definition permitted")
    task=item["Properties"]
    if type(task) is not dict or set(task)!={
        "Family","RequiresCompatibilities","NetworkMode","Cpu","Memory",
        "RuntimePlatform","ExecutionRoleArn","TaskRoleArn",
        "ContainerDefinitions","Tags",
    }:
        raise UnsafeCloudRuntimeTemplate("Unknown task-level privilege")
    expected={
        "Family":_sub("flowminute-owner-readonly-${DeploymentSuffix}"),
        "RequiresCompatibilities":["FARGATE"],
        "NetworkMode":"awsvpc",
        "Cpu":"512",
        "Memory":"1024",
        "RuntimePlatform":{"OperatingSystemFamily":"LINUX","CpuArchitecture":"X86_64"},
        "ExecutionRoleArn":_sub(
            "arn:${AWS::Partition}:iam::${AWS::AccountId}:role/${ExecutionRoleName}"),
        "TaskRoleArn":_sub(
            "arn:${AWS::Partition}:iam::${AWS::AccountId}:role/${ReadOnlyTaskRoleName}"),
        "Tags":[
            {"Key":"FlowMinute","Value":"owner-readonly-no-publisher"},
            {"Key":"ReleaseStatus","Value":"blocked-no-oauth-or-upload"},
            {"Key":"OwnerChangeReference","Value":_ref("OwnerApprovalReference")},
        ],
    }
    for name,want in expected.items():
        _expect(task.get(name),want,"Changed Fargate role/compute parameter: "+name)

    containers=task["ContainerDefinitions"]
    if type(containers) is not list or len(containers)!=1 or type(containers[0]) is not dict:
        raise UnsafeCloudRuntimeTemplate("Unexpected sidecar/extra container")
    container=containers[0]
    expected_fields={
        "Name","Image","Essential","User","ReadonlyRootFilesystem",
        "WorkingDirectory","EntryPoint","StopTimeout","LinuxParameters",
        "Environment","LogConfiguration","DockerLabels",
    }
    _expect(set(container),expected_fields,"No Secrets, EnvFiles, ports, mounts or custom commands")
    want={
        "Name":"flowminute-owner-readonly-guard",
        "Image":_sub(
            "${AWS::AccountId}.dkr.ecr.${AWS::Region}.amazonaws.com/"
            "${EcrRepositoryName}@${ImageDigest}"),
        "Essential":True,
        "User":"65532",
        "ReadonlyRootFilesystem":True,
        "WorkingDirectory":"/app",
        "EntryPoint":["python","-B","-m","autopilot.b4c2_runtime_boot_guard"],
        "StopTimeout":30,
        "LinuxParameters":{"InitProcessEnabled":True},
        "LogConfiguration":{
            "LogDriver":"awslogs",
            "Options":{
                "awslogs-group":_ref("ExistingLogGroupName"),
                "awslogs-region":_ref("AWS::Region"),
                "awslogs-stream-prefix":"flowminute-readonly-guard",
            },
        },
        "DockerLabels":{
            "flowminute.release_authorized":"false",
            "flowminute.runtime":"owner-readonly-inert-source",
        },
    }
    for name,value in want.items():
        _expect(container.get(name),value,"Unsafe task container drift: "+name)
    env=container["Environment"]
    if type(env) is not list or len(env)!=len(REQUIRED_OFF)+2:
        raise UnsafeCloudRuntimeTemplate("Injected or missing runtime flags")
    flags={}
    for row in env:
        if (type(row) is not dict or set(row)!={"Name","Value"}
            or type(row["Name"]) is not str or type(row["Value"]) is not str
            or row["Name"] in flags):
            raise UnsafeCloudRuntimeTemplate("Duplicate/malformed runtime variable")
        flags[row["Name"]]=row["Value"]
    _expect(flags,{
        "FLOWMINUTE_RUNTIME_MODE":"OWNER_READ_ONLY_BOOT_GUARD",
        "PYTHONDONTWRITEBYTECODE":"1",
        **REQUIRED_OFF,
    },"Publishing/network/secret flag changed")
    _expect(root["Outputs"],{
        "ManualOnlyInertTaskDefinitionArn":{
            "Description":"An ECS task definition identifier only. NO actual task, service, scheduler, DB, OAuth or upload is provisioned.",
            "Value":_ref("OwnerReadOnlyTaskDefinition"),
        },
        "DoesNotCreateServiceOrSchedule":{
            "Value":"SOURCE_ONLY_TASK_DEFINITION_NO_SERVICE_NO_SCHEDULE_NO_RUN_TASK",
        },
        "RealYouTubePublishingAuthorized":{"Value":"false"},
        "OwnerChangeReferenceNotConsent":{"Value":_ref("OwnerApprovalReference")},
    },"Owner output incorrectly asserts deployment or release")
    return {
        "status":"OFFLINE_OWNER_MANUAL_TASK_DEF_SECURITY_LINT_NO_DEPLOY",
        "task_definition_only":True,
        "pinned_same_account_region_ecr_image":True,
        "nonroot_readonly_inert_entrypoint":True,
        "external_iam_policy_and_image_signing_verified":False,
        "actual_private_vpc_or_route_verified":False,
        "real_cloud_task_definition_registered":False,
        "real_ecs_task_run":False,
        "real_youtube_oauth_or_video":False,
        "release_authorized":False,
    }


def lint_repo_template() -> dict:
    return lint_inert_task_definition(
        strict_load(Path(SOURCE).read_text(encoding="utf-8"))
    )
