"""FlowMinute Phase 2R2: claim-level editorial review PREPARATION, offline only.

Never treats quoted passages as proof of factual accuracy. Validates exact
research/source/quote bindings, contradictory review positions, recency and
reviewer separation. Reviewer IDs and verdicts are caller assertions with NO
cryptographic or human identity authentication. No live source collection,
credential use, cloud account writes, video creation or publishing.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import re
from typing import Sequence

from .agent_org import WorkflowError
from .phase2_pipeline import ResearchPackage, _stamp, digest
from .phase2_source_evidence import (
    ClaimExcerpt, SourceCapture, verify_source_text_evidence,
)

_ID = re.compile(r"[a-z][a-z0-9_]{2,63}\Z")
_HEX = re.compile(r"[a-f0-9]{64}\Z")
VERDICTS = frozenset(("SUPPORTS", "CONTRADICTS", "AMBIGUOUS", "UNREVIEWED"))
CLAIM_KINDS = frozenset(("evergreen", "product_access", "pricing", "performance_benchmark", "news"))
SENSITIVE_KINDS = frozenset(("product_access", "pricing", "performance_benchmark", "news"))
RECENT_WINDOW = timedelta(hours=24)
REVIEW_AGE = timedelta(hours=24)
MAX_NOTE = 600


class EditorialBlocked(WorkflowError):
    """Structural claim-review contract is missing or cannot be trusted."""


@dataclass(frozen=True)
class ClaimAssessment:
    claim_id: str
    source_id: str
    quote_sha256: str
    claim_sha256: str
    claim_kind: str
    verdict: str
    reviewer_id: str
    reviewed_at_utc: str
    interpretation_note: str
    vendor_claim_explicitly_attributed: bool = False


@dataclass(frozen=True)
class DemoAssessment:
    demonstration_sha256: str
    reviewer_id: str
    reviewed_at_utc: str
    verdict: str  # PASS | REJECT | NEEDS_REVIEW
    synthetic_demo_labeled: bool
    real_product_screen_claimed: bool
    evidence_note: str


def _check_time(value: str, *, now: datetime) -> datetime:
    when = _stamp(value)
    if not timedelta(0) <= now - when <= REVIEW_AGE:
        raise EditorialBlocked("Review is stale or future dated")
    return when


def _text_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def prepare_editorial_review(
    *,
    research: ResearchPackage,
    captures: Sequence[SourceCapture],
    excerpts: Sequence[ClaimExcerpt],
    assessments: Sequence[ClaimAssessment],
    demo: DemoAssessment,
    creator_id: str,
    now: datetime,
) -> dict:
    """Prepare a fail-closed issue report; NEVER approve scripts or publishing.

    All role claims, quote content, capture timestamps, publisher independence
    and reviewer verdicts are UNTRUSTED. A positive-looking packet is not an
    authenticated independent fact-review or quality assurance decision.
    """
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise EditorialBlocked("Verifier requires timezone-aware clock")
    now_utc = now.astimezone(timezone.utc)
    if not isinstance(research, ResearchPackage):
        raise EditorialBlocked("Typed research package required")
    if not isinstance(creator_id, str) or not _ID.fullmatch(creator_id):
        raise EditorialBlocked("Safe creator identity label required")
    if (not isinstance(assessments, (list, tuple)) or len(assessments) > 40
            or not isinstance(demo, DemoAssessment)
            or not isinstance(excerpts, (list, tuple))):
        raise EditorialBlocked("Bounded claim and demo review artifacts required")
    try:
        evidence = verify_source_text_evidence(research, captures, excerpts, now=now_utc)
    except (ValueError, TypeError, WorkflowError) as exc:
        raise EditorialBlocked("Source/quote structural preflight not satisfied") from exc

    citation_by_id = {x.source_id: x for x in research.sources}
    claim_by_id = {x.claim_id: x for x in research.claims}
    quotes = {(e.claim_id, e.source_id): _text_hash(e.quoted_text) for e in excerpts}
    expected_pairs = set(quotes)
    found: dict[tuple[str, str], ClaimAssessment] = {}
    reviewer_ids = set()
    review_times = []
    kinds: dict[str, str] = {}
    for a in assessments:
        if not isinstance(a, ClaimAssessment):
            raise EditorialBlocked("Typed claim assessment required")
        key = (a.claim_id, a.source_id)
        if key not in expected_pairs or key in found:
            raise EditorialBlocked("Unknown or duplicated claim/source assessment")
        if (a.quote_sha256 != quotes[key]
                or a.claim_sha256 != _text_hash(claim_by_id[a.claim_id].statement)
                or not isinstance(a.claim_kind, str) or a.claim_kind not in CLAIM_KINDS
                or a.verdict not in VERDICTS
                or not isinstance(a.reviewer_id, str) or not _ID.fullmatch(a.reviewer_id)
                or a.reviewer_id == creator_id
                or not isinstance(a.interpretation_note, str)
                or not 25 <= len(a.interpretation_note.strip()) <= MAX_NOTE
                or type(a.vendor_claim_explicitly_attributed) is not bool):
            raise EditorialBlocked("Reviewer, claim, quote or assessment binding invalid")
        reviewed_at = _check_time(a.reviewed_at_utc, now=now_utc)
        # News/pricing/access/vendor benchmarks need recent original source
        # observations and cannot cite week-old copied claim text as current.
        if a.claim_kind in SENSITIVE_KINDS:
            source_time = _stamp(citation_by_id[a.source_id].checked_at_utc)
            cap = next(c for c in captures if c.source_id == a.source_id)
            capture_time = _stamp(cap.observed_at_utc)
            if (now_utc - source_time > RECENT_WINDOW
                    or now_utc - capture_time > RECENT_WINDOW):
                raise EditorialBlocked("Rapidly changing claim needs fresh source/capture")
            if a.claim_kind == "performance_benchmark" and not a.vendor_claim_explicitly_attributed:
                raise EditorialBlocked("Performance marketing claim requires explicit company attribution")
        if a.claim_id in kinds and kinds[a.claim_id] != a.claim_kind:
            raise EditorialBlocked("Inconsistent claim risk classification")
        kinds[a.claim_id] = a.claim_kind
        reviewer_ids.add(a.reviewer_id)
        review_times.append(reviewed_at)
        found[key] = a
    if set(found) != expected_pairs:
        raise EditorialBlocked("Every quoted claim/source pair needs independent review position")
    if set(kinds) != set(claim_by_id):
        raise EditorialBlocked("Unclassified claim")
    if (not isinstance(demo.demonstration_sha256, str)
            or not _HEX.fullmatch(demo.demonstration_sha256)
            or demo.demonstration_sha256 != _text_hash(research.demonstration)
            or not isinstance(demo.reviewer_id, str)
            or not _ID.fullmatch(demo.reviewer_id)
            or demo.reviewer_id == creator_id
            or demo.reviewer_id in reviewer_ids
            or demo.verdict not in ("PASS", "REJECT", "NEEDS_REVIEW")
            or type(demo.synthetic_demo_labeled) is not bool
            or type(demo.real_product_screen_claimed) is not bool
            or not isinstance(demo.evidence_note, str)
            or not 25 <= len(demo.evidence_note.strip()) <= MAX_NOTE):
        raise EditorialBlocked("Demo/creator/reviewer separation or evidence invalid")
    _check_time(demo.reviewed_at_utc, now=now_utc)

    issues = []
    claim_results = []
    for claim_id in sorted(claim_by_id):
        related = [v for k,v in found.items() if k[0] == claim_id]
        types = {citation_by_id[x.source_id].kind for x in related
                 if x.verdict == "SUPPORTS"}
        if any(x.verdict == "CONTRADICTS" for x in related):
            issues.append("CONTRADICTORY_EVIDENCE:" + claim_id)
        if any(x.verdict in ("AMBIGUOUS", "UNREVIEWED") for x in related):
            issues.append("UNCERTAIN_SOURCE_SUPPORT:" + claim_id)
        if types != {"official", "independent"}:
            issues.append("MISSING_DUAL_REVIEW_SUPPORT:" + claim_id)
        claim_results.append({
            "claim_id": claim_id,
            "risk_kind": kinds[claim_id],
            "source_verdict_counts": {
                state: sum(v.verdict == state for v in related)
                for state in sorted(VERDICTS)
            },
        })
    if demo.verdict != "PASS":
        issues.append("DEMO_NOT_REVIEWED_OR_REJECTED")
    if not demo.synthetic_demo_labeled:
        issues.append("DEMO_SIMULATION_LABEL_REQUIRED")
    if demo.real_product_screen_claimed:
        issues.append("REAL_SCREEN_RECORDING_REQUIRES_INDEPENDENT_ASSET_EVIDENCE")

    # Summary never contains raw article, exact quotations, reviewer notes or
    # claims. Fields report internal consistency only, not approval.
    status = ("ISSUES_REQUIRE_INDEPENDENT_EDITORIAL_REVIEW"
              if issues else "STRUCTURALLY_COMPLETE_UNAUTHENTICATED_REVIEW")
    stable_summary = {
        "schema_version": 1,
        "status": status,
        "episode_id": research.episode_id,
        "research_sha256": digest(research),
        "source_hashes": evidence["source_hashes"],
        "assessment_count": len(found),
        "claim_reports": claim_results,
        "issues": sorted(set(issues)),
    }
    stable_sha256 = sha256(json.dumps(stable_summary, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()
    return {
        **stable_summary,
        "report_sha256": stable_sha256,
        "quarantine": bool(issues),
        "reviewer_identity_authenticated": False,
        "independent_source_factual_accuracy_verified": False,
        "human_editorial_verdict_verified": False,
        "demo_real_screen_recording_verified": False,
        "source_text_retrieved_by_authenticated_collector": False,
        "ready_for_production_script": False,
        "ready_for_media_generation": False,
        "publishing_authorized": False,
        "network_calls": 0,
        "spend_inr": 0,
    }
