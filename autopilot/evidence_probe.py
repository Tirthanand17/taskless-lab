"""Unprivileged source-observation agent for FlowMinute Branch 2.

Reads bounded PUBLIC web pages selected by the allowlisted RSS scout. A successful
fetch proves only HTTP bytes were observed; it CANNOT validate any factual claim,
script, rights, media or permission to publish. No laptop, secrets, API or billing.

Do not change to follow arbitrary redirects or write full copyrighted page bodies
into public GitHub Actions logs/artifacts.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import time
import xml.etree.ElementTree as ET
import urllib.error
import urllib.request
from urllib.parse import urljoin
from pathlib import Path
from urllib.parse import urlsplit

from autopilot.scout import FEEDS, _article_link, _find_text
from autopilot.public_article_passages import (
    PASSAGE_STATUS, extract_literal_passages,
)
from autopilot.daily_cloud_plan import (
    APPROVED_RESEARCH_ORIGINS,
    PlanError,
    candidate_leads,
)

UTC = dt.timezone.utc
MAX_SOURCES = 6
MAX_BODY_BYTES = 1_048_576
DEFAULT_TIMEOUT_SECONDS = 10.0
ALLOWED_TYPES = frozenset({
    "text/html", "application/xhtml+xml", "text/plain", "application/xml", "text/xml",
})
PROBE_STATUS = "PUBLIC_SOURCE_METADATA_ONLY_NOT_FACT_VERIFIED"


class EvidenceError(ValueError):
    """Observed bytes fail structural or allowlist safety controls."""


class RejectRedirect(urllib.request.HTTPRedirectHandler):
    """Do not follow redirects from exact publisher RSS feed requests."""

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise EvidenceError("RSS feed redirect not approved")


MAX_ARTICLE_REDIRECTS = 2
SAFE_FETCH_FAILURES = frozenset((
    "HTTP_ACCESS_DENIED", "HTTP_RATE_LIMITED", "HTTP_NOT_FOUND",
    "HTTP_UNAVAILABLE", "HTTP_OTHER", "TRANSPORT_UNAVAILABLE",
    "REDIRECT_REJECTED", "UNEXPECTED_FINAL_URL",
    "UNEXPECTED_HTTP_STATUS", "UNSUPPORTED_CONTENT_TYPE",
    "ARTICLE_TOO_SMALL", "ARTICLE_TOO_LARGE", "BOT_CHALLENGE_PAGE",
    "SOURCE_STRUCTURAL_REJECTED",
))


class ArticleFetchRefused(EvidenceError):
    """Only a constant, non-sensitive diagnostic category is ever retained."""

    def __init__(self, category: str):
        if category not in SAFE_FETCH_FAILURES:
            raise ValueError("Unrecognized bounded public fetch error class")
        self.category = category
        super().__init__(category)


class PublisherOnlyArticleRedirect(urllib.request.HTTPRedirectHandler):
    """Allow at most two GET redirects to publisher's exact approved HTTPS hosts.

    Never send a request to a redirect Location until the final URL is checked
    against the same original publisher origin allowlist. No arbitrary hosts,
    IP addresses, credentials, non-standard ports, scripts or loops.
    """

    def __init__(self, publisher: str, first_url: str):
        self.publisher = publisher
        self.first_url = verify_public_source_url(first_url, publisher)
        self.targets: list[str] = []

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        if request.get_method() != "GET" or code not in (301, 302, 303, 307, 308):
            raise ArticleFetchRefused("REDIRECT_REJECTED")
        try:
            target = verify_public_source_url(urljoin(request.full_url, newurl), self.publisher)
        except (EvidenceError, ValueError):
            raise ArticleFetchRefused("REDIRECT_REJECTED") from None
        if (len(self.targets) >= MAX_ARTICLE_REDIRECTS
            or target in (self.first_url, *self.targets)):
            raise ArticleFetchRefused("REDIRECT_REJECTED")
        next_request = super().redirect_request(
            request, fp, code, msg, headers, target)
        if next_request is None:
            raise ArticleFetchRefused("REDIRECT_REJECTED")
        self.targets.append(target)
        return next_request


def _fetch_failure_category(exc: EvidenceError) -> str:
    return exc.category if isinstance(exc, ArticleFetchRefused) else "SOURCE_STRUCTURAL_REJECTED"


def verify_public_source_url(url: object, publisher: str) -> str:
    """Exact allowlisted HTTPS origins. No domains inferred from source titles."""
    if not isinstance(url, str) or not 12 <= len(url) <= 512:
        raise EvidenceError("Invalid source URL length")
    if publisher not in APPROVED_RESEARCH_ORIGINS:
        raise EvidenceError("Unrecognized research publisher")
    try:
        p = urlsplit(url)
        port = p.port
    except ValueError as exc:
        raise EvidenceError("Malformed source URL") from exc
    if (p.scheme != "https" or not p.hostname
        or p.hostname.lower() not in APPROVED_RESEARCH_ORIGINS[publisher]
        or p.username is not None or p.password is not None
        or port not in (None, 443)
        or p.fragment or any(ord(c) <= 32 for c in url)
        or not p.path.startswith("/")):
        raise EvidenceError("Only approved public HTTPS source origins are allowed")
    # Never mistake an RSS feed, bulk PDF or arbitrary search query for a
    # directly observed primary abstract/article page.
    if publisher == "arXiv AI" and (
        re.fullmatch(r"/abs/[0-9]{4}\.[0-9]{4,5}(?:v[1-9][0-9]*)?",
                     p.path) is None or p.query):
        raise EvidenceError("Only exact arXiv abstract article URLs allowed")
    return url


def choose_independent_sources(scout_report: object, *, limit: int = MAX_SOURCES) -> list[dict]:
    """Prefer one headline per independent publisher, then fill limited capacity."""
    if not 1 <= limit <= MAX_SOURCES:
        raise EvidenceError("Bounded one-to-six source requests only")
    leads = candidate_leads(scout_report, limit=24)
    # Include at most one primary arXiv paper; never flood the archive with
    # dozens of page requests because its daily RSS contains many papers.
    # Prefer first-party preprint identity to an unverified news headline.
    leads.sort(key=lambda x: x["publisher"] != "arXiv AI")
    picked, seen_url, seen_pub = [], set(), set()
    for fresh_publisher_only in (True, False):
        for lead in leads:
            if len(picked) == limit:
                break
            if (lead["publisher"] == "arXiv AI" and lead["publisher"] in seen_pub
                or fresh_publisher_only and lead["publisher"] in seen_pub):
                continue
            try:
                verify_public_source_url(lead["url"], lead["publisher"])
            except EvidenceError:
                continue
            if lead["url"] in seen_url:
                continue
            picked.append(lead)
            seen_url.add(lead["url"])
            seen_pub.add(lead["publisher"])
    return picked


def probe_source(
    lead: dict,
    *,
    clock: dt.datetime | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    opener=None,
    ephemeral_passage_sink: dict | None = None,
) -> dict:
    """Create a content-addressed observation; never record a source fact claim."""
    url = verify_public_source_url(lead.get("url"), lead.get("publisher"))
    if not 1 <= timeout_seconds <= 15:
        raise EvidenceError("Unsafe timeout")
    clock = clock or dt.datetime.now(UTC)
    if clock.tzinfo is None or clock.utcoffset() is None:
        raise EvidenceError("Timezone-aware observation clock required")
    safe_redirects = PublisherOnlyArticleRedirect(lead["publisher"], url)
    # A fake opener in unit tests cannot claim it was allowed to redirect.
    # Production opener uses ONLY the bounded exact-publisher redirect handler.
    agent = opener if opener is not None else urllib.request.build_opener(safe_redirects)
    request = urllib.request.Request(
        url, headers={"User-Agent": "FlowMinuteResearchMetadata/1.0",
                      "Accept": "text/html,application/xhtml+xml,text/plain"}
    )
    try:
        with agent.open(request, timeout=timeout_seconds) as response:
            final_url = response.geturl()
            try:
                verify_public_source_url(final_url, lead["publisher"])
            except EvidenceError:
                raise ArticleFetchRefused("UNEXPECTED_FINAL_URL") from None
            expected = safe_redirects.targets[-1] if safe_redirects.targets else url
            if final_url != expected:
                raise ArticleFetchRefused("UNEXPECTED_FINAL_URL")
            status = response.status
            if status != 200:
                raise ArticleFetchRefused("UNEXPECTED_HTTP_STATUS")
            mime = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if mime not in ALLOWED_TYPES:
                raise ArticleFetchRefused("UNSUPPORTED_CONTENT_TYPE")
            body = response.read(MAX_BODY_BYTES + 1)
            if not isinstance(body, bytes) or len(body) < 96:
                raise ArticleFetchRefused("ARTICLE_TOO_SMALL")
            if len(body) > MAX_BODY_BYTES:
                raise ArticleFetchRefused("ARTICLE_TOO_LARGE")
            # A 200 OK Cloudflare/captcha interstitial is NOT a fetched article.
            # Only inspect ephemeral original bytes; never retain page bodies.
            if mime in ("text/html", "application/xhtml+xml"):
                opening = body[:16_384].lower()
                if (b"<title>just a moment" in opening
                    or b"<title>attention required! | cloudflare" in opening
                    or b"cf-challenge-running" in opening
                    or b"verify you are human" in opening):
                    raise ArticleFetchRefused("BOT_CHALLENGE_PAGE")
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            category = "HTTP_ACCESS_DENIED"
        elif exc.code == 429:
            category = "HTTP_RATE_LIMITED"
        elif exc.code in (404, 410):
            category = "HTTP_NOT_FOUND"
        elif 500 <= exc.code <= 599:
            category = "HTTP_UNAVAILABLE"
        else:
            category = "HTTP_OTHER"
        raise ArticleFetchRefused(category) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ArticleFetchRefused("TRANSPORT_UNAVAILABLE") from None
    source_id = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
    # Literal snippets are ONLY held inside an explicitly provided ephemeral
    # research sink; they NEVER enter observation JSON, source receipts,
    # workflow summaries or any public Actions artifact.
    if ephemeral_passage_sink is not None:
        if type(ephemeral_passage_sink) is not dict:
            raise EvidenceError("Passage collector must be an ephemeral dict")
        ephemeral_passage_sink[source_id] = {
            "source_id": source_id,
            "observed_article_sha256": hashlib.sha256(body).hexdigest(),
            "status": PASSAGE_STATUS,
            "passages": extract_literal_passages(body, mime),
            "rights_approved": False,
            "facts_verified": False,
        }
    return {
        "source_id": source_id,
        "publisher": lead["publisher"],
        "title": lead["title"],
        "source_url": url,
        "observed_final_url": final_url,
        "approved_same_publisher_redirect_hops": len(safe_redirects.targets),
        "approved_same_publisher_redirect": bool(safe_redirects.targets),
        "observed_at_utc": clock.astimezone(UTC).isoformat(),
        "http_status": status,
        "response_content_type": mime,
        "body_bytes_hashed": len(body),
        "response_sha256": hashlib.sha256(body).hexdigest(),
        "status": "SOURCE_FETCHED_NOT_FACT_CHECKED",
        "claim_level_evidence_extracted": False,
        "independent_corroboration_confirmed": False,
        "facts_verified": False,
        "rights_verified": False,
        # Full publisher article bodies/images are never retained. The opt-in
        # sink holds at most two tiny literal excerpts only on the runner.
        "source_text_or_image_stored": False,
        "literal_short_excerpts_temporarily_held": ephemeral_passage_sink is not None,
        "youtube_release_authorized": False,
    }



def verified_pinned_feed_url(publisher: str) -> str:
    """The feed is a fixed code-reviewed config URL, never an RSS lead URL."""
    feed=dict(FEEDS).get(publisher)
    if not feed:
        raise EvidenceError("No official pinned RSS feed for publisher")
    p=urlsplit(feed)
    if (p.scheme != "https" or p.username is not None or p.password is not None
        or p.port not in (None,443) or p.fragment or not p.path.startswith("/")
        or not p.hostname):
        raise EvidenceError("Malformed exact-source RSS feed configuration")
    # Only article abstract origins qualify as article targets. Official arXiv
    # RSS must remain on its separate rss.arxiv.org feed hostname.
    if publisher == "arXiv AI" and feed != "https://rss.arxiv.org/rss/cs.AI":
        raise EvidenceError("Unapproved archive feed")
    return feed


def probe_feed_entry(lead: dict, *, clock: dt.datetime | None = None,
                     timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
                     opener=None) -> dict:
    """Evidence fallback: observe an existing RSS headline, NOT article content or truth."""
    url = verify_public_source_url(lead.get("url"), lead.get("publisher"))
    feed = verified_pinned_feed_url(lead["publisher"])
    if not 1 <= timeout_seconds <= 15:
        raise EvidenceError("Unsafe timeout")
    clock = clock or dt.datetime.now(UTC)
    if clock.tzinfo is None or clock.utcoffset() is None:
        raise EvidenceError("Timezone-aware observation clock required")
    agent = opener or urllib.request.build_opener(RejectRedirect())
    request = urllib.request.Request(
        feed, headers={"User-Agent": "FlowMinutePublicResearch/1.0", "Accept": "application/rss+xml,application/atom+xml,application/xml,text/xml,*/*"}
    )
    try:
        with agent.open(request, timeout=timeout_seconds) as response:
            if response.status != 200 or response.geturl() != feed:
                raise EvidenceError("Feed URL redirected or returned non-200 response")
            mime = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if mime not in ("application/rss+xml", "application/atom+xml",
                            "application/xml", "text/xml", "text/plain", "text/html"):
                raise EvidenceError("Invalid feed content type")
            body = response.read(1_048_577)
            if not 96 <= len(body) <= 1_048_576:
                raise EvidenceError("Unbounded RSS feed body")
        root = ET.fromstring(body)
        items = (n for n in root.iter() if n.tag.split("}")[-1] in ("entry", "item"))
        selected = next((item for item in items if
            _article_link(item) == url and
            " ".join(_find_text(item, ("title",)).split())[:200] == lead["title"]), None)
        if selected is None:
            raise EvidenceError("Article headline not found in observed publisher feed")
    except (urllib.error.HTTPError, urllib.error.URLError,
            TimeoutError, OSError, ET.ParseError) as exc:
        raise EvidenceError("Public RSS entry unavailable: " + type(exc).__name__) from exc
    return {
        "source_id": hashlib.sha256(url.encode("utf-8")).hexdigest()[:24],
        "publisher": lead["publisher"],
        "title": lead["title"],
        "source_url": url,
        "observed_final_url": feed,
        "observed_at_utc": clock.astimezone(UTC).isoformat(),
        "http_status": 200,
        "response_content_type": mime,
        "body_bytes_hashed": len(body),
        "response_sha256": hashlib.sha256(body).hexdigest(),
        "feed_entry_sha256": hashlib.sha256(ET.tostring(selected, encoding="utf-8")).hexdigest(),
        "status": "RSS_ENTRY_ONLY_ARTICLE_NOT_FETCHED",
        "source_article_fetched": False,
        "claim_level_evidence_extracted": False,
        "independent_corroboration_confirmed": False,
        "facts_verified": False,
        "rights_verified": False,
        "source_text_or_image_stored": False,
        "youtube_release_authorized": False,
    }


def probe_report(scout_report: object, *, clock: dt.datetime | None = None,
                 max_sources: int = MAX_SOURCES, opener=None,
                 ephemeral_passage_sink: dict | None = None) -> dict:
    """Errors are counted without exposing page bodies or URL query credentials."""
    clock = clock or dt.datetime.now(UTC)
    selected = choose_independent_sources(scout_report, limit=max_sources)
    successes, failures = [], []
    direct_failures = {}
    for lead in selected:
        try:
            successes.append(probe_source(
                lead, clock=clock, opener=opener,
                ephemeral_passage_sink=ephemeral_passage_sink))
        except EvidenceError as exc:
            # B4d3 diagnosis is deliberately category-only. A publisher's
            # server error body, token-bearing URL or article text is NEVER
            # copied into logs or the final public research receipt.
            category = _fetch_failure_category(exc)
            direct_failures[category] = direct_failures.get(category, 0) + 1
            # The original publisher's RSS entry is useful provenance when
            # a page blocks bots. This is NOT independent factual support.
            # Archive API policy: <=1 request / three seconds, single runner
            # connection. No repeat/retry storm if a paper's abstract fails.
            if lead["publisher"] == "arXiv AI" and opener is None:
                time.sleep(3.2)
            try:
                fallback = probe_feed_entry(lead, clock=clock, opener=opener)
                fallback["direct_article_failure_class"] = category
                successes.append(fallback)
            except EvidenceError:
                failures.append({
                    "publisher": lead["publisher"],
                    "direct_article_failure_class": category,
                    "source_id": hashlib.sha256(lead["url"].encode()).hexdigest()[:24],
                    "error_type": "SOURCE_AND_FEED_UNAVAILABLE",
                    "error_class": "STRUCTURAL_OR_REMOTE_ERROR",
                })
    return {
        "schema_version": 1,
        "generated_at_utc": clock.astimezone(UTC).isoformat(),
        "status": PROBE_STATUS,
        "source_probes_attempted": len(selected),
        "sources_fetched": sum(x["status"] == "SOURCE_FETCHED_NOT_FACT_CHECKED" for x in successes),
        "feed_entries_observed_only": sum(x["status"] == "RSS_ENTRY_ONLY_ARTICLE_NOT_FETCHED" for x in successes),
        "sources_observed_total": len(successes),
        "sources_failed": len(failures),
        "distinct_publishers_fetched": len({s["publisher"] for s in successes}),
        "direct_article_fetch_failure_counts": {
            key: direct_failures[key] for key in sorted(direct_failures)},
        "source_articles_with_bounded_publisher_redirect": sum(
            x.get("approved_same_publisher_redirect") is True for x in successes),
        "sources": successes,
        "failures": failures,
        "claims_verified": 0,
        "semantic_corroboration_performed": False,
        "source_body_persisted": False,
        "scripts_generated": 0,
        "audio_or_video_generated": False,
        "youtube_upload_enabled": False,
        "youtube_schedule_enabled": False,
        "production_credentials_used": False,
        "billed_provider_calls": 0,
        "next_gate": "Independent claim-by-claim corroboration; observed HTTP bytes do not prove a factual assertion",
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Read-only bounded public-source observations; no claims or uploads")
    p.add_argument("--scout-report", required=True)
    p.add_argument("--output", default="out/source-evidence-unverified.json")
    p.add_argument("--max-sources", type=int, default=3)
    p.add_argument("--ephemeral-passages",default=None)
    args = p.parse_args()
    report_file = Path(args.scout_report)
    if report_file.stat().st_size > 512_000:
        raise PlanError("Unbounded scout input")
    report = json.loads(report_file.read_text(encoding="utf-8"))
    passage_sink = {} if args.ephemeral_passages is not None else None
    # Refuse to accidentally write copyrighted excerpts into an artifact
    # name that a future workflow could confuse with public receipts.
    private_output = Path(args.ephemeral_passages) if args.ephemeral_passages else None
    if private_output is not None:
        if (private_output.parent.name != "out"
            or not private_output.name.startswith("flowminute-ephemeral-")
            or private_output.suffix != ".json"
            or private_output.is_symlink() or private_output.exists()):
            raise EvidenceError("Only new, ephemeral out/ research files may hold excerpts")
    result = probe_report(report, max_sources=args.max_sources,
                          ephemeral_passage_sink=passage_sink)
    if private_output is not None:
        limited = {
            "status": PASSAGE_STATUS,
            "source_observation_generated_at_utc": result["generated_at_utc"],
            "sources": list(passage_sink.values()),
            "not_a_fact_check": True,
            "not_a_rights_clearance": True,
            "not_for_public_artifacts": True,
        }
        payload = json.dumps(limited,ensure_ascii=True,
                             separators=(",",":"),allow_nan=False)
        if len(payload.encode("utf8")) > 16000:
            raise EvidenceError("Unbounded ephemeral passages")
        private_output.parent.mkdir(parents=True, exist_ok=True)
        private_output.write_text(payload+"\n",encoding="utf8")
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "attempted": result["source_probes_attempted"],
        "direct_page_fetched": result["sources_fetched"],
        "feed_only_observed": result["feed_entries_observed_only"],
        "direct_fetch_failure_classes": result["direct_article_fetch_failure_counts"],
        "same_publisher_redirects": result["source_articles_with_bounded_publisher_redirect"],
        "failed": result["sources_failed"],
        "publish_authorized": False,
        "factual_claims_verified": 0,
        "billed_api_requests": 0,
    }))


if __name__ == "__main__":
    main()
