"""FlowMinute B4g6 source-based phase audit, with strict evidence labels.

Source inspection confirms repository configuration, NOT production deployment,
authentication, publishing, human approval, or execution of the latest videos.
Use the separate date-stamped status document for actual GitHub run IDs and
external evidence. No network access, token, secrets, media, GitHub writes.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import json

RUBRIC = (
    ("Architecture, roles, CI and prototype", 15, 14),
    ("Observed public research and draft planning", 15, 8),
    ("Physical media and technical quality", 20, 16),
    ("Authenticated facts, rights and human review", 15, 2),
    ("Protected owner cloud deployment and persistence", 15, 4),
    ("Owner OAuth and verified real YouTube releases", 15, 0),
    ("Seven-day unattended 21-release acceptance", 5, 0),
)
PHASE_COUNTS = {"source_and_prototype_roles":48,"episodes":3,
                "original_voiced_scenes":17,"required_7_day_releases":21}
NO_EXTERNAL_EVIDENCE = "NOT_ESTABLISHED_BY_SOURCE_INSPECTION"


class PhaseAuditRefused(ValueError):
    """The audit source tree is wrong or a source-level safety gate regressed."""


def _need(ok: bool, message: str) -> None:
    if not ok:
        raise PhaseAuditRefused(message)


def _read(root: Path, relative: str) -> str:
    path=root.joinpath(*relative.split("/"))
    _need(path.is_file() and not path.is_symlink()
          and path.stat().st_size<=180_000,
          "Expected audit source is missing, symlinked or unexpectedly large")
    return path.read_text(encoding="utf8")


def inspect_source_acceptance(root: Path) -> dict:
    """Inspect fixed safety/trust boundaries, not a self-certified release."""
    _need(isinstance(root,Path) and root.is_dir()
          and not root.is_symlink(),
          "Require a local checked-out copy of the GitHub source tree")
    daily=_read(root,".github/workflows/flowminute-daily-cloud-foundation.yml")
    publisher=_read(root,".github/workflows/publish-artifact-youtube.yml")
    owner_readonly=_read(root,
        ".github/workflows/flowminute-owner-readonly-channel-audit-b4f6.yml")
    org=_read(root,"autopilot/agent_org.py")
    planner=_read(root,"autopilot/daily_cloud_plan.py")
    media=_read(root,"autopilot/full_original_rehearsal_media_b4e1.py")
    mastering=_read(root,"autopilot/verified_aac_mastering_b4g5.py")
    loudness=_read(root,"autopilot/encoded_aac_loudness_review_b4g4.py")
    portal=_read(root,"autopilot/offline_review_portal_b4e7.py")
    approval=_read(root,"scripts/publish_youtube.py")
    owner_signed=_read(root,"scripts/owner_signed_release_b4f1.py")
    inventory=_read(root,"autopilot/branch1_nov_repair_inventory.py")
    gates={
        "48_roles_are_draft_contracts_not_independent_llm_workers":
            ('_DEPARTMENTS=' in org and
             '"upload_video"' in org and
             'STAGING ONLY' in org and
             'No network, LLM billing' in org),
        "three_tomorrow_slots_are_unverified_research_leads":
            ('PUBLISH_SLOTS = (' in planner and
             'UNVERIFIED_SCOUT_STATUS' in planner and
             'NO LLM calls' in planner),
        "daily_cloud_automated_job_does_not_publish":
            ('PUBLISH_ENABLED: "false"' in daily and
             'FLOWMINUTE_ENABLE_PUBLISH: "0"' in daily and
             'contents: read' in daily and
             'actions: read' in daily),
        "full_original_17_scene_media_render_is_real":
            ('Generate all 17 original narrated rehearsal scenes' in daily and
             '_encode_full(ffmpeg' in media and
             '_inspect_full(ffmpeg,movie' in media and
             '"actual_full_ffmpeg_decode_passed":True' in media),
        "owner_review_artifact_requires_main_manual_opt_in":
            ("github.event_name == 'workflow_dispatch' && inputs.retain_rehearsal_review_artifact == true && github.ref == 'refs/heads/main'"
              in daily and 'retention-days: 1' in daily and
              '"HUMAN_REVIEW_WORKSHEET_UNFILLED.json"' in daily),
        "native_subtitles_original_17_scene_clock_and_audio_layer":
            ('compose_rehearsal_native_ass(cues' in media and
             'scene_durations=durations' in media and
             'mix_original_sound_design(' in media),
        "post_encode_true_peak_and_cross_video_gate_source":
            ('AUDIO_MASTERING_FILTER' in media and
             'verify_exact_encoded_master(' in media and
             'verify_three_matching_masters(actual)' in media and
             'MEASUREMENT_FILTER' in mastering and
             'parse_encoded_loudnorm(process.stderr)' in mastering and
             'measured_encoded_integrated_lufs' in loudness),
        "offline_owner_player_cannot_mark_human_approval_automatically":
            ('data.youtube_publish_authorized=false' in portal and
             'player.pause();player.focus();' in portal and
             'fetch(' not in portal),
        "manual_publisher_protected_and_disabled_by_default":
            ("environment: youtube-production" in publisher and
             "github.ref == 'refs/heads/main'" in publisher and
             "vars.PUBLISH_ENABLED == 'true'" in publisher and
             'PUBLISH_ENABLED") != "true"' in approval),
        "manual_upload_requires_real_external_owner_signature":
            ('verify_owner_release_signature' in approval and
             'def verify_owner_release_signature(' in owner_signed and
             'FLOWMINUTE_OWNER_RELEASE_ED25519_PUBLIC_HEX' in approval and
             'FLOWMINUTE_OWNER_RELEASE_ED25519_PUBLIC_HEX' in publisher),
        "live_channel_readonly_checks_cannot_change_youtube":
            ('workflow_dispatch:' in owner_readonly and
             'environment: youtube-production' in owner_readonly and
             'youtube_video_insert_update_delete_requests' not in owner_readonly),
        "branch1_historical_receipts_are_not_live_youtube_proof":
            ('HISTORICAL' in inventory.upper() and
             'historical_confirmation_not_live_readback' in inventory and
             'No uploads, replacement' in inventory),
    }
    return {
        "status":"SOURCE_CONTRACT_AUDIT_ONLY_NOT_DEPLOYMENT_PROOF",
        "checks":gates,
        "checks_passed":sum(gates.values()),
        "checks_total":len(gates),
        "all_source_acceptance_gates_present":all(gates.values()),
        "main_branch_latest_real_three_video_run_status":NO_EXTERNAL_EVIDENCE,
        "current_owner_youtube_oauth_status":NO_EXTERNAL_EVIDENCE,
        "current_branch1_schedule_state":NO_EXTERNAL_EVIDENCE,
        "actual_human_reviews_verified":NO_EXTERNAL_EVIDENCE,
        "actual_unattended_real_youtube_publications":NO_EXTERNAL_EVIDENCE,
    }


def rubric_snapshot() -> dict:
    _need(sum(weight for _,weight,_ in RUBRIC)==100 and
          sum(earned for _,weight,earned in RUBRIC
              if 0<=earned<=weight)==44,
          "Published production-readiness score arithmetic changed")
    return {
        "status":"QUALITATIVE_EVIDENCE_WEIGHTED_ESTIMATE_NOT_UPLOAD_PERCENT",
        "categories":[
            {"phase":phase,"weight":weight,"earned":earned,
             "remaining":weight-earned}
            for phase,weight,earned in RUBRIC],
        "overall_production_readiness_estimate_percent":44,
        "overall_remaining_estimate_percent":56,
        "engineering_progress_not_the_same_metric":True,
        "real_seven_day_unattended_release_target":21,
        "real_seven_day_unattended_releases_independently_verified":0,
        "seven_day_verified_release_proportion_percent":0,
        "score_valid_only_for_dated_2026_11_07_evidence":True,
    }


def main() -> None:
    p=argparse.ArgumentParser(description="FlowMinute source-only phase audit")
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--strict",action="store_true",
                   help="Exit nonzero if a source safety/trust boundary changes")
    args=p.parse_args()
    audit=inspect_source_acceptance(args.root)
    result={"source_acceptance":audit,"rubric":rubric_snapshot()}
    print(json.dumps(result,indent=2,sort_keys=True))
    if args.strict:
        _need(audit["all_source_acceptance_gates_present"],
              "One or more fail-closed repo source gates disappeared")


if __name__=="__main__":
    main()
