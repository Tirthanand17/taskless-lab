import datetime as dt
import unittest
from autopilot import scout
from autopilot.growth import VideoMetric, analyze
from autopilot.cloud_guard import (preflight, CloudGateError,
                                   require_approval_for_spend,
                                   validate_distinct_short_voices,
                                   public_worker_can_publish)

NOW = dt.datetime(2026,10,16,12,0,tzinfo=dt.timezone.utc)
FEED = """<rss><channel>
<item><title>New AI agents help code faster</title><link>https://openai.com/index/agents/</link>
<pubDate>Fri, 16 Oct 2026 09:00:00 +0000</pubDate></item>
<item><title>Old AI agents are different</title><link>https://openai.com/index/old/</link>
<pubDate>Mon, 12 Oct 2026 09:00:00 +0000</pubDate></item>
</channel></rss>"""
ATOM = """<feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>Gemini AI coding agent update</title>
<link href="https://deepmind.google/blog/coding-agent"/>
<updated>2026-10-16T08:00:00Z</updated></entry></feed>"""

class ResearchTests(unittest.TestCase):
    def test_only_recent_leads_and_no_publish_authorization(self):
        result = scout.extract(FEED,"OpenAI",NOW,max_age_hours=72)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0].status,"unverified_lead")
    def test_atom(self):
        result=scout.extract(ATOM,"Google DeepMind",NOW)
        self.assertEqual(len(result),1)
        self.assertIn("deepmind.google",result[0].url)
    def test_duplicate_rejected(self):
        existing=("New AI agents help code faster",)
        self.assertEqual(scout.extract(FEED,"OpenAI",NOW,existing_titles=existing),[])
    def test_ssrf_disallowed(self):
        with self.assertRaises(ValueError):
            scout.fetch_feed("http://127.0.0.1/")
        with self.assertRaises(ValueError):
            scout.fetch_feed("https://evil.example/feed.xml")

class GrowthTests(unittest.TestCase):
    def make(self,i,format="short",views=400,engaged=300,avg=17):
        return VideoMetric(f"vid{i}",format,72,views,engaged,avg,40,2,3)
    def test_low_sample_does_not_overfit(self):
        report=analyze([self.make(1)])
        self.assertEqual(report["cohorts"]["short"]["status"],"insufficient_sample")
        self.assertIsNone(report["cohorts"]["short"]["experiment"])
    def test_age_and_content_type_cohorts(self):
        v=[self.make(i) for i in range(6)]+[self.make(9,"long")]
        out=analyze(v)
        self.assertEqual(out["cohorts"]["short"]["status"],"experiment_eligible")
        self.assertEqual(out["cohorts"]["long"]["status"],"insufficient_sample")
    def test_bad_data_rejected(self):
        with self.assertRaises(ValueError):
            analyze([self.make(1,views=5,engaged=7)])

class CloudSafetyTests(unittest.TestCase):
    def test_deny_everything_by_default(self):
        r=preflight({}, "C:/Users/Dell/Desktop/youtube con")
        self.assertFalse(r.authorized)
        self.assertIn("WORKDIR_MUST_BE_ISOLATED_LINUX_CLOUD_PATH",r.missing)
        self.assertFalse(public_worker_can_publish())
    def test_only_private_worker_with_explicit_approval(self):
        vals={k:"ok" for k in (
            "FLOWMINUTE_OBJECT_STORAGE", "FLOWMINUTE_DURABLE_LEDGER",
            "FLOWMINUTE_YOUTUBE_ANALYTICS_SCOPE")}
        vals.update(FLOWMINUTE_CLOUD_DEPLOYMENT="1",FLOWMINUTE_PRIVATE_WORKER="1",
                    FLOWMINUTE_MEDIA_QA="1",FLOWMINUTE_ENABLE_PUBLISH="1",
                    FLOWMINUTE_YOUTUBE_OAUTH_SECRET_REF="render/vault/youtube1",
                    FLOWMINUTE_DAILY_SPEND_CAP_USD="0")
        self.assertTrue(preflight(vals,"/app/work").authorized)
        vals["FLOWMINUTE_ALLOW_LAPTOP"]="1"
        self.assertFalse(preflight(vals,"/app/work").authorized)
    def test_spending_and_voice_safety(self):
        validate_distinct_short_voices("af_bella","am_michael")
        with self.assertRaises(CloudGateError):
            validate_distinct_short_voices("af_bella","af_bella")
        with self.assertRaises(CloudGateError):
            require_approval_for_spend(.10,0)

if __name__=="__main__":
    unittest.main()
