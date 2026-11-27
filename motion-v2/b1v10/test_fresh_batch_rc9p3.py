"""RC9 phase 3: actual fresh batch evidence, caption correction, and release hold."""
import copy,unittest
from fresh_batch_rc9p3 import D,load,sha,build
from autopilot.branch1_recovery import validate_creative
class FreshBatchPhase3Tests(unittest.TestCase):
 def test_media_links(self):
  for prefix,key,frames,fmt in (("ZIP","zip_crc",646,"short"),("SQL","sql_null",1779,"long")):
   c=load(D/f"RC9_{prefix}_CAPTURE_QA.json");r=load(D/f"RC9_{prefix}_{fmt.upper()}_QA.json")
   n=load(D/("RC9_SQL_NARRATION_R3_QA.json" if prefix=="SQL" else "RC9_ZIP_NARRATION_QA.json"))
   self.assertEqual(c["topic"],key);self.assertTrue(c["continuous"])
   self.assertEqual(c["transient_blank_frames"],[]);self.assertLess(c["max_sample_lag_seconds"],.35)
   for name,h in c["source_sha256"].items():self.assertEqual(sha(D/name),h)
   self.assertEqual(r["capture_report_sha256"],sha(D/f"RC9_{prefix}_CAPTURE_QA.json"))
   self.assertEqual(r["narration_report_sha256"],sha(D/("RC9_SQL_NARRATION_R3_QA.json" if prefix=="SQL" else "RC9_ZIP_NARRATION_QA.json")))
   self.assertEqual(r["creative_brief_sha256"],sha(D/f"RC9_{prefix}_CREATIVE_BRIEF.json"))
   self.assertEqual(r["receipt_sha256"],sha(D/f"RC9_{prefix}_CAPTURE_RECEIPT.json"))
   self.assertEqual(r["render_source_sha256"],sha(D/("render_daily_sql_rc9p3.py" if fmt=="long" else "render_daily_rc9p3.py")))
   self.assertEqual(r["frames"],frames);self.assertEqual(r["audio"]["decoded_samples"],frames*1600)
   self.assertEqual(r["audio"]["clipped_samples"],0);self.assertTrue(r["full_decode_pass"] and n["asr_screen_pass"])
   self.assertTrue(all(x["error"]<4 for x in r["observed"]))
   self.assertEqual(validate_creative(load(D/f"RC9_{prefix}_CREATIVE_BRIEF.json"))["status"],r["identity"]["status"])
   self.assertFalse(r["release_authorized"])
 def test_sql_caption_review(self):
  r=load(D/"RC9_SQL_LONG_QA.json");c=load(D/"RC9_SQL_CAPTION_REVIEW.json");n=load(D/"RC9_SQL_NARRATION_R3_QA.json")
  self.assertEqual(r["caption_review_sha256"],sha(D/"RC9_SQL_CAPTION_REVIEW.json"))
  self.assertEqual(c["raw_caption_sha256"],n["word_captions_sha256"])
  self.assertEqual(len(c["corrections"]),1);self.assertEqual(c["corrections"][0]["to"],"blocked")
  self.assertTrue(c["corrected_tokens_match_script"]);self.assertFalse(c["human_listening_approved"])
 def test_batch(self):
  r=load(D/"RC9_FRESH_BATCH_QA.json");rows={x["topic"]:x for x in r["slots"]}
  self.assertEqual(r["fresh_video_count"],3);self.assertEqual(r["release_ready_count"],0)
  self.assertEqual([x["format"] for x in r["slots"]],["short","long","short"])
  self.assertFalse(r["unattended_generation_verified"])
  for key,prefix in [("zip_crc","ZIP_SHORT"),("sql_null","SQL_LONG"),("path_suffix","PATH_SHORT")]:
   self.assertEqual(rows[key]["render_report_sha256"],sha(D/f"RC9_{prefix}_QA.json"))
  for field,value in [("release_authorized",True),("video_sha256",rows["zip_crc"]["video_sha256"]),("capture_sha256",rows["zip_crc"]["capture_sha256"]),("technical_review_pass",False)]:
   bad=copy.deepcopy(rows);bad["path_suffix"][field]=value
   with self.assertRaises(ValueError):build("2026-11-28",bad)
if __name__=="__main__":unittest.main()
