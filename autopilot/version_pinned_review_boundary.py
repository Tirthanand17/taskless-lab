"""B3d4c2d2: independently read S3 versioned media, bind mock reviews (NO RELEASE).

No production S3 client, identity enrollment, cloud provisioner, uploader or
signing key is created here. The only signer keys used by the GitHub tests are
synthetic. S3 GET/HEAD verify the exact bytes and immutable VERSION of EVERY
object, then Ed25519 verifies seven externally supplied MOCK reviewer records
against a SHA of the complete version-pinned package.

Even seven valid Ed25519 signatures do not prove any human reviewed facts,
copyright, voices, disclosure, visual semantics, original channel material,
or a real playback. The function NEVER authorizes real publication.
"""
from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import math
import re
from typing import Mapping, Sequence

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from autopilot.mock_final_editorial_review import ROLES
from autopilot.primary_sourced_storyboards import build_story,canonical
from autopilot.primary_claim_surface_docket import make_unapproved_claim_surface_docket
from autopilot.private_versioned_media_escrow import (
    ReviewRequiredStorageIntent, _check_plan, _validate_config, _utc,
    VERSION, MAX_MANIFEST, MAX_BODY,
)

STATUS="VERSION_PINNED_SYNTHETIC_EDITORIAL_BINDING_NOT_REAL_HUMAN_APPROVAL"
PURPOSE="FLOWMINUTE_B3D4C2D2_VERSION_PINNED_SYNTHETIC_REVIEWS_V1"
DOMAIN=b"FLOWMINUTE_B3D4C2D2_DOMAIN_SEPARATED_MOCK_ONLY\x00"
ID=re.compile(r"[a-z][a-z0-9_]{2,63}\Z")
HEX=re.compile(r"[0-9a-f]{64}\Z")
MAX_NOTES=800
MAX_AGE=timedelta(hours=24)
MAX_VALIDITY=timedelta(hours=36)


class VersionedReviewError(ValueError):
    """An exact version/identity/reviewer claim cannot be authenticated."""


@dataclass(frozen=True)
class ExternalMockReviewer:
    reviewer_id: str
    key_id: str
    role: str
    public_ed25519_b64: str
    active: bool = True


@dataclass(frozen=True)
class VersionBoundMockReviewClaim:
    purpose: str
    episode_id: str
    context_sha256: str
    role: str
    role_binding_sha256: str
    reviewer_id: str
    key_id: str
    receipt_id: str
    decision: str
    notes: str
    signed_at_utc: str
    expires_at_utc: str
    claimed_full_watch_seconds: int = 0
    synthetic_disclosure_choice: str = "NOT_DECIDED"


@dataclass(frozen=True)
class DetachedVersionBoundMockReview:
    claim: VersionBoundMockReviewClaim
    signature_ed25519_b64: str


def _sha(value:bytes)->str:
    return sha256(value).hexdigest()


def _at(value:str)->datetime:
    if not isinstance(value,str) or len(value)>44:
        raise VersionedReviewError("Invalid signed reviewer timestamp")
    try:
        d=datetime.fromisoformat(value)
    except (TypeError,ValueError) as exc:
        raise VersionedReviewError("Invalid review datetime") from exc
    if d.tzinfo is None or d.utcoffset() is None:
        raise VersionedReviewError("Naive reviewer clock")
    return d.astimezone(timezone.utc)


def _duplicate_denied(pairs:list[tuple[str,object]])->dict:
    result={}
    for key,value in pairs:
        if key in result:
            raise VersionedReviewError("Duplicate JSON member in stored original manifest")
        result[key]=value
    return result


def _strict_json(raw:bytes)->dict:
    if not isinstance(raw,bytes) or not 100<=len(raw)<=MAX_MANIFEST:
        raise VersionedReviewError("Invalid actual escrow manifest bytes")
    try:
        result=json.loads(
            raw.decode("utf-8",errors="strict"),
            object_pairs_hook=_duplicate_denied,
            parse_constant=lambda _: (_ for _ in ()).throw(
                VersionedReviewError("Nonfinite manifest number")
            ),
        )
    except (UnicodeError,json.JSONDecodeError,ValueError) as exc:
        raise VersionedReviewError("Malformed version-pinned escrow manifest") from exc
    if not isinstance(result,dict) or canonical(result)!=raw:
        raise VersionedReviewError("Stored escrow manifest must be exact canonical bytes")
    return result


def _version_bytes(s3,*,bucket:str,key:str,version:str,
                   expected_sha:str,count:int,config:ReviewRequiredStorageIntent,
                   docket_sha:str,episode_id:str,now:datetime)->bytes:
    """Actual read-only HEAD + GET for specifically addressed S3 version."""
    if (not isinstance(version,str) or not VERSION.fullmatch(version)
            or version=="null" or not isinstance(key,str) or not key.startswith(
                config.prefix+"/"+episode_id+"/"
            ) or not isinstance(count,int) or isinstance(count,bool)
            or not 30<=count<=MAX_BODY or not isinstance(expected_sha,str)
            or not HEX.fullmatch(expected_sha)):
        raise VersionedReviewError("Unscoped immutable object-version readback")
    try:
        head=s3.head_object(
            Bucket=bucket,Key=key,VersionId=version,ChecksumMode="ENABLED",
        )
        get=s3.get_object(
            Bucket=bucket,Key=key,VersionId=version,ChecksumMode="ENABLED",
        )
        try:
            raw=get["Body"].read(count+1)
        finally:
            get["Body"].close()
    except Exception as exc:
        raise VersionedReviewError("Read-only exact-version HTTP check failed, no approval") from exc
    checksum=base64.b64encode(bytes.fromhex(expected_sha)).decode("ascii")
    meta=head.get("Metadata",{})
    try:
        expiry=_utc(head["ObjectLockRetainUntilDate"])
    except (KeyError,TypeError,ValueError) as exc:
        raise VersionedReviewError("No independently fetched retained ObjectLock version") from exc
    if (
        type(raw) is not bytes or len(raw)!=count
        or _sha(raw)!=expected_sha
        or head.get("VersionId")!=version or get.get("VersionId")!=version
        or head.get("ContentLength")!=count
        or head.get("ServerSideEncryption")!="aws:kms"
        or head.get("SSEKMSKeyId")!=config.kms_key_arn
        or head.get("ObjectLockMode")!="COMPLIANCE"
        or expiry<=now
        or head.get("ChecksumSHA256") not in (None,checksum)
        or get.get("ChecksumSHA256") not in (None,checksum)
        or meta.get("sha256")!=expected_sha
        or meta.get("source-docket")!=docket_sha
        or meta.get("episode")!=episode_id
    ):
        raise VersionedReviewError("Object version failed SHA/KMS/lock/source-bound integrity")
    return raw


def reconstruct_version_bound_review_context(
    *,s3,plan:dict,escrow_receipt:dict,config:ReviewRequiredStorageIntent,
    runtime_seconds:float,now:datetime,
)->dict:
    """Recompute source, fetch exact stored final manifest AND EVERY asset version.

    Tests use fake/Moto clients only. Rebuilt source and a caller-pinned root
    alone are NOT an independently trusted external owner or source reviewer.
    """
    at=_utc(now)
    _validate_config(config)
    _check_plan(plan)
    if (not isinstance(escrow_receipt,dict)
            or escrow_receipt.get("release_authorized") is not False
            or escrow_receipt.get("youtube_upload_enabled") is not False
            or escrow_receipt.get("real_cloud_account_identity_and_bucket_iam_verified") is not False
            or escrow_receipt.get("actual_independent_factual_voice_rights_and_owner_review") is not False
            or escrow_receipt.get("escrow_plan_sha256")!=plan["unapproved_escrow_plan_sha256"]
            or escrow_receipt.get("exact_source_bound_media_inventory_sha256")!=plan["original_producer_media_inventory_sha256"]
            or escrow_receipt.get("exact_source_claim_surface_docket_sha256")!=plan["unapproved_claim_surface_docket_sha256"]
            or escrow_receipt.get("original_versioned_object_count")!=plan["object_count"]
            or escrow_receipt.get("total_object_count_including_final_manifest")!=plan["object_count"]+1
            or escrow_receipt.get("all_object_versions_independently_read_back") is not True
            or not isinstance(escrow_receipt.get("final_manifest_s3_version_id"),str)
            or not VERSION.fullmatch(escrow_receipt["final_manifest_s3_version_id"])
            or not HEX.fullmatch(escrow_receipt.get("unapproved_manifest_sha256",""))
            or plan["bucket"]!=config.bucket
            or plan["region"]!=config.region
            or plan["customer_kms_key_arn"]!=config.kms_key_arn
            or plan["planned_compliance_retention_days"]!=config.retention_days
            or plan["object_key_prefix"]!=config.prefix
            or not isinstance(runtime_seconds,(int,float))
            or isinstance(runtime_seconds,bool) or not math.isfinite(runtime_seconds)
            or not 30<=runtime_seconds<=400):
        raise VersionedReviewError("Escrow receipt or unreviewed playback scope forged")
    episode=plan["episode_id"]
    source_day=episode[3:7]+"-"+episode[7:9]+"-"+episode[9:11]
    slot=episode[12:]
    story=build_story(slot,source_day)
    docket=make_unapproved_claim_surface_docket(slot,source_day)
    if (story["draft_sha256"]!=plan["source_draft_sha256"]
            or docket["unapproved_claim_surface_docket_sha256"]!=plan["unapproved_claim_surface_docket_sha256"]
            or plan["object_count"]!=7+story["scene_count"]*6):
        raise VersionedReviewError("Source research or claim ledger changed since media render")

    version=escrow_receipt["final_manifest_s3_version_id"]
    manifest_key=(config.prefix+"/"+episode+"/escrow-manifest/"
                  +plan["unapproved_escrow_plan_sha256"]+".json")
    manifest_sha=escrow_receipt["unapproved_manifest_sha256"]
    if not HEX.fullmatch(manifest_sha):
        raise VersionedReviewError("Unpinned external manifest")
    # Get the exact immutable version via HEAD+GET; final manifest remains
    # UNAPPROVED and never grants publishing even if this succeeds.
    # Expected byte length comes from the exact first GET response's HEAD;
    # a subsequent VersionId GET checks it again by SHA and evidence headers.
    try:
        head=s3.head_object(Bucket=config.bucket,Key=manifest_key,
                            VersionId=version,ChecksumMode="ENABLED")
    except Exception as exc:
        raise VersionedReviewError("Pinned unapproved manifest version missing") from exc
    length=head.get("ContentLength")
    if type(length) is not int or not 100<=length<=MAX_MANIFEST:
        raise VersionedReviewError("Invalid version-pinned unapproved manifest size")
    raw=_version_bytes(
        s3,bucket=config.bucket,key=manifest_key,version=version,
        expected_sha=manifest_sha,count=length,config=config,
        docket_sha=docket["unapproved_claim_surface_docket_sha256"],
        episode_id=episode,now=at,
    )
    manifest=_strict_json(raw)
    if (
        manifest.get("schema_version")!=1
        or manifest.get("status")!="ALL_EXACT_ORIGINAL_VERSIONED_OBJECTS_STORED_UNAPPROVED"
        or manifest.get("episode_id")!=episode
        or manifest.get("unapproved_escrow_plan_sha256")!=plan["unapproved_escrow_plan_sha256"]
        or manifest.get("original_media_inventory_sha256")!=plan["original_producer_media_inventory_sha256"]
        or manifest.get("source_claim_docket_sha256")!=docket["unapproved_claim_surface_docket_sha256"]
        or manifest.get("object_count")!=plan["object_count"]
        or manifest.get("real_owner_workload_iam_and_cost_terms_confirmed") is not False
        or manifest.get("real_review_and_final_playback_completed") is not False
        or manifest.get("youtube_upload_enabled") is not False
        or manifest.get("release_authorized") is not False
        or not isinstance(manifest.get("object_versions"),list)
        or len(manifest["object_versions"])!=plan["object_count"]
    ):
        raise VersionedReviewError("Stored object manifest differs from original authoritative source")

    versions=[]
    seen_keys=set()
    seen_versions=set()
    for original,remote in zip(plan["objects"],manifest["object_versions"]):
        if (not isinstance(remote,dict)
                or remote.get("key")!=original["key"]
                or remote.get("sha256")!=original["sha256"]
                or remote.get("exact_bytes")!=original["bytes"]
                or remote.get("s3_version_id_readback_passed") is not True
                or remote.get("sha256_entire_returned_object_confirmed") is not True
                or remote.get("object_lock_compliance_mode_returned") is not True
                or remote.get("specific_customer_kms_key_returned") is not True):
            raise VersionedReviewError("Manifest contains swapped, unsigned or incomplete media version")
        key=remote["key"]
        v=remote.get("object_version_id")
        if key in seen_keys or not isinstance(v,str) or not VERSION.fullmatch(v) or (key,v) in seen_versions:
            raise VersionedReviewError("Versioned duplicate asset or missing object version")
        seen_keys.add(key)
        seen_versions.add((key,v))
        _version_bytes(
            s3,bucket=config.bucket,key=key,version=v,
            expected_sha=original["sha256"],count=original["bytes"],
            config=config,docket_sha=docket["unapproved_claim_surface_docket_sha256"],
            episode_id=episode,now=at,
        )
        versions.append({
            "name":original["name"],"key":key,"object_version_id":v,
            "sha256":original["sha256"],"bytes":original["bytes"],
        })
    if len(versions)!=plan["object_count"]:
        raise VersionedReviewError("Incomplete exact version proof")
    inventory_root=_sha(canonical(versions))
    critical={}
    for name in (
        "UNAPPROVED_FULL_EDUCATION_TEST.mp4","original_voice.wav",
        "scene_captions.srt","UNAPPROVED_THUMBNAIL_TEST.png",
    ):
        matches=[row for row in versions if row["name"]==name]
        if len(matches)!=1:
            raise VersionedReviewError("Missing exact full video/voice/SRT/thumbnail version")
        critical[name]=matches[0]
    base={
        "schema_version":1,
        "status":STATUS,
        "episode_id":episode,
        "timeslot_ist":story["time_ist"],
        "format":story["format"],
        "bucket":config.bucket,
        "kms_key_arn":config.kms_key_arn,
        "storage_region":config.region,
        "source_draft_sha256":story["draft_sha256"],
        "source_claim_docket_sha256":docket["unapproved_claim_surface_docket_sha256"],
        "source_claim_count":docket["claim_count"],
        "source_spoken_caption_cue_count":docket["exact_original_narration_sentence_cue_count"],
        "source_visible_spoken_metadata_surface_count":docket["exact_literal_text_surface_count"],
        "media_inventory_sha256":plan["original_producer_media_inventory_sha256"],
        "escrow_plan_sha256":plan["unapproved_escrow_plan_sha256"],
        "pinned_manifest_key":manifest_key,
        "pinned_manifest_version_id":version,
        "pinned_manifest_sha256":manifest_sha,
        "all_version_specific_assets_sha256":inventory_root,
        "object_count":len(versions),
        "critical_media_version_pins":critical,
        "expected_playback_seconds_claimed_not_human_observed":round(float(runtime_seconds),3),
        "actual_public_cloud_identity_or_kms_verified":False,
        "all_source_claims_independently_human_reviewed":False,
        "actual_full_playback_by_real_human_verified":False,
        "voice_image_music_rights_approved":False,
        "real_channel_owner_release_authorized":False,
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }
    return {**base,"version_bound_review_context_sha256":_sha(canonical(base))}


def mock_registry_digest(registry:Mapping[str,ExternalMockReviewer])->str:
    if not isinstance(registry,Mapping) or len(registry)!=len(ROLES):
        raise VersionedReviewError("Independent seven-role synthetic registry missing")
    ordered={}
    for rid,value in sorted(registry.items()):
        if not isinstance(value,ExternalMockReviewer) or value.reviewer_id!=rid:
            raise VersionedReviewError("Untrusted separately enrolled reviewer record")
        ordered[rid]=asdict(value)
    return _sha(canonical(ordered))


def verify_version_bound_mock_reviews(
    *,context:dict,expected_context_sha256:str,
    registry:Mapping[str,ExternalMockReviewer],
    expected_external_registry_sha256:str,
    receipts:Sequence[DetachedVersionBoundMockReview],
    excluded_agent_editor_and_publisher_ids:frozenset[str],
    now:datetime,
)->dict:
    """Verify synthetic cryptographic replay/fencing ONLY, never real human approval.

    External trusted IDs and anchor SHA are supplied independently in API
    shape, but public CI uses only FAKE keys/anchors generated in test memory.
    There is no authenticated external owner registry in this repository.
    """
    at=_utc(now)
    if (not isinstance(context,dict)
            or context.get("release_authorized") is not False
            or context.get("real_channel_owner_release_authorized") is not False
            or context.get("actual_public_cloud_identity_or_kms_verified") is not False
            or context.get("all_source_claims_independently_human_reviewed") is not False
            or context.get("actual_full_playback_by_real_human_verified") is not False
            or context.get("voice_image_music_rights_approved") is not False
            or context.get("youtube_upload_enabled") is not False
            or not HEX.fullmatch(context.get("version_bound_review_context_sha256",""))
            or not HEX.fullmatch(expected_context_sha256)
            or context["version_bound_review_context_sha256"]!=expected_context_sha256
            or _sha(canonical({
                k:v for k,v in context.items()
                if k!="version_bound_review_context_sha256"
            }))!=expected_context_sha256
            or not isinstance(excluded_agent_editor_and_publisher_ids,frozenset)
            or not excluded_agent_editor_and_publisher_ids
            or any(not ID.fullmatch(x) for x in excluded_agent_editor_and_publisher_ids)
            or not HEX.fullmatch(expected_external_registry_sha256)
            or mock_registry_digest(registry)!=expected_external_registry_sha256
            or not isinstance(receipts,(list,tuple))
            or len(receipts)>len(ROLES)):
        raise VersionedReviewError("Fake context, unanchored mock reviewer or fake owner status")
    checked_roles=set()
    checked_reviewer_ids=set()
    checked_key_ids=set()
    checked_public_keys=set()
    checked_receipts=set()
    unresolved=[]
    for record in receipts:
        if not isinstance(record,DetachedVersionBoundMockReview) or not isinstance(record.claim,VersionBoundMockReviewClaim):
            raise VersionedReviewError("Invalid detached mock reviewer receipt")
        c=record.claim
        if (
            c.purpose!=PURPOSE or c.episode_id!=context["episode_id"]
            or c.context_sha256!=expected_context_sha256
            or c.role not in ROLES or not isinstance(c.role_binding_sha256,str)
            or c.role_binding_sha256!=_sha(canonical({
                "purpose":PURPOSE,"role":c.role,
                "version_bound_review_context_sha256":expected_context_sha256,
            }))
            or not ID.fullmatch(c.reviewer_id) or not ID.fullmatch(c.key_id)
            or not ID.fullmatch(c.receipt_id)
            or c.decision not in ("MOCK_ACCEPT","MOCK_REJECT","MOCK_UNRESOLVED")
            or not isinstance(c.notes,str) or not 32<=len(c.notes.strip())<=MAX_NOTES
            or c.reviewer_id in excluded_agent_editor_and_publisher_ids
            or c.role in checked_roles or c.reviewer_id in checked_reviewer_ids
            or c.key_id in checked_key_ids or c.receipt_id in checked_receipts
        ):
            raise VersionedReviewError("Wrong exact version, source, reviewer scope, role or duplicate")
        entry=registry.get(c.reviewer_id)
        if (
            not isinstance(entry,ExternalMockReviewer)
            or entry.active is not True or entry.role!=c.role
            or entry.key_id!=c.key_id or entry.reviewer_id!=c.reviewer_id
        ):
            raise VersionedReviewError("Reviewer was not independently scoped to this one role")
        issued=_at(c.signed_at_utc)
        expires=_at(c.expires_at_utc)
        if not timedelta(0)<=at-issued<=MAX_AGE or not timedelta(0)<expires-issued<=MAX_VALIDITY or expires<=at:
            raise VersionedReviewError("Old, future or expired reviewer signature")
        if (type(c.claimed_full_watch_seconds) is not int
                or c.claimed_full_watch_seconds<0
                or (c.role=="human_full_watch_listen" and
                    c.claimed_full_watch_seconds<
                    math.ceil(context["expected_playback_seconds_claimed_not_human_observed"]))
                or (c.role!="human_full_watch_listen" and c.claimed_full_watch_seconds!=0)
                or (c.role=="altered_synthetic_disclosure" and
                    c.synthetic_disclosure_choice not in (
                        "DISCLOSE_YES","DISCLOSE_NO","MOCK_UNRESOLVED"
                    ))
                or (c.role!="altered_synthetic_disclosure" and
                    c.synthetic_disclosure_choice!="NOT_DECIDED")):
            raise VersionedReviewError("No genuine AI disclosure or full watch duration proof")
        try:
            public=base64.b64decode(entry.public_ed25519_b64,validate=True)
            signature=base64.b64decode(record.signature_ed25519_b64,validate=True)
            if len(public)!=32 or len(signature)!=64 or public in checked_public_keys:
                raise VersionedReviewError("Wrong or shared reviewer public key")
            Ed25519PublicKey.from_public_bytes(public).verify(
                signature,DOMAIN+canonical(asdict(c)),
            )
        except (binascii.Error,InvalidSignature,ValueError,TypeError) as exc:
            raise VersionedReviewError("Detached review is not authentically Ed25519 signed") from exc
        checked_roles.add(c.role)
        checked_reviewer_ids.add(c.reviewer_id)
        checked_key_ids.add(c.key_id)
        checked_public_keys.add(public)
        checked_receipts.add(c.receipt_id)
        if c.decision!="MOCK_ACCEPT":
            unresolved.append(c.role)
        if c.role=="altered_synthetic_disclosure" and c.synthetic_disclosure_choice=="MOCK_UNRESOLVED":
            unresolved.append("unreviewed_disclosure")
    missing=sorted(set(ROLES)-checked_roles)
    unresolved.extend("missing_"+role for role in missing)
    return {
        "status":("ALL_SEVEN_SYNTHETIC_ED25519_VERSION_BINDINGS_VALID_NO_REAL_REVIEW"
                  if not unresolved else
                  "SYNTHETIC_VERSION_REVIEWS_INCOMPLETE_OR_REJECTED_NO_RELEASE"),
        "episode_id":context["episode_id"],
        "verified_object_version_count":context["object_count"],
        "version_bound_review_context_sha256":expected_context_sha256,
        "synthetic_registry_digest_sha256":expected_external_registry_sha256,
        "synthetic_valid_role_count":len(checked_roles),
        "synthetic_role_coverage":sorted(checked_roles),
        "synthetic_unresolved_roles":sorted(unresolved),
        "all_synthetic_signature_shapes_valid":not unresolved,
        "external_actual_human_reviewer_identities_authenticated":False,
        "real_owner_key_enrolled_from_private_authority":False,
        "actual_human_source_fact_rights_originality_disclosure_and_full_watch_verified":False,
        "real_production_immutable_approval_ledger_connected":False,
        "real_cloud_iam_kms_backup_and_billing_verified":False,
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }
