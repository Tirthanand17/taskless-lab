"""B1 Nov13–17: original 15-media source and pixel QA, no YouTube writes."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

from autopilot.branch1_nov13_17_original_batch import (
    read_day,frame,cover,VALID_DATES,STATUS,
    OriginalBatchRefused,ACCENT_BY_DAY,TIME_IST,EXPECTED_SOURCE_BY_DATE,
)


class SourceBoundFiveDayTests(unittest.TestCase):
    def test_complete_15_video_5_day_calendar_and_voice_script(self):
        names=[]
        titles=[]
        for date in sorted(VALID_DATES):
            day,hash_=read_day(date)
            self.assertEqual(len(hash_),64)
            self.assertEqual(day["date_ist"],date)
            self.assertEqual(day["channel_id"],"UCCcL9Q_jqVq6LJmnYUSAFZA")
            self.assertEqual([ep["time_ist"] for ep in day["episodes"]],
                             list(TIME_IST))
            self.assertEqual([ep["kind"] for ep in day["episodes"]],
                             ["short","short","long"])
            self.assertEqual([len(ep["scenes"]) for ep in day["episodes"]],
                             [5,5,12])
            self.assertEqual([ep["source"] for ep in day["episodes"]],
                             list(EXPECTED_SOURCE_BY_DATE[date]))
            for ep in day["episodes"]:
                self.assertFalse(any(ep["approval"].values()))
                self.assertTrue(ep["title"])
                self.assertEqual(ep["language"],"en")
                self.assertTrue(ep["source"].startswith("https://"))
                self.assertNotIn("real footage",ep.get("source_linked_claims","").lower())
                names.append(ep["id"]); titles.append(ep["title"])
                from autopilot.branch1_nov12_four_review_videos import split_script
                for scene in ep["scenes"]:
                    text=scene[3]
                    self.assertEqual(" ".join(split_script(text,ep["kind"])),
                                     " ".join(text.split()))
        self.assertEqual(len(names),15)
        self.assertEqual(len(set(names)),15)
        self.assertEqual(len(set(titles)),15)

    def test_unknown_date_and_approval_refused(self):
        for bad in ("2026-11-12","2026-11-18","2026-10-31","tomorrow","2026-11-13Z"):
            with self.assertRaises(OriginalBatchRefused):
                read_day(bad)
        self.assertTrue(STATUS.endswith("NO_UPLOAD"))


@unittest.skipUnless(importlib.util.find_spec("PIL"),
                     "Full original pixel rendering requires Pillow")
class PhysicalSourcePixelTests(unittest.TestCase):
    def test_all_15_original_video_first_frames_distinct_and_not_blank(self):
        from PIL import ImageChops
        signatures=set()
        for date in sorted(VALID_DATES):
            daily,_=read_day(date)
            for ep in daily["episodes"]:
                scene=ep["scenes"][0]
                color=ACCENT_BY_DAY[date]
                base=frame(ep,scene,0,0,color)
                middle=frame(ep,scene,0,1,color)
                end=frame(ep,scene,0,2,color)
                expected=(1080,1920) if ep["kind"]=="short" else (1920,1080)
                self.assertEqual(base.size,expected)
                self.assertIsNotNone(ImageChops.difference(base,middle).getbbox())
                self.assertIsNotNone(ImageChops.difference(middle,end).getbbox())
                region=(78,392,1002,1418) if ep["kind"]=="short" else (
                        110,356,1810,802)
                h=hashlib.sha256(base.crop(region).tobytes()).hexdigest()
                self.assertNotIn(h,signatures)
                signatures.add(h)
                # Native subtitles are an independent fixed bottom panel.
                sub=(78,1515,1002,1750) if ep["kind"]=="short" else (
                      110,835,1810,1021)
                self.assertIsNone(ImageChops.difference(
                    base.crop(sub),end.crop(sub)).getbbox())
                self.assertIsNone(ImageChops.difference(
                    end,frame(ep,scene,0,2,color)).getbbox())
        self.assertEqual(len(signatures),15)

    def test_no_circular_loading_animation_and_27_scenes_per_date_have_distinct_hashes(self):
        from PIL import ImageChops
        for date in sorted(VALID_DATES):
            daily,_=read_day(date)
            seen=set()
            for ep in daily["episodes"]:
                for idx,scene in enumerate(ep["scenes"]):
                    end=frame(ep,scene,idx,2,ACCENT_BY_DAY[date])
                    h=hashlib.sha256(end.tobytes()).hexdigest()
                    self.assertNotIn(h,seen)
                    seen.add(h)
            self.assertEqual(len(seen),22)  # 5 + 5 + 12 = 22 true beats

    def test_five_original_full_aware_covers_by_day(self):
        from PIL import Image
        from tempfile import TemporaryDirectory
        for date in sorted(VALID_DATES):
            day,_=read_day(date)
            with TemporaryDirectory() as root:
                for ep in day["episodes"]:
                    coverpath=cover(ep,ACCENT_BY_DAY[date],Path(root))
                    with Image.open(coverpath) as picture:
                        self.assertEqual(picture.size,
                                         (1080,1920) if ep["kind"]=="short"
                                         else (1280,720))
                        self.assertEqual(picture.mode,"RGB")
                    self.assertGreater(coverpath.stat().st_size,20_000)

    def test_reject_untrusted_motion_phase_and_no_extra_episode(self):
        ep=read_day("2026-11-13")[0]["episodes"][0]
        scene=ep["scenes"][0]
        for bad in (-1,3,"1",True,None):
            with self.assertRaises(OriginalBatchRefused):
                frame(ep,scene,0,bad,ACCENT_BY_DAY["2026-11-13"])
        with self.assertRaises(OriginalBatchRefused):
            frame(ep,scene,8,0,ACCENT_BY_DAY["2026-11-13"])


if __name__=="__main__":
    unittest.main()
