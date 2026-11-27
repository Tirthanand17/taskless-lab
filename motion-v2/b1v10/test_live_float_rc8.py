"""RC8 actual continuous capture and unchanged creative brief contract."""
import hashlib,json,unittest,sys
from pathlib import Path
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D.parents[1]))
from autopilot.branch1_recovery import validate_creative,RecoveryRefused
def read(n):return json.loads((D/n).read_text(encoding="utf-8"))
def sha(n):return hashlib.sha256((D/n).read_bytes()).hexdigest()
class LiveFloatTests(unittest.TestCase):
 def test_capture_identity_and_events(self):
  c=read("RC8_LIVE_CAPTURE_QA.json")
  self.assertTrue(c["continuous"] and c["scripted_demo"])
  self.assertEqual(c["frames"],221)
  self.assertEqual(c["fps"],10)
  self.assertLess(c["max_sample_lag_seconds"],.35)
  self.assertEqual(len(c["capture_times_seconds"]),221)
  self.assertEqual([x["result"] for x in c["events"]],["0.30000000000000004","False","3602879701896397/36028797018963968","1/10","command shown","0.3","True"])
  for name,h in c["source_sha256"].items():self.assertEqual(sha(name),h)
 def test_exact_video_and_live_changes(self):
  c=read("RC8_LIVE_CAPTURE_QA.json");r=read("RC8_LIVE_SHORT_QA.json")
  self.assertEqual(r["capture_sha256"],c["capture_sha256"])
  self.assertEqual(r["capture_report_sha256"],sha("RC8_LIVE_CAPTURE_QA.json"))
  self.assertEqual(r["source_sha256"],sha("render_live_float_rc8.py"))
  self.assertEqual(r["frames"],661)
  self.assertEqual(r["audio"]["decoded_samples"],661*1600)
  self.assertTrue(r["full_decode_pass"] and r["pcm_identical"])
  self.assertEqual(len(r["observed"]),9)
  self.assertTrue(all(x["error"]<4 for x in r["observed"]))
  self.assertLessEqual(r["actual_changes"][0]["seconds"],2)
  self.assertTrue(any(1.5<=x["seconds"]<=3 for x in r["actual_changes"]))
 def test_legacy_brief_but_no_release(self):
  b=read("RC8_CREATIVE_BRIEF.json");r=read("RC8_LIVE_SHORT_QA.json")
  self.assertEqual(r["creative_brief_sha256"],sha("RC8_CREATIVE_BRIEF.json"))
  self.assertEqual(validate_creative(b),r["creative_schema_result"])
  self.assertEqual([x["role"] for x in b["beats"]],["hook","demonstration","cause","fix","payoff","takeaway"])
  self.assertFalse(r["legacy_capture_receipt_compatible"])
  self.assertFalse(r["human_playback_approved"])
  self.assertFalse(r["release_authorized"])
if __name__=="__main__":unittest.main()
