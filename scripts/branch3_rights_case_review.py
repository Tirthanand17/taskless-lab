"""Clivox A2: offline review of source-rights dossiers.

A passing structural review is NEVER a grant, a contract acceptance, a source
download or an upload authorization. This tool emits unresolved gate evidence.
No HTTP, OAuth, third-party media retrieval or YouTube modifications.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
CASES=ROOT/"branch3/rights_cases"
CHANNEL="UCfPEvy0SefE_5nNlYlY_CyQ"
PERMS=ROOT/"branch3/creator_permissions.json"
LIVE=ROOT/"branch3/channel_state.json"
CASE_ID=re.compile(r"clivox_[a-z0-9][a-z0-9_-]{5,80}\Z")
VIDEO_ID=re.compile(r"[A-Za-z0-9_-]{11}\Z")
URL_LIMIT=1200
MAX_CASE_BYTES=120_000
REQUIRED_CHECKS=(
    "issuer_controls_source_rights",
    "original_youtube_source_confirmed",
    "clip_and_edit_permission",
    "youtube_shorts_redistribution",
    "youtube_commercial_use",
    "license_current_and_not_revoked",
    "source_timestamps_verified",
    "underlying_music_audio_cleared",
    "underlying_visuals_guests_cleared",
    "game_publisher_rights_when_applicable",
    "contract_scope_and_ownership_reviewed",
    "credit_and_sponsor_rules_reviewed",
)
ALLOWED_CASE_STATUS=frozenset({"RESEARCH_ONLY","NEEDS_HUMAN_REVIEW","BLOCKED"})
ALLOWED_PROOF_KIND=frozenset({
    "not_yet_provided",
    "direct_written_creator_grant",
    "creator_published_clipping_policy",
})
class RightsCaseDenied(ValueError):
    """Invalid or deceptively approved rights dossier."""

def require(ok: bool, code: str) -> None:
    if not ok:
        raise RightsCaseDenied("CLIVOX_A2_DENY_"+code)

def safe_public_url(value: object) -> bool:
    if type(value) is not str or not 1<len(value)<=URL_LIMIT:
        return False
    try:
        u=urlsplit(value)
        return u.scheme=="https" and u.hostname is not None and u.username is None \
            and u.password is None and u.fragment=="" and u.query=="" \
            and u.port in (None,443)
    except ValueError:
        return False

def check_dossier(d: object) -> dict:
    require(type(d) is dict and set(d)=={
        "schema_version","case_id","case_status","channel_id","source",
        "permission","underlying_rights","contract","review","controls",
    },"CASE_KEYS")
    require(d["schema_version"]==1 and d["channel_id"]==CHANNEL,"CHANNEL_OR_VERSION")
    require(type(d["case_id"]) is str and CASE_ID.fullmatch(d["case_id"]) is not None,"CASE_ID")
    require(d["case_status"] in ALLOWED_CASE_STATUS,"MUST_BE_UNAPPROVED")
    source=d["source"]
    require(type(source) is dict and set(source)=={
        "platform","original_video_id","original_video_url","creator_name","original_creator_channel_id",
        "category","time_in_ms","time_out_ms",
    },"SOURCE_KEYS")
    require(source["platform"]=="youtube","SOURCE_PLATFORM")
    vid=source["original_video_id"]
    require(type(vid) is str and VIDEO_ID.fullmatch(vid) is not None
            and source["original_video_url"]=="https://www.youtube.com/watch?v="+vid,
            "SOURCE_ID")
    require(type(source["creator_name"]) is str and 2<=len(source["creator_name"])<=120,"CREATOR_NAME")
    require(source["category"] in ("gaming","livestream","comedy","entertainment","podcast_interview"),"CATEGORY")
    require(source["original_creator_channel_id"] is None
            or (type(source["original_creator_channel_id"]) is str
            and re.fullmatch(r"UC[A-Za-z0-9_-]{22}",source["original_creator_channel_id"]) is not None),
            "SOURCE_CHANNEL_ID")
    for field in ("time_in_ms","time_out_ms"):
        require(source[field] is None or (type(source[field]) is int
                and 0<=source[field]<=100_000_000),"TIMESTAMP")
    require((source["time_in_ms"] is None)==(source["time_out_ms"] is None),"TIMESTAMP_PAIR")
    if source["time_in_ms"] is not None:
        require(source["time_out_ms"]>source["time_in_ms"],"TIMESTAMP_ORDER")
    perm=d["permission"]
    require(type(perm) is dict and set(perm)=={
        "kind","public_invitation_url","actual_grant_reference","evidence_sha256",
        "issuer_identity_verified","commercial_rights_confirmed","scope_confirmed",
        "revocation_checked","expires_at_utc",
    },"GRANT_KEYS")
    require(perm["kind"] in ALLOWED_PROOF_KIND,"GRANT_KIND")
    require(perm["public_invitation_url"] is None
            or safe_public_url(perm["public_invitation_url"]),"PUBLIC_URL")
    # Raw private agreements, access links, contracts or contact details must
    # never be copied into a public Git repository.
    require(perm["actual_grant_reference"] is None
            or (type(perm["actual_grant_reference"]) is str
                and re.fullmatch(r"public-ref:[a-z0-9_-]{12,80}",perm["actual_grant_reference"]) is not None),
            "PRIVATE_EVIDENCE_LEAK")
    require(perm["evidence_sha256"] is None
            or (type(perm["evidence_sha256"]) is str and
                re.fullmatch(r"[0-9a-f]{64}",perm["evidence_sha256"]) is not None),"EVIDENCE_DIGEST")
    for field in ("issuer_identity_verified","commercial_rights_confirmed",
                  "scope_confirmed","revocation_checked"):
        require(type(perm[field]) is bool,"GRANT_BOOLEAN")
    require(perm["expires_at_utc"] is None,"EXPIRED_STATUS_MUST_BE_HUMAN_REVIEWED")
    rights=d["underlying_rights"]
    require(type(rights) is dict and set(rights)=={
        "music_cleared","guests_cleared","visuals_cleared","game_publisher_cleared",
        "third_party_claims_reviewed",
    },"UNDERLYING_KEYS")
    require(all(type(x) is bool for x in rights.values()),"UNDERLYING_BOOLEAN")
    contract=d["contract"]
    require(type(contract) is dict and set(contract)=={
        "terms_reviewed_by_owner","brand_ip_assignment_accepted_by_owner",
        "campaign_joined","copyright_claim_policy_reviewed",
        "sponsor_disclosure_reviewed",
    },"CONTRACT_KEYS")
    require(all(type(x) is bool for x in contract.values()),"CONTRACT_BOOLEAN")
    human=d["review"]
    require(type(human) is dict and set(human)=={
        "checklist","human_verifier_receipt","exact_media_owner_approval",
        "human_approver_identified",
    },"REVIEW_KEYS")
    checks=human["checklist"]
    require(type(checks) is dict and set(checks)==set(REQUIRED_CHECKS)
            and all(type(x) is bool for x in checks.values()),"CHECKLIST")
    require(human["human_verifier_receipt"] is None,"FORGED_REVIEW_RECEIPT")
    require(human["exact_media_owner_approval"] is False
            and human["human_approver_identified"] is False,"FORGED_OWNER_APPROVAL")
    controls=d["controls"]
    require(type(controls) is dict and controls=={
        "source_download_enabled":False,
        "render_enabled":False,
        "youtube_upload_enabled":False,
        "youtube_schedule_enabled":False,
        "allowlist_write_enabled":False,
    },"UNSAFE_CONTROLS")
    outstanding=[key for key in REQUIRED_CHECKS if checks[key] is False]
    if source["time_in_ms"] is None:
        outstanding.append("exact_source_timestamps_missing")
    if perm["kind"]=="not_yet_provided" or perm["actual_grant_reference"] is None:
        outstanding.append("creator_issued_grant_missing")
    if not contract["terms_reviewed_by_owner"]:
        outstanding.append("campaign_terms_owner_review_missing")
    if perm["public_invitation_url"] and perm["actual_grant_reference"] is None:
        outstanding.append("public_invitation_is_not_a_license")
    # Intentionally no "APPROVED" result in A2. Human evidence is required in a
    # future cryptographically verified gate; JSON booleans cannot grant rights.
    return {
        "case_id":d["case_id"],"channel_id":CHANNEL,
        "review_state":"HOLD_FOR_HUMAN_RIGHTS_AND_CONTRACT_REVIEW",
        "missing_gates":outstanding,
        "creator_license_verified_by_software":False,
        "media_download_allowed":False,
        "youtube_upload_allowed":False,
        "youtube_schedule_allowed":False,
        "permission_allowlist_mutated":False,
    }

def audit_folder(path: Path) -> dict:
    require(path.is_dir() and not path.is_symlink(),"CASE_DIRECTORY")
    files=sorted(path.glob("*.json"))
    require(0<len(files)<=40,"CASE_COUNT")
    summaries=[]
    seen=set()
    for file in files:
        require(not file.is_symlink() and file.stat().st_size<=MAX_CASE_BYTES,"UNSAFE_CASE_FILE")
        dossier=json.loads(file.read_text("utf-8"))
        report=check_dossier(dossier)
        require(report["case_id"] not in seen,"DUPLICATE_CASE")
        seen.add(report["case_id"])
        summaries.append(report)
    perms=json.loads(PERMS.read_text("utf-8"))
    live=json.loads(LIVE.read_text("utf-8"))
    require(perms.get("creators")==[] and perms.get("policy")=="EXPLICIT_CREATOR_GRANT_ONLY",
            "NONEMPTY_CREATOR_ALLOWLIST")
    require(live.get("channel_id")==CHANNEL
            and live.get("release_gates",{}).get("verified_creator_permissions_count")==0
            and live.get("channel_settings",{}).get("automatic_publishing_enabled") is False,
            "LIVE_RELEASE_ON")
    return {
        "schema_version":1,"stage":"A2_RIGHTS_DOSSIERS_OFFLINE_REVIEW_ONLY",
        "channel_id":CHANNEL,
        "cases_checked":len(summaries),"cases":summaries,
        "verified_licenses":0,"source_media_downloads":0,
        "youtube_writes":0,"publishing_enabled":False,
    }

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--cases",type=Path,default=CASES)
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    report=audit_folder(args.cases)
    raw=json.dumps(report,indent=2)+"\n"
    if args.out:
        require(not args.out.is_symlink(),"OUTPUT_SYMLINK")
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(raw,"utf-8")
    else:
        print(raw,end="")
    print("CLIVOX_A2_RIGHTS_CASES_RESEARCH_ONLY_ZERO_VERIFIED_RIGHTS_ZERO_YOUTUBE_WRITES")

if __name__=="__main__":
    main()
