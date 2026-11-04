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
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from autopilot.daily_cloud_plan import (
    APPROVED_RESEARCH_ORIGINS,
    PlanError,
    candidate_leads,
)

UTC = dt.timezone.utc
MAX_SOURCES = 6
MAX_BODY_BYTES = 262_144
DEFAULT_TIMEOUT_SECONDS = 10.0
ALLOWED_TYPES = frozenset({
    "text/html", "application/xhtml+xml", "text/plain", "application/xml", "text/xml",
})
PROBE_STATUS = "PUBLIC_SOURCE_METADATA_ONLY_NOT_FACT_VERIFIED"


class EvidenceError(ValueError):
    """Observed bytes fail structural or allowlist safety controls."""


class RejectRedirect(urllib.request.HTTPRedirectHandler):
    """Do not follow any Location header from an untrusted external site."""

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise EvidenceError("Redirects are not automatically trusted")


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
    return url


def choose_independent_sources(scout_report: object, *, limit: int = MAX_SOURCES) -> list[dict]:
    """Prefer one headline per independent publisher, then fill limited capacity."""
    if not 1 <= limit <= MAX_SOURCES:
        raise EvidenceError("Bounded one-to-six source requests only")
    leads = candidate_leads(scout_report, limit=24)
    picked, seen_url, seen_pub = [], set(), set()
    for fresh_publisher_only in (True, False):
        for lead in leads:
            if len(picked) == limit:
                break
            if fresh_publisher_only and lead["publisher"] in seen_pub:
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
) -> dict:
    """Create a content-addressed observation; never record a source fact claim."""
    url = verify_public_source_url(lead.get("url"), lead.get("publisher"))
    if not 1 <= timeout_seconds <= 15:
        raise EvidenceError("Unsafe timeout")
    clock = clock or dt.datetime.now(UTC)
    if clock.tzinfo is None or clock.utcoffset() is None:
        raise EvidenceError("Timezone-aware observation clock required")
    agent = opener or urllib.request.build_opener(RejectRedirect())
    request = urllib.request.Request(
        url, headers={"User-Agent": "FlowMinuteResearchMetadata/1.0", "Accept": "text/html,application/xhtml+xml,text/plain"}
    )
    try:
        with agent.open(request, timeout=timeout_seconds) as response:
            final_url = response.geturl()
            verify_public_source_url(final_url, lead["publisher"])
            if final_url != url:
                raise EvidenceError("Unexpected remote URL change")
            status = response.status
            if status != 200:
                raise EvidenceError("Non-200 source page")
            mime = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if mime not in ALLOWED_TYPES:
                raise EvidenceError("Unexpected binary or unsupported content type")
            body = response.read(MAX_BODY_BYTES + 1)
            if not isinstance(body, bytes) or not 96 <= len(body) <= MAX_BODY_BYTES:
                raise EvidenceError("Source empty or exceeds bounded response limit")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
        raise EvidenceError("Remote fetch failed: " + type(exc).__name__) from exc
    return {
        "source_id": hashlib.sha256(url.encode("utf-8")).hexdigest()[:24],
        "publisher": lead["publisher"],
        "title": lead["title"],
        "source_url": url,
        "observed_final_url": final_url,
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
        "source_text_or_image_stored": False,
        "youtube_release_authorized": False,
    }


def probe_report(scout_report: object, *, clock: dt.datetime | None = None,
                 max_sources: int = MAX_SOURCES, opener=None) -> dict:
    """Errors are counted without exposing page bodies or URL query credentials."""
    clock = clock or dt.datetime.now(UTC)
    selected = choose_independent_sources(scout_report, limit=max_sources)
    successes, failures = [], []
    for lead in selected:
        try:
            successes.append(probe_source(lead, clock=clock, opener=opener))
        except EvidenceError as exc:
            failures.append({
                "publisher": lead["publisher"],
                "source_id": hashlib.sha256(lead["url"].encode()).hexdigest()[:24],
                "error_type": "SOURCE_FETCH_FAILED",
                "error_class": "STRUCTURAL_OR_REMOTE_ERROR",
            })
    return {
        "schema_version": 1,
        "generated_at_utc": clock.astimezone(UTC).isoformat(),
        "status": PROBE_STATUS,
        "source_probes_attempted": len(selected),
        "sources_fetched": len(successes),
        "sources_failed": len(failures),
        "distinct_publishers_fetched": len({s["publisher"] for s in successes}),
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
    args = p.parse_args()
    report_file = Path(args.scout_report)
    if report_file.stat().st_size > 512_000:
        raise PlanError("Unbounded scout input")
    report = json.loads(report_file.read_text(encoding="utf-8"))
    result = probe_report(report, max_sources=args.max_sources)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "attempted": result["source_probes_attempted"],
        "fetched": result["sources_fetched"],
        "failed": result["sources_failed"],
        "publish_authorized": False,
        "factual_claims_verified": 0,
        "billed_api_requests": 0,
    }))


if __name__ == "__main__":
    main()
