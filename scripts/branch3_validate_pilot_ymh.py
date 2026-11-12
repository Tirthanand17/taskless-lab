"""Prelaunch safety gates for source-free YMH Ep. 347 pilot.

Never downloads third-party media, never joins a campaign and never publishes.
The permission flags are statements from documents, not a source of authority.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PILOT=ROOT/"branch3/pilot_ymh_ep347.json"
STATE=ROOT/"branch3/channel_state.json"
PERMISSIONS=ROOT/"branch3/creator_permissions.json"

class PilotNotReady(ValueError):
    pass

def require(value: bool, message: str) -> None:
    if not value:
        raise PilotNotReady(message)

def verify_source_free_pilot(p: object, state: object, permissions: object) -> None:
    require(type(p) is dict and type(state) is dict and type(permissions) is dict,"invalid payload")
    require(p.get("schema_version")==1 and p.get("pilot_id")=="clivox_ymh_ep347_eighties_restaurant","unknown pilot")
    require(p.get("channel_id")=="UCfPEvy0SefE_5nNlYlY_CyQ"==state.get("channel_id"),"wrong channel")
    require(state.get("channel_settings",{}).get("intermediate_features")=="enabled","intermediate features not verified")
    require(state.get("channel_settings",{}).get("upload_default_visibility")=="private","unsafe default visibility")
    require(state.get("release_gates",{}).get("videos_uploaded_by_this_setup")==0,"channel release history changed")
    require(state.get("release_gates",{}).get("github_release_automation_enabled") is False,"publishing enabled")
    require(permissions.get("policy")=="EXPLICIT_CREATOR_GRANT_ONLY" and permissions.get("creators")==[],"permission not yet reviewed")
    require(p.get("workflow_status")=="SOURCE_RESEARCH_ONLY_REQUIRES_CREATOR_PERMISSION_AND_OWNER_CONTRACT_REVIEW","false rights claim")
    source=p.get("candidate_source",{})
    require(source.get("original_video_id")=="i6pmnpaOaZQ" and source.get("episode_number")==347,"wrong episode")
    require(source.get("original_video_url")=="https://www.youtube.com/watch?v=i6pmnpaOaZQ","wrong source")
    require(source.get("creator_public_clipping_invitation_page")=="https://whop.com/ymhclipping/","wrong invitation")
    require(source.get("campaign_membership_confirmed") is False and source.get("creator_grant_for_clivox_confirmed") is False,"unverified membership or grant")
    require(source.get("rights_holder_verified_for_this_exact_edit") is False,"rights were improperly asserted")
    window=p.get("research_window",{})
    require(window.get("start")=="01:04:52" and window.get("end")=="01:09:36","unverified research chapter")
    for x in ("exact_clip_in","exact_clip_out"):
        require(window.get(x) is None,"unapproved timestamps")
    for x in ("transcript_verified","spoken_words_quoted","third_party_footage_cleared"):
        require(window.get(x) is False,f"rights/editorial review not completed: {x}")
    req=p.get("required_gates",{})
    required=("full_ymh_campaign_rules_reviewed","participant_eligibility_verified",
              "content_rewards_17_6_assignment_acknowledged","commercial_scope_verified",
              "brand_or_creator_rights_holder_authority_verified",
              "creator_permission_allowlist_added","third_party_music_and_visual_rights_cleared",
              "source_episode_watched_in_context","final_segment_timestamps_verified",
              "clip_originality_reviewed","final_render_approved",
              "new_clivox_channel_oauth_verified")
    require(set(req)==set(required) and all(req[k] is False for k in required),"unauthorized pilot gate claimed")
    require(p.get("file_generation_allowed") is False
            and p.get("third_party_media_download_allowed") is False
            and p.get("ready_to_upload") is False
            and p.get("ready_to_publish") is False,"media was authorized without verified rights")
    flow=p.get("concept",{}).get("scene_flow",[])
    require(type(flow) is list and len(flow)>=4 and any(s.get("phase")=="permitted_excerpt" for s in flow),
            "incomplete editorial treatment")

def main()->None:
    p=json.loads(PILOT.read_text("utf8"))
    s=json.loads(STATE.read_text("utf8"))
    perms=json.loads(PERMISSIONS.read_text("utf8"))
    verify_source_free_pilot(p,s,perms)
    print("CLIVOX_YMH_EP347_SOURCE_FREE_PILOT_VALIDATED_ZERO_MEDIA_ZERO_PUBLICATION")

if __name__=="__main__":
    main()
