"""RC11 visual polish evidence checks."""
import unittest
from production_review_rc6 import read,sha,D
from polish_shorts_rc11 import CONFIG,diagram
class PolishShortsTests(unittest.TestCase):
 def test_layouts(self):
  for key in CONFIG:
   for i in range(7):self.assertEqual(diagram(key,i).size,(1080,1920))
 def test_exact_exports(self):
  for prefix,key,frames in (("SHARED","shared_lists",414),("GROUP","group_runs",489)):
   r=read(f"RC11_{prefix}_SHORT_QA.json");old=read(f"RC10_{prefix}_SHORT_QA.json");c=read(f"RC10_{prefix}_CAPTURE_QA.json")
   self.assertEqual(r["topic"],key)
   self.assertEqual(r["source_sha256"],sha(D/"polish_shorts_rc11.py"))
   self.assertEqual(r["prior_report_sha256"],sha(D/f"RC10_{prefix}_SHORT_QA.json"))
   self.assertEqual(r["prior_sha256"],old["mp4_sha256"]);self.assertNotEqual(r["video_sha256"],r["prior_sha256"])
   self.assertEqual(r["capture_sha256"],c["capture_sha256"])
   self.assertEqual(r["event_starts_frames"],[0]+[x["frame"]*5 for x in c["changes"]])
   self.assertTrue(all(f/30>=t-.001 for f,t in zip(r["event_starts_frames"][1:],r["actual_event_times_seconds"])))
   self.assertEqual(r["frames"],frames);self.assertEqual(r["audio"],old["audio"])
   self.assertEqual(r["resolution"],[1080,1920]);self.assertEqual(r["fps"],30)
   self.assertTrue(r["pcm_identical"] and r["full_decode_pass"])
   self.assertGreater(r["new_source_scale"],1.12*r["prior_source_scale"])
   self.assertEqual(r["caption_font_px"],58)
   self.assertEqual(len(r["source_checks"]),7);self.assertTrue(all(x["error"]<4 for x in r["source_checks"]))
   self.assertFalse(r["release_authorized"]);self.assertFalse(r["human_playback_approved"])
if __name__=="__main__":unittest.main()
