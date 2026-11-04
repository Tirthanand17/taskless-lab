"""Branch 2 B3c: source-linked editorial review dossier, NEVER publication approval.

A model's proposed citation is NOT corroboration. The only inputs accepted here
are the structurally checked proposal and revalidated public-source metadata.
No network, secrets, model calls, media, OAuth, or YouTube writes.
"""
from __future__ import annotations

from difflib import SequenceMatcher
import hashlib
import json
import re
from typing import Sequence

from autopilot.script_draft_agent import (
    DRAFT_STATUS, SCRIPT_SCHEMA, ScriptDraftError,
    build_draft_input, validate_proposal,
)

DOSSIER_STATUS = "CLAIM_EVIDENCE_AND_ORIGINALITY_REVIEW_PENDING_NO_PUBLISH"


class EditorialGateError(ValueError):
    """A corrupted or misleading dossier must be blocked."""


def _fingerprint(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def build_review_dossier(proposal: object, slot: object, observations: object) -> dict:
    """Recompute a proposed draft from provenance; never trust preapproved flags."""
    if not isinstance(proposal, dict) or not isinstance(slot, dict) or not isinstance(observations, dict):
        raise EditorialGateError("Inputs must be validated objects")
    try:
        draft_input = build_draft_input(slot, observations)
        required = SCRIPT_SCHEMA["required"]
        if not all(key in proposal for key in required):
            raise EditorialGateError("Missing draft content")
        expected = validate_proposal({key: proposal[key] for key in required}, draft_input)
    except (ScriptDraftError, KeyError, TypeError, ValueError) as exc:
        raise EditorialGateError("Invalid upstream draft/source contract") from exc
    # Reject any additional unvalidated field or a tampered review flag.
    if proposal != expected or proposal.get("status") != DRAFT_STATUS:
        raise EditorialGateError("Draft was altered or falsely approved")
    if proposal["episode_id"] != slot["episode_id"] or proposal["format"] != slot["format"]:
        raise EditorialGateError("Slot and candidate script mismatch")
    source_lookup = {s["source_id"]: s for s in observations["sources"]}
    if len(source_lookup) != len(observations["sources"]):
        raise EditorialGateError("Duplicate source identifiers")
    claims = []
    seen_claims = set()
    for index, item in enumerate(proposal["claim_candidates"], start=1):
        normalized = " ".join(item["claim"].split()).casefold()
        if normalized in seen_claims:
            raise EditorialGateError("Repeated candidate claim requires consolidation")
        seen_claims.add(normalized)
        if len(item["source_ids"]) != len(set(item["source_ids"])):
            raise EditorialGateError("Repeated source ID falsely inflates support")
        links = []
        for source_id in item["source_ids"]:
            source = source_lookup.get(source_id)
            if source is None:
                raise EditorialGateError("Claim references a missing observed source")
            links.append({
                "source_id": source_id,
                "publisher": source["publisher"],
                "source_url": source["source_url"],
                "observation_status": source["status"],
                "observed_sha256": source["response_sha256"],
                "article_fetched": source["status"] == "SOURCE_FETCHED_NOT_FACT_CHECKED",
                "supports_exact_claim_verified": False,
                "independent_source_authorship_verified": False,
            })
        distinct_publishers = len({x["publisher"].casefold() for x in links})
        claims.append({
            "claim_id": hashlib.sha256(
                (proposal["episode_id"] + "\n" + normalized).encode("utf-8")
            ).hexdigest()[:20],
            "candidate_number": index,
            "candidate_claim_untrusted": item["claim"],
            "cited_observation_count": len(links),
            "distinct_publisher_labels_not_independent_attestations": distinct_publishers,
            "linked_source_observations": links,
            "needs_claim_level_source_read": True,
            "needs_independent_corrob_and_context": True,
            "factually_verified": False,
            "reviewer_decision": "PENDING",
        })
    return {
        "schema_version": 1,
        "status": DOSSIER_STATUS,
        "episode_id": proposal["episode_id"],
        "format": proposal["format"],
        "proposed_title_unreviewed": proposal["title"],
        "draft_sha256": _fingerprint(proposal),
        "source_input_sha256": proposal["research_input_sha256"],
        "proposed_claim_count": len(claims),
        "claim_candidates_not_exhaustive": True,
        "claim_inventory_human_checked": False,
        "claim_dossiers": claims,
        "unverified_source_count": len(source_lookup),
        "article_observation_is_not_factual_attestation": True,
        "duplicate_publisher_labels_do_not_count_as_independent_sources": True,
        "syndication_or_shared_reporting_not_excluded": True,
        "rights_and_originality_review_complete": False,
        "original_demo_editorial_review_complete": False,
        "ai_realism_and_synthetic_disclosure_decision": "PENDING_EDITORIAL_ASSESSMENT",
        "human_full_playback_review_complete": False,
        "all_claims_verified": False,
        "real_media_from_this_draft_exists": False,
        "youtube_upload_enabled": False,
        "youtube_schedule_enabled": False,
        "release_authorized": False,
        "next_gate": "Independent source-to-claim, original demonstration, rights, AI disclosure and complete playback review",
    }


def review_three_episode_candidates(items: Sequence[tuple[dict, dict, dict]]) -> dict:
    """Cross-episode similarity screen, not a guarantee of novelty."""
    if not isinstance(items, (list, tuple)) or len(items) != 3:
        raise EditorialGateError("Exactly 2 Shorts and 1 long are required")
    dossiers = []
    slots = []
    proposals = []
    for candidate in items:
        if not isinstance(candidate, (tuple, list)) or len(candidate) != 3:
            raise EditorialGateError("Expected proposal, slot and observations")
        proposal, slot, observations = candidate
        dossiers.append(build_review_dossier(proposal, slot, observations))
        slots.append(slot)
        proposals.append(proposal)
    if [x.get("release_slot") for x in slots] != ["short_am", "long", "short_pm"]:
        raise EditorialGateError("Wrong daily release slot order")
    if [x["format"] for x in dossiers] != ["short", "long", "short"]:
        raise EditorialGateError("Wrong daily video formats")
    dates = {s["episode_id"].split("_")[1] for s in slots}
    if len(dates) != 1 or len({d["episode_id"] for d in dossiers}) != 3:
        raise EditorialGateError("Multiple days or repeated episode IDs")
    normalized_titles = [" ".join(p["title"].casefold().split()) for p in proposals]
    normalized_hooks = [" ".join(p["hook"].casefold().split()) for p in proposals]
    if len(set(normalized_titles)) != 3 or len(set(normalized_hooks)) != 3:
        raise EditorialGateError("Repeated daily topic or opening hook")
    for i in range(3):
        for j in range(i + 1, 3):
            a, b = proposals[i], proposals[j]
            if SequenceMatcher(None, normalized_titles[i], normalized_titles[j]).ratio() >= .87:
                raise EditorialGateError("Daily titles are near-duplicates")
            if SequenceMatcher(None, a["example_walkthrough"].casefold(),
                               b["example_walkthrough"].casefold()).ratio() >= .82:
                raise EditorialGateError("Daily demonstrations are near-duplicates")
            if SequenceMatcher(None, a["narration"].casefold(),
                               b["narration"].casefold()).ratio() >= .82:
                raise EditorialGateError("Daily narrations are near-duplicates")
    return {
        "status": DOSSIER_STATUS,
        "release_day_ist": next(iter(dates)),
        "episode_count": 3,
        "formats": ["short", "long", "short"],
        "dossiers": dossiers,
        "syntactic_cross_episode_duplicate_screen_passed": True,
        "semantic_novelty_or_youtube_policy_compliance_proven": False,
        "every_fact_and_right_verified": False,
        "youtube_upload_enabled": False,
        "youtube_schedule_enabled": False,
        "release_authorized": False,
    }
