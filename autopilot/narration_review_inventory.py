"""Branch 2 B3d2: exhaustive spoken-sentence review docket (NO FACT APPROVAL).

A generative model can omit factual assertions from its self-reported claim
list. Every spoken sentence must therefore get a separate pending review row
after the full exact narration is cryptographically bound by B3d1. This module
neither judges whether a sentence is factual nor verifies source truth.
No network, real reviewer, paid model, file persistence or publishing calls.
"""
from __future__ import annotations

from hashlib import sha256
import re
from typing import Mapping
from datetime import datetime

from autopilot.claim_review_dossier import build_review_dossier
from autopilot.script_continuity_gate import (
    DetachedScriptSeal, TrustedScriptCustodian, verify_script_seal,
    ScriptContinuityError,
)

STATUS = "NARRATION_WIDE_SENTENCE_REVIEW_PENDING_NO_PUBLISH"
MAX_SENTENCES = 160
MAX_NARRATION_CHARS = 20_000
SEGMENT = re.compile(r"[^.!?]*[.!?]+|[^.!?]+$", re.DOTALL)


class NarrationInventoryError(ValueError):
    """All spoken content must be included or reject the review packet."""


def sentence_spans(narration: str) -> tuple[tuple[int, int, str], ...]:
    """Deterministic Unicode-character spans preserving every original character.

    This is intentionally a coarse punctuation segmentation, NOT semantic NLP.
    Abbreviations, decimals and punctuated initials may create fragments which
    require manual reconciliation, not silently vanished or approved facts.
    """
    if (not isinstance(narration, str) or not narration.strip()
            or len(narration) > MAX_NARRATION_CHARS):
        raise NarrationInventoryError("Missing or unbounded exact spoken narration")
    chunks = list(SEGMENT.finditer(narration))
    if not 1 <= len(chunks) <= MAX_SENTENCES:
        raise NarrationInventoryError("No sentences or too many narration fragments")
    spans = []
    for chunk in chunks:
        raw = chunk.group(0)
        sentence = raw.strip()
        if (not sentence or not re.search(r"\w", sentence, flags=re.UNICODE)
                or len(sentence) > 1250):
            raise NarrationInventoryError("Empty, punctuation-only or excessive sentence")
        spans.append((chunk.start(), chunk.end(), sentence))
    if "".join(narration[start:end] for start, end, _ in spans) != narration:
        raise NarrationInventoryError("Some narration characters were omitted")
    if spans[0][0] != 0 or spans[-1][1] != len(narration):
        raise NarrationInventoryError("Narration beginning/end omitted")
    for prev, nxt in zip(spans, spans[1:]):
        if prev[1] != nxt[0]:
            raise NarrationInventoryError("Narration segmentation skipped a span")
    return tuple(spans)


def prepare_sentence_review_docket(
    proposal: dict, slot: dict, observations: dict,
    *, seal: DetachedScriptSeal,
    anchor_manifest_sha256: str,
    registry: Mapping[str, TrustedScriptCustodian],
    excluded_creator_and_publisher_ids: frozenset[str],
    now: datetime | None = None,
) -> dict:
    """Require B3d1 detached signature before inventorying all spoken sentences."""
    continuity = verify_script_seal(
        proposal, slot, observations,
        seal=seal, anchor_manifest_sha256=anchor_manifest_sha256,
        registry=registry,
        excluded_creator_and_publisher_ids=excluded_creator_and_publisher_ids,
        now=now,
    )
    if (continuity.get("immutable_content_binding_checked") is not True
            or continuity.get("release_authorized") is not False
            or continuity.get("youtube_upload_enabled") is not False):
        raise NarrationInventoryError("Untrusted B3d1 provenance boundary")
    dossier = build_review_dossier(proposal, slot, observations)
    spans = sentence_spans(proposal["narration"])
    script_hash = continuity["manifest_sha256"]
    rows = []
    for index, (start, end, text) in enumerate(spans, 1):
        exact_raw = proposal["narration"][start:end]
        row_id = sha256(
            (script_hash + "\n" + str(index) + "\n" + str(start)
             + "\n" + str(end) + "\n" + exact_raw).encode("utf-8")
        ).hexdigest()[:24]
        rows.append({
            "sentence_id": row_id,
            "ordinal": index,
            "unicode_char_start": start,
            "unicode_char_end": end,
            "exact_spoken_text_unreviewed": text,
            "verbatim_segment_sha256": sha256(exact_raw.encode("utf-8")).hexdigest(),
            "independent_statement_classification": "PENDING",
            "factual_claims_in_sentence_identified_by_reviewer": False,
            "independently_corrob_source_text_verified": False,
            "source_context_and_date_reviewed": False,
            "potentially_reused_or_syndicated_sources_excluded": False,
            "materially_misleading_claims_excluded": False,
            "rights_and_originality_reviewed": False,
            "reviewer_outcome": "PENDING",
        })
    if len({r["sentence_id"] for r in rows}) != len(rows):
        raise NarrationInventoryError("Repeated sentence review identifier")
    # Even when the model proposes zero claims, ALL narration remains pending.
    return {
        "schema_version": 1,
        "status": STATUS,
        "episode_id": continuity["episode_id"],
        "release_slot": continuity["release_slot"],
        "externally_anchored_script_manifest_sha256": script_hash,
        "sentence_inventory_source": "COMPLETE_ORIGINAL_PROPOSAL_NARRATION",
        "segmentation_is_not_semantic_fact_detection": True,
        "full_narration_characters_accounted_for": True,
        "number_of_sentence_review_rows": len(rows),
        "pending_independent_sentence_reviews": len(rows),
        "model_reported_candidate_claim_count": len(dossier["claim_dossiers"]),
        "model_candidate_claim_inventory_complete": False,
        "candidate_claims_untrusted": [
            {"candidate_claim_id": x["claim_id"], "reported_claim_unverified": x["candidate_claim_untrusted"]}
            for x in dossier["claim_dossiers"]
        ],
        "source_observation_count_not_fact_attestations": dossier["unverified_source_count"],
        "sentence_review_rows": rows,
        "external_ledger_authenticity_verified_by_software": False,
        "all_claims_correct_or_complete": False,
        "human_fact_review_complete": False,
        "copyright_and_originality_approved": False,
        "ai_disclosure_decision_complete": False,
        "media_render_enabled": False,
        "youtube_upload_enabled": False,
        "youtube_schedule_enabled": False,
        "release_authorized": False,
        "next_gate": "Authenticated independent assessment of every narrated sentence and its sources, context and rights",
    }
