"""B4d4 official arXiv AI metadata source, lawful rate and abstract scope tests.

All tests offline with synthetic RSS XML and fake article text responses.
No paper PDFs, scripts, rights approval, inference, YouTube or live feeds.
"""
from __future__ import annotations

import datetime as dt
from hashlib import sha256
import io
import json
import re
import unittest
from unittest.mock import patch
import urllib.error

from autopilot.scout import FEEDS, Lead, extract, scout, UTC
from autopilot.daily_cloud_plan import (
    APPROVED_RESEARCH_ORIGINS, candidate_leads, build_plan,
)
from autopilot.evidence_probe import (
    MAX_BODY_BYTES, EvidenceError, ArticleFetchRefused,
    verify_public_source_url, verified_pinned_feed_url,
    choose_independent_sources, probe_source, probe_report,
)
from autopilot.daily_editorial_board import build_editorial_board
from autopilot.test_evidence_probe import FakeOpener, FakeResponse, HTML

CLOCK=dt.datetime(2026,11,6,12,0,tzinfo=UTC)
FEED="https://rss.arxiv.org/rss/cs.AI"
ABS="https://arxiv.org/abs/2611.12345"
TITLE="A new neural agent model for reliable data science automation"
DATETIME="Fri, 06 Nov 2026 00:00:00 -0500"


def fake_arxiv_rss(count=1) -> str:
    records=[]
    for i in range(count):
        link=f"https://arxiv.org/abs/2611.{12345+i}"
        title=f"{TITLE} {i}"
        records.append(
            "<item><title>"+title+"</title>"
            "<link>"+link+"</link>"
            "<pubDate>"+DATETIME+"</pubDate>"
            "<description>arXiv paper abstract for research metadata only.</description>"
            "</item>"
        )
    return ("<?xml version='1.0'?><rss version='2.0'>"
            "<channel><title>cs.AI</title>"+ "".join(records)+"</channel></rss>")


def arxiv_scout_report(count=1):
    return {
        "status":"leads_only_no_publish_authorization",
        "generated_at_utc":CLOCK.isoformat(),
        "leads":[
            {
                "publisher":"arXiv AI",
                "title":f"{TITLE} {i}",
                "url":f"https://arxiv.org/abs/2611.{12345+i}",
                "published_utc":"2026-11-06T05:00:00+00:00",
                "status":"unverified_lead",
            } for i in range(count)
        ]
    }


class ArxivOfficialSourceScope(unittest.TestCase):
    def test_archive_feed_exact_url_and_approved_article_origin_separate(self):
        self.assertIn(("arXiv AI",FEED),FEEDS)
        self.assertEqual(APPROVED_RESEARCH_ORIGINS["arXiv AI"],{"arxiv.org"})
        self.assertEqual(verified_pinned_feed_url("arXiv AI"),FEED)
        self.assertEqual(verify_public_source_url(ABS,"arXiv AI"),ABS)
        with self.assertRaises(EvidenceError):
            verify_public_source_url(FEED,"arXiv AI")

    def test_abstract_page_allowed_but_pdfs_rss_unapproved_hosts_query_denied(self):
        for url in (
            "https://arxiv.org/pdf/2611.12345",
            "https://arxiv.org/html/2611.12345",
            "https://arxiv.org/search/?q=agents",
            "https://arxiv.org/abs/2611.12345?token=secret",
            "https://arxiv.org/abs/2611.12345#source",
            "https://www.arxiv.org/abs/2611.12345",
            "https://rss.arxiv.org/rss/cs.AI",
            "https://arxiv.org:8080/abs/2611.12345",
            "https://x.arxiv.org/abs/2611.12345",
            "http://arxiv.org/abs/2611.12345",
        ):
            with self.subTest(url=url),self.assertRaises(EvidenceError):
                verify_public_source_url(url,"arXiv AI")

    def test_archive_rss_item_is_linked_to_original_abstract_not_pdf(self):
        data=extract(fake_arxiv_rss(), "arXiv AI", CLOCK)
        self.assertEqual(len(data),1)
        self.assertEqual(data[0].publisher,"arXiv AI")
        self.assertEqual(data[0].url,ABS)
        self.assertEqual(data[0].published_utc,"2026-11-06T05:00:00+00:00")
        self.assertEqual(data[0].status,"unverified_lead")
        self.assertFalse(hasattr(data[0],"paper_rights_approved"))
        self.assertFalse(hasattr(data[0],"claims_semantically_verified"))

    def test_no_paper_from_future_or_96hour_old_feed(self):
        self.assertEqual(extract(fake_arxiv_rss(), "arXiv AI",
                                 CLOCK-dt.timedelta(days=3)),[])
        self.assertEqual(extract(fake_arxiv_rss(), "arXiv AI",
                                 CLOCK+dt.timedelta(days=5)),[])

    def test_archive_cannot_swamp_24_leads_of_existing_three_publishers(self):
        primary=fake_arxiv_rss(12)
        articles_other=(
            "<?xml version='1.0'?><rss><channel><item>"
            "<title>New AI models and software automation insights this week</title>"
            "<link>https://openai.com/index/weekly-ai-report</link>"
            "<pubDate>Fri, 06 Nov 2026 11:00:00 GMT</pubDate>"
            "</item></channel></rss>"
        )
        def fake_feed(url,timeout_s=15):
            return primary if url == FEED else articles_other
        # The fictional OpenAI title is also served from different publishers
        # only for testing upper bounds; no true external identity is asserted.
        with patch("autopilot.scout.fetch_feed",side_effect=fake_feed):
            result=scout(now=CLOCK)
        self.assertEqual(result["independent_feeds_checked"],4)
        self.assertLessEqual(len(result["leads"]),24)
        self.assertLessEqual(sum(x["publisher"]=="arXiv AI" for x in result["leads"]),6)
        self.assertGreaterEqual(sum(x["publisher"]=="arXiv AI" for x in result["leads"]),1)
        self.assertEqual(result["status"],"leads_only_no_publish_authorization")

    def test_only_one_archive_article_probed_even_with_many_available(self):
        feed=arxiv_scout_report(8)
        feed["leads"].extend([
            {"publisher":"OpenAI","status":"unverified_lead",
             "title":"Research on AI safety and model agents",
             "url":"https://openai.com/index/research-ai"},
            {"publisher":"The Verge","status":"unverified_lead",
             "title":"AI data analytics automation changes",
             "url":"https://www.theverge.com/2026/11/6/analytics"},
        ])
        chosen=choose_independent_sources(feed,limit=6)
        self.assertEqual(sum(x["publisher"]=="arXiv AI" for x in chosen),1)
        self.assertEqual(chosen[0]["publisher"],"arXiv AI")
        self.assertLessEqual(len(chosen),3)

    def test_archive_canonical_source_plan_can_be_created_but_not_promoted(self):
        report=arxiv_scout_report()
        plan=build_plan("2026-11-07",scout_report=report,
                        generated_at_utc=CLOCK)
        self.assertEqual(plan["research_lead_count"],1)
        self.assertEqual(plan["slots"][0]["research_lead"]["publisher"],"arXiv AI")
        self.assertIs(plan["youtube_upload_enabled"],False)
        self.assertFalse(plan["any_content_verified"])
        self.assertFalse(plan["slots"][0]["real_script_exists"])

    def test_wrong_archive_topic_or_feed_host_in_daily_plan_rejected(self):
        report=arxiv_scout_report()
        for url in ("https://rss.arxiv.org/rss/cs.AI",
                    "https://arxiv.org/pdf/2611.12345",
                    "https://arxiv.org/abs/invalid",
                    "https://arxiv.org/abs/2611.12345?q=x"):
            with self.subTest(url=url):
                hacked=arxiv_scout_report()
                hacked["leads"][0]["url"]=url
                plan=build_plan("2026-11-07",scout_report=hacked,
                                generated_at_utc=CLOCK)
                self.assertEqual(plan["research_lead_count"],0)
                self.assertFalse(plan["youtube_schedule_enabled"])

    def test_real_page_bytes_under_new_one_megabyte_limit_not_approved_facts(self):
        self.assertEqual(MAX_BODY_BYTES,1_048_576)
        lead=arxiv_scout_report()["leads"][0]
        article_body=b"<html><head><title>Source abstract</title></head><body>" + (
            b"Research data and methods, not fact checked. " * 14000
        ) + b"</body></html>"
        self.assertGreater(len(article_body),262_144)
        self.assertLess(len(article_body),MAX_BODY_BYTES)
        observation=probe_source(lead,clock=CLOCK,
                                 opener=FakeOpener(payload=article_body))
        self.assertEqual(observation["body_bytes_hashed"],len(article_body))
        self.assertEqual(observation["response_sha256"],
                         sha256(article_body).hexdigest())
        self.assertEqual(observation["status"],"SOURCE_FETCHED_NOT_FACT_CHECKED")
        self.assertFalse(observation["facts_verified"])
        self.assertFalse(observation["rights_verified"])
        self.assertFalse(observation["youtube_release_authorized"])

    def test_over_one_megabyte_article_refused_with_bounded_reason(self):
        lead=arxiv_scout_report()["leads"][0]
        with self.assertRaises(ArticleFetchRefused) as cm:
            probe_source(lead,clock=CLOCK,opener=FakeOpener(
                payload=b"x" * (MAX_BODY_BYTES+1)))
        self.assertEqual(cm.exception.category,"ARTICLE_TOO_LARGE")

    def test_official_archive_rss_fallback_is_still_only_metadata(self):
        lead=arxiv_scout_report()["leads"][0]
        xml=fake_arxiv_rss().encode()
        class FakeArchiveOpener:
            def __init__(self):
                self.calls=[]
            def open(self,request,timeout):
                self.calls.append(request.full_url)
                if request.full_url == FEED:
                    return FakeResponse(FEED,body=xml,mime="application/rss+xml")
                raise urllib.error.HTTPError(request.full_url,403,
                                             "NO BOT ACCESS",{},None)
        agent=FakeArchiveOpener()
        evidence=probe_report(arxiv_scout_report(),clock=CLOCK,
                              opener=agent,max_sources=1)
        self.assertEqual(agent.calls,[ABS,FEED])
        self.assertEqual(evidence["sources_fetched"],0)
        self.assertEqual(evidence["feed_entries_observed_only"],1)
        self.assertEqual(evidence["direct_article_fetch_failure_counts"],
                         {"HTTP_ACCESS_DENIED":1})
        self.assertEqual(evidence["sources"][0]["source_url"],ABS)
        self.assertFalse(evidence["sources"][0]["source_article_fetched"])
        self.assertFalse(evidence["youtube_upload_enabled"])

    def test_no_archive_paper_contents_reproduced_in_source_receipts(self):
        lead=arxiv_scout_report()["leads"][0]
        observation=probe_source(lead,clock=CLOCK,
                                  opener=FakeOpener(payload=HTML))
        data=json.dumps(observation)
        self.assertNotIn("original research ",data)
        self.assertFalse(observation["facts_verified"])
        self.assertFalse(observation["source_text_or_image_stored"])


if __name__=="__main__":
    unittest.main()
