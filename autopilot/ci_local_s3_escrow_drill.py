"""B3d4c2d1: real boto3 HTTP to LOCAL ephemeral Moto S3, all 213 fake assets.

This script refuses non-loopback endpoints. Every media byte is a deliberately
NONPLAYABLE invented string, not the actual Kokoro full videos; no real AWS
region/bucket/account/client/credential or model used. Moto Object Lock is a
simulation and does NOT establish actual legal immutability, external cost,
owner consent, KMS encryption, IAM permissions, or durable backups.

The test demonstrates 3 independently sourced logical story+claim dockets,
213 physically simulated asset writes and reads, SHA and version ID integrity,
per-object lock request/response and final manifest-last receipts.
"""
from __future__ import annotations

from datetime import datetime,timezone
from hashlib import sha256
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit

from autopilot.private_versioned_media_escrow import (
    ReviewRequiredStorageIntent,prepare_exact_private_escrow,
    escrow_once_and_readback,EscrowError,
)
from autopilot.test_private_versioned_media_escrow import (
    CONFIG,fixture,
)
from autopilot.primary_claim_surface_docket import (
    make_unapproved_claim_surface_docket,
)

def main()->None:
    import boto3
    from botocore.config import Config

    # Never permit this hosted integration client to hit actual AWS or any
    # external S3-compatible service even if someone sets ambient credentials.
    endpoint=os.environ.get("FLOWMINUTE_LOCAL_MOTO_ENDPOINT","http://127.0.0.1:5000")
    parts=urlsplit(endpoint)
    if (parts.scheme!="http" or parts.hostname not in ("127.0.0.1","localhost")
            or parts.port!=5000 or parts.path not in ("","/")
            or parts.username is not None or parts.password is not None):
        raise RuntimeError("B3d4c2d1 emulator MUST be local to hosted GitHub CI")
    if os.environ.get("CI")!="true":
        raise RuntimeError("No local laptop or production S3 use allowed in this test")
    client=boto3.client(
        "s3",
        endpoint_url="http://127.0.0.1:5000",
        region_name=CONFIG.region,
        aws_access_key_id="fake_ephemeral_CI_access_key_only",
        aws_secret_access_key="fake_ephemeral_CI_secret_only",
        config=Config(
            retries={"total_max_attempts":1},
            s3={"addressing_style":"path"},
            connect_timeout=10,read_timeout=15,
        ),
    )
    client.create_bucket(
        Bucket=CONFIG.bucket,ObjectLockEnabledForBucket=True,
    )
    client.put_bucket_versioning(
        Bucket=CONFIG.bucket,
        VersioningConfiguration={"Status":"Enabled"},
    )
    # Intentionally DO NOT set or change a global default retention on a
    # real AWS bucket. These synthetic object PUTs supply 7-day explicit
    # COMPLIANCE request shape to Moto's temporary bucket only.
    status=client.get_bucket_versioning(Bucket=CONFIG.bucket)
    if status.get("Status")!="Enabled":
        raise RuntimeError("Emulator bucket is not versioned")
    output=[]
    with TemporaryDirectory(prefix="flowminute-ci-moto-escrow-") as tmp:
        for slot in ("short_am","long","short_pm"):
            src=Path(tmp)/slot
            src.mkdir(mode=0o700)
            story,folder,report=fixture(src,slot)
            plan=prepare_exact_private_escrow(
                story=story,folder=folder,producer_report=report,config=CONFIG,
            )
            source=make_unapproved_claim_surface_docket(slot)
            if plan["unapproved_claim_surface_docket_sha256"]!=source["unapproved_claim_surface_docket_sha256"]:
                raise RuntimeError("Original full source docket not tied to physical synthetic blob set")
            receipt=escrow_once_and_readback(
                s3=client,plan=plan,folder=folder,config=CONFIG,
                now=datetime.now(timezone.utc),
            )
            if (receipt["release_authorized"] is not False
                    or receipt["actual_independent_factual_voice_rights_and_owner_review"] is not False
                    or receipt["all_object_versions_independently_read_back"] is not True
                    or receipt["original_versioned_object_count"] not in (43,127)):
                raise RuntimeError("Unexpected fake source rights/complete asset escrow state")
            # Verify the manifest physically exists at its pinned VERSION,
            # without leaking contents of any actual private media object.
            key=(CONFIG.prefix+"/"+story["episode_id"]+
                 "/escrow-manifest/"+plan["unapproved_escrow_plan_sha256"]+".json")
            head=client.head_object(
                Bucket=CONFIG.bucket,Key=key,
                VersionId=receipt["final_manifest_s3_version_id"],
                ChecksumMode="ENABLED",
            )
            if (head.get("ContentLength",0)<=200
                    or head.get("ObjectLockMode")!="COMPLIANCE"
                    or head.get("ServerSideEncryption")!="aws:kms"):
                raise RuntimeError("Not a version-specific checksum-retained final escrow manifest")
            output.append({
                "episode_id":story["episode_id"],
                "original_synthetic_versioned_object_count":
                    receipt["original_versioned_object_count"],
                "all_version_specific_S3_GET_sha256_verified":True,
                "final_manifest_sha256":receipt["unapproved_manifest_sha256"],
                "final_manifest_s3_version_id_sha256":
                    sha256(receipt["final_manifest_s3_version_id"].encode()).hexdigest(),
                "final_manifest_object_lock_compliance_mock_verified":True,
                "source_claim_docket_sha256":
                    receipt["exact_source_claim_surface_docket_sha256"],
                "real_aws_deployed":False,
                "actual_usable_video_uploaded":False,
                "real_iam_kms_encryption_verified":False,
                "real_owner_human_fact_rights_approval":False,
                "youtube_upload_enabled":False,
                "release_authorized":False,
            })
    if (
        len(output)!=3
        or sum(x["original_synthetic_versioned_object_count"] for x in output)!=213
        or len({x["final_manifest_sha256"] for x in output})!=3
        or len({x["source_claim_docket_sha256"] for x in output})!=3
    ):
        raise RuntimeError("Three distinct source-script-bound uploaded mock manifests missing")
    print("B3D4C2D1_LOCAL_MOTO_S3_HTTP_213_SYNTHETIC_BYTES_VERSIONED_IMMUTABLE_REQUESTS_NO_REAL_AWS",
          json.dumps({
              "status":"LOCAL_MOTO_ONLY_NOT_A_REAL_PRIVATE_CLOUD_DEPLOYMENT",
              "episode_reports":output,
              "synthetic_asset_object_count":213,
              "final_unapproved_manifest_count":3,
              "total_versioned_S3_emulator_objects":216,
              "source_html_or_real_videos_stored":False,
              "object_lock_legally_enforceable_on_real_aws":False,
              "real_cloud_billable_usage":False,
              "real_human_voice_rights_owner_approvals":False,
              "youtube_upload_enabled":False,
              "release_authorized":False,
          },sort_keys=True),flush=True)


if __name__=="__main__":
    main()
