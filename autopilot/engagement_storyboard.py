"""Non-predictive editorial engagement checks for FlowMinute 3D storyboards.

This validates a *creative brief*, not audience behavior. No algorithmic claim,
YouTube upload, video generation or network calls are performed.
"""
from __future__ import annotations

import re
from typing import Any

class EngagementBriefError(ValueError):
    pass

BAD_CTA = re.compile(
    r"(subscribe\s+to\s+win|like\s+to\s+unlock|guaranteed\s+views|"
    r"पैसे\s+जीतो|लाइक\s+करो\s+वरना|subscribe\s+or\s+else)",
    flags=re.IGNORECASE,
)
CORE_METRICS = {
    "short": {"engaged_views", "stayed_to_watch", "average_view_duration", "likes", "comments", "subscribers_gained"},
    "long": {"impressions", "click_through_rate", "watch_time", "average_view_duration", "audience_retention", "subscribers_gained"},
}

def require(test: bool, problem: str) -> None:
    if not test:
        raise EngagementBriefError(problem)

def description(value: Any, lo=14, hi=280) -> bool:
    return isinstance(value, str) and lo <= len(value.strip()) <= hi

def validate_engagement_brief(brief: dict, scene_plan: dict) -> dict:
    """Fail on missing *proposed* teaching elements; never green-light release."""
    require(isinstance(brief, dict) and brief.get("schema_version") == 1,
            "Unknown engagement brief version")
    require(isinstance(scene_plan, dict)
            and brief.get("episode_id") == scene_plan.get("episode_id"),
            "Episode/storyboard mismatch")
    kind = scene_plan.get("format")
    require(kind in CORE_METRICS and brief.get("format") == kind,
            "Video format mismatch")
    require(brief.get("language") == scene_plan.get("language"),
            "Locale mismatch")
    hook = brief.get("first_seconds")
    require(isinstance(hook, dict)
            and isinstance(hook.get("start_second"), (float, int))
            and not isinstance(hook["start_second"], bool)
            and 0 <= hook["start_second"] <= 1.5,
            "A visible opening should begin immediately")
    for field in ("physical_action", "viewer_question", "payoff_promise"):
        require(description(hook.get(field)), "Missing meaningful opening: " + field)
    require(not hook["physical_action"].lower().startswith("logo"),
            "Do not lead with a logo animation")
    require(hook.get("character_id") in {x["id"] for x in scene_plan["characters"]},
            "Opening character must exist in story")
    require(not BAD_CTA.search(" ".join(str(x) for x in hook.values())),
            "Do not manipulate viewers")

    segments = brief.get("instructional_moments")
    require(isinstance(segments, list) and len(segments) >= 3,
            "Show concrete teaching moments")
    numbered = {shot["number"]: shot for shot in scene_plan["shots"]}
    seen = set()
    for moment in segments:
        require(isinstance(moment, dict), "Malformed teaching moment")
        number = moment.get("scene_number")
        require(type(number) is int and number in numbered and number not in seen,
                "Teaching moment must identify a unique storyboard scene")
        seen.add(number)
        require(numbered[number]["mode"] in ("true_3d","real_screen_capture","illustrative_ui"),
                "Teaching moment cannot be decorative cards alone")
        for key in ("visual_cause_effect", "takeaway", "focal_object"):
            require(description(moment.get(key), 7, 320), "Missing causal teaching visual: " + key)
        require(1 <= moment.get("highlight_count", 0) <= 2
                and type(moment.get("highlight_count")) is int,
                "Use one or two visual attention cues; not a noisy HUD")
    require(any(x["scene_number"] >= len(scene_plan["shots"]) - 1 for x in segments),
            "Show a late takeaway rather than disappearing after the demonstration")

    voice = brief.get("dialogue_design")
    require(isinstance(voice, dict)
            and description(voice.get("learner_question"))
            and description(voice.get("presenter_response"))
            and description(voice.get("vocal_delivery"))
            and voice.get("independent_pronunciation_review") is False,
            "Voice casting is planned but independent audio review remains pending")
    require(description(brief.get("originality_angle"), 20, 450),
            "Original educational distinction required")
    question = brief.get("audience_question")
    require(description(question, 12, 230) and not BAD_CTA.search(question),
            "Question must invite a genuine topic discussion")

    packaging = brief.get("packaging")
    require(isinstance(packaging, dict), "Missing truthful title/thumbnail direction")
    titles = packaging.get("title_candidates")
    require(isinstance(titles, list) and len(titles) in (2, 3)
            and len({x.casefold().strip() for x in titles if isinstance(x, str)}) == len(titles)
            and all(description(x, 12, 100) for x in titles),
            "Use 2–3 distinct, relevant title options")
    require(description(packaging.get("thumbnail_visual"), 20, 340),
            "Give a mobile-readable, honest thumbnail concept")
    require(packaging.get("claims_checked_for_clickbait") is False,
            "Creative plans cannot self-attest fact checking")
    require(packaging.get("youtube_native_ab_test") == ("candidate_when_eligible" if kind=="long" else "not_available_for_shorts"),
            "YouTube Studio long-only A/B eligibility must be respected")

    links = brief.get("cross_video_plan")
    require(isinstance(links, dict), "Related-video strategy missing")
    if kind == "short":
        require(links.get("related_video") == "conditional_after_release"
                and links.get("end_screen") == "not_supported_for_shorts",
                "Shorts use the related-video feature, not long-form end screens")
    else:
        require(links.get("related_video") == "not_short"
                and links.get("end_screen") == "candidate_last_5_to_20_seconds",
                "Long videos can reserve a standard end screen if eligible")
    require(links.get("verified_destination_video_id") is None,
            "Never invent a destination video ID")

    measurements = brief.get("measurements")
    require(isinstance(measurements, dict), "Missing measurable experiment plan")
    require(set(measurements.get("evaluate_metrics", [])) == CORE_METRICS[kind],
            "Use mode-specific measures, not views alone")
    require(measurements.get("observed_values") is None,
            "Do not fabricate analytics")
    require(measurements.get("claim_of_lift") is None,
            "No uplift claims without controlled comparison")
    require(measurements.get("compare_similar_age_and_format") is True,
            "Only compare age- and format-matched performance")
    require(measurements.get("test_one_primary_variable") is True,
            "Restrict experiments to interpretable creative changes")
    require(brief.get("production_state") == "CREATIVE_BRIEF_ONLY",
            "A creative brief is not publication permission")

    return {
        "episode_id": scene_plan["episode_id"],
        "creative_coverage_passed": True,
        "unique_causal_teaching_moments": len(segments),
        "audit_type": "STRUCTURAL_EDITORIAL_NOT_PREDICTIVE",
        "observed_audience_improvement": None,
        "publishing_authorized": False,
        "ready_for_final_quality_review": False,
    }
