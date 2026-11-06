"""B4c3 owner-scoped AWS Fargate network and ECR image read-only preflight.

No client creation, AWS credentials, cloud writes, deployment, pricing,
publisher, media or YouTube access. Callers must supply authenticated read-only
EC2 and ECR clients AND an independently enrolled owner signing key.

Passing is *configuration evidence*, not permission to deploy/run/publish.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import base64
from hashlib import sha256
import ipaddress
import json
import re
from typing import Mapping

STATUS = "B4C3_OWNER_READ_ONLY_NETWORK_AND_SIGNED_IMAGE_PREFLIGHT_NO_DEPLOY"
ACCOUNT = re.compile(r"[0-9]{12}\Z")
REGION = re.compile(r"(?:us|eu|ap|sa|ca|me|af|il)-[a-z]+-[1-9][0-9]?\Z")
VPC = re.compile(r"vpc-[a-f0-9]{8,17}\Z")
SUBNET = re.compile(r"subnet-[a-f0-9]{8,17}\Z")
SG = re.compile(r"sg-[a-f0-9]{8,17}\Z")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
REPOSITORY = re.compile(r"[a-z0-9][a-z0-9._/-]{1,159}\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")
PL = re.compile(r"pl-[a-f0-9]{8,17}\Z")
ENDPOINT = re.compile(r"vpce-[a-f0-9]{8,17}\Z")
WORKFLOW = ".github/workflows/flowminute-b4c2-inert-fargate-taskdef.yml"
REQUIRED_SUFFIXES = ("ecr.api", "ecr.dkr", "logs", "s3")
SCHEMA = "flowminute-owner-image-source-attestation-v1"


class PreflightRefused(ValueError):
    """Topology, pinned image, or owner-trust evidence failed closed."""


@dataclass(frozen=True)
class OwnerInertNetworkScope:
    account_id: str
    region: str
    vpc_id: str
    subnet_ids: tuple[str, str]
    task_security_group_id: str
    endpoint_security_group_id: str
    ecr_repository: str
    image_digest: str
    source_commit_sha: str


def _require(ok: object, message: str) -> None:
    if ok is not True:
        raise PreflightRefused(message)


def _one(records: object, name: str) -> dict:
    _require(type(records) is list and len(records) == 1
             and type(records[0]) is dict, "Expected exactly one " + name)
    return records[0]


def verify_scope(scope: OwnerInertNetworkScope) -> None:
    _require(type(scope) is OwnerInertNetworkScope, "Owner scope class invalid")
    for name,pattern in (("account_id",ACCOUNT), ("region",REGION),
                         ("vpc_id",VPC), ("task_security_group_id",SG),
                         ("endpoint_security_group_id",SG),
                         ("ecr_repository",REPOSITORY), ("image_digest",DIGEST),
                         ("source_commit_sha",SHA)):
        val=getattr(scope,name)
        _require(type(val) is str and pattern.fullmatch(val) is not None,
                 "Invalid owner-selected " + name)
    _require(type(scope.subnet_ids) is tuple and len(scope.subnet_ids) == 2
             and len(set(scope.subnet_ids)) == 2
             and all(type(v) is str and SUBNET.fullmatch(v)
                     for v in scope.subnet_ids),
             "Exactly two distinct pinned private subnets required")
    _require(scope.task_security_group_id != scope.endpoint_security_group_id,
             "Task and service endpoint groups must be distinct")


def _private_rfc1918(cidr: object) -> bool:
    try:
        net=ipaddress.ip_network(cidr, strict=True)
        ranges=(ipaddress.ip_network("10.0.0.0/8"),
                ipaddress.ip_network("172.16.0.0/12"),
                ipaddress.ip_network("192.168.0.0/16"))
        return net.version==4 and any(net.subnet_of(r) for r in ranges)
    except (TypeError,ValueError):
        return False


def _is_exact_tcp_443_from_sg(permission: dict, source_group: str) -> bool:
    return (permission.get("IpProtocol") == "tcp"
            and permission.get("FromPort") == 443
            and permission.get("ToPort") == 443
            and permission.get("IpRanges",[]) == []
            and permission.get("Ipv6Ranges",[]) == []
            and permission.get("PrefixListIds",[]) == []
            and len(permission.get("UserIdGroupPairs",[])) == 1
            and permission["UserIdGroupPairs"][0].get("GroupId") == source_group)


def _is_s3_prefix_egress(permission: dict, prefix_list: str) -> bool:
    return (permission.get("IpProtocol") == "tcp"
            and permission.get("FromPort") == 443
            and permission.get("ToPort") == 443
            and permission.get("IpRanges",[]) == []
            and permission.get("Ipv6Ranges",[]) == []
            and permission.get("UserIdGroupPairs",[]) == []
            and len(permission.get("PrefixListIds",[])) == 1
            and permission["PrefixListIds"][0].get("PrefixListId") == prefix_list)


def _validate_route_tables(rows: object, scope: OwnerInertNetworkScope,
                           s3_gateway: dict, vpc_cidr: str) -> tuple[dict[str,dict], str]:
    _require(type(rows) is list and bool(rows), "Missing owner VPC route tables")
    by_id={}
    associations={}
    for table in rows:
        _require(type(table) is dict and table.get("VpcId") == scope.vpc_id,
                 "Route table VPC differs")
        name=table.get("RouteTableId")
        _require(type(name) is str and name not in by_id, "Duplicate route table")
        by_id[name]=table
        for a in table.get("Associations",[]):
            if a.get("SubnetId") in scope.subnet_ids:
                _require(a.get("AssociationState",{}).get("State","associated")=="associated",
                         "Task subnet route association not active")
                _require(a["SubnetId"] not in associations,"Multiple routes for task subnet")
                associations[a["SubnetId"]]=name
    _require(set(associations)==set(scope.subnet_ids),
             "Each task subnet must have explicit private route-table association")
    gateway_id=s3_gateway.get("VpcEndpointId")
    _require(type(gateway_id) is str and ENDPOINT.fullmatch(gateway_id) is not None,
             "S3 gateway endpoint identity invalid")
    _require(set(associations.values()).issubset(set(s3_gateway.get("RouteTableIds",[]))),
             "S3 gateway not attached to every task subnet route table")
    prefix_lists=set()
    for table_id in set(associations.values()):
        table=by_id[table_id]
        s3_routes=0
        for route in table.get("Routes",[]):
            _require(route.get("State","active")=="active","Blackholed route in task subnet")
            if route.get("GatewayId")=="local":
                _require(route.get("DestinationCidrBlock")==vpc_cidr
                         and not route.get("DestinationIpv6CidrBlock")
                         and not route.get("DestinationPrefixListId")
                         and not any(route.get(x) for x in (
                             "NatGatewayId","TransitGatewayId",
                             "VpcPeeringConnectionId","EgressOnlyInternetGatewayId")),
                         "Local route must cover ONLY the exact owner VPC CIDR")
                continue
            if route.get("GatewayId")==gateway_id:
                pl=route.get("DestinationPrefixListId")
                _require(type(pl) is str and PL.fullmatch(pl) is not None,
                         "S3 gateway route missing exact AWS prefix list")
                prefix_lists.add(pl)
                s3_routes+=1
                continue
            # This intentionally excludes public/NAT/peering/transit egress,
            # including IPv6 and direct/private VPC egress not yet approved.
            raise PreflightRefused("Task subnet has non-private-endpoint route")
        _require(s3_routes==1,"Task subnet must route S3 through gateway exactly once")
    _require(len(prefix_lists)==1,"Task subnets disagree on S3 gateway prefix list")
    return associations,next(iter(prefix_lists))


def verify_private_network(scope: OwnerInertNetworkScope, ec2: object) -> dict:
    """READ-ONLY AWS EC2 client is injected; never create a client or resources."""
    verify_scope(scope)
    vpc=_one(ec2.describe_vpcs(VpcIds=[scope.vpc_id]).get("Vpcs"),"owner VPC")
    _require(vpc.get("VpcId")==scope.vpc_id and vpc.get("State")=="available"
             and vpc.get("IsDefault") is False
             and _private_rfc1918(vpc.get("CidrBlock")),
             "Only existing available nondefault RFC1918 owner VPC accepted")
    for attribute in ("enableDnsSupport","enableDnsHostnames"):
        value=ec2.describe_vpc_attribute(VpcId=scope.vpc_id,Attribute=attribute)
        _require(value.get(attribute,{}).get("Value") is True,
                 "VPC private DNS support/hostnames not independently verified")
    subnets=ec2.describe_subnets(SubnetIds=list(scope.subnet_ids)).get("Subnets",[])
    _require(type(subnets) is list and len(subnets)==2
             and {s.get("SubnetId") for s in subnets}==set(scope.subnet_ids),
             "Two pinned task subnets not returned exactly")
    zones=set()
    for subnet in subnets:
        _require(subnet.get("VpcId")==scope.vpc_id
                 and subnet.get("State")=="available"
                 and subnet.get("MapPublicIpOnLaunch") is False
                 and _private_rfc1918(subnet.get("CidrBlock"))
                 and not subnet.get("Ipv6CidrBlockAssociationSet",[]),
                 "Task subnet not verified IPv4 private-only/no auto-public-IP")
        zones.add(subnet.get("AvailabilityZone"))
    _require(len(zones)==2 and all(isinstance(z,str) and z.startswith(scope.region)
                                   for z in zones),
             "Two distinct owner-region availability zones required")
    endpoints=ec2.describe_vpc_endpoints(
        Filters=[{"Name":"vpc-id","Values":[scope.vpc_id]}]).get("VpcEndpoints",[])
    _require(type(endpoints) is list,"VPC endpoints missing")
    by_service={}
    required={f"com.amazonaws.{scope.region}.{suffix}" for suffix in REQUIRED_SUFFIXES}
    for point in endpoints:
        name=point.get("ServiceName")
        if name in required:
            _require(name not in by_service,"Ambiguous duplicate required endpoint")
            by_service[name]=point
    _require(set(by_service)==required,"Missing ECR API/DKR, logs or S3 private endpoint")
    for suffix in ("ecr.api","ecr.dkr","logs"):
        ep=by_service[f"com.amazonaws.{scope.region}.{suffix}"]
        _require(ep.get("VpcId")==scope.vpc_id
                 and ep.get("State")=="available"
                 and ep.get("VpcEndpointType")=="Interface"
                 and ep.get("PrivateDnsEnabled") is True
                 and set(ep.get("SubnetIds",[]))>=set(scope.subnet_ids)
                 and {s.get("GroupId") for s in ep.get("Groups",[])}
                       =={scope.endpoint_security_group_id},
                 "Interface endpoint must cover both private subnets with pinned DNS/SG")
    s3=by_service[f"com.amazonaws.{scope.region}.s3"]
    _require(s3.get("VpcId")==scope.vpc_id
             and s3.get("State")=="available"
             and s3.get("VpcEndpointType")=="Gateway",
             "S3 image-layer gateway endpoint unavailable")
    route_tables=ec2.describe_route_tables(
        Filters=[{"Name":"vpc-id","Values":[scope.vpc_id]}]).get("RouteTables",[])
    associations,s3_prefix=_validate_route_tables(route_tables,scope,s3,vpc["CidrBlock"])
    groups=ec2.describe_security_groups(
        GroupIds=[scope.task_security_group_id,
                  scope.endpoint_security_group_id]).get("SecurityGroups",[])
    _require(type(groups) is list and len(groups)==2
             and {g.get("GroupId") for g in groups}
                  =={scope.task_security_group_id,scope.endpoint_security_group_id},
             "Owner task and VPC endpoint security groups differ")
    group_lookup={g["GroupId"]:g for g in groups}
    for g in groups:
        _require(g.get("VpcId")==scope.vpc_id,"Security group outside verified VPC")
    task=group_lookup[scope.task_security_group_id]
    ep_sg=group_lookup[scope.endpoint_security_group_id]
    _require(task.get("IpPermissions",[])==[],
             "Inert task group must have no inbound ports")
    outbound=task.get("IpPermissionsEgress",[])
    _require(len(outbound)==2
             and any(_is_exact_tcp_443_from_sg(p,scope.endpoint_security_group_id)
                     for p in outbound)
             and any(_is_s3_prefix_egress(p,s3_prefix) for p in outbound),
             "No public/task egress; only endpoint group TCP443 and S3 prefix allowed")
    inbound=ep_sg.get("IpPermissions",[])
    _require(len(inbound)==1
             and _is_exact_tcp_443_from_sg(inbound[0],scope.task_security_group_id),
             "Endpoint group must allow only task SG TCP443")
    return {
        "status":STATUS,
        "private_nondefault_vpc_verified":True,
        "two_private_az_subnets_verified":True,
        "no_internet_nat_ipv6_or_public_route_verified":True,
        "ecr_api_dkr_logs_interface_endpoints_verified":True,
        "s3_image_gateway_on_each_task_route_verified":True,
        "pinned_security_group_443_only_verified":True,
        "assign_public_ip_permitted":False,
        "actual_fargate_task_run":False,
        "aws_resources_modified":False,
        "release_authorized":False,
    }


def _json_no_dupes(source: object) -> dict:
    _require(isinstance(source,(bytes,str)) and len(source)<=8192,
             "Invalid owner-signed image provenance")
    try:
        def unique(pairs):
            obj={}
            for name,val in pairs:
                if name in obj:
                    raise PreflightRefused("Duplicate image provenance JSON key")
                obj[name]=val
            return obj
        data=json.loads(source,object_pairs_hook=unique,
                        parse_constant=lambda _: (_ for _ in ()).throw(
                            PreflightRefused("Nonfinite image provenance")))
    except (ValueError,UnicodeDecodeError) as exc:
        raise PreflightRefused("Malformed signed provenance") from exc
    _require(type(data) is dict,"Signed provenance must be a JSON object")
    return data


def verify_signed_owner_image(scope: OwnerInertNetworkScope, ecr: object,
                              signed_json: bytes, signature_b64: str,
                              trusted_owner_pubkey_b64: str,
                              trusted_owner_pubkey_sha256: str,
                              *, at: datetime) -> dict:
    """ECR readback AND verified pinned out-of-band Ed25519 owner signature.

    ECR image scans are NOT an OCI/Sigstore/Signer verification. This separate
    author-signed evidence is a narrower source-to-image binding, NOT proof
    that the image was actually rebuilt reproducibly or not compromised.
    """
    verify_scope(scope)
    _require(isinstance(at,datetime) and at.tzinfo is not None,
             "Owner inspection clock must be timezone aware")
    _require(type(signature_b64) is str and type(trusted_owner_pubkey_b64) is str
             and type(trusted_owner_pubkey_sha256) is str
             and re.fullmatch("[0-9a-f]{64}",trusted_owner_pubkey_sha256) is not None,
             "Owner's independently selected trust anchor is missing")
    try:
        key=base64.b64decode(trusted_owner_pubkey_b64,validate=True)
        signature=base64.b64decode(signature_b64,validate=True)
    except (ValueError,base64.binascii.Error) as exc:
        raise PreflightRefused("Invalid owner signature format") from exc
    _require(len(key)==32 and len(signature)==64
             and sha256(key).hexdigest()==trusted_owner_pubkey_sha256,
             "Owner pinned signing-key identity failed")
    # Requires cryptography on a protected owner verifier; public CI uses
    # disposable, synthetic keys only. No secret private keys are accepted.
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature
        Ed25519PublicKey.from_public_bytes(key).verify(signature,signed_json)
    except (InvalidSignature,ValueError,TypeError) as exc:
        raise PreflightRefused("Owner Ed25519 image signature invalid") from exc
    provenance=_json_no_dupes(signed_json)
    expected={
        "schema":SCHEMA,
        "aws_account_id":scope.account_id,
        "aws_region":scope.region,
        "repository":scope.ecr_repository,
        "image_digest":scope.image_digest,
        "source_commit_sha":scope.source_commit_sha,
        "workflow_path":WORKFLOW,
    }
    _require(set(provenance)==set(expected)|{"built_at_utc","expires_at_utc"},
             "Unreviewed image provenance attributes")
    for name,value in expected.items():
        _require(provenance.get(name)==value,"Signed image field differs: "+name)
    try:
        build=datetime.fromisoformat(provenance["built_at_utc"].replace("Z","+00:00"))
        expiry=datetime.fromisoformat(provenance["expires_at_utc"].replace("Z","+00:00"))
    except (AttributeError,ValueError,TypeError) as exc:
        raise PreflightRefused("Bad provenance UTC time fields") from exc
    _require(build.tzinfo is not None and expiry.tzinfo is not None
             and build<=at.astimezone(timezone.utc)<expiry
             and expiry-build<=timedelta(days=30)
             and at-build<=timedelta(days=30),
             "Stale/future/nonbounded owner image attestation")
    repositories=ecr.describe_repositories(
        repositoryNames=[scope.ecr_repository]).get("repositories",[])
    repository=_one(repositories,"owner ECR repository")
    _require(repository.get("repositoryName")==scope.ecr_repository
             and repository.get("registryId")==scope.account_id
             and repository.get("imageTagMutability")=="IMMUTABLE"
             and repository.get("repositoryUri")==(
                f"{scope.account_id}.dkr.ecr.{scope.region}.amazonaws.com/"
                f"{scope.ecr_repository}"),
             "ECR repository is not pinned same-account region immutable")
    image=_one(ecr.describe_images(
        repositoryName=scope.ecr_repository,
        registryId=scope.account_id,
        imageIds=[{"imageDigest":scope.image_digest}]).get("imageDetails",[]),
        "owner ECR image digest")
    _require(image.get("imageDigest")==scope.image_digest
             and image.get("registryId")==scope.account_id
             and image.get("repositoryName")==scope.ecr_repository,
             "Image digest or account differs")
    scan=ecr.describe_image_scan_findings(
        registryId=scope.account_id,repositoryName=scope.ecr_repository,
        imageId={"imageDigest":scope.image_digest})
    _require(scan.get("imageId",{}).get("imageDigest")==scope.image_digest
             and scan.get("imageScanStatus",{}).get("status")=="COMPLETE",
             "ECR image scan has no independently completed result")
    counts=scan.get("imageScanFindings",{}).get("findingSeverityCounts",{})
    _require(type(counts) is dict and all(
        type(value) is int and value>=0 for value in counts.values())
             and counts.get("CRITICAL",0)==0 and counts.get("HIGH",0)==0,
             "Image scan severity unacceptable/unknown")
    return {
        "status":STATUS,
        "pinned_owner_ed25519_signature_verified":True,
        "exact_account_region_repository_digest_verified":True,
        "immutable_ecr_repository_readback_verified":True,
        "completed_scan_no_high_critical_verified":True,
        "actual_oci_ecr_signer_signature_independently_verified":False,
        "reproducible_container_build_proven":False,
        "owner_billing_approval_verified":False,
        "actual_cloud_deployment":False,
        "release_authorized":False,
    }


def safe_read_only_gate(scope: OwnerInertNetworkScope, ec2: object, ecr: object,
                        signed_json: bytes, signature_b64: str,
                        trusted_owner_pubkey_b64: str,
                        trusted_owner_pubkey_sha256: str,
                        *, at: datetime) -> dict:
    network=verify_private_network(scope,ec2)
    provenance=verify_signed_owner_image(
        scope,ecr,signed_json,signature_b64,trusted_owner_pubkey_b64,
        trusted_owner_pubkey_sha256,at=at)
    _require(network["release_authorized"] is False
             and provenance["release_authorized"] is False,
             "Source-only owner security inspection must never enable release")
    return {
        "status":STATUS,
        "network_configuration_evidence":network,
        "image_provenance_evidence":provenance,
        "release_authorized":False,
        "real_cloud_task_executed":False,
        "real_youtube_upload":False,
        "cloud_resources_created":False,
        "owner_activation_still_required":True,
    }
