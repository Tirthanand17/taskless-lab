"""CLIVOX Branch 3 owner-closure state audit; proof claims fail CLOSED.

Reads public project policies and a *historical operator-authored* private
bootstrap report. Does not regard JSON as independent remote attestation.
Cannot certify real licensing, media, protected OAuth, durable ledgers,
video release or uploaded YouTube videos. It never calls external APIs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BOOTSTRAP=ROOT/"branch3/architecture/verified-private-bootstrap.json"
TRACKER=ROOT/"branch3/architecture/progress-tracker.json"
ARCH=ROOT/"branch3/architecture/architecture-config.json"
CREATORS=ROOT/"branch3/creator_permissions.json"
RELEASE=ROOT/"branch3/release/release-policy.json"
A2_POLICY=ROOT/"branch3/rights_review/private-ledger-policy.json"
A8_POLICY=ROOT/"branch3/a8/private-cas-policy.json"
CHANNEL="UCfPEvy0SefE_5nNlYlY_CyQ"


class ClosureDenied(ValueError):
    """False permission, wrong channel or forged readiness hard-stops."""


def require(ok:bool,code:str) -> None:
    if not ok:
        raise ClosureDenied("CLIVOX_B3_OWNER_GATE_DENIED_"+code)


def read_json(path:Path) -> dict:
    require(path.is_file() and not path.is_symlink()
            and path.stat().st_size<150_000, "FILE_UNSAFE")
    data=json.loads(path.read_text(encoding="utf-8"))
    require(type(data) is dict,"JSON_FORMAT")
    return data


def check_closed_state(*,bootstrap:dict,tracker:dict,arch:dict,
                       creators:dict,release:dict,
                       a2_policy:dict,a8_policy:dict) -> dict:
    require(type(bootstrap) is dict
            and bootstrap.get("schema_version")==1
            and bootstrap.get("channel_id")==CHANNEL
            and bootstrap.get("status")==
              "PRIVATE_METADATA_BOOTSTRAPPED_OWNER_RIGHTS_CREDENTIALS_ABSENT",
            "BOOTSTRAP_IDENTITY")
    repo=bootstrap.get("control_repository")
    require(type(repo) is dict
            and repo.get("separate_clivox_private_metadata_repo_created") is True
            and repo.get("privacy_and_owner_admin_checked_live") is True
            and repo.get("default_branch_main_checked_live") is True
            and repo.get("only_owner_listed_as_collaborator_at_readback") is True
            and repo.get("installed_app_access_and_external_backups_audited") is False
            and repo.get("actual_owner_approved_licensed_media_storage") is False
            and repo.get("copyrighted_source_or_contract_uploads")==0
            and repo.get("private_name_intentionally_not_in_public_report") is True,
            "FALSE_PRIVATE_STORAGE_SCOPE")
    ledgers=bootstrap.get("genesis_ledgers")
    require(type(ledgers) is dict
            and ledgers.get("a2_revocation_journal_private_file_created") is True
            and ledgers.get("a8_upload_attempt_journal_private_file_created") is True
            and ledgers.get("a2_revocation_events")==0
            and ledgers.get("a8_upload_attempt_events")==0
            and ledgers.get("both_channel_ids_checked") is True
            and ledgers.get("production_key_independently_enrolled") is False
            and ledgers.get("nonrollbackable_external_anchor_exists") is False
            and ledgers.get("authenticated_live_cross_run_writer_exists") is False,
            "FALSE_LEDGER_TRUST")
    envs=bootstrap.get("controller_environments")
    require(type(envs) is dict and set(envs)=={
        "clivox-vault-readonly","clivox-release"
    },"ENVIRONMENTS_MISSING")
    for name,env in envs.items():
        require(type(env) is dict and env.get("exists") is True
                and env.get("required_reviewer_owner_verified") is True
                and env.get("deploy_main_only_verified") is True
                and env.get("admin_bypass_disabled_verified") is True
                and env.get("environment_secret_count_at_readback")==0,
                "ENVIRONMENT_UNVERIFIED_"+name)
        action="actual_private_ledger_authenticated_script_run" if name=="clivox-vault-readonly" else "actual_release_or_youtube_upload_executed"
        require(env.get(action) is False,"FALSE_LIVE_ACTION_"+name)
    channel=bootstrap.get("channel")
    require(type(channel) is dict
            and channel.get("creator_issued_commercial_licenses_verified")==0
            and channel.get("actual_licensed_media_assets")==0
            and channel.get("signed_owner_video_releases")==0
            and channel.get("genuine_clivox_google_oauth_credentials_configured") is False
            and channel.get("real_youtube_upload_inventory_readback_executed") is False
            and channel.get("real_youtube_videos_uploaded_by_project")==0
            and channel.get("live_publication_enabled") is False,
            "FAKE_CHANNEL_READINESS")
    for field in (
        "approved_for_private_media_storage","approved_for_source_download",
        "approved_for_real_ledger_writes","approved_for_youtube_upload",
        "approved_for_youtube_schedule","approved_for_youtube_publish"
    ):
        require(bootstrap.get(field) is False,"PREMATURE_BOOTSTRAP_PERMISSION_"+field)
    require(bootstrap.get("public_record_is_not_live_continuous_attestation") is True,
            "FALSE_REPOSITORY_ATTESTATION")
    require(type(tracker) is dict
            and tracker.get("channel_id")==CHANNEL
            and tracker.get("creator_licenses_verified")==0
            and tracker.get("clivox_videos_uploaded")==0
            and tracker.get("github_private_media_vault_provisioned") is False
            and tracker.get("publishing_enabled") is False
            and tracker.get("branch1_and_branch2_paused") is True,
            "FALSE_PROGRESS_STATE")
    require(type(arch) is dict and arch.get("channel_id")==CHANNEL
            and arch.get("storage",{}).get("private_media_escrow_enabled") is False
            and arch.get("safety",{}).get("auto_publish_enabled") is False
            and arch.get("safety",{}).get("api_write_calls_enabled") is False
            and arch.get("isolation",{}).get("reuse_flowminute_youtube_tokens") is False,
            "FALSE_ARCHITECTURE_STATE")
    require(type(creators) is dict and creators.get("creators")==[]
            and creators.get("policy")=="EXPLICIT_CREATOR_GRANT_ONLY",
            "FAKE_LICENSE_REGISTRY")
    require(type(release) is dict and release.get("real_verified_creator_licenses")==0
            and release.get("real_signed_releases")==0
            and release.get("youtube_write_enabled") is False,
            "FAKE_OWNER_RELEASE")
    require(type(a2_policy) is dict
            and a2_policy.get("actual_creator_grants_approved")==0
            and a2_policy.get("remote_github_get_or_put_enabled") is False
            and a2_policy.get("source_media_download_enabled") is False,
            "FAKE_A2_PERMISSION")
    require(type(a8_policy) is dict
            and a8_policy.get("creator_licenses_authenticated")==0
            and a8_policy.get("cross_runner_durable_ledger_verified") is False
            and a8_policy.get("actual_github_get_put_enabled") is False
            and a8_policy.get("youtube_api_writes_enabled") is False,
            "FAKE_A8_PERMISSION")
    # A documented historical verification is not a currently trusted remote
    # service, proof of license, or owner consent. No PR/CI may promote this.
    return {
        "stage":"B3_OWNER_PRODUCTION_CLOSURE_GATE_READONLY",
        "status":"BLOCKED_MISSING_REAL_RIGHTS_OWNER_AUTH_AND_PRODUCTION_EVIDENCE",
        "private_metadata_repository_provisioned":True,
        "empty_a2_revocation_journal_bootstrapped":True,
        "empty_a8_upload_attempt_ledger_bootstrapped":True,
        "owner_review_and_main_only_empty_secret_environments_observed":True,
        "external_provisioning_record_is_historical_not_live_verified":True,
        "private_media_vault_owner_approval":False,
        "rights_holder_grants_authenticated":0,
        "real_owner_video_signatures":0,
        "dedicated_clivox_google_oauth_connected":False,
        "nonrollbackable_external_anchor_proven":False,
        "real_youtube_inventory_reconciled":False,
        "first_licensed_pilot_completed":False,
        "youtube_upload_authorized":False,
        "youtube_schedule_authorized":False,
        "youtube_publish_authorized":False,
        "actual_external_api_calls":0,
        "next_human_dependencies":[
            "ACTUAL_RIGHTSHOLDER_COMMERCIAL_REUSE_GRANTS",
            "OWNER_AUDIT_OF_APP_ACCESS_AND_PRIVATE_MEDIA_STORAGE_APPROVAL",
            "OWNER_ENROLLED_REVIEW_REVOCATION_AND_A6_SIGNER_KEYS",
            "NONROLLBACKABLE_SIGNED_JOURNAL_CHECKPOINTS",
            "CLIVOX_ONLY_GOOGLE_READ_AND_SEPARATE_UPLOAD_OAUTH",
            "LICENSED_HUMAN_APPROVED_ORIGINAL_VIDEO_AND_EXACT_A6_RELEASE",
            "AUTHENTICATED_VIDEO_ID_RECONCILIATION_AND_PRIVATE_FIRST_PILOT"
        ]
    }


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("audit",),default="audit")
    p.parse_args()
    result=check_closed_state(
        bootstrap=read_json(BOOTSTRAP),tracker=read_json(TRACKER),
        arch=read_json(ARCH),creators=read_json(CREATORS),
        release=read_json(RELEASE),a2_policy=read_json(A2_POLICY),
        a8_policy=read_json(A8_POLICY)
    )
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
