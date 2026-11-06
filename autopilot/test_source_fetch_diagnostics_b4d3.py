"""B4d3 adversarial tests: physical HTTP failure classes, safe redirects, zero claims.

Real public publisher fetches happen only in the GitHub daily job.
Tests use fake requests/responses and never access the internet.
"""
from __future__ import annotations

import copy
import datetime as dt
import io
from pathlib import Path
import unittest
import urllib.error
import urllib.request

from autopilot.evidence_probe import (
    ArticleFetchRefused, EvidenceError, MAX_ARTICLE_REDIRECTS,
    PublisherOnlyArticleRedirect, SAFE_FETCH_FAILURES, probe_report,
    probe_source, verify_public_source_url,
)
from autopilot.test_evidence_probe import (
    CLOCK, FakeOpener, FakeResponse, FeedFallbackOpener, HTML, sample_report,
)

LEAD=sample_report()["leads"][0]
START=LEAD["url"]


class OriginSafeRedirectPolicyTests(unittest.TestCase):
    def start(self):
        return PublisherOnlyArticleRedirect("OpenAI", START)

    def request(self, url: str=START, method: str="GET"):
        return urllib.request.Request(url, method=method)

    def hop(self, handler, request, location, code=302):
        return handler.redirect_request(request,None,code,"moved",{},location)

    def test_http_to_same_exact_publisher_domain_is_rejected(self):
        h=self.start()
        with self.assertRaises(ArticleFetchRefused) as cm:
            self.hop(h,self.request(),"http://openai.com/index/canonical")
        self.assertEqual(cm.exception.category,"REDIRECT_REJECTED")
        self.assertEqual(h.targets,[])

    def test_one_same_origin_canonical_path_redirect_is_allowed(self):
        h=self.start()
        target="https://openai.com/index/new-canonical"
        r=self.hop(h,self.request(),target,301)
        self.assertEqual(r.full_url,target)
        self.assertEqual(h.targets,[target])

    def test_publisher_apex_to_explicit_www_subdomain_allowed(self):
        h=self.start()
        url="https://www.openai.com/index/new-title"
        r=self.hop(h,self.request(),url,302)
        self.assertEqual(r.full_url,url)
        self.assertEqual(len(h.targets),1)

    def test_publisher_relative_redirect_resolves_to_allowed_https_url(self):
        h=self.start()
        r=self.hop(h,self.request(),"/index/corrected-page",307)
        self.assertEqual(r.full_url,"https://openai.com/index/corrected-page")
        self.assertEqual(len(h.targets),1)

    def test_second_hop_allowed_but_third_rejected_with_no_request_created(self):
        h=self.start()
        req=self.request()
        a=self.hop(h,req,"https://openai.com/index/new-a")
        b=self.hop(h,a,"https://openai.com/index/new-b")
        self.assertEqual(len(h.targets),MAX_ARTICLE_REDIRECTS)
        self.assertEqual(b.full_url,"https://openai.com/index/new-b")
        with self.assertRaises(ArticleFetchRefused):
            self.hop(h,b,"https://openai.com/index/new-c")
        self.assertEqual(len(h.targets),MAX_ARTICLE_REDIRECTS)

    def test_no_redirect_loops_back_to_original(self):
        h=self.start()
        a=self.hop(h,self.request(),"https://openai.com/index/a")
        with self.assertRaises(ArticleFetchRefused):
            self.hop(h,a,START)

    def test_no_redirect_loop_to_any_previous_target(self):
        h=self.start()
        a=self.hop(h,self.request(),"https://openai.com/index/a")
        b=self.hop(h,a,"https://openai.com/index/b")
        with self.assertRaises(ArticleFetchRefused):
            self.hop(h,b,"https://openai.com/index/a")

    def test_disallow_any_other_host_even_from_approved_source(self):
        for target in (
            "https://evil.example/article",
            "https://www.google.com/robots",
            "https://deepmind.google/discover/blog/foo",
            "https://openai.com.attacker.example/steal",
            "https://127.0.0.1/admin",
            "https://[::1]/private",
            "//evil.example/source",
            "https://sub.openai.com/unlisted",
            "file:///etc/shadow",
        ):
            with self.subTest(target=target):
                handler=self.start()
                with self.assertRaises(ArticleFetchRefused):
                    self.hop(handler,self.request(),target)
                self.assertEqual(handler.targets,[])

    def test_embedded_user_credentials_nonstandard_port_fragment_and_spaces_denied(self):
        for target in (
            "https://name:secret@openai.com/index/new",
            "https://openai.com:8080/index/new",
            "https://openai.com/index/new#private",
            "https://openai.com/index/new path",
        ):
            with self.subTest(target=target):
                with self.assertRaises(ArticleFetchRefused):
                    self.hop(self.start(),self.request(),target)

    def test_post_cannot_redirect_and_http_status_unapproved(self):
        with self.assertRaises(ArticleFetchRefused):
            self.hop(self.start(),self.request(method="POST"),
                     "https://openai.com/index/canonical")
        with self.assertRaises(ArticleFetchRefused):
            self.hop(self.start(),self.request(),
                     "https://openai.com/index/canonical",code=305)

    def test_normal_fake_opener_cannot_forge_an_allowed_redirect(self):
        f=FakeOpener(returned_url="https://www.openai.com/index/other")
        with self.assertRaises(ArticleFetchRefused) as cm:
            probe_source(LEAD,clock=CLOCK,opener=f)
        self.assertEqual(cm.exception.category,"UNEXPECTED_FINAL_URL")
        self.assertEqual(f.requests,[(START,10.0)])

    def test_successful_exact_article_still_records_no_redirect_and_zero_fact_claims(self):
        report=probe_source(LEAD,clock=CLOCK,opener=FakeOpener())
        self.assertEqual(report["approved_same_publisher_redirect_hops"],0)
        self.assertIs(report["approved_same_publisher_redirect"],False)
        self.assertEqual(report["status"],"SOURCE_FETCHED_NOT_FACT_CHECKED")
        self.assertIs(report["facts_verified"],False)
        self.assertIs(report["youtube_release_authorized"],False)


class PublisherBlockDiagnosticsTests(unittest.TestCase):
    def test_actual_403_with_successful_rss_fallback_counted_without_server_text(self):
        f=FeedFallbackOpener()
        report=probe_report({
            "status":"leads_only_no_publish_authorization",
            "leads":[LEAD],
        },clock=CLOCK,max_sources=1,opener=f)
        self.assertEqual(report["sources_fetched"],0)
        self.assertEqual(report["feed_entries_observed_only"],1)
        self.assertEqual(report["direct_article_fetch_failure_counts"],{
            "HTTP_ACCESS_DENIED":1})
        self.assertEqual(report["sources"][0]["direct_article_failure_class"],
                         "HTTP_ACCESS_DENIED")
        self.assertIs(report["sources"][0]["source_article_fetched"],False)
        self.assertEqual(report["source_articles_with_bounded_publisher_redirect"],0)

    def test_bounded_diagnostic_classes_cannot_accept_server_error_or_urls(self):
        for value in ("https://openai.com/auth?secret=abc",
                      "private_password", "", "403:private_info", "SUCCESS"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    ArticleFetchRefused(value)
        self.assertEqual(len(SAFE_FETCH_FAILURES),13)

    def test_status_429_classifies_rate_limit_without_exposing_response(self):
        bad=urllib.error.HTTPError(
            START,429,"private remote error and auth token",{},io.BytesIO(b"secret"))
        f=FakeOpener(error=bad)
        with self.assertRaises(ArticleFetchRefused) as cm:
            probe_source(LEAD,clock=CLOCK,opener=f)
        self.assertEqual(cm.exception.category,"HTTP_RATE_LIMITED")
        self.assertNotIn("secret",str(cm.exception))

    def test_status_403_classifies_access_denial_not_repeated_retry(self):
        bad=urllib.error.HTTPError(START,403,"Publisher bot blocked",{},None)
        with self.assertRaises(ArticleFetchRefused) as cm:
            probe_source(LEAD,clock=CLOCK,opener=FakeOpener(error=bad))
        self.assertEqual(cm.exception.category,"HTTP_ACCESS_DENIED")

    def test_status_404_classifies_missing_article(self):
        bad=urllib.error.HTTPError(START,404,"Content missing",{},None)
        with self.assertRaises(ArticleFetchRefused) as cm:
            probe_source(LEAD,clock=CLOCK,opener=FakeOpener(error=bad))
        self.assertEqual(cm.exception.category,"HTTP_NOT_FOUND")

    def test_http_503_classifies_remote_unavailability_not_truth(self):
        bad=urllib.error.HTTPError(START,503,"Service unavailable",{},None)
        with self.assertRaises(ArticleFetchRefused) as cm:
            probe_source(LEAD,clock=CLOCK,opener=FakeOpener(error=bad))
        self.assertEqual(cm.exception.category,"HTTP_UNAVAILABLE")

    def test_server_error_messages_never_stored_in_report(self):
        class BothBlocked:
            def open(self,request,timeout):
                raise urllib.error.HTTPError(
                    request.full_url,403,"TOP_PRIVATE_SERVER_TEXT",{},None)
        report=probe_report({"status":"leads_only_no_publish_authorization",
                             "leads":[LEAD]},clock=CLOCK,max_sources=1,
                            opener=BothBlocked())
        self.assertEqual(report["sources_failed"],1)
        self.assertEqual(report["direct_article_fetch_failure_counts"],
                         {"HTTP_ACCESS_DENIED":1})
        self.assertEqual(report["failures"][0]["direct_article_failure_class"],
                         "HTTP_ACCESS_DENIED")
        import json
        self.assertNotIn("TOP_PRIVATE_SERVER_TEXT",json.dumps(report))
        self.assertFalse(report["youtube_upload_enabled"])
        self.assertEqual(report["claims_verified"],0)

    def test_direct_200_cloudflare_challenge_is_not_counted_as_article(self):
        body=(b"<html><head><title>Just a moment...</title></head>"
              b"<body>Checking your browser</body></html>" + b" " * 160)
        with self.assertRaises(ArticleFetchRefused) as cm:
            probe_source(LEAD,clock=CLOCK,opener=FakeOpener(payload=body))
        self.assertEqual(cm.exception.category,"BOT_CHALLENGE_PAGE")

    def test_other_200_html_with_actual_body_is_only_observed_not_fact_checked(self):
        record=probe_source(LEAD,clock=CLOCK,opener=FakeOpener(payload=HTML))
        self.assertEqual(record["status"],"SOURCE_FETCHED_NOT_FACT_CHECKED")
        self.assertEqual(record["body_bytes_hashed"],len(HTML))
        self.assertFalse(record["independent_corroboration_confirmed"])

    def test_empty_body_and_binary_type_not_promoted_to_article(self):
        for f,reason in (
            (FakeOpener(payload=b"small"),"EMPTY_OR_OVERSIZED_ARTICLE"),
            (FakeOpener(mime="application/pdf"),"UNSUPPORTED_CONTENT_TYPE"),
        ):
            with self.subTest(reason=reason),self.assertRaises(ArticleFetchRefused) as cm:
                probe_source(LEAD,clock=CLOCK,opener=f)
            self.assertEqual(cm.exception.category,reason)

    def test_three_direct_page_failures_are_counted_by_category(self):
        bad=urllib.error.HTTPError(START,403,"blocked",{},None)
        f=FakeOpener(error=bad)
        report=probe_report(sample_report(),clock=CLOCK,max_sources=3,opener=f)
        self.assertEqual(report["sources_failed"],3)
        self.assertEqual(report["direct_article_fetch_failure_counts"],
                         {"HTTP_ACCESS_DENIED":3})
        self.assertEqual(report["sources_fetched"],0)
        self.assertFalse(report["source_body_persisted"])
        self.assertEqual(report["billed_provider_calls"],0)


if __name__=="__main__":
    unittest.main()
