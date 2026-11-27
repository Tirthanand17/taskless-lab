"""RC12 generic runner: selection identity and interruption guards."""
import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import run_generic_rc12 as q
class GenericRunnerTests(unittest.TestCase):
 def test_lock_collision(self):
  with tempfile.TemporaryDirectory() as t:
   w=Path(t)/"work";lock=w.with_name(w.name+".rc12p3-lock");lock.mkdir()
   with self.assertRaises(FileExistsError):q.run("2026-11-30",w,w,w,"ffmpeg")
   self.assertTrue(lock.exists())
 def test_wrong_selection_date(self):
  with tempfile.TemporaryDirectory() as t:
   w=Path(t);q.save(w/"SELECTION_QA.json",q.load(q.D/"RC12_1130_SELECTION_QA.json"))
   with self.assertRaises(ValueError):q.selection(w,"2026-12-01")
 def test_partial_stage(self):
  with tempfile.TemporaryDirectory() as t:
   w=Path(t)/"work";w.mkdir();q.save(w/"SELECTION_QA.json",{})
   rows=q.load(q.D/"RC12_1130_SELECTION_QA.json")["selected"]
   f=w/rows[0]["topic"];f.mkdir();(f/"audio").mkdir()
   with patch.object(q,"selection",return_value=rows):
    with self.assertRaises(ValueError):q.run("2026-11-30",w,w,w,"ffmpeg")
   self.assertTrue((f/"audio").exists())
   self.assertFalse((w/"GENERIC_BATCH_QA.json").exists())
   self.assertFalse(w.with_name(w.name+".rc12p3-lock").exists())
 def test_interruption_recorded(self):
  with tempfile.TemporaryDirectory() as t:
   w=Path(t)/"work";w.mkdir();q.save(w/"SELECTION_QA.json",{})
   rows=q.load(q.D/"RC12_1130_SELECTION_QA.json")["selected"]
   f=w/rows[0]["topic"];f.mkdir()
   def fail(*a,**k):
    (f/"audio").mkdir();raise RuntimeError("interrupted")
   with patch.object(q,"selection",return_value=rows),patch.object(q.subprocess,"run",side_effect=fail):
    with self.assertRaises(RuntimeError):q.run("2026-11-30",w,w,w,"ffmpeg")
    self.assertEqual(q.load(w/"RUN_GENERIC_STATE.json")["stages"][rows[0]["topic"]+"/audio"]["status"],"FAILED")
    with self.assertRaises(ValueError):q.run("2026-11-30",w,w,w,"ffmpeg")
 def test_revision_preserves_experiment(self):
  from revise_narration_rc12 import revised
  from select_topics_rc12 import steps
  from run_daily_rc10 import spec
  bank=q.load(q.D/q.BANK)
  for key in ("bounded_deque","count_missing"):
   base=next(t for t in bank if t["id"]==key)
   t={**base,"scenes":[[r,h,v,"Inspect result."] for r,h,v in zip(("hook","demonstration","cause","fix","payoff","takeaway"),base["head"],base["spoken"])]}
   new=revised(t)
   self.assertEqual(steps(t),steps(new))
   self.assertEqual({k:v for k,v in t.items() if k!="scenes"},{k:v for k,v in new.items() if k!="scenes"})
   self.assertNotEqual(spec(t),spec(new))
 def test_actual_revision_receipts(self):
  for key,pre in (("bounded_deque","DEQUE"),("count_missing","COUNT")):
   r=q.load(q.D/f"RC12_{pre}_REVISION_QA.json")
   self.assertEqual(r["topic"],key)
   self.assertEqual(r["selection_sha256"],q.sha(q.D/"RC12_1130_SELECTION_QA.json"))
   self.assertEqual(r["revision_source_sha256"],q.sha(q.D/"revise_narration_rc12.py"))
   self.assertFalse(r["release_authorized"])
   original=next(x for x in q.load(q.D/"RC12_1130_SELECTION_QA.json")["selected"] if x["topic"]==key)
   self.assertEqual(r["original_topic_sha256"],original["topic_sha256"])
   self.assertEqual(r["original_spec_sha256"],original["spec_sha256"])
 def test_rejected_narration(self):
  r=q.load(q.D/"RC12_DEQUE_REJECTED_NARRATION_QA.json")
  self.assertFalse(r["asr_screen_pass"])
  self.assertFalse(r["release_authorized"])
  self.assertEqual(r["spec_sha256"],q.load(q.D/"RC12_DEQUE_REVISION_QA.json")["original_spec_sha256"])
 def test_actual_batch(self):
  r=q.load(q.D/"RC12_GENERIC_BATCH_QA.json")
  self.assertEqual(r["runner_sha256"],q.sha(q.D/"run_generic_rc12.py"))
  self.assertEqual(r["selection_sha256"],q.sha(q.D/"RC12_1130_SELECTION_QA.json"))
  self.assertEqual(r["verified_stages"],9)
  self.assertEqual([x["frames"] for x in r["slots"]],[415,1416,396])
  self.assertEqual(list(r["execution_modes"].values()).count("generated"),6)
  self.assertEqual(r["release_ready_count"],0)
  for key,pre,fmt in (("count_missing","COUNT","LONG"),("bounded_deque","DEQUE","SHORT")):
   self.assertEqual(r["revisions"][key],q.sha(q.D/f"RC12_{pre}_REVISION_QA.json"))
   v=q.load(q.D/f"RC12_{pre}_{fmt}_QA.json");n=q.load(q.D/f"RC12_{pre}_NARRATION_QA.json");c=q.load(q.D/f"RC12_{pre}_CAPTURE_QA.json")
   self.assertTrue(n["all_exact_token_matches"] and v["full_decode_pass"])
   self.assertEqual(v["audio"]["decoded_samples"],v["frames"]*1600)
   self.assertEqual(v["audio"]["clipped_samples"],0)
   self.assertEqual(c["transient_blank_frames"],[])
   for name,digest in c["source_sha256"].items():self.assertEqual(q.sha(q.D/name),digest)
   for name,k in [(f"RC12_{pre}_CAPTURE_QA.json","capture_report_sha256"),(f"RC12_{pre}_NARRATION_QA.json","narration_report_sha256"),(f"RC12_{pre}_CREATIVE_BRIEF.json","creative_brief_sha256"),(f"RC12_{pre}_CAPTURE_RECEIPT.json","receipt_sha256"),("render_generic_rc12.py","render_source_sha256")]:self.assertEqual(q.sha(q.D/name),v[k])
   self.assertTrue(all(x["error"]<4 for x in v["observed"]))
  for x,pre in zip(r["slots"],("STRIP_SHORT","COUNT_LONG","DEQUE_SHORT")):
   self.assertEqual(x["render_report_sha256"],q.sha(q.D/f"RC12_{pre}_QA.json"))
   self.assertFalse(x["release_authorized"])
if __name__=="__main__":unittest.main()
