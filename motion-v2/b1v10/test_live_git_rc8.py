"""RC8 long continuous capture, exact repair and unchanged creative contract."""
import hashlib,json,unittest,sys
from pathlib import Path
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D.parents[1]))
from autopilot.branch1_recovery import validate_creative
def read(n):return json.loads((D/n).read_text(encoding="utf-8"))
def sha(n):return hashlib.sha256((D/n).read_bytes()).hexdigest()
class LiveGitTests(unittest.TestCase):
 def test_actual_repair(self):
  c=read("RC8_GIT_CAPTURE_QA.json");old=read("GIT_BISECT_DEMO.json");e=c["events"]
  self.assertTrue(c["continuous"] and c["scripted_demo"])
  self.assertEqual((c["frames"],c["fps"]),(672,6))
  self.assertEqual(len(c["capture_times_seconds"]),672)
  self.assertLess(c["max_sample_lag_seconds"],.35)
  self.assertEqual(c["original_evidence_sha256"],sha("GIT_BISECT_DEMO.json"))
  self.assertEqual(e["commits"],old["commits"])
  self.assertEqual(e["first_bad_commit"],old["first_bad_commit"])
  self.assertEqual([s["revision"] for s in e["steps"]],[7,11,9,10])
  self.assertEqual([s["classification"] for s in e["steps"]],["good","bad","good","good"])
  self.assertTrue(e["reset_completed"])
  self.assertEqual(e["repair_test_exit"],0)
  for n,h in c["source_sha256"].items():self.assertEqual(sha(n),h)
 def test_media(self):
  c=read("RC8_GIT_CAPTURE_QA.json");r=read("RC8_GIT_LONG_QA.json")
  self.assertEqual(r["capture_sha256"],c["capture_sha256"])
  self.assertEqual(r["capture_report_sha256"],sha("RC8_GIT_CAPTURE_QA.json"))
  self.assertEqual(r["source_sha256"],sha("render_live_git_rc8.py"))
  self.assertEqual(r["frames"],3360)
  self.assertEqual(r["audio"]["decoded_samples"],5376000)
  self.assertEqual(r["audio"]["clipped_samples"],0)
  self.assertTrue(r["pcm_identical"] and r["full_decode_pass"])
  self.assertEqual(len(r["observed"]),14)
  self.assertTrue(all(x["error"]<4 for x in r["observed"]))
  self.assertLessEqual(r["opening_changes"][0]["seconds"],2)
  self.assertTrue(any(1.5<=x["seconds"]<=3 for x in r["opening_changes"]))
  ev={x["id"]:x["actual_seconds"] for x in c["events"]["events"]}
  for p in r["note_panels"]:
   if p["event"]:self.assertGreaterEqual(p["start_frame"]/30,ev[p["event"]])
 def test_creative_review_only(self):
  r=read("RC8_GIT_LONG_QA.json");b=read("RC8_GIT_CREATIVE_BRIEF.json")
  self.assertEqual(r["creative_brief_sha256"],sha("RC8_GIT_CREATIVE_BRIEF.json"))
  self.assertEqual(validate_creative(b),r["creative_schema_result"])
  self.assertEqual([x["role"] for x in b["beats"]],["hook","demonstration","cause","fix","payoff","takeaway"])
  self.assertEqual(r["repair_test_exit"],0)
  for key in ("legacy_capture_receipt_compatible","human_playback_approved","release_authorized"):self.assertFalse(r[key])
if __name__=="__main__":unittest.main()
