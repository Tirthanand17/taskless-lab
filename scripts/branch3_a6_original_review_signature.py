"""CLIVOX A6 exact-original-video OWNER EDITORIAL REVIEW attestation bridge.

Produces an unsigned review checklist from the *actual* A6 original media
handoff. Supports independent Ed25519 signature math over an exact review
claim and exact MP4, WAV, caption, metadata and A6 packet identity.

NO private key is generated/stored; NO owner public key has been independently
enrolled. A caller-supplied matching key/fingerprint is NOT an owner identity.
A mathematical signature is NEVER a legal rights grant, A6 production release,
or permission for a GitHub ledger PUT or any YouTube upload or scheduling.

Never accesses network, owner secrets, third-party footage or Google APIs.
"""
from __future__ import annotations

import argparse
import base64
import binascii
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from scripts.branch3_a6_original_handoff import (
    CHANNEL, CATALOG, PACKET_NAME, METADATA_NAME, ROOT,
    read_json, verify_packet, digest, sha
)
from scripts.branch3_original_arcade_pilots import validate_catalog

DOMAIN="CLIVOX-A6-ORIGINAL-EDITORIAL-REVIEW-V1"
SIGNING_PREFIX=b"CLIVOX-A6-ORIGINAL-EDITORIAL-REVIEW-V1\n"
REQUEST_FILE="owner-editorial-review-UNSIGNED.json"
CHECKS=(
    "exact_full_video_watched",
    "narration_voice_and_sound_reviewed",
    "captions_checked_against_actual_final_audio",
    "original_graphics_audio_and_tools_commercial_rights_checked",
    "title_description_and_fictional_content_checked",
)
FIELDS=frozenset((
    "schema_version","domain","channel_id","episode_id",
    "exact_review_packet_sha256","exact_video_sha256",
    "exact_audio_sha256","exact_captions_sha256","exact_metadata_sha256",
    "owner_review_checks","owner_review_completed_at_utc",
    "action","third_party_footage_present"
))
SHA64=re.compile(r"[0-9a-f]{64}\Z")
B64=re.compile(r"[A-Za-z0-9+/]+={0,2}\Z")
REVIEW_ACTION="EDITORIAL_REVIEW_CLAIM_ONLY_NO_UPLOAD"


class EditorialReviewDenied(ValueError):
    pass


def require(ok:bool,why:str)->None:
    if not ok:
        raise EditorialReviewDenied("CLIVOX_A6_EDITORIAL_DENY_"+why)


def canonical(obj:dict)->bytes:
    require(type(obj) is dict,"CANONICAL_DICT")
    return json.dumps(obj,sort_keys=True,separators=(",",":"),
                      ensure_ascii=True,allow_nan=False).encode("utf-8")


def validate_handoff_identity(packet:dict,metadata:dict)->None:
    require(type(packet) is dict and type(metadata) is dict,
            "HANDOFF_OBJECTS")
    require(packet.get("schema_version")==1
            and type(packet.get("schema_version")) is int
            and packet.get("domain")=="CLIVOX-A6-ORIGINAL-REVIEW-PACKET-V1"
            and packet.get("channel_id")==CHANNEL
            and packet.get("episode_id")==metadata.get("episode_id")
            and metadata.get("channel_id")==CHANNEL
            and metadata.get("schema_version")==1
            and type(metadata.get("schema_version")) is int
            and packet.get("exact_metadata_sha256")==digest(metadata)
            and packet.get("packet_sha256")==digest({
                k:v for k,v in packet.items() if k!="packet_sha256"
            }),
            "HANDOFF_IDENTITY")
    for key in ("packet_sha256","exact_video_sha256",
                "exact_audio_sha256","exact_captions_sha256",
                "exact_metadata_sha256"):
        require(type(packet.get(key)) is str and
                SHA64.fullmatch(packet[key]) is not None,
                "INVALID_SOURCE_DIGEST")
    require(packet.get("asset_claim")==
              "FIRST_PARTY_SCRIPTED_FICTION_NO_BORROWED_GAMEPLAY"
            and packet.get("youtube_upload_authorized") is False
            and packet.get("youtube_schedule_authorized") is False
            and packet.get("youtube_publish_authorized") is False
            and packet.get("owner_signing_identity_enrolled") is False
            and packet.get("owner_detached_signature_present") is False
            and packet.get("exact_video_human_review_confirmed") is False
            and packet.get("rights_of_all_final_assets_independently_approved") is False
            and metadata.get("youtube_visibility")=="NOT_UPLOADED"
            and metadata.get("youtube_upload_or_publish_authorized") is False,
            "UNSAFE_APPROVAL_PROMOTION")


def make_unsigned_review_request(packet:dict,metadata:dict)->dict:
    validate_handoff_identity(packet,metadata)
    return {
        "schema_version":1,
        "domain":DOMAIN,
        "channel_id":CHANNEL,
        "episode_id":packet["episode_id"],
        "exact_review_packet_sha256":packet["packet_sha256"],
        "exact_video_sha256":packet["exact_video_sha256"],
        "exact_audio_sha256":packet["exact_audio_sha256"],
        "exact_captions_sha256":packet["exact_captions_sha256"],
        "exact_metadata_sha256":packet["exact_metadata_sha256"],
        "owner_review_checks":{k:False for k in CHECKS},
        "owner_review_completed_at_utc":None,
        "action":REVIEW_ACTION,
        "third_party_footage_present":False,
    }


def strict_review_claim(body:dict,*,template:dict,now:datetime)->None:
    require(type(body) is dict and set(body)==FIELDS,
            "REVIEW_EXACT_FIELDS")
    require(type(template) is dict and set(template)==FIELDS,
            "TEMPLATE_FIELDS")
    require(type(now) is datetime and now.tzinfo is not None
            and now.utcoffset() is not None,"AWARE_CLOCK")
    static=set(FIELDS)-{"owner_review_checks","owner_review_completed_at_utc"}
    require(all(body[k]==template[k] for k in static),
            "EXACT_RENDER_BINDING_CHANGED")
    for k in ("schema_version","domain","channel_id","episode_id","action",
              "third_party_footage_present"):
        require(body[k]==template[k],"FIXED_SUBJECT_"+k)
    checks=body["owner_review_checks"]
    require(type(checks) is dict and set(checks)==set(CHECKS)
            and all(checks[k] is True for k in CHECKS),
            "UNREVIEWED_OR_FABRICATED_CHECKLIST")
    reviewed_at=body["owner_review_completed_at_utc"]
    require(type(reviewed_at) is str
            and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",
                             reviewed_at) is not None,
            "REVIEW_TIMESTAMP_FORMAT")
    try:
        timestamp=datetime.fromisoformat(reviewed_at[:-1]+"+00:00")
    except ValueError:
        raise EditorialReviewDenied(
            "CLIVOX_A6_EDITORIAL_DENY_REVIEW_TIMESTAMP"
        ) from None
    now_utc=now.astimezone(timezone.utc)
    require(timestamp<=now_utc and
            timestamp.year>=2026 and
            (now_utc-timestamp).days<=90,
            "REVIEW_TIME_RANGE")


def payload(body:dict)->bytes:
    require(type(body) is dict and set(body)==FIELDS,"PAYLOAD_FIELDS")
    return SIGNING_PREFIX+canonical(body)


def verify_attestation(*,packet:dict,metadata:dict,
                       signed_body:dict,signature_b64:str,
                       signer_public_key:bytes,
                       caller_pinned_public_key_sha256:str,
                       now:datetime)->dict:
    """Math only; caller-provided pin is not independently enrolled authority."""
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    template=make_unsigned_review_request(packet,metadata)
    strict_review_claim(signed_body,template=template,now=now)
    require(type(signer_public_key) is bytes and
            len(signer_public_key)==32,
            "SIGNER_PUBLIC_BYTES")
    require(type(caller_pinned_public_key_sha256) is str
            and SHA64.fullmatch(caller_pinned_public_key_sha256) is not None
            and hashlib.sha256(signer_public_key).hexdigest()==
                caller_pinned_public_key_sha256,
            "CALLER_PIN_MISMATCH")
    require(type(signature_b64) is str and
            0<len(signature_b64)<=120 and
            B64.fullmatch(signature_b64) is not None,
            "DETACHED_SIGNATURE_B64")
    try:
        sig=base64.b64decode(signature_b64,validate=True)
        require(len(sig)==64
                and base64.b64encode(sig).decode("ascii")==signature_b64,
                "SIGNATURE_CANONICAL_64")
        Ed25519PublicKey.from_public_bytes(signer_public_key).verify(
            sig,payload(signed_body)
        )
    except (binascii.Error,ValueError,InvalidSignature):
        raise EditorialReviewDenied(
            "CLIVOX_A6_EDITORIAL_DENY_INVALID_DETACHED_SIGNATURE"
        ) from None
    return {
        "stage":"A6_EXACT_ORIGINAL_EDITORIAL_CLAIM_SIGNATURE_MATH_ONLY",
        "channel_id":CHANNEL,
        "episode_id":packet["episode_id"],
        "cryptographic_ed25519_detached_claim_valid":True,
        "exact_handoff_video_audio_captions_and_metadata_bound":True,
        "caller_provided_public_key_fingerprint_matches":True,
        "owner_signing_identity_independently_enrolled":False,
        "claim_of_human_playback_independently_observed":False,
        "original_audio_and_tool_commercial_rights_legal_verification_proven":False,
        "trusted_independent_revocation_checkpoint_verified":False,
        "production_a6_signed_release_issued":False,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
        "actual_google_api_calls":0,
        "note":"A signed claim is mathematical evidence only; independent owner identity, human review and legal permissions must be established separately."
    }


def create_unsigned_requests(directory:Path,*,selection:str)->dict:
    require(selection in ("one","all"),"EPISODE_SELECTION")
    require(isinstance(directory,Path) and directory.is_absolute()
            and directory.is_dir() and not directory.is_symlink()
            and ROOT not in directory.parents and directory!=ROOT,
            "OUTSIDE_PUBLIC_REPO_ONLY")
    catalog=json.loads(CATALOG.read_text("utf-8"))
    episodes=validate_catalog(catalog)
    if selection=="one":
        episodes=episodes[:1]
    for episode in episodes:
        folder=directory/episode["id"]
        require(folder.is_dir() and not folder.is_symlink(),
                "EPISODE_DIRECTORY")
        packet=read_json(folder/PACKET_NAME)
        metadata=read_json(folder/METADATA_NAME)
        verify_packet(episode,folder,packet,metadata,
                      catalog_sha256=sha(CATALOG))
        unsigned=make_unsigned_review_request(packet,metadata)
        target=folder/REQUEST_FILE
        require(not target.exists() and not target.is_symlink(),
                "NO_OVERWRITE_UNSIGNED_REQUEST")
        target.write_text(json.dumps(unsigned,indent=2)+"\n",encoding="utf-8")
    return {
        "stage":"A6_UNSIGNED_OWNER_REVIEW_REQUESTS_ONLY",
        "episode_count":len(episodes),
        "exact_media_and_metadata_reinspected":True,
        "unsigned_requests_written":len(episodes),
        "all_review_checks_default_false":True,
        "signing_keys_created_or_exported":False,
        "owner_approval_claimed":False,
        "real_a6_release_issued":False,
        "actual_github_writes":0,
        "actual_google_api_calls":0,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
    }



def verify_unsigned_requests(directory:Path,*,selection:str)->dict:
    """READ-ONLY verification of downloaded original-asset review package.

    Re-runs actual ffprobe, A5 media QA, A6 media/audio/SRT/metadata hashes,
    and exact unsigned review checklist equality. Valid data is still NOT
    a human attestation, production release, or Google upload authorization.
    """
    require(selection in ("one","all"),"VERIFY_SELECTION")
    require(isinstance(directory,Path) and directory.is_absolute()
            and directory.is_dir() and not directory.is_symlink()
            and ROOT not in directory.parents and directory!=ROOT,
            "VERIFY_OUTSIDE_REPO_ONLY")
    episodes=validate_catalog(json.loads(CATALOG.read_text("utf-8")))
    if selection=="one":
        episodes=episodes[:1]
    for episode in episodes:
        folder=directory/episode["id"]
        require(folder.is_dir() and not folder.is_symlink(),"VERIFY_FOLDER")
        source=folder/REQUEST_FILE
        require(source.is_file() and not source.is_symlink()
                and 0<source.stat().st_size<=15_000,
                "MISSING_UNSIGNED_REVIEW")
        packet=read_json(folder/PACKET_NAME)
        metadata=read_json(folder/METADATA_NAME)
        verify_packet(episode,folder,packet,metadata,
                      catalog_sha256=sha(CATALOG))
        expected=make_unsigned_review_request(packet,metadata)
        found=read_json(source)
        require(found==expected,"CHANGED_OR_FORGED_UNSIGNED_REVIEW")
    return {
        "stage":"A6_REAL_MEDIA_UNSIGNED_REVIEW_PACKAGE_READONLY_VERIFIED",
        "all_episode_video_audio_caption_metadata_and_qa_hashes_recomputed":True,
        "unsigned_checklist_files_matched_exact_media":True,
        "episode_count":len(episodes),
        "actual_owner_signature_keys_loaded":0,
        "actual_human_video_approvals_verified":0,
        "real_a6_signed_releases_verified":0,
        "google_api_calls":0,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
    }


def fixture()->dict:
    return {
        "stage":"A6_ORIGINAL_SIGNED_EDITORIAL_CLAIM_CONTRACT_NOT_OWNER_APPROVAL",
        "fixed_video_audio_caption_metadata_binding_implemented":True,
        "ed25519_detached_signature_math_tested_only":True,
        "owner_trusted_public_key_independently_enrolled":False,
        "real_owner_review_verified":False,
        "real_signed_release_issued":False,
        "actual_private_signature_records_read":0,
        "actual_google_api_calls":0,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
    }


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("fixture","unsigned","verify"),default="fixture")
    p.add_argument("--selection",choices=("one","all"),default="one")
    p.add_argument("--directory",type=Path)
    args=p.parse_args()
    try:
        if args.mode=="fixture":
            report=fixture()
        else:
            require(args.directory is not None,"REVIEW_DIRECTORY")
            if args.mode=="unsigned":
                report=create_unsigned_requests(args.directory,selection=args.selection)
            else:
                report=verify_unsigned_requests(args.directory,selection=args.selection)
    except (EditorialReviewDenied,ValueError,KeyError,TypeError):
        raise SystemExit(
            "CLIVOX_A6_REVIEW_REJECTED_NO_OWNER_SIGNATURE_NO_YOUTUBE"
        ) from None
    print(json.dumps(report,sort_keys=True))


if __name__=="__main__":
    main()
