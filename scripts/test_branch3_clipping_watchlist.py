"""Adversarial tests: never promote public clipping campaigns to permission."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import unittest
from scripts.branch3_validate_clipping_watchlist import WATCHLIST,validate_watchlist,ResearchOnlyError

class WatchlistTests(unittest.TestCase):
    def setUp(self):
        self.w=json.loads(WATCHLIST.read_text("utf8"))

    def test_research_only(self):
        self.assertEqual(validate_watchlist(self.w),5)

    def test_clearance_claim_rejected(self):
        for key in ("rights_verified","clipping_authorized_for_clivox","allowlist_approved","media_download_authorized","upload_authorized"):
            w=copy.deepcopy(self.w)
            w["candidates"][0][key]=True
            with self.subTest(key=key),self.assertRaises(ResearchOnlyError):
                validate_watchlist(w)

    def test_wont_turn_on_publishing_or_download(self):
        for key in ("automatic_download_enabled","automatic_publish_enabled"):
            w=copy.deepcopy(self.w);w[key]=True
            with self.subTest(key=key),self.assertRaises(ResearchOnlyError):
                validate_watchlist(w)

    def test_reject_untrusted_campaign_urls(self):
        for url in ("http://contentrewards.com/c/campaigns/123",
                    "https://evil.example/c/campaigns/123",
                    "https://contentrewards.com.evil.example/c/campaigns/123",
                    "https://user:pass@contentrewards.com/c/campaigns/123"):
            w=copy.deepcopy(self.w);w["candidates"][0]["campaign_url"]=url
            with self.subTest(url=url),self.assertRaises(ResearchOnlyError):
                validate_watchlist(w)

    def test_reject_ignored_platform_and_paused_campaign(self):
        for index,modified in ((3,{"initial_priority":"REVIEW_FIRST"}),
                               (4,{"initial_priority":"REVIEW_FIRST"})):
            w=copy.deepcopy(self.w);w["candidates"][index].update(modified)
            with self.subTest(index=index),self.assertRaises(ResearchOnlyError):
                validate_watchlist(w)

    def test_reject_bogus_approval_and_duplicate(self):
        w=copy.deepcopy(self.w);w["candidates"][0]["status"]="APPROVED"
        with self.assertRaises(ResearchOnlyError):validate_watchlist(w)
        w=copy.deepcopy(self.w);w["candidates"].append(copy.deepcopy(w["candidates"][0]))
        with self.assertRaises(ResearchOnlyError):validate_watchlist(w)

if __name__=="__main__":
    unittest.main()
