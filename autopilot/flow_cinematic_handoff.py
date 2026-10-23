"""Offline credit-safe handoff for Google Flow cinematic anchor clips.

This module is a plan validator, NOT a Google Flow API client or uploader.
It cannot certify subscription, available credits, rights, quality or release.
"""
from __future__ import annotations

from copy import deepcopy

PRICE_CREDITS_720P_10S = 15  # Research assumption; recheck in actual Flow UI.
CLIP_SECONDS = 10
LEAN_SELECTION = {
    "fm_20261024_short_en": ("01",),
    "fm_20261024_short_hi": ("01",),
    "fm_20261024_long_hi": ("01", "03", "05"),
}
EXPECTED_DURATIONS = {
    "fm_20261024_short_en": 48,
    "fm_20261024_short_hi": 48,
    "fm_20261024_long_hi": 300,
}
EXPECTED_ORIENTATION = {
    "fm_20261024_short_en": "9:16",
    "fm_20261024_short_hi": "9:16",
    "fm_20261024_long_hi": "16:9",
}


class FlowHandoffError(ValueError):
    pass


def demand(condition: bool, reason: str):
    if not condition:
        raise FlowHandoffError(reason)


def validate_source_package(package: dict) -> None:
    demand(isinstance(package, dict) and package.get("version") == 1,
           "Unknown Flow package")
    demand(package.get("credit_calculation", {}).get("credits_spent") == 0,
           "Draft package must not claim actual paid/credit-generating work")
    demand(package["credit_calculation"].get("actual_available_credits") == "UNVERIFIED",
           "Draft package must not self-attest account credits")
    episodes = package.get("episodes")
    demand(isinstance(episodes, list) and len(episodes) == 3,
           "Exactly three October 24 videos expected")
    demand({e.get("episode_id") for e in episodes if isinstance(e, dict)}
           == set(EXPECTED_DURATIONS), "Wrong or duplicated episodes")
    all_keys = set()
    for ep in episodes:
        episode_id = ep["episode_id"]
        demand(ep.get("orientation") == EXPECTED_ORIENTATION[episode_id],
               "Wrong episode orientation")
        demand(ep.get("existing_storyboard_target_seconds") == EXPECTED_DURATIONS[episode_id],
               "Duration does not match educational storyboard")
        demand(isinstance(ep.get("clips"), list) and ep["clips"], "Missing Flow shots")
        for clip in ep["clips"]:
            demand(isinstance(clip, dict) and isinstance(clip.get("clip_id"), str),
                   "Bad clip ID")
            key = (episode_id, clip["clip_id"])
            demand(key not in all_keys, "Duplicate clip would double-charge credits")
            all_keys.add(key)
            demand(clip.get("clip_status") == "NOT_GENERATED"
                   and clip.get("clip_qa") == "NOT_REVIEWED"
                   and clip.get("flow_asset_id") is None,
                   "Draft cannot self-attest generated or approved media")
            demand(len(clip.get("character_refs", [])) >= 2
                   and len(set(clip["character_refs"])) == len(clip["character_refs"]),
                   "Two distinct story characters required")
            demand(isinstance(clip.get("flow_prompt"), str)
                   and 160 <= len(clip["flow_prompt"]) <= 6000,
                   "Missing bounded generation instructions")
            demand(isinstance(clip.get("audio_dialogue_draft"), str)
                   and len(clip["audio_dialogue_draft"]) >= 12,
                   "Natural dialogue direction missing")
    demand(all((eid, cid) in all_keys
               for eid, ids in LEAN_SELECTION.items() for cid in ids),
           "One or more lean selection clip IDs do not exist")


def _selections(package: dict, mode: str):
    if mode == "pilot":
        return {"fm_20261024_short_en": ("01",)}
    if mode == "lean_day":
        return LEAN_SELECTION
    if mode == "full_keyshots":
        return {
            episode["episode_id"]: tuple(clip["clip_id"] for clip in episode["clips"])
            for episode in package["episodes"]
        }
    raise FlowHandoffError("Unknown production selection")


def build_plan(package: dict, *, mode: str = "pilot", price: int = PRICE_CREDITS_720P_10S):
    validate_source_package(package)
    demand(type(price) is int and 1 <= price <= 1000,
           "Price must be a positive explicitly checked estimate")
    selections = _selections(package, mode)
    lookup = {e["episode_id"]:e for e in package["episodes"]}
    selected = []
    for ep_id, clip_ids in selections.items():
        ep = lookup[ep_id]
        by_id = {clip["clip_id"]:clip for clip in ep["clips"]}
        for clip_id in clip_ids:
            clip = by_id[clip_id]
            selected.append({
                "episode_id":ep_id,
                "clip_id":clip_id,
                "target_orientation":ep["orientation"],
                "expected_seconds":CLIP_SECONDS,
                "character_refs":deepcopy(clip["character_refs"]),
                "prompt":clip["flow_prompt"],
                "planned_audio_direction":clip["audio_dialogue_draft"],
                "provider_asset_id":None,
                "qa_passed":False,
                "status":"NOT_GENERATED",
            })
    demand(len(selected) == len(set((c["episode_id"],c["clip_id"]) for c in selected)),
           "Duplicate selected clip")
    seconds = len(selected)*CLIP_SECONDS
    remaining = {
        ep_id: EXPECTED_DURATIONS[ep_id] - sum(CLIP_SECONDS for c in selected
                                                if c["episode_id"]==ep_id)
        for ep_id in EXPECTED_DURATIONS
    }
    demand(all(n >= 0 for n in remaining.values()), "Cinematic clips exceed episode length")
    return {
        "status":"STAGED_NO_PROVIDER_CONNECTION",
        "selection_mode":mode,
        "clip_count":len(selected),
        "estimated_flow_credits":len(selected)*price,
        "price_basis":"UI_RATE_ESTIMATE_NOT_LIVE_CHECK",
        "actual_available_credits":None,
        "real_credits_spent":0,
        "new_money_spent_inr":0,
        "cinematic_seconds_planned":seconds,
        "non_cinematic_seconds_still_to_produce":remaining,
        "clips":selected,
        "actual_render_count":0,
        "google_flow_assets_verified":False,
        "natural_voice_reviewed":False,
        "fact_check_reviewed":False,
        "video_composition_completed":False,
        "youtube_schedule_verified":False,
        "generation_authorized_by_this_plan":False,
        "publishing_authorized_by_this_plan":False,
    }


def validate_import_receipt(receipt: dict, *, selection: dict) -> dict:
    """Review candidate external receipt structure; does not verify actual bytes/rights.

    Accepted status remains INTAKE_PENDING_INDEPENDENT_MEDIA_QA, never RELEASED.
    """
    demand(isinstance(receipt, dict), "Missing external asset receipt")
    demand(receipt.get("episode_id")==selection["episode_id"]
           and receipt.get("clip_id")==selection["clip_id"], "Wrong clip/episode mapping")
    digest=receipt.get("sha256")
    import re
    demand(isinstance(digest,str) and re.fullmatch("[0-9a-f]{64}",digest) is not None,
           "Real media bytes and SHA256 must be recorded by an independent intake")
    demand(receipt.get("duration_seconds") is not None
           and type(receipt["duration_seconds"]) in (int,float)
           and 8 <= receipt["duration_seconds"] <= 10.5,
           "Unexpected clip duration")
    demand(receipt.get("orientation") == selection["target_orientation"],
           "Imported clip aspect ratio mismatch")
    demand(isinstance(receipt.get("source"),str)
           and receipt["source"] in ("google_flow_download", "user_supplied_file"),
           "Source provenance missing")
    demand(isinstance(receipt.get("file_name"),str)
           and re.fullmatch("[a-zA-Z0-9][a-zA-Z0-9_.-]{2,120}\.mp4",
                            receipt["file_name"]) is not None
           and ".." not in receipt["file_name"],"Unsafe media filename")
    return {"status":"INTAKE_PENDING_INDEPENDENT_MEDIA_QA",
            "candidate_episode":selection["episode_id"],
            "candidate_clip":selection["clip_id"],
            "sha256":digest,
            "media_file_decoded":False,
            "rights_reviewed":False,
            "fact_reviewed":False,
            "voice_reviewed":False,
            "ready_for_youtube":False}
