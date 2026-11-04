"""Offline GitHub-hosted Branch 2 B3c negative safety tests.

These invented sources and scripts are TEST FIXTURES, not factual approval.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import unittest

from autopilot.daily_cloud_plan import build_plan
from autopilot.script_draft_agent import build_draft_input, validate_proposal
from autopilot.claim_review_dossier import (
    DOSSIER_STATUS, EditorialGateError, build_review_dossier,
    review_three_episode_candidates,
)

SOURCES = (
    ("OpenAI", "https://openai.com/index/agent-research"),
    ("Google DeepMind", "https://deepmind.google/discover/blog/sample-research"),
    ("The Verge", "https://www.theverge.com/2026/11/4/sample-technology"),
)
TOPICS = (
    ("identifier strings", "Preserve the full string value of an identifier and show the original sample beside the program output. The example uses invented records."),
    ("ISO date validation", "Inspect dates using an explicit year month and day contract. Flag an invalid example without changing the original record."),
    ("duplicate conflict checks", "Compare duplicate keys in an invented dataset. Keep the conflicting records separate and request a documented review decision."),
)
WALKTHROUGHS = (
    "Read an invented five-digit member identifier, execute a string-preserving CSV import, and compare each original leading zero to the computed program result.",
    "Prepare three made-up calendar values in ISO order. Parse each date and generate an exception report for the mismatched input without guessing its meaning.",
    "Create conflicting synthetic member records with identical keys but differing dates. Locate each pair and write a review list while keeping both source rows untouched.",
)


def fixture(index: int) -> tuple[dict, dict, dict]:
    slot = build_plan("2026-11-05")["slots"][index]
    publisher, url = SOURCES[index]
    identifier = hashlib.sha256(url.encode()).hexdigest()[:24]
    observations = {
        "status": "PUBLIC_SOURCE_METADATA_ONLY_NOT_FACT_VERIFIED",
        "claims_verified": 0,
        "youtube_upload_enabled": False,
        "sources": [{
            "source_id": identifier,
            "publisher": publisher,
            "title": "An unverified public research link used for testing only",
            "source_url": url,
            "status": "SOURCE_FETCHED_NOT_FACT_CHECKED",
            "observed_at_utc": "2026-11-04T05:10:00+00:00",
            "response_sha256": "d" * 64,
            "facts_verified": False,
            "youtube_release_authorized": False,
        }],
    }
    name, narration = TOPICS[index]
    raw = {
        "title": f"Practical tutorial for {name} with example values",
        "hook": f"Discover the {name} detail that changes this simple demonstration.",
        "viewer_benefit": f"Understand the {name} rule by following a small reversible technical example.",
        "example_walkthrough": WALKTHROUGHS[index],
        "narration": (narration + " ") * (4 if slot["format"] == "short" else 14),
        "visual_beats": [
            f"Show step {number} of the {name} sample with labels, actual data and an animated transition."
            for number in range(1, 7 if slot["format"] == "short" else 13)
        ],
        "claim_candidates": [{
            "claim": f"Example assumptions for {name} require direct independent review.",
            "source_ids": [identifier],
        }],
    }
    proposal = validate_proposal(raw, build_draft_input(slot, observations))
    return (proposal, slot, observations)


class ClaimReviewDossierTests(unittest.TestCase):
    def test_single_dossier_never_grants_rights_or_release(self):
        proposal, slot, observations = fixture(0)
        r = build_review_dossier(proposal, slot, observations)
        self.assertEqual(r["status"], DOSSIER_STATUS)
        self.assertEqual(r["proposed_claim_count"], 1)
        self.assertTrue(r["claim_candidates_not_exhaustive"])
        self.assertFalse(r["claim_inventory_human_checked"])
        self.assertFalse(r["all_claims_verified"])
        self.assertFalse(r["release_authorized"])
        self.assertFalse(r["youtube_upload_enabled"])
        self.assertFalse(r["youtube_schedule_enabled"])
        self.assertEqual(r["ai_realism_and_synthetic_disclosure_decision"], "PENDING_EDITORIAL_ASSESSMENT")
        self.assertEqual(r["claim_dossiers"][0]["reviewer_decision"], "PENDING")
        self.assertFalse(r["claim_dossiers"][0]["linked_source_observations"][0]["supports_exact_claim_verified"])

    def test_three_different_concepts_pass_novelty_screen_but_remain_blocked(self):
        all_items = [fixture(i) for i in range(3)]
        r = review_three_episode_candidates(all_items)
        self.assertEqual(r["formats"], ["short", "long", "short"])
        self.assertEqual(len(r["dossiers"]), 3)
        self.assertFalse(r["semantic_novelty_or_youtube_policy_compliance_proven"])
        self.assertFalse(r["release_authorized"])
        self.assertFalse(r["youtube_upload_enabled"])

    def test_forged_publish_status_rejected(self):
        proposal, slot, observations = fixture(0)
        proposal["release_authorized"] = True
        with self.assertRaises(EditorialGateError):
            build_review_dossier(proposal, slot, observations)

    def test_forged_fact_review_status_rejected(self):
        proposal, slot, observations = fixture(0)
        proposal["factual_claims_verified"] = True
        with self.assertRaises(EditorialGateError):
            build_review_dossier(proposal, slot, observations)

    def test_untrusted_extra_field_rejected(self):
        proposal, slot, observations = fixture(0)
        proposal["status_approved_by_ai"] = "READY_TO_PUBLISH"
        with self.assertRaises(EditorialGateError):
            build_review_dossier(proposal, slot, observations)

    def test_unbounded_narration_change_rejected(self):
        proposal, slot, observations = fixture(0)
        proposal["narration"] += " This inserted draft material is not approved." * 200
        with self.assertRaises(EditorialGateError):
            build_review_dossier(proposal, slot, observations)

    def test_cross_slot_replay_rejected(self):
        proposal, _, observations = fixture(0)
        other_slot = fixture(1)[1]
        with self.assertRaises(EditorialGateError):
            build_review_dossier(proposal, other_slot, observations)

    def test_repeated_cited_source_not_corroboration(self):
        proposal, slot, observations = fixture(0)
        proposal = deepcopy(proposal)
        proposal["claim_candidates"][0]["source_ids"].append(
            proposal["claim_candidates"][0]["source_ids"][0]
        )
        # Recheck the proposal after changing its contents, to prove a valid
        # structured model draft still cannot count one URL twice.
        draft_input = build_draft_input(slot, observations)
        proposal = validate_proposal(
            {key: proposal[key] for key in (
                "title", "hook", "viewer_benefit", "example_walkthrough",
                "narration", "visual_beats", "claim_candidates"
            )}, draft_input)
        with self.assertRaises(EditorialGateError):
            build_review_dossier(proposal, slot, observations)

    def test_two_publishers_still_do_not_verify_a_fact(self):
        proposal, slot, observations = fixture(0)
        other_source = fixture(1)[2]["sources"][0]
        observations["sources"].append(other_source)
        original_keys = (
            "title", "hook", "viewer_benefit", "example_walkthrough",
            "narration", "visual_beats", "claim_candidates"
        )
        raw = {key: deepcopy(proposal[key]) for key in original_keys}
        raw["claim_candidates"][0]["source_ids"].append(other_source["source_id"])
        proposal = validate_proposal(raw, build_draft_input(slot, observations))
        dossier = build_review_dossier(proposal, slot, observations)
        claim = dossier["claim_dossiers"][0]
        self.assertEqual(claim["distinct_publisher_labels_not_independent_attestations"], 2)
        self.assertFalse(claim["factually_verified"])
        self.assertTrue(dossier["syndication_or_shared_reporting_not_excluded"])

    def test_source_observation_escalation_rejected(self):
        proposal, slot, observations = fixture(0)
        observations["sources"][0]["facts_verified"] = True
        with self.assertRaises(EditorialGateError):
            build_review_dossier(proposal, slot, observations)

    def test_altered_source_origin_rejected(self):
        proposal, slot, observations = fixture(0)
        observations["sources"][0]["source_url"] = "http://127.0.0.1/metadata"
        with self.assertRaises(EditorialGateError):
            build_review_dossier(proposal, slot, observations)

    def test_same_three_topics_fail_novelty_gate(self):
        items = [fixture(i) for i in range(3)]
        duplicate = deepcopy(items[2][0])
        duplicate["title"] = items[0][0]["title"]
        slot, obs = items[2][1:]
        duplicate = validate_proposal({
            k: duplicate[k] for k in (
                "title", "hook", "viewer_benefit", "example_walkthrough",
                "narration", "visual_beats", "claim_candidates"
            )
        }, build_draft_input(slot, obs))
        items[2] = (duplicate, slot, obs)
        with self.assertRaises(EditorialGateError):
            review_three_episode_candidates(items)

    def test_nonconforming_three_pack_rejected(self):
        with self.assertRaises(EditorialGateError):
            review_three_episode_candidates([fixture(0), fixture(1)])


if __name__ == "__main__":
    unittest.main()
