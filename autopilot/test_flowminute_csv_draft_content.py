"""Lightweight structural checks against the ACTUAL authored CSV video pack.

This tests only the written Markdown draft, not speech/audio synchronization,
source truth, visual assets, licensing or production publishing readiness.
"""
from pathlib import Path
import re
import unittest

from autopilot.examples.flowminute_csv_demo import demonstrate_csv_total

FILE = Path(__file__).parent / "research_briefs" / "2026-10-17_csv_bilingual_one_day_scripts_DRAFT.md"
TIME = re.compile(r"^\| (\d\d):(\d\d)–(\d\d):(\d\d) \| (.+?) \| (.+?) \|$", re.MULTILINE)


def seconds(minutes: str, sec: str) -> int:
    return 60 * int(minutes) + int(sec)


def sections():
    raw=FILE.read_text(encoding="utf-8")
    a,b,c=(raw.index("## SHORT 1"),
           raw.index("## SHORT 2"),
           raw.index("## LONG VIDEO"))
    return raw,raw[a:b],raw[b:c],raw[c:]


class AuthoredContentTests(unittest.TestCase):
    def test_source_file_exists(self):
        self.assertTrue(FILE.is_file())

    def test_two_short_and_one_long_section_present(self):
        raw,s1,s2,lg=sections()
        self.assertIn("Hindi/Hinglish",s1)
        self.assertIn("English",s2)
        self.assertIn("7 minutes 12 seconds",lg)

    def test_shorts_use_planned_distinct_narrators_only(self):
        raw,s1,s2,lg=sections()
        self.assertIn("narrator A",s1)
        self.assertIn("narrator B",s2)
        self.assertIn("voice has not been recorded",s1)
        self.assertIn("voice has not been recorded",s2)

    def test_timed_scenes_are_contiguous_and_approximate_intended_lengths(self):
        _,s1,s2,lg=sections()
        for label,part,target,num in (
            ("hindi_short",s1,42,4),
            ("english_short",s2,42,4),
            ("hindi_long",lg,432,24),
        ):
            with self.subTest(label=label):
                timings=TIME.findall(part)
                self.assertEqual(len(timings),num)
                prior=0
                for a,b,c,d,spoken,visual in timings:
                    start,end=seconds(a,b),seconds(c,d)
                    self.assertEqual(start,prior)
                    self.assertGreater(end,start)
                    self.assertGreater(len(spoken),30)
                    self.assertGreater(len(visual),20)
                    prior=end
                self.assertEqual(prior,target)

    def test_hindi_has_devanagari_and_english_has_explanation(self):
        _,s1,s2,lg=sections()
        self.assertGreater(len(re.findall(r"[\u0900-\u097f]",s1)),50)
        self.assertGreater(len(re.findall(r"[\u0900-\u097f]",lg)),250)
        self.assertIn("DictReader",s2)

    def test_labels_and_no_fake_actual_video_claim(self):
        raw,_,_,_=sections()
        self.assertIn("ILLUSTRATIVE SIMULATION",raw)
        self.assertIn("FICTIONAL SAMPLE DATA",raw)
        self.assertIn("voice has not been recorded",raw)
        self.assertIn("UNREVIEWED WRITING",raw)
        self.assertIn("not three generated MP4s",raw)

    def test_original_synthetic_code_demo_matches_video_claim(self):
        sample=demonstrate_csv_total()
        self.assertEqual(sample["total"],58)
        raw,_,_,_=sections()
        self.assertIn("58 fictional example units",raw)

    def test_no_unqualified_marketing_or_account_action_promises(self):
        raw,_,_,_=sections()
        lower=raw.casefold()
        for forbidden in ("guaranteed viral","we booked your ticket",
                          "we purchased for you","100% free for everyone"):
            self.assertNotIn(forbidden,lower)


if __name__=="__main__":
    unittest.main()
