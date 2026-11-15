"""Adversarial, offline QA for Branch 1 free viewer-first recovery."""
from __future__ import annotations

import copy
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from autopilot.branch1_recovery import (
    COLUMNS, RecoveryRefused, analyze_72h, parse_metrics_csv,
    validate_creative, verify_capture,
)
from autopilot.branch1_record_real_demo import EPISODE_ID, fixture

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT/"content/recovery_pilot/real_csv_proof_first_short.json"

def video_row(i, kind="short", series="privacy_browser"):
    return {
        "video_id": f"fmQ{i:08d}", "format": kind, "series": series,
        "age_hours": "72", "duration_seconds": "25" if kind=="short" else "180",
        "views": "60" if kind=="short" else "35",
        "engaged_views": "30" if kind=="short" else "20",
        "shown_in_feed": "120" if kind=="short" else "",
        "stayed_to_watch_pct": "21.2" if kind=="short" else "",
        "impressions": "" if kind=="short" else "160",
        "impressions_ctr_pct": "" if kind=="short" else "4.8",
        "average_view_duration_seconds": "17" if kind=="short" else "58",
        "subscribers_gained": "0", "retention_3s_pct": "",
        "retention_30s_pct": "",
    }

def write_csv(path, rows, *, columns=COLUMNS):
    with path.open("w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)

class CreativeTests(unittest.TestCase):
    def setUp(self):
        self.brief = json.loads(BRIEF.read_text("utf8"))

    def test_proof_first_real_software_brief_is_review_only(self):
        r = validate_creative(self.brief)
        self.assertEqual(r["opening_proof_by_seconds"], 1.6)
        self.assertEqual(r["first_real_action_at_seconds"], 1.6)
        self.assertFalse(r["owner_approval"])
        self.assertEqual(r["youtube_uploads"], 0)

    def test_reject_title_cards_fake_ui_and_approval_spoof(self):
        cases = [
            lambda b: b["beats"][0].update(role="intro"),
            lambda b: b["beats"][0].update(visual_evidence="illustrative_slide"),
            lambda b: b["beats"][0].update(end_seconds=4),
            lambda b: b["beats"][1].update(start_seconds=4),
            lambda b: b["beats"][4].update(start_seconds=10),
            lambda b: b["beats"][4].update(role="demonstration"),
            lambda b: b["demo"].update(mode="fictional_screen"),
            lambda b: b["demo"].update(fixture_only=False),
            lambda b: b["approval"].update(release_signed=True),
            lambda b: b["approval"].update(youtube_scheduled=True),
            lambda b: b.update(source_url="http://unsafe.invalid"),
            lambda b: b["beats"].pop(),
            lambda b: b["beats"][1].update(visual_evidence="template"),
            lambda b: b["beats"][3].update(action_or_result="<script>"),
        ]
        for mutate in cases:
            with self.subTest(mutate=mutate):
                b = copy.deepcopy(self.brief)
                mutate(b)
                with self.assertRaises(RecoveryRefused):
                    validate_creative(b)

    def test_only_hash_bound_nonapproved_media_claim(self):
        with tempfile.TemporaryDirectory() as d:
            dir = Path(d)
            media = dir/"capture.mp4"
            # Header and SHA bytes are only an identity fixture, not a real clip.
            media.write_bytes(b"\x00\x00\x00\x18ftypisom"+b"X"*31000)
            digest = hashlib.sha256(media.read_bytes()).hexdigest()
            fields = {
                "schema": "FLOWMINUTE_B1_REAL_CAPTURE_V1",
                "status": "ACTUAL_FIRST_PARTY_TERMINAL_CAPTURE_REVIEW_ONLY",
                "episode_id": EPISODE_ID,
                "capture_sha256": digest,
                "capture_bytes": media.stat().st_size,
                "fixture_sha256": "a"*64,
                "capture_method": "xvfb_xterm_ffmpeg_live",
                "private_data": False, "youtube_uploads": 0,
                "release_approved": False,
            }
            receipt = dir/"receipt.json"
            receipt.write_text(json.dumps(fields), "utf8")
            r = verify_capture(self.brief, media, receipt)
            self.assertEqual(r["capture_status"],
                             "EXACT_HASH_VERIFIED_REVIEW_ONLY")
            media.write_bytes(media.read_bytes()+b"X")
            with self.assertRaises(RecoveryRefused):
                verify_capture(self.brief, media, receipt)
            media.write_bytes(media.read_bytes()[:-1])
            fields["release_approved"] = True
            receipt.write_text(json.dumps(fields), "utf8")
            with self.assertRaises(RecoveryRefused):
                verify_capture(self.brief, media, receipt)

    def test_synthetic_fixture_executes_without_live_account_or_network(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source, program = fixture(root)
            self.assertIn("INV-101", source.read_text("utf8"))
            p = subprocess.run([sys.executable, str(program)], cwd=root,
                               capture_output=True, text=True, check=True)
            self.assertIn("4 input rows -> 3 unique invoices", p.stdout)
            with (root/"clean.csv").open(newline="", encoding="utf8") as f:
                cleaned = list(csv.DictReader(f))
            self.assertEqual(len(cleaned), 3)

class StudioMetricsTests(unittest.TestCase):
    def test_short_and_long_cohorts_are_not_blended(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/"synthetic.csv"
            write_csv(path, [video_row(i) for i in range(5)]+[
                video_row(i+5, "long", "excel_sheets") for i in range(5)])
            data = analyze_72h(parse_metrics_csv(path))
            cohorts = {(c["format"],c["series"]):c for c in data["cohorts"]}
            self.assertEqual(len(cohorts), 2)
            short = cohorts[("short","privacy_browser")]
            self.assertEqual(short["weighted_stayed_to_watch_pct"], 21.2)
            self.assertEqual(short["shown_in_feed_with_valid_stay_pct"], 600)
            self.assertEqual(short["status"], "DESCRIPTIVE_EXPERIMENT_ELIGIBLE")
            self.assertNotIn("weighted_impressions_ctr_pct",short)
            long = cohorts[("long","excel_sheets")]
            self.assertEqual(long["weighted_impressions_ctr_pct"], 4.8)
            self.assertEqual(long["status"], "DESCRIPTIVE_EXPERIMENT_ELIGIBLE")
            self.assertNotIn("weighted_stayed_to_watch_pct",long)
            self.assertNotIn("video_id",json.dumps(data))
            self.assertEqual(data["youtube_schedules"],0)

    def test_raw_view_start_ratio_is_never_called_stayed_to_watch(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/"metric.csv"
            rows = [video_row(i) for i in range(5)]
            for row in rows: row["stayed_to_watch_pct"] = ""
            write_csv(path, rows)
            value = analyze_72h(parse_metrics_csv(path))["cohorts"][0]
            self.assertIsNone(value["weighted_stayed_to_watch_pct"])
            self.assertEqual(value["status"], "INSUFFICIENT_SAMPLE")
            self.assertEqual(value["engaged_views"],150)

    def test_fail_closed_on_private_export_columns_and_impossible_metrics(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/"metric.csv"
            row=video_row(1)
            write_csv(path,[{**row,"user_email":"person@example.test"}],
                      columns=(*COLUMNS,"user_email"))
            with self.assertRaises(RecoveryRefused):
                parse_metrics_csv(path)
            bad_values = [
                ("video_id","NOT_A_VALID_ID"),
                ("stayed_to_watch_pct","101"),
                ("stayed_to_watch_pct","NaN"),
                ("shown_in_feed",""),
                ("views","-1"),
                ("engaged_views","90"),
                ("age_hours","100000"),
                ("series","unapproved_niche"),
                ("impressions","42"),
                ("retention_3s_pct","200"),
            ]
            for key,value in bad_values:
                with self.subTest(key=key,value=value):
                    changed={**row,key:value}
                    write_csv(path,[changed])
                    with self.assertRaises(RecoveryRefused):
                        parse_metrics_csv(path)

    def test_missing_age_match_and_low_exposure_never_claim_winner(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"tiny.csv"
            rows=[video_row(i) for i in range(5)]
            for row in rows:
                row["shown_in_feed"]="5"
                row["age_hours"]="24"
            write_csv(path,rows)
            self.assertEqual(analyze_72h(parse_metrics_csv(path))["cohorts"],[])
            for row in rows: row["age_hours"]="72"
            write_csv(path,rows)
            self.assertEqual(analyze_72h(parse_metrics_csv(path))["cohorts"][0]["status"],
                             "INSUFFICIENT_SAMPLE")

if __name__ == "__main__":
    unittest.main()
