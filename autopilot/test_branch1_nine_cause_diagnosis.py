"""Source-only regression tests: no YouTube, real users, paid API or fake recovery."""
from __future__ import annotations
import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from autopilot.branch1_nine_cause_diagnosis import (
    CAUSES, TRAFFIC_COLUMNS, diagnosis, parse_traffic_csv,
)
from autopilot.branch1_recovery import RecoveryRefused

def row(fmt,series,*,stay=None,ctr=None,subs=0,views=100,engaged=30):
    return {
        "format":fmt, "series":series, "age_hours":72,
        "duration_seconds":30 if fmt=="short" else 140,
        "views":views, "engaged_views":engaged,
        "shown_in_feed":200 if fmt=="short" else None,
        "stayed_to_watch_pct":stay if fmt=="short" else None,
        "impressions":200 if fmt=="long" else None,
        "impressions_ctr_pct":ctr if fmt=="long" else None,
        "average_view_duration_seconds":25 if fmt=="short" else 70,
        "subscribers_gained":subs,
        "retention_3s_pct":70 if fmt=="short" else None,
        "retention_30s_pct":50 if fmt=="long" else None,
    }

class NineCauseDiagnosisTests(unittest.TestCase):
    def test_no_data_cannot_be_called_fixed(self):
        cases=[row("short","excel_sheets",stay=10),
               row("long","excel_sheets",ctr=3)]
        report=diagnosis(cases)
        self.assertEqual(report["proven_fixed_count"],0)
        self.assertEqual(report["issues_count"],9)
        self.assertEqual(set(report["issues"]),set(CAUSES))
        self.assertTrue(all(z["status"]=="NEEDS_REAL_AUDIENCE_EVIDENCE"
                            for z in report["issues"].values()))
        self.assertFalse(report["automatic_publishing_approved"])
        self.assertEqual(report["youtube_uploads"],0)
        self.assertEqual(report["youtube_schedules"],0)

    def test_real_metric_sample_is_signal_not_viral_proof(self):
        rows=[row("short","excel_sheets",stay=31,subs=1,
                  views=160,engaged=60) for _ in range(5)]
        rows += [row("long","excel_sheets",ctr=6,subs=1,
                     views=160,engaged=60) for _ in range(5)]
        sources={
            ("baseline","short"):{"views":300,"suggested_views":6},
            ("recovery","short"):{"views":300,"suggested_views":30},
        }
        r=diagnosis(rows,sources)
        for key in ("weak_shorts_hook","weak_long_retention",
                    "weak_packaging","weak_suggested_discovery",
                    "low_subscriber_conversion"):
            self.assertEqual(r["issues"][key]["status"],"DESCRIPTIVE_SIGNAL_ONLY")
        for key in ("scattered_topic_language","repetitive_visuals",
                    "non_demonstrative_look","volume_before_quality"):
            self.assertEqual(r["issues"][key]["status"],"NEEDS_REAL_AUDIENCE_EVIDENCE")
        self.assertEqual(r["proven_fixed_count"],0)
        self.assertFalse(r["automatic_publishing_approved"])

    def test_traffic_csv_rejects_missing_private_and_fabricated_sources(self):
        cases=[
            ["baseline","short","100","3","20","10","40","12","15"],
            ["recovery","short","100","8","20","10","40","12","10"],
        ]
        with TemporaryDirectory() as folder:
            path=Path(folder)/"owner-curated.csv"
            def save(header,entries):
                with path.open("w",encoding="utf8",newline="") as stream:
                    w=csv.writer(stream);w.writerow(header);w.writerows(entries)
            save(TRAFFIC_COLUMNS,cases)
            result=parse_traffic_csv(path)
            self.assertEqual(result[("baseline","short")]["suggested_views"],3)
            save(TRAFFIC_COLUMNS+("email",),[cases[0]+["private@example.com"]])
            with self.assertRaises(RecoveryRefused):
                parse_traffic_csv(path)
            save(TRAFFIC_COLUMNS,[cases[0][:-1]+["100"]])
            with self.assertRaises(RecoveryRefused):
                parse_traffic_csv(path)
            save(TRAFFIC_COLUMNS,[cases[0],cases[0]])
            with self.assertRaises(RecoveryRefused):
                parse_traffic_csv(path)
            save(TRAFFIC_COLUMNS,[cases[0][:-1]+["-1"]])
            with self.assertRaises(RecoveryRefused):
                parse_traffic_csv(path)

if __name__=="__main__":
    unittest.main()
