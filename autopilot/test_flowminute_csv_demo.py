"""Verify that the original CSV teaching demo works without external inputs."""
import unittest
from autopilot.examples.flowminute_csv_demo import (
    demonstrate_csv_total, COLUMNS, ROWS,
)


class ActualCsvLessonTests(unittest.TestCase):
    def test_total_is_58_example_units(self):
        r = demonstrate_csv_total()
        self.assertEqual(r["total"], 58)
        self.assertEqual([x["line_total"] for x in r["rows"]],[20,30,8])

    def test_exact_csv_headers_and_three_synthetic_rows(self):
        r=demonstrate_csv_total()
        text=r["csv_text"].replace("\r\n","\n")
        self.assertEqual(text.splitlines()[0],",".join(COLUMNS))
        self.assertEqual(len(text.splitlines()),4)
        self.assertEqual(len(ROWS),3)

    def test_no_actual_purchase_or_account_actions(self):
        r=demonstrate_csv_total()
        self.assertTrue(r["dataset_is_fictional"])
        self.assertTrue(r["code_executed_without_network_or_personal_files"])
        self.assertFalse(r["purchased_anything"])
        self.assertFalse(r["youtube_uploaded"])
        self.assertFalse(r["publishing_authorized"])
        self.assertEqual(r["currency"],"example_units_no_real_transaction")

    def test_example_is_deterministic_across_runs(self):
        self.assertEqual(demonstrate_csv_total(),demonstrate_csv_total())


if __name__=="__main__":
    unittest.main()
