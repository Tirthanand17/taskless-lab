import unittest
from scripts.branch3_v3_editor_benchmark import compare


class EditorBenchmarkTests(unittest.TestCase):
    def case(self):
        return {"source_sha256":"a"*64,"duration_ms":120000,
                "labels":[[10000,30000],[60000,80000]],
                "baseline":[[10000,30000],[10000,30000],[0,2000]],
                "v3":[[10000,30000],[60000,80000]]}

    def test_same_budget_and_no_double_counting(self):
        r=compare([self.case()],2)
        self.assertEqual(r["totals"]["baseline"]["matched"],1)
        self.assertEqual(r["totals"]["v3"]["matched"],2)
        self.assertEqual(r["totals"]["v3"]["label_recall"],1)
        self.assertFalse(r["real_benchmark_accepted"])

    def test_missing_labels_not_fake_precision_or_recall(self):
        d=self.case()
        d.update(labels=[],baseline=[],v3=[])
        r=compare([d])
        self.assertIsNone(r["totals"]["v3"]["label_precision"])
        self.assertIsNone(r["totals"]["v3"]["label_recall"])

    def test_invalid_inputs_and_duplicate_episode(self):
        d=self.case()
        with self.assertRaises(ValueError):
            compare([d,d])
        for field,value in [("labels",[[0,True]]),("v3",[[10000,130000]]),
                            ("source_sha256","not-a-hash"),("api_views",[1])]:
            d=self.case();d[field]=value
            with self.assertRaises(ValueError):
                compare([d])

if __name__=="__main__":
    unittest.main()
