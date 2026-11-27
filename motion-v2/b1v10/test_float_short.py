"""RC5: exact evidence, clock, caption provenance and release fence."""
import hashlib,json,unittest
from pathlib import Path
from narration_review import normalized
D=Path(__file__).resolve().parent
def read(n):return json.loads((D/n).read_text(encoding="utf-8"))
def sha(n):return hashlib.sha256((D/n).read_bytes()).hexdigest()
class FloatShortTests(unittest.TestCase):
 def test_actual_result(self):
  c=read("FLOAT_CAPTURE_QA.json")
  self.assertEqual(c["result"],{"float_result":"0.30000000000000004","stored_fraction":"3602879701896397/36028797018963968","decimal_result":"0.3"})
  self.assertEqual(c["frames"],72)
  for n,h in c["source_sha256"].items():self.assertEqual(sha(n),h)
 def test_clock_and_audio(self):
  r=read("FLOAT_SHORT_QA.json");n=read("FLOAT_NARRATION_QA.json")
  self.assertEqual(r["frames"],661)
  self.assertEqual(r["resolution"],[1080,1920])
  self.assertEqual(r["audio_samples"],r["frames"]*1600)
  self.assertEqual(r["audio_samples"],n["samples"])
  self.assertEqual(r["voice"],"af_heart")
  self.assertEqual(r["audio_energy"]["clipped_samples"],0)
  self.assertTrue(r["full_decode_pass"] and r["raw_asr_screen_pass"])
  self.assertEqual(r["capture_sha256"],read("FLOAT_CAPTURE_QA.json")["capture_sha256"])
  self.assertEqual(r["narration_report_sha256"],sha("FLOAT_NARRATION_QA.json"))
  self.assertEqual(r["source_sha256"],sha("render_float_short.py"))
 def test_captions_and_panels(self):
  r=read("FLOAT_SHORT_QA.json");n=read("FLOAT_NARRATION_QA.json");c=read("FLOAT_CAPTION_REVIEW.json")
  self.assertEqual(r["corrected_captions_sha256"],sha("FLOAT_CAPTION_REVIEW.json"))
  self.assertEqual(sha("FLOAT_RAW_CAPTIONS.json"),n["word_captions_sha256"])
  self.assertEqual(sha("float_narration_spec.json"),n["spec_sha256"])
  self.assertEqual(sha("float_narration.py"),n["script_sha256"])
  raw=[w for x in read("FLOAT_RAW_CAPTIONS.json") for w in x["words"]]
  fixed=[w for x in c["cues"] for w in x["words"]]
  self.assertEqual([(w["start"],w["end"]) for w in raw],[(w["start"],w["end"]) for w in fixed])
  self.assertEqual(normalized(" ".join(w["word"] for w in fixed)),normalized(" ".join(s["expected"] for s in n["scene_timeline"])))
  self.assertEqual(len(r["observed_crops"]),3)
  self.assertTrue(all(x["error"]<4 for x in r["observed_crops"]))
  self.assertTrue(all(e["sample"]==e["frame"]*1600 for e in r["events"]))
 def test_review_fence(self):
  self.assertFalse(read("FLOAT_SHORT_QA.json")["release_authorized"])
  self.assertFalse(read("FLOAT_SHORT_QA.json")["human_playback_approved"])
  self.assertFalse(read("FLOAT_CAPTURE_QA.json")["legacy_xvfb_receipt_compatible"])
if __name__=="__main__":unittest.main()
