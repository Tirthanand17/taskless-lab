"""Phase 2R evidence-text preflight for educational video drafts (OFFLINE ONLY).

No network, browsing, remote account, model calls, media creation or publishing.
This validates caller-supplied source capture snapshots and source-text excerpts
against the existing Phase2 ResearchPackage. Caller controls every observation,
including claimed HTTP status, timestamp and publisher, so this module NEVER
asserts factual truth, independent human approval or real source retrieval.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from html.parser import HTMLParser
import re
import unicodedata
from typing import Sequence
from urllib.parse import urlsplit

from .agent_org import WorkflowError
from .phase2_pipeline import ResearchPackage, _https_source, _stamp

MAX_SNAPSHOT_BYTES = 131_072
MAX_TOTAL_BYTES = 500_000
MAX_EXCERPTS = 40
MAX_EXCERPT_CHARS = 500
MAX_SOURCE_AGE = timedelta(days=7)
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
SAFE_FETCHER = re.compile(r"[a-z][a-z0-9_]{2,63}\Z")
WHITESPACE = re.compile(r"\s+")


class EvidenceBlocked(WorkflowError):
    """Inputs do not satisfy the conservative structural research contract."""


class _VisibleHTML(HTMLParser):
    """Extract visible-ish HTML text, never script/style/template contents."""
    SKIP = frozenset({"script", "style", "head", "template", "svg", "noscript"})
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.excluded: list[str] = []
        self.chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag.lower() in self.SKIP:
            self.excluded.append(tag.lower())

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.SKIP and tag.lower() in self.excluded:
            # HTML from websites is often malformed. Still refuse to treat
            # anything under a non-closed excluded element as visible text.
            for i in range(len(self.excluded) - 1, -1, -1):
                if self.excluded[i] == tag.lower():
                    del self.excluded[i:]
                    break

    def handle_data(self, data: str) -> None:
        if not self.excluded:
            self.chunks.append(data)


def _normalize(value: str) -> str:
    return WHITESPACE.sub(" ", unicodedata.normalize("NFKC", value).casefold()).strip()


def _origin(url: str) -> tuple[str, str, int]:
    host = _https_source(url)
    parsed = urlsplit(url)
    return (parsed.scheme.lower(), host, parsed.port or 443)


def _related_hosts(a: str, b: str) -> bool:
    """Conservative suffix heuristic; NOT a full public-suffix registrable-domain check."""
    return a == b or a.endswith("." + b) or b.endswith("." + a)


@dataclass(frozen=True)
class SourceCapture:
    source_id: str
    requested_url: str
    final_url: str
    observed_at_utc: str
    claimed_http_status: int
    claimed_content_type: str
    text_utf8: str
    content_sha256: str
    collector_label: str


@dataclass(frozen=True)
class ClaimExcerpt:
    claim_id: str
    source_id: str
    quoted_text: str


def verify_source_text_evidence(
    research: ResearchPackage,
    captures: Sequence[SourceCapture],
    excerpts: Sequence[ClaimExcerpt],
    *,
    now: datetime,
) -> dict:
    """Validate structural text matches ONLY, with no permission side effects.

    A successful structural match does not mean sources are trustworthy, data is
    current, claim semantics are correct, an editor approved facts, or citation
    rights are granted. It cannot unlock the production script or video pipeline.
    """
    if not isinstance(research, ResearchPackage):
        raise EvidenceBlocked("Existing typed ResearchPackage required")
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise EvidenceBlocked("Explicit timezone-aware verifier clock required")
    now_utc = now.astimezone(timezone.utc)
    research.validate(now=now_utc)
    if (not isinstance(captures, (list, tuple))
            or len(captures) != len(research.sources)
            or not isinstance(excerpts, (list, tuple))
            or not 1 <= len(excerpts) <= MAX_EXCERPTS):
        raise EvidenceBlocked("Complete, bounded source snapshots and claim excerpts required")

    cited = {s.source_id: s for s in research.sources}
    matched = {}
    total_bytes = 0
    for cap in captures:
        if not isinstance(cap, SourceCapture) or cap.source_id not in cited or cap.source_id in matched:
            raise EvidenceBlocked("Missing, repeated or unrecognized source observation")
        citation = cited[cap.source_id]
        if (cap.requested_url != citation.url
                or _origin(cap.requested_url) != _origin(cap.final_url)):
            raise EvidenceBlocked("Source observation URL changed origin or citation binding")
        if (type(cap.claimed_http_status) is not int or cap.claimed_http_status != 200
                or cap.claimed_content_type not in ("text/html", "text/plain")
                or not isinstance(cap.collector_label, str)
                or SAFE_FETCHER.fullmatch(cap.collector_label) is None):
            raise EvidenceBlocked("Invalid or unreviewed claimed source capture metadata")
        at = _stamp(cap.observed_at_utc)
        cited_at = _stamp(citation.checked_at_utc)
        if (not timedelta(0) <= now_utc-at <= MAX_SOURCE_AGE
                or at < cited_at - timedelta(minutes=5)):
            raise EvidenceBlocked("Captured source stale, future, or inconsistent with citation check")
        if not isinstance(cap.text_utf8, str):
            raise EvidenceBlocked("Only UTF-8 text source captures accepted")
        data = cap.text_utf8.encode("utf-8")
        total_bytes += len(data)
        if not 1 <= len(data) <= MAX_SNAPSHOT_BYTES or total_bytes > MAX_TOTAL_BYTES:
            raise EvidenceBlocked("Oversized or empty source snapshot")
        if (not isinstance(cap.content_sha256, str)
                or HEX64.fullmatch(cap.content_sha256) is None
                or sha256(data).hexdigest() != cap.content_sha256):
            raise EvidenceBlocked("Source text hash invalid or changed")
        if cap.claimed_content_type == "text/html":
            parser = _VisibleHTML()
            parser.feed(cap.text_utf8)
            visible = " ".join(parser.chunks)
        else:
            visible = cap.text_utf8
        matched[cap.source_id] = {
            "source": citation,
            "normalized_visible": _normalize(visible),
            "hash": cap.content_sha256,
            "host": _https_source(citation.url),
        }
    if set(matched) != set(cited):
        raise EvidenceBlocked("Incomplete source observation set")

    # An official domain and a subdomain of the *same host* are not two
    # independent publishers, even if the package's simple host count is 2.
    official_hosts = {matched[s.source_id]["host"] for s in research.sources if s.kind == "official"}
    independent_hosts = {matched[s.source_id]["host"] for s in research.sources if s.kind == "independent"}
    if any(_related_hosts(a, b) for a in official_hosts for b in independent_hosts):
        raise EvidenceBlocked("Related official and independent hostnames")

    expected_claim_sources = {c.claim_id: set(c.source_ids) for c in research.claims}
    all_pairs = set()
    per_claim = {key: set() for key in expected_claim_sources}
    for ex in excerpts:
        if not isinstance(ex, ClaimExcerpt):
            raise EvidenceBlocked("Typed claim quotation required")
        pair = (ex.claim_id, ex.source_id)
        if pair in all_pairs or ex.source_id not in expected_claim_sources.get(ex.claim_id, set()):
            raise EvidenceBlocked("Duplicate or unsupported claim quotation")
        if not isinstance(ex.quoted_text, str) or not 30 <= len(ex.quoted_text.strip()) <= MAX_EXCERPT_CHARS:
            raise EvidenceBlocked("Source quotation must be meaningful and bounded")
        text = _normalize(ex.quoted_text)
        if text not in matched[ex.source_id]["normalized_visible"]:
            raise EvidenceBlocked("Quoted source passage not present in supplied snapshot")
        all_pairs.add(pair)
        per_claim[ex.claim_id].add(ex.source_id)
    for claim, ids in per_claim.items():
        kinds = {matched[sid]["source"].kind for sid in ids}
        if kinds != {"official", "independent"}:
            raise EvidenceBlocked("Every claim needs official and separately attributed supporting excerpts")

    # No raw pages, full quotations, source titles, private metadata or free text
    # in this summary: hashes and source IDs are deterministic, audit-only.
    return {
        "status": "EXCERPTS_MATCHED_IN_CALLER_SUPPLIED_TEXT_NOT_FACT_CHECKED",
        "episode_id": research.episode_id,
        "research_sha256": sha256(repr(research).encode("utf-8")).hexdigest(),
        "source_hashes": dict(sorted((sid, item["hash"]) for sid, item in matched.items())),
        "claim_ids_with_two_types_of_quotes": sorted(per_claim),
        "quoted_pairs": len(all_pairs),
        "captured_source_count": len(matched),
        "source_contents_exposed": False,
        "claims_independently_verified": False,
        "real_http_capture_verified": False,
        "editorial_approval_verified": False,
        "factually_safe_to_write": False,
        "production_script_authorized": False,
        "media_production_authorized": False,
        "publishing_authorized": False,
        "network_calls": 0,
        "spend_inr": 0,
    }
