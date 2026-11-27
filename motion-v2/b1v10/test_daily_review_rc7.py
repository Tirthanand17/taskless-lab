"""RC7 daily-review intake regression: rejects forged or mismatched review evidence."""
import copy,hashlib,tempfile,unittest
from pathlib import Path
from production_review_rc6 import read
from daily_review_rc7 import validate_receipt,build,SCHEMA
from autopilot.branch1_recovery import RecoveryRefused
class DailyReviewTests(unittest.TestCase):
 def fixture(self,p):
  p.write_bytes(b"test-only fixture"*2400)
  return {"schema":SCHEMA,"episode_id":"fm_test_fixture","method":"windows_classic_console_window_only_live","capture_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"capture_bytes":p.stat().st_size,"dimensions":[870,494],"fps":12,"frames":72,"source_receipt_sha256":"a"*64,"fixture_only":True,"local_only":True,"release_authorized":False}
 def test_identity_not_authentication(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/"capture.mp4";r=self.fixture(p)
   self.assertFalse(validate_receipt(r,p)["known_evidence_anchor_matched"])
   self.assertTrue(validate_receipt(r,p,r)["known_evidence_anchor_matched"])
   for field,value in [("release_authorized",True),("method","xvfb_xterm_ffmpeg_live"),("fps",True),("dimensions",[870,493]),("source_receipt_sha256","bad")]:
    bad={**r,field:value}
    with self.assertRaises(RecoveryRefused):validate_receipt(bad,p)
   with self.assertRaises(RecoveryRefused):validate_receipt({**r,"frames":73},p,r)
   p.write_bytes(b"tampered"+p.read_bytes())
   with self.assertRaises(RecoveryRefused):validate_receipt(r,p)
 def rows(self):
  return {k:{"pilot":k,"format":"long" if k=="git" else "short","episode_id":"fm_"+k+"_fixture","video_sha256":str(i)*64,"technical_review_pass":True,"legacy_creative_pass":False,"release_authorized":False} for i,k in enumerate(("sha256","float","git"),1)}
 def test_daily_plan_hold(self):
  r=build("2026-11-28",self.rows())
  self.assertEqual([s["reference_local_time"] for s in r["slots"]],["11:00","16:00","20:30"])
  self.assertEqual([s["format"] for s in r["slots"]],["short","long","short"])
  self.assertEqual(r["release_ready_count"],0)
  self.assertFalse(r["auto_publish_enabled"])
  self.assertTrue(all(s["disposition"]=="HOLD_NOT_SCHEDULED" for s in r["slots"]))
 def test_duplicate_and_approval_rejected(self):
  rows=self.rows();rows["float"]["video_sha256"]=rows["sha256"]["video_sha256"]
  with self.assertRaises(RecoveryRefused):build("2026-11-28",rows)
  rows=self.rows();rows["float"]["release_authorized"]=True
  with self.assertRaises(RecoveryRefused):build("2026-11-28",rows)
 def test_actual_daily_evidence(self):
  r=read("RC7_DAILY_REVIEW_QA.json")
  self.assertEqual(r["technical_pass_count"],3)
  self.assertEqual(r["release_ready_count"],0)
  self.assertFalse(r["inventory_checked_live"])
  self.assertTrue(all(s["receipt_validation"]["known_evidence_anchor_matched"] and s["audio"]["clipped_samples"]==0 and not s["release_authorized"] for s in r["slots"]))
if __name__=="__main__":unittest.main()
