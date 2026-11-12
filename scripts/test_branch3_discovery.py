"""Clivox A1 public-metadata-only discovery: adversarial unit tests."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import io
import json
from urllib.parse import parse_qs, urlsplit
from urllib.error import HTTPError
import unittest

from scripts.branch3_discovery import (
    API_ORIGIN, DiscoveryBlocked, build_report, canonical_ids,
    collect_public_videos, mock_fixture, parse_duration, public_count,
    source_score, api_read, utc_timestamp, CATEGORIES, TARGET_CHANNEL
)

NOW = datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)
KEY = "TEST_ONLY_FAKE_API_KEY_NOT_REAL_123456"


class Response:
    def __init__(self, payload):
        self.raw = json.dumps(payload).encode("utf-8")
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
    def read(self, limit=-1):
        return self.raw[:limit]


class A1DiscoveryTests(unittest.TestCase):
    def test_all_five_categories_and_fixture_score(self):
        for category in CATEGORIES:
            with self.subTest(category=category):
                report = build_report(
                    mock_fixture(), category=category,
                    mode="fixture", query="", now=NOW, fixture=True,
                )
                self.assertEqual(report["channel_id"], TARGET_CHANNEL)
                self.assertEqual(report["stage"], "A1_DISCOVERY_PUBLIC_METADATA_ONLY")
                self.assertTrue(report["is_synthetic_fixture"])
                self.assertEqual(report["source_of_numbers"], "synthetic_test_fixture")
                self.assertEqual(len(report["candidates"]), 2)
                self.assertEqual(report["youtube_api_write_calls"], 0)
                self.assertFalse(report["release_or_media_acquisition_allowed"])
                for c in report["candidates"]:
                    self.assertEqual(c["permission_state"], "UNVERIFIED")
                    self.assertFalse(c["ready_to_publish"])
                    self.assertFalse(c["source_media_download_allowed"])
                    self.assertFalse(c["clivox_commercial_clipping_rights_verified"])
                    self.assertFalse(c["underlying_game_music_guest_rights_cleared"])
                    self.assertFalse(c["youtube_upload_authorized"])
                    self.assertIn("youtube.com/watch?v=", c["source_url"])
                    self.assertGreaterEqual(c["research_priority_score_0_to_100"], 0)
                    self.assertLessEqual(c["research_priority_score_0_to_100"], 100)

    def test_example_duration_and_missing_stats_not_invented(self):
        self.assertEqual(parse_duration("PT1H02M04S"), 3724)
        self.assertEqual(parse_duration("PT21M15S"), 1275)
        self.assertEqual(parse_duration("P1DT2M"), 86520)
        self.assertIsNone(parse_duration("LIVE"))
        self.assertIsNone(parse_duration("PT"))
        self.assertIsNone(public_count({}, "likeCount"))
        self.assertIsNone(public_count({"viewCount": 1234}, "viewCount"))
        self.assertEqual(public_count({"viewCount": "0"}, "viewCount"), 0)
        videos = mock_fixture()
        del videos[0]["statistics"]["likeCount"]
        report = build_report(videos, category="gaming", mode="fixture",
                              query="", now=NOW, fixture=True)
        c = next(c for c in report["candidates"]
                 if c["source_video_id"] == "AbCdEf12345")
        self.assertIsNone(c["public_stats"]["likes"])
        self.assertIsNone(c["score_components"]["observed_engagement_ratio"])

    def test_dedupe_and_invalid_payloads(self):
        items = mock_fixture()
        report = build_report(items + [copy.deepcopy(items[0])],
                              category="gaming", mode="fixture",
                              query="", now=NOW, fixture=True)
        self.assertEqual(len(report["candidates"]), 2)
        report2 = build_report([{"id":"invalid"},{},None],category="gaming",
                               mode="fixture",query="",now=NOW,fixture=True)
        self.assertEqual(report2["candidates"], [])
        bad = copy.deepcopy(items[0])
        bad["snippet"]["publishedAt"] = "2027-01-01T00:00:00Z"
        report3=build_report([bad],category="gaming",mode="fixture",
                             query="",now=NOW,fixture=True)
        self.assertEqual(report3["candidates"], [])

    def test_api_only_fixed_host_and_read_endpoints(self):
        self.assertTrue(API_ORIGIN.startswith("https://www.googleapis.com/youtube/v3/"))
        with self.assertRaises(DiscoveryBlocked):
            api_read("videos.insert", {}, KEY, opener=lambda *_a, **_k: None)
        with self.assertRaises(DiscoveryBlocked):
            api_read("videos", {"media":"x"}, KEY, opener=lambda *_a, **_k: None)
        urls = []
        def opener(url,timeout):
            urls.append(url)
            self.assertEqual(timeout,15)
            return Response({"items": mock_fixture()})
        data=api_read("videos",{"part":"snippet,statistics,contentDetails",
                                "id":"AbCdEf12345"},KEY,opener=opener)
        self.assertEqual(len(data["items"]),2)
        self.assertTrue(urls[0].startswith(API_ORIGIN+"videos?"))
        self.assertEqual(parse_qs(urlsplit(urls[0]).query)["key"],[KEY])

    def test_ids_collection_one_metadata_call_and_no_download(self):
        calls=[]
        def opener(url,timeout):
            calls.append(url)
            return Response({"items":mock_fixture()})
        result = collect_public_videos(mode="ids",category="gaming",
            ids="AbCdEf12345,GhIjKl67890,AbCdEf12345",query="",
            key=KEY,now=NOW,opener=opener)
        self.assertEqual(len(result),2)
        self.assertEqual(len(calls),1)
        self.assertIn("/videos?",calls[0])
        self.assertNotIn("/videos.insert",calls[0])
        self.assertNotIn("/download",calls[0])

    def test_query_collection_bounded_two_readonly_api_calls(self):
        calls=[]
        def opener(url,timeout):
            calls.append(url)
            if "/search?" in url:
                self.assertEqual(parse_qs(urlsplit(url).query)["maxResults"],["10"])
                self.assertEqual(parse_qs(urlsplit(url).query)["type"],["video"])
                self.assertIn("publishedAfter",parse_qs(urlsplit(url).query))
                return Response({"items":[
                    {"id":{"videoId":"AbCdEf12345"}},
                    {"id":{"videoId":"AbCdEf12345"}},
                    {"id":{"videoId":"GhIjKl67890"}}
                ]})
            return Response({"items":mock_fixture()})
        found=collect_public_videos(mode="query",category="livestream",
            ids="",query="funny livestream",key=KEY,now=NOW,opener=opener)
        self.assertEqual(len(found),2)
        self.assertEqual(len(calls),2)
        self.assertIn("/search?",calls[0])
        self.assertIn("/videos?",calls[1])
        self.assertEqual(parse_qs(urlsplit(calls[1]).query)["id"][0],
                         "AbCdEf12345,GhIjKl67890")

    def test_invalid_ids_modes_and_categories(self):
        for bad in ("", "abc", "ABCDEFGHIJK,NOTVALID", "ABCDEFGHIJK," * 32,
                    "https://www.youtube.com/watch?v=ABCDEFGHIJK",
                    "ABCDEFGHIJK;rm -rf /"):
            with self.subTest(bad=bad),self.assertRaises(DiscoveryBlocked):
                canonical_ids(bad)
        for config in [
            dict(mode="unknown",category="gaming",ids="ABCDEFGHIJK",query=""),
            dict(mode="ids",category="gaming",ids="ABCDEFGHIJK",query="also query"),
            dict(mode="query",category="gaming",ids="ABCDEFGHIJK",query="gaming"),
            dict(mode="query",category="gaming",ids="",query=""),
            dict(mode="query",category="gaming",ids="",query="x"*91),
            dict(mode="ids",category="unknown",ids="ABCDEFGHIJK",query=""),
        ]:
            with self.subTest(config=config),self.assertRaises(DiscoveryBlocked):
                collect_public_videos(**config,key=KEY,now=NOW)

    def test_no_secret_in_error_and_no_write(self):
        def broken(url,timeout):
            raise HTTPError(url,403,"private details",{},None)
        with self.assertRaises(DiscoveryBlocked) as caught:
            api_read("videos",{"part":"snippet","id":"ABCDEFGHIJK"},
                     KEY,opener=broken)
        self.assertNotIn(KEY,str(caught.exception))
        self.assertEqual(str(caught.exception),
                         "CLIVOX_DISCOVERY_DENIED_METADATA_API_UNAVAILABLE")

    def test_score_is_source_level_only_not_a_license(self):
        hi,components=source_score(title="Funny gaming clutch",
            category="gaming",age_hours=24,views=50000,likes=3500,comments=200)
        lo,_=source_score(title="Talk",category="gaming",
            age_hours=30*24,views=10,likes=None,comments=None)
        self.assertGreater(hi,lo)
        self.assertIsNotNone(components["views_per_hour"])
        self.assertEqual(utc_timestamp(NOW),"2026-11-12T12:00:00Z")


if __name__ == "__main__":
    unittest.main()
