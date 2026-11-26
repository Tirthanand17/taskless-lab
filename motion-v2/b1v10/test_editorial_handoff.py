import copy
import unittest
from pathlib import Path
from editorial_handoff import build, read, demo_result, inventory
ROOT=Path(__file__).resolve().parent
class EditorialTest(unittest.TestCase):
    def setUp(self):
        self.d=read(ROOT/"editorial_fixture.json")
    def test_three_distinct(self):
        r=build(self.d,[],0)
        self.assertEqual([x["format"] for x in r["selected"]],["short","long","short"])
        self.assertEqual(len({x["family"] for x in r["selected"]}),3)
        self.assertFalse(r["release_authorized"])
        for x in r["selected"]:
            self.assertEqual(x["scenes"][-1]["end"],x["duration_seconds"])
            self.assertEqual(x["scenes"][0]["start"],0)
    def test_duplicate_history(self):
        r=build(self.d,[self.d["candidates"][0]["title"]],1)
        self.assertEqual(r["unfilled_slots"],1)
        self.assertEqual(len(r["rejected"]),1)
    def test_duplicate_family(self):
        self.d["candidates"][0]["family"]=self.d["candidates"][2]["family"]
        self.assertEqual(build(self.d,[],0)["unfilled_slots"],1)
    def test_stale_source(self):
        self.d["candidates"][0]["source"]["checked"]="2026-01-01"
        with self.assertRaises(ValueError): build(self.d,[],0)
    def test_fake_approval(self):
        self.d["release_authorized"]=True
        with self.assertRaises(ValueError): build(self.d,[],0)
    def test_bad_claim(self):
        self.d["candidates"][0]["scenes"][0]["claim_ids"]=["unknown"]
        with self.assertRaises(ValueError): build(self.d,[],0)
    def test_bad_score(self):
        self.d["candidates"][0]["scores"]["payoff"]=6
        with self.assertRaises(ValueError): build(self.d,[],0)
    def test_missing_early_proof(self):
        self.d["candidates"][0]["scenes"][1]["role"]="explain"
        with self.assertRaises(ValueError): build(self.d,[],0)
    def test_demo(self):
        self.assertEqual(demo_result("float")["decimal_result"],"0.3")
        self.assertEqual(demo_result("float")["float_result"],"0.30000000000000004")
        r=demo_result("sha256"); self.assertNotEqual(r["sha256_a"],r["sha256_b"])
        self.assertEqual(demo_result("bisect")["first_bad"],11)
    def test_no_history(self):
        with self.assertRaises(ValueError): inventory(ROOT)
if __name__=="__main__": unittest.main()
