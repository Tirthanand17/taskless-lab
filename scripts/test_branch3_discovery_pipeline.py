"""Clivox A1 discovery: offline tests; none calls external services."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from scripts.branch3_discovery_pipeline import (
    CHANNEL, DiscoveryDenied, editorial_score, intake, load,
)

DATA=Path(__file__).resolve().parents[1]/"branch3/discovery/fixtures/research-candidates.json"

def example():
    return json.loads(DATA.read_text("utf-8"))

class DiscoveryPipelineTests(unittest.TestCase):
    def test_fixture_all_pending_and_null_metrics(self):
        r=load(DATA)
        self.assertEqual(r["candidate_count"],3)
        self.assertTrue(r["all_creator_permissions_pending"])
        self.assertFalse(r["youtube_write_enabled"])
        self.assertFalse(r["source_media_download_enabled"])
        for candidate in r["queue"]:
            for field in ("rights_verified","creator_permission_verified",
                          "source_acquisition_authorized","render_authorized",
                          "youtube_upload_authorized","publishing_authorized"):
                self.assertIs(candidate[field],False)
            self.assertFalse(candidate["metric_evidence_available"])
            self.assertEqual(candidate["next_state"],"RIGHTS_PENDING")
            self.assertRegex(candidate["candidate_digest_sha256"],r"^[0-9a-f]{64}$")
        self.assertEqual([x["editorial_hypothesis_score_0_to_100"] for x in r["queue"]],
                         sorted((x["editorial_hypothesis_score_0_to_100"] for x in r["queue"]),reverse=True))

    def test_determinism(self):
        payload=example()
        self.assertEqual(intake(payload),intake(copy.deepcopy(payload)))
        self.assertLessEqual(max(x["editorial_hypothesis_score_0_to_100"] for x in intake(payload)["queue"]),100)

    def test_invalid_account_or_dataset(self):
        for key,value in (("channel_id","UCCcL9Q_jqVq6LJmnYUSAFZA"),
                          ("dataset_status","LICENSED"),("schema_version",2)):
            payload=example()
            payload[key]=value
            with self.subTest(key=key),self.assertRaises(DiscoveryDenied):
                intake(payload)

    def test_reject_approval_claims(self):
        for field in ("rights_verified","creator_approved","media_downloaded",
                      "upload_authorized","publication_authorized","paid_campaign_joined"):
            payload=example()
            payload["candidates"][0][field]=True
            with self.subTest(field=field),self.assertRaises(DiscoveryDenied):
                intake(payload)

    def test_duplicate_source_and_id(self):
        payload=example()
        payload["candidates"].append(copy.deepcopy(payload["candidates"][0]))
        with self.assertRaises(DiscoveryDenied):intake(payload)
        payload=example()
        payload["candidates"][1]["source_url"]=payload["candidates"][0]["source_url"]
        with self.assertRaises(DiscoveryDenied):intake(payload)

    def test_reject_malicious_url(self):
        for url in ("https://evil.example/c/campaigns/123",
                    "https://contentrewards.com.evil.example/c/campaigns/123",
                    "http://contentrewards.com/c/campaigns/123",
                    "https://user:pass@contentrewards.com/c/campaigns/123",
                    "https://contentrewards.com/c/campaigns/123?token=private",
                    "https://contentrewards.com/c/campaigns/123#credentials"):
            payload=example()
            payload["candidates"][0]["source_url"]=url
            with self.subTest(url=url),self.assertRaises(DiscoveryDenied):
                intake(payload)

    def test_reject_invented_campaign_metrics(self):
        for field in ("views","likes","comments"):
            payload=example()
            payload["candidates"][0]["video_statistics"][field]=1
            with self.subTest(field=field),self.assertRaises(DiscoveryDenied):
                intake(payload)

    def test_reject_negative_boolean_string_traffic(self):
        payload=example()
        payload["candidates"][0]["video_statistics"]["views"]=-5
        with self.assertRaises(DiscoveryDenied):intake(payload)
        payload=example()
        payload["candidates"][0]["signals"]["fast_hook"]="true"
        with self.assertRaises(DiscoveryDenied):intake(payload)

    def test_reject_invalid_discovery_categories_and_fields(self):
        payload=example()
        payload["candidates"][0]["category"]="sports_stolen_broadcasts"
        with self.assertRaises(DiscoveryDenied):intake(payload)
        payload=example()
        payload["candidates"][0]["internal_secret"]="never"
        with self.assertRaises(DiscoveryDenied):intake(payload)

    def test_video_source_requires_real_channel_and_exact_url(self):
        payload=example()
        record=payload["candidates"][0]
        record.update({"source_kind":"youtube_video","source_video_id":"i6pmnpaOaZQ",
                       "creator_channel_id":"UC"+"x"*22,
                       "source_url":"https://www.youtube.com/watch?v=i6pmnpaOaZQ"})
        r=intake(payload)
        self.assertEqual(r["candidate_count"],3)
        self.assertFalse(r["queue"][0]["youtube_upload_authorized"])
        record["source_url"]="https://www.youtube.com/watch?v=i6pmnpaOaZQ&token=secret"
        with self.assertRaises(DiscoveryDenied):intake(payload)
        record["source_url"]="https://www.youtube.com/watch?v=i6pmnpaOaZQ"
        record["creator_channel_id"]=CHANNEL
        with self.assertRaises(DiscoveryDenied):intake(payload)

    def test_no_candidates_and_over_limit(self):
        payload=example()
        payload["candidates"]=[]
        with self.assertRaises(DiscoveryDenied):intake(payload)
        payload=example()
        payload["candidates"]=payload["candidates"]*40
        with self.assertRaises(DiscoveryDenied):intake(payload)

    def test_reject_html_credentials_and_malformed_titles(self):
        payload=example()
        payload["candidates"][0]["title"]="Injected\nNewlines"
        with self.assertRaises(DiscoveryDenied):intake(payload)
        payload=example()
        payload["candidates"][0]["source_url"]="https://contentrewards.com:abc/c/campaigns/foo"
        with self.assertRaises((DiscoveryDenied,ValueError)):intake(payload)

if __name__=="__main__":
    unittest.main()
