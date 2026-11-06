"""B4c3 security regression fixtures: no AWS credentials, no task or upload."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime,timezone,timedelta
import base64
from hashlib import sha256
import json
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from autopilot.owner_private_network_image_preflight import (
    OwnerInertNetworkScope,PreflightRefused,SCHEMA,WORKFLOW,
    verify_scope,verify_private_network,verify_signed_owner_image,
    safe_read_only_gate,
)

NOW=datetime(2026,11,6,5,0,tzinfo=timezone.utc)
ACCOUNT="123456789012"
REGION="ap-south-1"
VPC="vpc-01234567"
SUBNET_A="subnet-01234567"
SUBNET_B="subnet-12345678"
TASK_SG="sg-01234567"
ENDPOINT_SG="sg-12345678"
ECR_REPO="flowminute/owner-inert"
IMAGE="sha256:"+"a"*64
S3_ID="vpce-01234567"
S3_PREFIX="pl-01234567"
TASK_RT_A="rtb-01234567"
TASK_RT_B="rtb-12345678"


def scope():
    return OwnerInertNetworkScope(
        account_id=ACCOUNT,region=REGION,vpc_id=VPC,
        subnet_ids=(SUBNET_A,SUBNET_B),task_security_group_id=TASK_SG,
        endpoint_security_group_id=ENDPOINT_SG,
        ecr_repository=ECR_REPO,image_digest=IMAGE,source_commit_sha="b"*40)


def sg_443(target):
    return {"IpProtocol":"tcp","FromPort":443,"ToPort":443,
            "UserIdGroupPairs":[{"GroupId":target}]}


def prefix_443():
    return {"IpProtocol":"tcp","FromPort":443,"ToPort":443,
            "PrefixListIds":[{"PrefixListId":S3_PREFIX}]}


def make_ec2_data():
    endpoints=[
        {"ServiceName":f"com.amazonaws.{REGION}.{service}",
         "VpcEndpointId":f"vpce-{i+20:08x}",
         "VpcId":VPC,"State":"available","VpcEndpointType":"Interface",
         "PrivateDnsEnabled":True,"SubnetIds":[SUBNET_A,SUBNET_B],
         "Groups":[{"GroupId":ENDPOINT_SG}]}
        for i,service in enumerate(("ecr.api","ecr.dkr","logs"))
    ]
    endpoints.append({
        "ServiceName":f"com.amazonaws.{REGION}.s3",
        "VpcEndpointId":S3_ID,"VpcId":VPC,"State":"available",
        "VpcEndpointType":"Gateway","RouteTableIds":[TASK_RT_A,TASK_RT_B],
    })
    return {
        "vpc":{"VpcId":VPC,"State":"available","IsDefault":False,
               "CidrBlock":"10.22.0.0/16"},
        "attributes":{"enableDnsSupport":{"Value":True},
                      "enableDnsHostnames":{"Value":True}},
        "subnets":[
            {"VpcId":VPC,"SubnetId":SUBNET_A,"State":"available",
             "MapPublicIpOnLaunch":False,"CidrBlock":"10.22.1.0/24",
             "AvailabilityZone":REGION+"a"},
            {"VpcId":VPC,"SubnetId":SUBNET_B,"State":"available",
             "MapPublicIpOnLaunch":False,"CidrBlock":"10.22.2.0/24",
             "AvailabilityZone":REGION+"b"},
        ],
        "endpoints":endpoints,
        "routes":[
            {"RouteTableId":route,"VpcId":VPC,
             "Associations":[{"SubnetId":subnet,
                              "AssociationState":{"State":"associated"}}],
             "Routes":[
                {"DestinationCidrBlock":"10.22.0.0/16",
                 "GatewayId":"local","State":"active"},
                {"DestinationPrefixListId":S3_PREFIX,
                 "GatewayId":S3_ID,"State":"active"},
             ]}
            for route,subnet in [(TASK_RT_A,SUBNET_A),(TASK_RT_B,SUBNET_B)]
        ],
        "groups":[
            {"GroupId":TASK_SG,"VpcId":VPC,
             "IpPermissions":[],"IpPermissionsEgress":[sg_443(ENDPOINT_SG),prefix_443()]},
            {"GroupId":ENDPOINT_SG,"VpcId":VPC,
             "IpPermissions":[sg_443(TASK_SG)],"IpPermissionsEgress":[]},
        ],
    }


class FakeEC2:
    """Has READ-ONLY client methods only; any unexpected call fails."""
    def __init__(self, data=None):
        self.data=deepcopy(data if data is not None else make_ec2_data())
        self.methods=[]
    def describe_vpcs(self,**kwargs):
        self.methods.append("describe_vpcs")
        return {"Vpcs":[deepcopy(self.data["vpc"])]}
    def describe_vpc_attribute(self,**kwargs):
        self.methods.append("describe_vpc_attribute")
        return {kwargs["Attribute"]:deepcopy(self.data["attributes"][kwargs["Attribute"]])}
    def describe_subnets(self,**kwargs):
        self.methods.append("describe_subnets")
        return {"Subnets":deepcopy(self.data["subnets"])}
    def describe_vpc_endpoints(self,**kwargs):
        self.methods.append("describe_vpc_endpoints")
        return {"VpcEndpoints":deepcopy(self.data["endpoints"])}
    def describe_route_tables(self,**kwargs):
        self.methods.append("describe_route_tables")
        return {"RouteTables":deepcopy(self.data["routes"])}
    def describe_security_groups(self,**kwargs):
        self.methods.append("describe_security_groups")
        return {"SecurityGroups":deepcopy(self.data["groups"])}


class FakeECR:
    def __init__(self):
        self.methods=[]
        self.repository={
            "repositoryName":ECR_REPO,"registryId":ACCOUNT,
            "imageTagMutability":"IMMUTABLE",
            "repositoryUri":f"{ACCOUNT}.dkr.ecr.{REGION}.amazonaws.com/{ECR_REPO}",
        }
        self.image={"imageDigest":IMAGE,"registryId":ACCOUNT,
                    "repositoryName":ECR_REPO}
        self.scan={"imageId":{"imageDigest":IMAGE},
                   "imageScanStatus":{"status":"COMPLETE"},
                   "imageScanFindings":{"findingSeverityCounts":
                                        {"CRITICAL":0,"HIGH":0,"LOW":2}}}
    def describe_repositories(self,**kwargs):
        self.methods.append("describe_repositories")
        return {"repositories":[deepcopy(self.repository)]}
    def describe_images(self,**kwargs):
        self.methods.append("describe_images")
        return {"imageDetails":[deepcopy(self.image)]}
    def describe_image_scan_findings(self,**kwargs):
        self.methods.append("describe_image_scan_findings")
        return deepcopy(self.scan)


def signed_context(s=None):
    s=s if s is not None else scope()
    doc={
        "schema":SCHEMA,"aws_account_id":s.account_id,
        "aws_region":s.region,"repository":s.ecr_repository,
        "image_digest":s.image_digest,"source_commit_sha":s.source_commit_sha,
        "workflow_path":WORKFLOW,
        "built_at_utc":"2026-11-05T05:00:00Z",
        "expires_at_utc":"2026-11-13T05:00:00Z",
    }
    raw=json.dumps(doc,sort_keys=True,separators=(",",":")).encode()
    key=Ed25519PrivateKey.generate()  # synthetic ephemeral test key only
    pub=key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw)
    return (doc,raw,base64.b64encode(key.sign(raw)).decode(),
            base64.b64encode(pub).decode(),sha256(pub).hexdigest(),key)


class OwnerPrivateNetworkReadOnlyTests(unittest.TestCase):
    def test_valid_no_internet_private_control_plane_structure(self):
        c=FakeEC2()
        result=verify_private_network(scope(),c)
        self.assertTrue(result["two_private_az_subnets_verified"])
        self.assertTrue(result["s3_image_gateway_on_each_task_route_verified"])
        self.assertFalse(result["assign_public_ip_permitted"])
        self.assertFalse(result["release_authorized"])
        self.assertFalse(result["aws_resources_modified"])
        self.assertEqual(len(c.methods),7)
        self.assertTrue(all(x.startswith("describe_") for x in c.methods))

    def test_invalid_scope_and_account_crossing(self):
        original=scope()
        for key,bad in (
            ("account_id","12345678901x"),("vpc_id","vpc-x"),
            ("image_digest","myimage:latest"),("ecr_repository","DockerHub/X"),
            ("source_commit_sha","HEAD"),("subnet_ids",(SUBNET_A,SUBNET_A)),
            ("subnet_ids",[SUBNET_A,SUBNET_B]),
            ("endpoint_security_group_id",TASK_SG),
        ):
            with self.subTest(key=key):
                vals={**original.__dict__,key:bad}
                with self.assertRaises(PreflightRefused):
                    verify_scope(OwnerInertNetworkScope(**vals))

    def test_public_private_or_dns_subnet_rejected(self):
        for mutate in (
            lambda d:d["vpc"].update(IsDefault=True),
            lambda d:d["vpc"].update(CidrBlock="8.8.0.0/16"),
            lambda d:d["attributes"]["enableDnsSupport"].update(Value=False),
            lambda d:d["attributes"]["enableDnsHostnames"].update(Value=False),
            lambda d:d["subnets"][0].update(MapPublicIpOnLaunch=True),
            lambda d:d["subnets"][1].update(CidrBlock="8.8.8.0/24"),
            lambda d:d["subnets"][1].update(AvailabilityZone=REGION+"a"),
            lambda d:d["subnets"][1].update(Ipv6CidrBlockAssociationSet=[{"X":1}]),
        ):
            d=make_ec2_data();mutate(d)
            with self.assertRaises(PreflightRefused):verify_private_network(scope(),FakeEC2(d))

    def test_nats_public_igw_ipv6_peering_and_blackholes_denied(self):
        for route in (
            {"DestinationCidrBlock":"0.0.0.0/0","GatewayId":"igw-abc"},
            {"DestinationCidrBlock":"0.0.0.0/0","NatGatewayId":"nat-abc"},
            {"DestinationIpv6CidrBlock":"::/0","EgressOnlyInternetGatewayId":"eigw-abc"},
            {"DestinationCidrBlock":"10.0.0.0/8","TransitGatewayId":"tgw-abc"},
            {"DestinationCidrBlock":"10.40.0.0/16","VpcPeeringConnectionId":"pcx-abc"},
            {"DestinationCidrBlock":"0.0.0.0/0","GatewayId":"local","State":"blackhole"},
        ):
            d=make_ec2_data();d["routes"][0]["Routes"].append(route)
            with self.subTest(route=route),self.assertRaises(PreflightRefused):
                verify_private_network(scope(),FakeEC2(d))

    def test_required_vpc_endpoints_have_private_dns_and_both_azs(self):
        mutations=(
            lambda d:d["endpoints"].pop(0),
            lambda d:d["endpoints"][0].update(PrivateDnsEnabled=False),
            lambda d:d["endpoints"][1].update(SubnetIds=[SUBNET_A]),
            lambda d:d["endpoints"][2].update(State="pending"),
            lambda d:d["endpoints"][3].update(VpcEndpointType="Interface"),
            lambda d:d["endpoints"][3].update(RouteTableIds=[TASK_RT_A]),
            lambda d:d["routes"][1]["Routes"].pop(),
            lambda d:d["routes"][0]["Associations"].clear(),
        )
        for mutate in mutations:
            d=make_ec2_data();mutate(d)
            with self.assertRaises(PreflightRefused):
                verify_private_network(scope(),FakeEC2(d))

    def test_task_and_endpoint_security_groups_are_separate_scoped(self):
        changes=(
            lambda d:d["groups"][0]["IpPermissions"].append(sg_443(ENDPOINT_SG)),
            lambda d:d["groups"][0]["IpPermissionsEgress"].append(
                {"IpProtocol":"-1","IpRanges":[{"CidrIp":"0.0.0.0/0"}]}),
            lambda d:d["groups"][0]["IpPermissionsEgress"][0].update(ToPort=444),
            lambda d:d["groups"][0]["IpPermissionsEgress"].pop(),
            lambda d:d["groups"][1]["IpPermissions"][0].update(
                IpRanges=[{"CidrIp":"0.0.0.0/0"}]),
            lambda d:d["groups"][1].update(VpcId="vpc-11111111"),
        )
        for change in changes:
            d=make_ec2_data();change(d)
            with self.assertRaises(PreflightRefused):
                verify_private_network(scope(),FakeEC2(d))


class SignedImageProvenanceReadOnlyTests(unittest.TestCase):
    def verify(self,ec=None,ctx=None):
        ec=ec if ec is not None else FakeECR()
        ctx=ctx if ctx is not None else signed_context()
        doc,raw,sig,pub,fp,key=ctx
        return verify_signed_owner_image(scope(),ec,raw,sig,pub,fp,at=NOW)

    def test_signed_immutable_owner_ecr_scan_with_no_high_findings(self):
        e=FakeECR()
        result=self.verify(e)
        self.assertTrue(result["pinned_owner_ed25519_signature_verified"])
        self.assertTrue(result["completed_scan_no_high_critical_verified"])
        self.assertFalse(result["actual_oci_ecr_signer_signature_independently_verified"])
        self.assertFalse(result["actual_cloud_deployment"])
        self.assertFalse(result["release_authorized"])
        self.assertEqual(e.methods,
            ["describe_repositories","describe_images","describe_image_scan_findings"])

    def test_forged_signature_pinned_key_or_payload_rejected_before_ecr_read(self):
        d,raw,sig,pub,fp,key=signed_context()
        for vals in (
            (raw,sig,pub,"f"*64),
            (raw,sig[::-1],pub,fp),
            (raw+b" ",sig,pub,fp),
            (raw,sig,pub[:-1]+"!",fp),
        ):
            e=FakeECR()
            with self.assertRaises(PreflightRefused):
                verify_signed_owner_image(scope(),e,*vals,at=NOW)
            self.assertEqual(e.methods,[])

    def test_signed_but_wrong_digest_workflow_or_stale_date_rejected(self):
        for column,value in (
            ("image_digest","sha256:"+"f"*64),
            ("repository","someone/else"),
            ("workflow_path",".github/workflows/evil.yml"),
            ("source_commit_sha","a"*40),
            ("aws_account_id","000000000000"),
            ("built_at_utc","2026-11-07T00:00:00Z"),
            ("expires_at_utc","2026-11-05T00:00:00Z"),
            ("expires_at_utc","2027-01-01T00:00:00Z"),
        ):
            doc,_,_,_,_,key=signed_context()
            doc[column]=value
            raw=json.dumps(doc,sort_keys=True,separators=(",",":")).encode()
            pub=key.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw)
            with self.subTest(column=column),self.assertRaises(PreflightRefused):
                verify_signed_owner_image(scope(),FakeECR(),raw,
                    base64.b64encode(key.sign(raw)).decode(),
                    base64.b64encode(pub).decode(),sha256(pub).hexdigest(),at=NOW)

    def test_unrecognized_or_duplicate_signed_fields_not_accepted(self):
        doc,raw,_,_,_,key=signed_context()
        for r in (
            raw[:-1]+b',"image_digest":"sha256:'+(b"f"*64)+b'"}',
            raw[:-1]+b',"release_authorized":true}',
        ):
            pub=key.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw)
            with self.assertRaises(PreflightRefused):
                verify_signed_owner_image(scope(),FakeECR(),r,
                    base64.b64encode(key.sign(r)).decode(),
                    base64.b64encode(pub).decode(),sha256(pub).hexdigest(),at=NOW)

    def test_image_mutable_wrong_account_no_scan_or_high_critical_rejected(self):
        for method in (
            lambda e:e.repository.update(imageTagMutability="MUTABLE"),
            lambda e:e.repository.update(registryId="000000000000"),
            lambda e:e.image.update(imageDigest="sha256:"+"f"*64),
            lambda e:e.scan["imageScanStatus"].update(status="IN_PROGRESS"),
            lambda e:e.scan["imageScanFindings"]["findingSeverityCounts"].update(HIGH=1),
            lambda e:e.scan["imageScanFindings"]["findingSeverityCounts"].update(CRITICAL=1),
            lambda e:e.scan["imageScanFindings"]["findingSeverityCounts"].update(HIGH="zero"),
        ):
            ec=FakeECR();method(ec)
            with self.assertRaises(PreflightRefused):self.verify(ec)

    def test_entire_combined_gate_cannot_attest_a_release(self):
        doc,raw,sig,pub,fp,key=signed_context()
        a=safe_read_only_gate(scope(),FakeEC2(),FakeECR(),
                              raw,sig,pub,fp,at=NOW)
        self.assertTrue(a["owner_activation_still_required"])
        self.assertFalse(a["release_authorized"])
        self.assertFalse(a["real_youtube_upload"])
        self.assertFalse(a["cloud_resources_created"])
        self.assertFalse(a["real_cloud_task_executed"])


if __name__=="__main__":
    unittest.main()
