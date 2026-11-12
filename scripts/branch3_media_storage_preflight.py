"""Clivox A3: fail-closed confidential media boundary preflight.

NO GitHub access tokens, network requests, downloads, uploads, or legal approvals.
GitHub's PUBLIC repo and artifacts must never store third-party source footage.
A passing offline preflight only confirms the storage boundary remains CLOSED.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/"branch3/media_storage/storage-policy.json"
MANIFEST=ROOT/"branch3/media_storage/examples/unlicensed-source-manifest.json"
CREATOR_PERMS=ROOT/"branch3/creator_permissions.json"
CHANNEL_STATE=ROOT/"branch3/channel_state.json"
CLIVOX="UCfPEvy0SefE_5nNlYlY_CyQ"
CONTROLLER="Tirthanand17/taskless-lab"
SHA256=re.compile(r"[0-9a-f]{64}\Z")
VIDEO_ID=re.compile(r"[A-Za-z0-9_-]{11}\Z")
MEDIA_ID=re.compile(r"clivox_[a-z0-9][a-z0-9_-]{6,80}\Z")
RESTRICTED_EXTENSIONS=frozenset({
    ".mp4",".mov",".mkv",".webm",".avi",".flv",".mp3",".wav",
    ".aac",".m4a",".opus",".srt",".vtt",".ass",".zip",".7z",
    ".rar",".tar",".gz",".pdf",".pem",".p12",".pfx",".key",
})
BRANDING_ALLOWLIST=frozenset({
    "branch3/branding/clivox-live-avatar.png",
    "branch3/branding/clivox-live-banner-2560x1440.png",
})
PUBLIC_SAFE_SUFFIXES=frozenset({".json",".md",".txt",".py",".yml",".yaml",".svg"})

class StorageDenied(ValueError):
    """Storage is not provisioned or required release/rights checks are missing."""

def require(value: bool, code: str) -> None:
    if not value:
        raise StorageDenied("CLIVOX_A3_DENY_"+code)

def read_json(path: Path) -> dict:
    require(path.is_file() and not path.is_symlink(),"MANIFEST_LOCATION")
    require(path.stat().st_size<64_000,"MANIFEST_SIZE")
    doc=json.loads(path.read_text(encoding="utf-8"))
    require(type(doc) is dict,"MANIFEST_TYPE")
    return doc

def inspect_private_repo_metadata(repo: object, *, expected_full_name: str) -> dict:
    """Checks supplied GitHub API metadata. This does NOT fetch or authenticate it.

    Used in future *authenticated* private-vault provisioning reviews. JSON
    assertions alone are not an authorization to retrieve any copyrighted media.
    """
    require(type(repo) is dict and set(repo)>={
        "full_name","private","visibility","owner","archived","disabled"
    },"VAULT_METADATA")
    owner=repo["owner"]
    require(type(owner) is dict and type(owner.get("login")) is str,"VAULT_OWNER")
    require(type(expected_full_name) is str and
            re.fullmatch(r"[A-Za-z0-9-]+/[A-Za-z0-9_.-]+",expected_full_name) is not None,
            "EXPECTED_VAULT")
    require(repo["full_name"]==expected_full_name and
            repo["full_name"]!=CONTROLLER and
            repo["full_name"].split("/",1)[0]==owner["login"],
            "VAULT_IDENTITY")
    require(repo["private"] is True and repo["visibility"]=="private",
            "VAULT_MUST_BE_PRIVATE")
    require(repo["archived"] is False and repo["disabled"] is False,
            "VAULT_UNAVAILABLE")
    require(owner["login"]=="Tirthanand17","VAULT_UNAPPROVED_OWNER")
    return {"vault_metadata_shape_checked":True,
            "access_control_verified_with_live_api":False,
            "owner_approval_verified":False,
            "can_download_copyrighted_media":False}

def validate_public_paths(files: list[str], *, allowed_visuals: list[str]) -> dict:
    """Validate a public-repo Branch 3 file inventory.

    PNG and JPEG footage screenshots are denied except two verified original
    channel-identity PNGs. This is a filename boundary, not copyright analysis.
    """
    require(type(files) is list and len(files)<=10_000,"TREE_SIZE")
    require(type(allowed_visuals) is list and set(allowed_visuals)==BRANDING_ALLOWLIST,
            "ALLOWLIST")
    seen=set()
    for name in files:
        require(type(name) is str and name.startswith("branch3/"),"BRANCH3_SCOPE")
        require(name not in seen,"DUPLICATE_PATH")
        seen.add(name)
        parts=Path(name).parts
        require(".." not in parts and "\\" not in name and
                not name.startswith("/") and not name.endswith("/"),
                "PATH_TRAVERSAL")
        suffix=Path(name).suffix.lower()
        require(name in BRANDING_ALLOWLIST or
                (suffix in PUBLIC_SAFE_SUFFIXES and
                 not any(x in name.lower() for x in (
                    "credentials.json","oauth.json","refresh_token","raw_contract",
                    "private_agreement","licensed_source",
                    "signed_access_url","source_media.mp4",
                 ))),"UNSAFE_PUBLIC_MEDIA_OR_SECRET")
        require(suffix not in RESTRICTED_EXTENSIONS,"RESTRICTED_MEDIA")
    return {"public_paths_checked":len(seen),
            "allowed_original_visuals_present":sum(x in seen for x in BRANDING_ALLOWLIST),
            "licensed_media_detected":False,
            "rights_documents_in_public_repo":False}

def validate_policy(policy: dict, manifest: dict, perms: dict,
                    channel: dict) -> dict:
    require(type(policy) is dict and set(policy)=={
        "schema_version","phase","controller_repository",
        "controller_repository_visibility","target_channel_id","mode",
        "preferred_backend","private_vault_repository",
        "private_vault_repository_identity_verified","private_vault_owner_approved",
        "identity_and_access_review_complete","creator_grants_verified",
        "owner_contract_scope_reviewed","github_production_environment_protection_verified",
        "media_fetch_enabled","media_write_enabled","media_render_enabled",
        "youtube_upload_enabled","data_policy","approved_public_visuals",
        "no_source_media_approved","notes",
    },"POLICY_KEYS")
    require(policy["schema_version"]==1 and
            policy["phase"]=="A3_CONFIDENTIAL_MEDIA_STORAGE_PREFLIGHT",
            "POLICY_VERSION")
    require(policy["controller_repository"]==CONTROLLER and
            policy["controller_repository_visibility"]=="public" and
            policy["target_channel_id"]==CLIVOX,"WRONG_CHANNEL_OR_REPOSITORY")
    require(policy["mode"]=="NOT_PROVISIONED" and
            policy["preferred_backend"]=="github_private_release_asset",
            "UNAPPROVED_STORAGE_BACKEND")
    require(policy["private_vault_repository"] is None,"UNAPPROVED_VAULT")
    require(policy["creator_grants_verified"]==0 and
            policy["no_source_media_approved"] is True,
            "UNVERIFIED_RIGHTS")
    for field in (
        "private_vault_repository_identity_verified","private_vault_owner_approved",
        "identity_and_access_review_complete","owner_contract_scope_reviewed",
        "github_production_environment_protection_verified","media_fetch_enabled",
        "media_write_enabled","media_render_enabled","youtube_upload_enabled",
    ):
        require(policy[field] is False,"PREMATURE_ENABLE_"+field)
    dp=policy["data_policy"]
    require(type(dp) is dict and set(dp)=={
        "public_repo_raw_rights_media_allowed",
        "public_actions_artifact_rights_media_allowed",
        "public_lfs_rights_media_allowed",
        "public_issue_attachments_rights_media_allowed",
        "private_contract_bytes_in_public_repo_allowed",
        "ephemeral_runner_temp_only","explicit_object_sha256_required",
        "exact_channel_identity_required","rights_expiry_recheck_required",
        "no_blind_retry_on_download_errors",
    },"DATA_POLICY_KEYS")
    for key in (
        "public_repo_raw_rights_media_allowed",
        "public_actions_artifact_rights_media_allowed",
        "public_lfs_rights_media_allowed",
        "public_issue_attachments_rights_media_allowed",
        "private_contract_bytes_in_public_repo_allowed",
    ):
        require(dp[key] is False,"PUBLIC_LEAK_"+key)
    for key in (
        "ephemeral_runner_temp_only","explicit_object_sha256_required",
        "exact_channel_identity_required","rights_expiry_recheck_required",
        "no_blind_retry_on_download_errors",
    ):
        require(dp[key] is True,"STORAGE_CHECK_MISSING_"+key)
    require(policy["approved_public_visuals"]==sorted(BRANDING_ALLOWLIST),
            "APPROVED_VISUALS_CHANGED")
    require(type(manifest) is dict and set(manifest)=={
        "schema_version","media_id","channel_id","status","kind","source",
        "permission","vault","controls","private_bytes_embedded",
        "user_secrets_embedded","note"
    },"MANIFEST_KEYS")
    require(manifest["schema_version"]==1 and
            manifest["channel_id"]==CLIVOX and
            manifest["status"]=="RESEARCH_ONLY_NO_LICENSE",
            "MANIFEST_UNAPPROVED")
    require(type(manifest["media_id"]) is str and
            MEDIA_ID.fullmatch(manifest["media_id"]) is not None,"MEDIA_ID")
    require(manifest["kind"]=="third_party_original_source","MEDIA_KIND")
    source=manifest["source"]
    require(type(source) is dict and set(source)=={
        "platform","video_id","canonical_url","exact_in_ms","exact_out_ms"
    },"SOURCE_KEYS")
    require(source["platform"]=="youtube" and
            type(source["video_id"]) is str and
            VIDEO_ID.fullmatch(source["video_id"]) is not None and
            source["canonical_url"]=="https://www.youtube.com/watch?v="+source["video_id"],
            "SOURCE_ID")
    require(source["exact_in_ms"] is None and
            source["exact_out_ms"] is None,"UNVERIFIED_SOURCE_SEGMENT")
    grant=manifest["permission"]
    require(type(grant) is dict and set(grant)=={
        "source_creator_rights_grant_verified",
        "source_creator_rights_grant_fingerprint_sha256",
        "commercial_youtube_reuse_verified",
        "music_visuals_guests_and_publisher_rights_cleared",
        "permission_active_reverified","license_expires_at_utc",
        "contract_owner_reviewed"
    },"PERMISSION_KEYS")
    for field in (
        "source_creator_rights_grant_verified",
        "commercial_youtube_reuse_verified",
        "music_visuals_guests_and_publisher_rights_cleared",
        "permission_active_reverified","contract_owner_reviewed",
    ):
        require(grant[field] is False,"FORGED_GRANT_"+field)
    require(grant["source_creator_rights_grant_fingerprint_sha256"] is None and
            grant["license_expires_at_utc"] is None,"FORGED_GRANT_EVIDENCE")
    vault=manifest["vault"]
    require(type(vault) is dict and set(vault)=={
        "provider","private_repository","asset_id","release_tag",
        "expected_sha256","expected_bytes","privacy_rechecked_with_authenticated_api",
    },"VAULT_KEYS")
    require(vault["provider"]=="github_private_release_asset" and
            all(vault[x] is None for x in (
                "private_repository","asset_id","release_tag",
                "expected_sha256","expected_bytes"
            )) and vault["privacy_rechecked_with_authenticated_api"] is False,
            "VAULT_REFERENCE_FORGED")
    controls=manifest["controls"]
    require(type(controls) is dict and set(controls)=={
        "vault_object_exists","media_fetch_authorized","media_stage_authorized",
        "render_authorized","upload_authorized","publish_authorized",
    } and all(v is False for v in controls.values()),
            "MEDIA_ACTION_AUTHORIZED")
    require(manifest["private_bytes_embedded"] is False and
            manifest["user_secrets_embedded"] is False,"PRIVATE_BYTES_LEAK")
    require(type(perms) is dict and
            perms.get("policy")=="EXPLICIT_CREATOR_GRANT_ONLY" and
            perms.get("creators")==[],"ALLOWLIST_NONEMPTY")
    require(type(channel) is dict and channel.get("channel_id")==CLIVOX and
            channel.get("release_gates",{}).get("verified_creator_permissions_count")==0 and
            channel.get("release_gates",{}).get("publishing_channel_oauth_connected") is False and
            channel.get("channel_settings",{}).get("automatic_publishing_enabled") is False,
            "UNAUTHORIZED_CHANNEL_RELEASE")
    return {
        "stage":"A3_PRIVATE_MEDIA_PREFLIGHT",
        "channel_id":CLIVOX,
        "status":"BLOCKED_UNTIL_OWNER_APPROVES_PRIVATE_VAULT_AND_CREATOR_RIGHTS",
        "creator_grants":0,
        "private_media_vault_provisioned":False,
        "third_party_media_stored":False,
        "private_contracts_stored_in_public_repo":False,
        "source_download_authorized":False,
        "source_upload_authorized":False,
        "youtube_upload_authorized":False,
        "youtube_publish_authorized":False,
    }

def check_no_upload_side_effects() -> None:
    raise StorageDenied("CLIVOX_A3_DENY_ACTUAL_MEDIA_OPERATIONS_NOT_IMPLEMENTED")

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    result=validate_policy(read_json(POLICY),read_json(MANIFEST),
        read_json(CREATOR_PERMS),read_json(CHANNEL_STATE))
    # Filename-only verification; actual check of tracked files in CI uses
    # the git tree so untracked local user files cannot grant security.
    files=[
        str(p.relative_to(ROOT)).replace("\\","/")
        for p in (ROOT/"branch3").rglob("*") if p.is_file()
    ]
    result.update(validate_public_paths(files,allowed_visuals=[
        *sorted(BRANDING_ALLOWLIST)
    ]))
    raw=json.dumps(result,indent=2)+"\n"
    if args.out:
        require(not args.out.is_symlink(),"OUTPUT_SYMLINK")
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(raw,encoding="utf-8")
    else:
        print(raw,end="")
    print("CLIVOX_A3_NO_PRIVATE_MEDIA_NO_VAULT_PROVISIONED_NO_YOUTUBE_WRITES")

if __name__=="__main__":
    main()
