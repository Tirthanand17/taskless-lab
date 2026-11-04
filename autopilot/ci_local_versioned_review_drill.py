"""B3d4c2d2: real boto3-to-LOCAL-Moto version-specific reads and fake signers.

ALL media is invented NONPLAYABLE fixture bytes and deleted at job exit.
No GitHub secret, live cloud endpoint, real owner, or YouTube use. Moto cannot
prove real S3 Object Lock, retained persistent bytes, IAM, KMS or data rights.
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
    prepare_exact_private_escrow,escrow_once_and_readback,
)
from autopilot.version_pinned_review_boundary import (
    reconstruct_version_bound_review_context, verify_version_bound_mock_reviews,
    mock_registry_digest,
)
from autopilot.test_version_pinned_review_boundary import (
    NOW,EXCLUDED,register_fake_people,fake_signed_reviews,
)
from autopilot.test_private_versioned_media_escrow import (
    CONFIG,fixture,
)


def main()->None:
    import boto3
    from botocore.config import Config

    endpoint=os.environ.get("FLOWMINUTE_LOCAL_MOTO_ENDPOINT","")
    parsed=urlsplit(endpoint)
    if (
        os.environ.get("CI")!="true"
        or parsed.scheme!="http" or parsed.hostname not in ("127.0.0.1","localhost")
        or parsed.port!=5000 or parsed.username is not None
        or parsed.password is not None or parsed.path not in ("","/")
        or parsed.query or parsed.fragment
    ):
        raise RuntimeError("Only localhost Moto emulator on hosted CI may be used")
    s3=boto3.client(
        "s3",
        endpoint_url="http://127.0.0.1:5000",
        region_name=CONFIG.region,
        aws_access_key_id="fake_ci_review_test_key",
        aws_secret_access_key="fake_ci_review_test_secret",
        config=Config(retries={"total_max_attempts":1},
                      s3={"addressing_style":"path"},
                      connect_timeout=10,read_timeout=12),
    )
    s3.create_bucket(Bucket=CONFIG.bucket,ObjectLockEnabledForBucket=True)
    s3.put_bucket_versioning(
        Bucket=CONFIG.bucket,VersioningConfiguration={"Status":"Enabled"}
    )
    registry,private=register_fake_people()
    root=mock_registry_digest(registry)
    output=[]
    with TemporaryDirectory(prefix="flowminute-version-review-fake-media-") as tmp:
        for slot,runtime in (("short_am",61.79),("long",219.12),("short_pm",60.02)):
            episode_root=Path(tmp)/slot
            episode_root.mkdir(mode=0o700)
            story,folder,producer=fixture(episode_root,slot)
            plan=prepare_exact_private_escrow(
                story=story,folder=folder,producer_report=producer,config=CONFIG,
            )
            receipt=escrow_once_and_readback(
                s3=s3,plan=plan,folder=folder,
                config=CONFIG,now=datetime.now(timezone.utc),
            )
            context=reconstruct_version_bound_review_context(
                s3=s3,plan=plan,escrow_receipt=receipt,
                config=CONFIG,runtime_seconds=runtime,
                now=datetime.now(timezone.utc),
            )
            # The same seven synthetic identities are role-separated;
            # signatures are bound to different per-video context roots.
            signed=fake_signed_reviews(
                context,registry,private,now=datetime.now(timezone.utc),
            )
            reviewed=verify_version_bound_mock_reviews(
                context=context,
                expected_context_sha256=context["version_bound_review_context_sha256"],
                registry=registry,expected_external_registry_sha256=root,
                receipts=signed,
                excluded_agent_editor_and_publisher_ids=EXCLUDED,
                now=datetime.now(timezone.utc),
            )
            if (
                reviewed["synthetic_valid_role_count"]!=7
                or not reviewed["all_synthetic_signature_shapes_valid"]
                or reviewed["external_actual_human_reviewer_identities_authenticated"] is not False
                or reviewed["real_owner_key_enrolled_from_private_authority"] is not False
                or reviewed["release_authorized"] is not False
                or context["object_count"]!=(127 if slot=="long" else 43)
            ):
                raise RuntimeError("Fake S3 versions or seven mock editorial reviewer signatures not verified")
            critical=context["critical_media_version_pins"]
            if set(critical)!={
                "UNAPPROVED_FULL_EDUCATION_TEST.mp4",
                "original_voice.wav",
                "scene_captions.srt",
                "UNAPPROVED_THUMBNAIL_TEST.png",
            }:
                raise RuntimeError("S3 review missed critical exact physical asset versions")
            output.append({
                "episode_id":story["episode_id"],
                "actual_boto3_http_to_local_moto_get_version_calls_passed":True,
                "exact_original_object_version_count":context["object_count"],
                "escrow_manifest_version_id_sha256":sha256(
                    context["pinned_manifest_version_id"].encode()
                ).hexdigest(),
                "source_claim_docket_sha256":context["source_claim_docket_sha256"],
                "all_asset_version_and_full_body_sha256":
                    context["all_version_specific_assets_sha256"],
                "version_pinned_review_context_sha256":
                    context["version_bound_review_context_sha256"],
                "synthetic_ed25519_role_signature_count":
                    reviewed["synthetic_valid_role_count"],
                "real_independent_human_editorial_or_rights_review":False,
                "real_authenticated_owner_and_private_cloud":False,
                "real_full_video_or_agency_source_content_stored":False,
                "release_authorized":False,
                "youtube_upload_enabled":False,
            })
    if (
        len(output)!=3
        or sum(x["exact_original_object_version_count"] for x in output)!=213
        or sum(x["synthetic_ed25519_role_signature_count"] for x in output)!=21
        or len({x["version_pinned_review_context_sha256"] for x in output})!=3
        or len({x["source_claim_docket_sha256"] for x in output})!=3
    ):
        raise RuntimeError("Missing unique three-video 213 version 21 fake review structure")
    print("B3D4C2D2_213_LOCAL_MOTO_VERSIONS_AND_21_SYNTHETIC_SIGNATURES_NOT_REAL_APPROVAL",
          json.dumps({
              "status":"LOCAL_EMULATOR_VERSION_READBACK_SYNTHETIC_REVIEW_ONLY",
              "episodes":output,
              "synthetic_bytes_read_from_s3_version_count":213,
              "synthetic_unsigned_escrow_manifest_versions_read":3,
              "synthetic_role_signatures_verified":21,
              "real_owner_approved_cloud_deployed":False,
              "actual_human_editorial_rights_source_and_full_watch":False,
              "source_html_or_real_video_persisted":False,
              "actual_youtube_remote_videos_uploaded":0,
              "release_authorized":False,
          },sort_keys=True),flush=True)


if __name__=="__main__":
    main()
