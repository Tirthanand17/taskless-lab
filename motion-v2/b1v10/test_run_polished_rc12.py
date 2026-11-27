"""RC12 integration, review-only output, and interruption guards."""
import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import run_polished_rc12 as q
class PolishedRunnerTests(unittest.TestCase):
 def test_date_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/"new"
   with self.assertRaises(ValueError):q.run("2026-11-30",root,root,root,"ffmpeg")
   self.assertFalse(root.exists())
 def test_lock(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/"new";lock=root.with_name("new.rc12-lock");lock.mkdir()
   with self.assertRaises(FileExistsError):q.run("2026-11-29",root,root,root,"ffmpeg")
   self.assertTrue(lock.exists())
 def test_failure_preserves_partial(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/"workspace";root.mkdir();(root/"BATCH_QA.json").write_text("{}")
   for topic in q.topics("2026-11-29"):(root/topic["id"]).mkdir()
   def fail(*a,**k):
    (root/"shared_lists"/"polish-rc12").mkdir()
    raise RuntimeError("test interruption")
   with patch.object(q,"base_run",return_value={"all_three_complete":True,"release_authorized":False}),patch.object(q.subprocess,"run",side_effect=fail):
    with self.assertRaises(RuntimeError):q.run("2026-11-29",root,root,root,"ffmpeg")
    self.assertTrue((root/"shared_lists"/"polish-rc12").exists())
    self.assertFalse((root/".run-lock").exists())
    self.assertFalse(root.with_name("workspace.rc12-lock").exists())
    with self.assertRaises(ValueError):q.run("2026-11-29",root,root,root,"ffmpeg")
    self.assertFalse((root/"RC12_REVIEW_QA.json").exists())
 def test_actual_batch(self):
  r=q.read("RC12_REVIEW_QA.json")
  self.assertEqual(r["runner_sha256"],q.sha(q.D/"run_polished_rc12.py"))
  self.assertEqual(r["base_batch_sha256"],q.sha(q.D/"RC10_1129_BATCH_QA.json"))
  self.assertEqual(r["polished_count"],3);self.assertEqual(r["verified_frames"],2743)
  self.assertEqual(r["release_ready_count"],0)
  self.assertFalse(r["scheduler_verified"]);self.assertFalse(r["live_inventory_complete"])
  self.assertEqual([x["mode"] for x in r["slots"]],["generated","adopted_exact_rc11","adopted_exact_rc11"])
  for x,p in zip(r["slots"],("RC12_SHARED_SHORT_QA.json","RC11_JOIN_LONG_QA.json","RC11_GROUP_SHORT_QA.json")):
   self.assertEqual(x["polish_report_sha256"],q.sha(q.D/p))
   self.assertEqual(x["video_sha256"],q.read(p)["video_sha256"])
   self.assertNotEqual(x["video_sha256"],x["base_video_sha256"])
   self.assertIn("/polish-rc12/",x["video_relative_path"])
   self.assertFalse(x["release_authorized"])
if __name__=="__main__":unittest.main()
