"""Offline transport-simulation tests: absolutely no real HTTP or account calls."""
from dataclasses import replace
from datetime import timedelta
import unittest

from autopilot.test_phase2_pipeline import fixtures, NOW
from autopilot.test_phase2_source_evidence import OFFICIAL_QUOTE, INDEPENDENT_QUOTE
from autopilot.phase2_public_collector import (
    CaptureDenied, PublicResponse, collect_csv_research_sources,
    public_capture_summary, AGENT, _ALLOWED, _retrieve_public_https,
)
from autopilot.phase2_source_evidence import ClaimExcerpt, verify_source_text_evidence

BODY_BY_URL={
    _ALLOWED["src_python_docs"]: OFFICIAL_QUOTE.encode(),
    _ALLOWED["src_independent_csv"]: INDEPENDENT_QUOTE.encode(),
}


def fake_transport(*, robots="User-agent: *\nAllow: /\n", overrides=None):
    history=[]
    overrides=overrides or {}
    def get(url: str, *, max_bytes: int) -> PublicResponse:
        history.append((url,max_bytes))
        if url in overrides:
            override=overrides[url]
            if isinstance(override,BaseException):
                raise override
            return override
        if url.endswith("/robots.txt"):
            return PublicResponse(200,url,"text/plain",robots.encode())
        return PublicResponse(200,url,"text/plain",BODY_BY_URL[url])
    return get,history


class AllowedPublicCaptureTests(unittest.TestCase):
    def setUp(self):
        self.research=fixtures()[0]
        self.transport,self.calls=fake_transport()

    def collect(self,*,research=None,now=NOW,transport=None,network=False):
        return collect_csv_research_sources(
            self.research if research is None else research,now=now,
            _test_transport=self.transport if transport is None else transport,
            allow_live_network=network,
        )

    def test_default_disables_real_network_entirely(self):
        with self.assertRaises(CaptureDenied):
            collect_csv_research_sources(self.research,now=NOW)
        self.assertEqual(self.calls,[])

    def test_two_allowlisted_sources_one_robots_and_one_page_each(self):
        captures=self.collect()
        self.assertEqual(len(captures),2)
        self.assertEqual(len(self.calls),4)
        self.assertEqual(len(set(x[0] for x in self.calls)),4)
        self.assertTrue(all(x[0].startswith("https://") for x in self.calls))
        self.assertTrue(all(c.claimed_http_status==200 for c in captures))

    def test_each_page_capture_has_exact_hash_and_no_autoapproval(self):
        captures=self.collect()
        report=public_capture_summary(captures)
        self.assertEqual(report["source_count"],2)
        self.assertFalse(report["fact_verification_completed"])
        self.assertFalse(report["script_authorized"])
        self.assertFalse(report["publishing_authorized"])
        self.assertNotIn(OFFICIAL_QUOTE,str(report))
        self.assertNotIn(INDEPENDENT_QUOTE,str(report))

    def test_captures_feed_existing_offline_structural_quote_checker(self):
        captures=self.collect()
        excerpts=[
            ClaimExcerpt("c_csv_reader","src_python_docs",OFFICIAL_QUOTE),
            ClaimExcerpt("c_csv_reader","src_independent_csv",INDEPENDENT_QUOTE),
        ]
        report=verify_source_text_evidence(self.research,captures,excerpts,now=NOW)
        self.assertEqual(report["quoted_pairs"],2)
        self.assertFalse(report["real_http_capture_verified"])
        self.assertFalse(report["publishing_authorized"])

    def test_unapproved_site_disallowed_before_transport(self):
        official,other=self.research.sources
        research=replace(self.research,sources=(
            official,replace(other,url="https://other.example.org/post")))
        with self.assertRaises(CaptureDenied):
            self.collect(research=research)
        self.assertEqual(self.calls,[])

    def test_missing_required_source_denied_before_transport(self):
        research=replace(self.research,sources=(self.research.sources[0],))
        with self.assertRaises(CaptureDenied):
            self.collect(research=research)
        self.assertEqual(self.calls,[])

    def test_robots_disallow_blocks_before_disallowed_page_fetch(self):
        transport,calls=fake_transport(robots="User-agent: *\nDisallow: /\n")
        with self.assertRaises(CaptureDenied):
            self.collect(transport=transport)
        self.assertEqual(len(calls),1)
        self.assertTrue(calls[0][0].endswith("/robots.txt"))

    def test_robots_specific_disallow_rule_observed(self):
        transport,calls=fake_transport(
            robots="User-agent: FlowMinutePublicResearch\nDisallow: /\n"
        )
        with self.assertRaises(CaptureDenied):
            self.collect(transport=transport)
        self.assertEqual(len(calls),1)

    def test_redirect_from_robots_is_denied(self):
        robot="https://realpython.com/robots.txt"
        transport,calls=fake_transport(overrides={
            robot:PublicResponse(301,"https://evil.example/robots.txt",
                                 "text/plain",b"Allow: /")})
        with self.assertRaises(CaptureDenied):
            self.collect(transport=transport)
        self.assertEqual(len(calls),1)

    def test_redirect_from_article_is_denied(self):
        url=_ALLOWED["src_independent_csv"]
        transport,_=fake_transport(overrides={
            url:PublicResponse(200,"https://evil.example/article",
                               "text/plain",INDEPENDENT_QUOTE.encode())})
        with self.assertRaises(CaptureDenied):
            self.collect(transport=transport)

    def test_page_403_429_and_challenge_denied_no_retry(self):
        url=_ALLOWED["src_independent_csv"]
        for status in (403,429,503):
            with self.subTest(status=status):
                transport,calls=fake_transport(overrides={
                    url:PublicResponse(status,url,"text/html",b"Try later")})
                with self.assertRaises(CaptureDenied):
                    self.collect(transport=transport)
                self.assertEqual(len(calls),2)

    def test_html_and_utf8_supported_but_binary_denied(self):
        url=_ALLOWED["src_independent_csv"]
        transport,_=fake_transport(overrides={
            url:PublicResponse(200,url,"text/html; charset=utf-8",
                               INDEPENDENT_QUOTE.encode())})
        captures=self.collect(transport=transport)
        self.assertEqual(captures[0].claimed_content_type,"text/html")
        bad,_=fake_transport(overrides={
            url:PublicResponse(200,url,"application/pdf",b"%PDF-1.7")})
        with self.assertRaises(CaptureDenied):
            self.collect(transport=bad)

    def test_non_utf8_and_null_bytes_denied(self):
        url=_ALLOWED["src_independent_csv"]
        for content in (b"\xff\xfd",b"A\x00B"):
            transport,_=fake_transport(overrides={
                url:PublicResponse(200,url,"text/plain",content)})
            with self.subTest(content=content),self.assertRaises(CaptureDenied):
                self.collect(transport=transport)

    def test_large_article_denied_without_truncating(self):
        url=_ALLOWED["src_independent_csv"]
        transport,_=fake_transport(overrides={
            url:PublicResponse(200,url,"text/plain",b"X"*131073)})
        with self.assertRaises(CaptureDenied):
            self.collect(transport=transport)

    def test_large_robots_denied(self):
        robot="https://realpython.com/robots.txt"
        transport,_=fake_transport(overrides={
            robot:PublicResponse(200,robot,"text/plain",b"#"*32769)})
        with self.assertRaises(CaptureDenied):
            self.collect(transport=transport)

    def test_compressed_response_denied_without_bypass(self):
        url=_ALLOWED["src_independent_csv"]
        transport,_=fake_transport(overrides={
            url:PublicResponse(200,url,"text/html",b"\x1f\x8b",content_encoding="gzip")})
        with self.assertRaises(CaptureDenied):
            self.collect(transport=transport)

    def test_live_and_injected_transport_cannot_be_combined(self):
        with self.assertRaises(CaptureDenied):
            self.collect(network=True)
        self.assertEqual(self.calls,[])

    def test_naive_clock_denied(self):
        with self.assertRaises(CaptureDenied):
            self.collect(now=NOW.replace(tzinfo=None))
        self.assertEqual(self.calls,[])

    def test_stale_citations_require_rechecking(self):
        old_sources=tuple(replace(x,checked_at_utc=(NOW-timedelta(days=9)).isoformat())
                          for x in self.research.sources)
        with self.assertRaises(Exception):
            self.collect(research=replace(self.research,sources=old_sources))
        self.assertEqual(self.calls,[])

    def test_fixture_origin_is_never_labeled_actual_provider_capture(self):
        captures=self.collect()
        self.assertTrue(all(c.collector_label=="offline_fixture_collector" for c in captures))
        report=public_capture_summary(captures)
        self.assertTrue(report["simulation_present"])
        self.assertFalse(report["real_source_provenance_verified"])
        self.assertEqual(report["status"],"SOURCE_CAPTURES_UNTRUSTED_UNTIL_INDEPENDENT_PROVENANCE_REVIEW")

    def test_low_level_transport_does_not_allow_arbitrary_https_urls(self):
        for url in (
            "https://evil.example/private",
            "https://docs.python.org/3/library/not-csv.html",
            "http://docs.python.org/3/library/csv.html",
            "https://realpython.com/login/",
            "https://realpython.com/robots.txt?query=anything",
        ):
            with self.subTest(url=url),self.assertRaises(CaptureDenied):
                _retrieve_public_https(url,max_bytes=1024)

    def test_robots_without_user_agent_rules_is_not_auto_allowed(self):
        transport,calls=fake_transport(robots="# no permissions specified\n")
        with self.assertRaises(CaptureDenied):
            self.collect(transport=transport)
        self.assertEqual(len(calls),1)

    def test_robots_crawl_delay_requires_explicit_rate_scheduler(self):
        transport,calls=fake_transport(
            robots="User-agent: *\nAllow: /\nCrawl-delay: 10\n"
        )
        with self.assertRaises(CaptureDenied):
            self.collect(transport=transport)
        self.assertEqual(len(calls),1)

    def test_robots_request_rate_requires_explicit_rate_scheduler(self):
        transport,calls=fake_transport(
            robots="User-agent: *\nAllow: /\nRequest-rate: 1/10\n"
        )
        with self.assertRaises(CaptureDenied):
            self.collect(transport=transport)
        self.assertEqual(len(calls),1)

    def test_summary_detects_changed_text_without_hash_replacement(self):
        records=self.collect()
        altered=replace(records[0],text_utf8=records[0].text_utf8+" changed")
        with self.assertRaises(CaptureDenied):
            public_capture_summary((altered,records[1]))

    def test_summary_cannot_mix_source_ids_or_urls(self):
        records=self.collect()
        altered=replace(records[0],source_id=records[1].source_id)
        with self.assertRaises(CaptureDenied):
            public_capture_summary((altered,records[1]))
        bad_url=replace(records[0],final_url="https://example.com/fake")
        with self.assertRaises(CaptureDenied):
            public_capture_summary((bad_url,records[1]))

    def test_public_report_rejects_fake_incomplete_captures(self):
        with self.assertRaises(CaptureDenied):
            public_capture_summary(tuple())


if __name__=="__main__":
    unittest.main()
