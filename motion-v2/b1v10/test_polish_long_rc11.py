"""RC11 landscape evidence and all-three polished review batch."""
import unittest
from production_review_rc6 import D,read,sha
from polish_long_rc11 import events,plate,CROP,DISPLAY
class PolishLongTests(unittest.TestCase):
 def test_layouts_and_fixture(self):
  e=events(read("RC10_JOIN_CAPTURE_QA.json"))
  self.assertEqual(e[0],[[1,"paid"]]);self.assertEqual(e[4],[[1,"paid"],[2,None],[3,None]])
  self.assertEqual(e[5],[1,3])
  for i in range(7):
   self.assertEqual(plate(i,e,14,2).size,(1920,1080))
 def test_long_media(self):
  r=read("RC11_JOIN_LONG_QA.json");old=read("RC10_JOIN_LONG_QA.json");c=read("RC10_JOIN_CAPTURE_QA.json")
  self.assertEqual(r["source_sha256"],sha(D/"polish_long_rc11.py"))
  self.assertEqual(r["design_dependency_sha256"],sha(D/"polish_shorts_rc11.py"))
  self.assertEqual(r["prior_report_sha256"],sha(D/"RC10_JOIN_LONG_QA.json"))
  self.assertEqual(r["prior_sha256"],old["mp4_sha256"]);self.assertNotEqual(r["video_sha256"],r["prior_sha256"])
  self.assertEqual(r["capture_sha256"],c["capture_sha256"])
  self.assertEqual(r["source_crop"],list(CROP));self.assertEqual(r["display_rect"],list(DISPLAY))
  self.assertEqual(r["event_starts_frames"],[0]+[x["frame"]*5 for x in c["changes"]])
  self.assertTrue(all(f/30>=t-.001 for f,t in zip(r["event_starts_frames"][1:],r["actual_event_times_seconds"])))
  self.assertEqual(r["frames"],1840);self.assertEqual(r["audio"],old["audio"])
  self.assertEqual(r["resolution"],[1920,1080]);self.assertEqual(r["fps"],30)
  self.assertTrue(r["pcm_identical"] and r["full_decode_pass"])
  self.assertGreater(r["new_source_scale"],1.4*r["prior_source_scale"])
  self.assertEqual(r["caption_font_px"],56);self.assertEqual(r["row_entrance_frames"],12)
  self.assertEqual(len(r["source_checks"]),7);self.assertTrue(all(x["error"]<4 for x in r["source_checks"]))
  self.assertFalse(r["release_authorized"]);self.assertFalse(r["human_playback_approved"])
 def test_polished_batch(self):
  r=read("RC11_POLISHED_BATCH_QA.json")
  self.assertEqual(r["original_batch_sha256"],sha(D/"RC10_SECOND_BATCH_QA.json"))
  self.assertEqual(r["audit_source_sha256"],sha(D/"audit_polish_rc11.py"))
  self.assertEqual(r["verified_frames"],2743);self.assertEqual(r["polished_count"],3)
  self.assertEqual(r["release_ready_count"],0)
  for row,prefix in zip(r["slots"],("SHARED_SHORT","JOIN_LONG","GROUP_SHORT")):
   n=f"RC11_{prefix}_QA.json";a=read(n)
   self.assertEqual(row["polish_report_sha256"],sha(D/n));self.assertEqual(row["video_sha256"],a["video_sha256"])
   self.assertTrue(row["audio_unchanged"]);self.assertFalse(row["release_authorized"])
if __name__=="__main__":unittest.main()
