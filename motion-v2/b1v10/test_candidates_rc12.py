"""RC12 candidate selection, evidence and shared render layout tests."""
import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from select_topics_rc12 import D,BANK,load,sha,steps,select,prepare,validate
from render_generic_rc12 import plate
class CandidateTests(unittest.TestCase):
 def test_fixtures_and_layouts(self):
  bank=load(D/BANK)
  for t in bank:
   self.assertEqual(len(validate(t)),6)
   for i in range(7):self.assertEqual(plate(t,i,steps(t)).size,(1920,1080) if t["format"]=="long" else (1080,1920))
  self.assertEqual(steps(bank[0])[4]["result"],["","ab"])
  self.assertEqual(steps(bank[4])[4]["result"],[4,2,2])
 def test_selection_history(self):
  bank=load(D/BANK);first,_=select(bank,[],set())
  reserved={x["id"] for x in first}
  second,_=select(bank,[],reserved)
  self.assertFalse(reserved&{x["id"] for x in second})
  with self.assertRaises(ValueError):select(bank,[],{x["id"] for x in bank})
  with self.assertRaises(ValueError):select(bank+bank,[],set())
  bad=copy.deepcopy(bank[0]);bad["op"]="exec"
  with self.assertRaises(ValueError):validate(bad)
 def test_missing_prior_receipt(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);out=p/"new"
   with patch("select_topics_rc12.inventory",return_value=([("","unrelated")],0)):
    with self.assertRaises(ValueError):prepare("2026-12-01",p,out,[])
    self.assertFalse(out.exists())
 def test_actual_selections(self):
  a=load(D/"RC12_1130_SELECTION_QA.json");b=load(D/"RC12_1201_SELECTION_QA.json")
  self.assertEqual(a["history_rows"],191)
  for r in (a,b):
   self.assertEqual(r["source_sha256"],sha(D/"select_topics_rc12.py"));self.assertEqual(r["bank_sha256"],sha(D/BANK))
   self.assertEqual([x["format"] for x in r["selected"]],["short","long","short"])
   self.assertFalse(r["live_inventory_complete"]);self.assertFalse(r["release_authorized"])
   for x in r["selected"]:self.assertEqual(x["experiment"],steps(next(t for t in load(D/BANK) if t["id"]==x["topic"])))
  self.assertFalse({x["topic"] for x in a["selected"]}&{x["topic"] for x in b["selected"]})
 def test_actual_capture(self):
  n=load(D/"RC12_STRIP_NARRATION_QA.json");c=load(D/"RC12_STRIP_CAPTURE_QA.json")
  self.assertTrue(n["all_exact_token_matches"]);self.assertEqual(n["frames_at_30fps"],415)
  self.assertEqual(c["narration_report_sha256"],sha(D/"RC12_STRIP_NARRATION_QA.json"))
  self.assertEqual(c["frames"],83);self.assertEqual(c["transient_blank_frames"],[])
  self.assertLess(c["max_sample_lag_seconds"],.35)
  self.assertEqual([e["result"] for e in c["events"]],[x["result"] for x in steps(load(D/BANK)[0])])
  for name,h in c["source_sha256"].items():self.assertEqual(sha(D/name),h)
  self.assertFalse(c["release_authorized"])
 def test_actual_render(self):
  r=load(D/"RC12_STRIP_SHORT_QA.json");c=load(D/"RC12_STRIP_CAPTURE_QA.json")
  for n,k in [("render_generic_rc12.py","render_source_sha256"),("RC12_STRIP_CAPTURE_QA.json","capture_report_sha256"),("RC12_STRIP_NARRATION_QA.json","narration_report_sha256"),("RC12_STRIP_CREATIVE_BRIEF.json","creative_brief_sha256"),("RC12_STRIP_CAPTURE_RECEIPT.json","receipt_sha256")]:self.assertEqual(sha(D/n),r[k])
  self.assertEqual(r["capture_sha256"],c["capture_sha256"])
  self.assertEqual(r["frames"],415);self.assertEqual(r["audio"]["decoded_samples"],664000)
  self.assertEqual(r["audio"]["clipped_samples"],0);self.assertTrue(r["full_decode_pass"])
  self.assertEqual(len(r["observed"]),10);self.assertTrue(all(x["error"]<4 for x in r["observed"]))
  self.assertFalse(r["release_authorized"])
if __name__=="__main__":unittest.main()
