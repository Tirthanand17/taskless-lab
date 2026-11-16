"""Synthetic-only regression cases for evidence-first YouTube growth decisions."""
from pathlib import Path
from tempfile import TemporaryDirectory
import csv
import json
import unittest

from autopilot.branch1_age_matched_learning import HEADER,read_csv
from autopilot.branch1_growth_action_engine import action_plan
from autopilot.branch1_recovery import RecoveryRefused
from autopilot.test_branch1_age_matched_learning import sample

def fixture_rows(folder,mutate=False):
    rows=[]
    for fmt in ("short","long"):
        for cohort in ("baseline","pilot"):
            for i in range(5):
                row=sample(fmt,cohort,i,72)
                if fmt=="long":
                    row["series"]="python_automation"
                if mutate and cohort=="pilot":
                    row["subscribers_gained"]="0"
                    if fmt=="short":
                        row["stayed_to_watch_pct"]="12"
                    else:
                        row["retention_30s_pct"]="25"
                        row["impressions_ctr_pct"]="2.3"
                rows.append(row)
    path=Path(folder)/"private-owner-studio.csv"
    with path.open("w",encoding="utf8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=HEADER)
        writer.writeheader()
        writer.writerows(rows)
    return read_csv(path)

class GrowthActionTests(unittest.TestCase):
    def test_absent_real_data_reports_concrete_missing_evidence(self):
        r=action_plan()
        self.assertFalse(r["real_age_matched_rows_supplied"])
        self.assertFalse(r["audience_growth_proven"])
        self.assertEqual(r["youtube_uploads"],0)
        self.assertEqual(r["youtube_schedules"],0)
        self.assertEqual(len(r["actions"]),3)
        self.assertEqual({a["code"] for a in r["actions"]},{
            "SHORT_NEEDS_REAL_72H_STUDIO",
            "LONG_NEEDS_REAL_72H_STUDIO",
            "RECOMMENDATION_SOURCE_EVIDENCE_MISSING"})
        self.assertIn("Chrome Find-in-Log Short",r["hold_out_of_first_cohort"])

    def test_good_synthetic_metrics_never_claim_real_growth(self):
        with TemporaryDirectory() as root:
            rows=fixture_rows(root)
            r=action_plan(rows)
            codes={a["code"] for a in r["actions"]}
            self.assertIn("SHORT_HOOK_HOLD_AND_VALIDATE",codes)
            self.assertIn("LONG_OPENING_MONITOR",codes)
            self.assertNotIn("SHORT_HOOK_REWORK",codes)
            self.assertNotIn("LONG_TITLE_COVER_REVIEW",codes)
            self.assertFalse(r["audience_growth_proven"])
            self.assertTrue(r["real_age_matched_rows_supplied"])
            self.assertNotIn("FM00",json.dumps(r))
            self.assertNotIn("private-owner-studio",json.dumps(r))
            self.assertTrue(all(a["automated_upload_authorized"] is False
                                for a in r["actions"]))

    def test_real_format_specific_declines_generate_distinct_actions(self):
        with TemporaryDirectory() as root:
            rows=fixture_rows(root,mutate=True)
            r=action_plan(rows)
            codes={a["code"] for a in r["actions"]}
            self.assertIn("SHORT_HOOK_REWORK",codes)
            self.assertIn("LONG_OPENING_REWORK",codes)
            self.assertIn("LONG_TITLE_COVER_REVIEW",codes)
            self.assertIn("SHORT_NO_SUBSCRIBER_GAINS",codes)
            self.assertIn("LONG_NO_SUBSCRIBER_GAINS",codes)
            self.assertFalse(r["audience_growth_proven"])
            self.assertTrue(all(a["evidence_status"]=="DESCRIPTIVE_NOT_CAUSAL"
                                for a in r["actions"] if a["code"] not in (
                                    "RECOMMENDATION_SOURCE_EVIDENCE_MISSING",)))

    def test_small_sample_does_not_fake_comparison(self):
        with TemporaryDirectory() as root:
            rows=fixture_rows(root)
            rows=[row for row in rows
                  if row["series"]=="excel_sheets" and row["cohort"]=="pilot"][:1]
            r=action_plan(rows)
            codes={a["code"] for a in r["actions"]}
            self.assertIn("SHORT_SAMPLE_TOO_SMALL",codes)
            self.assertIn("LONG_NEEDS_REAL_72H_STUDIO",codes)
            self.assertNotIn("SHORT_HOOK_REWORK",codes)
            self.assertFalse(r["audience_growth_proven"])

    def test_reduced_suggested_and_browse_is_not_called_shadowban(self):
        with TemporaryDirectory() as root:
            rows=fixture_rows(root)
            baseline={"views":200,"suggested_views":50,"browse_views":50}
            after={"views":200,"suggested_views":20,"browse_views":10}
            r=action_plan(rows,{("baseline","long"):baseline,
                                 ("recovery","long"):after})
            codes={a["code"] for a in r["actions"]}
            self.assertIn("LONG_SUGGESTED_BROWSE_SHARE_DOWN",codes)
            self.assertFalse(r["audience_growth_proven"])
            self.assertNotIn("shadowban",json.dumps(r).lower())

    def test_no_production_tokens_import_or_unauthorized_youtube_calls(self):
        code=(Path(__file__).parent/"branch1_growth_action_engine.py").read_text("utf8")
        for bad in ("youtube.videos().insert","googleapiclient",
                    "oauth2","publish_youtube(","status.publishAt",
                    "studio.youtube.com","PUBLISH_ENABLED: true"):
            self.assertNotIn(bad,code)
        with self.assertRaises(RecoveryRefused):
            action_plan([])
        with self.assertRaises(RecoveryRefused):
            action_plan(None,[])

if __name__=="__main__":
    unittest.main()
