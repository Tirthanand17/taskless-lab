"""B3d2 GitHub-only cover-all-spoken-sentences tests, no human fact approval.

The example signed receipts use disposable keys only. These demonstrations
are NOT actual source-supported or rights-licensed YouTube content.
"""
from __future__ import annotations

from copy import deepcopy
import unittest

from autopilot.test_script_continuity_gate import NOW, EXCLUDED, signed_fixture
from autopilot.script_draft_agent import validate_proposal, build_draft_input
from autopilot.narration_review_inventory import (
    STATUS, NarrationInventoryError, sentence_spans, prepare_sentence_review_docket
)
from autopilot.script_continuity_gate import ScriptContinuityError


def prepare(item):
    proposal, slot, sources, anchor, root, seal, _ = item
    return prepare_sentence_review_docket(
        proposal, slot, sources,
        seal=seal, anchor_manifest_sha256=anchor, registry=root,
        excluded_creator_and_publisher_ids=EXCLUDED, now=NOW
    )


class NarrationInventoryTests(unittest.TestCase):
    def test_complete_spoken_sentence_coverage_not_factual_certification(self):
        item = signed_fixture(0)
        dossier = prepare(item)
        self.assertEqual(dossier["status"], STATUS)
        spans = dossier["sentence_review_rows"]
        self.assertEqual(dossier["number_of_sentence_review_rows"], len(spans))
        self.assertGreater(len(spans), dossier["model_reported_candidate_claim_count"])
        self.assertEqual(len(spans), dossier["pending_independent_sentence_reviews"])
        self.assertTrue(dossier["full_narration_characters_accounted_for"])
        self.assertFalse(dossier["model_candidate_claim_inventory_complete"])
        self.assertFalse(dossier["all_claims_correct_or_complete"])
        self.assertFalse(dossier["release_authorized"])
        self.assertFalse(dossier["youtube_upload_enabled"])
        self.assertFalse(dossier["media_render_enabled"])
        self.assertTrue(all(r["reviewer_outcome"] == "PENDING" for r in spans))
        self.assertTrue(all(r["independent_statement_classification"] == "PENDING" for r in spans))

    def test_all_three_episodes_distinct_and_fully_pending(self):
        packs = [prepare(signed_fixture(i)) for i in range(3)]
        self.assertEqual([p["release_slot"] for p in packs], ["short_am", "long", "short_pm"])
        self.assertEqual(len({p["externally_anchored_script_manifest_sha256"] for p in packs}), 3)
        self.assertTrue(all(p["pending_independent_sentence_reviews"] > 0 for p in packs))
        self.assertTrue(all(not p["youtube_schedule_enabled"] for p in packs))

    def test_exact_unicode_character_coverage(self):
        spoken = "One ID is ００１２７. Here's a Unicode example—keep it. End?"
        spans = sentence_spans(spoken)
        self.assertEqual("".join(spoken[start:end] for start, end, _ in spans), spoken)
        self.assertEqual(spans[0][0], 0)
        self.assertEqual(spans[-1][1], len(spoken))

    def test_no_terminal_punctuation_still_inventoried(self):
        spoken = "A first claim. A second unpunctuated claim"
        spans = sentence_spans(spoken)
        self.assertEqual(len(spans), 2)
        self.assertEqual("".join(spoken[a:b] for a,b,_ in spans), spoken)

    def test_one_word_sentence_never_silently_disappears(self):
        spans = sentence_spans("Yes. Another relevant assertion appears.")
        self.assertEqual(len(spans), 2)
        self.assertEqual(spans[0][2], "Yes.")

    def test_abbreviations_remain_visible_for_manual_review(self):
        text = "For example, U.S. data could differ by context."
        spans = sentence_spans(text)
        self.assertEqual("".join(text[a:b] for a,b,_ in spans), text)
        self.assertTrue(len(spans) >= 2)

    def test_punctuation_only_fragment_is_blocked(self):
        with self.assertRaises(NarrationInventoryError):
            sentence_spans("... Real words are later.")

    def test_empty_narration_blocked(self):
        with self.assertRaises(NarrationInventoryError):
            sentence_spans(" ")

    def test_unbounded_narration_blocked(self):
        with self.assertRaises(NarrationInventoryError):
            sentence_spans("Safe test words. " * 2000)

    def test_excessive_sentence_count_blocked(self):
        with self.assertRaises(NarrationInventoryError):
            sentence_spans("Short word. " * 161)

    def test_valid_draft_with_zero_model_candidate_claims_still_fully_inventoried(self):
        # A model may omit every claim. This is not permission to exempt text.
        item = list(signed_fixture(0))
        proposal, slot, sources = item[:3]
        raw = {key: deepcopy(proposal[key]) for key in (
            "title", "hook", "viewer_benefit", "example_walkthrough",
            "narration", "visual_beats", "claim_candidates")}
        raw["claim_candidates"] = []
        draft = validate_proposal(raw, build_draft_input(slot, sources))
        # External detached signature must be changed too: without independently
        # anchored content, this candidate MUST fail before inventory construction.
        item[0] = draft
        with self.assertRaises(ScriptContinuityError):
            prepare(item)
        # A syntactic-only script alone therefore cannot bypass the trust step.

    def test_modified_narration_breaks_signed_boundary(self):
        item = list(signed_fixture(0))
        item[0] = deepcopy(item[0])
        item[0]["narration"] += " A totally different assertion."
        with self.assertRaises(ScriptContinuityError):
            prepare(item)

    def test_different_source_title_breaks_anchored_integrity(self):
        item = list(signed_fixture(0))
        item[2] = deepcopy(item[2])
        item[2]["sources"][0]["title"] = "A changed public source title should cause an integrity failure"
        with self.assertRaises(ScriptContinuityError):
            prepare(item)

    def test_moved_calendar_slot_blocks_inventory(self):
        item = list(signed_fixture(0))
        item[1] = dict(item[1], local_ist="20:30")
        with self.assertRaises(ScriptContinuityError):
            prepare(item)

    def test_bad_anchor_blocks_inventory(self):
        item = list(signed_fixture(0))
        item[3] = "f" * 64
        with self.assertRaises(ScriptContinuityError):
            prepare(item)

    def test_missing_custodian_registry_blocks_inventory(self):
        item = list(signed_fixture(0))
        item[4] = {}
        with self.assertRaises(ScriptContinuityError):
            prepare(item)


if __name__ == "__main__":
    unittest.main()
