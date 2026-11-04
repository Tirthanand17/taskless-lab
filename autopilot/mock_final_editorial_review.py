"""B3d4c2c2: independent final-media editorial receipt STRUCTURE (NO PUBLISH).

This re-hashes all exact ephemeral media, re-derives B3d4a script/source
lineage AND B3d3b signed atomic-claim reviewer coverage, then verifies
domain-separated Ed25519 *mock* signers for seven independent final-review
duties. Every account, credential, human, license, review and owner signature
in public CI is synthetic. A valid signature on a claim can never prove the
claims are true, the signer is an actual human, or the media may be published.

Never import model or uploader transports. No external provider, vault,
account, paid API, YouTube, deployed release ledger or local laptop used.
"""
from __future__ import annotations

import base64
import binascii
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import math
import json
import re
from typing import Mapping, Sequence

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from autopilot.final_media_evidence_gate import (
    create_unapproved_final_media_inventory, FinalMediaEvidenceError,
)
from autopilot.independent_fact_review_gate import (
    verify_independent_fact_records, FactReviewError, STATUS_PENDING,
)
from autopilot.script_continuity_gate import CHANNEL_ID

PURPOSE = "flowminute_b3d4c2c2_mock_final_editorial_review_v1"
DOMAIN = b"FLOWMINUTE_B3D4C2C2_MOCK_EDITORIAL_REVIEW\x00"
HEX = re.compile(r"[0-9a-f]{64}\Z")
ID = re.compile(r"[a-z][a-z0-9_]{2,63}\Z")
ROLES = (
    "independent_fact_sufficiency",
    "final_visual_caption_title",
    "originality_against_channel",
    "voice_music_image_rights",
    "altered_synthetic_disclosure",
    "human_full_watch_listen",
    "channel_owner_release_intent",
)
MAX_AGE = timedelta(hours=24)
MAX_VALIDITY = timedelta(hours=36)
MAX_NOTES = 1000
STATUS_COMPLETE = "MOCK_SEVEN_EDITS_SIGNATURE_COVERAGE_ONLY_NO_RELEASE"
STATUS_BLOCKED = "MOCK_EDITS_REJECTED_OR_UNRESOLVED_NO_RELEASE"


class FinalEditorialEvidenceError(ValueError):
    """No external editorial trust, altered final bytes or invalid review receipt."""


@dataclass(frozen=True)
class UnapprovedMetadata:
    """Owner has NOT approved any proposed public metadata or disclosure."""
    title_unreviewed: str
    description_unreviewed: str
    thumbnail_claim_unreviewed: str
    source_link_index_sha256: str
    previous_release_index_sha256: str
    license_evidence_index_sha256: str
    actual_synthetic_disclosure_decision: str = "PENDING_OWNER_REVIEW"


@dataclass(frozen=True)
class TrustedMockEditorialReviewer:
    """Only a separately authenticated PRIVATE registry could enroll real humans."""
    reviewer_id: str
    key_id: str
    public_key_ed25519_b64: str
    allowed_roles: tuple[str, ...]
    active: bool = True


@dataclass(frozen=True)
class MockEditorialReviewClaim:
    purpose: str
    channel_id: str
    episode_id: str
    inventory_sha256: str
    editorial_docket_sha256: str
    role: str
    role_evidence_sha256: str
    decision: str
    reviewer_id: str
    key_id: str
    reviewed_at_utc: str
    expires_at_utc: str
    receipt_id: str
    review_notes: str
    claimed_full_watch_seconds: int = 0
    synthetic_disclosure_choice: str = "NOT_DECIDED"


@dataclass(frozen=True)
class DetachedMockEditorialReview:
    claim: MockEditorialReviewClaim
    signature_ed25519_b64: str


def canonical(obj: object) -> bytes:
    try:
        data = json.dumps(obj,sort_keys=True,ensure_ascii=False,
                          separators=(",",":"),allow_nan=False).encode("utf-8")
    except (TypeError,ValueError,OverflowError,RecursionError) as exc:
        raise FinalEditorialEvidenceError("Unserializable editorial material") from exc
    if len(data) > 300_000:
        raise FinalEditorialEvidenceError("Unbounded review material")
    return data


def _digest(obj: object) -> str:
    return sha256(canonical(obj)).hexdigest()


def _time(raw: str) -> datetime:
    if not isinstance(raw,str) or len(raw)>64:
        raise FinalEditorialEvidenceError("Invalid reviewer timestamp")
    try:
        value=datetime.fromisoformat(raw.replace("Z","+00:00"))
    except (ValueError,TypeError,OverflowError) as exc:
        raise FinalEditorialEvidenceError("Invalid reviewer timestamp") from exc
    if value.tzinfo is None or value.utcoffset() is None:
        raise FinalEditorialEvidenceError("Missing review timezone")
    return value.astimezone(timezone.utc)


def _asset_sha(asset_rows: list, name: str) -> str:
    index={r["file_name"]:r["sha256"] for r in asset_rows}
    if name not in index:
        raise FinalEditorialEvidenceError("Required exact asset absent from inventory")
    return index[name]


def make_unapproved_editorial_docket(
    *, media_inputs: dict, fact_review_inputs: dict,
    metadata: UnapprovedMetadata,
) -> dict:
    """RECHECK every physical byte and all signed preflight fact-review inputs.

    Content authors and PR fixtures cannot supply an 'approved' flag. The
    exact external anchor/signers needed by the upstream verifiers must come
    from another trusted subsystem in production. A caller could fabricate
    ALL these fields in CI; all real approval and upload flags stay false.
    """
    if not isinstance(media_inputs,dict) or not isinstance(fact_review_inputs,dict):
        raise FinalEditorialEvidenceError("Recomputable signed media and atomic fact inputs needed")
    try:
        media=create_unapproved_final_media_inventory(**media_inputs)
        facts=verify_independent_fact_records(**fact_review_inputs)
    except (FinalMediaEvidenceError,FactReviewError,ValueError,KeyError,TypeError) as exc:
        raise FinalEditorialEvidenceError("Final assets or exact signed fact preflight failed") from exc
    if (
        not isinstance(metadata,UnapprovedMetadata)
        or not isinstance(metadata.title_unreviewed,str)
        or metadata.title_unreviewed!=media_inputs["plan"]["title_unverified"]
        or not 15<=len(metadata.description_unreviewed)<=4000
        or not isinstance(metadata.thumbnail_claim_unreviewed,str)
        or not 6<=len(metadata.thumbnail_claim_unreviewed)<=180
        or any(not isinstance(v,str) or not HEX.fullmatch(v) for v in (
            metadata.source_link_index_sha256,
            metadata.previous_release_index_sha256,
            metadata.license_evidence_index_sha256,
        ))
        or metadata.actual_synthetic_disclosure_decision!="PENDING_OWNER_REVIEW"
    ):
        raise FinalEditorialEvidenceError("Changed/unreviewed metadata, missing prior/rights evidence root")
    if (
        facts.get("episode_id")!=media["episode_id"]
        or facts.get("script_manifest_sha256")!=media["signed_original_script_manifest_sha256"]
        or facts.get("status")!=STATUS_PENDING
        or facts.get("signed_review_record_coverage_satisfied") is not True
        or facts.get("expected_atomic_claim_count",0)<1
        or facts.get("independent_fact_truth_verified_by_software") is not False
        or facts.get("reviewers_real_identity_authenticated_by_software") is not False
        or facts.get("external_owner_review_and_release_grant_present") is not False
        or facts.get("release_authorized") is not False
    ):
        raise FinalEditorialEvidenceError(
            "Atomic factual claim coverage missing or mock fact receipt pretending truth"
        )
    assets=media["asset_sha256_and_exact_sizes"]
    review_binding={
        "schema_version":1,
        "purpose":PURPOSE,
        "channel_id":CHANNEL_ID,
        "episode_id":media["episode_id"],
        "format":media["format"],
        "release_slot":media["release_slot"],
        "full_media_inventory_sha256":media["unapproved_inventory_sha256"],
        "script_manifest_sha256":media["signed_original_script_manifest_sha256"],
        "spoken_narration_sha256":media["signed_full_spoken_narration_sha256"],
        "source_observation_sha256":media["source_observations_sha256"],
        "fact_claim_docket_sha256":facts["review_docket_sha256"],
        "atomic_claim_count":facts["expected_atomic_claim_count"],
        "mock_fact_signed_record_count":facts["signed_review_records_valid_count"],
        "media_asset_hashes":assets,
        "metadata_draft":asdict(metadata),
        "editorial_real_humans_authenticated":False,
        "semantic_fact_truth_approved":False,
        "real_rights_or_voice_license_approved":False,
        "human_full_watch_observed_by_software":False,
        "repetitious_content_originality_approved":False,
        "owner_approved_synthetic_disclosure":False,
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }
    references={
        "independent_fact_sufficiency":_digest({
            "claim_docket":facts["review_docket_sha256"],
            "claim_count":facts["expected_atomic_claim_count"],
            "source_root":metadata.source_link_index_sha256,
        }),
        "final_visual_caption_title":_digest({
            "title":metadata.title_unreviewed,
            "description":metadata.description_unreviewed,
            "thumbnail_claim":metadata.thumbnail_claim_unreviewed,
            "mp4":_asset_sha(assets,"UNAPPROVED_FULL_EDUCATION_TEST.mp4"),
            "thumbnail":_asset_sha(assets,"UNAPPROVED_THUMBNAIL_TEST.png"),
            "srt":_asset_sha(assets,"scene_captions.srt"),
            "all_scenes":[r["sha256"] for r in assets if r["file_name"].startswith("scene_") and r["file_name"].endswith(".png")],
        }),
        "originality_against_channel":_digest({
            "prior_release_root":metadata.previous_release_index_sha256,
            "script":media["signed_original_script_manifest_sha256"],
            "demo":media["computed_demo_evidence_sha256"],
            "title":metadata.title_unreviewed,
        }),
        "voice_music_image_rights":_digest({
            "license_docs_root":metadata.license_evidence_index_sha256,
            "voice_id":media["voice"],
            "wav":_asset_sha(assets,"original_voice.wav"),
            "thumbnail":_asset_sha(assets,"UNAPPROVED_THUMBNAIL_TEST.png"),
            "all_assets":[r["sha256"] for r in assets],
        }),
        "altered_synthetic_disclosure":_digest({
            "pending_decision":metadata.actual_synthetic_disclosure_decision,
            "video":_asset_sha(assets,"UNAPPROVED_FULL_EDUCATION_TEST.mp4"),
            "voice":media["voice"],
            "title":metadata.title_unreviewed,
        }),
        "human_full_watch_listen":_digest({
            "video":_asset_sha(assets,"UNAPPROVED_FULL_EDUCATION_TEST.mp4"),
            "wav":_asset_sha(assets,"original_voice.wav"),
            "srt":_asset_sha(assets,"scene_captions.srt"),
            "duration_seconds":media["duration_seconds"],
        }),
        "channel_owner_release_intent":_digest({
            "channel_id":CHANNEL_ID,
            "video":_asset_sha(assets,"UNAPPROVED_FULL_EDUCATION_TEST.mp4"),
            "title":metadata.title_unreviewed,
            "fact_root":facts["review_docket_sha256"],
            "license_root":metadata.license_evidence_index_sha256,
            "prior_root":metadata.previous_release_index_sha256,
        }),
    }
    binding=canonical(review_binding)
    if len(binding)>200_000 or set(references)!=set(ROLES):
        raise FinalEditorialEvidenceError("Invalid bounded and comprehensive review set")
    return {
        **review_binding,
        "required_role_evidence_sha256":references,
        "editorial_docket_sha256":sha256(binding+canonical(references)).hexdigest(),
        "signed_final_review_receipts_present":False,
        "real_private_release_ledger_connected":False,
        "owner_or_human_real_world_identity_verified":False,
    }


def verify_mock_final_editorial_receipts(
    *, docket: dict,
    media_inputs: dict,
    fact_review_inputs: dict,
    metadata: UnapprovedMetadata,
    records: Sequence[DetachedMockEditorialReview],
    registry: Mapping[str,TrustedMockEditorialReviewer],
    excluded_creator_agent_and_publisher_ids: frozenset[str],
    expected_externally_pinned_docket_sha256: str,
    now: datetime,
) -> dict:
    """Signature/coverage check only; even 7 MOCK_ACCEPTs NEVER enable publish."""
    rebuilt=make_unapproved_editorial_docket(
        media_inputs=media_inputs,fact_review_inputs=fact_review_inputs,
        metadata=metadata,
    )
    if (
        not isinstance(docket,dict)
        or canonical(docket)!=canonical(rebuilt)
        or not isinstance(expected_externally_pinned_docket_sha256,str)
        or not HEX.fullmatch(expected_externally_pinned_docket_sha256)
        or docket["editorial_docket_sha256"]!=expected_externally_pinned_docket_sha256
    ):
        raise FinalEditorialEvidenceError("Editorial docket not exact, externally pinned final bytes")
    if (
        not isinstance(now,datetime) or now.tzinfo is None or now.utcoffset() is None
        or not isinstance(excluded_creator_agent_and_publisher_ids,frozenset)
        or not excluded_creator_agent_and_publisher_ids
        or any(not isinstance(x,str) or not ID.fullmatch(x)
               for x in excluded_creator_agent_and_publisher_ids)
        or not isinstance(registry,Mapping)
        or not isinstance(records,(tuple,list))
        or len(records)>len(ROLES)
    ):
        raise FinalEditorialEvidenceError("No independently trusted clock, roles or reviewer registry")
    at=now.astimezone(timezone.utc)
    used_ids=set()
    used_keys=set()
    used_public_keys=set()
    receipts=set()
    checked_roles=set()
    blocked=[]
    for record in records:
        if not isinstance(record,DetachedMockEditorialReview) or not isinstance(record.claim,MockEditorialReviewClaim):
            raise FinalEditorialEvidenceError("Not an immutable signed mock review")
        c=record.claim
        if (
            c.purpose!=PURPOSE or c.channel_id!=CHANNEL_ID
            or c.episode_id!=docket["episode_id"]
            or c.inventory_sha256!=docket["full_media_inventory_sha256"]
            or c.editorial_docket_sha256!=docket["editorial_docket_sha256"]
            or c.role not in ROLES
            or c.role_evidence_sha256!=docket["required_role_evidence_sha256"][c.role]
            or c.decision not in ("MOCK_ACCEPT","MOCK_REJECT","MOCK_UNRESOLVED")
            or not isinstance(c.reviewer_id,str) or not ID.fullmatch(c.reviewer_id)
            or not isinstance(c.key_id,str) or not ID.fullmatch(c.key_id)
            or not isinstance(c.receipt_id,str) or not ID.fullmatch(c.receipt_id)
            or c.reviewer_id in excluded_creator_agent_and_publisher_ids
            or not isinstance(c.review_notes,str) or not 35<=len(c.review_notes.strip())<=MAX_NOTES
        ):
            raise FinalEditorialEvidenceError("Review role, file, identity or signed scope changed")
        entry=registry.get(c.reviewer_id)
        if (
            not isinstance(entry,TrustedMockEditorialReviewer)
            or entry.active is not True
            or entry.reviewer_id!=c.reviewer_id
            or entry.key_id!=c.key_id
            or entry.allowed_roles!=(c.role,)
        ):
            raise FinalEditorialEvidenceError("Reviewer not separately enrolled for this one purpose")
        if (
            c.role in checked_roles or c.reviewer_id in used_ids
            or c.key_id in used_keys or c.receipt_id in receipts
        ):
            raise FinalEditorialEvidenceError("Reused editorial identity, key or receipt/role")
        if (
            type(c.claimed_full_watch_seconds) is not int
            or c.claimed_full_watch_seconds < 0
            or (c.role=="human_full_watch_listen" and (
                c.claimed_full_watch_seconds<math.ceil(media_inputs["report"]["seconds"])
            ))
            or (c.role!="human_full_watch_listen" and c.claimed_full_watch_seconds!=0)
            or (c.role=="altered_synthetic_disclosure"
                and c.synthetic_disclosure_choice not in (
                    "DISCLOSE_YES","DISCLOSE_NO","MOCK_UNRESOLVED"
                ))
            or (c.role!="altered_synthetic_disclosure"
                and c.synthetic_disclosure_choice!="NOT_DECIDED")
        ):
            raise FinalEditorialEvidenceError("Unreviewed disclosure or implausible mock watch interval")
        issued=_time(c.reviewed_at_utc)
        expires=_time(c.expires_at_utc)
        if not timedelta(0)<=at-issued<=MAX_AGE or not timedelta(0)<expires-issued<=MAX_VALIDITY or expires<=at:
            raise FinalEditorialEvidenceError("Mock editorial record stale/future/expired")
        try:
            pub=base64.b64decode(entry.public_key_ed25519_b64,validate=True)
            sig=base64.b64decode(record.signature_ed25519_b64,validate=True)
            if len(pub)!=32 or len(sig)!=64:
                raise FinalEditorialEvidenceError("Malformed reviewer public key or detached signature")
            if pub in used_public_keys:
                raise FinalEditorialEvidenceError("Same key reused under another reviewer ID")
            Ed25519PublicKey.from_public_bytes(pub).verify(
                sig,DOMAIN+canonical(asdict(c))
            )
        except (binascii.Error,InvalidSignature,TypeError,ValueError) as exc:
            raise FinalEditorialEvidenceError("Invalid domain-separated editorial signature") from exc
        checked_roles.add(c.role)
        used_ids.add(c.reviewer_id)
        used_keys.add(c.key_id)
        used_public_keys.add(pub)
        receipts.add(c.receipt_id)
        if c.decision!="MOCK_ACCEPT":
            blocked.append(c.role)
        if c.role=="altered_synthetic_disclosure" and c.synthetic_disclosure_choice=="MOCK_UNRESOLVED":
            blocked.append("missing_ai_disclosure_decision")
    missing=sorted(set(ROLES)-checked_roles)
    if missing:
        blocked.extend("missing_"+x for x in missing)
    return {
        "schema_version":1,
        "status":STATUS_BLOCKED if blocked else STATUS_COMPLETE,
        "episode_id":docket["episode_id"],
        "media_inventory_sha256":docket["full_media_inventory_sha256"],
        "editorial_docket_sha256":docket["editorial_docket_sha256"],
        "mock_role_coverage":sorted(checked_roles),
        "mock_structurally_valid_receipt_count":len(checked_roles),
        "mock_unresolved_roles_or_gaps":sorted(blocked),
        "all_mock_editorial_signature_shapes_valid":not blocked,
        "real_source_fact_accuracy_and_claim_completeness_verified":False,
        "real_human_full_watch_and_listen_verified":False,
        "live_voice_music_image_license_verified":False,
        "material_originality_against_real_channel_verified":False,
        "real_ai_disclosure_decision_verified":False,
        "owner_permission_and_signer_enrollment_authenticated":False,
        "private_immutable_review_ledger_connected":False,
        "actual_uploaded_youtube_video_id":None,
        "real_provider_model_used":False,
        "youtube_upload_enabled":False,
        "youtube_schedule_enabled":False,
        "release_authorized":False,
    }
