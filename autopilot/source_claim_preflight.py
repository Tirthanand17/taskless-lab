"""B3d3a: exact observed-source excerpts + all-script-surface claim docket.

This is preflight evidence, not a fact checker. It validates exact bytes from an
independently supplied public-source observation and pins potential atomic
assertions to specific original script spans. It cannot determine if a quote
actually supports a claim, identify syndicated reporting, or approve rights.
NO secrets, network, privileged actions, file writes or YouTube APIs.
"""
from __future__ import annotations

from hashlib import sha256
import re
from datetime import datetime
from typing import Mapping

from autopilot.script_continuity_gate import DetachedScriptSeal, TrustedScriptCustodian
from autopilot.narration_review_inventory import prepare_sentence_review_docket
from autopilot.evidence_probe import EvidenceError, verify_public_source_url

STATUS = "B3D3A_SOURCE_AND_ATOMIC_CLAIM_EVIDENCE_PENDING_NO_PUBLISH"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
MAX_RESPONSE_BYTES = 1_048_576
MAX_EXCERPT_BYTES = 256
MAX_CLAIMS = 100
MAX_BEATS = 24


class SourceClaimError(ValueError):
    """Never guess provenance, script surface or independent review outcome."""


def source_excerpt_evidence(
    observation: dict, raw_response: bytes, start_byte: int, end_byte: int,
) -> dict:
    """Reconcile a short exact quote against previously observed HTTP bytes.

    This requires the ORIGINAL response bytes from a separately trusted
    retrieval, not a newer re-download. A byte-identical excerpt still does
    NOT prove factual support, independence, correct context, or legal rights.
    Actual body and excerpt text are NOT returned to GitHub or persisted here.
    """
    if not isinstance(observation, dict):
        raise SourceClaimError("Source observation must be a record")
    try:
        url = verify_public_source_url(observation.get("source_url"), observation.get("publisher"))
    except EvidenceError as exc:
        raise SourceClaimError("Unapproved public source origin") from exc
    if (observation.get("status") != "SOURCE_FETCHED_NOT_FACT_CHECKED"
            or observation.get("facts_verified") is not False
            or observation.get("youtube_release_authorized") is not False
            or not isinstance(observation.get("source_id"), str)
            or observation["source_id"] != sha256(url.encode("utf-8")).hexdigest()[:24]):
        raise SourceClaimError("RSS, forged status or wrong article identity")
    expected = observation.get("response_sha256")
    if not isinstance(expected, str) or not HEX64.fullmatch(expected):
        raise SourceClaimError("Missing observed complete response digest")
    if not isinstance(raw_response, bytes) or not 96 <= len(raw_response) <= MAX_RESPONSE_BYTES:
        raise SourceClaimError("Missing, empty or oversized original HTTP response")
    if sha256(raw_response).hexdigest() != expected:
        raise SourceClaimError("Source body differs from the original observation")
    if ("body_bytes_hashed" in observation
            and (type(observation["body_bytes_hashed"]) is not int
                 or observation["body_bytes_hashed"] != len(raw_response))):
        raise SourceClaimError("Body size differs from recorded observation")
    if ("http_status" in observation and observation["http_status"] != 200):
        raise SourceClaimError("Source was not a successful HTTP article")
    if ("response_content_type" in observation
            and observation["response_content_type"] not in (
                "text/plain", "text/html", "application/xhtml+xml")):
        raise SourceClaimError("Source observation is not an accepted textual article")
    if (type(start_byte) is not int or type(end_byte) is not int
            or start_byte < 0 or end_byte > len(raw_response)
            or not 16 <= end_byte - start_byte <= MAX_EXCERPT_BYTES):
        raise SourceClaimError("Unbounded or invalid exact response byte span")
    excerpt = raw_response[start_byte:end_byte]
    try:
        text = excerpt.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SourceClaimError("Excerpt must be valid UTF-8 text") from exc
    if not text.strip() or not re.search(r"\w", text, flags=re.UNICODE):
        raise SourceClaimError("Empty or punctuation-only excerpt")
    # Hash a narrow independent context window but do not disclose/copy a
    # copyrighted source body into public GitHub logs or the output dossier.
    surrounding = raw_response[max(0, start_byte - 160):min(len(raw_response), end_byte + 160)]
    return {
        "source_id": observation["source_id"],
        "publisher_label_not_independence_proof": observation["publisher"],
        "source_url": url,
        "original_complete_response_sha256": expected,
        "excerpt_start_byte": start_byte,
        "excerpt_end_byte": end_byte,
        "excerpt_sha256": sha256(excerpt).hexdigest(),
        "adjacent_context_sha256": sha256(surrounding).hexdigest(),
        "excerpt_length_bytes": len(excerpt),
        "same_original_observed_response_bytes": True,
        "semantic_support_for_claim_verified": False,
        "source_independence_verified": False,
        "human_context_review_complete": False,
        "publication_or_rights_permission": False,
    }


def script_surface_docket(
    proposal: dict, slot: dict, observations: dict,
    *, seal: DetachedScriptSeal,
    anchor_manifest_sha256: str,
    registry: Mapping[str, TrustedScriptCustodian],
    excluded_creator_and_publisher_ids: frozenset[str],
    now: datetime | None = None,
) -> dict:
    """Enumerate every currently defined model script surface after B3d1+B3d2."""
    narration = prepare_sentence_review_docket(
        proposal, slot, observations, seal=seal,
        anchor_manifest_sha256=anchor_manifest_sha256, registry=registry,
        excluded_creator_and_publisher_ids=excluded_creator_and_publisher_ids,
        now=now,
    )
    if (not isinstance(proposal, dict)
            or not isinstance(proposal.get("visual_beats"), list)
            or not 1 <= len(proposal["visual_beats"]) <= MAX_BEATS):
        raise SourceClaimError("Missing or unbounded script visual beat list")
    surfaces = []
    for r in narration["sentence_review_rows"]:
        surfaces.append({
            "surface_id": "narration:" + r["sentence_id"],
            "surface_kind": "spoken_sentence",
            "text_unreviewed": r["exact_spoken_text_unreviewed"],
            "origin_unicode_start": r["unicode_char_start"],
            "origin_unicode_end": r["unicode_char_end"],
            "text_sha256": sha256(r["exact_spoken_text_unreviewed"].encode("utf-8")).hexdigest(),
            "review_state": "PENDING",
        })
    for kind in ("title", "hook", "viewer_benefit", "example_walkthrough"):
        value = proposal.get(kind)
        if not isinstance(value, str) or not value.strip():
            raise SourceClaimError("Missing unspoken script surface")
        surfaces.append({
            "surface_id": kind + ":0",
            "surface_kind": kind,
            "text_unreviewed": value,
            "origin_unicode_start": 0,
            "origin_unicode_end": len(value),
            "text_sha256": sha256(value.encode("utf-8")).hexdigest(),
            "review_state": "PENDING",
        })
    for index, value in enumerate(proposal["visual_beats"]):
        if not isinstance(value, str) or not value.strip():
            raise SourceClaimError("Invalid unreviewed visual scene description")
        surfaces.append({
            "surface_id": f"visual_beat:{index}",
            "surface_kind": "planned_visual_beat",
            "text_unreviewed": value,
            "origin_unicode_start": 0,
            "origin_unicode_end": len(value),
            "text_sha256": sha256(value.encode("utf-8")).hexdigest(),
            "review_state": "PENDING",
        })
    if len({r["surface_id"] for r in surfaces}) != len(surfaces):
        raise SourceClaimError("Duplicate source surface identities")
    observed_sources = []
    for row in observations.get("sources", []):
        if (not isinstance(row, dict) or row.get("status") not in (
            "SOURCE_FETCHED_NOT_FACT_CHECKED", "RSS_ENTRY_ONLY_ARTICLE_NOT_FETCHED")
                or not isinstance(row.get("source_id"), str)
                or not isinstance(row.get("response_sha256"), str)
                or not HEX64.fullmatch(row["response_sha256"])):
            raise SourceClaimError("Malformed signed public-source observation")
        observed_sources.append({
            "source_id": row["source_id"],
            "response_sha256": row["response_sha256"],
            "status": row["status"],
        })
    if len({r["source_id"] for r in observed_sources}) != len(observed_sources):
        raise SourceClaimError("Repeated observed source identity")
    return {
        "schema_version": 1,
        "status": STATUS,
        "episode_id": narration["episode_id"],
        "manifest_sha256": narration["externally_anchored_script_manifest_sha256"],
        "surface_rows": surfaces,
        "signed_source_response_index": observed_sources,
        "defined_script_surface_count": len(surfaces),
        "all_defined_script_surfaces_present": True,
        "all_defined_surfaces_reviewed": False,
        "unwritten_thumbnail_and_final_media_not_reviewable": True,
        "caption_and_actual_render_claims_not_reviewable": True,
        "semantic_fact_detection_completed": False,
        "youtube_upload_enabled": False,
        "release_authorized": False,
    }


def atomic_claim_docket(
    surface_docket: dict,
    proposed_atomic_claims: list[dict],
    excerpt_records: list[dict],
) -> dict:
    """Bind proposed atomic claims to literal surface spans and original excerpts.

    Every claimed connection is PENDING and NOT factual corroboration. The
    atomic-claim list can never be treated as complete without an independently
    trusted full-surface review, which this module does not provide.
    """
    if (not isinstance(surface_docket, dict)
            or surface_docket.get("status") != STATUS
            or surface_docket.get("all_defined_script_surfaces_present") is not True
            or surface_docket.get("all_defined_surfaces_reviewed") is not False
            or surface_docket.get("release_authorized") is not False
            or surface_docket.get("youtube_upload_enabled") is not False):
        raise SourceClaimError("Untrusted script surface review status")
    if (not isinstance(proposed_atomic_claims, list)
            or len(proposed_atomic_claims) > MAX_CLAIMS
            or not isinstance(excerpt_records, list)
            or len(excerpt_records) > MAX_CLAIMS * 3):
        raise SourceClaimError("Unbounded claim or excerpt evidence batch")
    all_surfaces = surface_docket.get("surface_rows")
    if not isinstance(all_surfaces, list) or not all_surfaces:
        raise SourceClaimError("Empty or forged surface inventory")
    surfaces = {r["surface_id"]: r for r in all_surfaces
                if isinstance(r, dict) and isinstance(r.get("surface_id"), str)}
    if len(surfaces) != len(all_surfaces):
        raise SourceClaimError("Invalid or repeated surface identities")
    index = surface_docket.get("signed_source_response_index")
    if not isinstance(index, list):
        raise SourceClaimError("No authenticated source response index")
    observed = {x["source_id"]: x for x in index
                if isinstance(x, dict) and isinstance(x.get("source_id"), str)}
    if len(observed) != len(index):
        raise SourceClaimError("Repeated or malformed signed source identities")
    excerpts = {}
    for rec in excerpt_records:
        if (not isinstance(rec, dict)
                or rec.get("same_original_observed_response_bytes") is not True
                or rec.get("semantic_support_for_claim_verified") is not False
                or rec.get("source_independence_verified") is not False
                or rec.get("publication_or_rights_permission") is not False
                or not isinstance(rec.get("excerpt_sha256"), str)
                or not HEX64.fullmatch(rec["excerpt_sha256"])
                or not isinstance(rec.get("source_id"), str)
                or not re.fullmatch(r"[0-9a-f]{24}", rec["source_id"])):
            raise SourceClaimError("Forged source excerpt approval or identity")
        source = observed.get(rec["source_id"])
        if (source is None
                or source.get("status") != "SOURCE_FETCHED_NOT_FACT_CHECKED"
                or source.get("response_sha256") != rec.get("original_complete_response_sha256")):
            raise SourceClaimError("Excerpt is not from the exact signed source response")
        key = (rec["source_id"], rec["excerpt_sha256"])
        if key in excerpts:
            raise SourceClaimError("Duplicated source/excerpt to inflate support")
        excerpts[key] = rec
    results = []
    ids = set()
    for raw in proposed_atomic_claims:
        if not isinstance(raw, dict) or set(raw) != {
            "surface_id", "start_char", "end_char", "claim_text", "excerpt_keys"
        }:
            raise SourceClaimError("Unexpected, missing or privileged proposed-claim field")
        source = surfaces.get(raw["surface_id"]) if isinstance(raw.get("surface_id"), str) else None
        if not source:
            raise SourceClaimError("Claim refers to an unobserved script surface")
        start, end, claim_text = raw["start_char"], raw["end_char"], raw["claim_text"]
        base = source.get("text_unreviewed")
        if (not isinstance(base, str) or type(start) is not int or type(end) is not int
                or start < 0 or not start < end <= len(base)
                or not isinstance(claim_text, str)
                or not 4 <= len(claim_text.strip()) <= 1000
                or base[start:end] != claim_text):
            raise SourceClaimError("Claim text must match exact sealed script span")
        keys = raw["excerpt_keys"]
        if not isinstance(keys, list) or len(keys) > 6:
            raise SourceClaimError("Claim has an unbounded source citation set")
        seen = set()
        refs = []
        for pair in keys:
            if (not isinstance(pair, (list, tuple)) or len(pair) != 2
                    or not all(isinstance(x, str) for x in pair)):
                raise SourceClaimError("Malformed source/excerpt link")
            key = tuple(pair)
            if key not in excerpts or key in seen:
                raise SourceClaimError("Unknown or repeated exact source excerpt")
            seen.add(key)
            refs.append({
                "source_id": key[0],
                "excerpt_sha256": key[1],
                "factual_claim_support_assessed": False,
            })
        claim_id = sha256(
            (surface_docket["manifest_sha256"] + "\n" + raw["surface_id"] +
             "\n" + str(start) + "\n" + str(end) + "\n" + claim_text).encode("utf-8")
        ).hexdigest()[:24]
        if claim_id in ids:
            raise SourceClaimError("Same atomic claim was counted twice")
        ids.add(claim_id)
        results.append({
            "atomic_claim_id": claim_id,
            "surface_id": raw["surface_id"],
            "exact_claim_text_unreviewed": claim_text,
            "source_span_start_char": start,
            "source_span_end_char": end,
            "cited_excerpt_links": refs,
            "independent_atomicity_and_completeness_review": "PENDING",
            "factual_support": "PENDING",
            "context_and_date_accuracy": "PENDING",
            "contradictions_assessed": False,
            "source_independence_assessed": False,
            "rights_clearance": False,
            "human_reviewer_attestation": False,
        })
    return {
        "schema_version": 1,
        "status": STATUS,
        "episode_id": surface_docket["episode_id"],
        "manifest_sha256": surface_docket["manifest_sha256"],
        "proposed_atomic_claim_count": len(results),
        "potential_claims": results,
        "source_excerpts_count_not_attestations": len(excerpts),
        "atomic_claims_exhaustive": False,
        "all_defined_surfaces_reviewed": False,
        "independent_factual_and_legal_review_complete": False,
        "render_authorized": False,
        "youtube_upload_enabled": False,
        "youtube_schedule_enabled": False,
        "release_authorized": False,
    }
