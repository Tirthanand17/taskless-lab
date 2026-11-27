"""RC9 batch evidence and fail-closed review slots."""
import copy,unittest
from production_review_rc6 import read,sha,D,RecoveryRefused
from review_batch_rc9 import PILOTS,build
class RC9BatchTests(unittest.TestCase):
 def test_measured_batch(self):
  r=read("RC9_BATCH_QA.json")
  self.assertEqual(r["technical_pass_count"],3)
  self.assertEqual(r["structured_creative_pass_count"],3)
  self.assertEqual(r["release_ready_count"],0)
  self.assertFalse(r["auto_publish_enabled"])
  self.assertEqual([s["reference_local_time"] for s in r["slots"]],["11:00","16:00","20:30"])
  for x in r["slots"]:
   c,f,b,*_=PILOTS[x["pilot"]]
   self.assertEqual(x["capture_report_sha256"],sha(D/c))
   self.assertEqual(x["render_report_sha256"],sha(D/f))
   self.assertEqual(x["creative_brief_sha256"],sha(D/b))
   self.assertEqual(x["capture_decoded_frames"],read(c)["frames"])
   self.assertEqual(x["final_decoded_frames"],read(f)["frames"])
   self.assertEqual(x["audio"]["clipped_samples"],0)
   self.assertFalse(x["identity"]["provenance_authenticated"])
   self.assertFalse(x["release_authorized"])
   self.assertTrue(x["publisher_unsigned_rejected"])
 def test_hold_rejects_duplicate_and_spoof(self):
  rows={s["pilot"]:s for s in read("RC9_BATCH_QA.json")["slots"]}
  for k,v in [("release_authorized",True),("technical_review_pass",False),("publisher_unsigned_rejected",False),("video_sha256",rows["sha256"]["video_sha256"])]:
   bad=copy.deepcopy(rows);bad["float"][k]=v
   with self.assertRaises(RecoveryRefused):build("2026-11-28",bad)
if __name__=="__main__":unittest.main()
