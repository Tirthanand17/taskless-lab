"""Tests guard real app recordings from being stretched under voice narration."""
from __future__ import annotations

import unittest

from autopilot.branch1_real_action_coverage_gate import (
    MAX_CLONED_SOURCE_SHARE,RealActionCoverageRefused,require_coverage,
    requirement_plan,
)
from autopilot.branch1_narrated_real_app_short import STORIES

class RealActionCoverageTests(unittest.TestCase):
    def test_existing_ten_second_source_is_unfit_for_real_voice(self):
        for app in ("calc","chrome"):
            report=requirement_plan(STORIES[app]["source_windows"],
                                    [6.,5.,5.,5.,6.])
            self.assertFalse(report["internal_screen_coverage_pass"])
            self.assertGreater(report["predicted_frozen_fraction"],.45)
            self.assertGreater(report["worst_frozen_chapter_seconds"],2)
            self.assertFalse(report["owner_approval"])
            self.assertEqual(report["youtube_schedules"],0)
            with self.assertRaisesRegex(RealActionCoverageRefused,
                                        "NO_PROLONGED_STATIC_GUI"):
                require_coverage(STORIES[app]["source_windows"],
                                 [6.,5.,5.,5.,6.])

    def test_real_extended_source_with_synchronized_voice_can_pass(self):
        windows=((0,5.5),(5.5,5.0),(10.5,5.0),(15.5,5.0),(20.5,5.5))
        report=require_coverage(windows,[6.,5.,5.,5.,6.])
        self.assertTrue(report["internal_screen_coverage_pass"])
        self.assertLess(report["predicted_frozen_fraction"],
                        MAX_CLONED_SOURCE_SHARE)
        self.assertEqual(report["status"],
                         "SOURCE_TIMELINE_COVERS_REAL_NARRATION")
        self.assertEqual(report["youtube_uploads"],0)

    def test_one_held_chapter_refused_even_if_average_looks_moderate(self):
        windows=((0,6.),(6.,6.),(12.,6.),(18.,1.),(19.,6.))
        plan=requirement_plan(windows,[6.,6.,6.,6.,6.])
        self.assertLess(plan["predicted_frozen_fraction"],.25)
        self.assertFalse(plan["internal_screen_coverage_pass"])
        with self.assertRaises(RealActionCoverageRefused):
            require_coverage(windows,[6.,6.,6.,6.,6.])

    def test_disallow_missing_forged_or_impossible_timing(self):
        cases=[
            ([(0,3)], [4]),
            ([(0,1)]*5, [float("nan")]*5),
            ([(0,1)]*5, [False]*5),
            ([(0,-1)]*5, [5]*5),
            ([(100,5)]*5, [5]*5),
            ([(0,5)]*5, [0]*5),
            ([(0,5)]*5, [float("inf")]*5),
            ([(0,5)]*5, [5]*4),
        ]
        for windows,durations in cases:
            with self.subTest(windows=windows,durations=durations):
                with self.assertRaises(RealActionCoverageRefused):
                    requirement_plan(windows,durations)

if __name__=="__main__":
    unittest.main()
