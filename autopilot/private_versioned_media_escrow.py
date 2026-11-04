"""B3d4c2d1: S3-compatible immutable-version media ESCROW adapter (NO PUBLISH).

Production-capable S3 request shapes, but NO AWS clients/credentials/accounts
created here; an independent owner-authorized process must supply the client,
private bucket, region, KMS key and retention decision. In public CI this
module is exercised only with invented media bytes, fake S3 or a LOCAL emulator.

Every exact physical original MP4/WAV/SRT/thumb/scene asset is rehashed
against B3d4c2c3c's source-script-and-visible-claims docket. Uploads:
  - no overwrite (IfNoneMatch='*'), SHA256 checksum header
  - versioned object, SSE-KMS key, per-version Object Lock COMPLIANCE retention
  - fixed expected metadata and independent exact VersionId GET/readback
  - final manifest written LAST only when every original byte verified
  - NEVER retry after uncertain PutObject/GET outcome. No delete/rollback.
COMPLIANCE retention can be irreversibly expensive: NEVER call on real AWS
without owner approval of terms, budget, region, duration and Object Lock.

Even a complete simulated escrow is NOT factual/voice/rightsholder/editorial
approval, actual cloud identity/IAM protection, a live private backup, or a
permission to upload/schedule in YouTube.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import io
import json
import re
import stat
from pathlib import Path
from typing import Mapping

from autopilot.primary_sourced_storyboards import (
    build_story, canonical, require_exact_draft,
)
from autopilot.primary_claim_surface_docket import (
    make_unapproved_claim_surface_docket, require_exact_unapproved_claim_surface_docket,
)
from autopilot.full_topic_narrated_pack import _exact_assets

STATUS = "S3_VERSIONED_SYNTHETIC_OR_APPROVAL_PENDING_ESCROW_NO_RELEASE"
HEX = re.compile(r"[0-9a-f]{64}\Z")
EPISODE = re.compile(r"fm_[0-9]{8}_(?:short_am|long|short_pm)\Z")
BUCKET = re.compile(r"[a-z0-9][a-z0-9.-]{3,62}\Z")
PREFIX = re.compile(r"[a-z0-9][a-z0-9_-]*(?:/[a-z0-9][a-z0-9_-]*)*\Z")
REGION = re.compile(r"[a-z]{2}-[a-z]+-[1-9][0-9]?\Z")
VERSION = re.compile(r"[A-Za-z0-9._+/~=-]{1,128}\Z")
ACCOUNT = re.compile(r"[0-9]{12}\Z")
MAX_BODY = 300_000_000
MAX_MANIFEST = 150_000
MIME = {
    ".mp4":"video/mp4",
    ".wav":"audio/wav",
    ".srt":"application/x-subrip",
    ".png":"image/png",
    ".ffconcat":"text/plain",
    ".json":"application/json",
}


class EscrowError(ValueError):
    """No owner-release authority; ambiguous object write MUST NOT retry."""


@dataclass(frozen=True)
class ReviewRequiredStorageIntent:
    """CANNOT prove independent owner approval or existence of these resources.

    Values must be externally provisioned and reviewed before live use.
    This is NOT an account configuration loader or a client constructor.
    """
    bucket: str
    region: str
    kms_key_arn: str
    prefix: str = "flowminute/unapproved-media-v1"
    retention_days: int = 7


def _utc(value:datetime)->datetime:
    if not isinstance(value,datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise EscrowError("Versioned escrow needs independent aware clock")
    return value.astimezone(timezone.utc)


def _sha(raw:bytes)->str:
    return sha256(raw).hexdigest()


def _validate_config(config:ReviewRequiredStorageIntent)->None:
    if (not isinstance(config,ReviewRequiredStorageIntent)
            or not BUCKET.fullmatch(config.bucket)
            or not PREFIX.fullmatch(config.prefix)
            or not REGION.fullmatch(config.region)
            or type(config.retention_days) is not int
            or not 1<=config.retention_days<=30
            or not isinstance(config.kms_key_arn,str)):
        raise EscrowError("Invalid proposed private owner-selected bucket/region/retention")
    m=re.fullmatch(
        r"arn:aws:kms:([a-z]{2}-[a-z]+-[1-9][0-9]?):([0-9]{12}):"
        r"key/([0-9a-fA-F]{8}-[0-9a-fA-F-]{27,40})",
        config.kms_key_arn,
    )
    if not m or m.group(1)!=config.region or not ACCOUNT.fullmatch(m.group(2)):
        raise EscrowError("Untrusted KMS region or specific customer-key ARN")


def _content_type(name:str)->str:
    for suffix,mime in MIME.items():
        if name.endswith(suffix):
            return mime
    raise EscrowError("Unrecognized video/source evidence asset extension")


def _validate_asset_name(name:str)->None:
    if (not isinstance(name,str)
            or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{3,100}",name)
            or ".." in name or "/" in name or "\\" in name):
        raise EscrowError("No path traversal or unreviewed asset name")


def _episode_day(story:dict)->str:
    episode=story["episode_id"]
    if not EPISODE.fullmatch(episode):
        raise EscrowError("Invalid original episode ID")
    raw=episode[3:11]
    return raw[:4]+"-"+raw[4:6]+"-"+raw[6:8]


def _read_exact_file(folder:Path,item:dict)->bytes:
    name=item["name"]
    _validate_asset_name(name)
    path=folder/name
    if folder.is_symlink() or not folder.is_dir() or path.is_symlink():
        raise EscrowError("Symbolic link or missing owner media folder")
    try:
        state=path.stat()
    except OSError as exc:
        raise EscrowError("Missing original full media file") from exc
    if (not stat.S_ISREG(state.st_mode)
            or type(item["bytes"]) is not int
            or not 20<item["bytes"]<=MAX_BODY
            or state.st_size!=item["bytes"]
            or not HEX.fullmatch(item["sha256"])):
        raise EscrowError("Changed exact media sizes or unsafe asset type")
    try:
        # In production use source-clamped one-object reads rather than a
        # multiput retry. Max 300 MB, no arbitrary untrusted source paths.
        raw=path.read_bytes()
    except OSError as exc:
        raise EscrowError("Original asset could not be read") from exc
    if len(raw)!=item["bytes"] or _sha(raw)!=item["sha256"]:
        raise EscrowError("Original video/source asset bytes changed")
    return raw


def prepare_exact_private_escrow(
    *,story:dict,folder:Path,producer_report:dict,
    config:ReviewRequiredStorageIntent,
) -> dict:
    """Rebuild each source assertion and physical byte, produce no cloud call."""
    _validate_config(config)
    require_exact_draft(story)
    day=_episode_day(story)
    source_docket=make_unapproved_claim_surface_docket(story["slot"],day)
    require_exact_unapproved_claim_surface_docket(source_docket,story["slot"],day)
    if source_docket["source_draft_sha256"]!=story["draft_sha256"]:
        raise EscrowError("Claim dossier not for final original story")
    if (not isinstance(producer_report,dict)
            or producer_report.get("actual_full_encoded_h264_aac_with_captions_and_animation") is not True
            or producer_report.get("actual_narration_text_and_srt_matched") is not True
            or producer_report.get("original_source_story_draft_sha256")!=story["draft_sha256"]
            or producer_report.get("release_authorized") is not False
            or producer_report.get("youtube_upload_enabled") is not False):
        raise EscrowError("No observed valid unapproved full-media report")
    files=_exact_assets(Path(folder),story,producer_report)
    if (files.get("release_authorized") is not False
            or files.get("all_spoken_visual_thumbnail_title_description_docket_sha256")
            !=source_docket["unapproved_claim_surface_docket_sha256"]
            or files.get("asset_count")!=7+story["scene_count"]*6):
        raise EscrowError("Physical exact media/source evidence inventory mismatch")
    entries=[]
    for row in files["exact_file_hashes_and_sizes"]:
        name=row["name"]
        _validate_asset_name(name)
        _read_exact_file(Path(folder),row)
        key=(config.prefix+"/"+story["episode_id"]+
             "/"+row["sha256"]+"/"+name)
        entries.append({
            "name":name,"key":key,"sha256":row["sha256"],
            "bytes":row["bytes"],"content_type":_content_type(name),
        })
    if len(entries)!=files["asset_count"] or len({x["key"] for x in entries})!=len(entries):
        raise EscrowError("Nonunique original media escrow object keys")
    binding={
        "schema_version":1,
        "status":STATUS,
        "episode_id":story["episode_id"],
        "source_draft_sha256":story["draft_sha256"],
        "unapproved_claim_surface_docket_sha256":
            source_docket["unapproved_claim_surface_docket_sha256"],
        "original_producer_media_inventory_sha256":files["draft_asset_inventory_sha256"],
        "storage_backend":"AWS_S3_INTERFACE_NOT_PROVISIONED_BY_THIS_MODULE",
        "bucket":config.bucket,"region":config.region,
        "customer_kms_key_arn":config.kms_key_arn,
        "object_key_prefix":config.prefix,
        "planned_compliance_retention_days":config.retention_days,
        "objects":entries,"object_count":len(entries),
        "independently_authenticated_real_owner_and_workload":False,
        "real_human_fact_rights_disclosure_and_full_watch_approvals":False,
        "production_bucket_iam_versioning_and_lock_verified":False,
        "actual_public_source_full_body_privately_archived":False,
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }
    if len(canonical(binding))>MAX_MANIFEST:
        raise EscrowError("Oversize immutable-media escrow candidate manifest")
    return {**binding,"unapproved_escrow_plan_sha256":_sha(canonical(binding))}


def _check_plan(plan:dict)->None:
    if not isinstance(plan,dict):
        raise EscrowError("Missing exact original asset escrow plan")
    b={k:v for k,v in plan.items() if k!="unapproved_escrow_plan_sha256"}
    if (plan.get("unapproved_escrow_plan_sha256")!=_sha(canonical(b))
            or b.get("status")!=STATUS or b.get("release_authorized") is not False
            or b.get("youtube_upload_enabled") is not False
            or b.get("real_human_fact_rights_disclosure_and_full_watch_approvals") is not False
            or b.get("independently_authenticated_real_owner_and_workload") is not False
            or b.get("production_bucket_iam_versioning_and_lock_verified") is not False
            or b.get("actual_public_source_full_body_privately_archived") is not False
            or not isinstance(b.get("objects"),list)
            or b.get("object_count")!=len(b["objects"])
            or not b["objects"]):
        raise EscrowError("Manipulated owner/media escrow scope or fake approval")


def _remote_verify(s3,*,bucket:str,key:str,version:str,
                   sha_hex:str,count:int,kms_arn:str,
                   retain_until:datetime,source_docket:str,
                   episode:str)->dict:
    """Verify immutable exact VERSION, not just current key/ETag."""
    if not VERSION.fullmatch(version):
        raise EscrowError("S3 did not prove a concrete non-null version")
    try:
        head=s3.head_object(Bucket=bucket,Key=key,VersionId=version,
                            ChecksumMode="ENABLED")
        get=s3.get_object(Bucket=bucket,Key=key,VersionId=version,
                          ChecksumMode="ENABLED")
        raw=get["Body"].read(count+1)
        get["Body"].close()
    except Exception as exc:
        raise EscrowError("Ambiguous versioned readback; DO NOT retry upload") from exc
    expected_b64=base64.b64encode(bytes.fromhex(sha_hex)).decode("ascii")
    metadata=head.get("Metadata",{})
    if (not isinstance(raw,bytes) or len(raw)!=count or _sha(raw)!=sha_hex
            or head.get("VersionId")!=version or get.get("VersionId")!=version
            or head.get("ContentLength")!=count
            or head.get("ServerSideEncryption")!="aws:kms"
            or head.get("SSEKMSKeyId")!=kms_arn
            or head.get("ObjectLockMode")!="COMPLIANCE"
            or "ObjectLockRetainUntilDate" not in head
            or _utc(head["ObjectLockRetainUntilDate"])<retain_until-timedelta(seconds=2)
            or metadata.get("sha256")!=sha_hex
            or metadata.get("source-docket")!=source_docket
            or metadata.get("episode")!=episode
            or head.get("ChecksumSHA256") not in (None,expected_b64)
            or get.get("ChecksumSHA256") not in (None,expected_b64)):
        raise EscrowError("S3 versioned checksum/KMS/retention/source claims not proved")
    return {
        "object_version_id":version,
        "key":key,
        "sha256":sha_hex,
        "exact_bytes":count,
        "s3_version_id_readback_passed":True,
        "sha256_entire_returned_object_confirmed":True,
        "object_lock_compliance_mode_returned":True,
        "specific_customer_kms_key_returned":True,
    }


def _one_put(s3,*,config:ReviewRequiredStorageIntent,key:str,raw:bytes,
             source_docket:str,episode:str,retain_until:datetime,
             mime:str)->dict:
    sha_hex=_sha(raw)
    checksum=base64.b64encode(bytes.fromhex(sha_hex)).decode("ascii")
    try:
        # Never call any delete, copy, overwrite without precondition,
        # multipart or implicit retry function. A remote network timeout
        # leaves the submitted object UNCERTAIN until operator audit.
        response=s3.put_object(
            Bucket=config.bucket,Key=key,Body=raw,
            ContentLength=len(raw),ContentType=mime,
            IfNoneMatch="*",
            ChecksumSHA256=checksum,
            ServerSideEncryption="aws:kms",SSEKMSKeyId=config.kms_key_arn,
            ObjectLockMode="COMPLIANCE",
            ObjectLockRetainUntilDate=retain_until,
            Metadata={
                "sha256":sha_hex,
                "source-docket":source_docket,
                "episode":episode,
            },
        )
    except Exception as exc:
        raise EscrowError("Storage write failed/uncertain: do NOT retry; audit version IDs") from exc
    version=response.get("VersionId")
    if not isinstance(version,str):
        raise EscrowError("Object write uncertain without a real S3 version ID")
    return _remote_verify(
        s3,bucket=config.bucket,key=key,version=version,
        sha_hex=sha_hex,count=len(raw),
        kms_arn=config.kms_key_arn,
        retain_until=retain_until,
        source_docket=source_docket,episode=episode,
    )


def escrow_once_and_readback(*,s3,plan:dict,
                             folder:Path,
                             config:ReviewRequiredStorageIntent,
                             now:datetime) -> dict:
    """Only an external owner-approved caller may supply a REAL S3 client.

    Test code MUST pass an isolated local fake/emulator. A forged settings
    object is NOT evidence of real permission or genuine owner identity.
    Do not expose this method to a public PR workflow with real AWS creds.
    """
    _validate_config(config)
    _check_plan(plan)
    # Botocore can RETRY PUT on its own after an ambiguous socket error.
    # A real boto3 client MUST explicitly disable all SDK automatic retries;
    # test-only in-memory fakes have no botocore config to inspect.
    sdk_config=getattr(getattr(s3,"meta",None),"config",None)
    if sdk_config is not None:
        retry_policy=getattr(sdk_config,"retries",{}) or {}
        if retry_policy.get("total_max_attempts")!=1:
            raise EscrowError("SDK PutObject automatic retries must be disabled")
    at=_utc(now)
    if (plan["bucket"]!=config.bucket or plan["region"]!=config.region
            or plan["customer_kms_key_arn"]!=config.kms_key_arn
            or plan["object_key_prefix"]!=config.prefix
            or plan["planned_compliance_retention_days"]!=config.retention_days
            or not EPISODE.fullmatch(plan["episode_id"])):
        raise EscrowError("Frozen proposed owner storage scope changed")
    source=plan["unapproved_claim_surface_docket_sha256"]
    episode=plan["episode_id"]
    # Local source is still part of the same valid exact authored story;
    # completely recompute the original physical inventory before ANY put.
    slot=episode[12:]
    story=build_story(slot,_episode_day({"episode_id":episode}))
    if story["draft_sha256"]!=plan["source_draft_sha256"]:
        raise EscrowError("Original narrative changed since escrow preflight")
    source_check=make_unapproved_claim_surface_docket(slot,_episode_day(story))
    if source_check["unapproved_claim_surface_docket_sha256"]!=source:
        raise EscrowError("Original complete factual/visible narrative source docket changed")
    if plan["object_count"]!=7+story["scene_count"]*6:
        raise EscrowError("No complete source-aligned media file set before private escrow")
    expected_prefix=config.prefix+"/"+episode+"/"
    all_files={p.name for p in Path(folder).iterdir()}
    if all_files!={x["name"] for x in plan["objects"]}:
        raise EscrowError("Unexpected/missing original files at escrow write")
    for item in plan["objects"]:
        if not item["key"].startswith(expected_prefix) or not item["key"].endswith(
            "/"+item["sha256"]+"/"+item["name"]
        ):
            raise EscrowError("Altered source file destination in escrow plan")
        _read_exact_file(Path(folder),item)
    retain_until=at+timedelta(days=config.retention_days)
    receipts=[]
    for item in plan["objects"]:
        original=_read_exact_file(Path(folder),item)
        receipt=_one_put(
            s3,config=config,key=item["key"],raw=original,
            source_docket=source,episode=episode,retain_until=retain_until,
            mime=item["content_type"],
        )
        receipts.append(receipt)
    if len(receipts)!=plan["object_count"]:
        raise EscrowError("Incomplete object storage; do not write final manifest")
    frozen={
        "schema_version":1,
        "status":"ALL_EXACT_ORIGINAL_VERSIONED_OBJECTS_STORED_UNAPPROVED",
        "episode_id":episode,
        "unapproved_escrow_plan_sha256":plan["unapproved_escrow_plan_sha256"],
        "original_media_inventory_sha256":plan["original_producer_media_inventory_sha256"],
        "source_claim_docket_sha256":source,
        "object_versions":receipts,
        "object_count":len(receipts),
        "real_owner_workload_iam_and_cost_terms_confirmed":False,
        "real_review_and_final_playback_completed":False,
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }
    raw=canonical(frozen)
    if len(raw)>MAX_MANIFEST:
        raise EscrowError("Evidence receipt list beyond bounded manifest")
    name=plan["unapproved_escrow_plan_sha256"]+".json"
    key=config.prefix+"/"+episode+"/"+"escrow-manifest/"+name
    # Distinct source report manifest is written only after ALL original
    # objects have been checked with their immutable exact VersionId.
    frozen_receipt=_one_put(
        s3,config=config,key=key,raw=raw,
        source_docket=source,episode=episode,
        retain_until=retain_until,mime="application/json",
    )
    return {
        "status":"STAGED_VERSIONED_PRIVATE_OBJECTS_AND_FINAL_UNAPPROVED_MANIFEST",
        "episode_id":episode,
        "escrow_plan_sha256":plan["unapproved_escrow_plan_sha256"],
        "original_versioned_object_count":len(receipts),
        "total_object_count_including_final_manifest":len(receipts)+1,
        "exact_source_bound_media_inventory_sha256":
            plan["original_producer_media_inventory_sha256"],
        "exact_source_claim_surface_docket_sha256":source,
        "unapproved_manifest_sha256":_sha(raw),
        "final_manifest_s3_version_id":frozen_receipt["object_version_id"],
        "all_object_versions_independently_read_back":True,
        "all_object_versions_compliance_retention_proved_by_adapter":True,
        "real_cloud_account_identity_and_bucket_iam_verified":False,
        "real_owner_approved_storage_cost_and_retention":False,
        "actual_independent_factual_voice_rights_and_owner_review":False,
        "real_cloud_backup_and_cross_region_restore_tested":False,
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }
