"""RC9 phase 2: bind actual fresh media and narration artifacts to the topic handoff."""
import unittest
from daily_topics_rc9 import D,load,sha
from production_review_rc6 import validate_creative
class FreshMediaTests(unittest.TestCase):
 def test_narration_receipts(self):
  r=load(D/"RC9_TOPIC_RESEARCH_QA.json")
  by={t["id"]:t for t in r["topics"]}
  for key,name,passed in [("zip_crc","ZIP",True),("path_suffix","PATH",True),("sql_null","SQL",False)]:
   n=load(D/f"RC9_{name}_NARRATION_QA.json")
   self.assertEqual(n["spec_sha256"],by[key]["narration_spec_sha256"])
   self.assertEqual(n["script_sha256"],sha(D/"narration_daily_rc9.py"))
   self.assertEqual(n["voice"],"af_heart")
   self.assertEqual(n["samples"],n["frames_at_30fps"]*1600)
   self.assertEqual(n["asr_screen_pass"],passed)
   self.assertFalse(n["release_authorized"])
 def test_actual_short(self):
  c=load(D/"RC9_PATH_CAPTURE_QA.json");r=load(D/"RC9_PATH_SHORT_QA.json")
  self.assertEqual(r["capture_report_sha256"],sha(D/"RC9_PATH_CAPTURE_QA.json"))
  self.assertEqual(r["narration_report_sha256"],sha(D/"RC9_PATH_NARRATION_QA.json"))
  self.assertEqual(r["render_source_sha256"],sha(D/"render_daily_rc9.py"))
  self.assertEqual(r["creative_brief_sha256"],sha(D/"RC9_PATH_CREATIVE_BRIEF.json"))
  self.assertEqual(r["receipt_sha256"],sha(D/"RC9_PATH_CAPTURE_RECEIPT.json"))
  self.assertEqual(r["capture_sha256"],c["capture_sha256"])
  for name,digest in c["source_sha256"].items():self.assertEqual(sha(D/name),digest)
  self.assertEqual(r["frames"],659);self.assertEqual(r["audio"]["decoded_samples"],1054400)
  self.assertEqual(r["audio"]["clipped_samples"],0);self.assertTrue(r["full_decode_pass"])
  self.assertEqual(r["resolution"],[1080,1920]);self.assertEqual(r["fps"],30)
  self.assertEqual(len(r["observed"]),10)
  self.assertTrue(all(x["error"]<4 for x in r["observed"]))
  self.assertLessEqual(r["opening_changes"][0]["seconds"],2)
  self.assertTrue(any(1.5<=x["seconds"]<=3 for x in r["opening_changes"]))
  self.assertEqual(validate_creative(load(D/"RC9_PATH_CREATIVE_BRIEF.json"))["status"],r["identity"]["status"])
  self.assertFalse(r["identity"]["provenance_authenticated"]);self.assertFalse(r["release_authorized"])
if __name__=="__main__":unittest.main()
