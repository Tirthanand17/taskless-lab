"""Adversarial Studio 24/72/168h longitudinal QA with synthetic tests ONLY."""
from __future__ import annotations
import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from autopilot.branch1_age_matched_learning import (
    HEADER,read_csv,summary,
)
from autopilot.branch1_recovery import RecoveryRefused

def sample(fmt,cohort,i,age):
    n={24:1,72:2,168:3}[age]
    vid=f"FM{i:02d}{cohort[0]}{fmt[0]}X0000"
    assert len(vid)==11,(vid,len(vid))
    row={field:"" for field in HEADER}
    row.update({
        "video_id":vid,"cohort":cohort,"format":fmt,
        "series":"excel_sheets","age_hours":str(age),
        "duration_seconds":"25.0" if fmt=="short" else "235.0",
        "views":str(60*n),"engaged_views":str(40*n),
        "average_view_duration_seconds":str(14+4*n if fmt=="short" else 43+8*n),
        "subscribers_gained":str(n-1),
    })
    if fmt=="short":
        row.update({
            "shown_in_feed":str(100*n),
            "stayed_to_watch_pct":"20" if cohort=="baseline" else "34",
            "retention_3s_pct":"43" if cohort=="baseline" else "65",
        })
    else:
        row.update({
            "impressions":str(100*n),
            "impressions_ctr_pct":"4.0" if cohort=="baseline" else "6.1",
            "retention_30s_pct":"41" if cohort=="baseline" else "57",
        })
    return row

class AgeMatchedStudioTests(unittest.TestCase):
    def write(self,folder,rows,header=HEADER):
        path=Path(folder)/"owner_studio_private.csv"
        with path.open("w",newline="",encoding="utf8") as file:
            writer=csv.DictWriter(file,fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def dataset(self):
        return [
            sample(fmt,cohort,i,age)
            for fmt in ("short","long")
            for cohort in ("baseline","pilot")
            for i in range(5)
            for age in (24,72,168)
        ]

    def test_age_match_same_video_and_noncausal_comparisons(self):
        with TemporaryDirectory() as folder:
            path=self.write(folder,self.dataset())
            result=summary(read_csv(path))
            self.assertEqual(len(result["cohorts"]),12)
            self.assertEqual(len(result["comparisons"]),6)
            self.assertEqual(result["youtube_uploads"],0)
            self.assertEqual(result["youtube_schedules"],0)
            self.assertFalse(result["audience_recovery_proven"])
            self.assertTrue(result["no_video_ids_or_audience_private_data_in_output"])
            for cmp in result["comparisons"]:
                self.assertEqual(cmp["status"],"DESCRIPTIVE_ONLY_NOT_CAUSAL")
                self.assertTrue(cmp["no_experimental_winner_claim"])
                self.assertEqual(cmp["pilot_minus_baseline_percentage_points"],
                                 14 if cmp["format"]=="short" else 16)
            self.assertNotIn("FM00",str(result))
            self.assertNotIn("owner_studio_private",str(result))

    def test_missing_or_tiny_comparison_never_becomes_a_winner(self):
        with TemporaryDirectory() as folder:
            rows=[sample("short","pilot",0,72),
                  sample("short","baseline",0,72)]
            report=summary(read_csv(self.write(folder,rows)))
            self.assertEqual(report["comparisons"][0]["status"],
                             "INSUFFICIENT_OR_INCOMPLETE_STUDIO_DATA")
            self.assertIsNone(report["comparisons"][0][
                "pilot_minus_baseline_percentage_points"])
            self.assertFalse(report["audience_recovery_proven"])

    def test_private_columns_duplicate_age_and_forged_format_rejected(self):
        with TemporaryDirectory() as folder:
            orig=self.dataset()
            with self.assertRaises(RecoveryRefused):
                read_csv(self.write(folder,[orig[0],orig[0]]))
            altered=[dict(x) for x in orig]
            altered[0]["cohort"]="fake_trial"
            with self.assertRaises(RecoveryRefused):
                read_csv(self.write(folder,altered))
            altered=[dict(x) for x in orig]
            altered[0]["age_hours"]="31"  # outside 24h ±6
            with self.assertRaises(RecoveryRefused):
                read_csv(self.write(folder,altered))
            private=[{**x,"email":"secret@example.com"} for x in orig]
            with self.assertRaises(RecoveryRefused):
                read_csv(self.write(folder,private,HEADER+("email",)))
            altered=[dict(x) for x in orig]
            altered[0]["impressions"]="200"  # not a valid Shorts CTR measure
            with self.assertRaises(RecoveryRefused):
                read_csv(self.write(folder,altered))

    def test_metrics_cumulative_and_studio_source_not_fake(self):
        with TemporaryDirectory() as folder:
            original=self.dataset()
            altered=[dict(x) for x in original]
            altered[2]["views"]="1"  # same video, 168h lower than 72h
            with self.assertRaises(RecoveryRefused):
                read_csv(self.write(folder,altered))
            altered=[dict(x) for x in original]
            altered[0]["stayed_to_watch_pct"]="75"
            altered[0]["shown_in_feed"]=""  # cannot invent swipe from views
            with self.assertRaises(RecoveryRefused):
                read_csv(self.write(folder,altered))
            altered=[dict(x) for x in original]
            altered[0]["age_hours"]="-1"
            with self.assertRaises(RecoveryRefused):
                read_csv(self.write(folder,altered))
            altered=[dict(x) for x in original]
            altered[0]["stayed_to_watch_pct"]="110"
            with self.assertRaises(RecoveryRefused):
                read_csv(self.write(folder,altered))

if __name__=="__main__":
    unittest.main()
