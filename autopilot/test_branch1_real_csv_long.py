"""Source-only adversarial QA for genuine Python long-form data cleaning."""
from __future__ import annotations
import csv
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from autopilot.branch1_real_csv_long import (
    STORY,RAW_ROWS,RAW_TOTAL,CLEAN_TOTAL,EXPECTED_IDS,
    LongPilotRefused,make_fixture,read_and_clean,save_clean_and_recheck,
    verify_story,stage_content,real_app_screen,render,
)

class RealPythonLongPilotTests(unittest.TestCase):
    def test_verified_story_is_substantive_one_problem_not_an_illustration(self):
        result=verify_story()
        self.assertEqual(result["scenes"],12)
        self.assertGreaterEqual(result["words"],360)
        self.assertLessEqual(result["words"],640)
        self.assertTrue(result["real_python_required"])
        self.assertFalse(result["youtube_release_approved"])
        self.assertIn("FIXED TOTAL",STORY[9][0])
        self.assertIn("TAKEAWAY",STORY[-1][0])
        self.assertNotIn("viral", " ".join(scene[1] for scene in STORY).lower())
        self.assertEqual(len(RAW_ROWS),8)

    def test_actual_long_tts_caption_split_cannot_leave_a_one_word_cue(self):
        from autopilot.branch1_nov12_four_review_videos import split_script
        for title,spoken in STORY:
            cues=split_script(spoken,"long")
            self.assertTrue(all(8<=len(cue)<=114 for cue in cues))
            self.assertEqual(" ".join(cues)," ".join(spoken.split()))
        # The exact first physical attempt #43876156866 was rejected
        # when a sentence split left a tiny terminal cue "cents.".
        broken=("This original CSV says eight rows add up to two thousand six hundred fifty "
                "six dollars and twenty five cents. But the genuinely cleaned file has six "
                "invoices worth one thousand four hundred thirty dollars and seventy five "
                "cents. Let us find each mistake using real Python.")
        with patch("autopilot.branch1_real_csv_long.STORY",
                   ((STORY[0][0],broken),)+STORY[1:]):
            with self.assertRaises(LongPilotRefused):
                verify_story()

    def test_actual_decimal_cleaning_and_file_reimport(self):
        with TemporaryDirectory() as t:
            root=Path(t)
            source=make_fixture(root)
            data=read_and_clean(source)
            self.assertEqual(data["raw_total"],str(RAW_TOTAL))
            self.assertEqual(data["clean_total"],str(CLEAN_TOTAL))
            self.assertEqual(data["difference"],"1225.50")
            self.assertEqual(data["duplicates"],["INV-101","INV-104"])
            self.assertEqual(tuple(r["invoice"] for r in data["clean"]),EXPECTED_IDS)
            self.assertEqual(len(data["original"]),8)
            self.assertEqual(len(data["clean"]),6)
            saved=save_clean_and_recheck(root,data)
            self.assertTrue(saved.is_file())
            with saved.open(newline="",encoding="utf8") as f:
                output=list(csv.DictReader(f))
            self.assertEqual(len(output),6)
            self.assertEqual(sum((Decimal(r["amount"]) for r in output),
                                 Decimal("0")),CLEAN_TOTAL)
            with self.assertRaises(LongPilotRefused):
                save_clean_and_recheck(root,data)
            self.assertEqual(len(source.read_text().splitlines()),9)

    def test_source_malformed_money_and_identity_are_rejected(self):
        with TemporaryDirectory() as t:
            root=Path(t)
            source=make_fixture(root)
            text=source.read_text("utf8")
            for before,after in (
                ("1,200.50","X,200.50"),
                ("  INV-101","INV-007"),
                ("INV-104,25.00","INV-999,25.00"),
            ):
                with self.subTest(before=before):
                    source.write_text(text.replace(before,after,1),"utf8")
                    with self.assertRaises(LongPilotRefused):
                        read_and_clean(source)
            source.write_text(text,"utf8")
            self.assertEqual(read_and_clean(source)["raw_total"],"2656.25")

    def test_every_visible_result_is_from_actually_read_source(self):
        with TemporaryDirectory() as t:
            root=Path(t)
            data=read_and_clean(make_fixture(root))
            for stage in range(12):
                for part in range(4):
                    with self.subTest(stage=stage,part=part):
                        title,line=stage_content(stage,part,data)
                        self.assertEqual(title,STORY[stage][0])
                        self.assertGreater(len(line),12)
                        self.assertNotIn("www.",line)
            self.assertIn("2656.25",stage_content(0,0,data)[1])
            self.assertIn("1430.75",stage_content(0,1,data)[1])
            self.assertIn("1225.50",stage_content(9,3,data)[1])

    def test_16_by_9_lesson_uses_real_source_zoom_not_empty_desktop(self):
        code=(Path(__file__).parent/"branch1_real_csv_long.py").read_text("utf8")
        self.assertIn("crop=1120:500:0:0",code)
        self.assertIn("scale=1920:858:flags=lanczos",code)
        self.assertIn("pad=1920:1080:0:0:color=0x081827",code)
        self.assertIn("drawbox=x=0:y=840:w=iw:h=240:color=0x081827@0.94",code)
        self.assertNotIn("scale=1920:1080:flags=lanczos",code)
        self.assertIn('source=folder/SOURCE',code)
        self.assertIn('"x11grab"',code)

    def test_capture_never_runs_on_laptop_or_approves_youtube(self):
        with TemporaryDirectory() as t:
            out=Path(t)/"original"
            with patch.dict("os.environ",{"GITHUB_ACTIONS":"false"}):
                with self.assertRaises(LongPilotRefused):
                    real_app_screen(out,160)
            with self.assertRaises(LongPilotRefused):
                render(out,Path("fake.onnx"),Path("fake.bin"))
        source=(Path(__file__).parent/"branch1_real_csv_long.py").read_text("utf8")
        for needle in (
            'os.environ.get("GITHUB_REF")=="refs/heads/main"',
            'os.environ.get("PUBLISH_ENABLED")=="false"',
            '"FLOWMINUTE_ALLOW_LAPTOP")=="0"',
            "REAL_PYTHON_EXECUTION_FINISHED",
            "save_clean_and_recheck(folder,data)",
            "verify_exact_encoded_master",
            "AUDIO_REMASTER_FILTER",
            '"youtube_uploads":0,"youtube_schedules":0',
            '"publishing_authorized":False',
            "xterm",
            "x11grab",
        ):
            self.assertIn(needle,source)
        for forbidden in ("youtube.videos().insert","status.publishAt",
                          "googleapiclient","oauth2","publish_youtube(",
                          "moviepy", "yt-dlp"):
            self.assertNotIn(forbidden,source)

if __name__=="__main__":
    unittest.main()
