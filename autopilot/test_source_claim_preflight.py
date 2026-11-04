"""B3d3a GitHub-only tests for exact observed source excerpts and atomic claims.

All source bodies are synthetic in-memory bytes. The three videos and their
signatures are TEST FIXTURES, not true, cleared or published YouTube content.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import unittest

from autopilot.test_script_continuity_gate import NOW, EXCLUDED, signed_fixture
from autopilot.source_claim_preflight import (
    STATUS, SourceClaimError, source_excerpt_evidence,
    script_surface_docket, atomic_claim_docket,
)


BODY = (
    b"An invented technical demonstration uses a CSV record with a five digit key. "
    b"The original string 00127 remains unchanged when it is parsed as text, "
    b"while converting that value to an integer changes the display of the key. "
    b"These are synthetic values, not sourced statistics. "
)
QUOTE = b"The original string 00127 remains unchanged when it is parsed as text"
START = BODY.index(QUOTE)


def accepted_source():
    # A source record with a matching response digest means byte equality,
    # NOT that the quote actually corroborates any drafted claim.
    observation = deepcopy(signed_fixture(0)[2]["sources"][0])
    observation["response_sha256"] = sha256(BODY).hexdigest()
    observation["body_bytes_hashed"] = len(BODY)
    observation["http_status"] = 200
    observation["response_content_type"] = "text/plain"
    return observation


def accepted_excerpt():
    return source_excerpt_evidence(accepted_source(), BODY, START, START + len(QUOTE))


def surface_packet(index=0):
    proposal, slot, sources, anchor, registry, seal, _ = signed_fixture(index)
    return script_surface_docket(
        proposal, slot, sources,
        seal=seal, anchor_manifest_sha256=anchor,
        registry=registry,
        excluded_creator_and_publisher_ids=EXCLUDED,
        now=NOW,
    )


def draft_claim(packet, excerpt):
    title = next(r for r in packet["surface_rows"] if r["surface_id"] == "title:0")
    statement = title["text_unreviewed"]
    return {
        "surface_id": "title:0",
        "start_char": 0,
        "end_char": len(statement),
        "claim_text": statement,
        "excerpt_keys": [[excerpt["source_id"], excerpt["excerpt_sha256"]]],
    }


class SourceClaimPreflightTests(unittest.TestCase):
    def test_byte_identical_observed_excerpt_only_creates_pending_evidence(self):
        rec = accepted_excerpt()
        self.assertEqual(rec["original_complete_response_sha256"], sha256(BODY).hexdigest())
        self.assertEqual(rec["excerpt_sha256"], sha256(QUOTE).hexdigest())
        self.assertTrue(rec["same_original_observed_response_bytes"])
        self.assertFalse(rec["semantic_support_for_claim_verified"])
        self.assertFalse(rec["source_independence_verified"])
        self.assertFalse(rec["publication_or_rights_permission"])
        self.assertNotIn("source_body", rec)
        self.assertNotIn("excerpt_text", rec)

    def test_source_bytes_mismatch_blocks_unsupported_quote(self):
        changed = BODY.replace(b"original string", b"altered string ")
        with self.assertRaises(SourceClaimError):
            source_excerpt_evidence(accepted_source(), changed, START, START + len(QUOTE))

    def test_rss_headline_cannot_claim_article_excerpt(self):
        observation = accepted_source()
        observation["status"] = "RSS_ENTRY_ONLY_ARTICLE_NOT_FETCHED"
        with self.assertRaises(SourceClaimError):
            source_excerpt_evidence(observation, BODY, START, START + len(QUOTE))

    def test_fake_verified_http_observation_rejected(self):
        observation = accepted_source()
        observation["facts_verified"] = True
        with self.assertRaises(SourceClaimError):
            source_excerpt_evidence(observation, BODY, START, START + len(QUOTE))

    def test_forged_source_url_rejected(self):
        observation = accepted_source()
        observation["source_url"] = "https://127.0.0.1/internal"
        with self.assertRaises(SourceClaimError):
            source_excerpt_evidence(observation, BODY, START, START + len(QUOTE))

    def test_misreported_size_rejected(self):
        observation = accepted_source()
        observation["body_bytes_hashed"] += 1
        with self.assertRaises(SourceClaimError):
            source_excerpt_evidence(observation, BODY, START, START + len(QUOTE))

    def test_non_html_binary_content_rejected(self):
        observation = accepted_source()
        observation["response_content_type"] = "application/pdf"
        with self.assertRaises(SourceClaimError):
            source_excerpt_evidence(observation, BODY, START, START + len(QUOTE))

    def test_invalid_offsets_bool_and_too_long_blocked(self):
        for start, end in ((True, 80), (-1, 80), (START, START+2), (0, len(BODY)+1)):
            with self.subTest(start=start, end=end):
                with self.assertRaises(SourceClaimError):
                    source_excerpt_evidence(accepted_source(), BODY, start, end)

    def test_original_source_bytes_not_unicode_cannot_be_a_quote(self):
        body = (b"A" * 130) + b"\xff" + (b"B" * 80)
        observation = accepted_source()
        observation["response_sha256"] = sha256(body).hexdigest()
        observation["body_bytes_hashed"] = len(body)
        with self.assertRaises(SourceClaimError):
            source_excerpt_evidence(observation, body, 120, 145)

    def test_all_defined_script_surfaces_listed_not_reviewed(self):
        for index in range(3):
            with self.subTest(episode=index):
                packet = surface_packet(index)
                names = {r["surface_id"] for r in packet["surface_rows"]}
                self.assertEqual(packet["status"], STATUS)
                self.assertIn("title:0", names)
                self.assertIn("hook:0", names)
                self.assertIn("viewer_benefit:0", names)
                self.assertIn("example_walkthrough:0", names)
                self.assertIn("visual_beat:0", names)
                self.assertTrue(any(x.startswith("narration:") for x in names))
                self.assertEqual(len(names), packet["defined_script_surface_count"])
                self.assertTrue(all(r["review_state"] == "PENDING" for r in packet["surface_rows"]))
                self.assertFalse(packet["all_defined_surfaces_reviewed"])
                self.assertFalse(packet["semantic_fact_detection_completed"])
                self.assertTrue(packet["unwritten_thumbnail_and_final_media_not_reviewable"])
                self.assertFalse(packet["youtube_upload_enabled"])

    def test_tampered_script_cannot_create_all_surface_docket(self):
        proposal, slot, sources, anchor, registry, seal, _ = signed_fixture(0)
        proposal["narration"] += " A different factual statement."
        with self.assertRaises(ValueError):
            script_surface_docket(
                proposal, slot, sources,
                seal=seal, anchor_manifest_sha256=anchor,
                registry=registry,
                excluded_creator_and_publisher_ids=EXCLUDED, now=NOW,
            )

    def test_atomic_claim_binds_exact_sealed_surface_and_source_excerpt(self):
        packet = surface_packet()
        rec = accepted_excerpt()
        result = atomic_claim_docket(packet, [draft_claim(packet, rec)], [rec])
        self.assertEqual(result["proposed_atomic_claim_count"], 1)
        self.assertEqual(result["source_excerpts_count_not_attestations"], 1)
        self.assertEqual(result["potential_claims"][0]["factual_support"], "PENDING")
        self.assertFalse(result["atomic_claims_exhaustive"])
        self.assertFalse(result["independent_factual_and_legal_review_complete"])
        self.assertFalse(result["render_authorized"])
        self.assertFalse(result["youtube_upload_enabled"])

    def test_no_atomic_claims_can_never_approve_script(self):
        packet = surface_packet()
        result = atomic_claim_docket(packet, [], [])
        self.assertEqual(result["proposed_atomic_claim_count"], 0)
        self.assertFalse(result["all_defined_surfaces_reviewed"])
        self.assertFalse(result["release_authorized"])

    def test_wrong_surface_or_span_or_forged_claim_string_rejected(self):
        packet, rec = surface_packet(), accepted_excerpt()
        for mutation in (
            {"surface_id": "thumbnail:0"},
            {"start_char": 1},
            {"end_char": 10000},
            {"claim_text": "Unsupported claim inserted by a model"},
            {"release_authorized": True},
        ):
            candidate = draft_claim(packet, rec)
            candidate.update(mutation)
            with self.subTest(mutation=mutation), self.assertRaises(SourceClaimError):
                atomic_claim_docket(packet, [candidate], [rec])

    def test_fake_corroboration_or_rights_grant_source_record_rejected(self):
        packet, rec = surface_packet(), accepted_excerpt()
        for field in ("semantic_support_for_claim_verified",
                      "source_independence_verified", "publication_or_rights_permission"):
            changed = dict(rec, **{field: True})
            with self.subTest(field=field), self.assertRaises(SourceClaimError):
                atomic_claim_docket(packet, [draft_claim(packet, rec)], [changed])

    def test_duplicate_claim_or_source_cannot_inflate_evidence(self):
        packet, rec = surface_packet(), accepted_excerpt()
        claim = draft_claim(packet, rec)
        with self.assertRaises(SourceClaimError):
            atomic_claim_docket(packet, [claim, claim], [rec])
        with self.assertRaises(SourceClaimError):
            atomic_claim_docket(packet, [claim], [rec, rec])
        double = dict(claim, excerpt_keys=[claim["excerpt_keys"][0]] * 2)
        with self.assertRaises(SourceClaimError):
            atomic_claim_docket(packet, [double], [rec])

    def test_unknown_excerpt_is_not_evidence(self):
        packet, rec = surface_packet(), accepted_excerpt()
        claim = draft_claim(packet, rec)
        claim["excerpt_keys"] = [[rec["source_id"], "f" * 64]]
        with self.assertRaises(SourceClaimError):
            atomic_claim_docket(packet, [claim], [rec])

    def test_surface_status_escalation_is_denied(self):
        packet = surface_packet()
        packet["all_defined_surfaces_reviewed"] = True
        with self.assertRaises(SourceClaimError):
            atomic_claim_docket(packet, [], [])


if __name__ == "__main__":
    unittest.main()
