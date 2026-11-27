"""Independent cross-date audit tests and measured November 29 batch evidence."""
import copy,unittest
from audit_second_batch_rc10 import compare_history
from production_review_rc6 import read,sha,D
from autopilot.branch1_recovery import validate_creative
class SecondBatchTests(unittest.TestCase):
 def test_history_rejection(self):
  a=[{"topic":"new","video_sha256":"new-video","capture_sha256":"new-capture"}]
  b=[{"topic":"old","video_sha256":"old-video","capture_sha256":"old-capture"}]
  compare_history(a,b)
  for key in a[0]:
   x=copy.deepcopy(a);x[0][key]=b[0][key]
   with self.assertRaises(ValueError):compare_history(x,b)
  with self.assertRaises(ValueError):compare_history(a+a,b)
 def test_actual_sql(self):
  r=read("RC10_JOIN_LONG_QA.json");n=read("RC10_JOIN_NARRATION_QA.json");c=read("RC10_JOIN_CAPTURE_QA.json")
  self.assertTrue(n["all_exact_token_matches"] and r["full_decode_pass"])
  self.assertEqual(r["frames"],1840);self.assertEqual(r["audio"]["decoded_samples"],2944000)
  self.assertEqual(r["audio"]["clipped_samples"],0)
  self.assertEqual(r["resolution"],[1920,1080])
  self.assertEqual([x["result"] for x in c["events"]][-2:],[[[1,"paid"],[2,None],[3,None]],[1,3]])
  for name,h in c["source_sha256"].items():self.assertEqual(sha(D/name),h)
  for name,key in [("RC10_JOIN_CAPTURE_QA.json","capture_report_sha256"),("RC10_JOIN_NARRATION_QA.json","narration_report_sha256"),("render_rc10p2.py","render_source_sha256"),("RC10_JOIN_CREATIVE_BRIEF.json","creative_brief_sha256"),("RC10_JOIN_CAPTURE_RECEIPT.json","receipt_sha256")]:self.assertEqual(sha(D/name),r[key])
  self.assertEqual(validate_creative(read("RC10_JOIN_CREATIVE_BRIEF.json"))["status"],r["identity"]["status"])
  self.assertFalse(r["release_authorized"])
 def test_actual_batch(self):
  r=read("RC10_SECOND_BATCH_QA.json");b=read("RC10_1129_BATCH_QA.json")
  self.assertEqual(r["batch_sha256"],sha(D/"RC10_1129_BATCH_QA.json"))
  self.assertEqual(r["runner_sha256"],sha(D/"run_registered_rc10p2.py"))
  self.assertEqual(r["source_sha256"],sha(D/"audit_second_batch_rc10.py"))
  for name,h in r["prior_report_sha256"].items():self.assertEqual(sha(D/name),h)
  self.assertEqual(r["verified_stages"],9);self.assertEqual(r["fresh_media_count"],3)
  self.assertEqual(r["prior_batch_hash_overlap"],0);self.assertEqual(r["release_ready_count"],0)
  self.assertEqual([x["frames"] for x in r["slots"]],[414,1840,489])
  self.assertEqual([x["reference_local_time"] for x in r["slots"]],["11:00","16:00","20:30"])
  self.assertEqual([x["format"] for x in r["slots"]],["short","long","short"])
  for x,y,p in zip(r["slots"],b["rows"],("SHARED_SHORT","JOIN_LONG","GROUP_SHORT")):
   self.assertEqual(x["render_report_sha256"],sha(D/f"RC10_{p}_QA.json"));self.assertEqual(x["video_sha256"],y["video_sha256"])
   self.assertFalse(x["release_authorized"])
  self.assertFalse(r["live_inventory_complete"]);self.assertFalse(r["unattended_scheduler_verified"])
if __name__=="__main__":unittest.main()
