"""RC8 SHA continuous capture evidence and review-only policy checks."""
import hashlib,json,unittest,sys
from pathlib import Path
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D.parents[1]))
from autopilot.branch1_recovery import validate_creative
def read(n):return json.loads((D/n).read_text(encoding="utf-8"))
def sha(n):return hashlib.sha256((D/n).read_bytes()).hexdigest()
class LiveShaTests(unittest.TestCase):
 def test_actual_capture(self):
  c=read("RC8_SHA_CAPTURE_QA.json")
  a,b=[hashlib.sha256(v).hexdigest() for v in (b"A",b"B")]
  self.assertTrue(c["continuous"] and c["scripted_demo"])
  self.assertEqual((c["frames"],c["fps"]),(194,10))
  self.assertEqual(len(c["capture_times_seconds"]),194)
  self.assertLess(c["max_sample_lag_seconds"],.35)
  ev={x["id"]:x["result"] for x in c["events"]}
  self.assertEqual(ev["preview"],[a,b])
  self.assertEqual(ev["hashes"],[a,b])
  self.assertEqual(ev["trusted_reference"],a)
  self.assertEqual(ev["comparison"],[True,False])
  for n,h in c["source_sha256"].items():self.assertEqual(sha(n),h)
 def test_final_media(self):
  c=read("RC8_SHA_CAPTURE_QA.json");r=read("RC8_SHA_SHORT_QA.json")
  self.assertEqual(r["capture_sha256"],c["capture_sha256"])
  self.assertEqual(r["capture_report_sha256"],sha("RC8_SHA_CAPTURE_QA.json"))
  self.assertEqual(r["source_sha256"],sha("render_live_sha_rc8.py"))
  self.assertEqual(r["frames"],581)
  self.assertEqual(r["audio"]["decoded_samples"],929600)
  self.assertEqual(r["audio"]["clipped_samples"],0)
  self.assertTrue(r["pcm_identical"] and r["full_decode_pass"])
  self.assertEqual(len(r["observed"]),9)
  self.assertTrue(all(x["error"]<4 for x in r["observed"]))
  self.assertLessEqual(r["actual_changes"][0]["seconds"],2)
  self.assertTrue(any(1.5<=x["seconds"]<=3 for x in r["actual_changes"]))
 def test_creative_and_release_fence(self):
  r=read("RC8_SHA_SHORT_QA.json");b=read("RC8_SHA_CREATIVE_BRIEF.json")
  self.assertEqual(r["creative_brief_sha256"],sha("RC8_SHA_CREATIVE_BRIEF.json"))
  self.assertEqual(validate_creative(b),r["creative_schema_result"])
  self.assertEqual([x["role"] for x in b["beats"]],["hook","demonstration","cause","fix","payoff","takeaway"])
  for key in ("legacy_capture_receipt_compatible","human_playback_approved","release_authorized"):self.assertFalse(r[key])
if __name__=="__main__":unittest.main()
