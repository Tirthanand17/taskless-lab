"""RC7 opening plans and review-only report tests."""
import json,unittest
from pathlib import Path
from proof_first_rc7 import PLANS
from production_review_rc6 import CATALOG,read,sha
D=Path(__file__).resolve().parent
class ProofFirstTests(unittest.TestCase):
 def test_opening_plans(self):
  for k,plans in PLANS.items():
   c=read(CATALOG[k][0]);w,h=c["dimensions"]
   self.assertEqual(plans[0][4],0)
   self.assertEqual(plans[0][5],plans[1][4])
   self.assertLessEqual(plans[1][4],90)
   for sf,(x,y,cw,ch),title,detail,start,end in plans:
    self.assertTrue(0<=x<x+cw<=w and 0<=y<y+ch<=h)
    self.assertTrue(0<=sf<c.get("decoded_frames",c.get("frames")))
    self.assertGreater(end,start)
 def test_report(self):
  r=read("RC7_OPENING_QA.json")
  self.assertEqual(r["source_sha256"],sha(D/"proof_first_rc7.py"))
  self.assertEqual({x["pilot"] for x in r["pilots"]},set(PLANS))
  for x in r["pilots"]:
   c,p,n=[read(k) for k in CATALOG[x["pilot"]][:3]]
   self.assertEqual(x["capture_sha256"],c["capture_sha256"])
   self.assertEqual(x["prior_video_sha256"],p["mp4_sha256"])
   self.assertEqual(x["frames"],p["frames"])
   self.assertEqual(x["audio"]["decoded_samples"],p["audio_samples"])
   self.assertEqual(x["first_recorded_evidence_frame"],0)
   self.assertEqual(x["second_recorded_result_frame"],60)
   self.assertEqual(len(x["observed"]),6)
   self.assertTrue(all(z["gray_error"]<4 for z in x["observed"]))
   self.assertTrue(x["pcm_identical"] and x["full_decode_pass"])
   for field in ("continuous_live_action_verified","legacy_creative_pass","owner_approval","release_authorized"):
    self.assertIs(x[field],False)
  self.assertFalse(r["release_authorized"])
if __name__=="__main__":unittest.main()
