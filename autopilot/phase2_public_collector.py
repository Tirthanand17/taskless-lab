"""Phase 2R1: tightly allowlisted public HTTPS source capture (opt-in only).

A first narrow, *real* public-source fetch path for the existing CSV demo.
No new account, login, OAuth, cookies, proxy, paid API, GitHub schedule,
YouTube, Cloudflare, laptop control, or publishing. Network OFF by default.

Authenticated TLS and robots compliance do not mean any claim is true or
independently reviewed, and this module never grants script/video clearance.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import ssl
from typing import Callable
from urllib import robotparser
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import (
    HTTPSHandler, HTTPRedirectHandler, ProxyHandler, Request, build_opener,
)

from .agent_org import WorkflowError
from .phase2_pipeline import ResearchPackage, _stamp
from .phase2_source_evidence import SourceCapture, MAX_SNAPSHOT_BYTES

AGENT = "FlowMinutePublicResearch/1.0"
TIMEOUT_S = 6
PAGE_MAX_BYTES = MAX_SNAPSHOT_BYTES
ROBOTS_MAX_BYTES = 32768
# Explicit narrow public-access allowlist; no arbitrary websites/URLs.
_ALLOWED = {
    "src_python_docs": "https://docs.python.org/3/library/csv.html",
    "src_independent_csv": "https://realpython.com/python-csv/",
}
_ALLOWED_ROBOTS = frozenset(
    "https://" + urlsplit(url).hostname + "/robots.txt"
    for url in _ALLOWED.values()
)
_ALLOWED_ENDPOINTS = frozenset(_ALLOWED.values()) | _ALLOWED_ROBOTS


class CaptureDenied(WorkflowError):
    """Public fetch policy, robots or transport failed closed."""


@dataclass(frozen=True)
class PublicResponse:
    status: int
    final_url: str
    content_type: str
    data: bytes
    content_encoding: str = "identity"


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _retrieve_public_https(url: str, *, max_bytes: int) -> PublicResponse:
    """HTTPS with OS trust, no cookies, proxies, custom headers or redirects.

    May only be used for URLs already checked against the exact allowlist,
    including the corresponding /robots.txt file. No retry or auth fallback.
    """
    if not isinstance(url, str) or url not in _ALLOWED_ENDPOINTS:
        raise CaptureDenied("Exact allowlisted public HTTPS endpoint required")
    opener = build_opener(
        ProxyHandler({}), HTTPSHandler(context=ssl.create_default_context()),
        _NoRedirect(),
    )
    req = Request(url, headers={
        "User-Agent": AGENT,
        "Accept": "text/html,text/plain;q=0.9,*/*;q=0.1",
        "Accept-Encoding": "identity",
    }, method="GET")
    try:
        with opener.open(req, timeout=TIMEOUT_S) as response:
            data = response.read(max_bytes + 1)
            if len(data) > max_bytes:
                raise CaptureDenied("Public response larger than bounded byte cap")
            return PublicResponse(
                status=response.status,
                final_url=response.geturl(),
                content_type=response.headers.get("Content-Type", ""),
                content_encoding=response.headers.get("Content-Encoding", "identity"),
                data=data,
            )
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise CaptureDenied("Public source unavailable or access denied; no retries") from exc


def _robots_url(url: str) -> str:
    parsed = urlsplit(url)
    return f"https://{parsed.hostname}/robots.txt"


def _validate_response(response: PublicResponse, *, exact_url: str,
                       types: frozenset[str], cap: int) -> tuple[str, str]:
    """Enforce a non-redirected, strictly bounded text-only response."""
    if not isinstance(response, PublicResponse):
        raise CaptureDenied("Unexpected public HTTPS response type")
    if (type(response.status) is not int or response.status != 200
            or response.final_url != exact_url
            or response.content_encoding.lower() != "identity"
            or not isinstance(response.data, bytes)
            or not 1 <= len(response.data) <= cap
            or not isinstance(response.content_type, str)):
        raise CaptureDenied("Redirect, error, encoding or size policy violation")
    kind = response.content_type.split(";", 1)[0].lower().strip()
    if kind not in types:
        raise CaptureDenied("Non-text or unapproved content type")
    try:
        text = response.data.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise CaptureDenied("UTF-8 public source required") from exc
    return kind, text


def collect_csv_research_sources(
    research: ResearchPackage,
    *,
    now: datetime,
    allow_live_network: bool = False,
    _test_transport: Callable[..., PublicResponse] | None = None,
) -> tuple[SourceCapture, ...]:
    """Collect two ONLY allowlisted public CSV teaching sources, not generic web.

    The actual network needs opt-in allow_live_network=True. Unit fixtures may
    use injected _test_transport only when live network is FALSE. Robots and page
    are fetched once each, no retries, following external links or pagination.
    HTTPS cert checking is delegated to the standard trusted SSL implementation.

    Network transport is NOT evidence of true claim support or publisher rights;
    captures remain explicitly CLAIMED to the separate source-evidence checker.
    """
    if not isinstance(research, ResearchPackage):
        raise CaptureDenied("Typed research package required")
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise CaptureDenied("Timezone aware clock required")
    if allow_live_network is not True and _test_transport is None:
        raise CaptureDenied("Live public HTTP collection disabled by default")
    if allow_live_network is True and _test_transport is not None:
        raise CaptureDenied("Test transport cannot impersonate real network")
    now_utc = now.astimezone(timezone.utc)
    try:
        research.validate(now=now_utc)
    except WorkflowError as exc:
        raise CaptureDenied("Invalid or incomplete typed public research package") from exc
    sources = {s.source_id: s for s in research.sources}
    if set(sources) != set(_ALLOWED):
        raise CaptureDenied("Only a two-site allowlisted CSV research example is enabled")
    for sid, url in _ALLOWED.items():
        if sources[sid].url != url:
            raise CaptureDenied("Unapproved public source URL")

    transport = _retrieve_public_https if allow_live_network else _test_transport
    captures = []
    for sid in sorted(_ALLOWED):
        url = _ALLOWED[sid]
        robots_url = _robots_url(url)
        robots_response = transport(robots_url, max_bytes=ROBOTS_MAX_BYTES)
        _, robots_text = _validate_response(
            robots_response, exact_url=robots_url,
            types=frozenset(("text/plain",)), cap=ROBOTS_MAX_BYTES)
        rule = robotparser.RobotFileParser()
        rule.set_url(robots_url)
        rule.parse(robots_text.splitlines())
        if not any(line.strip().lower().startswith("user-agent:")
                   for line in robots_text.splitlines()):
            raise CaptureDenied("Robots rules missing; not permission to crawl")
        if not rule.can_fetch(AGENT, url):
            raise CaptureDenied("Robots policy does not permit public collection")
        # This one-shot collector has no durable cross-run throttling or clock
        # enforcement; do not silently ignore published pacing directives.
        if rule.crawl_delay(AGENT) is not None or rule.request_rate(AGENT) is not None:
            raise CaptureDenied("Robots crawl pacing requires an approved rate scheduler")
        page = transport(url, max_bytes=PAGE_MAX_BYTES)
        content_type, body = _validate_response(
            page, exact_url=url,
            types=frozenset(("text/html", "text/plain")), cap=PAGE_MAX_BYTES)
        if "\x00" in body:
            raise CaptureDenied("Embedded NUL in public text source")
        # Use a single UTC observation per collection call, not a caller-told
        # timestamp from a fetched page. This is still not a signed attestation.
        stamp = now_utc.isoformat()
        # validate that caller's citation time is consistent, enforced again in
        # phase2_source_evidence at subsequent staged review.
        if _stamp(sources[sid].checked_at_utc) > now_utc:
            raise CaptureDenied("Future-dated source check")
        captures.append(SourceCapture(
            source_id=sid, requested_url=url, final_url=url,
            observed_at_utc=stamp, claimed_http_status=200,
            claimed_content_type=content_type, text_utf8=body,
            content_sha256=sha256(body.encode("utf-8")).hexdigest(),
            collector_label=("public_https_collector" if allow_live_network
                             else "offline_fixture_collector"),
        ))
    return tuple(captures)


def public_capture_summary(captures: tuple[SourceCapture, ...]) -> dict:
    """Safe text-free diagnostics; not independent source verification."""
    if not isinstance(captures, tuple) or len(captures) != 2:
        raise CaptureDenied("Two captured sources required")
    source_ids = []
    for item in captures:
        if (not isinstance(item, SourceCapture)
                or not isinstance(item.source_id, str)
                or item.source_id not in _ALLOWED
                or item.requested_url != _ALLOWED[item.source_id]
                or item.final_url != item.requested_url
                or type(item.claimed_http_status) is not int
                or item.claimed_http_status != 200
                or item.claimed_content_type not in ("text/plain", "text/html")
                or item.collector_label not in ("offline_fixture_collector",
                                                "public_https_collector")
                or not isinstance(item.text_utf8, str)
                or not isinstance(item.content_sha256, str)):
            raise CaptureDenied("Malformed or out-of-scope capture summary input")
        try:
            serialized = item.text_utf8.encode("utf-8")
        except UnicodeError as exc:
            raise CaptureDenied("Invalid capture text") from exc
        if (not 1 <= len(serialized) <= PAGE_MAX_BYTES
                or sha256(serialized).hexdigest() != item.content_sha256):
            raise CaptureDenied("Capture summary checksum invalid or oversized")
        source_ids.append(item.source_id)
    if set(source_ids) != set(_ALLOWED):
        raise CaptureDenied("Expected exactly one record per allowed source")
    return {
        "status": "SOURCE_CAPTURES_UNTRUSTED_UNTIL_INDEPENDENT_PROVENANCE_REVIEW",
        "source_hashes": {s.source_id: s.content_sha256 for s in captures},
        "source_count": len(captures),
        "simulation_present": any(s.collector_label == "offline_fixture_collector"
                                  for s in captures),
        "real_source_provenance_verified": False,
        "fact_verification_completed": False,
        "public_source_licensing_verified": False,
        "claim_quotation_review_completed": False,
        "script_authorized": False, "publishing_authorized": False,
        "zero_paid_providers": True,
    }
