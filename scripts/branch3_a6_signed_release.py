"""Clivox A6: signed-release cryptography preview + production quarantine.

This module does NOT approve rights, ingest footage or access YouTube.
No owner signing public key is enrolled. Synthetic tests exercise Ed25519
without storing a private key. Real license/human review is external evidence.
"""
from __future__ import annotations
import argparse
import base64
import binascii
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import re

CLIVOX="UCfPEvy0SefE_5nNlYlY_CyQ"
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/"branch3/release/fixtures/unapproved-release.json"
POLICY=ROOT/"branch3/release/release-policy.json"
SHA=re.compile(r"[0-9a-f]{64}\Z")
RELEASE_ID=re.compile(r"clivox_[a-z0-9][a-z0-9_-]{10,100}\Z")
B64=re.compile(r"[A-Za-z0-9+/]+={0,2}\Z")
REVIEW_FIELDS=frozenset({
 "creator_rights_grant_verified","underlying_rights_cleared",
 "license_not_expired_and_not_revoked","exact_source_context_verified",
 "original_commentary_human_reviewed","final_video_human_reviewed",
 "video_qa_passed_for_actual_licensed_content"
})
RELEASE_FIELDS=frozenset({
 "schema_version","channel_id","release_id","release_state","asset_kind",
 "asset","reviewed","signature","planned_release","controls","note"
})

class ReleaseBlocked(ValueError):
    pass

def require(ok: bool,reason: str) -> None:
    if not ok:
        raise ReleaseBlocked("CLIVOX_A6_DENY_"+reason)

def iso_utc(value: object) -> datetime:
    require(type(value) is str and value.endswith("Z"),"UTC_TIMESTAMP")
    try:
        parsed=datetime.fromisoformat(value[:-1]+"+00:00")
    except (ValueError,TypeError):
        raise ReleaseBlocked("CLIVOX_A6_DENY_INVALID_TIME") from None
    require(parsed.utcoffset()==timedelta(0),"WRONG_TIMEZONE")
    return parsed

def signing_payload(*, channel_id: str, release_id: str,
                    video_sha256: str, metadata_sha256: str,
                    rights_sha256: str, privacy: str,
                    publish_at_utc: str) -> bytes:
    """Canonical signed subject: exact video + metadata + grant + channel + schedule.

    Preview utility, not an upload or rights check. Any media/metadata/schedule
    mutation must invalidate the signature. Domain separator stops cross-use.
    """
    require(channel_id==CLIVOX,"WRONG_CHANNEL")
    require(type(release_id) is str and RELEASE_ID.fullmatch(release_id) is not None,
            "RELEASE_ID")
    for label,digest in (
        ("VIDEO",video_sha256),("METADATA",metadata_sha256),("RIGHTS",rights_sha256)
    ):
        require(type(digest) is str and SHA.fullmatch(digest) is not None,
                "DIGEST_"+label)
    require(privacy=="private","REQUIRE_PRIVATE")
    iso_utc(publish_at_utc)
    payload={
        "asset_video_sha256":video_sha256,"channel_id":channel_id,
        "metadata_sha256":metadata_sha256,"publish_at_utc":publish_at_utc,
        "release_id":release_id,"rights_evidence_sha256":rights_sha256,
        "status_on_initial_upload":privacy,"version":1
    }
    return b"CLIVOX-A6-EXACT-RELEASE-V1\n"+json.dumps(
        payload,sort_keys=True,separators=(",",":"),ensure_ascii=True
    ).encode("utf-8")

def verify_signature(payload: bytes, signature_b64: str,
                     trusted_public_key_raw: bytes) -> bool:
    """Only verifies mathematical Ed25519 signature; not issuer or legal authority.

    The trusted key must be externally enrolled as an *owner* key before
    a future release controller may rely on it. Current repository has none.
    """
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    require(type(payload) is bytes and payload.startswith(b"CLIVOX-A6-EXACT-RELEASE-V1\n"),
            "SIGNING_DOMAIN")
    require(type(signature_b64) is str and len(signature_b64)<=120
            and B64.fullmatch(signature_b64) is not None,"SIGNATURE_ENCODING")
    require(type(trusted_public_key_raw) is bytes and len(trusted_public_key_raw)==32,
            "TRUSTED_KEY_BYTES")
    try:
        sig=base64.b64decode(signature_b64,validate=True)
        require(len(sig)==64,"SIGNATURE_LENGTH")
        Ed25519PublicKey.from_public_bytes(trusted_public_key_raw).verify(sig,payload)
        return True
    except (InvalidSignature,ValueError,binascii.Error):
        return False

def validate_quarantine_manifest(manifest: dict, policy: dict) -> dict:
    require(type(manifest) is dict and set(manifest)==RELEASE_FIELDS,"MANIFEST_FIELDS")
    require(type(policy) is dict and set(policy)=={
        "schema_version","channel_id","phase",
        "real_owner_signing_public_key_enrolled","real_signed_releases",
        "real_verified_creator_licenses","exact_licensed_asset_available",
        "quarantine_default","live_release_approval_enabled",
        "github_release_workflow_enabled","youtube_write_enabled",
        "immutable_digest_fields","status"
    },"POLICY_FIELDS")
    require(policy["schema_version"]==manifest["schema_version"]==1
            and policy["channel_id"]==manifest["channel_id"]==CLIVOX,
            "CHANNEL_POLICY")
    require(policy["phase"]=="A6_RELEASE_APPROVAL_CRYPTO_PREVIEW"
            and policy["status"]=="DESIGN_AND_OFFLINE_TESTS_ONLY","UNAUTH_PRODUCTION")
    require(policy["real_signed_releases"]==policy["real_verified_creator_licenses"]==0,
            "BOGUS_REAL_RELEASE")
    require(policy["exact_licensed_asset_available"] is False
            and policy["real_owner_signing_public_key_enrolled"] is False,
            "OWNER_KEY_OR_LICENSE_NOT_CONFIGURED")
    for flag in ("live_release_approval_enabled","github_release_workflow_enabled","youtube_write_enabled"):
        require(policy[flag] is False,"RELEASE_ON_"+flag)
    require(policy["quarantine_default"] is True,"QUARANTINE_OFF")
    require(manifest["release_state"]=="QUARANTINED_UNLICENSED_DEMO"
            and manifest["asset_kind"]=="A5_ORIGINAL_ONLY_SYNTHETIC_BENCHMARK",
            "INVALID_STAGE")
    require(type(manifest["release_id"]) is str
            and RELEASE_ID.fullmatch(manifest["release_id"]) is not None,
            "BAD_RELEASE_ID")
    asset=manifest["asset"]
    require(type(asset) is dict and set(asset)=={
        "video_sha256","metadata_sha256","source_rights_evidence_sha256",
        "video_bytes","third_party_footage_present"
    },"ASSET_FIELDS")
    require(all(asset[k] is None for k in (
        "video_sha256","metadata_sha256","source_rights_evidence_sha256","video_bytes"
    )) and asset["third_party_footage_present"] is False,
            "FALSE_LICENSED_ASSET")
    review=manifest["reviewed"]
    require(type(review) is dict and set(review)==REVIEW_FIELDS
            and all(review[k] is False for k in REVIEW_FIELDS),
            "FORGED_HUMAN_REVIEW")
    signature=manifest["signature"]
    require(type(signature) is dict and set(signature)=={
        "algorithm","public_key_id","detached_signature_base64",
        "signing_receipt_ref","owner_signed"
    },"SIGNATURE_FIELDS")
    require(signature["algorithm"]=="Ed25519"
            and all(signature[k] is None for k in (
                "public_key_id","detached_signature_base64","signing_receipt_ref"
            )) and signature["owner_signed"] is False,
            "FAKE_OWNER_SIGNATURE")
    release=manifest["planned_release"]
    require(type(release) is dict and set(release)=={
        "target_channel_id","privacy_status","publish_at_utc",
        "owner_approved_exact_schedule"
    },"SCHEDULE_FIELDS")
    require(release["target_channel_id"]==CLIVOX
            and release["privacy_status"]=="private"
            and release["publish_at_utc"] is None
            and release["owner_approved_exact_schedule"] is False,
            "PREMATURE_SCHEDULE")
    controls=manifest["controls"]
    require(type(controls) is dict and set(controls)=={
        "production_release_key_enrolled","github_environment_reviewed",
        "channel_oauth_verified","private_vault_verified",
        "quarantine_enabled","media_download_enabled",
        "youtube_upload_enabled","youtube_schedule_enabled",
        "youtube_publish_enabled"
    },"CONTROLS_FIELDS")
    require(controls["quarantine_enabled"] is True
            and all(controls[k] is False for k in controls if k!="quarantine_enabled"),
            "RELEASE_FLAGS_ENABLED")
    require("private key" in manifest["note"].lower(),"MISSING_KEY_SAFETY_NOTE")
    return {
        "channel_id":CLIVOX,"release_id":manifest["release_id"],
        "stage":"A6_QUARANTINED_DEMO_ONLY",
        "status":"HOLD_MISSING_LICENSE_AND_OWNER_SIGNATURE",
        "owner_public_key_enrolled":False,"signed_licensed_assets":0,
        "mathematical_signature_verification_available_for_FUTURE_TESTS":True,
        "human_license_and_originality_review_complete":False,
        "video_download_authorized":False,"video_upload_authorized":False,
        "youtube_schedule_authorized":False,"youtube_publish_authorized":False,
        "note":"No third-party content or signed final asset has been supplied."
    }

def validate_future_release_time(value: str, *, now: datetime) -> bool:
    future=iso_utc(value)
    require(now.tzinfo is not None and now.utcoffset() is not None,"NAIVE_NOW")
    require(future>now.astimezone(timezone.utc)+timedelta(minutes=30),
            "UNSAFE_PUBLISH_TIME")
    return True

def production_release(*_args,**_kwargs) -> None:
    raise ReleaseBlocked("CLIVOX_A6_DENY_NO_PRODUCTION_SIGNER_OR_LIVE_RIGHTS_GATE")

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    m=json.loads(FIXTURE.read_text("utf-8"))
    p=json.loads(POLICY.read_text("utf-8"))
    r=validate_quarantine_manifest(m,p)
    report=json.dumps(r,indent=2)+"\n"
    if args.out:
        require(not args.out.is_symlink(),"OUTPUT_SYMLINK")
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(report,encoding="utf-8")
    else:
        print(report,end="")
    print("CLIVOX_A6_CRYPTO_PREVIEW_QUARANTINE_NO_RIGHTS_NO_UPLOAD")

if __name__=="__main__":
    main()
