"""Clivox architecture offline safety validation: DESIGN ONLY, no API, no media.

Run from a GitHub-hosted runner with Python standard library.
Successful validation NEVER grants third-party rights, signs a release or calls YouTube.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
ARCH=ROOT/"branch3/architecture/architecture-config.json"
GRAPH=ROOT/"branch3/contracts/state-machine.json"
SCHEMA=ROOT/"branch3/contracts/clip-job.schema.json"
EXAMPLE=ROOT/"branch3/contracts/example-discovered-job.json"
PERMS=ROOT/"branch3/creator_permissions.json"
CHANNEL=ROOT/"branch3/channel_state.json"
WATCHLIST=ROOT/"branch3/clip_source_watchlist_2026-11-12.json"
CLIVOX_ID="UCfPEvy0SefE_5nNlYlY_CyQ"
FLOWMINUTE_ID="UCCcL9Q_jqVq6LJmnYUSAFZA"
SHA=re.compile(r"[a-f0-9]{64}\Z")
VIDEO=re.compile(r"[a-zA-Z0-9_-]{11}\Z")
JOB=re.compile(r"clivox_[a-z0-9][a-z0-9_-]{6,80}\Z")

class ArchitectureBlocked(ValueError):
    """Unsafe architecture or operation; never treat this as authorization."""

def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ArchitectureBlocked("CLIVOX_DENY_"+reason)

def data(path: Path) -> dict:
    loaded=json.loads(path.read_text(encoding="utf-8"))
    require(type(loaded) is dict,"DOCUMENT_NOT_OBJECT")
    return loaded

def validate_architecture(
    cfg: dict, graph: dict, schema: dict, job: dict, channel: dict, perms: dict,
) -> None:
    require(cfg.get("architecture_state")=="DESIGN_ONLY","NO_PRODUCTION_DEPLOYMENT")
    require(cfg.get("channel_id")==CLIVOX_ID and cfg.get("release",{}).get("target_channel_id")==CLIVOX_ID,"WRONG_CHANNEL")
    require(FLOWMINUTE_ID not in json.dumps(cfg),"FLOWMINUTE_TOKEN_CROSSOVER")
    require(cfg.get("handle")=="@ClivoxPulse" and cfg.get("source_owner_repo")=="Tirthanand17/taskless-lab","WRONG_REPOSITORY")
    isolation=cfg.get("isolation",{})
    require(isolation.get("branch1_paused") is True and isolation.get("branch2_paused") is True,"PAUSED_BRANCH_NOT_ISOLATED")
    require(isolation.get("reuse_flowminute_youtube_tokens") is False
            and isolation.get("separate_clivox_oauth_configured") is False,"WRONG_OAUTH")
    storage=cfg.get("storage",{})
    require(storage.get("public_repo_contains_copyrighted_raw_video") is False
            and storage.get("raw_license_documents_public") is False
            and storage.get("private_media_escrow_enabled") is False
            and storage.get("cloud_hosted_runners_only") is True,"PUBLIC_MEDIA_LEAK")
    require(storage.get("raw_media_storage")=="NOT_SELECTED_REQUIRE_OWNER_APPROVAL","UNAPPROVED_MEDIA_STORAGE")
    safety=cfg.get("safety",{})
    require(safety.get("approved_creators_count")==0,"INVENTED_RIGHTS")
    for flag in (
        "auto_download_enabled","auto_publish_enabled","api_write_calls_enabled",
        "global_upload_enabled","owner_signing_implemented",
        "github_environment_protection_configured",
    ):
        require(safety.get(flag) is False,"AUTOMATION_ENABLED_"+flag)
    release=cfg.get("release",{})
    require(release.get("state")=="DISABLED_BY_DESIGN"
            and release.get("default_visibility")=="private","PRODUCTION_ENABLED")
    for flag in (
        "require_remote_owner_identity","require_future_utc_schedule",
        "require_exact_signed_release","require_human_rights_review",
        "require_original_commentary","require_live_remote_readback",
    ):
        require(release.get(flag) is True,"MISSING_RELEASE_GUARD_"+flag)
    require(release.get("min_schedule_margin_minutes")>=30
            and release.get("duplicate_upload_policy")=="RECONCILE_DO_NOT_BLIND_RETRY","UNSAFE_SCHEDULING")
    discovery=cfg.get("discovery",{})
    require(discovery.get("a1_metadata_adapter_implemented") is True
            and discovery.get("live_metadata_api_key_verified") is False
            and discovery.get("execution")=="manual_github_actions_only","DISCOVERY_MODE_NOT_SAFE")
    require(discovery.get("fixed_api_host")=="https://www.googleapis.com/youtube/v3/"
            and discovery.get("max_known_source_ids_per_run")==30
            and discovery.get("max_search_results_per_run")==10
            and discovery.get("max_search_calls_per_run")==1
            and discovery.get("max_video_details_calls_per_run")==1,"UNBOUNDED_DISCOVERY")
    require(discovery.get("third_party_source_download_allowed") is False
            and discovery.get("clip_permission_inferred_from_popularity") is False
            and discovery.get("output_status")=="RESEARCH_ONLY_PUBLIC_METADATA","DISCOVERY_RIGHTS_BYPASS")
    intake=cfg.get("rights_intake",{})
    require(intake.get("a2_pending_review_case_generator_implemented") is True
            and intake.get("a2_human_rights_grant_verification_implemented") is False
            and intake.get("actual_verified_creator_grants")==0
            and intake.get("real_contract_review_completed") is False
            and intake.get("creator_allowlist_automatically_modified") is False
            and intake.get("source_media_acquisition_authorized") is False
            and intake.get("public_report_contains_private_legal_agreements") is False
            and intake.get("output_status")=="AWAITING_REAL_RIGHTS_HOLDER_VERIFICATION",
            "RIGHTS_INTAKE_PRETENDS_APPROVAL")
    require(cfg.get("metrics",{}).get("missing_metric_policy")=="NULL_NOT_ZERO","INVENTED_ANALYTICS")
    require(cfg.get("categories")==["gaming","livestream","comedy","entertainment","podcast_interview"],"WRONG_CATEGORIES")
    require(channel.get("channel_id")==CLIVOX_ID
            and channel.get("channel_settings",{}).get("upload_default_visibility")=="private"
            and channel.get("channel_settings",{}).get("automatic_publishing_enabled") is False,"WRONG_LIVE_ACCOUNT")
    require(channel.get("release_gates",{}).get("verified_creator_permissions_count")==0
            and channel.get("release_gates",{}).get("publishing_channel_oauth_connected") is False
            and channel.get("release_gates",{}).get("videos_uploaded_by_this_setup")==0,"FALSE_LIVE_RELEASE")
    require(perms.get("policy")=="EXPLICIT_CREATOR_GRANT_ONLY" and perms.get("creators")==[],"UNVERIFIED_CREATOR_ADDED")
    require(graph.get("kind")=="TARGET_STATE_GRAPH_NOT_DEPLOYED"
            and graph.get("no_automated_transition_implementation") is True,"STATE_MACHINE_LIVE")
    states=graph.get("states",[])
    transitions=graph.get("transitions",{})
    require(type(states) is list and type(transitions) is dict
            and len(states)==len(set(states)) and set(states)==set(transitions),"INCONSISTENT_GRAPH")
    require(graph.get("initial_state")=="DISCOVERED"
            and graph.get("terminal_states")==["MEASURED","REVOKED"],"UNEXPECTED_STATE_ROOTS")
    for source,targets in transitions.items():
        require(type(targets) is list and len(targets)==len(set(targets)) and all(t in states for t in targets),"BAD_GRAPH_EDGE")
        require(source not in targets,"GRAPH_SELF_LOOP")
    require(not transitions["MEASURED"] and not transitions["REVOKED"],"UNSAFE_TERMINAL_TRANSITION")
    protected={"RIGHTS_VERIFIED","OWNER_SIGNED","PRIVATE_UPLOADED","SCHEDULED","PUBLISHED"}
    require(set(graph.get("prohibited_without_external_human_or_owner_proof",[]))==protected,"MISSING_HUMAN_GATE")
    require(schema.get("$schema")=="https://json-schema.org/draft/2020-12/schema"
            and schema.get("properties",{}).get("channel_id",{}).get("const")==CLIVOX_ID,"INVALID_SCHEMA")
    require(schema.get("additionalProperties") is False
            and "rights" in schema.get("required",[])
            and "release" in schema.get("required",[]),"WEAK_SCHEMA")
    require(job.get("schema_version")==1 and job.get("channel_id")==CLIVOX_ID
            and job.get("status")=="DISCOVERED","JOB_ALREADY_ADVANCED")
    require(type(job.get("clip_id")) is str and JOB.fullmatch(job["clip_id"]) is not None,"BAD_CLIP_ID")
    require(job.get("category") in cfg["categories"],"WRONG_CATEGORY")
    src=job.get("source",{})
    require(type(src.get("video_id")) is str and VIDEO.fullmatch(src["video_id"]) is not None
            and src.get("canonical_url")==f"https://www.youtube.com/watch?v={src['video_id']}","BAD_SOURCE_URL")
    require(src.get("creator_channel_id") is None and src.get("exact_in_ms") is None
            and src.get("exact_out_ms") is None and src.get("transcript_checked") is False,"INVENTED_TRANSCRIPT")
    rights=job.get("rights",{})
    require(rights.get("permission_state")=="unverified"
            and rights.get("creator_issuer_verified") is False
            and rights.get("commercial_youtube_licensed") is False
            and rights.get("game_music_guest_rights_cleared") is False
            and rights.get("evidence_digest_sha256") is None
            and rights.get("rights_expire_utc") is None,"INVENTED_LICENSE")
    require(job.get("editorial",{}).get("original_story_approved") is False
            and job.get("editorial",{}).get("fact_check_complete") is False,"INVENTED_EDITORIAL_APPROVAL")
    media=job.get("media",{})
    require(media.get("media_sha256") is None
            and media.get("metadata_sha256") is None
            and media.get("qa_passed") is False
            and media.get("file_in_public_repo") is False,"UNLICENSED_MEDIA")
    require(job.get("release",{}).get("owner_signed") is False
            and job.get("release",{}).get("signed_release_proof_ref") is None
            and job.get("release",{}).get("release_enabled") is False,"FAKE_RELEASE_APPROVAL")
    yt=job.get("youtube",{})
    require(yt.get("video_id") is None
            and yt.get("privacy")=="not_uploaded"
            and yt.get("publish_at_utc") is None
            and yt.get("readback_verified") is False,"YOUTUBE_WRITE_CLAIM")
    analytics=job.get("analytics",{})
    require(analytics.get("engaged_views") is None
            and analytics.get("shown_in_feed") is None
            and analytics.get("reviewed") is False,"INVENTED_ANALYTICS_DATA")

def preview_state_transition(graph: dict, source: str, target: str) -> dict:
    """Preview a graph edge only; no persistence and no protected authorization."""
    transitions=graph.get("transitions",{})
    require(source in transitions and target in transitions[source],"ILLEGAL_STATE_TRANSITION")
    require(target not in graph.get("prohibited_without_external_human_or_owner_proof",[]),
            "PROTECTED_TRANSITION_NOT_IMPLEMENTED")
    return {"source":source,"target":target,"mode":"PLAN_ONLY_NO_SIDE_EFFECTS","release_authorized":False}

def preview_schedule(time_utc: str, *, now: datetime, privacy: str,
                     channel_id: str, margin_minutes: int=30) -> dict:
    """Strict time validator; does NOT call an uploader or authorize publication."""
    require(channel_id==CLIVOX_ID,"WRONG_CHANNEL")
    require(privacy=="private","UNSAFE_PRIVACY")
    require(type(time_utc) is str and time_utc.endswith("Z"),"NON_UTC_SCHEDULE")
    require(now.tzinfo is not None and now.utcoffset() is not None,"NAIVE_NOW")
    try:
        future=datetime.fromisoformat(time_utc[:-1]+"+00:00")
    except (ValueError,TypeError):
        raise ArchitectureBlocked("CLIVOX_DENY_INVALID_SCHEDULE") from None
    require(future>now.astimezone(timezone.utc)+timedelta(minutes=margin_minutes),
            "SCHEDULE_NOT_SAFELY_FUTURE")
    return {"normalized_publish_at":future.isoformat().replace("+00:00","Z"),
            "mode":"PLAN_ONLY_NO_YOUTUBE_CALL","release_authorized":False,
            "youtube_upload_authorized":False}

def assert_no_api_write_allowed(cfg: dict) -> None:
    """Always reject API writes: production module intentionally does not exist."""
    require(False,"ARCHITECTURE_ONLY_NO_YOUTUBE_WRITES")

def main() -> None:
    validate_architecture(data(ARCH),data(GRAPH),data(SCHEMA),data(EXAMPLE),data(CHANNEL),data(PERMS))
    # The legacy research watchlist is *not* a license.
    watchlist=data(WATCHLIST)
    require(watchlist.get("all_candidates")=="RESEARCH_ONLY"
            and watchlist.get("creator_allowlist_empty") is True,"WATCHLIST_PRETENDS_LICENSE")
    print("BRANCH3_CLIVOX_ARCHITECTURE_VALIDATED_DESIGN_ONLY_ZERO_RIGHTS_ZERO_UPLOADS")

if __name__=="__main__":
    main()

