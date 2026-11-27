"""RC10 phase 2: new dates, actual experiments, and exact first Short evidence."""
import unittest
from topic_registry_rc10 import topics,experiment,REGISTRY,D
from run_registered_rc10p2 import command
from production_review_rc6 import read,sha
from pathlib import Path
class RegistryTests(unittest.TestCase):
 def test_dates(self):
  t=topics("2026-11-29")
  self.assertEqual([x["format"] for x in t],["short","long","short"])
  with self.assertRaises(ValueError):topics("2026-11-30")
  for x in t:
   for stage in ("audio","capture","render"):
    self.assertTrue((D/command(stage,Path("fixture"),x["id"],"2026-11-29",Path("assets"),"ffmpeg")[0]).is_file())
 def test_actual_experiments(self):
  a=experiment("shared_lists");self.assertTrue(a["shared"] and a["independent"])
  self.assertEqual(a["after"],{"a":["item"],"b":[]})
  b=experiment("outer_join_filter");self.assertEqual(b["after"],[[1,"paid"],[2,None],[3,None]])
  c=experiment("group_runs");self.assertEqual((len(c["before"]),len(c["after"])),(3,2))
 def test_topic_evidence(self):
  r=read("RC10_1129_TOPIC_QA.json")
  self.assertEqual(r["bank_sha256"],sha(D/REGISTRY["2026-11-29"]))
  self.assertEqual(r["duplicate_flags"],0);self.assertFalse(r["live_inventory_complete"])
  for t in r["topics"]:self.assertEqual(t["experiment"],experiment(t["topic"]))
 def test_actual_short(self):
  c=read("RC10_SHARED_CAPTURE_QA.json");r=read("RC10_SHARED_SHORT_QA.json");n=read("RC10_SHARED_NARRATION_QA.json")
  for name,h in c["source_sha256"].items():self.assertEqual(sha(D/name),h)
  self.assertEqual(r["capture_report_sha256"],sha(D/"RC10_SHARED_CAPTURE_QA.json"))
  self.assertEqual(r["narration_report_sha256"],sha(D/"RC10_SHARED_NARRATION_QA.json"))
  self.assertEqual(r["render_source_sha256"],sha(D/"render_rc10p2.py"))
  self.assertEqual(r["creative_brief_sha256"],sha(D/"RC10_SHARED_CREATIVE_BRIEF.json"))
  self.assertEqual(r["receipt_sha256"],sha(D/"RC10_SHARED_CAPTURE_RECEIPT.json"))
  self.assertEqual(r["frames"],414);self.assertEqual(r["audio"]["decoded_samples"],414*1600)
  self.assertTrue(n["all_exact_token_matches"] and r["full_decode_pass"])
  self.assertLessEqual(r["opening_changes"][0]["seconds"],2)
  self.assertFalse(r["release_authorized"])
 def test_generated_group_short(self):
  c=read("RC10_GROUP_CAPTURE_QA.json");r=read("RC10_GROUP_SHORT_QA.json");n=read("RC10_GROUP_NARRATION_QA.json");b=read("RC10_GROUP_RUN_QA.json")
  for name,h in c["source_sha256"].items():self.assertEqual(sha(D/name),h)
  for name,key in [("RC10_GROUP_CAPTURE_QA.json","capture_report_sha256"),("RC10_GROUP_NARRATION_QA.json","narration_report_sha256"),("render_rc10p2.py","render_source_sha256"),("RC10_GROUP_CREATIVE_BRIEF.json","creative_brief_sha256"),("RC10_GROUP_CAPTURE_RECEIPT.json","receipt_sha256")]:self.assertEqual(sha(D/name),r[key])
  self.assertEqual(r["frames"],489);self.assertEqual(r["audio"]["decoded_samples"],489*1600)
  self.assertTrue(n["all_exact_token_matches"] and r["full_decode_pass"])
  self.assertEqual(b["rows"][0]["render_report_sha256"],sha(D/"RC10_GROUP_SHORT_QA.json"))
  self.assertFalse(b["release_authorized"])
if __name__=="__main__":unittest.main()
