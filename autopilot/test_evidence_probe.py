"""Tests for evidence-only public source probing; no live external requests."""
from __future__ import annotations

import datetime as dt
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

from autopilot.evidence_probe import (
    MAX_BODY_BYTES,
    PROBE_STATUS,
    EvidenceError,
    choose_independent_sources,
    probe_report,
    probe_source,
    verify_public_source_url,
)

UTC = dt.timezone.utc
CLOCK = dt.datetime(2026, 11, 4, 5, 10, tzinfo=UTC)
HTML = b"<!doctype html><html><head><title>Original research item</title></head><body>" + b"original research " * 80 + b"</body></html>"


def sample_report():
    return {
        "status": "leads_only_no_publish_authorization",
        "leads": [
            {"publisher": "OpenAI", "title": "AI agent research review and findings",
             "url": "https://openai.com/index/research-paper", "status": "unverified_lead"},
            {"publisher": "OpenAI", "title": "Second OpenAI research report on agents",
             "url": "https://openai.com/index/another-report", "status": "unverified_lead"},
            {"publisher": "The Verge", "title": "Open source data analytics changes this week",
             "url": "https://www.theverge.com/2026/11/3/analytics-news", "status": "unverified_lead"},
            {"publisher": "Google DeepMind", "title": "A technical report on Gemini model evaluation",
             "url": "https://deepmind.google/discover/blog/model-evaluation", "status": "unverified_lead"},
        ],
    }


class FakeResponse:
    def __init__(self, request_url, *, body=HTML, mime="text/html; charset=utf-8",
                 status=200, returned_url=None):
        self.body = io.BytesIO(body)
        self.status = status
        self.headers = {"Content-Type": mime}
        self.url = returned_url or request_url

    def read(self, count):
        return self.body.read(count)

    def geturl(self):
        return self.url

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.body.close()


class FakeOpener:
    def __init__(self, *, payload=HTML, mime="text/html", status=200, returned_url=None, error=None):
        self.payload = payload
        self.mime = mime
        self.status = status
        self.returned_url = returned_url
        self.error = error
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request.full_url, timeout))
        if self.error:
            raise self.error
        return FakeResponse(request.full_url, body=self.payload, mime=self.mime,
                            status=self.status, returned_url=self.returned_url)


class FeedFallbackOpener:
    """Simulate a publisher that denies article requests but serves its own RSS."""
    RSS = (b"<rss version='2.0'><channel><item>"
           b"<title>AI agent research review and findings</title>"
           b"<link>https://openai.com/index/research-paper</link>"
           b"<pubDate>Wed, 04 Nov 2026 02:00:00 GMT</pubDate>"
           b"</item></channel></rss>")

    def __init__(self):
        self.requests = []

    def open(self, request, timeout):
        self.requests.append(request.full_url)
        if request.full_url == "https://openai.com/news/rss.xml":
            return FakeResponse(request.full_url, body=self.RSS, mime="application/rss+xml")
        raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", {}, None)


class EvidenceProbeTests(unittest.TestCase):
    def setUp(self):
        self.lead = sample_report()["leads"][0]

    def test_real_url_allowlist_has_no_wildcards(self):
        self.assertEqual(verify_public_source_url(self.lead["url"], "OpenAI"), self.lead["url"])
        for url in [
            "http://openai.com/index/article",
            "https://evil.openai.com/index/article",
            "https://openai.com.evil.example/a",
            "https://evil.example@openai.com/index/article",
            "https://name:password@openai.com/index/article",
            "https://openai.com:8443/index/article",
            "https://127.0.0.1/index/article",
            "https://openai.com/a#fragment",
            "ftp://openai.com/index/article",
            "https://openai.com/index/bad path",
            "https://openai.com",
            "https://deepmind.google/discover",
        ]:
            with self.subTest(url=url), self.assertRaises(EvidenceError):
                verify_public_source_url(url, "OpenAI")

    def test_publisher_must_match_allowlisted_source_host(self):
        with self.assertRaises(EvidenceError):
            verify_public_source_url(self.lead["url"], "OtherPublisher")

    def test_source_probe_creates_a_real_digest_but_never_factual_approval(self):
        opener = FakeOpener()
        report = probe_source(self.lead, clock=CLOCK, opener=opener)
        self.assertEqual(report["response_sha256"], hashlib.sha256(HTML).hexdigest())
        self.assertEqual(report["observed_at_utc"], "2026-11-04T05:10:00+00:00")
        self.assertEqual(report["response_content_type"], "text/html")
        self.assertEqual(report["status"], "SOURCE_FETCHED_NOT_FACT_CHECKED")
        self.assertEqual(report["http_status"], 200)
        self.assertEqual(report["body_bytes_hashed"], len(HTML))
        self.assertIs(report["facts_verified"], False)
        self.assertIs(report["independent_corroboration_confirmed"], False)
        self.assertIs(report["rights_verified"], False)
        self.assertIs(report["source_text_or_image_stored"], False)
        self.assertIs(report["youtube_release_authorized"], False)
        self.assertNotIn("original research ", json.dumps(report))
        self.assertEqual(opener.requests, [(self.lead["url"], 10.0)])

    def test_response_body_never_persisted(self):
        result = probe_report(sample_report(), opener=FakeOpener(), clock=CLOCK, max_sources=3)
        data = json.dumps(result)
        self.assertNotIn("original research ", data)
        self.assertNotIn("<html>", data)
        self.assertNotIn("SOURCE_VERIFIED_FACT", data)
        self.assertFalse(result["semantic_corroboration_performed"])

    def test_three_distinct_publishers_preferred_for_audit(self):
        selected = choose_independent_sources(sample_report(), limit=3)
        self.assertEqual({x["publisher"] for x in selected}, {"OpenAI", "The Verge", "Google DeepMind"})
        self.assertEqual(selected[0]["publisher"], "OpenAI")

    def test_max_six_and_invalid_limits_fail_closed(self):
        for count in (0, -1, 7, 300):
            with self.subTest(count=count), self.assertRaises(EvidenceError):
                choose_independent_sources(sample_report(), limit=count)

    def test_redirect_to_any_other_url_refused_even_same_domain(self):
        opener = FakeOpener(returned_url="https://openai.com/index/other")
        with self.assertRaises(EvidenceError):
            probe_source(self.lead, opener=opener)

    def test_non_200_http_does_not_count(self):
        opener = FakeOpener(status=403)
        with self.assertRaises(EvidenceError):
            probe_source(self.lead, opener=opener)

    def test_binary_mime_blocked(self):
        for mime in ("image/png", "application/octet-stream", "application/pdf"):
            with self.subTest(mime=mime), self.assertRaises(EvidenceError):
                probe_source(self.lead, opener=FakeOpener(mime=mime))

    def test_empty_or_large_payload_is_blocked(self):
        for payload in (b"", b"X" * 95, b"X" * (MAX_BODY_BYTES + 1)):
            with self.subTest(length=len(payload)), self.assertRaises(EvidenceError):
                probe_source(self.lead, opener=FakeOpener(payload=payload))

    def test_timeout_and_network_error_are_captured_safely(self):
        opener = FakeOpener(error=urllib.error.URLError("network secret body suppressed"))
        result = probe_report(sample_report(), clock=CLOCK, opener=opener, max_sources=3)
        self.assertEqual(result["sources_failed"], 3)
        self.assertEqual(result["sources_fetched"], 0)
        self.assertEqual(result["claims_verified"], 0)
        self.assertNotIn("network secret", json.dumps(result))

    def test_response_with_naive_clock_is_rejected(self):
        with self.assertRaises(EvidenceError):
            probe_source(self.lead, clock=dt.datetime(2026, 11, 4), opener=FakeOpener())

    def test_unsupported_scout_state_does_not_cause_network_fetch(self):
        data = sample_report()
        data["status"] = "release_ready"
        opener = FakeOpener()
        with self.assertRaises(ValueError):
            probe_report(data, opener=opener)
        self.assertEqual(opener.requests, [])

    def test_rss_fallback_observes_real_entry_but_not_article_or_fact(self):
        opener = FeedFallbackOpener()
        report = probe_report({"status": "leads_only_no_publish_authorization",
                               "leads": [self.lead]}, clock=CLOCK, opener=opener, max_sources=1)
        self.assertEqual(report["sources_fetched"], 0)
        self.assertEqual(report["feed_entries_observed_only"], 1)
        self.assertEqual(report["sources_observed_total"], 1)
        self.assertEqual(report["sources_failed"], 0)
        self.assertEqual(opener.requests,
                         [self.lead["url"], "https://openai.com/news/rss.xml"])
        observed = report["sources"][0]
        self.assertEqual(observed["status"], "RSS_ENTRY_ONLY_ARTICLE_NOT_FETCHED")
        self.assertFalse(observed["source_article_fetched"])
        self.assertFalse(observed["facts_verified"])
        self.assertEqual(len(observed["feed_entry_sha256"]), 64)
        self.assertEqual(observed["response_sha256"], hashlib.sha256(opener.RSS).hexdigest())
        self.assertNotIn("pubDate", json.dumps(observed))

    def test_rss_fallback_must_match_actual_publisher_title_and_url(self):
        opener = FeedFallbackOpener()
        forged = dict(self.lead, title="A made up article headline not in the real RSS feed")
        result = probe_report({"status": "leads_only_no_publish_authorization",
                               "leads": [forged]}, clock=CLOCK, opener=opener, max_sources=1)
        self.assertEqual(result["sources_observed_total"], 0)
        self.assertEqual(result["sources_failed"], 1)
        self.assertFalse(result["semantic_corroboration_performed"])

    def test_fetched_source_alone_never_grants_approval(self):
        result = probe_report(sample_report(), clock=CLOCK, opener=FakeOpener(), max_sources=3)
        self.assertEqual(result["status"], PROBE_STATUS)
        self.assertEqual(result["sources_fetched"], 3)
        self.assertEqual(result["distinct_publishers_fetched"], 3)
        self.assertEqual(result["claims_verified"], 0)
        self.assertEqual(result["scripts_generated"], 0)
        self.assertIs(result["audio_or_video_generated"], False)
        self.assertIs(result["youtube_upload_enabled"], False)
        self.assertIs(result["youtube_schedule_enabled"], False)
        self.assertIs(result["production_credentials_used"], False)
        self.assertEqual(result["billed_provider_calls"], 0)

    def test_cli_read_only_no_source_file_persistence(self):
        # No real URLs or credential calls: the bounded empty report must work entirely offline.
        with tempfile.TemporaryDirectory() as path:
            directory = Path(path)
            scout_file = directory / "scout.json"
            result_file = directory / "evidence.json"
            scout_file.write_text(
                json.dumps({"status": "leads_only_no_publish_authorization", "leads": []}),
                encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, "-m", "autopilot.evidence_probe",
                 "--scout-report", str(scout_file), "--output", str(result_file),
                 "--max-sources", "3"], capture_output=True, text=True, timeout=20)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            saved = json.loads(result_file.read_text(encoding="utf-8"))
            self.assertEqual(saved["sources_fetched"], 0)
            self.assertEqual(saved["status"], PROBE_STATUS)
            self.assertIs(saved["youtube_upload_enabled"], False)


if __name__ == "__main__":
    unittest.main()
