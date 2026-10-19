"""FlowMinute four-prompt bundle -> one EXISTING guarded production staging cycle.

Integrates, does NOT replace:
  PublishingCalendar (Asia/Kolkata, overrides, pauses, reserved slots),
  MasterOrchestrator / 8 departments / 48 restricted specialist roles,
  October-20 independently original 3-program source packet,
  genuine 3D + digital-illustration shot plan,
  independently reviewed growth and release prerequisites.

The bridge hands out real typed draft assignments but intentionally HAS NO
publishing API, account connection, cloud resource or human-rights bypass.
NO autonomous production or authoritatively verified upload is implied.
"""
from __future__ import annotations

from datetime import date
from hashlib import sha256
import json

from .agent_org import (
    CHANNEL_ID,EpisodeSpec,MasterOrchestrator,WorkflowError,
)
from .calendar import PublishingCalendar,CalendarError
from .hybrid_scene_director import scene_recipe_plan
from .oct20_silent_concept_preview import load_preview_plan,preview_spec

PACK_DAY=date(2026,10,20)
EXPECTED_EPISODES={
    ("short",1):("fm_20261020_short_en","en",42),
    ("short",2):("fm_20261020_short_hi","hi",44),
    ("long",1):("fm_20261020_long_hi","hi",480),
}
HARD_PRODUCTION_BLOCKERS=(
    "NO_RIGHTS_CLEARED_NATURAL_ENGLISH_HINDI_NARRATION",
    "NO_REAL_AUDIO_WORD_ALIGNED_SUBTITLES",
    "NO_COMPLETE_FINAL_HD_ORIGINAL_AUDIOVISUAL_MEDIA",
    "NO_INDEPENDENT_MEDIA_AND_COMMERCIAL_RIGHTS_APPROVAL",
    "NO_VERIFIED_LAPTOP_INDEPENDENT_ZERO_COST_RENDER_CAPACITY",
    "NO_AUTHORIZED_YOUTUBE_UPLOAD_READBACK_OR_PUBLIC_RELEASE",
)


def staging_cycle_for_day(
    day:date,
    *,
    calendar:PublishingCalendar|None=None,
    existing_reserved_utc:tuple[str,...]=(),
)->dict:
    """Make a real calendar plan, source-match exact programs, queue subagents.

    If schedule count exceeds authored, approved source inventory, signal
    the shortage instead of inventing AI content, videos, voices, channels,
    upload status, analytics or extra release permissions.
    """
    if (type(day) is not date
            or calendar is not None
            and type(calendar) is not PublishingCalendar
            or type(existing_reserved_utc) is not tuple):
        raise WorkflowError("Staging requires exact date and trusted calendar inputs")
    cal=calendar if calendar is not None else PublishingCalendar()
    slots=cal.plan(day,reserved_utc=existing_reserved_utc)
    if len(slots)>18 or any(s.status!="DRAFT_ONLY_NO_PUBLISH_PERMISSION"
                             for s in slots):
        raise WorkflowError("Unsafe release plan received")

    # Only the 20-Oct pack has independently checked source scripts here.
    # On other dates keep research jobs pending instead of reusing old videos.
    source=load_preview_plan() if day==PACK_DAY and slots else None
    accepted=[]
    needs_content=[]
    seen=set()
    for slot in slots:
        key=(slot.kind,slot.ordinal)
        match=EXPECTED_EPISODES.get(key) if source is not None else None
        if match is None:
            needs_content.append({
                "slot_utc":slot.planned_utc,"kind":slot.kind,
                "ordinal":slot.ordinal,
                "status":"NO_ORIGINAL_SOURCE_EPISODE_HOLD",
            })
            continue
        episode_id,language,seconds=match
        spec=preview_spec(source,episode_id)
        if (spec.kind!=slot.kind or spec.language!=language
                or spec.duration_seconds!=seconds
                or episode_id in seen):
            raise WorkflowError("Script/slot mismatch, cannot reuse a video")
        seen.add(episode_id)
        visuals=(scene_recipe_plan(episode_id,7)
                 if spec.kind=="short" else None)
        accepted.append({
            "episode_id":episode_id,
            "kind":slot.kind,
            "language":language,
            "duration_seconds":seconds,
            "calendar_utc":slot.planned_utc,
            "calendar_status":slot.status,
            "source_state":"ORIGINAL_SCRIPT_ONLY",
            "visual_style_plan":visuals,
            "long_full_hybrid_visuals_rendered":False,
            "full_hd_media_verified":False,
            "authentic_human_narration_verified":False,
            "rights_and_facts_independently_verified":False,
            "real_youtube_schedule_created":False,
        })

    # Reuse the actual 18-task-per-video DAG, not decorative list-of-agents.
    queue=tuple(EpisodeSpec(
        episode_id=x["episode_id"],
        kind=x["kind"],language=x["language"],
        priority=(85 if x["kind"]=="short" else 70),
    ) for x in accepted)
    master=MasterOrchestrator(queue) if queue else None
    report=master.summary() if master else {
        "master":"FlowMinute Master Growth Orchestrator",
        "departments":8,"specialists":48,
        "episodes_queued":0,"episodes_active":0,
        "ready_tasks":0,"cloud_deployed":False,
        "uploads_enabled":False,"scheduling_enabled":False,
        "max_monthly_spend_inr":0,
        "status":"NO_AUTHORED_EPISODES_READY_FOR_ASSIGNMENT",
    }
    assignments=master.ready_assignments() if master else ()
    # A verified source script is not automatically a completed research,
    # independently reviewed facts, completed media, or rights clearance.
    return {
        "status":"BUNDLE_FOUR_PROMPTS_INTEGRATED_STAGING_NOT_LIVE_AUTOPILOT",
        "day_local":day.isoformat(),
        "timezone":"Asia/Kolkata",
        "channel_id":CHANNEL_ID,
        "bundles_applied":(
            "MASTER_CONTENT_GROWTH_AND_SAFETY",
            "NESTED_EIGHT_DEPARTMENT_48_SPECIALIST_ORGANIZATION",
            "PRACTICAL_ORIGINAL_3D_AND_DIGITAL_TUTORIAL_VISUALS",
            "ADAPTIVE_CALENDAR_NEWS_AND_OBSERVATIONAL_ANALYTICS",
        ),
        "calendar_draft_slots":len(slots),
        "source_matched_original_episodes":accepted,
        "source_missing_slots":needs_content,
        "master_agent":report,
        "initial_ready_assignments":[
            {"episode_id":episode,"task_id":task,"owner":owner}
            for episode,task,owner in assignments
        ],
        "specialist_task_contracts":(
            sum(len(wf.contracts) for wf in master.workflows.values())
            if master else 0
        ),
        "supported_media_mode":"ORIGINAL_SCRIPT_STORYBOARD_DRAFT_ONLY",
        "verified_engagement_analytics_loaded":False,
        "audience_data_fabricated":False,
        "estimated_srt_promoted_to_real_asr":False,
        "visual_3d_preview_is_final_movie":False,
        "real_human_or_model_voice_accepted":False,
        "pending_production_gates":HARD_PRODUCTION_BLOCKERS,
        "authenticated_youtube_receipts_used":False,
        "real_upload_scheduling_or_publication_performed":False,
        "cloud_deployment_performed":False,
        "new_external_service_connected":False,
        "accessed_nirala":False,
        "paid_resources_used":False,
        "monthly_recurring_budget_inr":0,
    }


def staging_cycle_json(
    day:date,
    *,
    calendar:PublishingCalendar|None=None,
    existing_reserved_utc:tuple[str,...]=(),
)->str:
    """Deterministic preview manifest printable by existing public CI."""
    return json.dumps(
        staging_cycle_for_day(day,calendar=calendar,
                              existing_reserved_utc=existing_reserved_utc),
        ensure_ascii=False,sort_keys=True,indent=2,
    )+"\n"
