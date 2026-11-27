"""RC10 orchestration, restart and fail-closed tests."""
import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import run_daily_rc10 as q
class DailyRunnerTests(unittest.TestCase):
 def test_seed_syntax(self):
  self.assertEqual(q.parse_seeds(["zip_crc=audio","sql_null=render"]),{"zip_crc":0,"sql_null":2})
  for bad in (["zip_crc=bad"],["other=audio"],["zip_crc=audio","zip_crc=render"]):
   with self.assertRaises(ValueError):q.parse_seeds(bad)
 def test_commands_and_specs(self):
  for k,t in q.catalog().items():
   self.assertEqual(q.spec(t)["candidate_id"],k)
   self.assertEqual(len(q.spec(t)["scenes"]),6)
   for stage in q.STAGES:
    cmd=q.command(stage,k,Path("fixture"),Path("assets"),"ffmpeg")
    self.assertTrue((q.D/cmd[0]).is_file())
    self.assertNotIn("publish",str(cmd))
  self.assertEqual(q.command("render","sql_null",Path("fixture"),Path("assets"),"ffmpeg")[0],"render_daily_sql_rc9p3.py")
 def test_locked_workspace(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/".run-lock").mkdir()
   with self.assertRaises(ValueError):q.run(root,root,root,"ffmpeg",None,{})
   self.assertTrue((root/".run-lock").exists())
 def test_failed_stage_and_quarantine(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);work=root/"run"
   def fail(*args,**kw):
    (work/"zip_crc/audio").mkdir()
    raise RuntimeError("fixture failure")
   with patch.object(q,"inventory",return_value=([("","unrelated")],0)),patch.object(q.subprocess,"run",side_effect=fail):
    with self.assertRaises(RuntimeError):q.run(work,root,root,"ffmpeg",None,{})
    j=q.load(work/"RUN_STATE.json")
    self.assertEqual(j["status"],"FAILED_REVIEW_HOLD")
    self.assertEqual(j["stages"]["zip_crc/audio"]["status"],"FAILED")
    self.assertFalse((work/".run-lock").exists())
    with self.assertRaises(ValueError):q.run(work,root,root,"ffmpeg",None,{})
    self.assertTrue((work/"zip_crc/audio").exists())
 def test_actual_run(self):
  r=q.load(q.D/"RC10_RUN_QA.json")
  self.assertEqual(r["orchestrator_source_sha256"],q.sha(q.D/"run_daily_rc10.py"))
  self.assertEqual(r["fresh_video_count"],3);self.assertEqual(r["release_ready_count"],0)
  self.assertEqual(len(r["execution_modes"]),9)
  self.assertEqual(r["execution_modes"]["zip_crc/capture"],"generated")
  self.assertEqual(r["execution_modes"]["zip_crc/render"],"generated")
  self.assertEqual(r["execution_modes"]["zip_crc/audio"],"adopted")
  self.assertFalse(r["unattended_generation_verified"]);self.assertFalse(r["live_inventory_complete"])
  self.assertTrue(all(x["technical_review_pass"] and not x["release_authorized"] for x in r["slots"]))
if __name__=="__main__":unittest.main()
