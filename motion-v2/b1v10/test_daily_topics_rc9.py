"""Fresh topic intake tests: deterministic fixtures, historical duplicate fence, no release."""
import json,tempfile,unittest
from pathlib import Path
from daily_topics_rc9 import D,duplicate,experiment,inventory,load,sha,screen_topics
class DailyTopicsTests(unittest.TestCase):
 def test_real_fixtures(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   z=experiment("zip_crc",root/"zip");s=experiment("sql_null",root/"sql");p=experiment("path_suffix",root/"path")
   self.assertEqual(z["broken_testzip"],"note.txt");self.assertIsNone(z["intact_testzip"])
   self.assertEqual(s["not_in"],[]);self.assertEqual(s["not_exists"],[[1],[3],[4]])
   self.assertEqual(s["outer_null_included"],[[None],[1],[3],[4]])
   self.assertEqual(p["exists_after_with_suffix"],[True,False]);self.assertEqual(p["exists_after_rename"],[False,True])
   self.assertEqual(p["content_sha256_before"],p["content_sha256_after"])
 def test_duplicate_fence(self):
  topics=load(D/"RC9_TOPIC_BANK.json")
  for t in topics:
   self.assertEqual(duplicate(t,[("", "unrelated topic")]),0)
   self.assertEqual(duplicate(t,[("",t["title"].lower())]),1)
   with self.assertRaises(ValueError):screen_topics([t],[("",t["aliases"][0].replace("_"," "))])
 def test_historical_evidence(self):
  r=load(D/"RC9_TOPIC_RESEARCH_QA.json")
  self.assertEqual(r["topic_bank_sha256"],sha(D/"RC9_TOPIC_BANK.json"))
  self.assertGreater(r["historical_manifest_rows"],0)
  self.assertEqual(r["release_ready_count"],0);self.assertFalse(r["live_title_inventory_complete"])
  self.assertEqual(len(r["topics"]),3)
  self.assertTrue(all(t["historical_duplicate_flags"]==0 and not t["release_authorized"] for t in r["topics"]))
if __name__=="__main__":unittest.main()
